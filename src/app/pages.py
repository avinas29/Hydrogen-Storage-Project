"""Core pages: Overview, Property Predictor, Thermodynamic Explorer, Model Performance, Material Comparison.

All numbers come from the live model or saved result files.
"""
from __future__ import annotations

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from ..thermodynamics.vant_hoff import LHV_H2_MJ_PER_KG, M_H2, peq_bar
from .data import csv, manifest, material_label, n_cv_groups, pci_points, predictor
from .predictor import CompositionError
from .ui import EVIDENCE_KIND, badges, chart_layout, header

FAMILY_COLORS = {"AB5": "#1F4E79", "AB2": "#C0504D", "AB": "#4F8A5B", "AB3": "#8E6BB0", "A2B7": "#7A4B5E",
                 "A2B": "#9A8F3A", "SS": "#5B9BD5", "Mg": "#D69B2D", "Complex": "#333333", "MIC": "#A0667F",
                 "Misc": "#8C8C8C", "(missing)": "#BBBBBB"}
ESTIMATE_NOTE = ("**Estimate.** Predicted ΔH (ML) combined with an *assumed* ΔS (family median of experimental Purdue values). "
                 "This is not an experimental measurement.")


def _fmt(x, nd=2):
    return "–" if x is None or (isinstance(x, float) and not np.isfinite(x)) else f"{x:.{nd}f}"


def _nav(label: str):
    st.session_state["nav"] = label


# =============================================================================
def page_overview():
    man = manifest()
    header("Overview", "ML-assisted prediction, candidate generation and application-specific selection of metal hydrides. "
                       "There is no universally best hydride: the right choice depends on temperature, pressure, heat and demand.")
    d = csv("data/processed/features_dH.csv")
    cv = csv("results/metrics/dH_cv_summary.csv")
    hold = csv("results/metrics/dH_holdout_metrics.csv")
    rf = cv[(cv.model == "RandomForest") & (cv.feature_set == man.get("feature_set", "composition"))].iloc[0]
    fam_base = cv[cv.model == "FamilyMedianBaseline"].iloc[0]
    rf_hold = hold[hold.model == "RandomForest"].iloc[0]
    exp = csv("results/tables/screening_candidates.csv")

    st.markdown("##### ΔH model performance (nested grouped cross-validation)")
    c = st.columns(5)
    c[0].metric("Training compositions", f"{len(d)}", help=f"{n_cv_groups()} near-composition CV groups")
    c[1].metric("CV MAE, kJ/mol H₂", f"{rf.MAE:.2f} ± {rf.MAE_sd:.2f}")
    c[2].metric("CV R²", f"{rf.R2:.2f}")
    c[3].metric("Hold-out MAE", f"{rf_hold.MAE:.2f}")
    c[4].metric("Family-median baseline MAE", f"{fam_base.MAE:.2f}")
    st.caption("These metrics describe the **ΔH model only**. Application recommendations have no ground-truth "
               "performance metric. They are rule-based screenings of experimental data and must be validated by measurement.")

    st.markdown("##### Workflows")
    w = st.columns(4)
    for col, (title, text, target) in zip(w, [
        ("Property Predictor", "ΔH, interval and domain check for one composition.", "Property Predictor"),
        ("Candidate Discovery Lab", "Generate constrained alloy grids and screen them with the model.", "Candidate Discovery Lab"),
        ("Application Designer", "Describe an application and get tailored recommendations.", "Application Requirement Designer"),
        ("Dataset & Evidence", "Provenance, flags and coverage of the data.", "Dataset & Evidence Explorer")]):
        with col.container(border=True):
            st.markdown(f"**{title}**")
            st.caption(text)
            st.button("Open", key=f"go_{target}", on_click=_nav, args=(target,), width="stretch")

    left, right = st.columns([1, 1])
    with left:
        st.markdown("##### Dataset coverage")
        fam = d["family"].fillna("(missing)").value_counts().rename_axis("family").reset_index(name="compositions")
        fig = px.bar(fam, x="family", y="compositions", color="family", color_discrete_map=FAMILY_COLORS,
                     labels={"family": "Material family", "compositions": "ΔH training compositions"})
        st.plotly_chart(chart_layout(fig, 300, showlegend=False), width="stretch")
        st.caption(f"{len(exp)} experimental Purdue materials are available for application screening "
                   f"({exp['data_quality_pass'].sum()} pass the data-quality gate).")
    with right:
        st.markdown("##### Model")
        st.markdown(f"""
| | |
|---|---|
| Estimator | {man.get('estimator')}, {man.get('n_estimators')} trees, `{man.get('hyperparameters')}` |
| Inputs | {man.get('n_features')} composition descriptors (no ΔS, P, T or capacity) |
| Interval | {man.get('interval')} |
| Applicability domain | nearest training composition at L1 ≤ {man.get('applicability_domain_L1')} |
| Artifact | `{man.get('bundle_file')}` |
""")
        lofo = csv("results/metrics/dH_leave_family_out.csv")
        piv = lofo.pivot(index="held_out_family", columns="model", values="MAE")
        worse = [f for f in piv.index if piv.loc[f, "RandomForest"] > piv.loc[f, "MeanBaseline (other families)"]]
        st.warning(f"**Limitation:** the model does not extrapolate to unseen families. Trained without them, it is worse "
                   f"than a mean for {', '.join(worse)}. Predictions are trusted only inside the calibrated domain.")
    hist = st.session_state.get("history", [])
    if hist:
        st.markdown("##### Activity this session")
        st.dataframe(pd.DataFrame(hist[::-1]), hide_index=True, width="stretch")


# =============================================================================
def page_predict():
    header("Property Predictor", "Live ΔH prediction from composition, with calibrated uncertainty and an applicability-domain check.")
    try:
        P = predictor()
    except FileNotFoundError as e:
        st.error(str(e)); return
    with st.form("predict"):
        c = st.columns([3, 1])
        text = c[0].text_input("Alloy composition", key="comp_input", placeholder="e.g. LaNi4.2Al0.8 or TiFe0.75Mn0.25",
                               help="Formats: LaNi4.2Al0.8 · (Ti0.8Zr0.2)(Cr0.5Mn0.5)2 · Ti[1]Fe[0.9]Mn[0.1] · V75Ti17.5Zr7.5. "
                                    "Enter the hydrogen-free alloy.")
        c[1].markdown("<div style='height:1.75rem'></div>", unsafe_allow_html=True)
        go_ = c[1].form_submit_button("Predict ΔH", type="primary", width="stretch")
    if go_:
        try:
            pred = P.predict(text)
            st.session_state["pred"] = pred
            st.session_state.setdefault("history", []).append(
                {"composition": pred.comp_key, "ΔH_pred": round(pred.dH_pred, 2),
                 "interval": f"{pred.interval[0]:.1f}–{pred.interval[1]:.1f}", "status": pred.reliability})
        except CompositionError as e:
            st.session_state.pop("pred", None)
            st.error(f"Invalid composition: {e}")
            return
    pred = st.session_state.get("pred")
    if pred is None:
        st.info("Enter a composition and press **Predict ΔH**. The model computes the result live.")
        return
    show_prediction(P, pred)


def show_prediction(P, pred):
    lo, hi = pred.interval
    st.subheader(f"{pred.input_text} → {pred.comp_key}")
    kind = {"in-domain": "ok", "in-training": "info", "OUTSIDE DOMAIN": "bad"}[pred.reliability]
    badges((pred.reliability, kind), (f"NN distance L1 = {pred.nn_distance:.3f}", "info"), ("ML prediction", "warn"))
    if pred.reliability == "OUTSIDE DOMAIN":
        st.error("**Outside the calibrated applicability domain. This value is an unreliable extrapolation.** " + " ".join(pred.warnings))
    elif pred.in_training:
        st.info(" ".join(pred.warnings))
    c = st.columns(4)
    label = "Predicted ΔH (UNRELIABLE)" if pred.reliability == "OUTSIDE DOMAIN" else "Predicted ΔH"
    c[0].metric(f"{label}, kJ/mol H₂", f"{pred.dH_pred:.1f}")
    c[1].metric("80% prediction interval", f"{lo:.1f} – {hi:.1f}")
    c[2].metric("Distance to nearest training comp. (L1)", f"{pred.nn_distance:.3f}")
    c[3].metric("Typical |error| at this distance (OOF MAE)", f"{pred.bin_MAE:.1f}")
    if pred.in_training:
        r = pred.training_row
        c = st.columns(3)
        c[0].metric("Experimental ΔH in training data", f"{r['dH_kJmol']:.2f}")
        c[1].metric("Out-of-fold prediction (model not trained on it)", _fmt(r.get("oof_pred_mean")))
        c[2].metric("Source", f"{r['value_source']}")
    st.caption(f"Interval: 10–90% quantiles of out-of-fold residuals for training compositions in the same nearest-neighbour "
               f"distance bin {pred.interval_bin}. For compositions in the training set, distance is measured to the nearest *other* composition.")

    left, right = st.columns([1.35, 1])
    with left:
        st.markdown("**5 nearest training compositions (experimental ΔH)**")
        nb = pred.neighbours.copy()
        nb["source"] = np.where(nb["value_source"] == "purdue", "Purdue .mh (experimental)", "ML-HydPARK (literature)")
        nb["purdue_id"] = nb["purdue_id"].fillna("")
        st.dataframe(nb[["comp_key", "L1_distance", "family", "dH_experimental_kJmol", "source", "purdue_id"]].round(3),
                     hide_index=True, width="stretch")
    with right:
        fam = P.nearest_family(pred)
        dS_lo, dS, dS_hi, famu = P.dS_for(fam)
        st.markdown("**Thermodynamic estimate**")
        rows = []
        for p in (1, 10):
            t, tl, th = P.T_for_pressure(p, lo, pred.dH_pred, hi, dS_lo, dS, dS_hi)
            rows.append({"pressure (bar)": p, "T estimate (°C)": round(t, 0), "band (°C)": f"{tl:.0f} – {th:.0f}"})
        st.dataframe(pd.DataFrame(rows), hide_index=True, width="stretch")
        st.caption(f"{ESTIMATE_NOTE} ΔS = {dS:.1f} J mol⁻¹ K⁻¹ (IQR {dS_lo:.1f}–{dS_hi:.1f}; family '{famu}'). "
                   f"Heat ≈ {pred.dH_pred / M_H2:.1f} MJ/kg H₂. Details are on the **Thermodynamic Explorer** page.")
    with st.expander("Parsed composition and the 38 descriptors passed to the model"):
        st.write({k: round(v, 4) for k, v in pred.composition.items()})
        st.dataframe(pred.features.rename("value").to_frame().T, width="stretch")


# =============================================================================
def page_vant_hoff():
    header("Thermodynamic Explorer", "Van't Hoff plateau pressure vs temperature for the current predicted composition, "
                                     "with experimental lines of its nearest known neighbours.")
    try:
        P = predictor()
    except FileNotFoundError as e:
        st.error(str(e)); return
    pred = st.session_state.get("pred")
    if pred is None:
        st.info("Make a prediction on the **Property Predictor** page first.")
        st.button("Go to Property Predictor", on_click=_nav, args=("Property Predictor",))
        return
    st.warning(ESTIMATE_NOTE)
    if pred.reliability == "OUTSIDE DOMAIN":
        st.error("The ΔH used here comes from a composition outside the applicability domain, so the window below is not meaningful.")
    fams = list(P.dS.index)
    default_fam = P.nearest_family(pred)
    default_fam = default_fam if default_fam in fams else "(all)"
    c = st.columns([1.2, 1, 1])
    fam = c[0].selectbox("Family for the ΔS assumption", fams, index=fams.index(default_fam),
                         help="Default: the family of the nearest training composition. '(all)' = all single-plateau Purdue materials.")
    dS_lo, dS, dS_hi, fam = P.dS_for(fam)
    Trange = c[1].slider("Temperature range (°C)", -80, 400, (-20, 150))
    pressures = c[2].multiselect("Pressures of interest (bar)", [0.5, 1, 2, 5, 10, 20, 30, 50, 100], default=[1, 10])
    dH_lo, dH_hi = pred.interval
    badges((f"ΔH {pred.dH_pred:.1f} kJ/mol (ML, {dH_lo:.1f}–{dH_hi:.1f})", "warn"),
           (f"ΔS {dS:.1f} J/mol/K (assumed, IQR {dS_lo:.1f}–{dS_hi:.1f}, '{fam}')", "warn"), ("P₀ = 1 atm", "info"))

    T = np.linspace(Trange[0], Trange[1], 300) + 273.15
    centre, lo, hi = P.vant_hoff_band(T, dH_lo, pred.dH_pred, dH_hi, dS_lo, dS, dS_hi)
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=T - 273.15, y=hi, line=dict(width=0), showlegend=False, hoverinfo="skip"))
    fig.add_trace(go.Scatter(x=T - 273.15, y=lo, fill="tonexty", fillcolor="rgba(192,80,77,0.15)", line=dict(width=0),
                             name="band: ΔH interval × ΔS IQR"))
    fig.add_trace(go.Scatter(x=T - 273.15, y=centre, line=dict(color="#C0504D", width=3), name="ESTIMATE (ML ΔH, assumed ΔS)"))
    pc = csv("data/processed/purdue_cleaned.csv").set_index("purdue_id")
    shown = 0
    for _, r in pred.neighbours.iterrows():
        pid = r["purdue_id"]
        if isinstance(pid, str) and pid and pid in pc.index and not pc.loc[pid, "flag_multi_plateau"] and shown < 2:
            q = pc.loc[pid]
            fig.add_trace(go.Scatter(x=T - 273.15, y=peq_bar(T, q["dH_kJmol"], q["dS_JmolK"]), line=dict(color="#1F4E79", dash="dash"),
                                     name=f"experimental: {material_label(pid)} (L1 {r['L1_distance']:.3f})"))
            shown += 1
    for p in pressures:
        fig.add_hline(y=p, line=dict(color="#8C8C8C", width=1, dash="dot"), annotation_text=f"{p:g} bar", annotation_position="top left")
    fig.update_yaxes(type="log", title="Equilibrium desorption pressure P_eq (bar)", range=[-3, 3])
    fig.update_xaxes(title="Temperature (°C)")
    st.plotly_chart(chart_layout(fig, 480, title=f"{pred.comp_key}: ESTIMATED plateau pressure vs temperature"), width="stretch")
    rows = []
    for p in sorted(pressures):
        c_, l_, h_ = P.T_for_pressure(p, dH_lo, pred.dH_pred, dH_hi, dS_lo, dS, dS_hi)
        rows.append({"pressure (bar)": p, "estimated T (°C)": round(c_, 1), "band low (°C)": round(l_, 1),
                     "band high (°C)": round(h_, 1), "basis": "ESTIMATE"})
    if rows:
        st.dataframe(pd.DataFrame(rows), hide_index=True, width="stretch")
    s_rows = []
    for s in (dS_lo, dS, dS_hi):
        t = P.T_for_pressure(1.0, pred.dH_pred, pred.dH_pred, pred.dH_pred, s, s, s)[0]
        s_rows.append({"assumed ΔS (J/mol/K)": round(s, 1), "T(1 bar) at predicted ΔH (°C)": round(t, 1)})
    st.markdown("**Sensitivity to the ΔS assumption**")
    st.dataframe(pd.DataFrame(s_rows), hide_index=True, width="stretch")
    q = pred.dH_pred / M_H2
    st.caption(f"Estimated reaction heat: {q:.1f} MJ per kg H₂ ({100*q/LHV_H2_MJ_PER_KG:.0f}% of the H₂ lower heating value). "
               "Flat-plateau model; slope and hysteresis are ignored.")


# =============================================================================
def page_performance():
    header("Model Performance", "Read from results/metrics/*.csv, written by src/models/train.py (nested grouped CV). Nothing is hardcoded.")
    cv = csv("results/metrics/dH_cv_summary.csv")
    hold = csv("results/metrics/dH_holdout_metrics.csv")
    t1, t2, t3, t4, t5 = st.tabs(["Grouped CV and hold-out", "Actual vs predicted", "By family / leave-family-out",
                                  "Applicability calibration", "Capacity (wt%)"])
    with t1:
        st.dataframe(cv[["feature_set", "model", "MAE", "MAE_sd", "RMSE", "RMSE_sd", "R2", "R2_sd", "n"]].round(3),
                     hide_index=True, width="stretch")
        fig = px.bar(cv.assign(label=cv.model + " [" + cv.feature_set + "]"), x="label", y="MAE", error_y="MAE_sd",
                     color="feature_set", labels={"label": "", "MAE": "CV MAE (kJ/mol H₂)", "feature_set": "feature set"},
                     color_discrete_sequence=["#8C8C8C", "#5B9BD5", "#1F4E79"])
        nf = csv("results/tables/cross_dataset_agreement_stats.csv").set_index("subset").loc["Purdue ref = DOI/other", "dH_MAE_kJmol"]
        fig.add_hline(y=nf, line_dash="dash", line_color="#C0504D", annotation_text=f"inter-source scatter ≈ {nf:.1f}")
        st.plotly_chart(chart_layout(fig, 380), width="stretch")
        st.markdown(f"**Grouped 80/20 hold-out** ({hold.feature_set.iloc[0]}). The model was selected by CV, not by its hold-out score.")
        st.dataframe(hold[["model", "MAE", "RMSE", "R2", "n", "params"]].round(3), hide_index=True, width="stretch")
        st.dataframe(csv("results/metrics/dH_grouping_effect.csv").round(3), hide_index=True, width="stretch")
    with t2:
        src = st.radio("Predictions", ["Hold-out set (single grouped split)", "Out-of-fold, nested CV (mean of 3 repeats)"], horizontal=True)
        m = st.selectbox("Model", ["RandomForest", "GradientBoosting", "Ridge"])
        if src.startswith("Hold"):
            h = csv("results/metrics/dH_holdout_predictions.csv")
            df = pd.DataFrame({"reported": h["y"], "predicted": h[m], "family": h["family"], "composition": h["comp_key"]})
        else:
            o = csv("results/metrics/dH_oof_predictions.csv")
            o = o[(o.model == m) & (o.feature_set == "composition")]
            g = o.groupby("row").agg(reported=("y", "first"), predicted=("pred", "mean"), family=("family", "first")).reset_index()
            df = g.assign(composition=g["row"].map(csv("data/processed/features_dH.csv")["comp_key"]))
        df["residual"] = df["predicted"] - df["reported"]
        c = st.columns(2)
        f1 = px.scatter(df, x="reported", y="predicted", color="family", hover_data=["composition"], color_discrete_map=FAMILY_COLORS,
                        title=f"{m}: MAE {df['residual'].abs().mean():.2f} kJ/mol (n = {len(df)})",
                        labels={"reported": "Reported ΔH (kJ/mol H₂)", "predicted": "Predicted ΔH (kJ/mol H₂)"})
        lim = [0, float(max(df.reported.max(), df.predicted.max())) * 1.05]
        f1.add_trace(go.Scatter(x=lim, y=lim, mode="lines", line=dict(color="black", dash="dash"), showlegend=False))
        c[0].plotly_chart(chart_layout(f1, 450), width="stretch")
        f2 = px.scatter(df, x="predicted", y="residual", color="family", hover_data=["composition"], color_discrete_map=FAMILY_COLORS,
                        title="Residuals (predicted − reported)",
                        labels={"predicted": "Predicted ΔH (kJ/mol H₂)", "residual": "Residual (kJ/mol)"})
        f2.add_hline(y=0, line_color="black")
        c[1].plotly_chart(chart_layout(f2, 450), width="stretch")
    with t3:
        lofo = csv("results/metrics/dH_leave_family_out.csv")
        piv = lofo.pivot(index="held_out_family", columns="model", values="MAE")
        st.error(f"**Generalisation limit.** Trained without the family, the model is worse than the other-family mean for "
                 f"AB5 ({piv.loc['AB5','RandomForest']:.2f} vs {piv.loc['AB5','MeanBaseline (other families)']:.2f} kJ/mol) and "
                 f"SS ({piv.loc['SS','RandomForest']:.2f} vs {piv.loc['SS','MeanBaseline (other families)']:.2f}).")
        fig = px.bar(lofo, x="held_out_family", y="MAE", color="model", barmode="group",
                     labels={"held_out_family": "Held-out family", "MAE": "MAE on held-out family (kJ/mol)"},
                     color_discrete_sequence=["#8C8C8C", "#C0504D"])
        st.plotly_chart(chart_layout(fig, 360), width="stretch")
        fam = csv("results/metrics/dH_cv_by_family.csv")
        st.dataframe(fam[fam.model.isin(["RandomForest", "FamilyMedianBaseline"]) & fam.feature_set.isin(["composition", "-"])]
                     [["model", "family", "MAE", "MAE_sd", "R2", "n"]].round(2), hide_index=True, width="stretch")
        st.dataframe(csv("results/metrics/dH_within_family.csv").round(2), hide_index=True, width="stretch")
    with t4:
        cal = csv("results/tables/applicability_domain_calibration.csv")
        fig = px.bar(cal, x="bin", y="MAE", text=cal["n"].map(lambda n: f"n={n}"),
                     labels={"bin": "Distance to nearest training composition (L1)", "MAE": "Out-of-fold MAE (kJ/mol)"},
                     color_discrete_sequence=["#1F4E79"])
        fig.add_vline(x=2.5, line_dash="dash", line_color="#C0504D", annotation_text="domain limit 0.15")
        st.plotly_chart(chart_layout(fig, 360), width="stretch")
        st.dataframe(cal.round(2), hide_index=True, width="stretch")
    with t5:
        st.warning("The capacity (wt%) model barely beats a one-parameter-per-family physics baseline. It is **not used** anywhere as a capacity estimate.")
        st.dataframe(csv("results/metrics/wt_cv_summary.csv").round(3), hide_index=True, width="stretch")


# =============================================================================
def page_compare():
    header("Material Comparison", "Experimental Purdue materials side by side. Each value carries its provenance, and missing data are shown as missing.")
    vh = csv("results/tables/vant_hoff_purdue.csv")
    pc = csv("data/processed/purdue_cleaned.csv").set_index("purdue_id")
    fits = csv("results/tables/pci_vant_hoff_fits.csv")
    from .recommend import experimental_pool
    pool = experimental_pool().set_index("purdue_id")
    try:
        tr = predictor().train.set_index("comp_key")
    except FileNotFoundError:
        tr = pd.DataFrame()
    ids = sorted(vh["purdue_id"].unique(), key=material_label)
    default = [i for i in ["La[1]Ni[5]", "Ti[1]Fe[1]", "Ti[1]Fe[0.9]Mn[0.1]", "Mg[2]Ni[1]"] if i in ids]
    sel = st.multiselect("Materials", ids, default=default, format_func=material_label)
    if not sel:
        st.info("Select one or more materials."); return
    rows = []
    for pid in sel:
        q, e = pc.loc[pid], pool.loc[pid]
        for _, r in vh[vh.purdue_id == pid].iterrows():
            ck = q["comp_key"]
            ml = tr.loc[ck, "oof_pred_mean"] if isinstance(ck, str) and ck in tr.index else np.nan
            f = fits[(fits.material_id == pid) & (fits["mode"] == "des") & ~fits.multi_plateau_excluded]
            rows.append({
                "material": material_label(pid) + (f" (plateau {r.plateau}/{r.n_plateaus})" if r.n_plateaus > 1 else ""),
                "family": r.family, "evidence": e["evidence_class"],
                "ΔH exp. (kJ/mol)": r.dH_kJmol, "ΔS exp. (J/mol/K)": r.dS_JmolK,
                "ΔH source": "fit to digitised isotherms (Purdue curators)" if r.flag_thermo_from_isotherm_fit else "literature value (.mh)",
                "P(25 °C) bar": r.Pdes_bar_25C, "T(1 bar) °C": r.T_C_at_1bar, "T(10 bar) °C": r.T_C_at_10bar,
                "heat MJ/kg H₂": r.heat_MJ_per_kgH2, "Pabs/Pdes 25 °C": r.hysteresis_ratio_Pa_Pd_25C,
                "reported wt% (definition varies)": r.wt_pct_reported, "capacity note": r.capacity_definition,
                "density kg/m³ (stated)": q["rho_kg_m3"], "k_eff W/m/K": q["keff_W_mK"], "Cp J/kg/K": q["cp_J_kgK"],
                "Ea abs kJ/mol": q["kin_abs_Ea_Jmol"] / 1000, "Ea des kJ/mol": q["kin_des_Ea_Jmol"] / 1000,
                "ΔH from PCI curves (digitised literature)": f["dH_fit_kJmol"].iloc[0] if len(f) else np.nan,
                "ΔH ML estimate (out-of-fold)": ml if r.n_plateaus == 1 else np.nan,
            })
    tab = pd.DataFrame(rows)
    tab["P(25 °C) bar"] = tab["P(25 °C) bar"].map(lambda v: f"{v:.3g}")
    st.dataframe(tab.style.format(precision=2, na_rep="– (no data)"), hide_index=True, width="stretch")
    st.caption("Experimental = .mh file value. 'Digitised literature' = this project's Van't Hoff fit to the digitised PCI curves. "
               "'ML estimate' = out-of-fold prediction from a model that did not see the composition. Capacities are reported "
               "material-level values (definition varies), not ML predictions.")
    st.download_button("Download comparison (CSV)", tab.assign(basis="see column headers; '– (no data)' = not reported").to_csv(index=False),
                       "material_comparison.csv", "text/csv")
    T = np.linspace(230, 700, 300)
    fig = go.Figure()
    for _, r in vh[vh.purdue_id.isin(sel)].iterrows():
        name = material_label(r.purdue_id) + (f" p{r.plateau}" if r.n_plateaus > 1 else "")
        fig.add_trace(go.Scatter(x=T - 273.15, y=peq_bar(T, r.dH_kJmol, r.dS_JmolK), name=f"{name} (experimental)"))
    fig.add_hrect(y0=1, y1=10, fillcolor="#4F8A5B", opacity=0.07, line_width=0)
    fig.update_yaxes(type="log", range=[-3, 3], title="Desorption plateau pressure (bar)")
    fig.update_xaxes(title="Temperature (°C)")
    st.plotly_chart(chart_layout(fig, 440, title="Van't Hoff lines from experimental ΔH, ΔS (shaded: 1–10 bar)"), width="stretch")
    with_pci = [p for p in sel if isinstance(pc.loc[p, "pci_file"], str) and pc.loc[p, "pci_file"]]
    if with_pci:
        pick = st.selectbox("Digitised PCI isotherms (literature figures)", with_pci, format_func=material_label)
        s = pci_points()
        s = s[s.material_id == pick].sort_values(["curve_id", "wt_pct"])
        f2 = px.line(s, x="wt_pct", y="P_bar", color=s["T_K"].astype(str) + " K", line_dash="mode", markers=True,
                     labels={"wt_pct": "H content (wt%)", "P_bar": "Pressure (bar)", "color": "T"})
        f2.update_yaxes(type="log")
        st.plotly_chart(chart_layout(f2, 400, title=f"{material_label(pick)}: digitised PCI curves (solid = abs, dash = des)"), width="stretch")
