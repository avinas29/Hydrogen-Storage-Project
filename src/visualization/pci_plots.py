"""Phase 7 figures: PCI isotherms, PCI-derived Van't Hoff check, kinetics.

Run:  MPLCONFIGDIR=.mplcache .venv/bin/python -m src.visualization.pci_plots
"""
from __future__ import annotations

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D

from ..thermodynamics.pci_kinetics import REPRESENTATIVE_PCI, WINDOW, load_all_pci
from ..thermodynamics.vant_hoff import peq_bar
from .style import ROOT, apply_style, family_color, save

T = ROOT / "results/tables"


def fig21_pci():
    pts, meta = load_all_pci()
    curves = pd.read_csv(T / "pci_curve_plateaus.csv")
    p = pd.read_csv(ROOT / "data/processed/purdue_cleaned.csv").set_index("purdue_id")
    fig, axes = plt.subplots(2, 3, figsize=(15, 8.6))
    for ax, (mid, label) in zip(axes.flat, REPRESENTATIVE_PCI.items()):
        sub = pts[pts["material_id"] == mid]
        Ts = sorted(sub["T_K"].unique())
        cmap = plt.cm.coolwarm(np.linspace(0, 1, max(len(Ts), 2)))
        for (cid, g) in sub.groupby("curve_id"):
            col = cmap[Ts.index(g["T_K"].iloc[0])]
            ls = "-" if g["mode"].iloc[0] == "abs" else "--"
            mk = "o" if g["mode"].iloc[0] == "abs" else "s"
            g = g.sort_values("wt_pct")
            ax.plot(g["wt_pct"], g["P_bar"], ls=ls, marker=mk, ms=2.5, lw=1.2, color=col)
            c = curves[curves["curve_id"] == cid].iloc[0]
            if np.isfinite(c["P_plateau_bar"]):
                ax.scatter([0.5 * c["wt_max_curve"]], [c["P_plateau_bar"]], marker="D", s=30,
                           facecolor="white", edgecolor=col, zorder=5)
        ax.set_yscale("log")
        m = meta[meta["material_id"] == mid].iloc[0]
        shifted = " | curator-shifted" if m["flag_shifted_by_curator"] else ""
        ax.set_title(f"{label}\n{m['author']}, {m['figure']}{shifted}", fontsize=10)
        ax.set_xlabel("Hydrogen content (wt% H)")
        ax.set_ylabel("Pressure (bar)")
        handles = [Line2D([], [], color=cmap[i], lw=2, label=f"{t:g} K") for i, t in enumerate(Ts)]
        ax.legend(handles=handles, fontsize=7.5, loc="lower right", ncol=2 if len(Ts) > 4 else 1)
    ax = axes.flat[-1]
    ax.axis("off")
    ax.legend(handles=[Line2D([], [], color="k", ls="-", marker="o", ms=3, label="absorption"),
                       Line2D([], [], color="k", ls="--", marker="s", ms=3, label="desorption"),
                       Line2D([], [], color="k", ls="", marker="D", mfc="white", label=f"extracted plateau\n(median ln P, x = {WINDOW[0]}–{WINDOW[1]})")],
              loc="center", fontsize=10, title="All curves digitised from published figures\n(see data/interim/purdue_pci_index.csv)")
    fig.suptitle("Fig. 21  Pressure–composition isotherms of five representative hydrides", x=0.01, ha="left", fontweight="bold")
    fig.tight_layout()
    return save(fig, "fig21_pci_isotherms")


def fig22_pci_vant_hoff():
    f = pd.read_csv(T / "pci_vant_hoff_fits.csv")
    curves = pd.read_csv(T / "pci_curve_plateaus.csv")
    p = pd.read_csv(ROOT / "data/processed/purdue_cleaned.csv").set_index("purdue_id")
    fig, axes = plt.subplots(1, 2, figsize=(13, 5))
    ax = axes[0]
    show = ["La[1]Ni[5]", "Ti[1.01]Cr[1.06]Mn[1]", "Ti[0.95]Zr[0.05]Mn[1.55]V[0.45]Fe[0.09]", "Ti[0.5]Zr[0.5]Mn[1.36]Fe[0.34]"]
    for mid, c in zip(show, ["#0072B2", "#D55E00", "#009E73", "#CC79A7"]):
        g = curves[(curves["material_id"] == mid) & (curves["mode"] == "des")].dropna(subset=["P_plateau_bar"])
        ax.scatter(1000 / g["T_K"], g["P_plateau_bar"], color=c, s=30, zorder=3)
        Tl = np.linspace(g["T_K"].min() - 15, g["T_K"].max() + 15, 50)
        r = p.loc[mid]
        ax.plot(1000 / Tl, peq_bar(Tl, r["dH_kJmol"], r["dS_JmolK"]), color=c, lw=1.5,
                label=f"{mid.replace('[1]', '').replace('[', '').replace(']', '')}")
        fr = f[(f["material_id"] == mid) & (f["mode"] == "des")].iloc[0]
        ax.plot(1000 / Tl, peq_bar(Tl, fr["dH_fit_kJmol"], fr["dS_fit_JmolK"]), color=c, lw=1, ls=":")
    ax.set_yscale("log")
    ax.set_xlabel("1000 / T (K$^{-1}$)"); ax.set_ylabel("Desorption plateau pressure (bar)")
    ax.set_title("Points: plateaus extracted from PCI; solid: .mh ΔH/ΔS;\ndotted: this work's Van't Hoff fit to the points", fontsize=10.5)
    ax.legend(fontsize=7.5)
    ax = axes[1]
    for multi, mk, lab in [(False, "o", "single-plateau"), (True, "x", "multi-plateau (fit not meaningful)")]:
        q = f[(f["multi_plateau_excluded"] == multi) & f["dH_mh_kJmol"].notna()]
        for mode, col in (("des", "#0072B2"), ("abs", "#E69F00")):
            s = q[q["mode"] == mode]
            ax.scatter(s["dH_mh_kJmol"], s["dH_fit_kJmol"], marker=mk, s=34, color=col, alpha=0.85,
                       label=f"{mode}, {lab} (n={len(s)})")
    lim = (5, 60)
    ax.plot(lim, lim, "k--", lw=1)
    ax.fill_between(lim, [l - 2 for l in lim], [l + 2 for l in lim], color="grey", alpha=0.15, label="±2 kJ/mol")
    ax.set_xlim(lim); ax.set_ylim(lim)
    ax.set_xlabel("ΔH in .mh file (kJ mol$^{-1}$ H$_2$)"); ax.set_ylabel("ΔH from PCI plateaus, this work")
    ax.set_title("Consistency of PCI curves with tabulated ΔH\n(not independent: most .mh values were fitted to these curves)", fontsize=10.5)
    ax.legend(fontsize=7.5, loc="upper left")
    fig.suptitle("Fig. 22  Van't Hoff analysis of the digitised PCI curves", x=0.01, ha="left", fontweight="bold")
    fig.tight_layout()
    return save(fig, "fig22_pci_vant_hoff_check")


def fig23_kinetics():
    k = pd.read_csv(T / "kinetics_purdue.csv")
    fig, axes = plt.subplots(1, 2, figsize=(13, 4.8))
    ax = axes[0]
    fams = ["AB5", "AB2", "AB", "AB3", "Mg", "Complex"]
    for i, f in enumerate(fams):
        for mode, dx, mk in (("abs", -0.15, "o"), ("des", 0.15, "s")):
            s = k[(k["family"] == f) & (k["mode"] == mode)]
            if not len(s):
                continue
            x = np.full(len(s), i + dx) + np.random.default_rng(1).normal(0, 0.03, len(s))
            ax.scatter(x, s["Ea_kJmol"], marker=mk, s=30, color=family_color(f),
                       edgecolor=np.where(s["model_form_comparable"], "white", "k"), lw=0.9, alpha=0.9)
    ax.set_xticks(range(len(fams)), [f"{f}\n(n={len(k[k.family == f])})" for f in fams])
    ax.set_ylabel("Activation energy E$_a$ (kJ mol$^{-1}$)")
    ax.set_title("Activation energies in the Purdue kinetics records\n(circle = absorption, square = desorption; black edge = different rate-law form)", fontsize=10)
    ax = axes[1]
    c = k[k["model_form_comparable"]]
    for mode, col in (("abs", "#0072B2"), ("des", "#D55E00")):
        s = c[c["mode"] == mode]
        ax.scatter(s["Ea_kJmol"], s["t90_s_25C"], color=col, s=30, alpha=0.85, label=f"{mode} (n={len(s)})")
        fl = s[s["flag_data_assumed"] | s["flag_conflicting_source"]]
        ax.scatter(fl["Ea_kJmol"], fl["t90_s_25C"], facecolor="none", edgecolor="k", s=80, lw=0.9)
    ax.scatter([], [], facecolor="none", edgecolor="k", s=80, label="source note: 'data assumed' or 'conflicts'")
    ax.set_yscale("log")
    ax.set_xlabel("E$_a$ (kJ mol$^{-1}$)")
    ax.set_ylabel("Model t$_{90}$ at 25 °C, P/P$_{eq}$ = 2 or ½ (s)")
    ax.set_title("Comparable group only: f$_p$ = ln(P/P$_{eq}$), first order in w\n(model-based illustration, not measured times)", fontsize=10)
    ax.legend(fontsize=8)
    fig.suptitle("Fig. 23  Kinetic parameters (31 absorption / 26 desorption records; type defaults excluded)",
                 x=0.01, ha="left", fontweight="bold")
    fig.tight_layout()
    return save(fig, "fig23_kinetics")


def main():
    apply_style()
    for f in (fig21_pci, fig22_pci_vant_hoff, fig23_kinetics):
        print(f().relative_to(ROOT))


if __name__ == "__main__":
    main()
