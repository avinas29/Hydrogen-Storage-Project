"""Phase 5: ML for ΔH (primary) and wt% (secondary).

Validation design
* Groups: near-composition components (``groups.near_composition_groups``).
* Estimate of generalisation: nested grouped CV. Outer: GroupKFold(5, shuffled),
  repeated over 3 seeds. Inner: GroupKFold(4) grid search on the outer-train part only.
* Baselines: global mean, and family median (both fitted on the training fold only).
* Hold-out: one grouped 80/20 split (seed 42), used for parity/residual plots and
  permutation importance. Model choice is made inside the training part.
* Extra analyses (ΔH): per-family error, leave-one-family-out, within-family models,
  and data-subset sensitivity.

Run:  .venv/bin/python -m src.models.train
"""
from __future__ import annotations

import json
import time
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import GradientBoostingRegressor, RandomForestRegressor
from sklearn.inspection import permutation_importance
from sklearn.linear_model import Ridge
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.model_selection import GridSearchCV, GroupKFold, GroupShuffleSplit
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

from .groups import near_composition_groups

ROOT = Path(__file__).resolve().parents[2]
PROC = ROOT / "data/processed"
METRICS = ROOT / "results/metrics"
MODELS = ROOT / "results/models"
SEEDS = (0, 1, 2)
N_OUTER, N_INNER = 5, 4


def model_specs():
    return {
        "Ridge": (make_pipeline(StandardScaler(), Ridge()),
                  {"ridge__alpha": [0.1, 1, 10, 100, 300, 1000]}),
        "RandomForest": (RandomForestRegressor(n_estimators=300, random_state=0, n_jobs=-1),
                         {"max_features": [0.33, 0.66], "min_samples_leaf": [1, 3]}),
        "GradientBoosting": (GradientBoostingRegressor(n_estimators=300, subsample=0.8, random_state=0),
                             {"learning_rate": [0.05, 0.1], "max_depth": [2, 3]}),
    }


def metrics(y, p) -> dict:
    return {"MAE": mean_absolute_error(y, p), "RMSE": float(np.sqrt(mean_squared_error(y, p))),
            "R2": r2_score(y, p), "n": len(y)}


def family_median_predict(fam_tr, y_tr, fam_te):
    med = pd.Series(y_tr).groupby(np.asarray(fam_tr)).median()
    glob = float(np.median(y_tr))
    return np.array([med.get(f, glob) for f in fam_te])


def fit_tuned(name, X, y, groups):
    est, grid = model_specs()[name]
    gs = GridSearchCV(est, grid, cv=GroupKFold(N_INNER), scoring="neg_mean_absolute_error",
                      n_jobs=-1)
    gs.fit(X, y, groups=groups)
    return gs.best_estimator_, gs.best_params_


def nested_cv(X, y, fam, groups, models, seeds=SEEDS, tag=""):
    """Return long OOF prediction table: seed, row, model, y, pred."""
    out = []
    chosen = []
    for seed in seeds:
        cv = GroupKFold(N_OUTER, shuffle=True, random_state=seed)
        for fold, (tr, te) in enumerate(cv.split(X, y, groups)):
            preds = {"MeanBaseline": np.full(len(te), y[tr].mean()),
                     "FamilyMedianBaseline": family_median_predict(fam[tr], y[tr], fam[te])}
            for name in models:
                m, params = fit_tuned(name, X[tr], y[tr], groups[tr])
                preds[name] = m.predict(X[te])
                chosen.append({"tag": tag, "seed": seed, "fold": fold, "model": name,
                               "params": json.dumps(params)})
            for name, p in preds.items():
                out.append(pd.DataFrame({"seed": seed, "fold": fold, "row": te, "model": name,
                                         "y": y[te], "pred": p, "family": fam[te]}))
    return pd.concat(out, ignore_index=True), pd.DataFrame(chosen)


def summarise(oof: pd.DataFrame, by=("model",)) -> pd.DataFrame:
    per_seed = (oof.groupby(list(by) + ["seed"])
                .apply(lambda g: pd.Series(metrics(g["y"], g["pred"])), include_groups=False)
                .reset_index())
    agg = per_seed.groupby(list(by)).agg(
        MAE=("MAE", "mean"), MAE_sd=("MAE", "std"), RMSE=("RMSE", "mean"), RMSE_sd=("RMSE", "std"),
        R2=("R2", "mean"), R2_sd=("R2", "std"), n=("n", "first")).reset_index()
    return agg


def load_task(name):
    d = pd.read_csv(PROC / f"features_{name}.csv")
    fl = pd.read_csv(ROOT / "results/tables/feature_list.csv")
    kept = fl[fl["kept_after_pruning"]]["feature"].tolist()
    comp = [c for c in kept if not c.startswith("fam_")]
    fam_cols = [c for c in kept if c.startswith("fam_")]
    target = "dH_kJmol" if name == "dH" else "wt_pct"
    groups = near_composition_groups(d["comp_key"])
    return d, comp, fam_cols, target, groups


# --------------------------------------------------------------------------
def run_dH(log):
    d, comp, fam_cols, target, groups = load_task("dH")
    y = d[target].to_numpy()
    fam = d["family"].fillna("(missing)").to_numpy()
    feature_sets = {"composition": comp, "composition+family": comp + fam_cols}
    models = list(model_specs())
    METRICS.mkdir(parents=True, exist_ok=True)

    all_oof, all_params = [], []
    for fs_name, cols in feature_sets.items():
        t0 = time.time()
        oof, params = nested_cv(d[cols].to_numpy(float), y, fam, groups, models, tag=fs_name)
        oof["feature_set"] = fs_name
        params["feature_set"] = fs_name
        all_oof.append(oof); all_params.append(params)
        log(f"dH nested CV [{fs_name}] done in {time.time() - t0:.0f}s")
    oof = pd.concat(all_oof, ignore_index=True)
    # baselines do not depend on the feature set: keep one copy
    base = oof["model"].str.endswith("Baseline")
    oof.loc[base, "feature_set"] = "-"
    oof = oof.drop_duplicates(subset=["seed", "row", "model", "feature_set"])
    oof.to_csv(METRICS / "dH_oof_predictions.csv", index=False)
    pd.concat(all_params).to_csv(METRICS / "dH_selected_hyperparameters.csv", index=False)

    summ = summarise(oof, by=("feature_set", "model")).sort_values("MAE")
    summ.to_csv(METRICS / "dH_cv_summary.csv", index=False)
    log(summ.round(3).to_string(index=False))

    fam_summ = summarise(oof[oof["family"].isin(["AB5", "AB2", "AB", "SS", "Mg", "MIC"])],
                         by=("feature_set", "model", "family"))
    fam_summ.to_csv(METRICS / "dH_cv_by_family.csv", index=False)

    # Best configuration by mean CV MAE (non-baseline)
    best = summ[~summ["model"].str.endswith("Baseline")].iloc[0]
    best_model, best_fs = best["model"], best["feature_set"]
    log(f"best: {best_model} on {best_fs} (CV MAE {best['MAE']:.2f})")

    # ---- hold-out split for plots / importance
    cols = feature_sets[best_fs]
    X = d[cols].to_numpy(float)
    gss = GroupShuffleSplit(n_splits=1, test_size=0.2, random_state=42)
    tr, te = next(gss.split(X, y, groups))
    rows = []
    holdout_preds = pd.DataFrame({"row": te, "comp_key": d["comp_key"].iloc[te].values,
                                  "family": fam[te], "y": y[te]})
    for name in models:
        m, params = fit_tuned(name, X[tr], y[tr], groups[tr])
        p = m.predict(X[te])
        holdout_preds[name] = p
        rows.append({"model": name, **metrics(y[te], p), "params": json.dumps(params)})
        if name == best_model:
            imp = permutation_importance(m, X[te], y[te], n_repeats=30, random_state=0,
                                         scoring="neg_mean_absolute_error", n_jobs=-1)
            pd.DataFrame({"feature": cols, "importance_MAE_increase": imp.importances_mean,
                          "sd": imp.importances_std}).sort_values(
                "importance_MAE_increase", ascending=False).to_csv(
                METRICS / "dH_permutation_importance.csv", index=False)
            if hasattr(m, "feature_importances_"):
                pd.DataFrame({"feature": cols, "impurity_importance": m.feature_importances_}).sort_values(
                    "impurity_importance", ascending=False).to_csv(
                    METRICS / "dH_impurity_importance.csv", index=False)
    for nm, p in (("MeanBaseline", np.full(len(te), y[tr].mean())),
                  ("FamilyMedianBaseline", family_median_predict(fam[tr], y[tr], fam[te]))):
        holdout_preds[nm] = p
        rows.append({"model": nm, **metrics(y[te], p), "params": ""})
    hold = pd.DataFrame(rows).sort_values("MAE")
    hold.insert(0, "feature_set", best_fs)
    hold.to_csv(METRICS / "dH_holdout_metrics.csv", index=False)
    holdout_preds.to_csv(METRICS / "dH_holdout_predictions.csv", index=False)
    log("hold-out:\n" + hold.round(3).to_string(index=False))

    # ---- leave-one-family-out (composition features only: family one-hot would be constant)
    Xc = d[comp].to_numpy(float)
    lofo = []
    for f in ["AB5", "AB2", "AB", "SS", "Mg", "MIC"]:
        te = np.where(fam == f)[0]; tr = np.where(fam != f)[0]
        m, _ = fit_tuned(best_model, Xc[tr], y[tr], groups[tr])
        lofo.append({"held_out_family": f, "model": best_model,
                     **metrics(y[te], m.predict(Xc[te]))})
        lofo.append({"held_out_family": f, "model": "MeanBaseline (other families)",
                     **metrics(y[te], np.full(len(te), y[tr].mean()))})
    lofo = pd.DataFrame(lofo)
    lofo.to_csv(METRICS / "dH_leave_family_out.csv", index=False)
    log("leave-one-family-out:\n" + lofo.round(2).to_string(index=False))

    # ---- within-family models (AB5, AB2), composition features
    wf = []
    for f in ["AB5", "AB2"]:
        idx = np.where(fam == f)[0]
        o, _ = nested_cv(Xc[idx], y[idx], fam[idx], groups[idx], [best_model, "Ridge"],
                         tag=f"within_{f}")
        s = summarise(o)
        s.insert(0, "family", f)
        wf.append(s)
    wf = pd.concat(wf)
    wf.to_csv(METRICS / "dH_within_family.csv", index=False)
    log("within-family:\n" + wf.round(2).to_string(index=False))

    # ---- sensitivity to data subset (best model + baselines, 1 seed)
    hc = ~(d["flag_hydpark_only_no_reference"] | d["flag_unverified_ref_sandia"]
           | d["flag_dS_atypical"] | d["flag_nonmetal_element"])
    subsets = {"all (union)": np.ones(len(d), bool),
               "Purdue values only": (d["value_source"] == "purdue").to_numpy(),
               "HydPARK-only compositions": (d["value_source"] != "purdue").to_numpy(),
               "high-confidence (referenced, typical dS, metals only)": hc.to_numpy(),
               "dH <= 60 kJ/mol (exclude very stable)": (y <= 60)}
    sens = []
    for sname, mask in subsets.items():
        idx = np.where(mask)[0]
        o, _ = nested_cv(X[idx], y[idx], fam[idx], groups[idx], [best_model], seeds=(0,),
                         tag=sname)
        s = summarise(o)
        s.insert(0, "subset", sname)
        sens.append(s)
    sens = pd.concat(sens)
    sens.to_csv(METRICS / "dH_sensitivity.csv", index=False)
    log("sensitivity:\n" + sens.round(2).to_string(index=False))

    # ---- final model on all data (for Phase 6/8 estimates on new compositions)
    MODELS.mkdir(parents=True, exist_ok=True)
    m, params = fit_tuned(best_model, X, y, groups)
    joblib.dump({"model": m, "features": cols, "feature_set": best_fs, "params": params,
                 "cv_MAE": float(best["MAE"]), "trained_on": "dH_union_by_composition (725)"},
                MODELS / "dH_final.joblib")
    return summ


def run_wt(log):
    d, comp, fam_cols, target, groups = load_task("wt")
    y = d[target].to_numpy()
    fam = d["family"].fillna("(missing)").to_numpy()
    models = list(model_specs())
    all_oof = []
    for fs_name, cols in {"composition": comp, "composition+family": comp + fam_cols}.items():
        cols = [c for c in cols if d[c].std() > 0]
        oof, _ = nested_cv(d[cols].to_numpy(float), y, fam, groups, models, tag=fs_name)
        oof["feature_set"] = fs_name
        all_oof.append(oof)
    # Physics baseline on the same outer splits: H per metal atom fixed at the
    # training-fold family median, converted with the alloy's own mean atomic mass
    #   h = wt/(100-wt) * M / 1.008   and   wt = 100 h 1.008 / (M + h 1.008)
    Mbar = d["mass_mean"].to_numpy()
    h = y / (100 - y) * Mbar / 1.008
    phys = []
    for seed in SEEDS:
        for fold, (tr, te) in enumerate(GroupKFold(N_OUTER, shuffle=True, random_state=seed)
                                        .split(Mbar, y, groups)):
            h_te = family_median_predict(fam[tr], h[tr], fam[te])
            p = 100 * h_te * 1.008 / (Mbar[te] + h_te * 1.008)
            phys.append(pd.DataFrame({"seed": seed, "fold": fold, "row": te,
                                      "model": "PhysicsBaseline(H/M x mass)", "y": y[te],
                                      "pred": p, "family": fam[te]}))
    all_oof.append(pd.concat(phys).assign(feature_set="-"))
    oof = pd.concat(all_oof, ignore_index=True)
    base = oof["model"].str.contains("Baseline")
    oof.loc[base, "feature_set"] = "-"
    oof = oof.drop_duplicates(subset=["seed", "row", "model", "feature_set"])
    oof.to_csv(METRICS / "wt_oof_predictions.csv", index=False)
    summ = summarise(oof, by=("feature_set", "model")).sort_values("MAE")
    summ.to_csv(METRICS / "wt_cv_summary.csv", index=False)
    summarise(oof[oof["family"].isin(["AB5", "AB2", "AB"])],
              by=("feature_set", "model", "family")).to_csv(METRICS / "wt_cv_by_family.csv", index=False)
    log("wt% nested CV:\n" + summ.round(3).to_string(index=False))
    return summ


def grouping_effect(log):
    """Same nested CV with near-composition groups vs. one group per row (no grouping)."""
    d, comp, _, target, groups = load_task("dH")
    y = d[target].to_numpy(); fam = d["family"].fillna("(missing)").to_numpy()
    X = d[comp].to_numpy(float)
    rows = []
    for label, g in (("near-composition groups", groups), ("ungrouped (one group per row)", np.arange(len(d)))):
        o, _ = nested_cv(X, y, fam, g, ["RandomForest"], seeds=SEEDS, tag=label)
        s = summarise(o)
        s.insert(0, "cv_grouping", label)
        rows.append(s[s["model"] == "RandomForest"])
    out = pd.concat(rows)
    out.to_csv(METRICS / "dH_grouping_effect.csv", index=False)
    log("grouping effect:\n" + out.round(3).to_string(index=False))


def main():
    lines = []

    def log(s):
        print(s, flush=True)
        lines.append(s)

    import sys
    t0 = time.time()
    if "--grouping-only" in sys.argv:
        grouping_effect(log)
        return
    if "--wt-only" not in sys.argv:
        run_dH(log)
        grouping_effect(log)
    run_wt(log)
    log(f"total {time.time() - t0:.0f}s")
    (METRICS / "train_log.txt").write_text("\n".join(lines))


if __name__ == "__main__":
    main()
