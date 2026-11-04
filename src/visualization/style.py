"""Shared figure style: readable fonts, colour-blind-safe palette (Okabe-Ito)."""
from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
FIG_DIR = ROOT / "results/figures"

FAMILY_ORDER = ["AB5", "AB2", "AB", "AB3", "A2B7", "A2B", "SS", "Mg", "Complex", "MIC", "Misc"]
FAMILY_COLORS = {
    "AB5": "#0072B2", "AB2": "#D55E00", "AB": "#009E73", "AB3": "#CC79A7",
    "A2B7": "#882255", "A2B": "#999933", "SS": "#56B4E9", "Mg": "#E69F00",
    "Complex": "#000000", "MIC": "#AA4499", "Misc": "#777777", "(missing)": "#BBBBBB",
}
DATASET_COLORS = {"Purdue": "#0072B2", "HydPARK": "#D55E00", "Union": "#444444"}


def apply_style() -> None:
    plt.rcParams.update({
        "figure.dpi": 110, "savefig.dpi": 300, "savefig.bbox": "tight",
        "font.size": 11, "axes.titlesize": 12.5, "axes.titleweight": "bold",
        "axes.labelsize": 11.5, "legend.fontsize": 9.5, "legend.frameon": False,
        "xtick.labelsize": 10, "ytick.labelsize": 10,
        "axes.spines.top": False, "axes.spines.right": False,
        "axes.grid": True, "grid.alpha": 0.25, "grid.linewidth": 0.6,
    })


def save(fig, name: str) -> Path:
    FIG_DIR.mkdir(parents=True, exist_ok=True)
    path = FIG_DIR / f"{name}.png"
    fig.savefig(path)
    fig.savefig(FIG_DIR / f"{name}.pdf")
    plt.close(fig)
    return path


def family_color(f) -> str:
    return FAMILY_COLORS.get(f if isinstance(f, str) else "(missing)", "#BBBBBB")
