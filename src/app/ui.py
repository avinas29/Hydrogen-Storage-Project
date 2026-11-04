"""Shared look and feel: CSS, page header, badges, chart defaults."""
from __future__ import annotations

import plotly.io as pio
import streamlit as st

NAVY = "#1F4E79"
CSS = """
<style>
html, body, [class*="css"] { font-feature-settings: "tnum"; }
.block-container { padding-top: 1.6rem; padding-bottom: 3rem; max-width: 1320px; }
h1 { font-size: 1.65rem !important; font-weight: 650 !important; letter-spacing: -0.01em; margin-bottom: .1rem !important; }
h2 { font-size: 1.2rem !important; font-weight: 620 !important; }
h3 { font-size: 1.02rem !important; font-weight: 620 !important; }
.mh-sub { color: #5B6B7C; font-size: .92rem; margin: 0 0 1.1rem 0; }
.mh-brand { font-weight: 750; letter-spacing: .06em; color: #1F4E79; font-size: 1.02rem; }
.mh-brand-sub { color: #5B6B7C; font-size: .76rem; line-height: 1.25; margin-top: .15rem; }
div[data-testid="stMetric"] { background: #FFFFFF; border: 1px solid #E3E8EF; border-radius: 10px; padding: .65rem .9rem;
  box-shadow: 0 1px 2px rgba(16,24,40,.04); }
div[data-testid="stMetricValue"] { font-size: 1.35rem; font-weight: 640; color: #1C2733; }
div[data-testid="stMetricLabel"] p { font-size: .78rem; color: #5B6B7C; }
.mh-badge { display:inline-block; padding: .12rem .55rem; border-radius: 999px; font-size: .74rem; font-weight: 600;
  border: 1px solid; margin-right: .3rem; }
.mh-ok { color:#1E6B3A; background:#EAF6EE; border-color:#BFE3CB; }
.mh-warn { color:#8A5A00; background:#FFF6E5; border-color:#F2D9A6; }
.mh-bad { color:#9B1C1C; background:#FDECEC; border-color:#F5C2C2; }
.mh-info { color:#1F4E79; background:#EAF1F8; border-color:#C5D7EA; }
.mh-step { font-size:.78rem; font-weight:650; color:#1F4E79; text-transform:uppercase; letter-spacing:.05em; margin-top:.6rem; }
section[data-testid="stSidebar"] { background: #F7F9FB; border-right: 1px solid #E3E8EF; }
section[data-testid="stSidebar"] .stRadio label p { font-size: .9rem; }
div[data-testid="stExpander"] { border: 1px solid #E3E8EF; border-radius: 10px; }
</style>
"""


def setup():
    st.markdown(CSS, unsafe_allow_html=True)
    pio.templates.default = "plotly_white"


def header(title: str, subtitle: str = ""):
    st.title(title)
    if subtitle:
        st.markdown(f'<p class="mh-sub">{subtitle}</p>', unsafe_allow_html=True)


def badge(text: str, kind: str = "info") -> str:
    return f'<span class="mh-badge mh-{kind}">{text}</span>'


def badges(*items: tuple[str, str]):
    st.markdown(" ".join(badge(t, k) for t, k in items), unsafe_allow_html=True)


def step(label: str):
    st.markdown(f'<div class="mh-step">{label}</div>', unsafe_allow_html=True)


EVIDENCE_KIND = {"data-supported": "ok", "provisional": "warn", "insufficient evidence": "bad"}
STATUS_KIND = {"pass": "ok", "pass (incomplete evidence)": "warn", "fail": "bad"}


def chart_layout(fig, height=420, **kw):
    # legend below the x-axis title (rotated tick labels push the title down)
    fig.update_layout(height=height, margin=dict(l=10, r=10, t=40, b=10), font=dict(size=12),
                      legend=dict(orientation="h", y=-0.32, yanchor="top"), **kw)
    return fig
