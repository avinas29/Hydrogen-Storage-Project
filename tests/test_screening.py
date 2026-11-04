"""Phase 8 checks: constraints are enforced, scores are bounded, weights sum to 1."""
from pathlib import Path

import numpy as np
import pandas as pd

from src.screening.screen import CRITERIA, WEIGHTS, cost_class

ROOT = Path(__file__).resolve().parents[1]
T = ROOT / "results/tables"


def test_weights_sum_to_one():
    for w in WEIGHTS.values():
        assert abs(sum(w.values()) - 1) < 1e-9


def test_cost_classes():
    assert cost_class({"Ti", "Fe"})[0] == 1.0
    assert cost_class({"La", "Ni"})[0] == 0.5
    assert cost_class({"Ti", "V"})[0] == 0.5
    assert cost_class({"Pd"})[0] == 0.0


def test_rankings_respect_constraints():
    for app in ("mobile", "stationary"):
        r = pd.read_csv(T / f"screening_{app}_ranking.csv")
        cr = CRITERIA[app]
        assert (r["T1_full_C"] <= cr["T1_full_max_C"] + 1e-9).all()
        assert (r["P50_bar"] <= cr["P50_max_bar"] + 1e-9).all()
        assert (r["Pcharge25_bar"] <= cr["Pcharge25_max_bar"] + 1e-9).all()
        if "P25_max_bar" in cr:
            assert (r["P25_bar"] <= cr["P25_max_bar"] + 1e-9).all()
        assert r["data_quality_pass"].all()
        assert r["score"].between(0, 1).all() and r["score"].is_monotonic_decreasing
        contrib = r[[c for c in r.columns if c.startswith("contrib_")]].sum(axis=1)
        assert np.allclose(contrib, r["score"])


def test_mg_hydrides_fail_mobile_on_temperature():
    c = pd.read_csv(T / "screening_candidates.csv").set_index("purdue_id")
    assert c.loc["Mg[1]", "mobile_fail_reasons"].startswith("T(1 bar)")
