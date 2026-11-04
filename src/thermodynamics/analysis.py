"""Phase 6: Van't Hoff analysis of the Purdue materials plus ML-estimated substitution series.

Outputs (results/tables/)
* vant_hoff_purdue.csv: every Purdue plateau, experimental ΔH/ΔS only
* vant_hoff_representative.csv: selected materials for the report and slides
* vant_hoff_ml_series.csv: substitution series, experimental vs ML estimate (flagged)

Run:  .venv/bin/python -m src.thermodynamics.analysis
"""
from __future__ import annotations

from pathlib import Path

import joblib
import numpy as np
import pandas as pd

from ..data.clean import comp_key
from ..features.composition import featurize, parse_key
from .vant_hoff import (P0_BAR, T_REF_SLOPE, absorption_pressure_bar, heat_fraction_of_LHV,
                        heat_kJ_per_kg_material, heat_MJ_per_kg_H2, peq_bar, plateau_pressure_span,
                        T_at_P)

ROOT = Path(__file__).resolve().parents[2]
PROC = ROOT / "data/processed"
TABLES = ROOT / "results/tables"
M = ROOT / "results/metrics"

T_GRID_C = [-20, 0, 25, 50, 80, 100, 150, 200, 300]
P_GRID_BAR = [1, 5, 10, 30, 100]

REPRESENTATIVE = {
    "La[1]Ni[5]": "LaNi5",
    "Mm[1]Ni[4.5]Al[0.5]": "MmNi4.5Al0.5",
    "Ca[1]Ni[5]": "CaNi5",
    "Ti[1]Fe[1]": "TiFe",
    "Ti[1]Fe[0.9]Mn[0.1]": "TiFe0.9Mn0.1",
    "Ti[1.01]Cr[1.06]Mn[1]": "TiCrMn (Ti1.01Cr1.06Mn)",
    "HydralloyC2": "Hydralloy C2 (Ti-Mn-V-Fe AB2)",
    "Ti[1]Mn[1.5]": "TiMn1.5",
    "Zr[1]Mn[2]": "ZrMn2",
    "V[0.855]Ti[0.095]Fe[0.05]": "V0.855Ti0.095Fe0.05 (BCC SS)",
    "Mg[2]Ni[1]": "Mg2Ni",
    "Mg[1]": "MgH2",
    "Na[1]Al[1]H[1]": "NaAlH4",
}
# Plateaus are stored in order of capacity fraction (``centers`` 0.2, 0.72 in the .mh file),
# i.e. low H content first. For Ti-doped NaAlH4 the low-H plateau is Na3AlH6 -> NaH + Al and the
# high-H plateau is NaAlH4 -> 1/3 Na3AlH6 + 2/3 Al (Bogdanovic et al., J. Alloys Compd. 302 (2000) 36).
PLATEAU_NAMES = {("Na[1]Al[1]H[1]", 1): "NaAlH4: Na3AlH6→NaH step (low-H plateau)",
                 ("Na[1]Al[1]H[1]", 2): "NaAlH4: NaAlH4→Na3AlH6 step (high-H plateau)"}


def plateau_rows(p: pd.DataFrame) -> pd.DataFrame:
    """One row per (material, plateau). Single-plateau entries give one row."""
    rows = []
    for _, r in p.iterrows():
        if r["flag_multi_plateau"]:
            dHs = [float(x) for x in str(r["dH_all_plateaus_kJmol"]).split(";")]
            dSs = [float(x) for x in str(r["dS_all_plateaus_JmolK"]).split(";")]
        else:
            dHs, dSs = [r["dH_kJmol"]], [r["dS_JmolK"]]
        for k, (dH, dS) in enumerate(zip(dHs, dSs), 1):
            rows.append({"purdue_id": r["purdue_id"], "family": r["family"], "plateau": k,
                         "n_plateaus": len(dHs), "dH_kJmol": dH, "dS_JmolK": dS,
                         "wt_pct_reported": r["wt_pct"], "capacity_definition": r["capacity_definition"],
                         "abs_dH_kJmol": r["abs_dH_kJmol"] if len(dHs) == 1 else np.nan,
                         "abs_dS_JmolK": r["abs_dS_JmolK"] if len(dHs) == 1 else np.nan,
                         "ln_Pa_Pd": r["hysteresis_ln_Pa_Pd"] if len(dHs) == 1 else np.nan,
                         "flag_unverified_ref_sandia": r["flag_unverified_ref_sandia"],
                         "flag_thermo_from_isotherm_fit": r["flag_des_thermo_from_isotherm_fit"],
                         "flag_dS_atypical": r["flag_dS_atypical"]})
    return pd.DataFrame(rows)


def compute_table(pl: pd.DataFrame, slopes: pd.Series) -> pd.DataFrame:
    out = pl.copy()
    dH, dS = out["dH_kJmol"].to_numpy(), out["dS_JmolK"].to_numpy()
    for t in T_GRID_C:
        out[f"Pdes_bar_{t}C"] = peq_bar(t + 273.15, dH, dS)
    for P in P_GRID_BAR:
        out[f"T_C_at_{P}bar"] = T_at_P(P, dH, dS) - 273.15
    out["window_1_10bar_Tlow_C"] = out["T_C_at_1bar"]
    out["window_1_10bar_Thigh_C"] = out["T_C_at_10bar"]
    out["heat_MJ_per_kgH2"] = heat_MJ_per_kg_H2(dH)
    out["heat_pct_of_LHV"] = 100 * heat_fraction_of_LHV(dH)
    out["heat_kJ_per_kg_material_full_charge"] = heat_kJ_per_kg_material(dH, out["wt_pct_reported"])

    pa, src = [], []
    for _, r in out.iterrows():
        v, s = absorption_pressure_bar(298.15, r["dH_kJmol"], r["dS_JmolK"], r["abs_dH_kJmol"],
                                       r["abs_dS_JmolK"], r["ln_Pa_Pd"])
        pa.append(float(v)); src.append(s)
    out["Pabs_bar_25C"] = pa
    out["abs_source"] = src
    out["hysteresis_ratio_Pa_Pd_25C"] = out["Pabs_bar_25C"] / out["Pdes_bar_25C"]
    out["abs_heat_MJ_per_kgH2"] = heat_MJ_per_kg_H2(out["abs_dH_kJmol"])

    out["slope_stated"] = out["purdue_id"].map(slopes)
    out.loc[out["n_plateaus"] > 1, "slope_stated"] = np.nan  # per-plateau slopes not mapped here
    lo, hi = plateau_pressure_span(298.15, dH, dS, out["slope_stated"].to_numpy())
    out["Pdes_bar_25C_x0.1"] = lo
    out["Pdes_bar_25C_x0.9"] = hi
    return out


# --------------------------------------------------------------------------
SERIES = {
    "LaNi5-xAlx (AB5)": ("AB5", [{"La": 1, "Ni": 5 - x, "Al": x} for x in np.round(np.arange(0, 1.01, 0.1), 2)], "x(Al)"),
    "LaNi5-xSnx (AB5)": ("AB5", [{"La": 1, "Ni": 5 - x, "Sn": x} for x in np.round(np.arange(0, 0.51, 0.05), 2)], "x(Sn)"),
    "TiFe1-xMnx (AB)": ("AB", [{"Ti": 1, "Fe": 1 - x, "Mn": x} for x in np.round(np.arange(0, 0.31, 0.05), 2)], "x(Mn)"),
    "TiCr2-xMnx (AB2)": ("AB2", [{"Ti": 1, "Cr": 2 - x, "Mn": x} for x in np.round(np.arange(0, 1.01, 0.1), 2)], "x(Mn)"),
}


NN_BINS = [0, 0.05, 0.1, 0.15, 0.2, 0.3, 0.5, 2.0]
DOMAIN_L1 = 0.15  # applicability limit, chosen from the calibration table (error < overall MAE)


def _l1(a: dict, b: dict) -> float:
    return sum(abs(a.get(e, 0) - b.get(e, 0)) for e in set(a) | set(b))


def applicability_calibration(d: pd.DataFrame, resid: pd.Series) -> tuple[np.ndarray, pd.DataFrame]:
    """NN distance of each training row to compositions outside its own CV group, and the
    out-of-fold residual distribution per distance bin."""
    from ..models.groups import near_composition_groups
    C = [parse_key(k) for k in d["comp_key"]]
    g = near_composition_groups(d["comp_key"])
    nn = np.array([min(_l1(C[i], C[j]) for j in range(len(C)) if g[j] != g[i]) for i in range(len(C))])
    b = pd.cut(nn, NN_BINS)
    cal = pd.DataFrame({"bin": b, "res": resid.to_numpy(), "abs": resid.abs().to_numpy()}).groupby(
        "bin", observed=False).agg(n=("res", "size"), MAE=("abs", "mean"), median_abs=("abs", "median"),
                                   res_q10=("res", lambda s: s.quantile(0.1)),
                                   res_q90=("res", lambda s: s.quantile(0.9))).reset_index()
    cal["bin"] = cal["bin"].astype(str)
    return nn, cal


def ml_series(p_single: pd.DataFrame) -> pd.DataFrame:
    from pymatgen.core import Composition
    art = joblib.load(ROOT / "results/models/dH_final.joblib")
    feats = art["features"]
    frac_els = [f[2:] for f in feats if f.startswith("x_")]
    d = pd.read_csv(PROC / "features_dH.csv")
    oof = pd.read_csv(M / "dH_oof_predictions.csv")
    oof = oof[(oof["model"] == type(art["model"]).__name__.replace("Regressor", ""))
              & (oof["feature_set"] == art["feature_set"])]
    oof_mean = oof.groupby("row")["pred"].mean()  # mean over the 3 CV repeats
    d["oof_pred"] = d.index.map(oof_mean)
    resid = (d["oof_pred"] - d["dH_kJmol"])
    train = [parse_key(k) for k in d["comp_key"]]
    nn_train, cal = applicability_calibration(d, resid)
    cal.to_csv(TABLES / "applicability_domain_calibration.csv", index=False)
    bins = pd.IntervalIndex.from_breaks(NN_BINS)
    group_of = dict(zip(d["comp_key"], range(len(d))))

    dS_fam = p_single.groupby("family")["dS_JmolK"].quantile([0.25, 0.5, 0.75]).unstack()
    rows = []
    for sname, (fam, comps, xlab) in SERIES.items():
        keys = [comp_key(Composition(c)) for c in comps]
        X, _, _ = featurize(pd.Series(keys), frac_elements=frac_els)
        pred_all = art["model"].predict(X[feats].to_numpy(float))
        for c, k, pa in zip(comps, keys, pred_all):
            xval = [v for e, v in c.items() if e not in ("La", "Ti") and e not in ("Ni", "Fe", "Cr")]
            xval = xval[0] if xval else 0.0
            known = d.index[d["comp_key"] == k]
            ck = parse_key(k)
            # in-data points: distance as seen in CV (outside own group); new points: to any training row
            nn = (nn_train[group_of[k]] if k in group_of
                  else min(_l1(ck, t) for t in train))
            row_cal = cal.iloc[min(bins.get_indexer([nn])[0], len(cal) - 1)]
            q10, q90 = row_cal["res_q10"], row_cal["res_q90"]
            if len(known):
                i = known[0]
                dH_pred, kind = d.loc[i, "oof_pred"], "out-of-fold prediction (composition in data)"
                dH_exp = d.loc[i, "dH_kJmol"]
                dS_exp = d.loc[i, "dS_JmolK"] if "dS_JmolK" in d else np.nan
            else:
                dH_pred, kind, dH_exp, dS_exp = pa, "ESTIMATE: final model, composition not in data", np.nan, np.nan
            dS_lo, dS_med, dS_hi = dS_fam.loc[fam, 0.25], dS_fam.loc[fam, 0.5], dS_fam.loc[fam, 0.75]
            # T(1 bar) estimate band: ΔH interval (q10..q90 of family OOF residuals) × ΔS IQR
            dH_lo, dH_hi = dH_pred - q90, dH_pred - q10   # residual = pred - true
            corners = [T_at_P(1, h, s) - 273.15 for h in (dH_lo, dH_hi) for s in (dS_lo, dS_hi)]
            rows.append({
                "series": sname, "family": fam, "x_label": xlab, "x": xval, "comp_key": k,
                "in_data": bool(len(known)), "prediction_type": kind,
                "dH_experimental": dH_exp, "dH_predicted": dH_pred,
                "dH_interval_low": dH_lo, "dH_interval_high": dH_hi,
                "dS_assumed_family_median": dS_med, "dS_assumed_IQR": f"{dS_lo:.0f}-{dS_hi:.0f}",
                "T1bar_C_estimate": T_at_P(1, dH_pred, dS_med) - 273.15,
                "T1bar_C_band_low": min(corners), "T1bar_C_band_high": max(corners),
                # contributions: ΔH interval at median ΔS, and ΔS IQR at predicted ΔH
                "T1bar_width_from_dH_K": float(T_at_P(1, dH_hi, dS_med) - T_at_P(1, dH_lo, dS_med)),
                "T1bar_width_from_dS_K": float(T_at_P(1, dH_pred, dS_lo) - T_at_P(1, dH_pred, dS_hi)),
                "Peq25_bar_estimate": peq_bar(298.15, dH_pred, dS_med),
                "nn_L1_distance": nn, "in_applicability_domain": nn <= DOMAIN_L1,
                "applicability_threshold_L1": DOMAIN_L1, "error_bin_MAE": row_cal["MAE"],
                "label": "ESTIMATE (ML ΔH + assumed family-median ΔS); not experimentally validated",
            })
    return pd.DataFrame(rows)


def main():
    p = pd.read_csv(PROC / "purdue_cleaned.csv")
    raw = pd.read_csv(ROOT / "data/interim/purdue_extracted.csv").set_index("material_id")
    slopes = raw["des_slope"]
    pl = plateau_rows(p)
    tab = compute_table(pl, slopes)
    tab.to_csv(TABLES / "vant_hoff_purdue.csv", index=False)

    rep = tab[tab["purdue_id"].isin(REPRESENTATIVE)].copy()
    rep.insert(1, "name", rep["purdue_id"].map(REPRESENTATIVE))
    rep["name"] = [PLATEAU_NAMES.get((pid, k), nm if n == 1 else f"{nm} plateau {k}/{n}")
                   for pid, k, n, nm in zip(rep["purdue_id"], rep["plateau"], rep["n_plateaus"], rep["name"])]
    rep = rep.set_index("purdue_id").loc[list(REPRESENTATIVE)].reset_index()
    rep.to_csv(TABLES / "vant_hoff_representative.csv", index=False)

    ser = ml_series(p[~p["flag_multi_plateau"]])
    ser.to_csv(TABLES / "vant_hoff_ml_series.csv", index=False)

    cols = ["name", "dH_kJmol", "dS_JmolK", "Pdes_bar_25C", "T_C_at_1bar", "T_C_at_10bar",
            "heat_MJ_per_kgH2", "heat_pct_of_LHV", "Pabs_bar_25C", "abs_source", "slope_stated"]
    pd.set_option("display.width", 250)
    print(rep[cols].round(3).to_string(index=False))
    print(tab.shape, tab["abs_source"].value_counts().to_dict())
    print(ser[["series", "x", "in_data", "dH_experimental", "dH_predicted", "T1bar_C_estimate",
               "T1bar_C_band_low", "T1bar_C_band_high", "nn_L1_distance", "in_applicability_domain"]].round(2).to_string(index=False))


if __name__ == "__main__":
    main()
