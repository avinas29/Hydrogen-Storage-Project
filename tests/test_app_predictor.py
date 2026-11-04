"""Explorer app: composition parsing, feature/prediction consistency with training, artifact integrity."""
import hashlib
import json
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
import pytest

from src.app.predictor import BUNDLE_PATH, MANIFEST_PATH, CompositionError, Predictor, parse_composition

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture(scope="module")
def P():
    return Predictor()


@pytest.fixture(scope="module")
def train_table():
    return pd.read_csv(ROOT / "data/processed/features_dH.csv")


# ---------------- parsing
@pytest.mark.parametrize("text,expected", [
    ("LaNi4.2Al0.8", {"La": 1, "Ni": 4.2, "Al": 0.8}),
    ("TiFe0.75Mn0.25", {"Ti": 1, "Fe": 0.75, "Mn": 0.25}),
    ("Ti[1]Fe[0.9]Mn[0.1]", {"Ti": 1, "Fe": 0.9, "Mn": 0.1}),
    ("(Ti0.8Zr0.2)(Cr0.5Mn0.5)2", {"Ti": 0.8, "Zr": 0.2, "Cr": 1.0, "Mn": 1.0}),
    (" Mg2 Ni ", {"Mg": 2, "Ni": 1}),
])
def test_parse_valid(text, expected):
    got = parse_composition(text)
    assert set(got) == set(expected)
    for k, v in expected.items():
        assert got[k] == pytest.approx(v)


@pytest.mark.parametrize("text,msg", [
    ("", "Enter a composition"), ("LaNi5H6", "hydrogen-free"), ("MmNi5", "pseudo-element"),
    ("Xx2", "not a chemical element"), ("LaNi5;DROP", "Only element symbols"), ("La-Ni5", "Only element symbols"),
])
def test_parse_invalid(text, msg):
    with pytest.raises(CompositionError, match=msg):
        parse_composition(text)


# ---------------- consistency with the training pipeline
def test_features_identical_to_training_table(P, train_table):
    sample = train_table.sample(60, random_state=0)
    for _, r in sample.iterrows():
        X = P.featurise(r["comp_key"])
        np.testing.assert_allclose(X.to_numpy(float)[0], r[P.features].to_numpy(float), rtol=0, atol=1e-12)


def test_prediction_equals_saved_model_on_training_rows(P, train_table):
    src = joblib.load(ROOT / "results/models/dH_final.joblib")
    assert src["features"] == P.features
    rows = train_table.sample(40, random_state=1)
    expected = src["model"].predict(rows[src["features"]].to_numpy(float))
    got = np.array([P.predict(k).dH_pred for k in rows["comp_key"]])
    np.testing.assert_allclose(got, expected, rtol=0, atol=1e-9)


def test_prediction_is_deterministic_and_notation_independent(P):
    a = P.predict("LaNi4.2Al0.8").dH_pred
    assert a == P.predict("LaNi4.2Al0.8").dH_pred
    assert a == pytest.approx(P.predict("La5Ni21Al4").dH_pred)       # same fractions, different notation


def test_matches_phase6_estimate_table(P):
    s = pd.read_csv(ROOT / "results/tables/vant_hoff_ml_series.csv").set_index("comp_key")
    for text, key in (("LaNi4.2Al0.8", "Al0.133La0.167Ni0.7"), ("TiFe0.75Mn0.25", "Fe0.375Mn0.125Ti0.5")):
        r = P.predict(text)
        assert r.comp_key == key
        assert r.dH_pred == pytest.approx(s.loc[key, "dH_predicted"], abs=1e-9)
        assert r.interval == pytest.approx((s.loc[key, "dH_interval_low"], s.loc[key, "dH_interval_high"]), abs=1e-9)


# ---------------- domain and interval logic
def test_domain_and_interval(P):
    r = P.predict("TiFe0.75Mn0.25")
    assert r.in_domain and not r.in_training and r.interval[0] < r.dH_pred < r.interval[1]
    assert len(r.neighbours) == 5 and r.neighbours["L1_distance"].is_monotonic_increasing
    far = P.predict("AuPt")
    assert not far.in_domain and far.reliability == "OUTSIDE DOMAIN"
    assert "Au" in far.unseen_elements and far.warnings


def test_training_composition_is_flagged(P):
    r = P.predict("LaNi5")
    assert r.in_training and r.training_row["dH_kJmol"] == pytest.approx(32.151)
    assert r.nn_distance > 0  # distance to nearest *other* composition


# ---------------- artifacts
def test_manifest_hashes_match():
    m = json.loads(MANIFEST_PATH.read_text())
    for f, h in ((m["bundle_file"], m["bundle_sha256"]), (m["source_model_file"], m["source_model_sha256"])):
        assert hashlib.sha256((ROOT / f).read_bytes()).hexdigest() == h
    assert m["n_features"] == 38 and m["estimator"] == "RandomForestRegressor"


def test_missing_bundle_is_reported(tmp_path):
    with pytest.raises(FileNotFoundError, match="export_bundle"):
        Predictor(tmp_path / "missing.joblib")


# ---------------- app workflow (headless)
def test_app_prediction_workflow():
    from streamlit.testing.v1 import AppTest
    at = AppTest.from_file(str(ROOT / "app.py"), default_timeout=180).run()
    assert not at.exception
    at.sidebar.radio[0].set_value("Property Predictor").run()
    at.text_input[0].set_value("TiFe0.75Mn0.25")
    at.button[0].click().run()
    assert not at.exception
    vals = {m.label: m.value for m in at.metric}
    live = Predictor().predict("TiFe0.75Mn0.25")
    assert vals["Predicted ΔH, kJ/mol H₂"] == f"{live.dH_pred:.1f}"
    at.text_input[0].set_value("NaAlH4")
    at.button[0].click().run()
    assert any("hydrogen-free" in e.value for e in at.error)
    for page in ("Thermodynamic Explorer", "Model Performance", "Material Comparison", "Overview"):
        at.sidebar.radio[0].set_value(page).run()
        assert not at.exception, page
