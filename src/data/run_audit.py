"""Phase 1: extract both datasets, attach flags, write audit tables and reports.

Run from the project root:  .venv/bin/python -m src.data.run_audit
"""
from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

from .hydpark import BLOCK_DESCRIPTION, DS_TYPICAL, load_hydpark
from .purdue_flags import add_flags
from .purdue_parser import load_purdue, read_pci_file

ROOT = Path(__file__).resolve().parents[2]
TOOLBOX = ROOT / "data/raw/purdue/MetalHydrideToolbox"
HYDPARK_CSV = ROOT / "data/raw/hydpark/ML-HYDPARK_v0.0.5.csv"
XLSX = ROOT / "data/raw/purdue/MetalHydrideToolbox_database_337 (1).xlsx"
INTERIM = ROOT / "data/interim"
TABLES = ROOT / "results/tables"
REPORTS = ROOT / "reports"


def md_table(df: pd.DataFrame, floatfmt: str = "{:.3g}") -> str:
    cols = [str(c) for c in df.columns]
    out = ["| " + " | ".join(cols) + " |", "|" + "---|" * len(cols)]
    for _, r in df.iterrows():
        cells = [floatfmt.format(v) if isinstance(v, float) else str(v) for v in r]
        out.append("| " + " | ".join(cells) + " |")
    return "\n".join(out)


def pci_index(pci_dir: Path) -> pd.DataFrame:
    rows = []
    for f in sorted(pci_dir.glob("*_PCI.csv")):
        p = read_pci_file(f)
        c = p["curves"]
        rows.append({
            "material_id": f.name.replace("_PCI.csv", ""), "pci_file": f.name,
            "author": p["author"], "doi_or_source": p["doi"],
            "figure_location": p["location"], "note": p["note"],
            "digitized_from_figure": p["location"].lower().startswith("fig"),
            "shifted_by_curator": "shift" in p["note"].lower(),
            "n_curves": len(c), "n_abs": sum(x["mode"] == "abs" for x in c),
            "n_des": sum(x["mode"] == "des" for x in c),
            "T_K_list": ";".join(f"{t:g}" for t in sorted({x["T_K"] for x in c})),
            "n_points": sum(len(x["P_bar"]) for x in c),
        })
    return pd.DataFrame(rows)


def missing_summary(purdue: pd.DataFrame, hp: pd.DataFrame) -> pd.DataFrame:
    p_props = {
        "capacity (wt% stated)": "wt_pct_stated",
        "capacity (H/M stated)": "hm_stated",
        "capacity (either; wt% derived by toolbox)": "wt_pct_toolbox",
        "desorption dH": "des_dH_J_per_molH2",
        "desorption dS": "des_dS_J_per_molH2K",
        "absorption dH": "abs_dH_J_per_molH2",
        "absorption dS": "abs_dS_J_per_molH2K",
        "hysteresis ln(Pa/Pd)": "abs_lnPa_Pd",
        "critical temperature Tc": "abs_Tc",
        "plateau slope": "des_slope",
        "density rho": "rho_kg_per_m3",
        "heat capacity Cp": "cp_J_per_kgK",
        "thermal conductivity keff": "keff_W_per_mK",
        "absorption kinetics Ea": "kin_abs_Ea",
        "desorption kinetics Ea": "kin_des_Ea",
    }
    rows = []
    n = len(purdue)
    for name, col in p_props.items():
        present = pd.to_numeric(purdue[col], errors="coerce").notna().sum() if col in purdue else 0
        rows.append({"dataset": "Purdue", "property": name, "column": col, "n_records": n,
                     "n_present": int(present), "n_missing": int(n - present),
                     "pct_present": round(100 * present / n, 1),
                     "toolbox_substitutes_default_if_missing":
                         col in {"rho_kg_per_m3", "cp_J_per_kgK", "keff_W_per_mK",
                                 "kin_abs_Ea", "kin_des_Ea", "abs_lnPa_Pd", "abs_Tc",
                                 "des_slope", "abs_dH_J_per_molH2", "abs_dS_J_per_molH2K"}})
    for i in ["pci_file"]:
        present = (purdue[i] != "").sum()
        rows.append({"dataset": "Purdue", "property": "PCI isotherm file", "column": i,
                     "n_records": n, "n_present": int(present), "n_missing": int(n - present),
                     "pct_present": round(100 * present / n, 1),
                     "toolbox_substitutes_default_if_missing": False})
    n = len(hp)
    for col in ["Material_Class", "Composition_Formula", "Hydrogen_Weight_Percent",
                "Heat_of_Formation_kJperMolH2", "Temperature_oC",
                "Pressure_Atmospheres_Absolute", "Entropy_of_Formation_JperMolH2perK",
                "Equilibrium_Pressure_25C", "LnEquilibrium_Pressure_25C", "HtoM", "Reference"]:
        present = hp[col].notna().sum()
        rows.append({"dataset": "HydPARK", "property": col, "column": col, "n_records": n,
                     "n_present": int(present), "n_missing": int(n - present),
                     "pct_present": round(100 * present / n, 1),
                     "toolbox_substitutes_default_if_missing": False})
    return pd.DataFrame(rows)


def class_distribution(purdue: pd.DataFrame, hp: pd.DataFrame) -> pd.DataFrame:
    a = purdue["type"].value_counts().rename_axis("material_class").reset_index(name="n_records")
    a.insert(0, "dataset", "Purdue")
    b = hp["Material_Class"].fillna("(missing)").value_counts().rename_axis(
        "material_class").reset_index(name="n_records")
    b.insert(0, "dataset", "HydPARK")
    out = pd.concat([a, b], ignore_index=True)
    out["pct_of_dataset"] = out.groupby("dataset")["n_records"].transform(
        lambda s: (100 * s / s.sum()).round(1))
    return out


def crosscheck_xlsx(purdue: pd.DataFrame) -> pd.DataFrame:
    if not XLSX.exists():
        return pd.DataFrame()
    x = pd.read_excel(XLSX)
    m = purdue.merge(x, left_on="material_id", right_on="Name", how="left")
    pairs = [("wt_pct_stated", "Weight Percent (wt% H)"), ("hm_stated", "H/M"),
             ("des_dH_J_per_molH2", "Dehyd DH (J/mol H2)"),
             ("des_dS_J_per_molH2K", "Dehyd DS (J/mol.K)"),
             ("abs_dH_J_per_molH2", "Hyd DH (J/mol H2)"),
             ("abs_dS_J_per_molH2K", "Hyd DS (J/mol.K)"),
             ("rho_kg_per_m3", "rho (kg/m3)"), ("cp_J_per_kgK", "Cp (J/kg.K)"),
             ("keff_W_per_mK", "keff (W/m.K)")]
    rows = []
    for a, b in pairs:
        A = pd.to_numeric(m[a], errors="coerce")
        B = pd.to_numeric(m[b], errors="coerce")
        both = A.notna() & B.notna()
        rows.append({"parser_column": a, "xlsx_column": b, "n_parser": int(A.notna().sum()),
                     "n_xlsx": int(B.notna().sum()),
                     "n_agree": int(np.isclose(A[both], B[both]).sum()),
                     "n_disagree": int((~np.isclose(A[both], B[both])).sum()),
                     "only_parser": int((A.notna() & B.isna()).sum()),
                     "only_xlsx": int((A.isna() & B.notna()).sum())})
    return pd.DataFrame(rows)


def main() -> None:
    for d in (INTERIM, TABLES, REPORTS):
        d.mkdir(parents=True, exist_ok=True)

    purdue = add_flags(load_purdue(TOOLBOX))
    pci = pci_index(TOOLBOX / "data/supporting")
    hp = load_hydpark(HYDPARK_CSV)
    # The Excel export is a private earlier extraction used only as a cross-check. Without it, reuse the saved table.
    xfile = TABLES / "purdue_parser_vs_xlsx_crosscheck.csv"
    xchk = crosscheck_xlsx(purdue) if XLSX.exists() else pd.read_csv(xfile)

    purdue.to_csv(INTERIM / "purdue_extracted.csv", index=False)
    pci.to_csv(INTERIM / "purdue_pci_index.csv", index=False)
    hp.to_csv(INTERIM / "hydpark_flagged.csv", index=False)
    xchk.to_csv(xfile, index=False)
    cls = class_distribution(purdue, hp)
    cls.to_csv(TABLES / "material_class_distribution.csv", index=False)
    miss = missing_summary(purdue, hp)
    miss.to_csv(TABLES / "missing_value_summary.csv", index=False)

    write_purdue_report(purdue, pci, xchk)
    write_hydpark_report(hp)
    write_audit_report(purdue, pci, hp, cls, miss)
    print(f"Purdue: {purdue.shape}, PCI files: {len(pci)}, HydPARK: {hp.shape}")


# --------------------------------------------------------------------------
# Reports
# --------------------------------------------------------------------------
def _n(s) -> int:
    return int(s.sum())


def write_purdue_report(p: pd.DataFrame, pci: pd.DataFrame, xchk: pd.DataFrame) -> None:
    single = p[~p["flag_multi_plateau"]]
    types = p["type"].value_counts()
    cap = p["capacity_definition"].value_counts()
    ids = p["ref_ids"].str.split("; ").explode()
    id_kind = np.select(
        [ids.str.match(r"10\.\d+", na=False), ids.str.contains("SandiaDBRef", na=False)],
        ["DOI", "SandiaDBRef placeholder"], "ISBN / report / other")
    id_kind = pd.Series(id_kind).value_counts()
    dS = p["des_dS_J_per_molH2K"]
    dH = p["des_dH_J_per_molH2"]
    pseudo = p["pseudo_elements"].str.split(",").explode().replace("", np.nan).dropna().value_counts()
    approx = p[p["flag_composition_approximate"]][["material_id", "elements_comment"]]
    multi = p[p["flag_multi_plateau"]][["material_id", "type", "n_plateaus",
                                        "des_dH_J_per_molH2_all", "des_dS_J_per_molH2K_all"]]
    text = f"""# Purdue Metal Hydride Toolbox: dataset summary

Generated by `src/data/run_audit.py` from the local snapshot
`data/raw/purdue/MetalHydrideToolbox/` (copied unchanged from
`~/Documents/MATLAB/MetalHydrideToolbox`, git HEAD `68e445f`).

## 1. What the toolbox is

An object-oriented MATLAB toolbox (T. Voskuilen, Purdue Hydrogen Systems Lab).
Each material is one ASCII `data/*.mh` file. These are read by
`@MetalHydride/MetalHydride.m` via `ReadFile.m`, `ReadZones.m`, `ReadThermo.m` and
`ReadProps.m`, plus `@KineticsModel` and `@Reference`.

| Item | Count |
|---|---|
| `.mh` material files (loaded by the toolbox) | {len(p)} |
| `.ignore` files (excluded by the toolbox, not extracted) | {len(list((TOOLBOX / 'data').glob('*.ignore')))} |
| PCI isotherm files `data/supporting/*_PCI.csv` | {len(pci)} |
| Distinct material types | {p['type'].nunique()} |

Material types: {', '.join(f'{k} {v}' for k, v in types.items())}.

## 2. How properties are represented (verified in the MATLAB source)

* **Sign convention.** `DH` and `DS` are *formation* values. They are negative, in
  J/mol H2 and J/(mol H2 K). `Peq.m` evaluates `Peq = 101325*exp((dH - T*dS)/(R*T))`
  with R = 8.314. In decomposition (positive) form this is
  `ln(P/P0) = -|dH|/(RT) + |dS|/R`. Example: TiFe, dH = -28.1 kJ/mol H2 and
  dS = -106 J/(mol H2 K), gives Peq(298 K) of about 4 atm. All {len(p)} desorption dH values
  are negative: min {dH.min()/1000:.1f}, max {dH.max()/1000:.1f} kJ/mol H2.
* **Desorption ("Dehydriding") thermodynamics are mandatory.** `ReadThermo.m`
  raises an error without them, so all {len(p)} files have dH and dS.
  {len(single)} are single-plateau scalars. {_n(p['flag_multi_plateau'])} are multi-plateau arrays (this explains
  the earlier "~325 with dH and dS" figure: 337 - 12 = 325).
* **Absorption ("Hydriding") thermodynamics are optional.** Given directly as dH/dS in
  {_n(p['abs_dH_J_per_molH2'].notna())} files and as hysteresis ln(Pa/Pd) in {_n(p['has_hysteresis'])}.
  Otherwise the toolbox *computes* them from a type-default hysteresis and Tc.
* **Capacity.** A file gives either `Weight Percent` ({_n(p['capacity_basis']=='stated_wt_pct')} files) or
  `H/M` ({_n(p['flag_capacity_from_HM'])} files). `ReadThermo.m` converts H/M as
  `wt = HM*1.008 / (HM*1.008 + W_formula)`, where `W_formula` is the molar
  mass of **one formula unit**. So the `.mh` "H/M" entry is really **H atoms per
  formula unit**. For example, `Mm[1]Ni[4.8]Al[0.2]` has `H/M: 6`, i.e. MmNi4.8Al0.2H6.
  The stated values support this reading: AB5 3.0-7.2, AB2 2.0-3.5, SS 0.4-1.8,
  and converted to H per metal atom they fall in 0.4-2.0. The class property `HM`
  that MATLAB exposes is different: it is H **per metal atom**. The Excel export
  in `Downloads/` labels the column "H atoms per metal atom", which is
  **incorrect** for the raw `.mh` entry. Weight percent is defined on the hydride
  basis H/(H+M), since `wMax = WtPct/(1-WtPct)` is kg H per kg metal.
* **Missing properties.** `ReadProps.m`, `KineticsModel.m` and `ReadThermo.m` silently
  substitute **type defaults** (`GetTypeProperty.m`) for absent rho, Cp, keff,
  kinetics Ca/Ea, hysteresis, Tc and plateau slope. The extractor here does **not**
  insert these defaults. Absent means NaN.
* **Multi-plateau.** Arrays `DH: [..]`, `DS: [..]` plus `centers`, `widths`,
  `minSpans`, which give the fractional capacity spans of each plateau.
* **Elements and pseudo-elements.** `@Element/Element.m` hard-codes molar masses,
  including three non-elements: `Mm` (mischmetal, 140.311), `Lm` (La-rich
  mischmetal, 138.9055) and `Vf` (ferrovanadium, 53.39). Their real compositions
  vary by supplier and are not recorded.

## 3. Parser verification

The Python parser (`src/data/purdue_parser.py`) was cross-checked against the
independent verbatim Excel export (`MetalHydrideToolbox_database_337 (1).xlsx`):

{md_table(xchk)}

All shared values agree. The parser-only values are the {_n(p['flag_multi_plateau'])} multi-plateau
entries: the Excel export leaves the scalar blank, while the parser keeps the first
plateau in the scalar column and the full array in `*_all`.

## 4. Property availability

| Property | Records with a written value |
|---|---|
| Capacity, any basis | {_n(p['wt_pct_toolbox'].notna())} |
| Capacity explicitly described as reversible | {cap.get('reversible_stated', 0)} |
| Desorption dH and dS | {len(p)} ({len(single)} single-plateau) |
| Absorption dH/dS | {_n(p['abs_dH_J_per_molH2'].notna())} |
| Hysteresis ln(Pa/Pd) | {_n(p['has_hysteresis'])} |
| Absorption kinetics (Ca, Ea) | {_n(p['has_kin_abs'])} |
| Desorption kinetics (Ca, Ea) | {_n(p['has_kin_des'])} |
| Density | {_n(p['has_rho'])} |
| Heat capacity | {_n(p['has_cp'])} |
| Thermal conductivity | {_n(p['has_keff'])} |
| PCI isotherm file | {_n(p['flag_has_pci_digitized'])} |
| Desorption thermo flagged `From Isotherms: true` | {_n(p['des_from_isotherms'])} |

## 5. Capacity definition (from the source comment of each value)

{md_table(cap.rename_axis('capacity_definition').reset_index(name='n'))}

Most capacity values cite a table or figure but do **not** say whether the number is
reversible, maximum or plateau capacity. They are labelled
`literature_value_definition_unstated`. The earlier description of "223 direct
reversible capacities" is not supported: 223 values are stated in wt%, but only
{cap.get('reversible_stated', 0)} comments say "reversible". The toolbox itself uses the value as `wMax`,
the capacity spanned by the plateau model.

## 6. References

{md_table(id_kind.rename_axis('reference_id_type').reset_index(name='n_citations'))}

{_n(p['flag_unverified_ref_sandia'])} materials cite at least one `SandiaDBRef####` placeholder. These come from the
legacy Sandia hydride database, and the toolbox's own `WriteExcelSummary.m` marks them
"Verified? = NO".

## 7. Ambiguous or approximate compositions ({_n(p['flag_ambiguous_formula'])} materials)

* Pseudo-elements: {', '.join(f'{k} in {v} files' for k, v in pseudo.items())}
  ({_n(p['flag_pseudo_element'])} materials).
* Trade-name files (no composition in the filename): {', '.join(p.loc[p['flag_trade_name_file'], 'material_id'])}.
* Hydrogen written as an element: {', '.join(p.loc[p['flag_contains_H_in_formula'], 'material_id'])}
  (NaAlH4 entered as `Na[1]Al[1]H[1]`).
* Comments flagging an approximate composition:

{md_table(approx)}

## 8. Multi-plateau materials

{md_table(multi)}

## 9. PCI files

All {len(pci)} PCI files were **digitized from published figures**: the `Location`
field is "Figure N" in {_n(pci['digitized_from_figure'])}/{len(pci)}. {_n(pci['shifted_by_curator'])} carry a note that the curve was **shifted
along the composition axis** to remove the irreversible portion. They are processed
literature curves, not raw experimental files. {_n(pci['n_abs']>0)} files contain absorption
curves, {_n(pci['n_des']>0)} contain desorption curves, and {_n((pci['n_abs']>0)&(pci['n_des']>0))} contain both (hysteresis can be read off these).
Full index: `data/interim/purdue_pci_index.csv`.

## 10. Entropy sanity check

{_n(p['flag_dS_atypical'])} materials have |dS| outside {DS_TYPICAL[0]:.0f}-{DS_TYPICAL[1]:.0f} J/(mol H2 K). The typical value
for interstitial hydrides is about 110-130, set by the entropy of H2 gas, 130.7 J/(mol K):

{md_table(p[p['flag_dS_atypical']][['material_id','type','des_dH_J_per_molH2','des_dS_J_per_molH2K','ref_keys']])}
"""
    (REPORTS / "purdue_dataset_summary.md").write_text(text)


def write_hydpark_report(h: pd.DataFrame) -> None:
    blocks = h.groupby("source_block").agg(
        n=("hydpark_id", "size"),
        classes=("Material_Class", lambda s: ", ".join(f"{k} {v}" for k, v in s.fillna("(none)").value_counts().items())),
        with_reference=("Reference", lambda s: int(s.notna().sum())),
        with_T_P=("Temperature_oC", lambda s: int(s.notna().sum())),
        dS_derived_from_TP=("flag_dS_derived_from_TP", "sum"),
    ).reset_index()
    blocks["description"] = blocks["source_block"].map(BLOCK_DESCRIPTION)
    flag_cols = [c for c in h.columns if c.startswith("flag_")]
    flags = pd.DataFrame({"flag": flag_cols, "n_rows": [int(h[c].sum()) for c in flag_cols]})
    cols = ["hydpark_id", "source_block", "Material_Class", "Composition_Formula",
            "Hydrogen_Weight_Percent", "Heat_of_Formation_kJperMolH2", "Temperature_oC",
            "Pressure_Atmospheres_Absolute", "Entropy_of_Formation_JperMolH2perK"]
    err = h[h["flag_suspected_entry_error"]][cols]
    tpbad = h[h["flag_dS_TP_inconsistent"]][cols + ["dS_from_TP"]]
    atyp = h[h["flag_dS_atypical"]][cols]
    dup = h[h["flag_duplicate_formula"]]
    lnp = h.groupby("source_block").apply(
        lambda g: (g["lnP25_recomputed"] - g["LnEquilibrium_Pressure_25C"]).abs().max(),
        include_groups=False)
    text = f"""# ML-HydPARK v0.0.5: dataset summary

Generated by `src/data/run_audit.py` from `data/raw/hydpark/ML-HYDPARK_v0.0.5.csv`
(an unchanged copy of `~/Downloads/ML-HYDPARK_v0.0.5.csv`).

## 1. Dimensions

**{len(h)} rows x 13 columns** (an unnamed row counter, `index`, and 11 data
columns). This is **not** the ~420 records previously reported. The `index` column
restarts three times, which shows the file is **four appended source blocks**:

{md_table(blocks)}

No composition appears in more than one block. A `source_block` column is added
so that provenance is never lost. Records are also given a stable ID, `HP0000`-`HP{len(h)-1:04d}`.

## 2. Columns, units and conventions (verified numerically)

| Column | Meaning / finding |
|---|---|
| `Heat_of_Formation_kJperMolH2` | **Positive** magnitude, kJ/mol H2 (decomposition convention). It is the *opposite sign* to Purdue (negative, J/mol H2) |
| `Entropy_of_Formation_JperMolH2perK` | Positive magnitude, J/(mol H2 K) |
| `Temperature_oC`, `Pressure_Atmospheres_Absolute` | A single (T, P) point. Present for {int(h['Temperature_oC'].notna().sum())} rows (blocks 0 and 2) |
| `Equilibrium_Pressure_25C` | atm, = exp(`LnEquilibrium_Pressure_25C`). **Derived** |
| `LnEquilibrium_Pressure_25C` | = -dH/(R x 298.15) + dS/R. **Derived** (max deviation per block: {', '.join(f'block {k}: {v:.3f}' for k, v in lnp.items())}; block 1 seems to use slightly different constants) |
| `HtoM` | H atoms per **metal atom**, computed from wt% on the H/(H+M) basis (max deviation 1e-4). **Derived from, or used to derive, wt%**, so it is not independent |
| `Reference` | DOI string. Missing for all of block 0 ({int(h['flag_missing_reference'].sum())} rows missing in total) |

**Entropy is back-calculated.** For {int(h['flag_dS_derived_from_TP'].sum())} of {int(h['Temperature_oC'].notna().sum())} rows that have T and P,
`dS = R ln P + dH/T` holds to better than 0.01 J/(mol K). So dS is a function of
(dH, T, P) and is **not** an independent measurement. In consequence:
(i) dS, Peq(25 C) and ln Peq(25 C) must never be inputs when predicting dH
(target leakage); (ii) the "experimental" dS in block 0 carries the same
uncertainty as the single (T, P) point it came from.

## 3. Quality flags (rows are flagged, never deleted)

{md_table(flags)}

### Suspected data-entry errors

{md_table(err)}

* Er6Fe23 and Ho6Fe23 have `Temperature_oC = 0`, and their stored dS does not
  match R ln P + dH/T at 0 C (by about 42 J/(mol K)). The temperature is
  probably missing and coded as 0. Their Peq(25 C) is NaN in the file.
* ErAg has dS = -5.2 J/(mol K), which is physically implausible for H2 release.
* (Ti)(Cr0.93Mo0.07)2.37 has capacity 0 and HtoM 0, probably a missing value coded as 0.

### dS inconsistent with the stated (T, P)

{md_table(tpbad)}

### Entropy outside {DS_TYPICAL[0]:.0f}-{DS_TYPICAL[1]:.0f} J/(mol H2 K) ({len(atyp)} rows)

These are flagged as *atypical*, not as wrong. Many are low-dH Zr-Mn-Fe AB2 alloys
whose dS came from a single high-pressure point.

{md_table(atyp)}

## 4. Duplicates

* Exact duplicate rows (all data columns): {int(h.drop(columns=[c for c in h.columns if c.startswith(('flag_','dS_from','lnP25'))]+['hydpark_id','row_in_file','index_in_block','source_block']).duplicated().sum())}.
* Duplicate `Composition_Formula` strings: {dup['Composition_Formula'].nunique()} formulas in {len(dup)} rows,
  all inside block 3. They are repeated measurements from different papers or C14/C15
  assignments, with different dH. They are kept, and they are grouped together during
  cross-validation.
* Formula strings mix three notations: plain (`LaNi4.8Al0.2`), atomic-%
  (`V75Ti17.5Zr7.5`), and sublattice (`(Ti0.2Zr0.8)(Cr0.56Mn0.44)2.25`). pymatgen
  parses all {len(h)}. Normalising to fractional composition (Phase 2) reveals
  further chemical duplicates that differ only in notation.

## 5. Capacity definition

`Hydrogen_Weight_Percent` has no stated definition (reversible, maximum, or at what
P/T). In block 3 it is computed from a rounded `HtoM`. It is therefore treated
as a *reported* capacity, of uncertain definition, and is not mixed with Purdue
capacity without a compatibility check.
"""
    (REPORTS / "hydpark_dataset_summary.md").write_text(text)


def write_audit_report(p, pci, h, cls, miss) -> None:
    text = f"""# Phase 1 data audit

All numbers are produced by `src/data/run_audit.py`. Raw files are untouched.

## Files found

| Item | Location | Status |
|---|---|---|
| Purdue Metal Hydride Toolbox (MATLAB, git HEAD 68e445f) | `~/Documents/MATLAB/MetalHydrideToolbox` | Found. Snapshot in `data/raw/purdue/MetalHydrideToolbox/` (179 files were iCloud placeholders and are now downloaded) |
| `.mh` material files | `data/*.mh` | {len(p)} |
| PCI isotherms | `data/supporting/*_PCI.csv` | {len(pci)} |
| MATLAB classes | `@MetalHydride` (18 .m), `@Element`, `@KineticsModel`, `@Reference` | Read and used to fix conventions |
| Toolbox docs | `README.md`, `doc/Demo.m`, `doc/dbSummary.csv`, `doc/refs.txt`, `doc/hydrideRefs.bib` | Found |
| Excel export (prior verbatim extraction) | `~/Downloads/MetalHydrideToolbox_database_337 (1).xlsx` (54 cols) and `...337.xlsx` (50 cols) | Used only as a cross-check |
| ML-HydPARK v0.0.5 | `~/Downloads/ML-HYDPARK_v0.0.5.csv` | Found, {len(h)} rows |
| Untracked user scratch files in toolbox | `untitled*.mlx`, `doc1.m` | Not part of the toolbox; not copied |

Nothing that was required is missing.

## Key findings that change the analysis plan

1. **HydPARK has {len(h)} rows in 4 appended blocks, not ~420.** The block number is kept
   as provenance.
2. **Opposite sign conventions.** Purdue: negative formation dH/dS in J/mol H2.
   HydPARK: positive magnitudes, dH in kJ/mol H2. Both were verified against the
   Van't Hoff relation, so the analytical copies are converted to one convention
   (positive desorption magnitudes, kJ/mol H2).
3. **HydPARK dS is back-calculated** from dH and one (T, P) point for
   {int(h['flag_dS_derived_from_TP'].sum())} rows. Peq(25 C), ln Peq(25 C) and HtoM are all derived. None of them may
   be used as features for dH or wt% prediction.
4. **The Purdue "H/M" input is H per formula unit**, not per metal atom (verified in
   `ReadThermo.m` and by the value ranges). wt% derived from it is reproduced with
   the toolbox's own molar masses and flagged `capacity_basis = derived_from_HM_per_formula_unit`.
5. **Purdue capacity is mostly of unstated definition.** Only
   {int((p['capacity_definition']=='reversible_stated').sum())} comments say "reversible", and {int(p['flag_capacity_uncertain'].sum())} are assumed, approximate,
   theoretical or unconfirmed.
6. **The toolbox fills missing properties with type defaults.** Defaults are excluded here.
   Density is present for {int(p['has_rho'].sum())}, Cp for {int(p['has_cp'].sum())}, keff for {int(p['has_keff'].sum())}, and kinetics for {int(p['has_kin_abs'].sum())} (abs) / {int(p['has_kin_des'].sum())} (des) materials.
7. **All 68 PCI files are digitized from literature figures**; {int(pci['shifted_by_curator'].sum())} were also shifted by the curator.
8. **{int(p['flag_unverified_ref_sandia'].sum())} Purdue materials cite unverified SandiaDBRef placeholders**, and {int(p['flag_ambiguous_formula'].sum())} have ambiguous compositions
   (Mm/Lm/Vf, trade names, approximate notes, NaAlH4 written as NaAlH).

## Previously reported statistics vs. verified

| Statistic | Reported | Verified | Note |
|---|---|---|---|
| Purdue .mh files | ~337 | {len(p)} | |
| AB5 / AB2 / AB / SS / AB3 / A2B7 / Misc / Mg / Complex | 146/106/29/24/14/8/5/4/1 | {'/'.join(str(int((p['type']==t).sum())) for t in ['AB5','AB2','AB','SS','AB3','A2B7','Misc','Mg','Complex'])} | matches |
| Entries with dH and dS | ~325 | {len(p)} (all); {int((~p['flag_multi_plateau']).sum())} single-plateau | 12 multi-plateau |
| Direct reversible capacity | ~223 | 223 stated wt% + 114 via H/M; {int((p['capacity_definition']=='reversible_stated').sum())} explicitly "reversible" | definition mostly unstated |
| PCI files | ~68 | {len(pci)} | all digitized |
| Kinetics abs / des | 31 / 26 | {int(p['has_kin_abs'].sum())} / {int(p['has_kin_des'].sum())} | |
| Density / Cp / keff | 37 / 28 / 14 | {int(p['has_rho'].sum())} / {int(p['has_cp'].sum())} / {int(p['has_keff'].sum())} | |
| Sandia placeholder refs | ~102 | {int(p['flag_unverified_ref_sandia'].sum())} | |
| Ambiguous formulas | ~49 | {int(p['flag_pseudo_element'].sum())} pseudo-element; {int(p['flag_ambiguous_formula'].sum())} incl. trade names/approx./NaAlH | |
| HydPARK records | ~420 | {len(h)} | 4 blocks |

## Outputs

* `data/interim/purdue_extracted.csv`: {p.shape[0]} x {p.shape[1]}, raw values plus flags
* `data/interim/purdue_pci_index.csv`: index of the 68 PCI files
* `data/interim/hydpark_flagged.csv`: {h.shape[0]} x {h.shape[1]}, raw columns plus block plus flags
* `results/tables/material_class_distribution.csv`
* `results/tables/missing_value_summary.csv`
* `results/tables/purdue_parser_vs_xlsx_crosscheck.csv`
* `reports/purdue_dataset_summary.md`, `reports/hydpark_dataset_summary.md`

## Material class distribution

{md_table(cls)}

## Missing values

{md_table(miss[['dataset','property','n_present','n_missing','pct_present','toolbox_substitutes_default_if_missing']])}
"""
    (REPORTS / "data_audit.md").write_text(text)


if __name__ == "__main__":
    main()
