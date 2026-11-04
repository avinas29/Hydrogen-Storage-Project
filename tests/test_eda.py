"""Phase 3 checks: figures exist and the Van't Hoff numbers in the report are right."""
import math
from pathlib import Path

import pandas as pd
import pytest

ROOT = Path(__file__).resolve().parents[1]
FIGS = [f"fig{i:02d}" for i in range(1, 11)]


def test_all_figures_written():
    names = {p.name for p in (ROOT / "results/figures").glob("fig*.png")}
    for f in FIGS:
        assert any(n.startswith(f) for n in names), f
        assert any(n.startswith(f) for n in {p.name for p in (ROOT / "results/figures").glob("*.pdf")})


def test_representative_vant_hoff_table():
    t = pd.read_csv(ROOT / "results/tables/eda_representative_vant_hoff.csv").set_index("material")
    # LaNi5: dH 32.151 kJ, dS 112.8 -> ~1.8 bar at 25 C (literature ~1.7-2 bar)
    assert t.loc["La[1]Ni[5]", "Peq_25C_bar"] == pytest.approx(1.84, abs=0.02)
    # T at 1 bar = dH / (dS - R ln(1/1.01325)) for MgH2
    dH, dS = 78300, 136.1
    expected = dH / (dS - 8.314 * math.log(1 / 1.01325)) - 273.15
    assert t.loc["Mg[1]", "T_at_1bar_C"] == pytest.approx(expected, abs=1)
