"""Phase 8: mobile vs stationary screening of Purdue metal hydrides.

Method (all thresholds and weights are listed in CRITERIA / WEIGHTS and exported):
1. Candidates: all 337 Purdue materials (experimental ΔH/ΔS; reported capacity). Mischmetal
   alloys ARE included here (they need no elemental descriptors).
2. Data-quality gate (both applications): exclude atypical ΔS (|ΔS| outside 70-170) and
   capacities marked assumed / unconfirmed.
3. Hard constraints per application (engineering requirements, below).
4. Weighted score of normalised criteria among the candidates that pass (0 = worst, 1 = best).
5. Sensitivity: random weights (Dirichlet), one-at-a-time weight changes, and
   alternative constraint thresholds.

Everything is MATERIAL-LEVEL. System capacity (vessel, heat exchanger, bed porosity, balance of
plant) is much lower and is not modelled.

Run:  .venv/bin/python -m src.screening.screen
"""
from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

from ..thermodynamics.vant_hoff import M_H2, T_at_P, peq_bar

ROOT = Path(__file__).resolve().parents[2]
PROC = ROOT / "data/processed"
TABLES = ROOT / "results/tables"

PRECIOUS = {"Pd", "Pt", "Rh", "Ir", "Ru", "Ag", "Au"}
COSTLY = {"La", "Ce", "Pr", "Nd", "Sm", "Eu", "Gd", "Tb", "Dy", "Ho", "Er", "Tm", "Yb", "Lu", "Y",
          "Sc", "Mm", "Lm", "Co", "Hf", "Ta", "Nb", "Th", "U", "Ga", "Ge", "In", "V", "Vf"}
# Qualitative element cost/supply indicator, NOT a price model: precious metals 0, rare earths
# (incl. mischmetal), Co, V/ferrovanadium and minor metals 0.5, common structural metals
# (Fe, Ti, Mn, Ni, Cr, Al, Cu, Mg, Ca, Zr, ...) 1. Tested in the sensitivity analysis (weight -> 0).
# Family-level kinetics class from Phase 7 (comparable-group activation energies):
# AB5/AB2/AB/AB3 absorption Ea ~20-35 kJ/mol -> fast near ambient; complex ~92; Mg ~132.
KINETICS_CLASS = {"AB5": 1.0, "AB2": 1.0, "AB": 1.0, "AB3": 1.0, "Complex": 0.25, "Mg": 0.0}
KINETICS_NO_DATA = 0.5   # SS, A2B7, Misc: no comparable records -> neutral, flagged

CRITERIA = {
    "mobile": {
        "T1_full_max_C": 80.0,      # all H released at >= 1 bar with PEMFC waste heat (60-80 C)
        "P50_max_bar": 50.0,        # hot-day (50 C) plateau pressure limit for the tank
        "Pcharge25_max_bar": 100.0,  # charging pressure at 25 C (refuelling compressor)
    },
    "stationary": {
        "T1_full_max_C": 150.0,     # low-grade industrial / electrolyser + boiler heat
        "P25_max_bar": 10.0,        # low-pressure storage at room temperature (safety)
        "P50_max_bar": 30.0,
        "Pcharge25_max_bar": 30.0,  # pressurised PEM electrolyser delivery pressure, no compressor
    },
}
WEIGHTS = {
    "mobile": {"capacity": 0.35, "heat": 0.20, "kinetics": 0.15, "hysteresis": 0.10,
               "pressure_fit": 0.10, "cost": 0.10},
    "stationary": {"cost": 0.25, "pressure_safety": 0.20, "hysteresis": 0.15, "kinetics": 0.10,
                   "heat": 0.10, "capacity": 0.10, "pressure_fit": 0.10},
}


def elements_of(comp: str) -> set[str]:
    return {p.split(":")[0] for p in str(comp).split(";") if p}


def cost_class(els: set[str]) -> tuple[float, str]:
    if els & PRECIOUS:
        return 0.0, "precious metal"
    if els & COSTLY:
        return 0.5, "rare earth / Co / minor metal"
    return 1.0, "common metals"


def candidate_table() -> pd.DataFrame:
    p = pd.read_csv(PROC / "purdue_cleaned.csv")
    vh = pd.read_csv(TABLES / "vant_hoff_purdue.csv")
    raw = pd.read_csv(ROOT / "data/interim/purdue_extracted.csv").set_index("material_id")
    rows = []
    for _, r in p.iterrows():
        pl = vh[vh["purdue_id"] == r["purdue_id"]].sort_values("plateau")
        dH, dS = pl["dH_kJmol"].to_numpy(), pl["dS_JmolK"].to_numpy()
        if len(pl) > 1:
            w = np.array([float(x) for x in str(raw.loc[r["purdue_id"], "des_widths_all"]).split(";")])
            w = w / w.sum()
        else:
            w = np.array([1.0])
        T1 = T_at_P(1.0, dH, dS) - 273.15
        P25 = peq_bar(298.15, dH, dS)
        P50 = peq_bar(323.15, dH, dS)
        single = pl.iloc[0]
        pabs = single["Pabs_bar_25C"] if len(pl) == 1 else np.nan
        els = elements_of(r["composition_raw"])
        cval, clab = cost_class(els)
        kin = KINETICS_CLASS.get(r["family"], KINETICS_NO_DATA)
        rho = r["rho_kg_m3"]
        wt = r["wt_pct"] / 100
        rows.append({
            "purdue_id": r["purdue_id"], "family": r["family"], "n_plateaus": len(pl),
            "wt_pct": r["wt_pct"], "capacity_definition": r["capacity_definition"],
            "dH_kJmol_weighted": float(np.sum(w * dH)), "dS_JmolK_weighted": float(np.sum(w * dS)),
            "T1_full_C": float(T1.max()), "T1_first_C": float(T1.min()),
            "P25_bar": float(P25.max()), "P50_bar": float(P50.max()),
            "Pabs25_bar": pabs, "abs_source": single["abs_source"] if len(pl) == 1 else "not_available",
            "Pcharge25_bar": pabs if np.isfinite(pabs) else float(P25.max()),
            "flag_charge_pressure_from_Pdes": not np.isfinite(pabs),
            "hyst_ln_Pa_Pd_25C": float(np.log(single["hysteresis_ratio_Pa_Pd_25C"])) if len(pl) == 1 and np.isfinite(single["hysteresis_ratio_Pa_Pd_25C"]) else np.nan,
            "heat_MJ_per_kgH2": float(np.sum(w * dH)) / M_H2,
            "kinetics_class": kin, "flag_kinetics_no_family_data": r["family"] not in KINETICS_CLASS,
            "cost_class": cval, "cost_label": clab,
            "rho_kg_m3_stated": rho,
            "vol_H_kg_m3_solid": rho * wt / (1 - wt) if np.isfinite(rho) else np.nan,
            "flag_dS_atypical": bool(r["flag_dS_atypical"]),
            "flag_unverified_ref_sandia": bool(r["flag_unverified_ref_sandia"]),
            "flag_thermo_refit_from_isotherms": bool(r["flag_des_thermo_from_isotherm_fit"]),
            "flag_pseudo_element": bool(r["flag_pseudo_element"]),
        })
    c = pd.DataFrame(rows)
    c["data_quality_pass"] = ~c["flag_dS_atypical"] & ~c["capacity_definition"].isin(["assumed", "unconfirmed_source"])
    # Cross-check with Phase 7: material's own PCI curves give a ΔH > 5 kJ/mol away from the .mh value
    fits = pd.read_csv(TABLES / "pci_vant_hoff_fits.csv")
    bad = fits[(fits["mode"] == "des") & ~fits["multi_plateau_excluded"] & (fits["d_dH"].abs() > 5)]
    c["flag_pci_dH_inconsistent"] = c["purdue_id"].isin(bad["material_id"])
    # Different files carrying identical thermodynamics and capacity (likely duplicated source data)
    key = c[["dH_kJmol_weighted", "dS_JmolK_weighted", "wt_pct"]].round(4).astype(str).agg("|".join, axis=1)
    c["flag_identical_values_other_file"] = key.duplicated(keep=False)
    return c


def apply_constraints(c: pd.DataFrame, app: str, crit: dict | None = None) -> pd.DataFrame:
    crit = crit or CRITERIA[app]
    c = c.copy()
    reasons = []
    for _, r in c.iterrows():
        why = []
        if not r["data_quality_pass"]:
            why.append("data quality")
        if r["T1_full_C"] > crit["T1_full_max_C"]:
            why.append(f"T(1 bar) {r['T1_full_C']:.0f} > {crit['T1_full_max_C']:.0f} °C")
        if "P25_max_bar" in crit and r["P25_bar"] > crit["P25_max_bar"]:
            why.append(f"P(25 °C) {r['P25_bar']:.3g} > {crit['P25_max_bar']:g} bar")
        if r["P50_bar"] > crit["P50_max_bar"]:
            why.append(f"P(50 °C) {r['P50_bar']:.3g} > {crit['P50_max_bar']:g} bar")
        if r["Pcharge25_bar"] > crit["Pcharge25_max_bar"]:
            why.append(f"charging P(25 °C) {r['Pcharge25_bar']:.3g} > {crit['Pcharge25_max_bar']:g} bar")
        reasons.append("; ".join(why))
    c[f"{app}_fail_reasons"] = reasons
    c[f"{app}_pass"] = c[f"{app}_fail_reasons"] == ""
    return c


def _minmax(x: pd.Series, higher_better=True) -> pd.Series:
    lo, hi = x.min(), x.max()
    s = (x - lo) / (hi - lo) if hi > lo else pd.Series(0.5, index=x.index)
    return s if higher_better else 1 - s


def criterion_scores(c: pd.DataFrame) -> pd.DataFrame:
    """Normalised criterion scores among the given candidate set (0..1, 1 = best)."""
    s = pd.DataFrame(index=c.index)
    s["capacity"] = _minmax(c["wt_pct"])
    s["heat"] = _minmax(c["heat_MJ_per_kgH2"], higher_better=False)
    s["kinetics"] = c["kinetics_class"]
    h = c["hyst_ln_Pa_Pd_25C"]
    s["hysteresis"] = _minmax(h, higher_better=False).fillna(0.5)  # missing -> neutral (flagged)
    # pressure_fit: 1 inside 1-10 bar at 25 C, falling linearly to 0 one decade outside
    lp = np.log10(c["P25_bar"])
    dist = np.where(lp < 0, -lp, np.where(lp > 1, lp - 1, 0))
    s["pressure_fit"] = np.clip(1 - dist, 0, 1)
    s["pressure_safety"] = _minmax(np.log10(c["P25_bar"]), higher_better=False)
    s["cost"] = c["cost_class"]
    return s


def score(c: pd.DataFrame, s: pd.DataFrame, weights: dict) -> pd.Series:
    w = pd.Series(weights) / sum(weights.values())
    return (s[w.index] * w).sum(axis=1)


def rank_app(c_all: pd.DataFrame, app: str, weights=None, crit=None) -> pd.DataFrame:
    c = apply_constraints(c_all, app, crit)
    cand = c[c[f"{app}_pass"]].copy()
    s = criterion_scores(cand)
    w = weights or WEIGHTS[app]
    cand["score"] = score(cand, s, w)
    for k in w:
        cand[f"contrib_{k}"] = s[k] * w[k] / sum(w.values())
        cand[f"crit_{k}"] = s[k]
    cand = cand.sort_values("score", ascending=False)
    cand["rank"] = np.arange(1, len(cand) + 1)
    return cand


# --------------------------------------------------------------------------
def sensitivity(c_all: pd.DataFrame, app: str, n=2000, seed=0) -> tuple[pd.DataFrame, pd.DataFrame]:
    base = rank_app(c_all, app)
    c = apply_constraints(c_all, app)
    cand = c[c[f"{app}_pass"]].copy()
    s = criterion_scores(cand)
    keys = list(WEIGHTS[app])
    bw = np.array([WEIGHTS[app][k] for k in keys])
    rng = np.random.default_rng(seed)
    ranks = {"perturbed (Dirichlet, base x 20)": [], "random (uniform Dirichlet)": []}
    for label, alpha in (("perturbed (Dirichlet, base x 20)", bw * 20), ("random (uniform Dirichlet)", np.ones(len(keys)))):
        for _ in range(n):
            w = rng.dirichlet(alpha)
            sc = (s[keys].to_numpy() * w).sum(axis=1)
            order = (-sc).argsort().argsort() + 1
            ranks[label].append(order)
    rows = []
    for label, R in ranks.items():
        R = np.array(R)
        for j, pid in enumerate(cand["purdue_id"]):
            rows.append({"scheme": label, "purdue_id": pid, "family": cand["family"].iloc[j],
                         "base_rank": int(base.set_index("purdue_id").loc[pid, "rank"]),
                         "median_rank": float(np.median(R[:, j])), "rank_q10": float(np.quantile(R[:, j], 0.1)),
                         "rank_q90": float(np.quantile(R[:, j], 0.9)),
                         "p_top5": float((R[:, j] <= 5).mean()), "p_top10": float((R[:, j] <= 10).mean())})
    mc = pd.DataFrame(rows)
    # one-at-a-time: drop each criterion / double it
    from scipy.stats import kendalltau
    oat = []
    top_base = base["purdue_id"].head(10).tolist()
    for k in keys:
        for factor in (0.0, 2.0):
            w = dict(WEIGHTS[app]); w[k] = w[k] * factor
            r = rank_app(c_all, app, weights=w)
            m = base[["purdue_id", "rank"]].merge(r[["purdue_id", "rank"]], on="purdue_id", suffixes=("_base", "_new"))
            tau = kendalltau(m["rank_base"], m["rank_new"]).statistic
            oat.append({"criterion": k, "weight_factor": factor, "kendall_tau_vs_base": tau,
                        "top10_overlap": len(set(top_base) & set(r["purdue_id"].head(10))),
                        "new_top3": "; ".join(r["purdue_id"].head(3))})
    return mc, pd.DataFrame(oat)


def constraint_scenarios(c_all: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for app, key, values in (("mobile", "T1_full_max_C", [60, 80, 100]),
                             ("mobile", "P50_max_bar", [30, 50, 100]),
                             ("stationary", "T1_full_max_C", [80, 150, 350]),
                             ("stationary", "P25_max_bar", [5, 10, 20])):
        for v in values:
            crit = dict(CRITERIA[app]); crit[key] = v
            r = rank_app(c_all, app, crit=crit)
            rows.append({"application": app, "threshold": key, "value": v, "n_pass": len(r),
                         "families_passing": ", ".join(f"{f} {n}" for f, n in r["family"].value_counts().items()),
                         "top3": "; ".join(r["purdue_id"].head(3))})
    return pd.DataFrame(rows)


def main():
    pd.set_option("display.width", 230); pd.set_option("display.max_colwidth", 70)
    c = candidate_table()
    for app in ("mobile", "stationary"):
        c = apply_constraints(c, app)
    c.to_csv(TABLES / "screening_candidates.csv", index=False)
    crit_rows = [{"application": a, "criterion": k, "value": v, "type": "hard constraint"} for a, d in CRITERIA.items() for k, v in d.items()]
    crit_rows += [{"application": a, "criterion": k, "value": v, "type": "weight"} for a, d in WEIGHTS.items() for k, v in d.items()]
    pd.DataFrame(crit_rows).to_csv(TABLES / "screening_criteria.csv", index=False)

    for app in ("mobile", "stationary"):
        r = rank_app(c, app)
        r.to_csv(TABLES / f"screening_{app}_ranking.csv", index=False)
        mc, oat = sensitivity(c, app)
        mc.to_csv(TABLES / f"screening_{app}_sensitivity_mc.csv", index=False)
        oat.to_csv(TABLES / f"screening_{app}_sensitivity_oat.csv", index=False)
        print(f"\n=== {app}: {len(r)} pass of {len(c)} (data-quality pass {c.data_quality_pass.sum()})")
        print(r[["rank", "purdue_id", "family", "wt_pct", "T1_full_C", "P25_bar", "heat_MJ_per_kgH2", "cost_label", "score"]].head(12).round(2).to_string(index=False))
        print(r["family"].value_counts().to_dict())
        print(oat.round(2).to_string(index=False))
    sc = constraint_scenarios(c)
    sc.to_csv(TABLES / "screening_constraint_scenarios.csv", index=False)
    print(sc.to_string(index=False))


if __name__ == "__main__":
    main()
