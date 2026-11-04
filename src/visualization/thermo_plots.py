"""Phase 6 figures from results/tables/vant_hoff_*.csv.

Run:  MPLCONFIGDIR=.mplcache .venv/bin/python -m src.visualization.thermo_plots
"""
from __future__ import annotations

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.patches import Patch

from ..thermodynamics.vant_hoff import LHV_H2_MJ_PER_KG, peq_bar
from .style import ROOT, apply_style, family_color, save

T = ROOT / "results/tables"
PEMFC_C = (60, 80)       # typical PEM fuel cell coolant/stack temperature range, °C


def fig17_vant_hoff():
    t = pd.read_csv(T / "vant_hoff_purdue.csv")
    rep = pd.read_csv(T / "vant_hoff_representative.csv")
    single = t[(t["n_plateaus"] == 1) & t["family"].isin(["AB5", "AB2", "AB", "SS"])]
    fig, ax = plt.subplots(figsize=(9.5, 6))
    invT = np.linspace(1000 / 700, 1000 / 233, 200)
    for _, r in single.iterrows():
        ax.plot(invT, peq_bar(1000 / invT, r["dH_kJmol"], r["dS_JmolK"]), color=family_color(r["family"]),
                lw=0.5, alpha=0.18)
    for (_, r), c in zip(rep.iterrows(), plt.cm.tab20.colors[::1]):
        ax.plot(invT, peq_bar(1000 / invT, r["dH_kJmol"], r["dS_JmolK"]), color=c, lw=2.0, label=r["name"])
    ax.set_yscale("log"); ax.set_ylim(1e-3, 1e3)
    ax.axhspan(1, 10, color="green", alpha=0.08)
    ax.axvspan(1000 / (PEMFC_C[1] + 273.15), 1000 / (PEMFC_C[0] + 273.15), color="red", alpha=0.07)
    ax.text(1000 / 343, 1.4e-3, "PEMFC\n60–80 °C", color="darkred", ha="center", fontsize=8.5)
    ax.text(4.25, 3.2, "1–10 bar", color="darkgreen", fontsize=9)
    ax.set_xlabel("1000 / T (K$^{-1}$)")
    ax.set_ylabel("Desorption plateau pressure P$_{eq}$ (bar)")
    top = ax.secondary_xaxis("top", functions=(lambda x: 1000 / np.maximum(x, 1e-3) - 273.15,
                                               lambda c: 1000 / (np.asarray(c) + 273.15)))
    top.set_xticks([400, 300, 200, 150, 100, 50, 25, 0, -25])
    top.set_xlabel("Temperature (°C)")
    ax.set_title("Fig. 17  Van't Hoff lines from experimental ΔH, ΔS\n(faint: all single-plateau AB5/AB2/AB/SS Purdue materials, coloured by family)",
                 fontsize=11.5)
    fam_handles = [Patch(color=family_color(f), alpha=0.5, label=f"{f} (all)") for f in ["AB5", "AB2", "AB", "SS"]]
    leg1 = ax.legend(fontsize=7.8, loc="lower left", ncol=2)
    ax.add_artist(leg1)
    ax.legend(handles=fam_handles, fontsize=7.8, loc="upper right")
    fig.tight_layout()
    return save(fig, "fig17_vant_hoff_lines")


def fig18_windows():
    rep = pd.read_csv(T / "vant_hoff_representative.csv")
    from ..thermodynamics.vant_hoff import T_at_P
    fig, ax = plt.subplots(figsize=(11, 6.2))
    y = np.arange(len(rep))[::-1]
    for yi, (_, r) in zip(y, rep.iterrows()):
        lo, hi = r["T_C_at_1bar"], r["T_C_at_10bar"]
        ax.barh(yi + 0.18, hi - lo, left=lo, height=0.34, color="#0072B2", label="desorption: P$_{eq}$ 1–10 bar" if yi == y[0] else None)
        if r["abs_source"] == "stated_abs_dH_dS":
            alo, ahi = T_at_P(1, r["abs_dH_kJmol"], r["abs_dS_JmolK"]) - 273.15, T_at_P(10, r["abs_dH_kJmol"], r["abs_dS_JmolK"]) - 273.15
            ax.barh(yi - 0.18, ahi - alo, left=alo, height=0.34, color="#E69F00",
                    label="absorption: P$_{abs}$ 1–10 bar (stated ΔH$_{abs}$, ΔS$_{abs}$)" if "abs_lab" not in locals() else None)
            abs_lab = True  # noqa: F841
        ax.text(445, yi, f"{r['heat_MJ_per_kgH2']:.1f} MJ/kg H$_2$ ({r['heat_pct_of_LHV']:.0f}% LHV)",
                va="center", fontsize=8.5)
    ax.axvspan(-20, 40, color="green", alpha=0.07)
    ax.axvspan(*PEMFC_C, color="red", alpha=0.10)
    ax.text(10, y[-1] - 0.85, "ambient −20–40 °C", ha="center", fontsize=8, color="darkgreen")
    ax.text(70, y[-1] - 1.25, "PEMFC 60–80 °C", ha="center", fontsize=8, color="darkred")
    ax.set_ylim(y[-1] - 1.5, y[0] + 0.6)
    ax.set_yticks(y, rep["name"])
    ax.set_xlim(-130, 440)
    ax.set_xlabel("Temperature (°C)")
    ax.set_title("Fig. 18  Operating windows: temperature range giving 1–10 bar plateau pressure\n(right: reaction heat to be supplied on desorption / removed on absorption)", fontsize=11.5)
    ax.legend(loc="upper right", fontsize=8.5)
    ax.grid(axis="y", visible=False)
    fig.tight_layout()
    return save(fig, "fig18_operating_windows")


def fig19_heat():
    t = pd.read_csv(T / "vant_hoff_purdue.csv")
    s = t[t["n_plateaus"] == 1]
    fig, ax = plt.subplots(figsize=(8.5, 5.5))
    for f in ["AB5", "AB2", "AB", "SS", "AB3", "A2B7", "Mg", "Misc"]:
        q = s[s["family"] == f]
        ax.scatter(q["T_C_at_1bar"], q["heat_MJ_per_kgH2"], s=20, color=family_color(f), alpha=0.8,
                   edgecolor="white", lw=0.3, label=f"{f} (n={len(q)})")
    fl = s[s["flag_dS_atypical"]]
    ax.scatter(fl["T_C_at_1bar"], fl["heat_MJ_per_kgH2"], s=70, facecolor="none", edgecolor="k", lw=0.9,
               label=f"flagged: atypical ΔS (n={len(fl)})")
    na = t[t["purdue_id"] == "Na[1]Al[1]H[1]"]
    ax.scatter(na["T_C_at_1bar"], na["heat_MJ_per_kgH2"], marker="*", s=140, color="k", label="NaAlH$_4$ (both plateaus)")
    ax.axvspan(*PEMFC_C, color="red", alpha=0.08)
    ax.axvline(PEMFC_C[1], color="darkred", lw=0.8, ls="--")
    ax.text(PEMFC_C[1] + 4, 41, "PEMFC waste heat ≤ 80 °C", color="darkred", fontsize=8.5)
    ax.set_xlabel("Temperature for 1 bar desorption pressure, T(1 bar) (°C)")
    ax.set_ylabel("Reaction heat (MJ per kg H$_2$)")
    sec = ax.secondary_yaxis("right", functions=(lambda q: 100 * q / LHV_H2_MJ_PER_KG,
                                                  lambda p: p * LHV_H2_MJ_PER_KG / 100))
    sec.set_ylabel("Heat as % of H$_2$ lower heating value")
    ax.set_xlim(-130, 330)
    ax.set_title("Fig. 19  Heat requirement vs operating temperature (experimental, all Purdue plateaus)")
    ax.legend(fontsize=8, ncol=2, loc="upper left")
    fig.tight_layout()
    return save(fig, "fig19_heat_vs_temperature")


def fig20_ml_series():
    s = pd.read_csv(T / "vant_hoff_ml_series.csv")
    series = list(dict.fromkeys(s["series"]))
    fig, axes = plt.subplots(2, len(series), figsize=(15, 7.2), sharex="col")
    for j, name in enumerate(series):
        q = s[s["series"] == name]
        ax = axes[0, j]
        ax.fill_between(q["x"], q["dH_interval_low"], q["dH_interval_high"], color="#E69F00", alpha=0.2,
                        label="80% interval (by NN-distance bin)")
        ax.plot(q["x"], q["dH_predicted"], color="#E69F00", lw=1.5)
        k = q[q["in_data"]]; n = q[~q["in_data"]]
        ax.scatter(k["x"], k["dH_predicted"], color="#0072B2", s=28, zorder=3, label="out-of-fold prediction")
        ax.scatter(n["x"], n["dH_predicted"], marker="^", color="#D55E00", s=36, zorder=3, label="ESTIMATE (not in data)")
        ax.scatter(k["x"], k["dH_experimental"], color="k", marker="x", s=36, zorder=4, label="experimental ΔH")
        ax.set_title(name, fontsize=11)
        if j == 0:
            ax.set_ylabel("ΔH (kJ mol$^{-1}$ H$_2$)")
            ax.legend(fontsize=7.5, loc="upper left")
        ax = axes[1, j]
        ax.fill_between(q["x"], q["T1bar_C_band_low"], q["T1bar_C_band_high"], color="#CC79A7", alpha=0.25,
                        label="band: ΔH interval × ΔS IQR")
        ax.plot(q["x"], q["T1bar_C_estimate"], color="#CC79A7", lw=1.8, label="ML ΔH + family-median ΔS")
        ax.axhspan(*PEMFC_C, color="red", alpha=0.08)
        ax.set_xlabel(q["x_label"].iloc[0])
        if j == 0:
            ax.set_ylabel("Estimated T(1 bar) (°C)")
            ax.legend(fontsize=7.5, loc="upper left")
    fig.suptitle("Fig. 20  ESTIMATES: ML-predicted ΔH along substitution series and the implied 1-bar temperature "
                 "(assumed ΔS, not experimentally validated)", x=0.01, ha="left", fontweight="bold", fontsize=11.5)
    fig.tight_layout()
    return save(fig, "fig20_ml_estimated_series")


def main():
    apply_style()
    for f in (fig17_vant_hoff, fig18_windows, fig19_heat, fig20_ml_series):
        print(f().relative_to(ROOT))


if __name__ == "__main__":
    main()
