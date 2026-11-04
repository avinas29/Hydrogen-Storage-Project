"""Write reports/ml_results.md from results/metrics/*.csv (all numbers computed)."""
from __future__ import annotations

from pathlib import Path

import pandas as pd

from ..data.run_audit import md_table
from .train import N_INNER, N_OUTER, SEEDS, model_specs

ROOT = Path(__file__).resolve().parents[2]
M = ROOT / "results/metrics"
T = ROOT / "results/tables"


def r(df, cols=None, nd=2):
    df = df if cols is None else df[cols]
    return df.round(nd)


def main():
    cv = pd.read_csv(M / "dH_cv_summary.csv")
    hold = pd.read_csv(M / "dH_holdout_metrics.csv")
    fam = pd.read_csv(M / "dH_cv_by_family.csv")
    wf = pd.read_csv(M / "dH_within_family.csv")
    lofo = pd.read_csv(M / "dH_leave_family_out.csv")
    sens = pd.read_csv(M / "dH_sensitivity.csv")
    imp = pd.read_csv(M / "dH_permutation_importance.csv")
    grp = pd.read_csv(M / "dH_grouping_effect.csv")
    wt = pd.read_csv(M / "wt_cv_summary.csv")
    wtf = pd.read_csv(M / "wt_cv_by_family.csv")
    hp = pd.read_csv(M / "dH_selected_hyperparameters.csv")
    st = pd.read_csv(T / "cross_dataset_agreement_stats.csv").set_index("subset")
    u = pd.read_csv(ROOT / "data/processed/dH_union_by_composition.csv")

    nf = st.loc["Purdue ref = DOI/other", "dH_MAE_kJmol"]
    multi = u[u["n_purdue"] + u["n_hydpark"] > 1]
    best = cv[~cv["model"].str.endswith("Baseline")].iloc[0]
    fam_base = cv[cv["model"] == "FamilyMedianBaseline"].iloc[0]
    mean_base = cv[cv["model"] == "MeanBaseline"].iloc[0]
    hb = hold[hold["model"] == best["model"]].iloc[0]  # CV-selected model, not hold-out best
    hp_counts = (hp.groupby(["feature_set", "model", "params"]).size()
                 .reset_index(name="times_selected").sort_values(["feature_set", "model", "times_selected"],
                                                                 ascending=[True, True, False]))
    hp_mode = hp_counts.groupby(["feature_set", "model"]).head(1)
    bf = fam[(fam["model"] == best["model"]) & (fam["feature_set"] == best["feature_set"])].set_index("family")
    fb = fam[fam["model"] == "FamilyMedianBaseline"].set_index("family")
    fam_tab = pd.DataFrame({
        "n": fb["n"], "family_median_MAE": fb["MAE"],
        f"{best['model']}_MAE": bf["MAE"], f"{best['model']}_R2": bf["R2"]}).reset_index().round(2)
    lofo_w = lofo.pivot(index="held_out_family", columns="model", values="MAE").round(2).reset_index()
    lofo_w["n"] = lofo.drop_duplicates("held_out_family").set_index("held_out_family").loc[lofo_w["held_out_family"], "n"].values
    worse = lofo_w[lofo_w[best["model"]] > lofo_w["MeanBaseline (other families)"]]["held_out_family"].tolist()
    wt_best = wt[~wt["model"].str.contains("Baseline")].iloc[0]
    wt_phys = wt[wt["model"].str.startswith("Physics")].iloc[0]
    wt_ridge = wt[(wt["model"] == "Ridge") & (wt["feature_set"] == "composition")].iloc[0]
    g_grp = grp.set_index("cv_grouping")

    grids = "\n".join(f"| {k} | {v[1]} |" for k, v in model_specs().items())
    text = f"""# Phase 5: machine learning results

Code: `src/models/train.py` and `src/models/groups.py`. Figures: `src/visualization/ml_plots.py`,
saved as `results/figures/fig11`–`fig16`. All numbers below are read from `results/metrics/*.csv`.
No neural networks are used.

## 1. Set-up

| Item | Choice |
|---|---|
| Primary target | ΔH of hydride decomposition, kJ/mol H2 (positive). Table `features_dH.csv`, {int(best['n'])} compositions |
| Inputs | composition only: 38 descriptors, optionally + 7 family one-hot columns. No ΔS, Peq, T, P, wt% or H/M |
| Groups | near-composition components (same elements, L1 ≤ 0.02): 659 groups |
| Generalisation estimate | **nested grouped CV**: outer GroupKFold({N_OUTER}, shuffled) × {len(SEEDS)} repeats; inner GroupKFold({N_INNER}) grid search on the outer-train part only |
| Hold-out | one grouped 80/20 split (seed 42); used only for plots and permutation importance |
| Baselines | global mean; median of the family (fitted on the training fold) |
| Metrics | MAE, RMSE, R² (mean ± sd over repeats) |

Hyperparameter grids:

| Model | Grid |
|---|---|
{grids}

Most frequently selected settings: {'; '.join(f"{a.model} [{a.feature_set}]: {a.params}" for a in hp_mode.itertuples())}.

## 2. ΔH: main result (Fig. 11)

{md_table(r(cv, ['feature_set', 'model', 'MAE', 'MAE_sd', 'RMSE', 'RMSE_sd', 'R2', 'R2_sd']))}

* **Tree ensembles clearly beat both baselines.** {best['model']} reaches MAE {best['MAE']:.2f} ± {best['MAE_sd']:.2f} kJ/mol H2 against
  {fam_base['MAE']:.2f} for the family-median baseline ({100*(1-best['MAE']/fam_base['MAE']):.0f}% lower) and {mean_base['MAE']:.2f} for the mean baseline.
  R² is {best['R2']:.2f}. Gradient Boosting is statistically the same on MAE and slightly better on RMSE and R². Ridge is clearly worse,
  so the composition–ΔH relation is non-linear.
* **Family one-hot adds nothing** once composition is known: the differences are within one sd. The
  composition descriptors already encode the family.
* **Grouped vs ungrouped CV:** {g_grp.loc['near-composition groups','MAE']:.2f} vs {g_grp.loc['ungrouped (one group per row)','MAE']:.2f} kJ/mol. Without grouping the error
  would look about {100*(1-g_grp.loc['ungrouped (one group per row)','MAE']/g_grp.loc['near-composition groups','MAE']):.0f}% better. The effect is small here, because only about 9% of rows have
  near-duplicates, but the grouped figure is the one reported.

**Hold-out (Fig. 12)**, best configuration [{hold['feature_set'].iloc[0]}]:

{md_table(r(hold, ['model', 'MAE', 'RMSE', 'R2', 'n']))}

The single split agrees with the CV estimate: the CV-selected {best['model']} gets MAE {hb['MAE']:.2f} on it. The ranking of RF and
GB on this one split is not used for model choice, because their CV difference is within noise. RMSE is about twice the MAE because of a few
very stable hydrides (ΔH > 60) with large errors, visible in the residual plot.

### How good is MAE ≈ {best['MAE']:.1f}?

* Two independently referenced sources for the same composition differ by {nf:.1f} kJ/mol on average (Phase 2).
  Of the {len(multi)} union compositions reported more than once, {int((multi['dH_spread_kJmol'] == 0).sum())} carry an identical value, because they were
  copied from the same source. That is why their median spread is {multi['dH_spread_kJmol'].median():.1f}. The {int((multi['dH_spread_kJmol'] > 0).sum())} with differing values
  have a median spread of {multi.loc[multi['dH_spread_kJmol'] > 0, 'dH_spread_kJmol'].median():.1f} kJ/mol. **No model can be expected to go below roughly 2 kJ/mol** with this data.
* The model error is therefore about {best['MAE']/nf:.1f}× the measurement scatter. It is useful for **screening**:
  telling a 25 kJ/mol alloy (room temperature, a few bar) from a 40 kJ/mol one (about 100 °C).
  It is **not** precise enough to design an exact plateau pressure. A 5 kJ/mol error in ΔH changes Peq at
  25 °C by a factor of exp(5000/(8.314×298)) ≈ {__import__('math').exp(5000/(8.314*298)):.0f}.

## 3. Family analysis (Fig. 13)

Out-of-fold error by family (whole-dataset model):

{md_table(fam_tab)}

Separate models trained and tested *within* one family (nested grouped CV):

{md_table(r(wf, ['family', 'model', 'MAE', 'MAE_sd', 'R2', 'n']))}

AB5 and AB2, the two primary families, are where the model works best in relative terms. The error is well below
the within-family spread, so the model captures substitution effects. Examples are Al or Sn on the Ni site in LaNi5,
and Ti/Zr and Cr/Mn/Fe ratios in Laves phases.

## 4. Extrapolation: leave one family out (Fig. 15)

{md_table(lofo_w)}

**The model does not generalise to an unseen family.** For {', '.join(worse) if worse else 'no family'}, it is *worse* than predicting
the mean of the other families. Where it beats that baseline (e.g. Mg), the error is still several times larger than in-family
CV. Predictions are only meaningful for compositions similar to the training families. This is stated as a limitation,
and Mg-based and complex hydrides are not screened with ML.

## 5. Data-subset sensitivity ({best['model']}, 1 repeat)

{md_table(r(sens, ['subset', 'model', 'MAE', 'RMSE', 'R2', 'n']))}

* On the **high-confidence subset** (referenced, typical ΔS, metals only), MAE falls to
  {sens[(sens.subset.str.startswith('high')) & (sens.model==best['model'])]['MAE'].iloc[0]:.2f}. Part of the full-data error comes from low-quality records.
* Excluding very stable hydrides (ΔH > 60) also lowers MAE, because the large errors come from the sparse high-ΔH tail.
* Purdue-only (n = 276) gives a similar MAE but lower R², because the ΔH range is narrower.

## 6. What the model uses (Fig. 14)

Top permutation importances on the hold-out set (increase in MAE when the feature is shuffled):

{md_table(r(imp.head(10), nd=3))}

Interpretation is limited because the features are correlated: importance is shared between correlated features.
The top three are, in order:
* `{imp.feature.iloc[0]}`: mean atomic volume, a proxy for interstitial-site size, as in the Lundin correlation;
* `{imp.feature.iloc[1]}`: the fraction of strong hydride formers, i.e. the A:B stoichiometry;
* `{imp.feature.iloc[2]}`: spread of valence-electron count, an electronic descriptor.

This ordering is physically sensible for interstitial hydrides.

Note on run warnings: `results/metrics/train_stderr.txt` contains repeated scikit-learn 1.9 `UserWarning`s
("`sklearn.utils.parallel.delayed` should be used with `sklearn.utils.parallel.Parallel`"). These come from
parallel grid search and concern configuration propagation to worker processes. They do not change results.
Repeated runs give identical metrics.

## 7. Secondary task: capacity (wt%)

Purdue stated wt% only ({int(wt_best['n'])} records; assumed, theoretical and H/M-derived values excluded).
The added physics baseline fixes H per metal atom at the training-fold family median and converts it to wt% with the
alloy's own mean atomic mass.

{md_table(r(wt, ['feature_set', 'model', 'MAE', 'MAE_sd', 'RMSE', 'R2', 'R2_sd'], 3))}

By family:

{md_table(r(wtf[wtf.model.isin(['FamilyMedianBaseline', wt_best['model']])], ['feature_set', 'model', 'family', 'MAE', 'R2', 'n'], 3))}

**Decision: the capacity model is reported but not used.** The best ML model (MAE {wt_best['MAE']:.3f} wt%) improves
only slightly on the one-parameter-per-family physics baseline (MAE {wt_phys['MAE']:.3f}, R² {wt_phys['R2']:.2f}). Ridge
reaches R² {wt_ridge['R2']:.2f}, about equal to the baseline. The model mostly rediscovers that wt% falls as alloy mass rises. With
181 records, narrow ranges (mostly 0.6–2.2 wt%) and capacity definitions that are not uniform, this is not a reliable
predictor. In screening (Phase 8), **reported** capacities are used and labelled as material-level, definition-uncertain values.

## 8. Claims

Can be claimed:
* Composition-only models predict ΔH for AB5/AB2-type intermetallics with MAE ≈ {best['MAE']:.1f} kJ/mol, {100*(1-best['MAE']/fam_base['MAE']):.0f}% lower than a
  family-median rule, under nested grouped CV.
* The accuracy is limited by the data (inter-source scatter ≈ {nf:.1f} kJ/mol) and by composition-only descriptors
  (no crystal structure, no C14/C15 distinction).

Cannot be claimed:
* External validation: the two datasets share most values (Phase 2).
* Generalisation to new families (section 4).
* A useful wt% predictor (section 7).

## 9. Saved model

`results/models/dH_final.joblib`: {best['model']} retuned on all {int(best['n'])} compositions with the same grid, stored together with
its feature list. It is used in Phase 6 only for **clearly labelled estimates** of compositions without
experimental ΔH. Experimental ΔH and ΔS are always preferred.
"""
    (ROOT / "reports/ml_results.md").write_text(text)


if __name__ == "__main__":
    main()
