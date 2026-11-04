"""Phase 5 checks: grouping, baselines, no leakage into the saved model, sane metrics."""
from pathlib import Path

import joblib
import numpy as np
import pandas as pd

from src.features.composition import LEAKY_FOR_DH
from src.models.groups import near_composition_groups
from src.models.train import family_median_predict

ROOT = Path(__file__).resolve().parents[1]
M = ROOT / "results/metrics"


def test_near_groups_link_rounding_variants():
    keys = pd.Series(["Fe0.333Mn0.366Zr0.3", "Fe0.334Mn0.366Zr0.3", "Fe0.5Ti0.5", "Fe0.333Mn0.367Zr0.3"])
    g = near_composition_groups(keys)
    assert g[0] == g[1] == g[3] and g[2] != g[0]


def test_family_median_baseline_uses_training_only():
    p = family_median_predict(np.array(["AB5", "AB5", "AB2"]), np.array([30.0, 34.0, 20.0]),
                              np.array(["AB5", "Mg"]))
    assert p[0] == 32.0 and p[1] == 30.0  # unseen family -> global median of training targets


def test_saved_model_has_no_leaky_inputs_and_predicts():
    art = joblib.load(ROOT / "results/models/dH_final.joblib")
    assert not set(art["features"]) & LEAKY_FOR_DH
    d = pd.read_csv(ROOT / "data/processed/features_dH.csv")
    lani5 = d[d["comp_key"] == "La0.167Ni0.833"]
    pred = art["model"].predict(lani5[art["features"]].to_numpy(float))[0]
    assert 20 < pred < 45   # in-sample sanity, LaNi5 is ~30-32 kJ/mol


def test_models_beat_baselines_in_cv():
    s = pd.read_csv(M / "dH_cv_summary.csv").set_index(["feature_set", "model"])
    best = s[~s.index.get_level_values("model").str.endswith("Baseline")]["MAE"].min()
    assert best < s.loc[("-", "FamilyMedianBaseline"), "MAE"] < s.loc[("-", "MeanBaseline"), "MAE"]
