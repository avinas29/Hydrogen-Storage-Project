"""Phase 2 checks: conventions, composition keys, no silent record loss."""
from pathlib import Path

import pandas as pd
import pytest
from pymatgen.core import Composition

from src.data.clean import comp_key

ROOT = Path(__file__).resolve().parents[1]
PROC = ROOT / "data/processed"


@pytest.fixture(scope="module")
def cleaned():
    return (pd.read_csv(PROC / "purdue_cleaned.csv"),
            pd.read_csv(PROC / "hydpark_cleaned.csv"),
            pd.read_csv(PROC / "dH_union_by_composition.csv"))


def test_comp_key_is_notation_independent():
    keys = {comp_key(Composition(f)) for f in
            ["LaNi5", "La1Ni5", "La16.6667Ni83.3333", "(La)(Ni)5"]}
    assert keys == {"La0.167Ni0.833"}
    assert comp_key(Composition("ZrMn2")) == comp_key(Composition("(Zr)(Mn)2"))


def test_no_records_dropped(cleaned):
    p, h, _ = cleaned
    assert len(p) == 337 and len(h) == 772


def test_positive_desorption_convention(cleaned):
    p, h, _ = cleaned
    assert (p["dH_kJmol"] > 0).all() and (h["dH_kJmol"] > 0).all()
    tife = p.set_index("purdue_id").loc["Ti[1]Fe[1]"]
    assert tife["dH_kJmol"] == pytest.approx(28.1)
    assert tife["dS_JmolK"] == pytest.approx(106)


def test_pseudo_elements_not_parsed(cleaned):
    p, _, _ = cleaned
    pseudo = p["composition_raw"].str.contains(r"(?:^|;)(?:Mm|Lm|Vf):")
    assert p.loc[pseudo, "comp_key"].isna().all()
    assert p.loc[~pseudo, "comp_key"].notna().all()


def test_zero_capacity_is_missing(cleaned):
    _, h, _ = cleaned
    assert not (h["wt_pct"] == 0).any()


def test_union_one_row_per_composition_and_exclusions(cleaned):
    p, h, u = cleaned
    assert u["comp_key"].is_unique
    bad = set(h.loc[h["flag_suspected_entry_error"] | h["flag_excluded_by_purdue_curators"], "hydpark_id"])
    used = set(";".join(u["hydpark_ids"].fillna("")).split(";")) - {""}
    assert not (bad & used)
    multi = set(p.loc[p["flag_multi_plateau"], "purdue_id"])
    assert not (multi & set(u["purdue_id"].fillna("")))
