"""Report-only figures: schematics of the actual pipeline and plots from project result files.

Run from the project root:  MPLCONFIGDIR=.mplcache .venv/bin/python -m report.make_figures
"""
from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "report/figures"
OUT.mkdir(parents=True, exist_ok=True)
NAVY, RED, GREY, LIGHT = "#1F4E79", "#C0504D", "#7F7F7F", "#EAF1F8"
plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 10, "savefig.dpi": 300, "savefig.bbox": "tight",
                     "axes.spines.top": False, "axes.spines.right": False})


def box(ax, x, y, w, h, text, fc=LIGHT, ec=NAVY, fs=9, bold=False):
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.004,rounding_size=0.015", fc=fc, ec=ec, lw=1.2, clip_on=False))
    ax.text(x + w / 2, y + h / 2, text, ha="center", va="center", fontsize=fs, wrap=True,
            fontweight="bold" if bold else "normal")


def arrow(ax, x1, y1, x2, y2, color=NAVY):
    ax.add_patch(FancyArrowPatch((x1, y1), (x2, y2), arrowstyle="-|>", mutation_scale=12, color=color, lw=1.2))


def canvas(w, h):
    fig, ax = plt.subplots(figsize=(w, h))
    ax.set_xlim(0, 1); ax.set_ylim(0, 1); ax.axis("off")
    return fig, ax


def fig_workflow():
    fig, ax = canvas(11, 2.6)
    steps = ["Alloy\ncomposition", "38 composition\ndescriptors", "Random Forest\nΔH + 80% interval\n+ domain check",
             "Van't Hoff\nP(T), T(P), heat", "Engineering\nconstraints\n(pass/fail/unknown)", "Application-specific\nranking, Pareto,\nevidence class"]
    w, gap = 0.145, 0.025
    for i, s in enumerate(steps):
        x = 0.01 + i * (w + gap)
        box(ax, x, 0.42, w, 0.42, s, fs=8, bold=i in (2, 5))
        if i:
            arrow(ax, x - gap + 0.002, 0.63, x - 0.002, 0.63)
    ax.text(0.5, 0.16, "Experimental ΔH, ΔS (Purdue .mh) enter at the Van't Hoff step for known materials;\n"
            "ML ΔH with an assumed ΔS is used only for new compositions and is labelled an estimate.",
            ha="center", fontsize=8.5, color=GREY, style="italic")
    fig.savefig(OUT / "f_workflow.png"); plt.close(fig)


def fig_pct_schematic():
    """Illustrative PCT isotherms from a simple lattice-gas-like shape (schematic, not data)."""
    fig, axes = plt.subplots(1, 2, figsize=(10, 3.8), gridspec_kw={"width_ratios": [1.25, 1]})
    ax = axes[0]
    x = np.linspace(0.01, 0.99, 400)
    for T, c, lab in ((1.0, NAVY, "T₁"), (1.12, "#5B9BD5", "T₂ > T₁"), (1.25, "#9DC3E6", "T₃ > T₂")):
        p_plat = np.exp(-8 / T + 8)          # higher T -> higher plateau
        y = np.where(x < 0.12, p_plat * (x / 0.12) ** 2.2, np.where(x > 0.88, p_plat * np.exp(9 * (x - 0.88)), p_plat * (1 + 0.15 * (x - 0.5))))
        ax.plot(x, y, color=c, lw=2, label=lab)
    ax.set_yscale("log")
    ax.axvspan(0, 0.12, color="#F2F2F2"); ax.axvspan(0.88, 1, color="#F2F2F2")
    ax.text(0.06, 0.03, "α", transform=ax.transAxes, ha="center", fontsize=12)
    ax.text(0.5, 0.03, "α + β plateau", transform=ax.transAxes, ha="center", fontsize=10)
    ax.text(0.94, 0.03, "β", transform=ax.transAxes, ha="center", fontsize=12)
    ax.set_xlabel("Hydrogen content, H/M (normalised)"); ax.set_ylabel("Equilibrium pressure (log scale)")
    ax.set_xticks([]); ax.set_yticks([])
    ax.set_title("(a) Pressure–composition isotherms", fontsize=10)
    ax.legend(frameon=False, fontsize=8, loc="upper left")
    ax = axes[1]
    invT = np.array([1 / 1.25, 1 / 1.12, 1.0])
    ax.plot(invT, -8 * invT + 8, "o-", color=NAVY)
    ax.set_xlabel("1/T"); ax.set_ylabel("ln P_plateau")
    ax.set_xticks([]); ax.set_yticks([])
    ax.text(0.5, 0.75, "slope = −ΔH/R\nintercept = ΔS/R", transform=ax.transAxes, fontsize=9)
    ax.set_title("(b) Van't Hoff plot of the plateaus", fontsize=10)
    fig.suptitle("Schematic (illustrative shapes, not measured data)", fontsize=8.5, color=GREY, y=0.02)
    fig.savefig(OUT / "f_pct_schematic.png"); plt.close(fig)


def fig_dataprep():
    fig, ax = canvas(10, 3.2)
    box(ax, 0.01, 0.6, 0.2, 0.3, "Purdue toolbox\n337 .mh files\n68 PCI CSVs", fc="#FFFFFF")
    box(ax, 0.01, 0.12, 0.2, 0.3, "ML-HydPARK v0.0.5\n772 rows\n(4 appended blocks)", fc="#FFFFFF")
    box(ax, 0.27, 0.6, 0.2, 0.3, "Parser mirroring\nMATLAB loaders;\nno type defaults")
    box(ax, 0.27, 0.12, 0.2, 0.3, "Block IDs, ΔS-derivation\ncheck, error flags")
    box(ax, 0.53, 0.36, 0.2, 0.3, "Cleaning: positive ΔH, ΔS;\npymatgen composition key;\nquality flags kept", fs=7.8)
    box(ax, 0.79, 0.36, 0.2, 0.3, "Composition-level union\n725 compositions\n(276 Purdue, 449 HydPARK)", fs=7.8, bold=True)
    arrow(ax, 0.21, 0.75, 0.27, 0.75); arrow(ax, 0.21, 0.27, 0.27, 0.27)
    arrow(ax, 0.47, 0.75, 0.53, 0.55); arrow(ax, 0.47, 0.27, 0.53, 0.45); arrow(ax, 0.73, 0.51, 0.79, 0.51)
    ax.text(0.63, -0.02, "Excluded from the union (kept in files): mischmetal alloys, multi-plateau entries,\n"
            "suspected entry errors, entries the Purdue curators excluded", ha="center", fontsize=8, color=GREY)
    fig.savefig(OUT / "f_dataprep.png"); plt.close(fig)


def fig_applicability():
    cal = pd.read_csv(ROOT / "results/tables/applicability_domain_calibration.csv")
    fig, ax = plt.subplots(figsize=(7.5, 3.6))
    x = np.arange(len(cal))
    ax.bar(x, cal["MAE"], color=[NAVY if i < 3 else "#9DC3E6" for i in x])
    for i, r in cal.iterrows():
        ax.text(i, r["MAE"] + 0.4, f"{r['MAE']:.1f}\n(n={r['n']})", ha="center", fontsize=8)
    ax.axvline(2.5, color=RED, ls="--"); ax.text(2.55, cal["MAE"].max() * 0.9, "domain limit\nL1 = 0.15", color=RED, fontsize=8.5)
    ax.set_xticks(x, cal["bin"], rotation=0, fontsize=8)
    ax.set_xlabel("L1 distance to nearest training composition outside the same CV group")
    ax.set_ylabel("Out-of-fold MAE (kJ mol⁻¹ H₂)")
    ax.set_ylim(0, cal["MAE"].max() * 1.25)
    fig.savefig(OUT / "f_applicability.png"); plt.close(fig)


def fig_architecture():
    fig, ax = canvas(10, 4.2)
    box(ax, 0.01, 0.4, 0.13, 0.22, "User input\n(composition,\nalloy ranges,\nrequirements)", fc="#FFFFFF")
    box(ax, 0.19, 0.25, 0.17, 0.52, "Streamlit interface\n(app.py, 8 pages)\n\nPredictor\nDiscovery Lab\nRequirement Designer\nComparison\nThermodynamics\nPerformance · Evidence", fs=8)
    engines = [("predictor.py\nparse → 38 descriptors → RF ΔH,\ninterval, nearest neighbours", 0.72),
               ("generator.py + discovery.py\nconstrained grids, screening,\nranking, Pareto", 0.47),
               ("recommend.py\nhard constraints, scores, Pareto,\nevidence class, explanations", 0.22)]
    for t, y in engines:
        box(ax, 0.42, y, 0.25, 0.2, t, fs=8)
        arrow(ax, 0.36, 0.51, 0.42, y + 0.1)
    box(ax, 0.73, 0.6, 0.25, 0.3, "Model artifacts\ndH_predictor_bundle.joblib\n(+ manifest, SHA-256)\ncalibration, ΔS assumption", fc="#FFFFFF", fs=8)
    box(ax, 0.73, 0.15, 0.25, 0.35, "Project data (read-only)\nPurdue / HydPARK cleaned tables,\nVan't Hoff, PCI and screening\nresults (Phases 1–8)", fc="#FFFFFF", fs=8)
    for y in (0.82, 0.57, 0.32):
        arrow(ax, 0.67, y, 0.73, 0.75 if y > 0.7 else 0.32, color=GREY)
    arrow(ax, 0.14, 0.51, 0.19, 0.51)
    ax.text(0.5, 0.05, "Outputs returned to the interface: predictions with uncertainty, estimates (labelled), "
            "rankings, explanations, CSV/JSON exports", ha="center", fontsize=8.5, color=GREY, style="italic")
    fig.savefig(OUT / "f_architecture.png"); plt.close(fig)


def fig_screening_flow():
    fig, ax = canvas(10, 2.4)
    s = ["Requirements\n(T, heat, P, demand,\nlimits, weights)", "Experimental pool\n337 Purdue materials",
         "Hard constraints\npass / fail / unknown", "Weighted score\n(normalised criteria)", "Pareto front\n(2 chosen objectives)",
         "Evidence class +\nexplanation +\nmeasurements needed"]
    w, gap = 0.145, 0.025
    for i, t in enumerate(s):
        x = 0.01 + i * (w + gap)
        box(ax, x, 0.3, w, 0.5, t, fs=7.5)
        if i:
            arrow(ax, x - gap + 0.002, 0.55, x - 0.002, 0.55)
    ax.text(0.5, 0.1, "'Unknown' (missing evidence) never rejects a material; 'insufficient evidence' materials are shown but never ranked.",
            ha="center", fontsize=8.5, color=GREY, style="italic")
    fig.savefig(OUT / "f_screening_flow.png"); plt.close(fig)


def fig_scenarios():
    import sys
    sys.path.insert(0, str(ROOT))
    from src.app.demo import SCENARIOS
    from src.app.recommend import APPLICATIONS, run
    fig, axes = plt.subplots(1, 2, figsize=(11, 4.0), sharey=True)
    tops = []
    for ax, s, lab in zip(axes, SCENARIOS, ["(a) Mobile (70 °C PEMFC heat, 3 bar)", "(b) Industrial buffer (120 °C heat, 5 bar)"]):
        req = s["req"]
        res = run(req, APPLICATIONS[req.application]["weights"], ("wt_pct", "heat_MJ_per_kgH2"))
        ok = res[res["rank"].notna()]
        fail = res[res.status == "fail"]
        ax.scatter(fail["heat_MJ_per_kgH2"], fail["wt_pct"], s=10, color="#D9D9D9", label=f"fail hard constraint (n={len(fail)})")
        ax.scatter(ok["heat_MJ_per_kgH2"], ok["wt_pct"], s=14, color="#9DC3E6", label=f"ranked (n={len(ok)})")
        t5 = ok.head(5)
        ax.scatter(t5["heat_MJ_per_kgH2"], t5["wt_pct"], s=45, color=NAVY, label="top 5 (weighted score)")
        pf = ok[ok.pareto]
        ax.scatter(pf["heat_MJ_per_kgH2"], pf["wt_pct"], s=90, facecolor="none", edgecolor=RED, lw=1.3, label="Pareto front (capacity↑, heat↓)")
        for j, (_, r) in enumerate(t5.iterrows()):
            ax.annotate(f"{int(r['rank'])}", (r["heat_MJ_per_kgH2"], r["wt_pct"]), xytext=(5 if j % 2 == 0 else -10, 5 if j % 2 == 0 else -12),
                        textcoords="offset points", fontsize=8, fontweight="bold")
        ax.set_xlabel("Reaction heat (MJ per kg H₂)"); ax.set_title(lab, fontsize=10)
        ax.set_xlim(5, 45); ax.set_ylim(0, 8.5); ax.legend(fontsize=7.5, frameon=False, loc="upper center", ncol=2, bbox_to_anchor=(0.5, -0.17))
        tops.append(t5.assign(scenario=lab))
    axes[0].set_ylabel("Reported capacity (wt% H, material level)")
    fig.savefig(OUT / "f_scenarios.png"); plt.close(fig)
    pd.concat(tops)[["scenario", "rank", "name", "family", "evidence_class", "score", "wt_pct", "heat_MJ_per_kgH2",
                     "T_required_C"]].to_csv(OUT / "f_scenarios_top5.csv", index=False)


if __name__ == "__main__":
    for f in (fig_workflow, fig_pct_schematic, fig_dataprep, fig_applicability, fig_architecture, fig_screening_flow, fig_scenarios):
        f(); print("ok", f.__name__)
