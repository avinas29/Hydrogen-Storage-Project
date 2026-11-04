"""Application Requirement Designer: guided requirements -> constraint screening -> ranked, explained recommendations."""
from __future__ import annotations

import json
from dataclasses import asdict

import numpy as np
import pandas as pd
import plotly.express as px
import streamlit as st

from ..thermodynamics.vant_hoff import T_at_P
from .data import predictor
from .recommend import (APPLICATIONS, CRITERIA, HEAT_SOURCES, LABELS, PARETO_OBJECTIVES, Requirements,
                        experimental_pool, explain, export_csv, run)
from .ui import EVIDENCE_KIND, STATUS_KIND, badge, badges, chart_layout, header, step

OPT_FIELDS = ["heat_temp_C", "heat_power_kW", "cooling_temp_C", "h2_kg", "flow_kg_h", "T_op_min_C", "T_op_max_C",
              "charge_time_h", "discharge_time_h", "max_mass_kg", "max_volume_L", "min_capacity_wt", "max_thermal_MJ",
              "max_pressure_bar", "max_temp_C", "charge_pressure_bar", "cycle_life"]
POBJ_LABEL = {"wt_pct": "reported capacity (wt%) ↑", "heat_MJ_per_kgH2": "reaction heat (MJ/kg H₂) ↓",
              "temperature_margin_K": "temperature margin (K) ↑", "hyst_ln_Pa_Pd_25C": "hysteresis ln(Pa/Pd) ↓",
              "evidence_score": "evidence quality ↑", "vol_H_kg_m3_solid": "volumetric H (kg/m³, stated density only) ↑"}


def _apply_defaults():
    app = st.session_state["ard_app"]
    d = APPLICATIONS[app]["defaults"]
    for f in OPT_FIELDS:   # number_input needs one numeric type: floats everywhere except cycle life
        v = d.get(f)
        st.session_state[f"ard_{f}"] = None if v is None else (int(v) if f == "cycle_life" else float(v))
    for f in ("ambient_min_C", "ambient_max_C", "P_delivery_bar"):
        st.session_state[f"ard_{f}"] = float(d[f])
    st.session_state["ard_heat_source"] = d.get("heat_source", "none")
    for k in CRITERIA:
        st.session_state[f"ard_w_{k}"] = float(APPLICATIONS[app]["weights"].get(k, 0.0))
    st.session_state.pop("ard_result", None)


def _num(label, key, help=None, **kw):
    # the value lives in session_state (set by _apply_defaults; None = empty / not specified)
    st.session_state.setdefault(f"ard_{key}", None)
    return st.number_input(label, key=f"ard_{key}", help=help, **kw)


def page_designer():
    header("Application Requirement Designer", "Describe the application and get materials ranked for **these** conditions. "
                                               "Experimental materials and ML-generated candidates are kept in separate sections.")
    if "ard_app" not in st.session_state:
        st.session_state["ard_app"] = "Mobile hydrogen storage"
        _apply_defaults()

    step("Step 1 · Application")
    st.selectbox("Application type", list(APPLICATIONS), key="ard_app", on_change=_apply_defaults,
                 help="Changing the type loads illustrative default requirements and weights. Every value can be edited.")

    step("Step 2 · Operating environment")
    c = st.columns(4)
    loc = c[0].text_input("Location / city (recorded only)", key="ard_location",
                          help="Not used to infer climate, waste heat, cooling water or infrastructure. Enter those values yourself.")
    amin = c[1].number_input("Min ambient T (°C)", -60.0, 60.0, key="ard_ambient_min_C", help="Coldest expected (seasonal) temperature")
    amax = c[2].number_input("Max ambient T (°C)", -40.0, 70.0, key="ard_ambient_max_C", help="Hottest expected temperature")
    hs = c[3].selectbox("Available heat source", HEAT_SOURCES, key="ard_heat_source")
    c = st.columns(4)
    with c[0]:
        htemp = _num("Heat-source temperature (°C)", "heat_temp_C", min_value=-50.0, max_value=900.0, disabled=hs == "none")
    with c[1]:
        hpow = _num("Available heating power (kW)", "heat_power_kW", min_value=0.0)
    cw = c[2].checkbox("Cooling water available", key="ard_cooling_water")
    with c[3]:
        ctemp = _num("Cooling-water temperature (°C)", "cooling_temp_C", min_value=0.0, max_value=80.0, disabled=not cw)

    step("Step 3 · Hydrogen requirements")
    c = st.columns(4)
    with c[0]:
        h2 = _num("Hydrogen quantity (kg)", "h2_kg", min_value=0.0)
    pdel = c[1].number_input("Delivery pressure (bar abs.)", 0.1, 700.0, key="ard_P_delivery_bar")
    with c[2]:
        flow = _num("Flow rate (kg/h)", "flow_kg_h", min_value=0.0, help="If empty: H₂ quantity ÷ discharge time")
    op = c[3].selectbox("Operation", ["intermittent", "continuous"], key="ard_operation")
    c = st.columns(4)
    with c[0]:
        tmin = _num("Operating T min (°C)", "T_op_min_C", min_value=-80.0, max_value=500.0)
    with c[1]:
        tmax = _num("Operating T max (°C)", "T_op_max_C", min_value=-80.0, max_value=500.0)
    with c[2]:
        cht = _num("Charging time (h)", "charge_time_h", min_value=0.0)
    with c[3]:
        dct = _num("Discharging time (h)", "discharge_time_h", min_value=0.0)

    step("Step 4 · Engineering constraints (all optional)")
    c = st.columns(4)
    with c[0]:
        mmass = _num("Max material mass (kg)", "max_mass_kg", min_value=0.0, help="Hydride material only: no vessel or heat exchanger")
    with c[1]:
        mvol = _num("Max material volume (L)", "max_volume_L", min_value=0.0, help="Evaluated only where a density is stated")
    with c[2]:
        mcap = _num("Min capacity (wt%)", "min_capacity_wt", min_value=0.0, max_value=20.0, help="Reported material capacity; definition varies")
    with c[3]:
        mth = _num("Max thermal energy (MJ)", "max_thermal_MJ", min_value=0.0)
    c = st.columns(4)
    with c[0]:
        mp = _num("Max pressure (bar)", "max_pressure_bar", min_value=0.0)
    with c[1]:
        mt = _num("Max temperature (°C)", "max_temp_C", min_value=-50.0, max_value=900.0)
    with c[2]:
        chp = _num("Charging pressure available (bar)", "charge_pressure_bar", min_value=0.0)
    with c[3]:
        cyc = _num("Required cycle life", "cycle_life", min_value=0, step=100, help="No cycle-life data exist; recorded as 'unknown'")
    st.caption("Budget is not available as a constraint: there is no verified cost data, only a qualitative element-cost class.")

    step("Step 5 · Preferences and weights")
    wc = st.columns(len(CRITERIA))
    weights = {k: wc[i].slider(k.replace("_", " "), 0.0, 0.5, key=f"ard_w_{k}", step=0.05) for i, k in enumerate(CRITERIA)}
    pc = st.columns(2)
    ox = pc[0].selectbox("Pareto objective 1", list(PARETO_OBJECTIVES), format_func=POBJ_LABEL.get, key="ard_ox")
    oy = pc[1].selectbox("Pareto objective 2", [o for o in PARETO_OBJECTIVES if o != ox], format_func=POBJ_LABEL.get, key="ard_oy")

    def opt(x):
        return None if x is None else float(x)
    req = Requirements(application=st.session_state["ard_app"], location=loc, ambient_min_C=amin, ambient_max_C=amax,
                       heat_source=hs, heat_temp_C=opt(htemp) if hs != "none" else None, heat_power_kW=opt(hpow),
                       cooling_water=cw, cooling_temp_C=opt(ctemp) if cw else None, h2_kg=opt(h2), P_delivery_bar=pdel,
                       flow_kg_h=opt(flow), T_op_min_C=opt(tmin), T_op_max_C=opt(tmax), charge_time_h=opt(cht),
                       discharge_time_h=opt(dct), operation=op, max_mass_kg=opt(mmass), max_volume_L=opt(mvol),
                       min_capacity_wt=opt(mcap), max_thermal_MJ=opt(mth), max_pressure_bar=opt(mp), max_temp_C=opt(mt),
                       charge_pressure_bar=opt(chp), cycle_life=int(cyc) if cyc else None)

    step("Step 6 · Review and run")
    errs = req.validate()
    s = {"application": req.application, "desorption T available (°C)": req.desorption_T_allowed_C(),
         "hottest bed T (°C)": req.bed_T_max_C(), "charging T (°C)": req.charge_T_C(),
         "delivery pressure (bar)": req.P_delivery_bar,
         "specified constraints": ", ".join(k for k in OPT_FIELDS if getattr(req, k) is not None) or "none"}
    st.dataframe(pd.DataFrame([s]), hide_index=True, width="stretch")
    st.caption("Derived conditions: H₂ must be delivered at the heat-source temperature, or at the coldest ambient if there is no heat source "
               "(capped by the max operating/max temperature). The overpressure check uses the hottest bed temperature. "
               "Charging uses the cooling-water temperature, else the hottest ambient.")
    for e in errs:
        st.error(e)
    if st.button("Run material screening", type="primary", disabled=bool(errs), key="ard_run"):
        res = run(req, weights, (ox, oy))
        st.session_state["ard_result"] = {"res": res, "req": req, "weights": weights, "pareto": (ox, oy)}
        st.session_state.setdefault("history", []).append(
            {"composition": f"Designer: {req.application}", "ΔH_pred": None,
             "interval": f"{(res.status != 'fail').sum()} pass of {len(res)}", "status": "screened"})
    out = st.session_state.get("ard_result")
    if out:
        show_results(out)


def show_results(out):
    res, req, weights = out["res"], out["req"], out["weights"]
    step("Step 7 · Recommendations")
    passed = res[res.status == "pass"]
    inc = res[res.status == "pass (incomplete evidence)"]
    fail = res[res.status == "fail"]
    c = st.columns(4)
    c[0].metric("Materials screened", len(res))
    c[1].metric("Pass", len(passed))
    c[2].metric("Pass, incomplete evidence", len(inc))
    c[3].metric("Fail a hard constraint", len(fail))
    t1, t2, t3, t4, t5, t6 = st.tabs(["Recommended (experimental)", "Pareto trade-offs", "Rejected", "Weight sensitivity",
                                      "ML-generated candidates", "Export"])
    ok = res[res.status != "fail"]
    with t1:
        if not len(ok):
            st.warning("No experimental material satisfies all hard constraints. Relax a constraint or add heat.")
        ev = st.multiselect("Evidence classes", ["data-supported", "provisional", "insufficient evidence"],
                            ["data-supported", "provisional"], key="ard_ev")
        view = ok[ok.evidence_class.isin(ev)]
        st.dataframe(view[["rank", "name", "family", "status", "evidence_class", "score", "pareto", "T_required_C",
                           "P_at_T_available_bar", "wt_pct", "heat_MJ_per_kgH2", "material_mass_kg", "heat_power_kW", "missing"]]
                     .round(2), hide_index=True, width="stretch")
        st.caption("Capacity = reported material-level value (definition varies). Mass is material only (no vessel, heat exchanger or porosity).")
        st.caption("Materials classed 'insufficient evidence' are shown when selected, but they get no rank.")
        for _, r in view[view["rank"].notna()].head(5).iterrows():
            e = explain(r, req)
            with st.expander(f"#{int(r['rank'])} {r['name']} ({r['family']}) · score {r['score']:.2f}"):
                badges((r["evidence_class"], EVIDENCE_KIND[r["evidence_class"]]), (r["status"], STATUS_KIND[r["status"]]),
                       ("Pareto-optimal", "info") if r["pareto"] else ("dominated on the chosen pair", "info"))
                st.markdown(e["why"])
                st.markdown("**Satisfies:** " + ("; ".join(e["satisfies"]) or "–"))
                if e["cannot_evaluate"]:
                    st.markdown("**Cannot evaluate (missing evidence):** " + "; ".join(e["cannot_evaluate"]))
                st.markdown("**Advantages:** " + (", ".join(e["advantages"]) or "–") + " · **Limitations:** " + (", ".join(e["limitations"]) or "–"))
                st.markdown("**Missing properties:** " + (e["missing"] or "none of the scored ones"))
                st.markdown("**Measure before deployment:** " + "; ".join(e["measurements"]))
    with t2:
        ox, oy = out["pareto"]
        d = res[res.status != "fail"]
        f = px.scatter(d, x=ox, y=oy, color=d["pareto"].map({True: "Pareto front", False: "dominated"}),
                       symbol="evidence_class", hover_data=["name", "family", "score"],
                       color_discrete_map={"Pareto front": "#C0504D", "dominated": "#B8C2CC"},
                       labels={ox: POBJ_LABEL[ox], oy: POBJ_LABEL[oy], "color": ""})
        st.plotly_chart(chart_layout(f, 460, title="Trade-off among the materials that pass"), width="stretch")
        st.dataframe(d[d.pareto][["rank", "name", "family", ox, oy, "score", "evidence_class"]].round(2), hide_index=True, width="stretch")
        st.caption("Pareto-optimal materials are shown even when their weighted score is lower: each one is best on some trade-off.")
    with t3:
        fr = fail.copy()
        fr["failed"] = fr.apply(lambda r: "; ".join(LABELS[k] for k in LABELS if r.get(f"c_{k}") == "fail"), axis=1)
        counts = pd.Series([x for s in fr["failed"] for x in s.split("; ") if x]).value_counts()
        st.dataframe(counts.rename_axis("failed requirement").reset_index(name="materials"), hide_index=True, width="stretch")
        st.dataframe(fr[["name", "family", "failed", "T_required_C", "T_available_C", "P_bed_max_bar"]].round(2), hide_index=True, width="stretch")
    with t4:
        base_top = ok.head(10)["purdue_id"].tolist()
        rows = []
        for k, v in weights.items():
            for fct in (0.0, 2.0):
                w = dict(weights); w[k] = v * fct
                r2 = run(req, w, out["pareto"])
                top = r2[r2.status != "fail"].head(10)
                rows.append({"criterion": k, "weight ×": fct, "top-10 overlap with base": len(set(base_top) & set(top.purdue_id)),
                             "new #1": top["name"].iloc[0] if len(top) else "–"})
        st.dataframe(pd.DataFrame(rows), hide_index=True, width="stretch")
        st.caption("How the recommendation changes when one weight is removed or doubled. Large changes mean the choice depends on that preference.")
    with t5:
        lab = st.session_state.get("lab")
        st.info("ML-generated candidates (Candidate Discovery Lab) are kept separate from experimental materials. Capacity, kinetics and "
                "stability are not predicted for them, so they can only be **provisional** at best.")
        if not lab:
            st.caption("No Lab run in this session. Generate candidates in the Candidate Discovery Lab first.")
        else:
            P = predictor()
            c = lab["res"].copy()
            dS_lo, dS, dS_hi, fam = P.dS_for(lab["family"])
            T_av = req.desorption_T_allowed_C()
            c["T_required_C (estimate)"] = [float(T_at_P(req.P_delivery_bar, h, dS)) - 273.15 if pd.notna(h) else np.nan for h in c["dH_pred_kJmol"]]
            c["T_required_band_C"] = [f"{float(T_at_P(req.P_delivery_bar, hi, dS_lo)) - 273.15:.0f}–{float(T_at_P(req.P_delivery_bar, lo, dS_hi)) - 273.15:.0f}"
                                      if pd.notna(lo) else "" for lo, hi in zip(c["dH_low"], c["dH_high"])]
            c["delivery (estimate)"] = np.where(c["T_required_C (estimate)"] <= T_av, "likely pass", "likely fail")
            c["evidence_class"] = np.where(c.status == "candidate", "provisional (ML ΔH, assumed ΔS)", "insufficient evidence")
            c["capacity"] = "not predicted"
            st.dataframe(c[["formula", "evidence_class", "dH_pred_kJmol", "dH_low", "dH_high", "T_required_C (estimate)",
                            "T_required_band_C", "delivery (estimate)", "capacity", "reasons"]].round(2), hide_index=True, width="stretch")
    with t6:
        st.download_button("Ranking results (CSV, with provenance and requirements)", export_csv(res, req, weights),
                           "application_ranking.csv", "text/csv", key="ard_dl_csv")
        st.download_button("Application requirements (JSON)", json.dumps({**asdict(req), "weights": weights}, indent=2),
                           "application_requirements.json", "application/json", key="ard_dl_json")
