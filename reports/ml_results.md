# Phase 5: machine learning results

Code: `src/models/train.py` and `src/models/groups.py`. Figures: `src/visualization/ml_plots.py`,
saved as `results/figures/fig11`–`fig16`. All numbers below are read from `results/metrics/*.csv`.
No neural networks are used.

## 1. Set-up

| Item | Choice |
|---|---|
| Primary target | ΔH of hydride decomposition, kJ/mol H2 (positive). Table `features_dH.csv`, 725 compositions |
| Inputs | composition only: 38 descriptors, optionally + 7 family one-hot columns. No ΔS, Peq, T, P, wt% or H/M |
| Groups | near-composition components (same elements, L1 ≤ 0.02): 659 groups |
| Generalisation estimate | **nested grouped CV**: outer GroupKFold(5, shuffled) × 3 repeats; inner GroupKFold(4) grid search on the outer-train part only |
| Hold-out | one grouped 80/20 split (seed 42); used only for plots and permutation importance |
| Baselines | global mean; median of the family (fitted on the training fold) |
| Metrics | MAE, RMSE, R² (mean ± sd over repeats) |

Hyperparameter grids:

| Model | Grid |
|---|---|
| Ridge | {'ridge__alpha': [0.1, 1, 10, 100, 300, 1000]} |
| RandomForest | {'max_features': [0.33, 0.66], 'min_samples_leaf': [1, 3]} |
| GradientBoosting | {'learning_rate': [0.05, 0.1], 'max_depth': [2, 3]} |

Most frequently selected settings: GradientBoosting [composition]: {"learning_rate": 0.1, "max_depth": 3}; RandomForest [composition]: {"max_features": 0.33, "min_samples_leaf": 1}; Ridge [composition]: {"ridge__alpha": 100}; GradientBoosting [composition+family]: {"learning_rate": 0.1, "max_depth": 3}; RandomForest [composition+family]: {"max_features": 0.33, "min_samples_leaf": 1}; Ridge [composition+family]: {"ridge__alpha": 100}.

## 2. ΔH: main result (Fig. 11)

| feature_set | model | MAE | MAE_sd | RMSE | RMSE_sd | R2 | R2_sd |
|---|---|---|---|---|---|---|---|
| composition | RandomForest | 5.26 | 0.14 | 10.3 | 0.78 | 0.71 | 0.04 |
| composition+family | RandomForest | 5.26 | 0.11 | 10.5 | 0.75 | 0.71 | 0.04 |
| composition | GradientBoosting | 5.3 | 0.13 | 9.77 | 0.69 | 0.74 | 0.04 |
| composition+family | GradientBoosting | 5.32 | 0.13 | 9.8 | 0.71 | 0.74 | 0.04 |
| composition+family | Ridge | 6.99 | 0.07 | 12.4 | 0.38 | 0.59 | 0.02 |
| composition | Ridge | 7.09 | 0.03 | 12.3 | 0.25 | 0.6 | 0.02 |
| - | FamilyMedianBaseline | 8.88 | 0.11 | 16.3 | 0.37 | 0.29 | 0.03 |
| - | MeanBaseline | 12.3 | 0.02 | 19.4 | 0.02 | -0 | 0 |

* **Tree ensembles clearly beat both baselines.** RandomForest reaches MAE 5.26 ± 0.14 kJ/mol H2 against
  8.88 for the family-median baseline (41% lower) and 12.26 for the mean baseline.
  R² is 0.71. Gradient Boosting is statistically the same on MAE and slightly better on RMSE and R². Ridge is clearly worse,
  so the composition–ΔH relation is non-linear.
* **Family one-hot adds nothing** once composition is known: the differences are within one sd. The
  composition descriptors already encode the family.
* **Grouped vs ungrouped CV:** 5.26 vs 5.12 kJ/mol. Without grouping the error
  would look about 3% better. The effect is small here, because only about 9% of rows have
  near-duplicates, but the grouped figure is the one reported.

**Hold-out (Fig. 12)**, best configuration [composition]:

| model | MAE | RMSE | R2 | n |
|---|---|---|---|---|
| GradientBoosting | 5.41 | 9.79 | 0.82 | 145 |
| RandomForest | 5.55 | 11.9 | 0.73 | 145 |
| Ridge | 7.26 | 13.8 | 0.64 | 145 |
| FamilyMedianBaseline | 9.31 | 19.9 | 0.25 | 145 |
| MeanBaseline | 13.7 | 22.9 | -0 | 145 |

The single split agrees with the CV estimate: the CV-selected RandomForest gets MAE 5.55 on it. The ranking of RF and
GB on this one split is not used for model choice, because their CV difference is within noise. RMSE is about twice the MAE because of a few
very stable hydrides (ΔH > 60) with large errors, visible in the residual plot.

### How good is MAE ≈ 5.3?

* Two independently referenced sources for the same composition differ by 2.2 kJ/mol on average (Phase 2).
  Of the 261 union compositions reported more than once, 149 carry an identical value, because they were
  copied from the same source. That is why their median spread is 0.0. The 112 with differing values
  have a median spread of 1.6 kJ/mol. **No model can be expected to go below roughly 2 kJ/mol** with this data.
* The model error is therefore about 2.4× the measurement scatter. It is useful for **screening**:
  telling a 25 kJ/mol alloy (room temperature, a few bar) from a 40 kJ/mol one (about 100 °C).
  It is **not** precise enough to design an exact plateau pressure. A 5 kJ/mol error in ΔH changes Peq at
  25 °C by a factor of exp(5000/(8.314×298)) ≈ 8.

## 3. Family analysis (Fig. 13)

Out-of-fold error by family (whole-dataset model):

| family | n | family_median_MAE | RandomForest_MAE | RandomForest_R2 |
|---|---|---|---|---|
| AB | 40 | 16.1 | 8.35 | 0.51 |
| AB2 | 401 | 7.12 | 4.17 | 0.64 |
| AB5 | 116 | 5.15 | 3.09 | 0.57 |
| MIC | 33 | 13.2 | 8.88 | 0.4 |
| Mg | 35 | 10.5 | 8.41 | 0.4 |
| SS | 59 | 12.4 | 6.86 | 0.67 |

Separate models trained and tested *within* one family (nested grouped CV):

| family | model | MAE | MAE_sd | R2 | n |
|---|---|---|---|---|---|
| AB5 | FamilyMedianBaseline | 5.18 | 0.05 | -0.02 | 116 |
| AB5 | MeanBaseline | 5.17 | 0.05 | -0.02 | 116 |
| AB5 | RandomForest | 3.25 | 0.02 | 0.51 | 116 |
| AB5 | Ridge | 3.8 | 0.26 | 0.2 | 116 |
| AB2 | FamilyMedianBaseline | 7.11 | 0.02 | -0.04 | 401 |
| AB2 | MeanBaseline | 7.38 | 0.01 | -0.01 | 401 |
| AB2 | RandomForest | 4.23 | 0.1 | 0.57 | 401 |
| AB2 | Ridge | 4.64 | 0.08 | 0.61 | 401 |

AB5 and AB2, the two primary families, are where the model works best in relative terms. The error is well below
the within-family spread, so the model captures substitution effects. Examples are Al or Sn on the Ni site in LaNi5,
and Ti/Zr and Cr/Mn/Fe ratios in Laves phases.

## 4. Extrapolation: leave one family out (Fig. 15)

| held_out_family | MeanBaseline (other families) | RandomForest | n |
|---|---|---|---|
| AB | 16.2 | 16.5 | 40 |
| AB2 | 17.5 | 13.8 | 401 |
| AB5 | 5.1 | 5.86 | 116 |
| MIC | 14.3 | 11.1 | 33 |
| Mg | 36 | 14.5 | 35 |
| SS | 12.3 | 21 | 59 |

**The model does not generalise to an unseen family.** For AB, AB5, SS, it is *worse* than predicting
the mean of the other families. Where it beats that baseline (e.g. Mg), the error is still several times larger than in-family
CV. Predictions are only meaningful for compositions similar to the training families. This is stated as a limitation,
and Mg-based and complex hydrides are not screened with ML.

## 5. Data-subset sensitivity (RandomForest, 1 repeat)

| subset | model | MAE | RMSE | R2 | n |
|---|---|---|---|---|---|
| all (union) | FamilyMedianBaseline | 8.82 | 16.2 | 0.3 | 725 |
| all (union) | MeanBaseline | 12.3 | 19.4 | -0.01 | 725 |
| all (union) | RandomForest | 5.24 | 9.97 | 0.73 | 725 |
| Purdue values only | FamilyMedianBaseline | 6.32 | 9.17 | 0.19 | 276 |
| Purdue values only | MeanBaseline | 7.37 | 10.3 | -0.02 | 276 |
| Purdue values only | RandomForest | 4.94 | 7.68 | 0.43 | 276 |
| HydPARK-only compositions | FamilyMedianBaseline | 9.97 | 18.9 | 0.34 | 449 |
| HydPARK-only compositions | MeanBaseline | 15.4 | 23.3 | -0 | 449 |
| HydPARK-only compositions | RandomForest | 5.83 | 13.2 | 0.68 | 449 |
| high-confidence (referenced, typical dS, metals only) | FamilyMedianBaseline | 6.42 | 9.15 | 0.22 | 456 |
| high-confidence (referenced, typical dS, metals only) | MeanBaseline | 7.51 | 10.4 | -0 | 456 |
| high-confidence (referenced, typical dS, metals only) | RandomForest | 3.51 | 5.33 | 0.74 | 456 |
| dH <= 60 kJ/mol (exclude very stable) | FamilyMedianBaseline | 6.74 | 9.19 | 0.16 | 667 |
| dH <= 60 kJ/mol (exclude very stable) | MeanBaseline | 7.9 | 10 | -0.01 | 667 |
| dH <= 60 kJ/mol (exclude very stable) | RandomForest | 4.08 | 5.84 | 0.66 | 667 |

* On the **high-confidence subset** (referenced, typical ΔS, metals only), MAE falls to
  3.51. Part of the full-data error comes from low-quality records.
* Excluding very stable hydrides (ΔH > 60) also lowers MAE, because the large errors come from the sparse high-ΔH tail.
* Purdue-only (n = 276) gives a similar MAE but lower R², because the ΔH range is narrower.

## 6. What the model uses (Fig. 14)

Top permutation importances on the hold-out set (increase in MAE when the feature is shuffled):

| feature | importance_MAE_increase | sd |
|---|---|---|
| vol_mean | 3.57 | 0.454 |
| frac_hydride_former | 2.1 | 0.299 |
| vec_std | 1.31 | 0.206 |
| X_mean | 0.763 | 0.175 |
| mass_std | 0.514 | 0.089 |
| vec_mean | 0.468 | 0.151 |
| Tm_mean | 0.468 | 0.097 |
| radius_mean | 0.375 | 0.079 |
| size_mismatch | 0.347 | 0.068 |
| x_Zr | 0.308 | 0.109 |

Interpretation is limited because the features are correlated: importance is shared between correlated features.
The top three are, in order:
* `vol_mean`: mean atomic volume, a proxy for interstitial-site size, as in the Lundin correlation;
* `frac_hydride_former`: the fraction of strong hydride formers, i.e. the A:B stoichiometry;
* `vec_std`: spread of valence-electron count, an electronic descriptor.

This ordering is physically sensible for interstitial hydrides.

Note on run warnings: `results/metrics/train_stderr.txt` contains repeated scikit-learn 1.9 `UserWarning`s
("`sklearn.utils.parallel.delayed` should be used with `sklearn.utils.parallel.Parallel`"). These come from
parallel grid search and concern configuration propagation to worker processes. They do not change results.
Repeated runs give identical metrics.

## 7. Secondary task: capacity (wt%)

Purdue stated wt% only (181 records; assumed, theoretical and H/M-derived values excluded).
The added physics baseline fixes H per metal atom at the training-fold family median and converts it to wt% with the
alloy's own mean atomic mass.

| feature_set | model | MAE | MAE_sd | RMSE | R2 | R2_sd |
|---|---|---|---|---|---|---|
| composition | RandomForest | 0.247 | 0.003 | 0.525 | 0.415 | 0.046 |
| composition+family | RandomForest | 0.247 | 0.001 | 0.527 | 0.41 | 0.054 |
| composition | Ridge | 0.256 | 0.001 | 0.477 | 0.515 | 0.08 |
| composition+family | Ridge | 0.258 | 0.004 | 0.506 | 0.454 | 0.083 |
| composition+family | GradientBoosting | 0.258 | 0.004 | 0.532 | 0.399 | 0.063 |
| composition | GradientBoosting | 0.262 | 0.007 | 0.536 | 0.388 | 0.074 |
| - | PhysicsBaseline(H/M x mass) | 0.286 | 0.009 | 0.486 | 0.497 | 0.072 |
| - | FamilyMedianBaseline | 0.332 | 0.005 | 0.612 | 0.205 | 0.064 |
| - | MeanBaseline | 0.439 | 0.002 | 0.692 | -0.016 | 0.005 |

By family:

| feature_set | model | family | MAE | R2 | n |
|---|---|---|---|---|---|
| - | FamilyMedianBaseline | AB | 0.284 | -0.117 | 23 |
| - | FamilyMedianBaseline | AB2 | 0.273 | -0.036 | 74 |
| - | FamilyMedianBaseline | AB5 | 0.258 | -0.098 | 59 |
| composition | RandomForest | AB | 0.262 | 0.033 | 23 |
| composition | RandomForest | AB2 | 0.216 | 0.157 | 74 |
| composition | RandomForest | AB5 | 0.116 | 0.737 | 59 |
| composition+family | RandomForest | AB | 0.261 | 0.031 | 23 |
| composition+family | RandomForest | AB2 | 0.216 | 0.152 | 74 |
| composition+family | RandomForest | AB5 | 0.117 | 0.723 | 59 |

**Decision: the capacity model is reported but not used.** The best ML model (MAE 0.247 wt%) improves
only slightly on the one-parameter-per-family physics baseline (MAE 0.286, R² 0.50). Ridge
reaches R² 0.51, about equal to the baseline. The model mostly rediscovers that wt% falls as alloy mass rises. With
181 records, narrow ranges (mostly 0.6–2.2 wt%) and capacity definitions that are not uniform, this is not a reliable
predictor. In screening (Phase 8), **reported** capacities are used and labelled as material-level, definition-uncertain values.

## 8. Claims

Can be claimed:
* Composition-only models predict ΔH for AB5/AB2-type intermetallics with MAE ≈ 5.3 kJ/mol, 41% lower than a
  family-median rule, under nested grouped CV.
* The accuracy is limited by the data (inter-source scatter ≈ 2.2 kJ/mol) and by composition-only descriptors
  (no crystal structure, no C14/C15 distinction).

Cannot be claimed:
* External validation: the two datasets share most values (Phase 2).
* Generalisation to new families (section 4).
* A useful wt% predictor (section 7).

## 9. Saved model

`results/models/dH_final.joblib`: RandomForest retuned on all 725 compositions with the same grid, stored together with
its feature list. It is used in Phase 6 only for **clearly labelled estimates** of compositions without
experimental ΔH. Experimental ΔH and ΔS are always preferred.
