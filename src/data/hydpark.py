"""Load ML-HydPARK v0.0.5 and attach provenance + quality flags.

Findings from inspecting the raw CSV (see reports/hydpark_dataset_summary.md):

* 772 rows, not ~420.  The ``index`` column restarts three times, so the file
  is four appended source blocks.  We keep the block number as ``source_block``.
* Sign convention: ``Heat_of_Formation_kJperMolH2`` and
  ``Entropy_of_Formation_JperMolH2perK`` are stored as POSITIVE magnitudes
  (desorption / decomposition convention), unlike Purdue (negative formation).
  Verified: LnEquilibrium_Pressure_25C = -dH/(R*298.15) + dS/R.
* Where Temperature_oC / Pressure_Atmospheres_Absolute exist, the entropy is
  back-calculated from one (T, P) point:  dS = R ln P + dH / T  (|diff| < 1e-3
  J/mol/K for 395 of 403 rows).  Such dS values are not independent
  measurements; ln P(25 C) is a deterministic function of dH and dS.
"""
from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

R = 8.314  # J/(mol K)

RAW_COLUMNS = [
    "Material_Class", "Composition_Formula", "Hydrogen_Weight_Percent",
    "Heat_of_Formation_kJperMolH2", "Temperature_oC",
    "Pressure_Atmospheres_Absolute", "Entropy_of_Formation_JperMolH2perK",
    "Equilibrium_Pressure_25C", "LnEquilibrium_Pressure_25C", "HtoM", "Reference",
]

# Typical range for the entropy of H2 desorption from interstitial hydrides is
# about 90-140 J/(mol H2 K), dominated by the standard entropy of H2 gas
# (130.7 J/(mol K)) (Sandrock 1999; Zuttel 2003).  We flag values outside a
# deliberately generous 70-170 window as "atypical", not as wrong.
DS_TYPICAL = (70.0, 170.0)


def load_raw(path: Path) -> pd.DataFrame:
    d = pd.read_csv(path)
    d = d.rename(columns={d.columns[0]: "row_in_file", "index": "index_in_block"})
    return d


def assign_blocks(d: pd.DataFrame) -> pd.Series:
    resets = np.r_[0, np.where(np.diff(d["index_in_block"].to_numpy()) < 0)[0] + 1]
    block = np.zeros(len(d), dtype=int)
    for b, start in enumerate(resets):
        block[start:] = b
    return pd.Series(block, index=d.index, name="source_block")


BLOCK_DESCRIPTION = {
    0: "397 rows, 7 broad classes, no Reference column; T and P given and dS back-calculated from them",
    1: "25 rows, no Material_Class, DOI references, no T/P; dS given directly",
    2: "15 SS (solid solution / HEA) rows, DOI references, T/P given",
    3: "335 AB2 rows split into C14/C15 Laves types, DOI references, no T/P",
}


def build_flags(d: pd.DataFrame) -> pd.DataFrame:
    f = pd.DataFrame(index=d.index)
    dH = d["Heat_of_Formation_kJperMolH2"]
    dS = d["Entropy_of_Formation_JperMolH2perK"]
    T = d["Temperature_oC"] + 273.15
    P = d["Pressure_Atmospheres_Absolute"]

    dS_tp = R * np.log(P) + dH * 1000 / T
    f["dS_from_TP"] = dS_tp
    f["flag_dS_derived_from_TP"] = (dS_tp - dS).abs() < 0.01
    f["flag_dS_TP_inconsistent"] = (dS_tp - dS).abs() >= 0.01
    lnp = -dH * 1000 / (R * 298.15) + dS / R
    f["lnP25_recomputed"] = lnp
    f["flag_lnP25_mismatch"] = (lnp - d["LnEquilibrium_Pressure_25C"]).abs() > 0.01

    f["flag_missing_reference"] = d["Reference"].isna()
    f["flag_missing_class"] = d["Material_Class"].isna()
    f["flag_missing_wt"] = d["Hydrogen_Weight_Percent"].isna()
    f["flag_zero_capacity"] = d["Hydrogen_Weight_Percent"] == 0
    f["flag_T_zero_suspect"] = d["Temperature_oC"] == 0  # 0 C combined with dS mismatch -> likely missing T coded 0
    f["flag_dS_atypical"] = (dS < DS_TYPICAL[0]) | (dS > DS_TYPICAL[1])
    f["flag_dS_negative"] = dS < 0
    # dH > 100 kJ/mol H2 means desorption needs > ~500 C: very stable hydrides (Th, Zr, Ti2Cu ...)
    f["flag_dH_very_stable"] = dH > 100
    f["flag_duplicate_formula"] = d["Composition_Formula"].duplicated(keep=False)

    f["flag_suspected_entry_error"] = (
        f["flag_zero_capacity"] | f["flag_dS_negative"]
        | (f["flag_T_zero_suspect"] & f["flag_dS_TP_inconsistent"])
    )
    return f


def load_hydpark(path: Path) -> pd.DataFrame:
    d = load_raw(path)
    d.insert(0, "hydpark_id", [f"HP{i:04d}" for i in range(len(d))])
    d.insert(1, "source_block", assign_blocks(d))
    return pd.concat([d, build_flags(d)], axis=1)
