# Phase 8: stationary vs mobile screening

Code: `src/screening/screen.py` (method, constants), `src/screening/report.py` (this file), and
`src/visualization/screening_plots.py` (Figs. 24–26). Tables: `results/tables/screening_*.csv`.

**Scope.** This is a *material-level* screening. Capacities are the reported values from the Purdue files
(definition not uniform, Phase 1). Thermodynamics are the experimental ΔH/ΔS (Phase 6). No ML prediction
is used. A real storage system adds a pressure vessel, heat exchanger, bed porosity and balance of plant, so
its gravimetric capacity is much lower than the material's. The DOE target (5.5 wt%) is a *system* target
and is drawn only for orientation.

## 1. Method

1. Candidates: all 337 Purdue materials. Mischmetal alloys are included here, because screening needs only measured
   properties, not elemental descriptors.
2. A data-quality gate and **hard constraints** remove unsuitable materials (each failure is recorded with its reason).
3. The remaining criteria are normalised to 0–1 among the candidates that pass, and combined with **transparent weights**.
4. A **sensitivity analysis** varies the weights (2000 random draws × 2 schemes, plus one-at-a-time changes) and the
   constraint thresholds.

| application | hard constraint | engineering reason |
|---|---|---|
| data quality (both) | |ΔS| within 70–170 J/(mol K); capacity not 'assumed'/'unconfirmed' | removes records flagged in Phases 1–2 |
| mobile | T(1 bar, full capacity) ≤ 80 °C | desorption driven by PEM fuel-cell waste heat (stack 60–80 °C) |
| mobile | P(50 °C) ≤ 50 bar | tank pressure on a hot day stays moderate |
| mobile | charging P(25 °C) ≤ 100 bar | refuelling without very high compression |
| stationary | T(1 bar, full capacity) ≤ 150 °C | low-grade industrial or electrolyser/boiler heat |
| stationary | P(25 °C) ≤ 10 bar | low-pressure storage at room temperature (safety, cheaper vessel) |
| stationary | P(50 °C) ≤ 30 bar | warm-day pressure limit |
| stationary | charging P(25 °C) ≤ 30 bar | fill directly from a pressurised PEM electrolyser (no compressor) — assumed 30 bar delivery |

Criteria (1 = best):

| criterion | definition |
|---|---|
| capacity | reported wt%, min–max scaled |
| heat | reaction heat per kg H2 (width-weighted over plateaus), lower is better |
| kinetics | family-level class from Phase 7: AB5/AB2/AB/AB3 = 1.0, complex = 0.25, Mg = 0.0; no data (SS, A2B7, Misc) = 0.5 and flagged |
| hysteresis | ln(Pa/Pd) at 25 °C, lower is better; missing = 0.5 (neutral) |
| pressure_fit | 1 if 1 ≤ P(25 °C) ≤ 10 bar, falling to 0 one decade outside |
| pressure_safety | lower log P(25 °C) is better (stationary only) |
| cost | qualitative element indicator: common metals 1; rare earth/mischmetal, Co, V, minor metals 0.5; precious metals 0. **Not a price model** |

Weights (sum to 1 per application). Mobile emphasises capacity and heat; stationary emphasises cost, low pressure and cycling
loss (hysteresis):

| criterion | mobile | stationary |
|---|---|---|
| capacity | 0.35 | 0.1 |
| heat | 0.2 | 0.1 |
| kinetics | 0.15 | 0.1 |
| hysteresis | 0.1 | 0.15 |
| pressure_fit | 0.1 | 0.1 |
| cost | 0.1 | 0.25 |
| pressure_safety | 0 | 0.2 |

Multi-plateau materials use the *most stable* plateau for T(1 bar), because full capacity is needed, and the *highest*
pressure plateau for pressure limits.

## 2. Constraint outcome (Fig. 24)

| | mobile | stationary |
|---|---|---|
| pass data-quality gate | 319 | 319 |
| pass all constraints | 232 | 252 |

Why materials fail:

**Mobile**

| reason (a material may fail several) | n_materials |
|---|---|
| data-quality gate | 18 |
| T(1 bar) too high | 56 |
| P(25 °C) too high | 0 |
| P(50 °C) too high | 35 |
| charging pressure too high | 12 |

**Stationary**

| reason (a material may fail several) | n_materials |
|---|---|
| data-quality gate | 18 |
| T(1 bar) too high | 10 |
| P(25 °C) too high | 57 |
| P(50 °C) too high | 51 |
| charging pressure too high | 32 |

By family:

| family | n | mobile_pass | mobile_best_rank | stationary_pass | stationary_best_rank |
|---|---|---|---|---|---|
| AB5 | 146 | 121 | 10 | 121 | 6 |
| AB2 | 106 | 66 | 1 | 67 | 2 |
| AB | 29 | 17 | 3 | 24 | 1 |
| SS | 24 | 14 | 35 | 19 | 141 |
| AB3 | 14 | 7 | 44 | 9 | 16 |
| A2B7 | 8 | 3 | 182 | 6 | 222 |
| Misc | 5 | 4 | 155 | 5 | 79 |
| Mg | 4 | 0 | - | 0 | - |
| Complex | 1 | 0 | - | 1 | 39 |

## 3. Rankings (Fig. 25)

### Mobile: top 10

| rank | material | family | wt_pct | T1_full_C | P25_bar | heat_MJ_per_kgH2 | cost_label | score | flags |
|---|---|---|---|---|---|---|---|---|---|
| 1 | Ti1.3Cr1.2Mn0.8 | AB2 | 1.9 | -41.8 | 18.6 | 12.4 | common metals | 0.74 |  |
| 2 | Ti1.2CrMn | AB2 | 2.02 | -44.1 | 22.3 | 12.7 | common metals | 0.73 |  |
| 3 | Ti0.56V0.3Zr0.1Mn0.94Fe0.06Ni0.04 | AB | 2.2 | -5.67 | 3.63 | 13.8 | rare earth / Co / minor metal | 0.72 | PCI ΔH mismatch, ΔH refit from isotherms |
| 4 | Ti0.9Zr0.2Mn1.4Cr0.4Vf0.2 | AB2 | 2.1 | -7.27 | 3.48 | 12.6 | rare earth / Co / minor metal | 0.72 |  |
| 5 | Ti0.8Zr0.2Mn1.5Cr0.5 | AB2 | 2 | -23.1 | 8.44 | 13.6 | common metals | 0.71 | Sandia ref unverified |
| 6 | TiFe | AB | 1.86 | -8.33 | 4.16 | 13.9 | common metals | 0.7 |  |
| 7 | Ti0.8Zr0.2Mn1.2Cr0.8 | AB2 | 2 | -15.3 | 6.18 | 14.3 | common metals | 0.7 | Sandia ref unverified |
| 8 | TiMn1.4 | AB2 | 1.75 | -4.87 | 3.58 | 14.1 | common metals | 0.7 | PCI ΔH mismatch, ΔH refit from isotherms |
| 9 | TiFe0.85Mn0.15 | AB | 1.9 | 2.27 | 2.67 | 14.6 | common metals | 0.7 |  |
| 10 | Mm0.3Ca0.7Ni5 | AB5 | 1.9 | -8.1 | 3.83 | 13.2 | rare earth / Co / minor metal | 0.7 | Sandia ref unverified |

### Stationary: top 10

| rank | material | family | wt_pct | T1_full_C | P25_bar | heat_MJ_per_kgH2 | cost_label | score | flags |
|---|---|---|---|---|---|---|---|---|---|
| 1 | TiFe0.9Al0.1 | AB | 1.3 | 16.8 | 1.41 | 14.9 | common metals | 0.73 |  |
| 2 | Ti0.9Zr0.1Mn1.4 | AB2 | 1.91 | 29.7 | 0.8 | 17.2 | common metals | 0.72 | ΔH refit from isotherms |
| 3 | Ti0.5Zr0.5Mn1.2Fe0.3 | AB2 | 1.9 | 111 | 0.01 | 24.2 | common metals | 0.7 | Sandia ref unverified, ΔH refit from isotherms |
| 4 | TiFe0.8Mn0.2 | AB | 1.3 | 29.4 | 0.83 | 15.8 | common metals | 0.7 |  |
| 5 | TiMn1.4 | AB2 | 1.75 | -4.87 | 3.58 | 14.1 | common metals | 0.7 | PCI ΔH mismatch, ΔH refit from isotherms |
| 6 | CaNi5 | AB5 | 1.15 | 46.3 | 0.45 | 14.7 | common metals | 0.69 | ΔH refit from isotherms |
| 7 | TiFe0.85Mn0.15 | AB | 1.9 | 2.27 | 2.67 | 14.6 | common metals | 0.69 |  |
| 8 | Zr0.7Ti0.3CrFe | AB2 | 1.7 | 26.8 | 0.93 | 14.6 | common metals | 0.69 | ΔH refit from isotherms |
| 9 | ZrCrFe1.6 | AB2 | 1.2 | -2.98 | 3.37 | 14.4 | common metals | 0.69 |  |
| 10 | TiFe | AB | 1.86 | -8.33 | 4.16 | 13.9 | common metals | 0.68 |  |

### Reference materials

| material | wt_pct | T1_full_C | P25_bar | mobile | stationary |
|---|---|---|---|---|---|
| LaNi5 | 1.49 | 12 | 1.84 | rank 58 / 232 | rank 66 / 252 |
| MmNi4.5Al0.5 | 1.2 | 11 | 1.83 | rank 98 / 232 | rank 88 / 252 |
| CaNi5 | 1.15 | 46 | 0.449 | rank 74 / 232 | rank 6 / 252 |
| TiFe | 1.86 | -8 | 4.16 | rank 6 / 232 | rank 10 / 252 |
| TiFe0.9Mn0.1 | 1.9 | 2 | 2.58 | rank 11 / 232 | rank 12 / 252 |
| Hydralloy C2 | 1.6 | -25 | 11.8 | rank 57 / 232 | fails: P(25 °C) 11.8 > 10 bar |
| TiCrMn | 1.8 | -79 | 108 | fails: P(50 °C) 212 > 50 bar; charging P(25 °C) 224 > 100 bar | fails: P(25 °C) 108 > 10 bar; P(50 °C) 212 > 30 bar; charging P(25 °C) 224 > 30 bar |
| V-Ti-Fe BCC | 3.7 | 35 | 0.562 | rank 35 / 232 | rank 141 / 252 |
| NaAlH4 (Ti-doped) | 3.9 | 100 | 0.787 | fails: T(1 bar) 100 > 80 °C | rank 39 / 252 |
| Mg2Ni | 3.6 | 255 | 1.2e-05 | fails: T(1 bar) 255 > 80 °C | fails: T(1 bar) 255 > 150 °C |
| MgH2 | 7.6 | 302 | 2.5e-07 | fails: T(1 bar) 302 > 80 °C | fails: T(1 bar) 302 > 150 °C |

**Interpretation.**
* *Mobile.* The best candidates are Ti-based AB2 Laves alloys (Ti–Cr–Mn, Ti–Zr–Mn–Cr) and TiFe-type alloys. The top 10 reach
  1.75–2.20 wt% at the material level, reach 1 bar at or below 2 °C, and need
  12.5–14.6 MJ/kg H2 (10–12% of LHV).
  The two highest-ranked AB2 alloys run at 19–22 bar at 25 °C, so they are high-pressure hydrides. LaNi5 passes but ranks only
  58 because of its low capacity (1.49 wt%).
  **No interstitial hydride comes near the 5.5 wt% system target.** Material-level capacities of about 2 wt% suit mobile
  uses where mass matters less than volume, safety or low pressure.
* *Stationary.* Constraints and weights favour **low-pressure alloys made of common metals**: TiFe and its Al- and Mn-substituted
  variants (Ni and Cr variants follow just below the top 10), Ti–Zr–Mn AB2 and CaNi5. TiFe-type alloys make up 4 of the top 10. They combine a plateau of
  0.8–4.2 bar at 25 °C, cheap elements and 1.3–1.9 wt%, and weight barely matters in stationary use. Ti-doped NaAlH4 passes (T(1 bar) about 100 °C ≤ 150 °C),
  but ranks 39 because of its family-level kinetics class and heat demand.
* Data caveats are kept visible. Several top-ranked entries cite unverified Sandia references, or have PCI curves whose
  Van't Hoff ΔH differs by more than 5 kJ/mol from the tabulated one (e.g. Ti0.56V0.3Zr0.1Mn0.94Fe0.06Ni0.04).
  Two files (Ti1Mn1.4V0.62, Ti1Mn1.5V0.62) carry identical data. Any candidate taken forward needs its own PCT measurement (Phase 9).

## 4. Sensitivity (Fig. 26)

Probability of staying in the top 10 under weight perturbation. "Perturbed": Dirichlet centred on the base weights
(concentration 20). "Random": uniform Dirichlet, i.e. any weights.

**Mobile**

| base_rank | material | perturbed (Dirichlet, base x 20) | random (uniform Dirichlet) |
|---|---|---|---|
| 1 | Ti1.3Cr1.2Mn0.8 | 0.88 | 0.72 |
| 2 | Ti1.2CrMn | 0.84 | 0.62 |
| 3 | Ti0.56V0.3Zr0.1Mn0.94Fe0.06Ni0.04 | 0.71 | 0.48 |
| 4 | Ti0.9Zr0.2Mn1.4Cr0.4Vf0.2 | 0.71 | 0.44 |
| 5 | Ti0.8Zr0.2Mn1.5Cr0.5 | 0.77 | 0.45 |
| 6 | TiFe | 0.57 | 0.53 |
| 7 | Ti0.8Zr0.2Mn1.2Cr0.8 | 0.48 | 0.28 |
| 8 | TiMn1.4 | 0.44 | 0.65 |
| 9 | TiFe0.85Mn0.15 | 0.41 | 0.42 |
| 10 | Mm0.3Ca0.7Ni5 | 0.47 | 0.45 |

**Stationary**

| base_rank | material | perturbed (Dirichlet, base x 20) | random (uniform Dirichlet) |
|---|---|---|---|
| 1 | TiFe0.9Al0.1 | 0.85 | 0.61 |
| 2 | Ti0.9Zr0.1Mn1.4 | 0.88 | 0.52 |
| 3 | Ti0.5Zr0.5Mn1.2Fe0.3 | 0.58 | 0.29 |
| 4 | TiFe0.8Mn0.2 | 0.63 | 0.2 |
| 5 | TiMn1.4 | 0.67 | 0.53 |
| 6 | CaNi5 | 0.47 | 0.14 |
| 7 | TiFe0.85Mn0.15 | 0.6 | 0.44 |
| 8 | Zr0.7Ti0.3CrFe | 0.47 | 0.23 |
| 9 | ZrCrFe1.6 | 0.42 | 0.23 |
| 10 | TiFe | 0.41 | 0.36 |

One-at-a-time changes (weight × 0 or × 2). Kendall τ of the full ranking vs base, and overlap of the top 10:

**Mobile**

| criterion | weight_factor | kendall_tau_vs_base | top10_overlap |
|---|---|---|---|
| capacity | 0 | 0.71 | 4 |
| capacity | 2 | 0.86 | 7 |
| heat | 0 | 0.79 | 7 |
| heat | 2 | 0.87 | 6 |
| kinetics | 0 | 0.95 | 8 |
| kinetics | 2 | 0.97 | 10 |
| hysteresis | 0 | 0.92 | 5 |
| hysteresis | 2 | 0.92 | 9 |
| pressure_fit | 0 | 0.87 | 9 |
| pressure_fit | 2 | 0.92 | 9 |
| cost | 0 | 0.88 | 5 |
| cost | 2 | 0.92 | 7 |

**Stationary**

| criterion | weight_factor | kendall_tau_vs_base | top10_overlap |
|---|---|---|---|
| cost | 0 | 0.65 | 2 |
| cost | 2 | 1 | 10 |
| pressure_safety | 0 | 0.7 | 6 |
| pressure_safety | 2 | 0.65 | 3 |
| hysteresis | 0 | 0.82 | 3 |
| hysteresis | 2 | 0.91 | 9 |
| kinetics | 0 | 0.96 | 9 |
| kinetics | 2 | 0.98 | 10 |
| heat | 0 | 0.84 | 7 |
| heat | 2 | 0.88 | 9 |
| capacity | 0 | 0.88 | 8 |
| capacity | 2 | 0.91 | 8 |
| pressure_fit | 0 | 0.67 | 3 |
| pressure_fit | 2 | 0.78 | 8 |

Constraint thresholds:

| application | threshold | value | n_pass | families_passing | top3 |
|---|---|---|---|---|---|
| mobile | T1_full_max_C | 60 | 203 | AB5 106, AB2 59, AB 15, SS 11, AB3 7, Misc 3, A2B7 2 | Ti[1.3]Cr[1.2]Mn[0.8]; Ti[1.2]Cr[1]Mn[1]; Ti[0.56]V[0.3]Zr[0.1]Mn[0.94]Fe[0.06]Ni[0.04] |
| mobile | T1_full_max_C | 80 | 232 | AB5 121, AB2 66, AB 17, SS 14, AB3 7, Misc 4, A2B7 3 | Ti[1.3]Cr[1.2]Mn[0.8]; Ti[1.2]Cr[1]Mn[1]; Ti[0.56]V[0.3]Zr[0.1]Mn[0.94]Fe[0.06]Ni[0.04] |
| mobile | T1_full_max_C | 100 | 253 | AB5 125, AB2 72, AB 20, SS 18, AB3 9, Misc 5, A2B7 3, Complex 1 | Ti[1.3]Cr[1.2]Mn[0.8]; Ti[1.2]Cr[1]Mn[1]; Ti[0.56]V[0.3]Zr[0.1]Mn[0.94]Fe[0.06]Ni[0.04] |
| mobile | P50_max_bar | 30 | 219 | AB5 117, AB2 60, AB 17, SS 12, AB3 6, Misc 4, A2B7 3 | Ti[0.56]V[0.3]Zr[0.1]Mn[0.94]Fe[0.06]Ni[0.04]; Ti[0.9]Zr[0.2]Mn[1.4]Cr[0.4]Vf[0.2]; Ti[0.8]Zr[0.2]Mn[1.5]Cr[0.5] |
| mobile | P50_max_bar | 50 | 232 | AB5 121, AB2 66, AB 17, SS 14, AB3 7, Misc 4, A2B7 3 | Ti[1.3]Cr[1.2]Mn[0.8]; Ti[1.2]Cr[1]Mn[1]; Ti[0.56]V[0.3]Zr[0.1]Mn[0.94]Fe[0.06]Ni[0.04] |
| mobile | P50_max_bar | 100 | 250 | AB5 127, AB2 76, AB 18, SS 15, AB3 7, Misc 4, A2B7 3 | Ti[1.3]Cr[1.2]Mn[0.8]; Ti[1.2]Cr[1]Mn[1]; Ti[0.56]V[0.3]Zr[0.1]Mn[0.94]Fe[0.06]Ni[0.04] |
| stationary | T1_full_max_C | 80 | 211 | AB5 113, AB2 57, AB 17, SS 12, AB3 6, Misc 4, A2B7 2 | Ti[1]Fe[0.9]Al[0.1]; Ti[0.9]Zr[0.1]Mn[1.4]; Ca[1]Ni[5] |
| stationary | T1_full_max_C | 150 | 252 | AB5 121, AB2 67, AB 24, SS 19, AB3 9, A2B7 6, Misc 5, Complex 1 | Ti[1]Fe[0.9]Al[0.1]; Ti[0.9]Zr[0.1]Mn[1.4]; Ti[0.5]Zr[0.5]Mn[1.2]Fe[0.3] |
| stationary | T1_full_max_C | 350 | 261 | AB5 121, AB2 68, AB 25, SS 19, AB3 11, A2B7 7, Misc 5, Mg 4, Complex 1 | Ti[1]Fe[0.9]Al[0.1]; Ti[0.9]Zr[0.1]Mn[1.4]; Ti[1]Mn[1.4] |
| stationary | P25_max_bar | 5 | 223 | AB5 105, AB2 57, AB 24, SS 18, AB3 8, Misc 5, A2B7 5, Complex 1 | Ti[1]Fe[0.9]Al[0.1]; Ti[0.9]Zr[0.1]Mn[1.4]; Ti[0.5]Zr[0.5]Mn[1.2]Fe[0.3] |
| stationary | P25_max_bar | 10 | 252 | AB5 121, AB2 67, AB 24, SS 19, AB3 9, A2B7 6, Misc 5, Complex 1 | Ti[1]Fe[0.9]Al[0.1]; Ti[0.9]Zr[0.1]Mn[1.4]; Ti[0.5]Zr[0.5]Mn[1.2]Fe[0.3] |
| stationary | P25_max_bar | 20 | 260 | AB5 125, AB2 70, AB 24, SS 19, AB3 9, A2B7 7, Misc 5, Complex 1 | Ti[1]Fe[0.9]Al[0.1]; Ti[0.9]Zr[0.1]Mn[1.4]; Ti[1]Fe[0.8]Mn[0.2] |

Conclusions from the sensitivity analysis:
* The *composition of the top group* is robust: Ti-based AB2/AB alloys for mobile, TiFe-type and Ti–Zr–Mn alloys for stationary.
  The exact order inside it is not, and depends on the weights. Rankings should be read as tiers, not as a single winner.
* The largest one-at-a-time effects are, for mobile: capacity ×0 (τ = 0.71), heat ×0 (τ = 0.79); for stationary: pressure_safety ×2 (τ = 0.65), cost ×0 (τ = 0.65).
* Doubling the mobile capacity weight moves the V–Ti–Fe BCC solid solutions (3.4–3.7 wt%) to the top
  (V[0.855]Ti[0.095]Fe[0.05]; V[0.8455]Ti[0.1045]Fe[0.05]; Ti[0.56]V[0.3]Zr[0.1]Mn[0.94]Fe[0.06]Ni[0.04]). Their high capacity is offset in the base case by higher heat demand and
  the neutral (no-data) kinetics class.
* Setting the stationary cost weight to zero brings a Ca–mischmetal AB5 alloy into the top 3 (Ti[0.56]V[0.3]Zr[0.1]Mn[0.94]Fe[0.06]Ni[0.04]; Mm[0.3]Ca[0.7]Ni[5]; Zr[0.76]Ti[0.24]Ni[1.16]Mn[0.63]V[0.14]Fe[0.18]).
* Mg-based hydrides enter the stationary set only when heat at about 350 °C is available. In that case
  261 materials pass, including all 4 Mg-based ones.

## 5. Under-represented families (MgH2, Mg2Ni, NaAlH4)

| purdue_id | family | wt_pct | capacity_definition | T1_full_C | heat_MJ_per_kgH2 | mobile_fail_reasons | stationary_fail_reasons |
|---|---|---|---|---|---|---|---|
| Mg[1] | Mg | 7.6 | theoretical_or_reduced_from_theoretical | 302 | 38.8 | T(1 bar) 302 > 80 °C | T(1 bar) 302 > 150 °C |
| Mg[1]Ni[0.02] | Mg | 7.5 | literature_value_definition_unstated | 276 | 35.7 | T(1 bar) 276 > 80 °C | T(1 bar) 276 > 150 °C |
| Mg[2]Cu[1] | Mg | 2 | literature_value_definition_unstated | 239 | 36.2 | T(1 bar) 239 > 80 °C | T(1 bar) 239 > 150 °C |
| Mg[2]Ni[1] | Mg | 3.6 | literature_value_definition_unstated | 255 | 32 | T(1 bar) 255 > 80 °C | T(1 bar) 255 > 150 °C |
| Na[1]Al[1]H[1] | Complex | 3.9 | theoretical_or_reduced_from_theoretical | 99.5 | 20.5 | T(1 bar) 100 > 80 °C | nan |

These families have the highest capacities in the dataset (3.6–7.6 wt%). They are excluded from mobile PEMFC use
by thermodynamics alone: ΔH of 47–78 kJ/mol means 100–300 °C for 1 bar and 23–39 MJ/kg H2 (19–32% of LHV). Their kinetic
records show absorption activation energies about 3–6× those of the intermetallics (92–132 vs median 24–31 kJ/mol, Phase 7). This agrees with standard reviews (Sandrock
1999, J. Alloys Compd. 293–295, 877; Schlapbach & Züttel 2001, Nature 414, 353): Mg-based and complex hydrides need
destabilisation, catalysis or nanostructuring, plus high-temperature heat integration. For stationary systems with a high-temperature
heat source (e.g. solid-oxide fuel cell or concentrated solar heat), MgH2 becomes a candidate (scenario above).
With only 4 Mg-based and 1 complex hydride in the Purdue data, this assessment rests on individual records, not statistics.

## 6. Volumetric density (where density is stated)

Hydrogen per unit volume of *solid* material, ρ·w/(1−w), for 37 materials with a stated density. It is an upper bound:
no bed porosity (often 40–50%) and no lattice expansion on hydriding, and some densities were back-calculated by the
curator ("assuming a porosity of 40%").

| material | rho_kg_m3_stated | wt_pct | vol_H_kg_m3_solid |
|---|---|---|---|
| CaNi5 | 6.6e+03 | 1.2 | 76.8 |
| LaNi5 | 8.3e+03 | 1.5 | 126 |
| MgH2 | 1.8e+03 | 7.6 | 148 |
| MmNi4.5Al0.5 | 8.1e+03 | 1.2 | 98.4 |
| NaAlH4 (Ti-doped) | 1.8e+03 | 3.9 | 73 |
| TiCrMn | 6.4e+03 | 1.8 | 117 |
| TiFe | 6.5e+03 | 1.9 | 123 |

Range over all 37: 56–150 kg H2/m³. For comparison, liquid H2 is 70.8 kg/m³ and compressed H2 at 700 bar
about 40 kg/m³ (NIST). Even after allowing about 50% bed porosity, hydrides store hydrogen at least as densely as
700 bar gas and at a few bar. This is their main argument for stationary and volume-limited applications, against
their weight penalty.

## 7. Limits of this screening

* Material level only. No vessel, heat exchanger or system mass and volume.
* Capacity definitions are not uniform. Cost is a qualitative element indicator. Kinetics enter only as a family-level class.
* Hysteresis is missing for 214 of 337 materials and scored as neutral.
* Cycle life, activation behaviour, impurity tolerance (O2, H2O, CO) and safety (pyrophoricity) are not in the data. These
  are often decisive in practice (e.g. TiFe needs activation).
