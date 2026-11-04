"""METAL HYDRIDE AI: Intelligent Discovery & Application-Specific Hydrogen Storage Materials Selection.

Run from the project root:
    .venv/bin/streamlit run app.py
Then open http://localhost:8501
"""
import streamlit as st

from src.app.pages import page_compare, page_overview, page_performance, page_predict, page_vant_hoff
from src.app.pages_designer import page_designer
from src.app.pages_evidence import page_evidence
from src.app.pages_lab import page_lab
from src.app.ui import setup

st.set_page_config(page_title="Metal Hydride AI", page_icon="⚗️", layout="wide")
setup()

PAGES = {
    "Overview": page_overview,
    "Property Predictor": page_predict,
    "Candidate Discovery Lab": page_lab,
    "Application Requirement Designer": page_designer,
    "Material Comparison": page_compare,
    "Thermodynamic Explorer": page_vant_hoff,
    "Model Performance": page_performance,
    "Dataset & Evidence Explorer": page_evidence,
}
with st.sidebar:
    st.markdown('<div class="mh-brand">METAL HYDRIDE AI</div>'
                '<div class="mh-brand-sub">Intelligent Discovery &amp; Application-Specific Hydrogen Storage Materials Selection</div>',
                unsafe_allow_html=True)
    st.divider()
    if st.session_state.get("nav") not in PAGES:
        st.session_state["nav"] = "Overview"
    choice = st.radio("Navigation", list(PAGES), key="nav", label_visibility="collapsed")
    st.divider()
    current = st.empty()   # filled after the page runs, so it reflects this run's prediction
    st.caption("ΔH model: Random Forest on 38 composition descriptors (725 compositions). Live predictions; estimates are labelled.")

PAGES[choice]()

pred = st.session_state.get("pred")
if pred is not None:
    current.caption(f"Current composition: **{pred.comp_key}** · ΔH {pred.dH_pred:.1f} kJ/mol ({pred.reliability})")
