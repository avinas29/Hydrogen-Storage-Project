"""Phase 2: cleaned analytical copies of both datasets.

Conventions in the cleaned files (raw values are kept alongside):
* ``dH_kJmol``  = desorption enthalpy magnitude, kJ/mol H2, positive
                 (Purdue: -DH/1000; HydPARK: Heat_of_Formation_kJperMolH2)
* ``dS_JmolK``  = desorption entropy magnitude, J/(mol H2 K), positive
* ``wt_pct``    = reported capacity, wt% H on hydride basis H/(H+M)
* ``comp_key``  = composition normalised to atomic fractions, elements sorted,
                 fractions rounded to 3 decimals, e.g. ``Fe0.5Ti0.5``.  Two
                 records with the same key are the same chemical composition
                 regardless of notation (LaNi5 == La1Ni5 == La16.67Ni83.33).

No record is dropped.  Records whose composition cannot be represented with
real elements get ``parse_status`` != "ok" and ``comp_key`` = NaN.
"""
from __future__ import annotations

import warnings
from pathlib import Path

import numpy as np
import pandas as pd
from pymatgen.core import Composition

from .purdue_parser import PSEUDO_ELEMENTS

warnings.filterwarnings("ignore", category=UserWarning, module="pymatgen")

ROOT = Path(__file__).resolve().parents[2]
INTERIM = ROOT / "data/interim"
PROCESSED = ROOT / "data/processed"

KEY_DECIMALS = 3


def comp_key(comp: Composition) -> str:
    frac = comp.fractional_composition
    items = sorted((el.symbol, round(float(x), KEY_DECIMALS)) for el, x in frac.items())
    return "".join(f"{s}{x:g}" for s, x in items if x > 0)


def reduced_formula(comp: Composition) -> str:
    return comp.reduced_formula


# --------------------------------------------------------------------------
def clean_purdue(p: pd.DataFrame) -> pd.DataFrame:
    out = pd.DataFrame({
        "purdue_id": p["material_id"],
        "source_file": p["source_file"],
        "type_raw": p["type"],
        "composition_raw": p["composition"],
    })
    keys, rf, status, n_el, natoms = [], [], [], [], []
    for comp_s, mid in zip(p["composition"], p["material_id"]):
        parts = dict(x.split(":") for x in comp_s.split(";") if x)
        els = set(parts)
        if els & PSEUDO_ELEMENTS:
            keys.append(np.nan); rf.append(np.nan); n_el.append(len(els))
            status.append("pseudo_element:" + ",".join(sorted(els & PSEUDO_ELEMENTS)))
            natoms.append(sum(float(v) for v in parts.values()))
            continue
        try:
            c = Composition({k: float(v) for k, v in parts.items()})
            keys.append(comp_key(c)); rf.append(reduced_formula(c))
            status.append("ok_contains_H" if "H" in els else "ok")
            n_el.append(len(c.elements)); natoms.append(c.num_atoms)
        except Exception as e:  # pragma: no cover - none observed
            keys.append(np.nan); rf.append(np.nan); status.append(f"error:{e}")
            n_el.append(len(els)); natoms.append(np.nan)
    out["comp_key"] = keys
    out["reduced_formula"] = rf
    out["parse_status"] = status
    out["n_elements"] = n_el
    out["atoms_per_formula_unit"] = natoms
    # Family label used for analysis: toolbox type, with the multi-element
    # 'Misc' kept as is.  (Purdue has no C14/C15 split.)
    out["family"] = p["type"]

    out["dH_kJmol"] = -p["des_dH_J_per_molH2"] / 1000
    out["dS_JmolK"] = -p["des_dS_J_per_molH2K"]
    out["dH_all_plateaus_kJmol"] = p["des_dH_J_per_molH2_all"].fillna("").apply(
        lambda s: ";".join(f"{-float(x)/1000:g}" for x in s.split(";")) if s else "")
    out["dS_all_plateaus_JmolK"] = p["des_dS_J_per_molH2K_all"].fillna("").apply(
        lambda s: ";".join(f"{-float(x):g}" for x in s.split(";")) if s else "")
    out["n_plateaus"] = p["n_plateaus"]
    out["abs_dH_kJmol"] = -p["abs_dH_J_per_molH2"] / 1000
    out["abs_dS_JmolK"] = -p["abs_dS_J_per_molH2K"]
    out["hysteresis_ln_Pa_Pd"] = p.get("abs_lnPa_Pd")
    out["wt_pct"] = p["wt_pct_toolbox"]
    out["wt_pct_stated"] = p["wt_pct_stated"]
    out["h_per_formula_unit_stated"] = p["hm_stated"]
    out["h_per_metal_atom"] = p["h_per_metal_atom_toolbox"]
    out["capacity_basis"] = p["capacity_basis"]
    out["capacity_definition"] = p["capacity_definition"]
    out["rho_kg_m3"] = p["rho_kg_per_m3"]
    out["cp_J_kgK"] = p["cp_J_per_kgK"]
    out["keff_W_mK"] = p["keff_W_per_mK"]
    for m in ("abs", "des"):
        out[f"kin_{m}_Ea_Jmol"] = pd.to_numeric(p.get(f"kin_{m}_Ea"), errors="coerce")
        out[f"kin_{m}_Ca_per_s"] = pd.to_numeric(p.get(f"kin_{m}_Ca"), errors="coerce")
    out["pci_file"] = p["pci_file"].fillna("")
    out["ref_keys"] = p["ref_keys"]
    out["ref_ids"] = p["ref_ids"]
    out["dH_source_comment"] = p["des_DH_comment"]
    for c in [c for c in p.columns if c.startswith("flag_")]:
        out[c] = p[c]
    out["flag_unparseable_composition"] = ~out["parse_status"].str.startswith("ok")
    return out


# --------------------------------------------------------------------------
HP_FAMILY = {"AB2(C14)": "AB2", "AB2(C15)": "AB2"}


def clean_hydpark(h: pd.DataFrame) -> pd.DataFrame:
    out = pd.DataFrame({
        "hydpark_id": h["hydpark_id"],
        "source_block": h["source_block"],
        "row_in_file": h["row_in_file"],
        "class_raw": h["Material_Class"],
        "formula_raw": h["Composition_Formula"],
    })
    keys, rf, status, n_el, natoms = [], [], [], [], []
    for f in h["Composition_Formula"]:
        try:
            c = Composition(f)
            keys.append(comp_key(c)); rf.append(reduced_formula(c)); status.append("ok")
            n_el.append(len(c.elements)); natoms.append(c.num_atoms)
        except Exception as e:  # pragma: no cover - none observed
            keys.append(np.nan); rf.append(np.nan); status.append(f"error:{e}")
            n_el.append(np.nan); natoms.append(np.nan)
    out["comp_key"] = keys
    out["reduced_formula"] = rf
    out["parse_status"] = status
    out["n_elements"] = n_el
    out["atoms_per_formula_as_written"] = natoms
    out["family"] = h["Material_Class"].map(lambda x: HP_FAMILY.get(x, x))
    out["laves_type"] = h["Material_Class"].where(h["Material_Class"].isin(HP_FAMILY), "")

    out["dH_kJmol"] = h["Heat_of_Formation_kJperMolH2"]
    out["dS_JmolK"] = h["Entropy_of_Formation_JperMolH2perK"]
    out["wt_pct"] = h["Hydrogen_Weight_Percent"]
    out["h_per_metal_atom"] = h["HtoM"]
    out["T_point_C"] = h["Temperature_oC"]
    out["P_point_atm"] = h["Pressure_Atmospheres_Absolute"]
    out["Peq25_atm_raw"] = h["Equilibrium_Pressure_25C"]
    out["lnPeq25_raw"] = h["LnEquilibrium_Pressure_25C"]
    out["reference"] = h["Reference"].str.replace(r"\s+", "", regex=True)
    for c in [c for c in h.columns if c.startswith("flag_")]:
        out[c] = h[c]
    # Missing values coded as 0 in the raw file are NaN in the analytical copy
    zero_cap = out["wt_pct"] == 0
    out.loc[zero_cap, ["wt_pct", "h_per_metal_atom"]] = np.nan
    out["note_cleaning"] = np.where(zero_cap, "wt_pct=0 and HtoM=0 treated as missing", "")
    out["flag_unparseable_composition"] = out["parse_status"] != "ok"
    return out


def mark_chemical_duplicates(df: pd.DataFrame, id_col: str) -> pd.DataFrame:
    df = df.copy()
    g = df.groupby("comp_key", dropna=True)[id_col]
    df["n_records_same_comp"] = df["comp_key"].map(g.size()).fillna(1).astype(int)
    df["flag_chemical_duplicate"] = df["n_records_same_comp"] > 1
    # Group id for grouped cross-validation: one group per composition
    codes = {k: i for i, k in enumerate(sorted(df["comp_key"].dropna().unique()))}
    df["comp_group"] = [codes.get(k, -1 - i) if isinstance(k, str) else -1 - i
                        for i, k in enumerate(df["comp_key"])]
    return df


def main() -> tuple[pd.DataFrame, pd.DataFrame]:
    PROCESSED.mkdir(parents=True, exist_ok=True)
    p = mark_chemical_duplicates(
        clean_purdue(pd.read_csv(INTERIM / "purdue_extracted.csv", keep_default_na=True)),
        "purdue_id")
    h = mark_chemical_duplicates(
        clean_hydpark(pd.read_csv(INTERIM / "hydpark_flagged.csv")), "hydpark_id")
    from .compare import ignored_purdue_in_hydpark
    ign = ignored_purdue_in_hydpark(h)
    ign_ids = set(";".join(ign["hydpark_ids"]).split(";")) - {""}
    h["flag_excluded_by_purdue_curators"] = h["hydpark_id"].isin(ign_ids)
    p.to_csv(PROCESSED / "purdue_cleaned.csv", index=False)
    h.to_csv(PROCESSED / "hydpark_cleaned.csv", index=False)
    return p, h


if __name__ == "__main__":
    p, h = main()
    print("purdue", p.shape, p.parse_status.value_counts().to_dict())
    print("hydpark", h.shape, h.parse_status.value_counts().to_dict())
    print("purdue chem dups:", p.flag_chemical_duplicate.sum(), "hydpark chem dups:", h.flag_chemical_duplicate.sum())
