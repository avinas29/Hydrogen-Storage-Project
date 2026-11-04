"""Phase 8 figures from results/tables/screening_*.csv.

Run:  MPLCONFIGDIR=.mplcache .venv/bin/python -m src.visualization.screening_plots
"""
from __future__ import annotations

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

from ..screening.screen import CRITERIA, WEIGHTS
from .style import ROOT, apply_style, family_color, save

T = ROOT / "results/tables"
CRIT_COLORS = {"capacity": "#0072B2", "heat": "#D55E00", "kinetics": "#009E73", "hysteresis": "#CC79A7",
               "pressure_fit": "#56B4E9", "pressure_safety": "#E69F00", "cost": "#999999"}


def short(pid: str) -> str:
    return pid.replace("[1]", "").replace("[", "").replace("]", "")


def fig24_map():
    c = pd.read_csv(T / "screening_candidates.csv")
    fig, axes = plt.subplots(1, 2, figsize=(13.5, 6.6), sharey=True)
    for ax, app in zip(axes, ("mobile", "stationary")):
        ok = c[c[f"{app}_pass"]]
        dq = c[~c["data_quality_pass"]]
        fail = c[~c[f"{app}_pass"] & c["data_quality_pass"]]
        ax.scatter(fail["T1_full_C"], fail["wt_pct"], s=16, color="#BBBBBB", label=f"fails constraints (n={len(fail)})")
        ax.scatter(dq["T1_full_C"], dq["wt_pct"], s=24, marker="x", color="k", lw=0.8, label=f"fails data-quality gate (n={len(dq)})")
        for f in ["AB5", "AB2", "AB", "SS", "AB3", "A2B7", "Misc", "Complex", "Mg"]:
            q = ok[ok["family"] == f]
            if len(q):
                ax.scatter(q["T1_full_C"], q["wt_pct"], s=18, color=family_color(f), alpha=0.85, edgecolor="white",
                           lw=0.3, label=f"{f} passes (n={len(q)})")
        ax.axvline(CRITERIA[app]["T1_full_max_C"], color="red", ls="--", lw=1)
        ax.text(CRITERIA[app]["T1_full_max_C"] + 4, 4.6, f"T(1 bar) ≤ {CRITERIA[app]['T1_full_max_C']:.0f} °C",
                color="red", fontsize=8.5)
        ax.axhline(5.5, color="k", ls=":", lw=0.8)
        ax.text(-120, 5.6, "DOE 2025 system target 5.5 wt% (system level)", fontsize=8)
        ax.set_xlim(-130, 330); ax.set_ylim(0, 8)
        ax.set_xlabel("Temperature for 1 bar, full capacity, T(1 bar) (°C)")
        extra = "P(50 °C) ≤ 50 bar; charging P ≤ 100 bar" if app == "mobile" else "P(25 °C) ≤ 10 bar; P(50 °C) ≤ 30 bar; charging P ≤ 30 bar"
        ax.set_title(f"{app.capitalize()}: {len(ok)} of {len(c)} pass\n(also: {extra})", fontsize=10.5)
        ax.legend(fontsize=7.5, loc="upper center", bbox_to_anchor=(0.5, -0.13), ncol=3)
    axes[0].set_ylabel("Reported capacity (wt% H, material level)")
    fig.suptitle("Fig. 24  Hard-constraint screening of the 337 Purdue materials", x=0.01, ha="left", fontweight="bold")
    fig.tight_layout()
    return save(fig, "fig24_screening_map")


def fig25_rankings(top=15):
    fig, axes = plt.subplots(1, 2, figsize=(15.5, 7.4))
    for ax, app in zip(axes, ("mobile", "stationary")):
        r = pd.read_csv(T / f"screening_{app}_ranking.csv").head(top)[::-1]
        left = np.zeros(len(r))
        for k in WEIGHTS[app]:
            v = r[f"contrib_{k}"].to_numpy()
            ax.barh(np.arange(len(r)), v, left=left, color=CRIT_COLORS[k], edgecolor="white", lw=0.4,
                    label=f"{k} (w={WEIGHTS[app][k]:.2f})")
            left += v
        labels = []
        for _, q in r.iterrows():
            flags = "".join(s for s, f in (("†", q["flag_pci_dH_inconsistent"]), ("‡", q["flag_unverified_ref_sandia"]),
                                           ("§", q["flag_identical_values_other_file"])) if f)
            labels.append(f"{short(q['purdue_id'])} [{q['family']}]{flags}")
        ax.set_yticks(np.arange(len(r)), labels, fontsize=8.5)
        for i, (_, q) in enumerate(r.iterrows()):
            ax.text(q["score"] + 0.005, i, f"{q['score']:.2f} | {q['wt_pct']:.2f} wt% | P25 {q['P25_bar']:.2g} bar",
                    va="center", fontsize=7.5)
        ax.set_xlim(0, 1.15)
        ax.set_xlabel("Weighted score (stacked: weighted criterion contributions)")
        ax.set_title(f"{app.capitalize()}: top {top}", fontsize=11)
        ax.legend(fontsize=7.5, loc="upper center", bbox_to_anchor=(0.5, -0.1), ncol=4)
        ax.grid(axis="y", visible=False)
    fig.suptitle("Fig. 25  Material-level rankings (base weights). † own PCI curves give ΔH > 5 kJ/mol different; "
                 "‡ unverified Sandia reference; § identical data in another file", x=0.01, ha="left", fontweight="bold", fontsize=10.5)
    fig.tight_layout()
    return save(fig, "fig25_screening_rankings")


def fig26_sensitivity(top=15):
    fig, axes = plt.subplots(1, 2, figsize=(14, 7.0))
    for ax, app in zip(axes, ("mobile", "stationary")):
        mc = pd.read_csv(T / f"screening_{app}_sensitivity_mc.csv")
        base = mc[mc["scheme"].str.startswith("perturbed")].sort_values("base_rank").head(top)
        ids = base["purdue_id"].tolist()[::-1]
        for j, (scheme, col, dy) in enumerate((("perturbed (Dirichlet, base x 20)", "#0072B2", 0.17),
                                               ("random (uniform Dirichlet)", "#D55E00", -0.17))):
            s = mc[mc["scheme"] == scheme].set_index("purdue_id").loc[ids]
            y = np.arange(len(ids)) + dy
            ax.errorbar(s["median_rank"], y, xerr=[s["median_rank"] - s["rank_q10"], s["rank_q90"] - s["median_rank"]],
                        fmt="o", color=col, ms=4, capsize=2, lw=1, label=f"{scheme}: median, 10–90%")
        b = base.set_index("purdue_id").loc[ids]
        ax.scatter(b["base_rank"], np.arange(len(ids)), marker="|", s=120, color="k", label="base-weight rank")
        ax.set_yticks(np.arange(len(ids)), [short(i) for i in ids], fontsize=8.5)
        ax.set_xscale("log")
        ax.set_xlabel("Rank among passing candidates (log scale)")
        ax.set_title(f"{app.capitalize()}: rank stability of the base top {top} (2000 weight draws each)", fontsize=10.5)
        ax.legend(fontsize=7.5, loc="upper center", bbox_to_anchor=(0.5, -0.12), ncol=2)
        ax.grid(axis="y", visible=False)
    fig.suptitle("Fig. 26  Sensitivity of rankings to the criterion weights", x=0.01, ha="left", fontweight="bold")
    fig.tight_layout()
    return save(fig, "fig26_screening_sensitivity")


def main():
    apply_style()
    for f in (fig24_map, fig25_rankings, fig26_sensitivity):
        print(f().relative_to(ROOT))


if __name__ == "__main__":
    main()
