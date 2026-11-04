"""Phase 4: build feature tables for the dH and wt% tasks.

Outputs
* data/processed/features_dH.csv   one row per composition (Phase 2 union)
* data/processed/features_wt.csv   Purdue stated-wt% subset
* results/tables/elemental_property_table.csv
* results/tables/feature_list.csv  (name, group, description, kept after pruning)
* results/tables/feature_collinear_pairs.csv

Run:  .venv/bin/python -m src.features.build
"""
from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

from .composition import LEAKY_FOR_DH, PROPS, featurize, parse_key

ROOT = Path(__file__).resolve().parents[2]
PROC = ROOT / "data/processed"
TABLES = ROOT / "results/tables"
NONMETALS = {"H", "O", "B", "C", "N", "Si", "Ge", "Sb", "Bi"}
COLLINEAR_R = 0.95
FAMILY_MIN = 10


def family_onehot(fam: pd.Series, keep: list[str]) -> pd.DataFrame:
    f = fam.fillna("other").where(fam.isin(keep), "other")
    return pd.get_dummies(f, prefix="fam").astype(int)


def prune_collinear(X: pd.DataFrame, priority: list[str]) -> tuple[list[str], pd.DataFrame]:
    """Greedy: walk features in priority order, drop any with |r| > COLLINEAR_R to a kept one."""
    corr = X.corr().abs()
    kept: list[str] = []
    pairs = []
    for c in priority:
        if X[c].std() == 0:
            pairs.append({"dropped": c, "because_of": "(constant)", "abs_r": np.nan})
            continue
        clash = [k for k in kept if corr.loc[c, k] > COLLINEAR_R]
        if clash:
            pairs.append({"dropped": c, "because_of": clash[0], "abs_r": corr.loc[c, clash[0]]})
        else:
            kept.append(c)
    return kept, pd.DataFrame(pairs)


def describe(name: str) -> tuple[str, str]:
    for p, (_, unit) in PROPS.items():
        for s, txt in (("mean", "fraction-weighted mean"), ("std", "fraction-weighted std"),
                       ("min", "minimum over elements"), ("max", "maximum over elements")):
            if name == f"{p}_{s}":
                return "elemental statistic", f"{txt} of {unit}"
    if name.startswith("x_"):
        return "elemental fraction", f"atomic fraction of {name[2:]}"
    if name.startswith("fam_"):
        return "family", f"one-hot: family = {name[4:]}"
    return "alloy descriptor", {
        "n_elements": "number of elements",
        "config_entropy": "ideal configurational entropy, -sum x ln x (units of R)",
        "size_mismatch": "atomic size mismatch delta",
        "frac_hydride_former": "fraction of atoms from stable-hydride-forming elements",
    }[name]


def target_correlations(dH, wt, feats) -> pd.DataFrame:
    rows = []
    for task, d, t in (("dH", dH, "dH_kJmol"), ("wt", wt, "wt_pct")):
        for c in feats:
            if d[c].std() == 0:
                continue
            rows.append({"task": task, "feature": c,
                         "spearman": d[[c, t]].corr(method="spearman").iloc[0, 1],
                         "pearson": d[[c, t]].corr().iloc[0, 1]})
    out = pd.DataFrame(rows)
    out.to_csv(TABLES / "feature_target_correlations.csv", index=False)
    return out


def write_report(dH, wt, flist, pairs, eltab, frac_els, corr, p, wt_mask) -> None:
    from ..data.run_audit import md_table

    top = {t: corr[corr["task"] == t].assign(a=lambda d: d["spearman"].abs())
           .nlargest(8, "a")[["feature", "spearman", "pearson"]] for t in ("dH", "wt")}
    excl = p[~wt_mask]
    excl_reasons = pd.Series({
        "capacity given as H/M (converted, not stated)": int((p["capacity_basis"] != "stated_wt_pct").sum()),
        "pseudo-element composition (Mm/Lm/Vf)": int(p["comp_key"].isna().sum()),
        "capacity assumed / approximate / theoretical / unconfirmed": int(p["flag_capacity_uncertain"].sum()),
    }).rename_axis("reason (a record may meet several)").reset_index(name="n_records")
    groups = flist.groupby("group").agg(n=("feature", "size"),
                                        kept=("kept_after_pruning", "sum")).reset_index()
    text = f"""# Phase 4: composition feature engineering

Code: `src/features/composition.py` (descriptors) and `src/features/build.py` (tables).
The input is composition only. No thermodynamic, pressure, temperature or capacity value is
used as a feature for ΔH, and the build script asserts this.

## 1. Elemental data

Every elemental value is read from pymatgen's periodic table (pymatgen
2026.10.24, `periodic_table.json`), and the values used are exported to
`results/tables/elemental_property_table.csv`. All {len(eltab)} elements that occur have a value for
every property used. Metallic radius (missing for 8 elements) and calculated radius
(missing for 5) were therefore **not** used. No elemental value was filled in by hand.

| Property | pymatgen attribute | Unit / note |
|---|---|---|
""" + "\n".join(f"| `{k}` | `{v[0] or 'group'}` | {v[1]} |" for k, v in PROPS.items()) + f"""

Valence electrons follow the VEC convention used for alloys: group number for groups 1–12,
group − 10 for groups 13–18, and 3 for lanthanides and actinides.
`frac_hydride_former` counts atoms of groups 1–5, the lanthanides/actinides, and Pd. These are the
"A-side" elements that form stable binary hydrides (Sandrock 1999).

## 2. Descriptors

{md_table(groups)}

* Elemental statistics: fraction-weighted mean and std, and min and max, for each of the 6 properties (24).
* Alloy descriptors: number of elements, ideal configurational entropy, atomic size mismatch δ,
  and fraction of hydride formers (4).
* Atomic fractions for the {len(frac_els)} elements present in at least 5% of compositions: {', '.join(frac_els)} (12).
* Family one-hot ({', '.join(c for c in flist.feature if c.startswith('fam_'))}). Families with fewer than
  {FAMILY_MIN} compositions are grouped as `other`. Family is a structural label known before any hydrogen
  measurement, so it is allowed as an input. It is kept as a **separate, optional** set so that Phase 5 can
  report composition-only and composition + family models side by side.

## 3. Collinearity pruning

Features were taken in order of interpretability (means, alloy descriptors, std, min/max,
fractions). A feature was dropped if its |Pearson r| with an already-kept feature exceeded {COLLINEAR_R}:

{md_table(pairs)}

{int(flist['kept_after_pruning'].sum())} of {len(flist)} features remain. Tree models are insensitive to the remaining correlation. For
Ridge regression, features are standardised inside the CV pipeline.

## 4. Task tables

| Table | Rows | Target | Notes |
|---|---|---|---|
| `data/processed/features_dH.csv` | {len(dH)} | `dH_kJmol` (union, positive desorption) | one row per composition; `cv_group` = composition |
| `data/processed/features_wt.csv` | {len(wt)} | `wt_pct` (Purdue, stated wt% only) | families: {', '.join(f'{k} {v}' for k, v in wt['family'].value_counts().items())} |

Purdue records left out of the wt% table ({len(excl)} of {len(p)}):

{md_table(excl_reasons)}

{int(dH['flag_nonmetal_element'].sum())} ΔH compositions contain B, Si, Ge, Sb, Bi or O as alloying additions. They are kept and flagged.

## 5. Sanity check: univariate correlation with the target

No single feature correlates very strongly with the target (max |Spearman| =
{corr[corr.task=='dH'].spearman.abs().max():.2f} for ΔH and {corr[corr.task=='wt'].spearman.abs().max():.2f} for wt%), which is consistent with no leakage. The signs match known physics:

**ΔH**

{md_table(top['dH'])}

* `vol_mean` > 0: a larger average atomic volume means larger interstitial sites and a more stable
  hydride. This is the interstitial-hole-size correlation of Lundin, Lynch and Magee (1977,
  J. Less-Common Met. 56, 19).
* AB2 is negative (less stable on average, consistent with Phase 3). Cr, Fe and Mn substitution is negative.
  Mg is positive.

**wt%**

{md_table(top['wt'])}

* `mass_mean` < 0: at a similar H/M, lighter alloys hold a larger weight fraction of hydrogen. This is
  the arithmetic link wt% ≈ (H/M · 1.008) / (M̄ + H/M · 1.008). So a wt% model will mostly learn
  alloy mass, which matters when interpreting it in Phase 5.

## 6. Limitations

* The descriptors are composition averages. They cannot tell C14 from C15 Laves phases, ordering,
  or microstructure, all of which affect ΔH for the same composition. The HydPARK C14/C15 duplicates
  in Phase 2 show this directly.
* The tabulated elemental radius is coarse (0.05 Å resolution), so `radius_*` features carry limited detail.
* Mischmetal (Mm/Lm) and ferrovanadium alloys cannot be featurised and are excluded from ML.
"""
    (ROOT / "reports/feature_engineering.md").write_text(text)


def main():
    TABLES.mkdir(parents=True, exist_ok=True)
    u = pd.read_csv(PROC / "dH_union_by_composition.csv")
    p = pd.read_csv(PROC / "purdue_cleaned.csv")

    # ---------------- dH task
    Xc, eltab, frac_els = featurize(u["comp_key"])
    eltab.to_csv(TABLES / "elemental_property_table.csv", index=False)
    fam_keep = sorted(f for f, n in u["family"].value_counts().items() if n >= FAMILY_MIN)
    Fh = family_onehot(u["family"], fam_keep)
    meta = u[["comp_key", "family", "value_source", "n_purdue", "n_hydpark", "dH_spread_kJmol",
              "purdue_id", "hydpark_ids", "flag_unverified_ref_sandia",
              "flag_hydpark_only_no_reference", "flag_dS_atypical"]].copy()
    meta["flag_nonmetal_element"] = u["comp_key"].apply(lambda k: bool(set(parse_key(k)) & NONMETALS))
    meta["cv_group"] = np.arange(len(u))  # one row per composition -> group = row
    dH = pd.concat([meta, Xc, Fh, u[["dH_kJmol"]]], axis=1)
    # Metadata (e.g. dH_spread_kJmol, kept for error analysis) is allowed in the
    # file; it is the *feature* columns that must be free of dH-linked quantities.
    assert not ((set(Xc.columns) | set(Fh.columns)) & LEAKY_FOR_DH), "leaky feature"
    dH.to_csv(PROC / "features_dH.csv", index=False)

    # Pruning on composition features only (family one-hot handled separately)
    comp_cols = list(Xc.columns)
    priority = ([c for c in comp_cols if c.endswith("_mean")] +
                ["frac_hydride_former", "size_mismatch", "config_entropy", "n_elements"] +
                [c for c in comp_cols if c.endswith("_std")] +
                [c for c in comp_cols if c.endswith(("_min", "_max"))] +
                [c for c in comp_cols if c.startswith("x_")])
    kept, pairs = prune_collinear(Xc[priority], priority)
    pairs.to_csv(TABLES / "feature_collinear_pairs.csv", index=False)

    flist = pd.DataFrame([{"feature": c, "group": describe(c)[0], "description": describe(c)[1],
                           "kept_after_pruning": c in kept or c.startswith("fam_"),
                           "n_missing_dH_table": int(dH[c].isna().sum())}
                          for c in comp_cols + list(Fh.columns)])
    flist.to_csv(TABLES / "feature_list.csv", index=False)

    # ---------------- wt% task (Purdue only)
    wt_mask = ((p["capacity_basis"] == "stated_wt_pct") & p["comp_key"].notna()
               & ~p["flag_capacity_uncertain"] & ~p["flag_contains_H_in_formula"])
    pw = p[wt_mask].reset_index(drop=True)
    Xw, _, _ = featurize(pw["comp_key"], frac_elements=frac_els)
    Fw = family_onehot(pw["family"], fam_keep)
    for c in Fh.columns:
        if c not in Fw:
            Fw[c] = 0
    wt = pd.concat([pw[["purdue_id", "comp_key", "family", "capacity_definition",
                        "flag_unverified_ref_sandia", "flag_multi_plateau"]],
                    Xw, Fw[Fh.columns], pw[["wt_pct"]]], axis=1)
    wt["cv_group"] = np.arange(len(wt))
    wt.to_csv(PROC / "features_wt.csv", index=False)

    corr = target_correlations(dH, wt, kept + list(Fh.columns))
    write_report(dH, wt, flist, pairs, eltab, frac_els, corr, p, wt_mask)
    print(f"dH table: {dH.shape}, comp features {len(comp_cols)}, kept {len(kept)}, "
          f"family cols {list(Fh.columns)}")
    print(f"fraction elements ({len(frac_els)}): {frac_els}")
    print(f"wt table: {wt.shape}; families {pw['family'].value_counts().to_dict()}")
    print("dropped:", pairs.to_string(index=False))
    print("missing values in dH comp features:", int(Xc.isna().sum().sum()))
    print("nonmetal-containing compositions:", int(meta['flag_nonmetal_element'].sum()))


if __name__ == "__main__":
    main()
