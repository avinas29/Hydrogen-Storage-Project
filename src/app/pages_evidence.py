"""Dataset & Evidence Explorer: provenance, quality flags and coverage (read-only)."""
from __future__ import annotations

import plotly.express as px
import streamlit as st

from .data import csv
from .recommend import experimental_pool
from .ui import chart_layout, header

PROVENANCE = """
| Label used in the app | Meaning |
|---|---|
| **experimental (.mh)** | value written in a Purdue Metal Hydride Toolbox file, citing a paper |
| **fit to digitised isotherms** | ΔH/ΔS fitted by the Purdue curators to digitised PCI curves (`From Isotherms: true`) |
| **digitised literature** | PCI points digitised from published figures; ΔH re-fitted in this project |
| **ML-HydPARK (literature)** | value from the ML-HydPARK v0.0.5 table (4 appended blocks; block 0 has no references) |
| **ML prediction / ESTIMATE** | Random Forest ΔH, with assumed ΔS for thermodynamic windows |
| **reported capacity** | wt% as written; reversibility usually not stated |
"""


def page_evidence():
    header("Dataset & Evidence Explorer", "Where every number comes from, how reliable it is, and what is missing.")
    t1, t2, t3, t4 = st.tabs(["Datasets", "Purdue materials & evidence", "Missing data", "Provenance legend"])
    with t1:
        c = st.columns(2)
        dist = csv("results/tables/material_class_distribution.csv")
        f = px.bar(dist, x="material_class", y="n_records", color="dataset", barmode="group",
                   labels={"material_class": "Material class", "n_records": "Records"}, color_discrete_sequence=["#1F4E79", "#C0504D"])
        c[0].plotly_chart(chart_layout(f, 340, title="Records per class (raw datasets)"), width="stretch")
        c[1].markdown("**Composition overlap between the datasets**")
        c[1].dataframe(csv("results/tables/composition_overlap.csv"), hide_index=True, width="stretch")
        st.markdown("**Agreement on shared compositions** (HydPARK largely reproduces Purdue/Sandia values, so there is no external validation)")
        st.dataframe(csv("results/tables/cross_dataset_agreement_stats.csv").round(2), hide_index=True, width="stretch")
    with t2:
        pool = experimental_pool()
        ev = pool["evidence_class"].value_counts().rename_axis("evidence class").reset_index(name="materials")
        c = st.columns([1, 2])
        c[0].dataframe(ev, hide_index=True, width="stretch")
        flags = {k: int(pool[k].sum()) for k in ["flag_unverified_ref_sandia", "flag_pci_dH_inconsistent", "flag_dS_atypical",
                                                 "flag_identical_values_other_file", "flag_pseudo_element", "flag_thermo_refit_from_isotherms"]}
        c[1].dataframe({"flag": list(flags), "materials": list(flags.values())}, hide_index=True, width="stretch")
        fam = st.multiselect("Family", sorted(pool.family.unique()), key="ev_fam")
        evs = st.multiselect("Evidence class", sorted(pool.evidence_class.unique()), key="ev_cls")
        mask = pool.family.isin(fam) if fam else pool.family.notna() | True
        if evs:
            mask &= pool.evidence_class.isin(evs)
        v = pool[mask]
        st.dataframe(v[["name", "family", "evidence_class", "evidence_notes", "dH_kJmol_weighted", "dS_JmolK_weighted",
                        "wt_pct", "capacity_definition", "rho_kg_m3_stated", "hyst_ln_Pa_Pd_25C", "pci_file"]].round(2),
                     hide_index=True, width="stretch")
    with t3:
        st.dataframe(csv("results/tables/missing_value_summary.csv"), hide_index=True, width="stretch")
        st.caption("'toolbox_substitutes_default_if_missing' = the MATLAB toolbox would fill a type default; this project never does.")
    with t4:
        st.markdown(PROVENANCE)
        st.caption("Reports: reports/data_audit.md, dataset_comparison.md, ml_results.md, thermodynamics.md, pci_kinetics.md, screening.md.")
