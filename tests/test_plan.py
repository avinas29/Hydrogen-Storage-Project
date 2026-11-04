"""Phase 9 checks: the plan is labelled as future work and its candidates trace to earlier results."""
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]


def test_plan_is_labelled_proposed():
    text = (ROOT / "reports/synthesis_characterization_plan.md").read_text()
    assert "PROPOSED FUTURE WORK" in text
    assert "No material was synthesised" in text


def test_candidates_trace_to_results():
    cand = pd.read_csv(ROOT / "results/tables/proposed_experimental_candidates.csv")
    exp = cand[cand["basis"] == "experimental (.mh)"]
    assert len(exp) == 9
    ml = cand[cand["role"].str.startswith("ML test")]
    assert len(ml) == 2 and ml["basis"].str.startswith("ESTIMATE").all()
    # blind-test compositions must not be in the ΔH training set
    train = set(pd.read_csv(ROOT / "data/processed/features_dH.csv")["comp_key"])
    for key in ("Al0.133La0.167Ni0.7", "Fe0.375Mn0.125Ti0.5"):
        assert key not in train
    series = pd.read_csv(ROOT / "results/tables/vant_hoff_ml_series.csv").set_index("comp_key")
    assert not series.loc[["Al0.133La0.167Ni0.7", "Fe0.375Mn0.125Ti0.5"], "in_data"].any()
