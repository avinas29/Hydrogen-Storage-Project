"""Phase 7 checks: plateau extraction, Van't Hoff fit recovery, kinetics comparability."""
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from src.thermodynamics.pci_kinetics import plateau_of_curve, vant_hoff_fit
from src.thermodynamics.vant_hoff import peq_bar

ROOT = Path(__file__).resolve().parents[1]


def test_plateau_of_flat_curve():
    w = np.linspace(0.05, 1.4, 20)
    g = pd.DataFrame({"wt_pct": w, "P_bar": np.full(20, 1.7)})
    r = plateau_of_curve(g)
    assert r["P_plateau_bar"] == pytest.approx(1.7) and abs(r["slope_dlnP_dx"]) < 1e-9


def test_vant_hoff_fit_recovers_parameters():
    T = np.array([273.0, 298.0, 323.0])
    f = vant_hoff_fit(T, peq_bar(T, 32.15, 112.8))
    assert f["dH_fit_kJmol"] == pytest.approx(32.15, abs=1e-6)
    assert f["dS_fit_JmolK"] == pytest.approx(112.8, abs=1e-6)


def test_kinetics_only_compares_same_rate_law():
    k = pd.read_csv(ROOT / "results/tables/kinetics_purdue.csv")
    assert len(k[k["mode"] == "abs"]) == 31 and len(k[k["mode"] == "des"]) == 26
    assert k.loc[~k["model_form_comparable"], "t90_s_25C"].isna().all()
    assert k.loc[k["model_form_comparable"], "pFcn"].str.lower().eq("log").all()


def test_naalh4_plateau_assignment():
    from src.thermodynamics.pci_kinetics import load_all_pci
    from src.thermodynamics.pci_report import naalh4_check
    pts, _ = load_all_pci()
    na = naalh4_check(pts)
    ratio = na["P_curve_bar"] / na["P_vant_hoff_bar"]
    assert ((ratio > 0.5) & (ratio < 2)).all()   # correct assignment within 2x; swapped would be ~10x off
