"""Cached loaders for the result tables used by the app (read-only; nothing is recomputed here)."""
from __future__ import annotations

import json
from pathlib import Path

import pandas as pd
import streamlit as st

from .predictor import MANIFEST_PATH, Predictor

ROOT = Path(__file__).resolve().parents[2]
M = ROOT / "results/metrics"
T = ROOT / "results/tables"
P = ROOT / "data/processed"


@st.cache_resource(show_spinner="Loading trained model bundle…")
def predictor() -> Predictor:
    return Predictor()


@st.cache_data
def manifest() -> dict:
    return json.loads(MANIFEST_PATH.read_text()) if MANIFEST_PATH.exists() else {}


@st.cache_data
def csv(rel: str) -> pd.DataFrame:
    return pd.read_csv(ROOT / rel)


@st.cache_data
def n_cv_groups() -> int:
    from ..models.groups import near_composition_groups
    return int(len(set(near_composition_groups(csv("data/processed/features_dH.csv")["comp_key"]))))


@st.cache_data
def pci_points() -> pd.DataFrame:
    from ..thermodynamics.pci_kinetics import load_all_pci
    pts, _ = load_all_pci()
    return pts


def material_label(pid: str) -> str:
    import re
    return re.sub(r"\[([0-9.]+)\]", lambda m: "" if m.group(1) == "1" else m.group(1), pid)
