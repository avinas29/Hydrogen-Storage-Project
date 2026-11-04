"""Package the already-trained ΔH model with everything needed to use it reproducibly.

No training happens here. The fitted estimator is loaded from ``results/models/dH_final.joblib``
(written by ``src.models.train``) and stored, unchanged, with:
* the exact ordered feature list and the element-fraction list used by the featuriser;
* the training compositions and their ΔH / family / provenance (for nearest-neighbour lookup);
* the applicability-domain calibration (out-of-fold residuals binned by NN distance, Phase 6);
* the documented ΔS assumption (family median and IQR of experimental Purdue ΔS, Phase 6);
* versions and SHA-256 hashes, so a stale or altered bundle can be detected.

Before writing, it checks that the featuriser reproduces the training feature table exactly and that
the model reproduces its own predictions on it.

Run:  .venv/bin/python -m src.models.export_bundle
"""
from __future__ import annotations

import hashlib
import importlib.metadata
import json
from datetime import datetime, timezone
from pathlib import Path

import joblib
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
MODEL_IN = ROOT / "results/models/dH_final.joblib"
BUNDLE = ROOT / "results/models/dH_predictor_bundle.joblib"
MANIFEST = ROOT / "results/models/dH_predictor_manifest.json"


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def main():
    from ..features.composition import featurize
    from ..thermodynamics.analysis import DOMAIN_L1, NN_BINS

    art = joblib.load(MODEL_IN)
    model, feats = art["model"], art["features"]
    frac_els = [f[2:] for f in feats if f.startswith("x_")]

    d = pd.read_csv(ROOT / "data/processed/features_dH.csv")
    # 1. featuriser reproduces the training table exactly
    X_new, _, _ = featurize(d["comp_key"], frac_elements=frac_els)
    max_diff = float(np.nanmax(np.abs(X_new[feats].to_numpy(float) - d[feats].to_numpy(float))))
    assert max_diff < 1e-9, f"featuriser drift: {max_diff}"
    # 2. model gives the same predictions on recomputed features. With n_jobs=-1 the per-tree
    # average is summed in a nondeterministic order (differences ~1e-14), so the bundle uses
    # n_jobs=1. That is a runtime setting only: the fitted trees are untouched.
    model.set_params(n_jobs=1)
    p1 = model.predict(d[feats].to_numpy(float))
    p2 = model.predict(X_new[feats].to_numpy(float))
    assert np.allclose(p1, p2, rtol=0, atol=1e-9)
    assert np.array_equal(p1, model.predict(d[feats].to_numpy(float)))  # bitwise repeatable

    cal = pd.read_csv(ROOT / "results/tables/applicability_domain_calibration.csv")
    oof = pd.read_csv(ROOT / "results/metrics/dH_oof_predictions.csv")
    oof = oof[(oof["model"] == "RandomForest") & (oof["feature_set"] == art["feature_set"])]
    oof_mean = oof.groupby("row")["pred"].mean()

    p = pd.read_csv(ROOT / "data/processed/purdue_cleaned.csv")
    ps = p[~p["flag_multi_plateau"]]
    dS = ps.groupby("family")["dS_JmolK"].quantile([0.25, 0.5, 0.75]).unstack()
    dS.columns = ["q25", "median", "q75"]
    dS.loc["(all)"] = ps["dS_JmolK"].quantile([0.25, 0.5, 0.75]).to_numpy()

    train = d[["comp_key", "family", "value_source", "dH_kJmol", "n_purdue", "n_hydpark",
               "dH_spread_kJmol", "purdue_id", "hydpark_ids"]].copy()
    train["oof_pred_mean"] = train.index.map(oof_mean)

    bundle = {
        "model": model, "features": feats, "frac_elements": frac_els,
        "feature_set": art["feature_set"], "params": art["params"],
        "train": train, "calibration": cal, "nn_bins": NN_BINS, "domain_l1": DOMAIN_L1,
        "dS_assumption": dS.reset_index().rename(columns={"index": "family"}),
    }
    joblib.dump(bundle, BUNDLE, compress=3)

    cv = pd.read_csv(ROOT / "results/metrics/dH_cv_summary.csv")
    best = cv[(cv["model"] == "RandomForest") & (cv["feature_set"] == art["feature_set"])].iloc[0]
    manifest = {
        "created_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "source_model_file": str(MODEL_IN.relative_to(ROOT)), "source_model_sha256": sha256(MODEL_IN),
        "bundle_file": str(BUNDLE.relative_to(ROOT)), "bundle_sha256": sha256(BUNDLE),
        "estimator": type(model).__name__, "hyperparameters": art["params"],
        "n_estimators": model.n_estimators, "random_state": model.random_state,
        "feature_set": art["feature_set"], "n_features": len(feats), "features": feats,
        "frac_elements": frac_els, "n_training_compositions": len(d),
        "training_table": "data/processed/features_dH.csv",
        "training_table_sha256": sha256(ROOT / "data/processed/features_dH.csv"),
        "cv_MAE_kJmol": float(best["MAE"]), "cv_MAE_sd": float(best["MAE_sd"]),
        "cv_RMSE_kJmol": float(best["RMSE"]), "cv_R2": float(best["R2"]),
        "validation": "nested grouped 5-fold CV x 3 repeats (near-composition groups)",
        "applicability_domain_L1": DOMAIN_L1, "interval": "80% (10-90% OOF residual quantiles by NN-distance bin)",
        "featuriser_check_max_abs_diff": max_diff,
        # package metadata (pymatgen's internal __version__ string differs from its pip version)
        "versions": {k: importlib.metadata.version(k) for k in ("scikit-learn", "pymatgen", "numpy", "pandas")},
    }
    MANIFEST.write_text(json.dumps(manifest, indent=2))
    print(f"bundle -> {BUNDLE.relative_to(ROOT)} ({BUNDLE.stat().st_size/1e6:.1f} MB); featuriser max diff {max_diff:g}")


if __name__ == "__main__":
    main()
