# Thermodynamic Analysis

## Method and a worked example

All operating windows in Sections 5.2–5.5 use the experimental ΔH and ΔS from the Purdue files. Predicted values appear only in Section 5.6, where they are labelled as estimates. The calculations use @eq:vh with P₀ = 1 atm, the convention of both datasets, and R = 8.314462618 J mol⁻¹ K⁻¹. Pressures are converted to bar, the temperature at a pressure follows from @eq:tp, and the heat from @eq:q, expressed also as a fraction of the lower heating value of hydrogen (119.96 MJ kg⁻¹).

For LaNi₅ (ΔH = 32.15 kJ mol⁻¹, ΔS = 112.8 J mol⁻¹ K⁻¹) at 298.15 K,

EQ lani5 | ln(P~eq~ / atm) = − 32 151 / (8.314 × 298.15) + 112.8 / 8.314 = 0.597,

so P~eq~ = 1.817 atm = 1.84 bar. The pressure reaches 1 bar at 11.6 °C, and desorption needs 32.15 / 2.01588 = 15.95 MJ per kg of H₂, which is 13.3% of the LHV. The same amount of heat is released on absorption and has to be removed during refuelling.

## Representative materials

@tab:representative and @fig:vhlines show the results for fourteen representative materials and reaction steps.

TAB representative | Van't Hoff results for representative materials (experimental Purdue ΔH and ΔS, desorption)
| Material | ΔH (kJ mol⁻¹) | ΔS (J mol⁻¹ K⁻¹) | P(25 °C) (bar) | T(1 bar) (°C) | T(10 bar) (°C) | Q (MJ kg⁻¹ H₂) | Q / LHV (%) |
|---|---|---|---|---|---|---|---|
| LaNi₅ | 32.2 | 113 | 1.84 | 11.6 | 69.7 | 15.9 | 13.3 |
| MmNi₄.₅Al₀.₅ | 30.5 | 107 | 1.83 | 11.1 | 72.8 | 15.1 | 12.6 |
| CaNi₅ | 29.7 | 92.9 | 0.449 | 46.3 | 129 | 14.7 | 12.3 |
| TiFe | 28.1 | 106 | 4.16 | −8.3 | 50.0 | 13.9 | 11.6 |
| TiFe₀.₉Mn₀.₁ | 27.6 | 100 | 2.58 | 1.6 | 66.2 | 13.7 | 11.4 |
| TiCrMn (Ti₁.₀₁Cr₁.₀₆Mn) | 21.8 | 112 | 107.5 | −78.5 | −38.4 | 10.8 | 9.0 |
| Hydralloy C2 (Ti–Mn–V–Fe AB₂) | 30.0 | 121 | 11.8 | −25.4 | 21.1 | 14.9 | 12.4 |
| TiMn₁.₅ | 28.7 | 114 | 8.56 | −21.6 | 29.1 | 14.2 | 11.9 |
| ZrMn₂ | 53.2 | 121 | 0.00101 | 166 | 249 | 26.4 | 22.0 |
| V₀.₈₅₅Ti₀.₀₉₅Fe₀.₀₅ (BCC) | 43.2 | 140 | 0.562 | 35.2 | 84.0 | 21.4 | 17.9 |
| Mg₂Ni | 64.5 | 122 | 1.2 × 10⁻⁵ | 255 | 353 | 32.0 | 26.7 |
| MgH₂ | 78.3 | 136 | 2.5 × 10⁻⁷ | 302 | 396 | 38.8 | 32.4 |
| NaAlH₄, Na₃AlH₆ → NaH step | 47.0 | 126 | 0.0225 | 99.5 | 166 | 23.3 | 19.4 |
| NaAlH₄, NaAlH₄ → Na₃AlH₆ step | 37.0 | 122 | 0.787 | 29.9 | 86.2 | 18.4 | 15.3 |

FIG vhlines | report/figures/existing/fig17_vant_hoff_lines.png | 14 | Van't Hoff lines of the representative materials (bold) over all single-plateau AB₅, AB₂, AB and SS Purdue materials (faint, coloured by family). The green band marks 1–10 bar and the red band PEM fuel-cell waste-heat temperatures.

The materials fall into four groups. LaNi₅, MmNi₄.₅Al₀.₅, TiFe and TiFe₀.₉Mn₀.₁ deliver 1–10 bar between about −10 and 75 °C and need 14–16 MJ kg⁻¹ H₂ (11–13% of the LHV), which PEM fuel-cell waste heat can supply. TiCrMn and Hydralloy C2 are high-pressure alloys (about 12–108 bar at 25 °C); they suit low-temperature operation or compressor stages and need a pressure-rated vessel. ZrMn₂ and the V-based BCC alloy need 35–170 °C. Mg₂Ni and MgH₂ need 255–300 °C and 32–39 MJ kg⁻¹ H₂, which is 27–32% of the energy content of the stored hydrogen. NaAlH₄ is discussed in Section 5.5.

## Whole-database view

@tab:windows applies the same calculation to the 318 single-plateau Purdue materials with a typical ΔS. Most of them operate close to ambient conditions: 85% reach 1 bar at or below 80 °C, and 83% stay at or below 10 bar at 25 °C. Only 7 (2%) need more than 150 °C.

TAB windows | Operating criteria met by the 318 single-plateau Purdue materials with typical ΔS
| Criterion | Materials | Share |
|---|---|---|
| T(1 bar) ≤ 25 °C (desorption at ambient temperature) | 168 | 53% |
| T(1 bar) ≤ 80 °C (PEMFC waste heat suffices) | 271 | 85% |
| P(25 °C) ≤ 10 bar | 263 | 83% |
| P(50 °C) ≤ 30 bar | 270 | 85% |
| 1 ≤ P(25 °C) ≤ 10 bar | 113 | 36% |
| T(1 bar) > 150 °C | 7 | 2% |

Because T(1 bar) ≈ ΔH/ΔS and ΔS varies little, heat demand and operating temperature are tied together (@fig:heat). Among materials that release hydrogen at 1 bar with heat at 80 °C or below, the median reaction heat is 15.1 MJ kg⁻¹ H₂ (12.6% of the LHV), and 95% have ΔH ≤ 41.9 kJ mol⁻¹ and Q ≤ 20.8 MJ kg⁻¹. Materials that need more than 80 °C have a median of 22.4 MJ kg⁻¹ (18.7%). The few exceptions, with ΔH up to 50 kJ mol⁻¹, combine high ΔH with an unusually high ΔS. Low-temperature operation and low heat demand therefore come together, but so do low stability and, for these intermetallics, low capacity.

FIG heat | report/figures/existing/fig19_heat_vs_temperature.png | 13 | Reaction heat against the temperature for 1 bar desorption pressure for all Purdue plateaus. Circles mark atypical ΔS; stars mark the two NaAlH₄ plateaus.

## Hysteresis and plateau slope

Absorption data are stated for 82 materials, and 41 more state a constant hysteresis. In all of them P~abs~ ≥ P~des~, so no inconsistent record was found. The median ratio P~abs~/P~des~ at 25 °C is 1.73 for materials with absorption ΔH and ΔS, and 1.34 for those with a stated constant. For TiFe the charging pressure is about 1.9 times the desorption pressure, which raises compressor work. The largest ratio, 40.7 for MgH₂, is an extrapolation of lines measured near 300 °C, not a statement about MgH₂ at room temperature. Where both absorption and desorption lines are given, they cross at a median of 499 K (interquartile range 429–597 K); above this temperature the hysteresis vanishes.

Plateau slopes are stated in 103 files. With the toolbox's model, ln P(x) = ln P~mid~ + slope · (298/T) · (x − 0.5), the pressure at 10% of the capacity is a median of 1.75 times lower than at 90% (interquartile range 1.33–2.76, maximum 24.5). A sloped AB₂ alloy thus delivers its last hydrogen at a pressure several times lower than its first.

## Consistency with the digitised isotherms

The 68 PCI files contain 311 curves (126 absorption, 185 desorption; 5306 points). @fig:pci shows five representative materials. LaNi₅ shows a flat plateau and small hysteresis; its desorption plateau rises by a factor of 3.2 between 273 and 298 K in the digitised curves, against 3.3 from the tabulated ΔH and ΔS. The Ti–Zr–Mn–V–Fe AB₂ alloy has the highest capacity of the intermetallics shown (about 1.9 wt%), a strongly sloped plateau and clear hysteresis. MgNi₀.₀₂ reaches about 7 wt%, but only at 547–653 K.

FIG pci | report/figures/existing/fig21_pci_isotherms.png | 16 | Digitised pressure–composition isotherms of five representative hydrides (data from the Purdue PCI files; diamonds mark the extracted plateau pressures).

The Ti-doped NaAlH₄ isotherm at 433 K shows two plateaus in one curve. It is a direct check of which tabulated step belongs to which plateau. The low-hydrogen plateau (6.1 bar in the curve) matches the 47 kJ mol⁻¹ step, Na₃AlH₆ → NaH, which predicts 8.27 bar (ratio 0.74). The high-hydrogen plateau (77.8 bar) matches the 37 kJ mol⁻¹ step, NaAlH₄ → Na₃AlH₆, which predicts 82.2 bar (ratio 0.95). The reverse assignment would be wrong by a factor of about ten. The practical result is that only the first step releases hydrogen near 30 °C; using all of the reported 3.9 wt% requires about 100 °C.

Plateau pressures were extracted from 228 curves as the median pressure between 20% and 80% of the maximum hydrogen content, and Van't Hoff lines were fitted for each material and mode with at least three temperatures. For the 34 single-plateau fits with a tabulated value, the median absolute difference from the .mh ΔH is 1.76 kJ mol⁻¹, and 53% agree within 2 kJ mol⁻¹. This is a consistency check, not an independent validation: for 32 of the desorption fits, the toolbox authors had derived the tabulated value from these same curves. The largest differences, up to 14 kJ mol⁻¹, occur for strongly sloped AB₂ and AB plateaus, where the fixed 20–80% window and the toolbox's sloped-plateau fit pick different pressures.

## Estimates for new compositions

For compositions without experimental data, an operating window can only be estimated. ΔH is the model prediction with its calibrated 80% interval, and ΔS is *assumed* to be the median experimental value of the family. @fig:mlseries shows such estimates for four substitution series: LaNi₅₋ₓAlₓ, LaNi₅₋ₓSnₓ, TiFe₁₋ₓMnₓ and TiCr₂₋ₓMnₓ. For compositions already in the data, the out-of-fold prediction is shown, so the model never saw that composition.

FIG mlseries | report/figures/existing/fig20_ml_estimated_series.png | 16 | Estimated (not validated) ΔH and T(1 bar) along four substitution series. Top: predicted ΔH with the 80% interval (band) and experimental values (crosses). Bottom: the implied temperature for 1 bar, using the assumed family-median ΔS; the band combines the ΔH interval with the interquartile range of ΔS.

The model reproduces the known trends. Al and Sn substitution in LaNi₅ stabilise the hydride, and Mn in TiCr₂ lowers ΔH slightly. All 18 new compositions lie inside the applicability domain (largest d~NN~ 0.09), because the series were chosen close to existing data. The resulting bands of T(1 bar) are about 105 K wide; about 65 K comes from the ΔH interval and about 35 K from the assumed ΔS. For LaNi₄.₂Al₀.₈, for example, the prediction is ΔH = 38.7 kJ mol⁻¹ (80% interval 34.3–41.6), and the estimated T(1 bar) is 74 °C, with a band of 15–124 °C. An ML estimate can therefore rank candidates, for example "more stable than LaNi₅", but fixing an operating window needs a PCT measurement, which gives ΔH and ΔS directly.

## Kinetics

The Purdue files contain 31 absorption and 26 desorption kinetic records. For the 47 records that use the same rate law, the median absorption activation energies are 31 kJ mol⁻¹ for AB₅ and 24 kJ mol⁻¹ for AB₂, against 92 kJ mol⁻¹ for Ti-doped NaAlH₄ and 132 kJ mol⁻¹ for MgH₂. This ordering agrees with Mg-based and complex hydrides being kinetically limited [@huot1999; @bogdanovic2000]. However, the modelled time to 90% conversion at 25 °C spans seven orders of magnitude within the comparable group. The fitted pre-factors depend on the test reactor, particle size, activation and heat-transfer conditions of each study. The kinetic data are therefore used only as a qualitative, family-level class in the screening, never to rank individual materials.
