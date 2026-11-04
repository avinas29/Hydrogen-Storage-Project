"""Phase 2: composition overlap and value comparison between Purdue and HydPARK.

Matching levels
* ``exact``: identical ``comp_key`` (atomic fractions equal to 3 decimals).
* ``near``: same element set, L1 distance between atomic-fraction vectors
  <= ``NEAR_L1`` (the metric of ``Element.CompareAlloys`` in the toolbox).
  Reported separately and never used as an exact match.

Purdue materials containing Mm/Lm/Vf cannot be matched (no real composition).
"""
from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
PROCESSED = ROOT / "data/processed"
TABLES = ROOT / "results/tables"
NEAR_L1 = 0.02
SAME_MEASUREMENT_TOL_KJ = 0.5  # |dH difference| below which two entries are taken as one source value


def key_to_dict(key: str) -> dict[str, float]:
    import re
    return {el: float(x) for el, x in re.findall(r"([A-Z][a-z]?)([0-9.]+)", key)}


def l1(a: dict, b: dict) -> float:
    els = set(a) | set(b)
    return sum(abs(a.get(e, 0) - b.get(e, 0)) for e in els)


def match(p: pd.DataFrame, h: pd.DataFrame) -> pd.DataFrame:
    hk = h.dropna(subset=["comp_key"])
    h_by_set: dict[frozenset, list] = {}
    for key in hk["comp_key"].unique():
        h_by_set.setdefault(frozenset(key_to_dict(key)), []).append(key)
    rows = []
    for _, r in p.dropna(subset=["comp_key"]).iterrows():
        pk = r["comp_key"]
        pdict = key_to_dict(pk)
        candidates = h_by_set.get(frozenset(pdict), [])
        for hkey in candidates:
            dist = l1(pdict, key_to_dict(hkey))
            if dist > NEAR_L1:
                continue
            level = "exact" if hkey == pk else "near"
            for _, q in hk[hk["comp_key"] == hkey].iterrows():
                rows.append({
                    "purdue_id": r["purdue_id"], "hydpark_id": q["hydpark_id"],
                    "match_level": level, "l1_distance": round(dist, 4),
                    "comp_key_purdue": pk, "comp_key_hydpark": hkey,
                    "family_purdue": r["family"], "family_hydpark": q["family"],
                    "laves_type_hydpark": q["laves_type"], "hydpark_block": q["source_block"],
                    "formula_hydpark": q["formula_raw"],
                    "dH_purdue": r["dH_kJmol"], "dH_hydpark": q["dH_kJmol"],
                    "dS_purdue": r["dS_JmolK"], "dS_hydpark": q["dS_JmolK"],
                    "wt_purdue": r["wt_pct"], "wt_hydpark": q["wt_pct"],
                    "purdue_capacity_definition": r["capacity_definition"],
                    "purdue_capacity_basis": r["capacity_basis"],
                    "purdue_multi_plateau": r["flag_multi_plateau"],
                    "purdue_sandia_ref": r["flag_unverified_ref_sandia"],
                    "purdue_ref_ids": r["ref_ids"], "hydpark_reference": q["reference"],
                    "hydpark_dS_derived_from_TP": q["flag_dS_derived_from_TP"],
                })
    m = pd.DataFrame(rows)
    m["d_dH"] = m["dH_hydpark"] - m["dH_purdue"]
    m["d_dS"] = m["dS_hydpark"] - m["dS_purdue"]
    m["d_wt"] = m["wt_hydpark"] - m["wt_purdue"]
    m["same_doi"] = [
        isinstance(hr, str) and hr.lower() in str(pr).lower().replace(" ", "")
        for hr, pr in zip(m["hydpark_reference"], m["purdue_ref_ids"])]
    m["likely_same_source_value"] = m["d_dH"].abs() <= SAME_MEASUREMENT_TOL_KJ

    # For multi-plateau Purdue entries, compare against the closest plateau
    pl = p.set_index("purdue_id")["dH_all_plateaus_kJmol"].fillna("")
    best = []
    for pid, dh_h, dh_p in zip(m["purdue_id"], m["dH_hydpark"], m["dH_purdue"]):
        vals = [float(x) for x in pl[pid].split(";")] if pl[pid] else [dh_p]
        best.append(min(vals, key=lambda v: abs(v - dh_h)))
    m["dH_purdue_closest_plateau"] = best
    m["d_dH_closest_plateau"] = m["dH_hydpark"] - m["dH_purdue_closest_plateau"]

    pf = p.set_index("purdue_id")
    hf = h.set_index("hydpark_id")
    m["purdue_thermo_from_isotherm_fit"] = m["purdue_id"].map(pf["flag_des_thermo_from_isotherm_fit"])
    m["hydpark_suspected_entry_error"] = m["hydpark_id"].map(hf["flag_suspected_entry_error"])
    m["discrepancy_explanation"] = [explain(r) for _, r in m.iterrows()]
    return m


def explain(r) -> str:
    if abs(r["d_dH"]) <= 2:
        return "agree_within_2kJ"
    if r["hydpark_suspected_entry_error"]:
        return "hydpark_suspected_entry_error"
    if r["purdue_multi_plateau"]:
        return ("multi_plateau_hydpark_matches_other_plateau"
                if abs(r["d_dH_closest_plateau"]) <= 0.5 else "multi_plateau_no_plateau_matches")
    if r["purdue_thermo_from_isotherm_fit"]:
        return "purdue_value_refitted_from_isotherms"
    return "different_source_or_measurement"


def overlap_table(p: pd.DataFrame, h: pd.DataFrame, m: pd.DataFrame) -> pd.DataFrame:
    pk = set(p["comp_key"].dropna())
    hk = set(h["comp_key"].dropna())
    ex = m[m["match_level"] == "exact"]
    near_only = set(m.loc[m["match_level"] == "near", "comp_key_purdue"]) - set(ex["comp_key_purdue"])
    rows = [
        ("Purdue records", len(p)), ("Purdue records with real-element composition", int(p["comp_key"].notna().sum())),
        ("Purdue unique compositions", len(pk)),
        ("HydPARK records", len(h)), ("HydPARK unique compositions", len(hk)),
        ("Compositions in both (exact)", len(pk & hk)),
        ("Purdue records with exact match", int(p["comp_key"].isin(hk).sum())),
        ("HydPARK records with exact match", int(h["comp_key"].isin(pk).sum())),
        ("Exact-match record pairs", len(ex)),
        (f"Purdue compositions with only a near match (L1<={NEAR_L1})", len(near_only)),
        ("Compositions only in Purdue (exact)", len(pk - hk)),
        ("Compositions only in HydPARK (exact)", len(hk - pk)),
        ("Purdue records not matchable (pseudo-elements)", int(p["comp_key"].isna().sum())),
    ]
    return pd.DataFrame(rows, columns=["quantity", "value"])


def overlap_by_family(p, h) -> pd.DataFrame:
    hk = set(h["comp_key"].dropna())
    pk = set(p["comp_key"].dropna())
    a = p.assign(in_other=p["comp_key"].isin(hk)).groupby("family").agg(
        n=("purdue_id", "size"), n_matchable=("comp_key", lambda s: int(s.notna().sum())),
        n_exact_in_hydpark=("in_other", "sum")).reset_index()
    a.insert(0, "dataset", "Purdue")
    b = h.assign(in_other=h["comp_key"].isin(pk)).groupby(h["family"].fillna("(missing)")).agg(
        n=("hydpark_id", "size"), n_matchable=("comp_key", lambda s: int(s.notna().sum())),
        n_exact_in_hydpark=("in_other", "sum")).reset_index().rename(
        columns={"n_exact_in_hydpark": "n_exact_in_purdue"})
    b.insert(0, "dataset", "HydPARK")
    return pd.concat([a, b], ignore_index=True)


def agreement_stats(m: pd.DataFrame) -> pd.DataFrame:
    ex = m[(m["match_level"] == "exact") & ~m["purdue_multi_plateau"]]
    rows = []
    for name, sub in [("all exact pairs (single-plateau)", ex),
                      ("Purdue ref = SandiaDBRef", ex[ex["purdue_sandia_ref"]]),
                      ("Purdue ref = DOI/other", ex[~ex["purdue_sandia_ref"]]),
                      ("HydPARK block 0", ex[ex["hydpark_block"] == 0]),
                      ("HydPARK blocks 1-3", ex[ex["hydpark_block"] > 0])]:
        if len(sub) == 0:
            continue
        rows.append({
            "subset": name, "n_pairs": len(sub),
            "n_purdue": sub["purdue_id"].nunique(),
            "dH_MAE_kJmol": sub["d_dH"].abs().mean(),
            "dH_median_abs_diff": sub["d_dH"].abs().median(),
            "frac_dH_within_0.5": (sub["d_dH"].abs() <= 0.5).mean(),
            "frac_dH_within_2": (sub["d_dH"].abs() <= 2).mean(),
            "dS_MAE_JmolK": sub["d_dS"].abs().mean(),
            "wt_MAE_pct": sub["d_wt"].abs().mean(),
            "pearson_r_dH": sub[["dH_purdue", "dH_hydpark"]].corr().iloc[0, 1] if len(sub) > 2 else np.nan,
        })
    return pd.DataFrame(rows)


def build_dH_union(p: pd.DataFrame, h: pd.DataFrame) -> pd.DataFrame:
    """One row per real-element composition, for dH analysis.

    Rules (documented in reports/dataset_comparison.md):
    1. Excluded records (kept in the cleaned files, not used here): Purdue
       pseudo-element compositions; Purdue multi-plateau entries; HydPARK
       suspected entry errors; HydPARK rows the Purdue curators excluded.
    2. If the composition is in Purdue, the Purdue value is selected (curated
       file, per-value source comment).  Otherwise the median of the HydPARK
       records for that composition is used.
    3. ``dH_spread_kJmol`` = max - min over all retained records of that
       composition from both datasets; it measures inter-source scatter.
    """
    pk = p[p["comp_key"].notna() & ~p["flag_multi_plateau"]]
    hk = h[h["comp_key"].notna() & ~h["flag_suspected_entry_error"]
           & ~h["flag_excluded_by_purdue_curators"]]
    rows = []
    for key in sorted(set(pk["comp_key"]) | set(hk["comp_key"])):
        a = pk[pk["comp_key"] == key]
        b = hk[hk["comp_key"] == key]
        vals = list(a["dH_kJmol"]) + list(b["dH_kJmol"])
        if len(a):
            r = a.iloc[0]
            sel, src, fam = r["dH_kJmol"], "purdue", r["family"]
            dS = r["dS_JmolK"]
        else:
            sel, src = b["dH_kJmol"].median(), "hydpark_median"
            fam = b["family"].mode().iloc[0] if b["family"].notna().any() else np.nan
            dS = b["dS_JmolK"].median()
        rows.append({
            "comp_key": key, "family": fam, "dH_kJmol": sel, "dS_JmolK": dS,
            "value_source": src, "n_purdue": len(a), "n_hydpark": len(b),
            "dH_spread_kJmol": max(vals) - min(vals),
            "purdue_id": a["purdue_id"].iloc[0] if len(a) else "",
            "hydpark_ids": ";".join(b["hydpark_id"]),
            "hydpark_blocks": ";".join(sorted({str(x) for x in b["source_block"]})),
            "laves_type": ";".join(sorted({x for x in b["laves_type"].fillna("") if x})),
            "flag_unverified_ref_sandia": bool(a["flag_unverified_ref_sandia"].any()) if len(a) else False,
            "flag_hydpark_only_no_reference": bool(len(a) == 0 and b["reference"].isna().all()),
            "flag_dS_atypical": bool((a["flag_dS_atypical"].any() if len(a) else False)
                                     or (b["flag_dS_atypical"].all() if len(b) and not len(a) else False)),
        })
    return pd.DataFrame(rows)


def ignored_purdue_in_hydpark(h: pd.DataFrame) -> pd.DataFrame:
    """Entries the Purdue curators excluded (*.ignore) but HydPARK still contains."""
    from pymatgen.core import Composition
    from .clean import comp_key
    from .purdue_parser import parse_elements, _get, _parse_zones, _read_lines
    rows = []
    for f in sorted((ROOT / "data/raw/purdue/MetalHydrideToolbox/data").glob("*.ignore")):
        z = _parse_zones(_read_lines(f))
        comp = parse_elements(_get(z, "Elements")[0])
        key = comp_key(Composition(comp))
        th = z["zones"].get("Thermodynamics", {"zones": {}})
        dh, _ = _get(th["zones"].get("Dehydriding"), "DH")
        hits = h[h["comp_key"] == key]
        rows.append({"ignored_file": f.name, "comp_key": key,
                     "dH_in_ignored_file_kJmol": -float(dh) / 1000 if dh else np.nan,
                     "in_hydpark": len(hits) > 0,
                     "hydpark_ids": ";".join(hits["hydpark_id"]),
                     "hydpark_dH": ";".join(f"{x:g}" for x in hits["dH_kJmol"]),
                     "hydpark_blocks": ";".join(map(str, hits["source_block"]))})
    return pd.DataFrame(rows)


def main():
    p = pd.read_csv(PROCESSED / "purdue_cleaned.csv")
    h = pd.read_csv(PROCESSED / "hydpark_cleaned.csv")
    m = match(p, h)
    ov = overlap_table(p, h, m)
    fam = overlap_by_family(p, h)
    st = agreement_stats(m)
    ign = ignored_purdue_in_hydpark(h)
    ign.to_csv(TABLES / "purdue_ignored_entries_in_hydpark.csv", index=False)
    expl = (m[m["match_level"] == "exact"]["discrepancy_explanation"]
            .value_counts().rename_axis("explanation").reset_index(name="n_pairs"))
    expl.to_csv(TABLES / "cross_dataset_discrepancy_explanations.csv", index=False)
    u = build_dH_union(p, h)
    u.to_csv(PROCESSED / "dH_union_by_composition.csv", index=False)
    fam_x = pd.crosstab(m.loc[m["match_level"] == "exact", "family_purdue"],
                        m.loc[m["match_level"] == "exact", "family_hydpark"].fillna("(missing)"))
    fam_x.to_csv(TABLES / "cross_dataset_family_agreement.csv")
    print(expl.to_string(index=False))
    print("union:", u.shape, u["value_source"].value_counts().to_dict())
    print(u.groupby("family", dropna=False).size().to_dict())
    print(fam_x)
    TABLES.mkdir(parents=True, exist_ok=True)
    m.to_csv(TABLES / "cross_dataset_comparison.csv", index=False)
    ov.to_csv(TABLES / "composition_overlap.csv", index=False)
    fam.to_csv(TABLES / "composition_overlap_by_family.csv", index=False)
    st.to_csv(TABLES / "cross_dataset_agreement_stats.csv", index=False)
    return p, h, m, ov, fam, st


if __name__ == "__main__":
    pd.set_option("display.width", 220)
    p, h, m, ov, fam, st = main()
    print(ov.to_string(index=False)); print(fam.to_string(index=False)); print(st.to_string(index=False))
