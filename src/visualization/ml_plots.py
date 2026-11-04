"""Phase 5 figures, drawn from results/metrics/*.csv.

Run:  MPLCONFIGDIR=.mplcache .venv/bin/python -m src.visualization.ml_plots
"""
from __future__ import annotations

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

from .style import ROOT, apply_style, family_color, save

M = ROOT / "results/metrics"
T = ROOT / "results/tables"
MODEL_ORDER = ["MeanBaseline", "FamilyMedianBaseline", "PhysicsBaseline(H/M x mass)", "Ridge",
               "RandomForest", "GradientBoosting"]
FS_COLORS = {"-": "#999999", "composition": "#56B4E9", "composition+family": "#0072B2"}


def noise_floor() -> float:
    """Mean |ΔH difference| between independently referenced Purdue/HydPARK pairs (Phase 2)."""
    st = pd.read_csv(T / "cross_dataset_agreement_stats.csv").set_index("subset")
    return float(st.loc["Purdue ref = DOI/other", "dH_MAE_kJmol"])


def _bars(ax, summ, metric, unit):
    rows = []
    for m in MODEL_ORDER:
        for fs in ["-", "composition", "composition+family"]:
            r = summ[(summ["model"] == m) & (summ["feature_set"] == fs)]
            if len(r):
                rows.append((m, fs, r[metric].iloc[0], r[f"{metric}_sd"].iloc[0]))
    labels = [f"{m.replace('Baseline', ' baseline').replace('FamilyMedian', 'Family median').replace('(H/M x mass)', '\n(H/M × alloy mass)')}"
              + ("" if fs == "-" else f"\n[{fs}]") for m, fs, _, _ in rows]
    x = np.arange(len(rows))
    ax.bar(x, [r[2] for r in rows], yerr=[r[3] for r in rows], capsize=3,
           color=[FS_COLORS[r[1]] for r in rows], edgecolor="white")
    for i, r in enumerate(rows):
        top = max(r[2], 0) + (0 if np.isnan(r[3]) else r[3])
        ax.text(i, top, f"{r[2]:.2f}", ha="center", va="bottom", fontsize=8.5)
    ax.set_xticks(x, labels, rotation=45, ha="right", fontsize=8.5)
    ax.set_ylabel(f"{metric} {unit}")


def fig11_dH_model_comparison():
    s = pd.read_csv(M / "dH_cv_summary.csv")
    fig, axes = plt.subplots(1, 2, figsize=(13, 4.8))
    _bars(axes[0], s, "MAE", "(kJ mol$^{-1}$ H$_2$)")
    nf = noise_floor()
    axes[0].axhline(nf, color="red", ls="--", lw=1)
    axes[0].text(len(axes[0].patches) - 0.5, nf - 0.25, f"inter-source scatter ≈ {nf:.1f}",
                 color="red", ha="right", va="top", fontsize=9,
                 bbox={"fc": "white", "ec": "none", "pad": 1})
    axes[0].set_title("Mean absolute error (lower is better)")
    _bars(axes[1], s, "R2", "")
    axes[1].set_ylabel("R²")
    axes[1].axhline(0, color="k", lw=0.8)
    axes[1].set_title("Coefficient of determination")
    fig.suptitle("Fig. 11  ΔH prediction: nested grouped 5-fold CV × 3 repeats (mean ± sd over repeats, n = 725)",
                 x=0.01, ha="left", fontweight="bold")
    fig.tight_layout()
    return save(fig, "fig11_dH_model_comparison")


def fig12_dH_parity():
    h = pd.read_csv(M / "dH_holdout_predictions.csv")
    hm = pd.read_csv(M / "dH_holdout_metrics.csv")
    cv = pd.read_csv(M / "dH_cv_summary.csv")
    # The model shown is the one selected by nested CV, never by its hold-out score
    name = cv[~cv["model"].str.endswith("Baseline")].iloc[0]["model"]
    best = hm[hm["model"] == name].iloc[0]
    fig, axes = plt.subplots(1, 3, figsize=(15, 4.8), gridspec_kw={"width_ratios": [1.1, 1.1, 0.8]})
    ax = axes[0]
    lim = (0, max(h["y"].max(), h[name].max()) * 1.05)
    for f in sorted(h["family"].unique()):
        s = h[h["family"] == f]
        ax.scatter(s["y"], s[name], s=22, color=family_color(f), alpha=0.8, edgecolor="white", lw=0.4, label=f)
    ax.plot(lim, lim, "k--", lw=1)
    ax.fill_between(lim, [lim[0] - 5, lim[1] - 5], [lim[0] + 5, lim[1] + 5], color="grey", alpha=0.12, label="±5 kJ/mol")
    ax.set_xlim(lim); ax.set_ylim(lim)
    ax.set_xlabel("Reported ΔH (kJ mol$^{-1}$ H$_2$)")
    ax.set_ylabel("Predicted ΔH (kJ mol$^{-1}$ H$_2$)")
    ax.set_title(f"{name}, held-out 20 % (n = {len(h)})\nMAE {best['MAE']:.2f}, RMSE {best['RMSE']:.2f}, R² {best['R2']:.2f}")
    ax.legend(fontsize=8, ncol=2)
    ax = axes[1]
    res = h[name] - h["y"]
    for f in sorted(h["family"].unique()):
        s = h[h["family"] == f]
        ax.scatter(s[name], s[name] - s["y"], s=22, color=family_color(f), alpha=0.8, edgecolor="white", lw=0.4)
    ax.axhline(0, color="k", lw=1)
    ax.set_xlabel("Predicted ΔH (kJ mol$^{-1}$ H$_2$)")
    ax.set_ylabel("Residual, predicted − reported (kJ mol$^{-1}$)")
    ax.set_title("Residuals vs prediction")
    ax = axes[2]
    ax.hist(res, bins=np.arange(-60, 62, 2.5), color="#0072B2", alpha=0.75)
    ax.axvline(0, color="k", lw=1)
    ax.set_xlabel("Residual (kJ mol$^{-1}$)")
    ax.set_ylabel("Count")
    ax.set_title(f"Residual distribution\nmedian |res| = {res.abs().median():.2f}")
    fig.suptitle("Fig. 12  ΔH: actual vs predicted and residuals on the grouped hold-out set",
                 x=0.01, ha="left", fontweight="bold")
    fig.tight_layout()
    return save(fig, "fig12_dH_parity_residuals")


def fig13_dH_family_errors():
    f = pd.read_csv(M / "dH_cv_by_family.csv")
    s = pd.read_csv(M / "dH_cv_summary.csv")
    best = s[~s["model"].str.endswith("Baseline")].iloc[0]
    fams = ["AB5", "AB2", "AB", "SS", "MIC", "Mg"]
    sel = {"Family median baseline": f[(f["model"] == "FamilyMedianBaseline")],
           f"{best['model']} [{best['feature_set']}]": f[(f["model"] == best["model"]) & (f["feature_set"] == best["feature_set"])]}
    fig, ax = plt.subplots(figsize=(9, 4.5))
    w = 0.38
    x = np.arange(len(fams))
    for i, (lab, d) in enumerate(sel.items()):
        d = d.set_index("family").reindex(fams)
        ax.bar(x + (i - 0.5) * w, d["MAE"], w, yerr=d["MAE_sd"], capsize=3,
               color=["#BBBBBB", "#0072B2"][i], label=lab)
    n = f[f["model"] == "FamilyMedianBaseline"].set_index("family").reindex(fams)["n"]
    ax.set_xticks(x, [f"{fa}\n(n={int(k)})" for fa, k in zip(fams, n)])
    ax.set_ylabel("MAE (kJ mol$^{-1}$ H$_2$)")
    ax.set_title("Fig. 13  ΔH error by family (out-of-fold, nested grouped CV)")
    ax.legend()
    fig.tight_layout()
    return save(fig, "fig13_dH_family_errors")


def fig14_importance():
    p = pd.read_csv(M / "dH_permutation_importance.csv").head(15)[::-1]
    fig, ax = plt.subplots(figsize=(8, 5.5))
    ax.barh(p["feature"], p["importance_MAE_increase"], xerr=p["sd"], color="#0072B2", capsize=2)
    ax.set_xlabel("Increase in hold-out MAE when the feature is permuted (kJ mol$^{-1}$)")
    ax.set_title("Fig. 14  Permutation importance, best ΔH model (top 15)")
    ax.grid(axis="y", visible=False)
    fig.tight_layout()
    return save(fig, "fig14_dH_permutation_importance")


def fig15_lofo():
    d = pd.read_csv(M / "dH_leave_family_out.csv")
    fams = d["held_out_family"].unique()
    fig, ax = plt.subplots(figsize=(9, 4.5))
    x = np.arange(len(fams)); w = 0.38
    for i, (lab, c) in enumerate([("MeanBaseline (other families)", "#BBBBBB"), (d["model"].iloc[0], "#D55E00")]):
        s = d[d["model"] == lab].set_index("held_out_family").reindex(fams)
        ax.bar(x + (i - 0.5) * w, s["MAE"], w, color=c, label=f"{lab}" if i == 0 else f"{lab}, trained without the family")
    n = d.drop_duplicates("held_out_family").set_index("held_out_family").reindex(fams)["n"]
    ax.set_xticks(x, [f"{f}\n(n={int(k)})" for f, k in zip(fams, n)])
    ax.set_ylabel("MAE on held-out family (kJ mol$^{-1}$)")
    ax.set_title("Fig. 15  Extrapolation test: leave one family out")
    ax.legend()
    fig.tight_layout()
    return save(fig, "fig15_dH_leave_family_out")


def fig16_wt():
    s = pd.read_csv(M / "wt_cv_summary.csv")
    o = pd.read_csv(M / "wt_oof_predictions.csv")
    best = s[~s["model"].str.contains("Baseline")].iloc[0]
    fig, axes = plt.subplots(1, 2, figsize=(14, 4.8), gridspec_kw={"width_ratios": [1.5, 1]})
    _bars(axes[0], s, "MAE", "(wt% H)")
    axes[0].set_title("wt%: MAE, nested grouped CV × 3 repeats")
    sel = o[(o["model"] == best["model"]) & (o["feature_set"] == best["feature_set"]) & (o["seed"] == 0)]
    ax = axes[1]
    for f in sorted(sel["family"].unique()):
        q = sel[sel["family"] == f]
        ax.scatter(q["y"], q["pred"], s=20, color=family_color(f), alpha=0.8, edgecolor="white", lw=0.4, label=f)
    lim = (0, max(sel["y"].max(), sel["pred"].max()) * 1.05)
    ax.plot(lim, lim, "k--", lw=1); ax.set_xlim(lim); ax.set_ylim(lim)
    ax.set_xlabel("Reported capacity (wt% H)"); ax.set_ylabel("Predicted (wt% H)")
    ax.set_title(f"{best['model']} [{best['feature_set']}], out-of-fold (seed 0)\nMAE {best['MAE']:.2f} ± {best['MAE_sd']:.2f}, R² {best['R2']:.2f}")
    ax.legend(fontsize=8, ncol=2)
    fig.suptitle(f"Fig. 16  Secondary task: reported capacity (Purdue stated wt%, definition not uniform, n = {int(best['n'])})",
                 x=0.01, ha="left", fontweight="bold")
    fig.tight_layout()
    return save(fig, "fig16_wt_model")


def main():
    apply_style()
    for f in (fig11_dH_model_comparison, fig12_dH_parity, fig13_dH_family_errors, fig14_importance,
              fig15_lofo, fig16_wt):
        print(f().relative_to(ROOT))


if __name__ == "__main__":
    main()
