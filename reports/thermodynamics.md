# Phase 6: Van't Hoff thermodynamics and operating windows

Code: `src/thermodynamics/vant_hoff.py` (equations), `analysis.py` (tables), `report.py` (this file),
and `src/visualization/thermo_plots.py` (Figs. 17–20). Tables are in `results/tables/vant_hoff_*.csv`.
**All windows in sections 2–5 use experimental ΔH and ΔS from the Purdue files.** Section 6 is the
only place where ML-predicted ΔH is used, and every number there is labelled ESTIMATE.

## 1. Equations, sign convention and units

Desorption equilibrium of the plateau, MHx ⇌ M + (x/2) H2, written per mol H2:

    ln(Peq / P0) = −ΔH / (R T) + ΔS / R

* ΔH and ΔS are **positive desorption magnitudes**. The Purdue files store formation values
  (negative). The toolbox's `Peq.m` evaluates `101325·exp((ΔH_f − TΔS_f)/(RT))`, which is the same equation.
  The HydPARK ln Peq(25 °C) column reproduces it with the same convention (Phase 1).
* **P0 = 1 atm.** Both the toolbox (p0 = 101325 Pa) and HydPARK reference ΔS to 1 atm. Pressures are
  converted to bar (×1.01325). R = 8.314462618 J mol⁻¹ K⁻¹.
* Temperature at a given pressure: T(P) = ΔH / (ΔS − R ln(P/P0)).
* Reaction heat per kg H2: Q = ΔH / M(H2), with M(H2) = 2.01588 g/mol, so 1 kJ/mol H2 = 0.496 MJ/kg H2.
  It is expressed as a fraction of the H2 lower heating value (119.96 MJ/kg). Desorption absorbs Q;
  absorption releases about the same amount (the absorption ΔH, where stated).
* **Worked example, LaNi5** (ΔH = 32.15 kJ/mol, ΔS = 112.8 J/(mol K)):
  ln(P/atm) at 298.15 K = −32151/(8.314×298.15) + 112.8/8.314 = 0.597,
  so P = 1.817 atm = 1.84 bar. T(1 bar) = 11.6 °C.
  Q = 15.9 MJ/kg H2 (13.3% of LHV).

Model limits: the relation assumes a flat plateau, and ΔH and ΔS independent of temperature. Real plateaus
are sloped and hysteretic (sections 4–5). Kinetics and heat transfer, not thermodynamics, usually limit the
achievable flow rate.

## 2. Representative materials (Figs. 17, 18)

| name | dH_kJmol | dS_JmolK | Pdes_bar_25C | T_C_at_1bar | T_C_at_10bar | heat_MJ_per_kgH2 | heat_pct_of_LHV | heat_kJ_per_kg_material_full_charge | hysteresis_ratio_Pa_Pd_25C | abs_source |
|---|---|---|---|---|---|---|---|---|---|---|
| LaNi5 | 32.2 | 113 | 1.84 | 11.6 | 69.7 | 15.9 | 13.3 | 238 | 1.3 | stated_abs_dH_dS |
| MmNi4.5Al0.5 | 30.5 | 107 | 1.83 | 11.1 | 72.8 | 15.1 | 12.6 | 182 | 1.6 | stated_abs_dH_dS |
| CaNi5 | 29.7 | 92.9 | 0.449 | 46.3 | 129 | 14.7 | 12.3 | 170 | 1.6 | stated_hysteresis_const |
| TiFe | 28.1 | 106 | 4.16 | -8.3 | 50 | 13.9 | 11.6 | 259 | 1.9 | stated_hysteresis_const |
| TiFe0.9Mn0.1 | 27.6 | 100 | 2.58 | 1.6 | 66.2 | 13.7 | 11.4 | 260 | 2.3 | stated_abs_dH_dS |
| TiCrMn (Ti1.01Cr1.06Mn) | 21.8 | 112 | 108 | -78.5 | -38.4 | 10.8 | 9 | 195 | 2.1 | stated_abs_dH_dS |
| Hydralloy C2 (Ti-Mn-V-Fe AB2) | 30 | 121 | 11.8 | -25.4 | 21.1 | 14.9 | 12.4 | 238 | 1.7 | stated_abs_dH_dS |
| TiMn1.5 | 28.7 | 114 | 8.56 | -21.6 | 29.1 | 14.2 | 11.9 | 265 | 2.5 | stated_hysteresis_const |
| ZrMn2 | 53.2 | 121 | 0.00101 | 166 | 249 | 26.4 | 22 | 467 | 2.7 | stated_hysteresis_const |
| V0.855Ti0.095Fe0.05 (BCC SS) | 43.2 | 140 | 0.562 | 35.2 | 84 | 21.4 | 17.9 | 793 | 2.2 | stated_hysteresis_const |
| Mg2Ni | 64.5 | 122 | 1.2e-05 | 255 | 353 | 32 | 26.7 | 1.15e+03 | nan | not_available |
| MgH2 | 78.3 | 136 | 2.5e-07 | 302 | 396 | 38.8 | 32.4 | 2.95e+03 | 40.7 | stated_abs_dH_dS |
| NaAlH4: Na3AlH6→NaH step (low-H plateau) | 47 | 126 | 0.0225 | 99.5 | 166 | 23.3 | 19.4 | 909 | nan | not_available |
| NaAlH4: NaAlH4→Na3AlH6 step (high-H plateau) | 37 | 122 | 0.787 | 29.9 | 86.2 | 18.4 | 15.3 | 716 | nan | not_available |

`heat_kJ_per_kg_material_full_charge` uses the reported capacity, whose definition varies (Phase 1). The
absorption pressure comes from stated absorption ΔH/ΔS, or from a stated hysteresis ln(Pa/Pd) assumed to be
independent of T. Without either it is not computed: the toolbox's type-default hysteresis is not used.

Reading the table:
* **LaNi5, MmNi4.5Al0.5, TiFe, TiFe0.9Mn0.1** give 1–10 bar between about −10 and 75 °C, and need about 14–16 MJ/kg H2
  (11–13% of LHV). PEMFC waste heat can supply this.
* **TiCrMn and Hydralloy C2** (AB2 Laves) are high-pressure alloys, about 12–108 bar at 25 °C. They suit
  low-temperature operation or compressor stages, and a pressure-rated vessel.
* **ZrMn2 and V-based BCC** need 35–170 °C.
* **NaAlH4:** the NaAlH4 → Na3AlH6 plateau (37 kJ/mol) reaches 1 bar near 30 °C. The
  Na3AlH6 → NaH plateau (47 kJ/mol) needs about 100 °C. Full use of the 3.9 wt% reported capacity therefore needs about
  100 °C or more.
* **Mg2Ni and MgH2** need 255–300 °C and remove/supply 32–39 MJ/kg H2, i.e. 27–32% of the LHV.

## 3. Whole-database view (Fig. 19)

Single-plateau Purdue materials with typical ΔS (n = 318):

| criterion (single-plateau, typical ΔS) | materials |
|---|---|
| T(1 bar) ≤ 25 °C (ambient desorption) | 168 (53%) |
| T(1 bar) ≤ 80 °C (PEMFC waste heat suffices) | 271 (85%) |
| Peq(25 °C) ≤ 10 bar (low-pressure storage at room T) | 263 (83%) |
| Peq(50 °C) ≤ 30 bar (no overpressure on a hot day) | 270 (85%) |
| 1 ≤ Peq(25 °C) ≤ 10 bar | 113 (36%) |
| T(1 bar) > 150 °C (needs a high-temperature heat source) | 7 (2%) |

Reaction heat by operating-temperature class:

| group | n | median_heat_MJ_per_kgH2 | median_pct_LHV |
|---|---|---|---|
| T(1 bar) > 80 °C | 47 | 22.4 | 18.7 |
| T(1 bar) ≤ 80 °C | 271 | 15.1 | 12.6 |

Because T(1 bar) ≈ ΔH/ΔS and ΔS varies little, **heat demand and operating temperature are tied
together**. Among materials that release H2 at 1 bar with low-grade (≤ 80 °C) heat, 95% have
ΔH ≤ 41.9 kJ/mol and a reaction heat ≤ 20.8 MJ/kg H2. The few exceptions, up to 50 kJ/mol, combine a high ΔH
with an unusually high ΔS. Mg-based hydrides need 32–39 MJ/kg H2 at about 255–300 °C.

## 4. Hysteresis

| abs_source | count | min | 50% | max |
|---|---|---|---|---|
| stated_abs_dH_dS | 82 | 1 | 1.73 | 40.7 |
| stated_hysteresis_const | 41 | 1.01 | 1.34 | 5.21 |

* Pabs ≥ Pdes for every material with stated absorption data, so no inconsistent record was found.
* Largest ratios at 25 °C: Mg[1] (40.68), Ti[1]Mn[2] (11.5), Nb[0.95]Cr[0.05] (9.13). For MgH2
  this is an extrapolation of the absorption and desorption lines far below the about 300 °C where they were
  measured. It is not a physical statement about MgH2 at room temperature.
* When absorption and desorption ΔH/ΔS are both stated, the two Van't Hoff lines cross at a median of
  499 K (IQR 429–597). Above this temperature hysteresis vanishes. This is how the toolbox defines its
  critical temperature Tc (`ReadThermo.m`).
* Engineering effect: the charging pressure must exceed Pabs, not Pdes. For TiFe this is about 1.9× the
  desorption pressure, which raises compressor work.

## 5. Plateau slope

Slopes are stated in 103 files. With the toolbox model ln P(x) = ln P_mid + slope·(298/T)·(x − 0.5),
the pressure ratio between 90% and 10% of capacity at 25 °C has median 1.75 (IQR 1.33–2.76,
max 24.5). A sloped AB2 alloy therefore delivers its last hydrogen at a pressure several times lower
than its first, so a window computed from the plateau midpoint is optimistic at low state of charge.

## 6. ML-estimated windows (Fig. 20): ESTIMATES, not validated

Four substitution series were evaluated: LaNi5−xAlx, LaNi5−xSnx, TiFe1−xMnx and TiCr2−xMnx. For compositions already in the data,
the **out-of-fold** prediction is shown, so the model never saw that composition. For new compositions the
final model is used.

* ΔS is not predicted. It is **assumed** to be the family median of experimental Purdue values (IQR shown).
* ΔH interval: the 10–90% quantiles of out-of-fold residuals for training compositions at a similar
  nearest-neighbour distance (calibration below). Applicability domain: nearest-neighbour L1 ≤ 0.15.

Calibration of error vs distance to the nearest training composition outside the same CV group:

| bin | n | MAE | median_abs | res_q10 | res_q90 |
|---|---|---|---|---|---|
| (0.0, 0.05] | 219 | 2.62 | 1.53 | -2.95 | 4.34 |
| (0.05, 0.1] | 220 | 4.22 | 2.8 | -5.76 | 6.36 |
| (0.1, 0.15] | 94 | 4.63 | 3.41 | -7.04 | 7.23 |
| (0.15, 0.2] | 86 | 6.14 | 4.44 | -7.81 | 10.7 |
| (0.2, 0.3] | 27 | 6.88 | 5.41 | -13.8 | 5.67 |
| (0.3, 0.5] | 57 | 12.9 | 5.82 | -32.2 | 8.28 |
| (0.5, 2.0] | 22 | 16.9 | 9.16 | -22.3 | 23.7 |

Check on the 22 series compositions that do have data: mean |out-of-fold − experimental| =
1.91 kJ/mol, and 91% of
experimental values fall inside the nominal 80% interval.

| series | x | in_data | dH_experimental | dH_predicted | dH_interval_low | dH_interval_high | T1bar_C_estimate | T1bar_C_band_low | T1bar_C_band_high | nn_L1_distance | in_applicability_domain |
|---|---|---|---|---|---|---|---|---|---|---|---|
| LaNi5-xAlx (AB5) | 0 | True | 32.2 | 29.4 | 25 | 32.3 | -9.4 | -63.2 | 35.2 | 0 | True |
| LaNi5-xAlx (AB5) | 0.1 | True | 30.3 | 32.2 | 27.8 | 35.1 | 15.6 | -39.9 | 61.7 | 0 | True |
| LaNi5-xAlx (AB5) | 0.2 | True | 30.4 | 34.2 | 29.9 | 37.2 | 34.4 | -22.3 | 81.7 | 0 | True |
| LaNi5-xAlx (AB5) | 0.3 | True | 28.5 | 36.1 | 29.7 | 41.8 | 50.8 | -24 | 126 | 0.1 | True |
| LaNi5-xAlx (AB5) | 0.4 | True | 35.8 | 37.2 | 32.9 | 40.2 | 61 | 2.5 | 110 | 0 | True |
| LaNi5-xAlx (AB5) | 0.5 | True | 37.5 | 37.3 | 32.9 | 40.2 | 61.6 | 3 | 111 | 0 | True |
| LaNi5-xAlx (AB5) | 0.6 | False | nan | 37.7 | 33.4 | 40.7 | 65.9 | 7 | 115 | 0 | True |
| LaNi5-xAlx (AB5) | 0.7 | False | nan | 38.6 | 34.3 | 41.6 | 73.5 | 14.2 | 123 | 0 | True |
| LaNi5-xAlx (AB5) | 0.8 | False | nan | 38.7 | 34.3 | 41.6 | 74.3 | 14.9 | 124 | 0 | True |
| LaNi5-xAlx (AB5) | 0.9 | False | nan | 40.5 | 36.2 | 43.5 | 90.7 | 30.2 | 142 | 0 | True |
| LaNi5-xAlx (AB5) | 1 | False | nan | 40.6 | 36.3 | 43.6 | 91.7 | 31.2 | 142 | 0 | True |
| LaNi5-xSnx (AB5) | 0 | True | 32.2 | 29.4 | 25 | 32.3 | -9.4 | -63.2 | 35.2 | 0 | True |
| LaNi5-xSnx (AB5) | 0 | True | 32 | 33 | 28.7 | 36 | 23.6 | -32.4 | 70.2 | 0 | True |
| LaNi5-xSnx (AB5) | 0.1 | True | 32.8 | 33.7 | 29.3 | 36.6 | 29.3 | -27.1 | 76.3 | 0 | True |
| LaNi5-xSnx (AB5) | 0.2 | False | nan | 33 | 28.7 | 36 | 23.4 | -32.6 | 70 | 0 | True |
| LaNi5-xSnx (AB5) | 0.2 | True | 34.6 | 33.3 | 28.9 | 36.2 | 25.8 | -30.4 | 72.5 | 0 | True |
| LaNi5-xSnx (AB5) | 0.2 | True | 34.8 | 35.1 | 30.7 | 38 | 41.6 | -15.6 | 89.4 | 0 | True |
| LaNi5-xSnx (AB5) | 0.3 | True | 36.5 | 35.9 | 31.5 | 38.8 | 49.1 | -8.6 | 97.3 | 0 | True |
| LaNi5-xSnx (AB5) | 0.4 | False | nan | 37.7 | 33.3 | 40.6 | 65.2 | 6.4 | 114 | 0 | True |
| LaNi5-xSnx (AB5) | 0.4 | True | 40 | 37.1 | 32.8 | 40.1 | 60.1 | 1.6 | 109 | 0 | True |
| LaNi5-xSnx (AB5) | 0.4 | False | nan | 39.1 | 34.8 | 42.1 | 78.2 | 18.6 | 128 | 0 | True |
| LaNi5-xSnx (AB5) | 0.5 | True | 40.6 | 36.9 | 32.5 | 39.8 | 58 | -0.3 | 107 | 0 | True |
| TiFe1-xMnx (AB) | 0 | True | 28.1 | 30.1 | 23.7 | 35.8 | 2.9 | -73.2 | 64.4 | 0.1 | True |
| TiFe1-xMnx (AB) | 0 | True | 29.3 | 28.8 | 24.5 | 31.8 | -8.6 | -66.7 | 26.2 | 0 | True |
| TiFe1-xMnx (AB) | 0.1 | True | 27.6 | 30.3 | 25.9 | 33.2 | 4.9 | -54.2 | 40.1 | 0 | True |
| TiFe1-xMnx (AB) | 0.2 | True | 29.5 | 30.5 | 26.1 | 33.4 | 6.5 | -52.8 | 41.7 | 0 | True |
| TiFe1-xMnx (AB) | 0.2 | True | 31.8 | 30.8 | 26.5 | 33.8 | 9.8 | -49.7 | 45.1 | 0 | True |
| TiFe1-xMnx (AB) | 0.2 | False | nan | 32 | 25.7 | 37.8 | 21.1 | -56.4 | 83.1 | 0.1 | True |
| TiFe1-xMnx (AB) | 0.3 | False | nan | 32.7 | 26.3 | 38.4 | 26.6 | -51.3 | 88.8 | 0.1 | True |
| TiCr2-xMnx (AB2) | 0 | True | 23 | 23.5 | 19.1 | 26.4 | -59.5 | -109 | -15.6 | 0 | True |
| TiCr2-xMnx (AB2) | 0.1 | False | nan | 22.1 | 15.7 | 27.8 | -72.2 | -138 | -1.8 | 0.1 | True |
| TiCr2-xMnx (AB2) | 0.2 | False | nan | 22.7 | 16.3 | 28.4 | -66.7 | -133 | 4 | 0.1 | True |
| TiCr2-xMnx (AB2) | 0.3 | False | nan | 23.1 | 16.7 | 28.8 | -63 | -130 | 8 | 0.1 | True |
| TiCr2-xMnx (AB2) | 0.4 | False | nan | 22.6 | 18.3 | 25.6 | -67.2 | -116 | -23.8 | 0 | True |
| TiCr2-xMnx (AB2) | 0.5 | True | 21.4 | 22.4 | 18.1 | 25.4 | -68.9 | -118 | -25.7 | 0 | True |
| TiCr2-xMnx (AB2) | 0.6 | False | nan | 21.7 | 15.4 | 27.5 | -75.3 | -141 | -5.1 | 0.1 | True |
| TiCr2-xMnx (AB2) | 0.7 | False | nan | 21.1 | 16.8 | 24.1 | -80.9 | -129 | -38.5 | 0 | True |
| TiCr2-xMnx (AB2) | 0.8 | False | nan | 21.2 | 16.8 | 24.1 | -80.3 | -129 | -37.9 | 0 | True |
| TiCr2-xMnx (AB2) | 0.9 | False | nan | 21.4 | 17.1 | 24.4 | -78 | -126 | -35.4 | 0 | True |
| TiCr2-xMnx (AB2) | 1 | True | 19.6 | 21.9 | 17.5 | 24.8 | -74 | -123 | -31.1 | 0 | True |

* The model reproduces the known trends: Al and Sn substitution in LaNi5 stabilise the hydride (ΔH rises), and
  Mn in TiCr2 lowers ΔH slightly.
* The resulting T(1 bar) bands are **about 105 K wide**. Of this, about
  65 K comes from the ΔH uncertainty and 35 K from the assumed ΔS. Even for well-sampled AB5 alloys, an ML
  estimate can only rank candidates ("more stable than LaNi5"). Only a PCT measurement, which gives ΔH
  and ΔS directly, can fix the operating window.
* All 18 new compositions are inside the applicability domain (max NN distance 0.09), because
  the series were chosen near existing data. Compositions far from the data would get much wider intervals.
