"""Candidate Discovery Lab: constrained alloy grids, screened by the existing model."""
from __future__ import annotations

import json

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from .data import predictor
from .discovery import DEFAULT_WEIGHTS, PARETO_CHOICES, Targets, evaluate, rank
from .generator import FREE_PRESETS, PRESETS, Site, generate_free, generate_sites
from .ui import chart_layout, header, step

OBJ_LABEL = {"temp_misfit_K": "|T(P_target) − T_target| (K)", "nn_L1": "distance to nearest known composition (L1)",
             "interval_width": "80% interval width (kJ/mol)", "heat_MJ_per_kgH2": "reaction heat (MJ/kg H₂)"}


def _site_editor(i: int, site: Site, preset: str) -> Site:
    c = st.columns([1, 1, 1])
    host = c[0].text_input(f"Site {i + 1} host element", site.host, key=f"lab_host_{preset}_{i}")
    total = c[1].number_input(f"Site {i + 1} total per formula unit", 0.1, 10.0, float(site.total), 0.1, key=f"lab_tot_{preset}_{i}")
    hmin = c[2].number_input(f"Host minimum", 0.0, 10.0, float(site.host_min), 0.05, key=f"lab_hmin_{preset}_{i}")
    df = pd.DataFrame([{"element": e, "min": lo, "max": hi} for e, (lo, hi) in site.subs.items()],
                      columns=["element", "min", "max"])
    ed = st.data_editor(df, num_rows="dynamic", key=f"lab_subs_{preset}_{i}", width="stretch",
                        column_config={"min": st.column_config.NumberColumn(min_value=0.0, step=0.05),
                                       "max": st.column_config.NumberColumn(min_value=0.0, step=0.05)})
    subs = {str(r.element).strip(): (float(r["min"]), float(r["max"])) for _, r in ed.dropna().iterrows() if str(r.element).strip()}
    return Site(host.strip(), float(total), subs, float(hmin))


def page_lab():
    header("Candidate Discovery Lab", "Generate constrained alloy compositions and screen them with the trained ΔH model. "
                                      "The output is a list of proposed candidate alloys, not discovered or validated materials.")
    st.info("A predicted ΔH does **not** show that a hydride forms, that it is reversible, or what its capacity is. "
            "Capacity, kinetics and stability are not predicted here.")
    try:
        P = predictor()
    except FileNotFoundError as e:
        st.error(str(e)); return
    known = sorted(P._train_elements)

    step("1 · Alloy system")
    names = list(PRESETS) + list(FREE_PRESETS)
    name = st.selectbox("Alloy system", names, key="lab_preset")
    free = name in FREE_PRESETS
    if free:
        family, ranges = FREE_PRESETS[name]
        st.caption("Free atomic fractions (sum = 1). The last element takes the remainder.")
        df = pd.DataFrame([{"element": e, "min": lo, "max": hi} for e, (lo, hi) in ranges.items()])
        ed = st.data_editor(df, num_rows="dynamic", key=f"lab_free_{name}", width="stretch")
        ranges = {str(r.element).strip(): (float(r["min"]), float(r["max"])) for _, r in ed.dropna().iterrows() if str(r.element).strip()}
        elements = set(ranges)
        family = st.selectbox("Family for the ΔS assumption", list(P.dS.index), index=list(P.dS.index).index(family)
                              if family in P.dS.index else 0, key="lab_fam_free")
    else:
        preset = PRESETS[name]
        st.caption(f"{preset.family} template: {preset.note}. Each site keeps its total, so the A:B stoichiometry is preserved.")
        sites = [_site_editor(i, s, name) for i, s in enumerate(preset.sites)]
        family = preset.family
        elements = {s.host for s in sites} | {e for s in sites for e in s.subs}

    step("2 · Grid and targets")
    c = st.columns(4)
    grid_step = c[0].number_input("Composition step", 0.01, 0.5, 0.05, 0.01, key="lab_step")
    max_n = c[1].number_input("Maximum candidates", 10, 1000, 300, 10, key="lab_max")
    seed = c[2].number_input("Random seed (used if the grid is larger)", 0, 10_000, 0, 1, key="lab_seed")
    c = st.columns(4)
    tg = Targets(c[0].number_input("Target operating T (°C)", -50.0, 300.0, 25.0, 5.0, key="lab_T"),
                 c[1].number_input("Target delivery pressure (bar)", 0.1, 200.0, 5.0, 0.5, key="lab_P"),
                 c[2].number_input("Acceptable T min (°C)", -80.0, 300.0, -20.0, 5.0, key="lab_Tmin"),
                 c[3].number_input("Acceptable T max (°C)", -50.0, 400.0, 80.0, 5.0, key="lab_Tmax"))
    with st.expander("Ranking weights and Pareto objectives"):
        wc = st.columns(4)
        weights = {k: wc[i].slider(k.replace("_", " "), 0.0, 1.0, v, 0.05, key=f"lab_w_{k}") for i, (k, v) in enumerate(DEFAULT_WEIGHTS.items())}
        pc = st.columns(2)
        ox = pc[0].selectbox("Pareto objective 1 (minimised)", list(PARETO_CHOICES), format_func=OBJ_LABEL.get, key="lab_ox")
        oy = pc[1].selectbox("Pareto objective 2 (minimised)", [o for o in PARETO_CHOICES if o != ox], format_func=OBJ_LABEL.get, key="lab_oy")

    bad = sorted(e for e in elements if e not in known)
    if bad:
        st.warning(f"Element(s) {', '.join(bad)} do not occur in the training data. Candidates containing them will be rejected.")
    if st.button("Generate and screen candidates", type="primary", key="lab_run"):
        try:
            cands = generate_free(ranges, grid_step, int(max_n), int(seed)) if free else generate_sites(sites, grid_step, int(max_n), int(seed))
        except ValueError as e:
            st.error(f"Invalid ranges: {e}"); return
        if not cands:
            st.error("No composition satisfies these ranges and site totals."); return
        with st.spinner(f"Predicting {len(cands)} candidates…"):
            res = rank(evaluate(P, cands, family, tg), tg, weights, (ox, oy))
        st.session_state["lab"] = {"res": res, "targets": tg.__dict__, "system": name, "family": family,
                                   "n_grid": cands[0]["n_grid_total"], "weights": weights, "pareto": (ox, oy)}
        st.session_state.setdefault("history", []).append({"composition": f"Lab: {name}", "ΔH_pred": None,
                                                            "interval": f"{len(cands)} candidates", "status": "screened"})
    lab = st.session_state.get("lab")
    if not lab:
        return
    show_lab(lab)


def show_lab(lab):
    res, tg = lab["res"], lab["targets"]
    ok = res[res.status == "candidate"]
    rej = res[res.status == "rejected"]
    step("3 · Results")
    c = st.columns(4)
    c[0].metric("Grid size (unique)", lab["n_grid"])
    c[1].metric("Evaluated", len(res))
    c[2].metric("Candidates in domain", len(ok))
    c[3].metric("Rejected", len(rej))
    t1, t2, t3, t4, t5 = st.tabs(["Ranked candidates", "Pareto front", "Composition map", "Rejected", "Compare & export"])
    show = ["rank", "formula", "dH_pred_kJmol", "dH_low", "dH_high", "nn_L1", "T_at_Ptarget_C", "T_at_Ptarget_low_C",
            "T_at_Ptarget_high_C", "heat_MJ_per_kgH2", "score", "pareto", "nearest_known", "nearest_known_dH_exp", "in_training_data"]
    with t1:
        st.caption(f"ESTIMATE: T(P_target = {tg['P_target_bar']:g} bar) uses ML ΔH and an assumed ΔS ({ok['dS_assumed'].iloc[0] if len(ok) else '–'} "
                   f"J/mol/K, family '{lab['family']}'). Score is normalised within this run.")
        st.dataframe(ok[show].round(3), hide_index=True, width="stretch")
        if len(ok):
            fig = go.Figure(go.Scatter(x=ok["dH_pred_kJmol"], y=ok["formula"], mode="markers",
                                       error_x=dict(type="data", symmetric=False, array=ok["dH_high"] - ok["dH_pred_kJmol"],
                                                    arrayminus=ok["dH_pred_kJmol"] - ok["dH_low"]),
                                       marker=dict(color="#1F4E79")))
            top = ok.head(25)
            fig.update_yaxes(range=[len(top) - 0.5, -0.5], title="")
            fig.update_xaxes(title="Predicted ΔH with 80% interval (kJ/mol H₂)")
            st.plotly_chart(chart_layout(fig, 520, title="Top candidates: prediction uncertainty"), width="stretch")
    with t2:
        ox, oy = lab["pareto"]
        if len(ok):
            f = px.scatter(ok, x=ox, y=oy, color=ok["pareto"].map({True: "Pareto front", False: "dominated"}),
                           hover_data=["formula", "dH_pred_kJmol", "T_at_Ptarget_C"],
                           color_discrete_map={"Pareto front": "#C0504D", "dominated": "#B8C2CC"},
                           labels={ox: OBJ_LABEL[ox], oy: OBJ_LABEL[oy], "color": ""})
            st.plotly_chart(chart_layout(f, 460, title="Trade-off between the two selected objectives (both minimised)"), width="stretch")
            st.dataframe(ok[ok.pareto][show].round(3), hide_index=True, width="stretch")
            st.caption("Non-dominated candidates are shown even when their weighted score is lower.")
        f = px.histogram(res.dropna(subset=["dH_pred_kJmol"]), x="dH_pred_kJmol", color="status", nbins=30,
                         labels={"dH_pred_kJmol": "Predicted ΔH (kJ/mol H₂)"}, color_discrete_map={"candidate": "#1F4E79", "rejected": "#C0504D"})
        st.plotly_chart(chart_layout(f, 320, title="Predicted ΔH distribution"), width="stretch")
    with t3:
        import re
        wide = pd.DataFrame([{e: float(v) for e, v in re.findall(r"([A-Z][a-z]?)([0-9.]+)", f)} for f in res["formula"]],
                            index=res.index).fillna(0.0)
        var = [c for c in wide.columns if wide[c].nunique() > 1]
        if len(var) >= 2:
            cc = st.columns(2)
            xa = cc[0].selectbox("x", var, 0, key="lab_mx")
            ya = cc[1].selectbox("y", [v for v in var if v != xa], 0, key="lab_my")
            m = res.join(wide)
            f = px.scatter(m, x=xa, y=ya, color="dH_pred_kJmol", symbol="status", hover_data=["formula", "nn_L1"],
                           color_continuous_scale="Viridis", labels={xa: f"{xa} (per f.u.)", ya: f"{ya} (per f.u.)", "dH_pred_kJmol": "ΔH pred"})
            st.plotly_chart(chart_layout(f, 460, title="Composition map coloured by predicted ΔH"), width="stretch")
        else:
            st.caption("The map needs at least two varying elements.")
    with t4:
        st.dataframe(rej[["formula", "reasons", "dH_pred_kJmol", "nn_L1", "nearest_known"]].round(3), hide_index=True, width="stretch")
    with t5:
        pick = st.multiselect("Candidates to compare", ok["formula"].tolist(), ok["formula"].head(3).tolist(), key="lab_cmp")
        if pick:
            P = predictor()
            import numpy as np
            T = np.linspace(-50, 200, 200) + 273.15
            fig = go.Figure()
            for f_ in pick:
                r = ok[ok.formula == f_].iloc[0]
                dS_lo, dS, dS_hi, _ = P.dS_for(lab["family"])
                cen, lo, hi = P.vant_hoff_band(T, r.dH_low, r.dH_pred_kJmol, r.dH_high, dS_lo, dS, dS_hi)
                fig.add_trace(go.Scatter(x=T - 273.15, y=cen, name=f"{f_} (ESTIMATE)"))
            fig.add_hline(y=tg["P_target_bar"], line_dash="dot", annotation_text=f"target {tg['P_target_bar']:g} bar")
            fig.update_yaxes(type="log", range=[-3, 3], title="Estimated P_eq (bar)")
            fig.update_xaxes(title="Temperature (°C)")
            st.plotly_chart(chart_layout(fig, 420, title="Estimated Van't Hoff lines (central values)"), width="stretch")
        exp = res.copy()
        exp["targets_json"] = json.dumps({**tg, "system": lab["system"], "weights": lab["weights"]})
        exp["evidence_class"] = exp["status"].map({"candidate": "provisional (ML estimate, in domain)",
                                                   "rejected": "insufficient evidence / rejected"})
        exp["note"] = "Proposed composition; not synthesised or validated; hydride formation and capacity not implied"
        st.download_button("Download all candidates (CSV)", exp.to_csv(index=False), "candidate_alloys.csv", "text/csv", key="lab_dl")
