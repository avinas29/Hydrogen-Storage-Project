"""Checks that the extraction reproduces the MATLAB toolbox conventions."""
import math
from pathlib import Path

import numpy as np
import pytest

from src.data.hydpark import load_hydpark
from src.data.purdue_parser import load_purdue, parse_mh_file

ROOT = Path(__file__).resolve().parents[1]
TOOLBOX = ROOT / "data/raw/purdue/MetalHydrideToolbox"
DATA = TOOLBOX / "data"


@pytest.fixture(scope="module")
def purdue():
    return load_purdue(TOOLBOX)


def test_all_files_parsed(purdue):
    assert len(purdue) == 337
    assert purdue["des_dH_J_per_molH2"].notna().all()


def test_tife_values_and_vant_hoff():
    r = parse_mh_file(DATA / "Ti[1]Fe[1].mh")
    assert r["des_dH_J_per_molH2"] == -28100
    assert r["des_dS_J_per_molH2K"] == -106
    assert r["wt_pct_stated"] == 1.86
    # Peq.m flat-plateau limit: P = exp((dH - T dS)/(R T)) atm; TiFe ~ 4 atm at 298 K
    p = math.exp((r["des_dH_J_per_molH2"] - 298 * r["des_dS_J_per_molH2K"]) / (8.314 * 298))
    assert 3 < p < 5


def test_hm_is_per_formula_unit():
    # Mm[1]Ni[4.8]Al[0.2] gives H/M: 6 -> MmNi4.8Al0.2H6 -> about 1 H per metal atom
    r = parse_mh_file(DATA / "Mm[1]Ni[4.8]Al[0.2].mh")
    assert r["hm_stated"] == 6
    assert r["capacity_basis"] == "derived_from_HM_per_formula_unit"
    assert abs(r["h_per_metal_atom_toolbox"] - 1.0) < 1e-9
    assert 1.3 < r["wt_pct_toolbox"] < 1.5


def test_multi_plateau_array():
    r = parse_mh_file(DATA / "Ho[2]Co[7].mh")
    assert r["des_n_values"] == 5
    assert r["des_dH_J_per_molH2_all"].split(";")[0] == "-46000"


def test_missing_property_is_nan_not_default(purdue):
    # GetTypeProperty would give AB rho = 6500; TiFe states rho 6500, but an AB
    # file without rho must stay NaN
    ab = purdue[purdue["type"] == "AB"]
    assert ab["rho_kg_per_m3"].isna().any()
    assert not (purdue["rho_kg_per_m3"] == 0).any()


def test_hydpark_blocks_and_sign():
    h = load_hydpark(ROOT / "data/raw/hydpark/ML-HYDPARK_v0.0.5.csv")
    assert len(h) == 772
    assert sorted(h["source_block"].unique()) == [0, 1, 2, 3]
    assert (h["Heat_of_Formation_kJperMolH2"] > 0).all()
    ok = ~h["flag_lnP25_mismatch"]
    lnp = (-h["Heat_of_Formation_kJperMolH2"] * 1000 / (8.314 * 298.15)
           + h["Entropy_of_Formation_JperMolH2perK"] / 8.314)
    assert np.allclose(lnp[ok], h["LnEquilibrium_Pressure_25C"][ok], atol=0.01)
