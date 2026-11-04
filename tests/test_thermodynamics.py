"""Phase 6 checks: Van't Hoff arithmetic, inverse consistency, units."""
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from src.thermodynamics.vant_hoff import (P0_BAR, R, T_at_P, absorption_pressure_bar,
                                          heat_MJ_per_kg_H2, peq_bar, plateau_pressure_span)

ROOT = Path(__file__).resolve().parents[1]


def test_peq_matches_toolbox_formula():
    # Peq.m: 101325 * exp((dH_f - T dS_f)/(R T)) with formation (negative) values, R = 8.314
    dHf, dSf, T = -28100.0, -106.0, 298.0
    toolbox_bar = 101325 * np.exp((dHf - T * dSf) / (8.314 * T)) / 1e5
    assert peq_bar(T, 28.1, 106.0) == pytest.approx(toolbox_bar, rel=1e-4)


def test_T_at_P_inverts_peq():
    for dH, dS in [(32.15, 112.8), (78.3, 136.1), (21.8, 111.9)]:
        for P in [0.5, 1, 10, 100]:
            assert peq_bar(T_at_P(P, dH, dS), dH, dS) == pytest.approx(P, rel=1e-10)


def test_reference_pressure_is_one_atm():
    # dH/T = dS  ->  P = P0 = 1 atm
    assert peq_bar(300.0, 30.0, 100.0) == pytest.approx(P0_BAR)


def test_heat_units():
    assert heat_MJ_per_kg_H2(30.0) == pytest.approx(30.0 / 2.01588)


def test_hysteresis_and_slope():
    pa, src = absorption_pressure_bar(298.15, 28.1, 106, ln_pa_pd=0.64)
    assert src == "stated_hysteresis_const"
    assert pa == pytest.approx(peq_bar(298.15, 28.1, 106) * np.exp(0.64))
    _, src2 = absorption_pressure_bar(298.15, 28.1, 106)
    assert src2 == "not_available"           # no toolbox default used
    lo, hi = plateau_pressure_span(298.0, 30, 110, slope=1.0)
    assert hi / lo == pytest.approx(np.exp(0.8))


def test_tables_consistent():
    t = pd.read_csv(ROOT / "results/tables/vant_hoff_purdue.csv")
    assert (t["Pabs_bar_25C"].dropna() >= t.loc[t["Pabs_bar_25C"].notna(), "Pdes_bar_25C"] * 0.999).all()
    s = pd.read_csv(ROOT / "results/tables/vant_hoff_ml_series.csv")
    assert s.loc[~s["in_data"], "prediction_type"].str.startswith("ESTIMATE").all()
    assert (s["T1bar_C_band_low"] <= s["T1bar_C_estimate"]).all() and (s["T1bar_C_estimate"] <= s["T1bar_C_band_high"]).all()
