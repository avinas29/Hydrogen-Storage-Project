"""METAL HYDRIDE AI platform: generator, discovery, recommendation engine, exports and page workflows."""
import io
import json
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from src.app.discovery import Targets, evaluate, rank
from src.app.generator import PRESETS, Site, generate_free, generate_sites
from src.app.pareto import pareto_mask, weighted
from src.app.predictor import Predictor
from src.app.recommend import (APPLICATIONS, Requirements, evaluate_constraints, evidence_class, experimental_pool,
                               export_csv, run, score)
from src.thermodynamics.vant_hoff import T_at_P, peq_bar

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture(scope="module")
def P():
    return Predictor()


@pytest.fixture(scope="module")
def pool():
    return experimental_pool()


# ---------------- 1-3 generator
def test_site_stoichiometry_and_ranges():
    sites = [Site("Ti", 1.0, {"Zr": (0.0, 0.3)}, 0.6), Site("Mn", 2.0, {"Cr": (0.2, 1.0)}, 0.8)]
    out = generate_sites(sites, 0.1, 10_000, 0)
    assert out
    for c in out:
        a = c["amounts"]
        assert a.get("Ti", 0) + a.get("Zr", 0) == pytest.approx(1.0)
        assert a.get("Mn", 0) + a.get("Cr", 0) == pytest.approx(2.0)
        assert 0 <= a.get("Zr", 0) <= 0.3 + 1e-9 and 0.2 - 1e-9 <= a["Cr"] <= 1.0 + 1e-9
        assert a["Ti"] >= 0.6 - 1e-9 and a["Mn"] >= 0.8 - 1e-9


def test_free_fractions_sum_to_one():
    out = generate_free({"V": (0.5, 0.9), "Ti": (0.05, 0.4), "Cr": (0.0, 0.3)}, 0.05, 10_000, 0)
    assert out and all(abs(sum(c["amounts"].values()) - 1) < 1e-9 for c in out)
    assert all(0.0 - 1e-9 <= c["amounts"].get("Cr", 0) <= 0.3 + 1e-9 for c in out)


def test_reproducible_sampling_and_no_duplicates():
    sites = PRESETS["La-Ce-Ni-Al (AB5)"].sites
    a = generate_sites(sites, 0.05, 40, seed=7)
    b = generate_sites(sites, 0.05, 40, seed=7)
    c = generate_sites(sites, 0.05, 40, seed=8)
    assert [x["comp_key"] for x in a] == [x["comp_key"] for x in b]
    assert [x["comp_key"] for x in a] != [x["comp_key"] for x in c]
    assert len(a) == 40 and a[0]["n_grid_total"] > 40
    keys = [x["comp_key"] for x in generate_sites(sites, 0.05, 10_000, 0)]
    assert len(keys) == len(set(keys))


def test_equivalent_compositions_deduplicated():
    # Zr range 0 on both sites duplicates nothing; host-only + identical subs are merged
    out = generate_sites([Site("La", 1.0), Site("Ni", 5.0, {"Ni": (0.0, 0.0)})], 0.1, 100, 0)
    assert len(out) == 1


def test_invalid_ranges():
    with pytest.raises(ValueError):
        generate_free({"Ti": (0.6, 0.4), "Fe": (0.0, 1.0)}, 0.1)
    with pytest.raises(ValueError):
        generate_free({"Ti": (0.0, 1.0)}, 0.1)


# ---------------- 4-8 discovery
def test_discovery_matches_single_predictor(P):
    cands = generate_sites(PRESETS["Ti-Fe-Mn (AB, TiFe1-xMnx)"].sites, 0.05, 100, 0)
    df = evaluate(P, cands, "AB", Targets())
    for _, r in df.iterrows():
        p = P.predict(r["formula"])
        assert r["dH_pred_kJmol"] == p.dH_pred and (r["dH_low"], r["dH_high"]) == p.interval
        assert r["dH_low"] < r["dH_pred_kJmol"] < r["dH_high"]
        # Van't Hoff consistency: P_eq at the estimated temperature equals the target pressure
        assert peq_bar(r["T_at_Ptarget_C"] + 273.15, r["dH_pred_kJmol"], r["dS_assumed"]) == pytest.approx(5.0, rel=1e-9)


def test_unsupported_elements_rejected(P):
    df = evaluate(P, generate_free({"Au": (0.4, 0.6), "Pt": (0.4, 0.6)}, 0.1, 10, 0), "(all)", Targets())
    assert (df["status"] == "rejected").all()
    assert df["reasons"].str.contains("not in training data").all()
    assert df["reasons"].str.contains("outside applicability domain").all()


def test_rank_scores_only_candidates_and_pareto(P):
    tg = Targets(25, 5, -20, 80)
    df = rank(evaluate(P, generate_sites(PRESETS["Ti-Zr-Mn-Cr (AB2 Laves)"].sites, 0.1, 200, 0), "AB2", tg), tg)
    ok = df[df.status == "candidate"]
    assert ok["score"].between(0, 1).all() and df.loc[df.status == "rejected", "score"].isna().all()
    assert ok["score"].is_monotonic_decreasing and ok["pareto"].any()
    assert (df.loc[df.status == "rejected", "pareto"] == False).all()  # noqa: E712


# ---------------- 9-11 constraints
def _pool(rows):
    base = dict(hyst_ln_Pa_Pd_25C=np.nan, wt_pct=1.5, rho_kg_m3_stated=np.nan, vol_H_kg_m3_solid=np.nan,
                kinetics_class=1.0, cost_class=1.0, flag_kinetics_no_family_data=False, evidence_class="data-supported",
                evidence_notes="", kin_abs_Ea_Jmol=np.nan, keff_W_mK=np.nan)
    out = []
    for i, r in enumerate(rows):
        d = {**base, **r, "purdue_id": f"m{i}", "name": f"m{i}", "family": "AB"}
        d["plateaus"] = [(d["dH"], d["dS"])]
        d["dH_kJmol_weighted"], d["dS_JmolK_weighted"] = d["dH"], d["dS"]
        d["heat_MJ_per_kgH2"] = d["dH"] / 2.01588
        out.append(d)
    return pd.DataFrame(out)


def test_delivery_and_pressure_constraints():
    pool = _pool([dict(dH=28.0, dS=106.0), dict(dH=40.0, dS=110.0), dict(dH=20.0, dS=110.0)])
    req = Requirements(ambient_min_C=10, ambient_max_C=40, heat_source="none", P_delivery_bar=2, max_pressure_bar=30)
    r = evaluate_constraints(pool, req)
    T_need = [float(T_at_P(2, h, s)) - 273.15 for h, s in [(28, 106), (40, 110), (20, 110)]]
    assert r["c_delivery"].tolist() == ["pass" if t <= 10 else "fail" for t in T_need]
    P_hot = [float(peq_bar(313.15, h, s)) for h, s in [(28, 106), (40, 110), (20, 110)]]
    assert r["c_max_pressure"].tolist() == ["pass" if p <= 30 else "fail" for p in P_hot]


def test_heat_source_compatibility():
    pool = _pool([dict(dH=40.0, dS=110.0)])
    cold = Requirements(ambient_min_C=10, ambient_max_C=30, heat_source="none", P_delivery_bar=2)
    hot = Requirements(ambient_min_C=10, ambient_max_C=30, heat_source="industrial waste heat", heat_temp_C=150, P_delivery_bar=2,
                       h2_kg=10, discharge_time_h=1, heat_power_kW=1.0)
    assert cold.desorption_T_allowed_C() == 10 and hot.desorption_T_allowed_C() == 150
    assert evaluate_constraints(pool, cold)["c_delivery"].iloc[0] == "fail"
    r = evaluate_constraints(pool, hot).iloc[0]
    assert r["c_delivery"] == "pass"
    assert r["heat_power_kW"] == pytest.approx(10 * (40 / 2.01588) / 3.6)  # 10 kg/h x MJ/kg -> kW
    assert r["c_heating_power"] == "fail" and r["status"] == "fail"
    capped = Requirements(heat_source="industrial waste heat", heat_temp_C=150, max_temp_C=60, P_delivery_bar=2)
    assert capped.desorption_T_allowed_C() == 60


def test_missing_data_is_unknown_not_failure():
    pool = _pool([dict(dH=28.0, dS=106.0, wt_pct=np.nan)])
    req = Requirements(ambient_min_C=20, P_delivery_bar=1, min_capacity_wt=1.0, h2_kg=1, max_volume_L=10, cycle_life=500)
    r = evaluate_constraints(pool, req).iloc[0]
    assert r["c_min_capacity"] == "unknown" and r["c_max_volume"] == "unknown" and r["c_cycle_life"] == "unknown"
    assert r["status"] == "pass (incomplete evidence)"
    assert r["c_max_mass"] == "not specified"


def test_requirement_validation():
    assert Requirements(ambient_min_C=30, ambient_max_C=10).validate()
    assert Requirements(heat_source="solar thermal", heat_temp_C=None).validate()
    assert Requirements(P_delivery_bar=5, max_pressure_bar=2).validate()
    assert not Requirements().validate()


# ---------------- 12-15 scoring, Pareto, sensitivity, classification
def test_weighted_scoring():
    s = pd.DataFrame({"a": [1.0, 0.0], "b": [0.0, 1.0]})
    assert weighted(s, {"a": 3, "b": 1}).tolist() == [0.75, 0.25]
    assert weighted(s, {"a": 0, "b": 0}).tolist() == [0.0, 0.0]


def test_pareto_dominance():
    df = pd.DataFrame({"cap": [2, 1, 2, 3, np.nan], "heat": [10, 10, 12, 20, 1]})
    m = pareto_mask(df, {"cap": "max", "heat": "min"})
    assert m.tolist() == [True, False, False, True, False]


def test_preferences_change_recommendation(pool):
    req = Requirements(application="Mobile hydrogen storage", **APPLICATIONS["Mobile hydrogen storage"]["defaults"])
    cap = run(req, {"capacity": 1.0}, pool=pool)
    heat = run(req, {"heat": 1.0}, pool=pool)
    top_cap, top_heat = cap.iloc[0], heat.iloc[0]
    assert top_cap["name"] != top_heat["name"]
    # among ranked recommendations (passing, not 'insufficient evidence')
    assert top_cap["rank"] == 1 and top_cap["wt_pct"] == cap[cap["rank"].notna()]["wt_pct"].max()
    assert top_heat["rank"] == 1 and top_heat["heat_MJ_per_kgH2"] == heat[heat["rank"].notna()]["heat_MJ_per_kgH2"].min()


def test_evidence_classification(pool):
    row = pool.iloc[0].copy()
    row["data_quality_pass"] = False
    assert evidence_class(row)[0] == "insufficient evidence"
    row["data_quality_pass"] = True
    for k in ("flag_pci_dH_inconsistent", "flag_unverified_ref_sandia", "flag_identical_values_other_file", "flag_pseudo_element"):
        row[k] = False
    row["capacity_definition"] = "literature_value_definition_unstated"
    assert evidence_class(row)[0] == "data-supported"
    row["flag_unverified_ref_sandia"] = True
    assert evidence_class(row)[0] == "provisional"
    assert set(pool["evidence_class"]) <= {"data-supported", "provisional", "insufficient evidence"}


def test_insufficient_evidence_never_ranked(pool):
    req = Requirements(application="Mobile hydrogen storage", **APPLICATIONS["Mobile hydrogen storage"]["defaults"])
    res = run(req, pool=pool)
    assert res.loc[res.evidence_class == "insufficient evidence", "rank"].isna().all()
    ranked = res[res["rank"].notna()]
    assert (ranked["status"] != "fail").all() and ranked["rank"].tolist() == list(range(1, len(ranked) + 1))
    assert ranked["score"].is_monotonic_decreasing


def test_scenarios_differ_and_fail_reasons(pool):
    mob = run(Requirements(application="Mobile hydrogen storage", **APPLICATIONS["Mobile hydrogen storage"]["defaults"]), pool=pool)
    ind = run(Requirements(application="Industrial hydrogen buffering", **APPLICATIONS["Industrial hydrogen buffering"]["defaults"]), pool=pool)
    assert mob.iloc[0]["name"] != ind.iloc[0]["name"]
    assert (mob[mob.status == "fail"][[c for c in mob if c.startswith("c_")]] == "fail").any(axis=1).all()


# ---------------- 16 export
def test_export_contains_provenance(pool):
    req = Requirements(application="Stationary hydrogen storage", **APPLICATIONS["Stationary hydrogen storage"]["defaults"])
    res = run(req, pool=pool)
    df = pd.read_csv(io.StringIO(export_csv(res, req, APPLICATIONS[req.application]["weights"])))
    for col in ("basis", "assumptions", "evidence_class", "requirements_json", "status", "c_delivery"):
        assert col in df
    assert json.loads(df["requirements_json"].iloc[0])["P_delivery_bar"] == req.P_delivery_bar


# ---------------- 17 page workflows
def test_all_pages_and_workflows():
    from streamlit.testing.v1 import AppTest
    at = AppTest.from_file(str(ROOT / "app.py"), default_timeout=300).run()
    assert not at.exception
    for page in ("Property Predictor", "Candidate Discovery Lab", "Application Requirement Designer", "Material Comparison",
                 "Thermodynamic Explorer", "Model Performance", "Dataset & Evidence Explorer"):
        at.sidebar.radio[0].set_value(page).run()
        assert not at.exception, page
    at.sidebar.radio[0].set_value("Candidate Discovery Lab").run()
    at.selectbox(key="lab_preset").set_value("La-Ni-Al (AB5)").run()   # switching presets must reload site hosts
    assert at.text_input(key="lab_host_La-Ni-Al (AB5)_0").value == "La"
    at.button(key="lab_run").click().run()
    assert not at.exception
    m = {x.label: x.value for x in at.metric}
    assert int(m["Evaluated"]) == int(m["Candidates in domain"]) + int(m["Rejected"])
    at.sidebar.radio[0].set_value("Application Requirement Designer").run()
    at.selectbox(key="ard_app").set_value("Industrial hydrogen buffering").run()
    assert at.number_input(key="ard_heat_temp_C").value == 120.0
    at.button(key="ard_run").click().run()
    assert not at.exception
    m = {x.label: x.value for x in at.metric}
    assert int(m["Materials screened"]) == 337
    at.sidebar.radio[0].set_value("Overview").run()
    at.button(key="go_Candidate Discovery Lab").click().run()
    assert at.sidebar.radio[0].value == "Candidate Discovery Lab" and not at.exception


def test_designer_pareto_only_among_ranked():
    from src.app.demo import SCENARIOS
    from src.app.recommend import APPLICATIONS, run
    for s in SCENARIOS:
        res = run(s["req"], APPLICATIONS[s["req"].application]["weights"])
        assert res.loc[res["rank"].isna(), "pareto"].eq(False).all()
        assert res.loc[res["rank"].notna(), "pareto"].any()  # a non-empty ranked set always has a front
