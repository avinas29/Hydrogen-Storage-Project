# Phase 4: composition feature engineering

Code: `src/features/composition.py` (descriptors) and `src/features/build.py` (tables).
The input is composition only. No thermodynamic, pressure, temperature or capacity value is
used as a feature for ΔH, and the build script asserts this.

## 1. Elemental data

Every elemental value is read from pymatgen's periodic table (pymatgen
2026.10.24, `periodic_table.json`), and the values used are exported to
`results/tables/elemental_property_table.csv`. All 52 elements that occur have a value for
every property used. Metallic radius (missing for 8 elements) and calculated radius
(missing for 5) were therefore **not** used. No elemental value was filled in by hand.

| Property | pymatgen attribute | Unit / note |
|---|---|---|
| `mass` | `atomic_mass` | g/mol |
| `X` | `X` | Pauling electronegativity |
| `radius` | `atomic_radius` | empirical atomic radius, Å |
| `Tm` | `melting_point` | K |
| `vol` | `molar_volume` | cm3/mol |
| `vec` | `group` | valence electrons (group convention) |

Valence electrons follow the VEC convention used for alloys: group number for groups 1–12,
group − 10 for groups 13–18, and 3 for lanthanides and actinides.
`frac_hydride_former` counts atoms of groups 1–5, the lanthanides/actinides, and Pd. These are the
"A-side" elements that form stable binary hydrides (Sandrock 1999).

## 2. Descriptors

| group | n | kept |
|---|---|---|
| alloy descriptor | 4 | 4 |
| elemental fraction | 12 | 12 |
| elemental statistic | 24 | 22 |
| family | 7 | 7 |

* Elemental statistics: fraction-weighted mean and std, and min and max, for each of the 6 properties (24).
* Alloy descriptors: number of elements, ideal configurational entropy, atomic size mismatch δ,
  and fraction of hydride formers (4).
* Atomic fractions for the 12 elements present in at least 5% of compositions: Zr, Ti, Mn, Fe, Ni, Cr, V, La, Co, Al, Mg, Cu (12).
* Family one-hot (fam_AB, fam_AB2, fam_AB5, fam_MIC, fam_Mg, fam_SS, fam_other). Families with fewer than
  10 compositions are grouped as `other`. Family is a structural label known before any hydrogen
  measurement, so it is allowed as an input. It is kept as a **separate, optional** set so that Phase 5 can
  report composition-only and composition + family models side by side.

## 3. Collinearity pruning

Features were taken in order of interpretability (means, alloy descriptors, std, min/max,
fractions). A feature was dropped if its |Pearson r| with an already-kept feature exceeded 0.95:

| dropped | because_of | abs_r |
|---|---|---|
| radius_std | size_mismatch | 0.999 |
| vol_max | radius_max | 0.964 |

45 of 47 features remain. Tree models are insensitive to the remaining correlation. For
Ridge regression, features are standardised inside the CV pipeline.

## 4. Task tables

| Table | Rows | Target | Notes |
|---|---|---|---|
| `data/processed/features_dH.csv` | 725 | `dH_kJmol` (union, positive desorption) | one row per composition; `cv_group` = composition |
| `data/processed/features_wt.csv` | 181 | `wt_pct` (Purdue, stated wt% only) | families: AB2 74, AB5 59, AB 23, SS 7, A2B7 6, Misc 5, AB3 4, Mg 3 |

Purdue records left out of the wt% table (156 of 337):

| reason (a record may meet several) | n_records |
|---|---|
| capacity given as H/M (converted, not stated) | 114 |
| pseudo-element composition (Mm/Lm/Vf) | 49 |
| capacity assumed / approximate / theoretical / unconfirmed | 17 |

11 ΔH compositions contain B, Si, Ge, Sb, Bi or O as alloying additions. They are kept and flagged.

## 5. Sanity check: univariate correlation with the target

No single feature correlates very strongly with the target (max |Spearman| =
0.54 for ΔH and 0.70 for wt%), which is consistent with no leakage. The signs match known physics:

**ΔH**

| feature | spearman | pearson |
|---|---|---|
| vol_mean | 0.539 | 0.647 |
| fam_AB2 | -0.512 | -0.398 |
| x_Cr | -0.389 | -0.242 |
| mass_std | 0.361 | 0.279 |
| size_mismatch | 0.361 | 0.213 |
| x_Fe | -0.361 | -0.24 |
| n_elements | -0.346 | -0.292 |
| config_entropy | -0.34 | -0.275 |

* `vol_mean` > 0: a larger average atomic volume means larger interstitial sites and a more stable
  hydride. This is the interstitial-hole-size correlation of Lundin, Lynch and Magee (1977,
  J. Less-Common Met. 56, 19).
* AB2 is negative (less stable on average, consistent with Phase 3). Cr, Fe and Mn substitution is negative.
  Mg is positive.

**wt%**

| feature | spearman | pearson |
|---|---|---|
| mass_mean | -0.699 | -0.638 |
| X_mean | -0.697 | -0.583 |
| vec_mean | -0.67 | -0.635 |
| mass_max | -0.661 | -0.519 |
| config_entropy | 0.578 | 0.241 |
| x_Ti | 0.575 | 0.306 |
| x_Mn | 0.575 | 0.29 |
| fam_AB2 | 0.574 | 0.325 |

* `mass_mean` < 0: at a similar H/M, lighter alloys hold a larger weight fraction of hydrogen. This is
  the arithmetic link wt% ≈ (H/M · 1.008) / (M̄ + H/M · 1.008). So a wt% model will mostly learn
  alloy mass, which matters when interpreting it in Phase 5.

## 6. Limitations

* The descriptors are composition averages. They cannot tell C14 from C15 Laves phases, ordering,
  or microstructure, all of which affect ΔH for the same composition. The HydPARK C14/C15 duplicates
  in Phase 2 show this directly.
* The tabulated elemental radius is coarse (0.05 Å resolution), so `radius_*` features carry limited detail.
* Mischmetal (Mm/Lm) and ferrovanadium alloys cannot be featurised and are excluded from ML.
