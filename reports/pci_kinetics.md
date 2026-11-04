# Phase 7: PCI isotherms and kinetics

Code: `src/thermodynamics/pci_kinetics.py`, `src/thermodynamics/pci_report.py`, `src/visualization/pci_plots.py`
(Figs. 21–23). Tables: `results/tables/pci_*.csv` and `kinetics_purdue.csv`.

## 1. What the PCI files are

* 68 files, 311 curves (126 absorption, 185 desorption) and 5306 points in total.
* **All 68 are digitised from published figures** (field `Location` = "Figure N"). **14 were shifted
  along the composition axis** by the curator to remove an irreversible part. Absolute capacities in these
  curves are therefore *reversible-portion* capacities under the authors' conditions, not total uptake.
* Composition is in mass% H. Pressure is in bar. 6 curves (file
  `La[1]Ni[4.61]Mn[0.26]Al[0.13]_PCI.csv`) only say "eq. pressure"; they are read as bar, as `ReadPCIData.m` does, and flagged.
* Digitisation error was not quantified by the curators. Treat points as ±a few % in P and ±0.02–0.05 wt%.

## 2. Representative materials (Fig. 21)

| material | source | curves (abs/des) | T range (K) | max wt% in curves | median plateau slope dlnP/dx | curator-shifted |
|---|---|---|---|---|---|---|
| LaNi5 (AB5) | Luo, Figure 2 | 5/5 | 248–323 | 1.47 | -0.01 | False |
| TiFe0.8Ni0.15V0.05 (AB) | Oguro, Figure 2 | 2/2 | 393–423 | 1.24 | 0.75 | True |
| Ti0.95Zr0.05Mn1.55V0.45Fe0.09 (AB2) | Herbrig, Figure 4a | 5/5 | 273.15–373.15 | 1.92 | 1.13 | False |
| MgNi0.02 (Mg) | Kapischke, Figure 4 | 5/0 | 547–653 | 7.5 | 0.51 | False |
| NaAlH4 + 4 mol% Ti (complex) | Streukens, Figure 1 4 mol % Ti | 1/1 | 433–433 | 4.1 | 4.58 | False |

* **LaNi5** shows the textbook behaviour: a flat plateau over about 0.2–1.3 wt% and small hysteresis. The desorption plateau rises
  3.2× from 273 to 298 K in the curves, against 3.3× from the .mh ΔH, ΔS.
* **TiFe0.8Ni0.15V0.05** (AB): a sloped plateau at 393–423 K. Substitution in TiFe is commonly used to tune the plateau and
  ease activation (Sandrock 1999).
* **Ti–Zr–Mn–V–Fe AB2** (Hydralloy-type): the largest capacity of the three intermetallics shown (about 1.9 wt%), a
  strongly sloped plateau, and clear hysteresis.
* **MgNi0.02** (absorption only): about 7 wt% but only at 547–653 K.
* **NaAlH4 + Ti**: two plateaus in one isotherm. They are a direct check of the Phase 6 plateau assignment:

| plateau | dH_kJmol | dS_JmolK | T_K | P_curve_bar | P_vant_hoff_bar |
|---|---|---|---|---|---|
| low-H (Na3AlH6 → NaH) | 47 | 126 | 433 | 6.1 | 8.27 |
| high-H (NaAlH4 → Na3AlH6) | 37 | 122 | 433 | 77.8 | 82.2 |

  The low-H plateau corresponds to the 47 kJ/mol step (Na3AlH6 → NaH): curve/Van't Hoff = 0.74. The high-H plateau
  corresponds to the 37 kJ/mol step (NaAlH4 → Na3AlH6): ratio 0.95. The reverse assignment would be off by a factor of about 10,
  so this confirms the relabelling made in Phase 6.

## 3. Plateau extraction and Van't Hoff check (Fig. 22)

Plateau = exp(median ln P) over 0.2 ≤ w/w_max ≤ 0.8, with at least 4 points. It was extracted for 228 of 311 curves;
the rest have too few points in the window. Median plateau slope d ln P / d(w/w_max): absorption
0.99, desorption 1.81.

A Van't Hoff fit was made for each material and mode with at least 3 temperatures: 49 fits (34 single-plateau
with a tabulated reference value).

* **Single-plateau:** median |ΔH_PCI − ΔH_.mh| = 1.76 kJ/mol. 53% are within 2 kJ/mol.
* **This is a consistency check, not independent validation.** For 32 of the desorption fits, the `.mh` value is flagged
  `From Isotherms: true`: the toolbox authors fitted it to these same curves, using their sloped-plateau model.
* The size of the disagreement is not explained by temperature spans (Spearman ρ(|ΔΔH|, ΔT span) = 0.29).
  The largest deviations are mostly strongly sloped AB2/AB plateaus. There, the fixed 0.2–0.8 window and the toolbox's
  sloped-plateau fit pick different "plateau" pressures:

| material_id | mode | dH_fit_kJmol | dH_mh_kJmol | d_dH | n_T | T_range_K | R2_fit |
|---|---|---|---|---|---|---|---|
| Ti[0.56]V[0.3]Zr[0.1]Mn[0.94]Fe[0.06]Ni[0.04] | abs | 12.5 | 26.6 | -14.1 | 3 | 363-423 | 1 |
| Zr[0.5]Ti[0.5]Cr[1]Fe[1] | des | 13.6 | 26.3 | -12.7 | 4 | 273-373 | 0.95 |
| Ti[0.56]V[0.3]Zr[0.1]Mn[0.94]Fe[0.06]Ni[0.04] | des | 17.1 | 27.9 | -10.8 | 3 | 323-423 | 0.99 |
| Ti[1]Mn[1.4] | abs | 12.2 | 22.2 | -10 | 3 | 273-333 | 0.92 |

* **Multi-plateau** materials (10 fits) disagree strongly, as expected: a single "mid-curve" pressure mixes plateaus.
  They are excluded from conclusions.

## 4. Hysteresis from PCI curves

ln(Pa/Pd) at the same temperature, from abs/des pairs (51 pairs):

| family | n_pairs | median | min | max | n_materials | toolbox_type_default |
|---|---|---|---|---|---|---|
| AB | 6 | 0.09 | 0.03 | 0.16 | 3 | 0.51 |
| AB2 | 23 | 0.25 | 0.01 | 1.24 | 8 | 0.54 |
| AB3 | 4 | 0.93 | 0.56 | 1.19 | 1 | 0.29 |
| AB5 | 13 | 0.33 | 0.11 | 0.62 | 7 | 0.39 |
| Complex | 1 | 0.09 | 0.09 | 0.09 | 1 | nan |
| SS | 4 | 1.32 | 1.11 | 1.92 | 2 | 0.8 |

The toolbox's **type-default** hysteresis values (`GetTypeProperty.m`, used when a file states none) differ from the
curve-derived medians, by up to several times for AB, AB3 and SS. The samples are small (often 1–3 materials per
family), so the medians are indicative only. This supports the decision not to use the defaults.
Physically, hysteresis is a loss: it raises the charging pressure (compressor work) or the temperature
swing needed per cycle.

## 5. Kinetics

31 absorption and 26 desorption records, giving the rate law
dw/dt = Ca·exp(−Ea/RT)·f_p(P, Peq)·f_w(w). The type-default kinetics the toolbox would substitute are not included.

**Comparable group** (f_p = ln(P/Peq), first order in w; 47 records). Activation energies:

| family | mode | n | min | median | max |
|---|---|---|---|---|---|
| AB | abs | 1 | 27.8 | 27.8 | 27.8 |
| AB | des | 1 | 23.1 | 23.1 | 23.1 |
| AB2 | abs | 9 | 20 | 23.8 | 31.9 |
| AB2 | des | 6 | 20 | 22.1 | 29 |
| AB3 | abs | 1 | 25.7 | 25.7 | 25.7 |
| AB5 | abs | 15 | 8.4 | 31.2 | 40 |
| AB5 | des | 14 | 7.2 | 27.5 | 33.3 |

**Not comparable**: other rate-law forms, which make Ca carry different units:

| material_id | mode | Ea_kJmol | pFcn | wFcn |
|---|---|---|---|---|
| La[1]Ni[4.1]Al[0.52]Mn[0.38] | des | 48 | linear | 1st Order |
| La[1]Ni[4.7]Al[0.3] | abs | 30 | linear | 1st Order |
| La[1]Ni[4.7]Al[0.3] | des | 30 | linear | 1st Order |
| Mg[1] | abs | 132 | (p-peq)/peq | ((w-wmax)/(2*log(1-max([1e-6 w])/wmax))) |
| Mg[1] | des | 41 | log(p/peq) | w/sqrt(-log(max([1e-6 w])/wmax)) |
| Na[1]Al[1]H[1] | abs | 91.5 | (p-peq)/peq | (wmax-w)*((tanh(5000*(w-0.017))+1)*0.5*0 |
| Na[1]Al[1]H[1] | des | 93.1 | (p-peq)/peq | w*((tanh(5000*(w-0.017))+1)*0.5*0.9+0.1) |
| Ti[0.95]Zr[0.05]Mn[1.55]V[0.45]Fe[0.09] | abs | 40 | Normalized Linear | 1st Order |
| Ti[1]Fe[0.8]Ni[0.2] | abs | 52.3 | (p-peq)/peq | 1st Order |
| Ti[1]Fe[0.8]Ni[0.2] | des | 37.2 | (p-peq)/peq | 1st Order |

* Absorption activation energies: median 31 kJ/mol (AB5) and 24 kJ/mol (AB2),
  against 92 kJ/mol for Ti-doped NaAlH4 and 132 kJ/mol for MgH2. For absorption the ordering
  intermetallics ≪ complex < Mg is consistent with Mg and complex hydrides being kinetically limited. (The MgH2
  *desorption* record, 41 kJ/mol, uses a different rate-law form, so its Ea is not directly comparable.)
* The model t90 at 25 °C spans **7 orders of magnitude**
  (0.0085–6.7e+04 s) within the comparable group. Even for one family, the fitted Ca
  depends on the test reactor, particle size, activation and heat-transfer limitation of each study. Several records carry notes
  such as "data assumed" (2) or "conflicts with Satheesh B" (2).
* **Conclusion:** the kinetic records are suitable for qualitative family comparison (Ea ranges) only. They are **not**
  used to rank individual materials in Phase 8. Kinetics enters the screening as a family-level qualitative criterion.
