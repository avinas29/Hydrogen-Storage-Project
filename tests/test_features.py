"""Phase 4 checks: descriptor arithmetic, no leakage, no missing values."""
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from src.features.composition import LEAKY_FOR_DH, featurize

ROOT = Path(__file__).resolve().parents[1]


def test_lani5_descriptors():
    X, tab, _ = featurize(pd.Series(["La0.167Ni0.833"]), frac_elements=["La", "Ni"])
    t = tab.set_index("element")
    x_la, x_ni = 0.167 / 1.0, 0.833 / 1.0
    assert X.loc[0, "mass_mean"] == pytest.approx(x_la * t.loc["La", "mass"] + x_ni * t.loc["Ni", "mass"])
    assert X.loc[0, "X_min"] == t.loc["Ni", "X"] or X.loc[0, "X_min"] == t.loc["La", "X"]
    assert X.loc[0, "frac_hydride_former"] == pytest.approx(x_la)   # La yes, Ni no
    assert X.loc[0, "vec_mean"] == pytest.approx(x_la * 3 + x_ni * 10)
    assert X.loc[0, "config_entropy"] == pytest.approx(-(x_la * np.log(x_la) + x_ni * np.log(x_ni)))
    assert X.loc[0, "n_elements"] == 2


def test_feature_tables_clean():
    fl = pd.read_csv(ROOT / "results/tables/feature_list.csv")
    feats = fl["feature"].tolist()
    assert not set(feats) & LEAKY_FOR_DH
    for f, n in (("features_dH.csv", 725), ("features_wt.csv", None)):
        d = pd.read_csv(ROOT / "data/processed" / f)
        if n:
            assert len(d) == n and d["comp_key"].is_unique
        assert d[feats].isna().sum().sum() == 0
