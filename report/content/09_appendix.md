#A Composition Descriptors

The 38 descriptors used by the ΔH model, in the order of the model input (source: `results/tables/feature_list.csv`). Elemental values are from pymatgen; fractions are atomic fractions.

TAB featlist | Descriptors of the ΔH model
| Descriptor | Group | Definition |
|---|---|---|
| mass_mean | elemental statistic | fraction-weighted mean of g/mol |
| mass_std | elemental statistic | fraction-weighted std of g/mol |
| mass_min | elemental statistic | minimum over elements of g/mol |
| mass_max | elemental statistic | maximum over elements of g/mol |
| X_mean | elemental statistic | fraction-weighted mean of Pauling electronegativity |
| X_std | elemental statistic | fraction-weighted std of Pauling electronegativity |
| X_min | elemental statistic | minimum over elements of Pauling electronegativity |
| X_max | elemental statistic | maximum over elements of Pauling electronegativity |
| radius_mean | elemental statistic | fraction-weighted mean of empirical atomic radius, Å |
| radius_min | elemental statistic | minimum over elements of empirical atomic radius, Å |
| radius_max | elemental statistic | maximum over elements of empirical atomic radius, Å |
| Tm_mean | elemental statistic | fraction-weighted mean of K |
| Tm_std | elemental statistic | fraction-weighted std of K |
| Tm_min | elemental statistic | minimum over elements of K |
| Tm_max | elemental statistic | maximum over elements of K |
| vol_mean | elemental statistic | fraction-weighted mean of cm3/mol |
| vol_std | elemental statistic | fraction-weighted std of cm3/mol |
| vol_min | elemental statistic | minimum over elements of cm3/mol |
| vec_mean | elemental statistic | fraction-weighted mean of valence electrons (group convention) |
| vec_std | elemental statistic | fraction-weighted std of valence electrons (group convention) |
| vec_min | elemental statistic | minimum over elements of valence electrons (group convention) |
| vec_max | elemental statistic | maximum over elements of valence electrons (group convention) |
| n_elements | alloy descriptor | number of elements |
| config_entropy | alloy descriptor | ideal configurational entropy, -sum x ln x (units of R) |
| size_mismatch | alloy descriptor | atomic size mismatch delta |
| frac_hydride_former | alloy descriptor | fraction of atoms from stable-hydride-forming elements |
| x_Zr | elemental fraction | atomic fraction of Zr |
| x_Ti | elemental fraction | atomic fraction of Ti |
| x_Mn | elemental fraction | atomic fraction of Mn |
| x_Fe | elemental fraction | atomic fraction of Fe |
| x_Ni | elemental fraction | atomic fraction of Ni |
| x_Cr | elemental fraction | atomic fraction of Cr |
| x_V | elemental fraction | atomic fraction of V |
| x_La | elemental fraction | atomic fraction of La |
| x_Co | elemental fraction | atomic fraction of Co |
| x_Al | elemental fraction | atomic fraction of Al |
| x_Mg | elemental fraction | atomic fraction of Mg |
| x_Cu | elemental fraction | atomic fraction of Cu |

#A Additional Machine-Learning Results

Models trained and tested within one family (nested grouped CV), and the random forest refitted on data subsets (one repeat). Source: `results/metrics/`.

TAB withinfam | Within-family nested grouped cross-validation
| family | model | MAE (kJ mol⁻¹) | R² | n |
|---|---|---|---|---|
| AB5 | FamilyMedianBaseline | 5.18 ± 0.05 | -0.02 | 116 |
| AB5 | MeanBaseline | 5.17 ± 0.05 | -0.02 | 116 |
| AB5 | RandomForest | 3.25 ± 0.02 | 0.51 | 116 |
| AB5 | Ridge | 3.80 ± 0.26 | 0.2 | 116 |
| AB2 | FamilyMedianBaseline | 7.11 ± 0.02 | -0.04 | 401 |
| AB2 | MeanBaseline | 7.38 ± 0.01 | -0.01 | 401 |
| AB2 | RandomForest | 4.23 ± 0.10 | 0.57 | 401 |
| AB2 | Ridge | 4.64 ± 0.08 | 0.61 | 401 |

TAB subsets | Sensitivity of the ΔH error to the data subset
| subset | model | MAE (kJ mol⁻¹) | RMSE (kJ mol⁻¹) | R² | n |
|---|---|---|---|---|---|
| all (union) | FamilyMedianBaseline | 8.82 | 16.19 | 0.3 | 725 |
| all (union) | MeanBaseline | 12.28 | 19.43 | -0.01 | 725 |
| all (union) | RandomForest | 5.24 | 9.97 | 0.73 | 725 |
| Purdue values only | FamilyMedianBaseline | 6.32 | 9.17 | 0.19 | 276 |
| Purdue values only | MeanBaseline | 7.37 | 10.3 | -0.02 | 276 |
| Purdue values only | RandomForest | 4.94 | 7.68 | 0.43 | 276 |
| HydPARK-only compositions | FamilyMedianBaseline | 9.97 | 18.93 | 0.34 | 449 |
| HydPARK-only compositions | MeanBaseline | 15.38 | 23.28 | -0.0 | 449 |
| HydPARK-only compositions | RandomForest | 5.83 | 13.2 | 0.68 | 449 |
| high-confidence (referenced, typical dS, metals only) | FamilyMedianBaseline | 6.42 | 9.15 | 0.22 | 456 |
| high-confidence (referenced, typical dS, metals only) | MeanBaseline | 7.51 | 10.38 | -0.0 | 456 |
| high-confidence (referenced, typical dS, metals only) | RandomForest | 3.51 | 5.33 | 0.74 | 456 |
| dH <= 60 kJ/mol (exclude very stable) | FamilyMedianBaseline | 6.74 | 9.19 | 0.16 | 667 |
| dH <= 60 kJ/mol (exclude very stable) | MeanBaseline | 7.9 | 10.03 | -0.01 | 667 |
| dH <= 60 kJ/mol (exclude very stable) | RandomForest | 4.08 | 5.84 | 0.66 | 667 |

#A Data-Quality Flags

Flags set during the audit (Phase 1–2). Flagged records are kept; the flags decide exclusion from the ΔH union, the screening data-quality gate and the evidence class. Source: `data/processed/*_cleaned.csv`.

TAB flags | Data-quality flags in the cleaned datasets
| Dataset | Flag | Records flagged | Records |
|---|---|---|---|
| Purdue | unverified ref sandia | 102 | 337 |
| Purdue | pseudo element | 49 | 337 |
| Purdue | trade name file | 2 | 337 |
| Purdue | composition approximate | 3 | 337 |
| Purdue | contains H in formula | 1 | 337 |
| Purdue | ambiguous formula | 51 | 337 |
| Purdue | multi plateau | 12 | 337 |
| Purdue | des thermo from isotherm fit | 67 | 337 |
| Purdue | has pci digitized | 68 | 337 |
| Purdue | capacity from HM | 114 | 337 |
| Purdue | capacity uncertain | 17 | 337 |
| Purdue | dS atypical | 7 | 337 |
| Purdue | todo in file | 76 | 337 |
| Purdue | unparseable composition | 49 | 337 |
| HydPARK | dS derived from TP | 395 | 772 |
| HydPARK | dS TP inconsistent | 8 | 772 |
| HydPARK | lnP25 mismatch | 25 | 772 |
| HydPARK | missing reference | 399 | 772 |
| HydPARK | missing class | 25 | 772 |
| HydPARK | missing wt | 31 | 772 |
| HydPARK | zero capacity | 1 | 772 |
| HydPARK | T zero suspect | 16 | 772 |
| HydPARK | dS atypical | 40 | 772 |
| HydPARK | dS negative | 1 | 772 |
| HydPARK | dH very stable | 9 | 772 |
| HydPARK | duplicate formula | 52 | 772 |
| HydPARK | suspected entry error | 4 | 772 |
| HydPARK | chemical duplicate | 127 | 772 |
| HydPARK | excluded by purdue curators | 15 | 772 |

FIG missing | report/figures/existing/fig10_missing_data.png | 16 | Missing-data map of the Purdue (left, sorted by family) and HydPARK (right, file order) records. Percentages give the fraction of records in which the property is present; missing values are shown as missing, not as zero.

#A ML-Generated Candidates of the Demonstration Scenarios

Candidates generated by the Discovery Lab (source: `reports/platform_demo_scenarios.md`). **Proposed compositions, not validated:** ΔH is the ML prediction with its 80% interval, ΔS is the assumed family median, capacity is not predicted. Temperatures are those needed for the scenario's delivery pressure.

TAB lab0 | Generation summary, scenario 1 (mobile)
| alloy system | generated | in domain and in window | rejected | main rejection reason |
|---|---|---|---|---|
| Ti-Cr-Mn (AB2 Laves) | 25 | 24 | 1 | even the pessimistic T(3 bar) -23 °C < -20 °C (plateau too high: needs cooling or a high-pressure vessel) |
| Ti-Zr-Mn-Cr (AB2 Laves) | 189 | 140 | 49 | outside applicability domain (NN L1 0.166 > 0.15) |

TAB labc0 | Top candidates, scenario 1 (mobile); ΔH in kJ mol⁻¹
| Candidate | ΔH pred. | 80% low | 80% high | d~NN~ | T est. (°C) | Nearest known | Its ΔH (exp.) |
|---|---|---|---|---|---|---|---|
| Ti1Cr2 | 23.2 | 18.8 | 26.1 | 0.02 | -43.1 | Cr0.667Ti0.333 | 23 |
| Ti1Cr1.95Mn0.05 | 22.8 | 18.4 | 25.8 | 0.03 | -46.8 | Al0.013Cr0.653Ti0.333 | 22.8 |
| Ti1Cr1.75Mn0.25 | 22.9 | 18.6 | 25.9 | 0.05 | -45.7 | Cr0.572Mn0.071Ti0.357 | 28 |
| Ti1Cr1.55Mn0.45 | 22.5 | 18.2 | 25.5 | 0.03 | -49.5 | Cr0.5Mn0.167Ti0.333 | 21.4 |
| Ti0.75Zr0.25Mn1.5Cr0.5 | 28.4 | 24.1 | 31.4 | 0.03 | 9.43 | Cr0.167Mn0.5Ti0.267Zr0.067 | 27.5 |
| Ti0.75Zr0.25Mn1.2Cr0.8 | 28.3 | 24 | 31.3 | 0.03 | 8.34 | Cr0.267Mn0.4Ti0.267Zr0.067 | 28.9 |
| Ti0.8Zr0.2Mn1.25Cr0.75 | 28.2 | 23.9 | 31.2 | 0.03 | 6.98 | Cr0.267Mn0.4Ti0.267Zr0.067 | 28.9 |
| Ti0.8Zr0.2Mn1.45Cr0.55 | 27.6 | 23.3 | 30.6 | 0.03 | 1.3 | Cr0.167Mn0.5Ti0.267Zr0.067 | 27.5 |

TAB lab1 | Generation summary, scenario 2 (industrial)
| alloy system | generated | in domain and in window | rejected | main rejection reason |
|---|---|---|---|---|
| La-Ce-Ni-Al (AB5) | 143 | 133 | 10 | outside applicability domain (NN L1 0.150 > 0.15) |
| Ti-Fe-Mn (AB, TiFe1-xMnx) | 9 | 8 | 1 | outside applicability domain (NN L1 0.189 > 0.15) |

TAB labc1 | Top candidates, scenario 2 (industrial); ΔH in kJ mol⁻¹
| Candidate | ΔH pred. | 80% low | 80% high | d~NN~ | T est. (°C) | Nearest known | Its ΔH (exp.) |
|---|---|---|---|---|---|---|---|
| La0.95Ce0.05Ni4.5Al0.5 | 36.1 | 31.8 | 39 | 0.02 | 95.2 | Al0.083La0.167Ni0.75 | 37.5 |
| La1Ni4.6Al0.4 | 36 | 31.6 | 38.9 | 0.02 | 94 | Al0.067La0.167Ni0.767 | 35.8 |
| La0.95Ce0.05Ni4.6Al0.4 | 35.5 | 31.1 | 38.4 | 0.02 | 88.7 | Al0.067La0.167Ni0.767 | 35.8 |
| La0.95Ce0.05Ni4.55Al0.45 | 36.1 | 31.8 | 39.1 | 0.03 | 95.7 | Al0.083La0.167Ni0.75 | 37.5 |
| Ti1Fe0.8Mn0.2 | 31.4 | 27.1 | 34.3 | 0.05 | 55.4 | Fe0.4Mn0.1Ti0.5 | 31.8 |
| Ti1Fe0.85Mn0.15 | 29.9 | 25.5 | 32.8 | 0.05 | 39.4 | Fe0.425Mn0.075Ti0.5 | 29.5 |
| Ti1Fe0.95Mn0.05 | 29.1 | 24.7 | 32 | 0.05 | 31.1 | Fe0.475Mn0.025Ti0.5 | 29.3 |
| Ti1Fe0.75Mn0.25 | 32 | 25.7 | 37.8 | 0.05 | 62.3 | Fe0.4Mn0.1Ti0.5 | 31.8 |

#A Scenario Rankings

Top eight experimental materials of each scenario as produced by the Application Requirement Designer (source: `reports/platform_demo_scenarios.md`). Capacities are reported, material-level values; mass is the alloy mass for the scenario's hydrogen quantity.

TAB rank0 | Ranking, scenario 1 (mobile)
| Rank | Material | Family | Evidence | Score | T needed (°C) | wt% | Q (MJ kg⁻¹) | Alloy mass (kg) |
|---|---|---|---|---|---|---|---|---|
| 1 | Ti0.9Zr0.2Mn1.4Cr0.4V0.2 | AB2 | data-supported | 0.64 | 33.1 | 2.1 | 13.2 | 47.6 |
| 2 | Ti0.9Zr0.2Mn1.8V0.2 | AB2 | data-supported | 0.63 | 23.9 | 2.1 | 12.9 | 47.6 |
| 3 | V0.855Ti0.095Fe0.05 | SS | data-supported | 0.62 | 56.7 | 3.7 | 21.4 | 27 |
| 4 | V0.8455Ti0.1045Fe0.05 | SS | data-supported | 0.62 | 35.5 | 3.44 | 21.3 | 29 |
| 5 | TiCrMn0.85Fe0.3V0.15 | AB2 | data-supported | 0.61 | -2.3 | 1.6 | 10.4 | 62.5 |
| 6 | Ti0.9Zr0.2Mn1.4Cr0.4Vf0.2 | AB2 | provisional | 0.61 | 20.7 | 2.1 | 12.6 | 47.6 |
| 7 | Ti0.56V0.3Zr0.1Mn0.94Fe0.06Ni0.04 | AB | provisional | 0.61 | 20 | 2.2 | 13.8 | 45.5 |
| 8 | TiFe0.9Mn0.1 | AB | data-supported | 0.6 | 29.1 | 1.9 | 13.7 | 52.6 |

TAB rank1 | Ranking, scenario 2 (industrial buffer)
| Rank | Material | Family | Evidence | Score | T needed (°C) | wt% | Q (MJ kg⁻¹) | Alloy mass (kg) |
|---|---|---|---|---|---|---|---|---|
| 1 | Ti0.9Zr0.1Mn1.4 | AB2 | data-supported | 0.87 | 69.8 | 1.91 | 17.2 | 2.61e+03 |
| 2 | Zr0.7Ti0.3CrFe | AB2 | data-supported | 0.86 | 74.3 | 1.7 | 14.6 | 2.94e+03 |
| 3 | TiFe0.9Al0.1 | AB | data-supported | 0.85 | 59.6 | 1.3 | 14.9 | 3.85e+03 |
| 4 | TiFe0.8Mn0.2 | AB | data-supported | 0.85 | 73.5 | 1.3 | 15.8 | 3.85e+03 |
| 5 | TiFe0.9Ni0.1 | AB | data-supported | 0.84 | 78.3 | 1.4 | 17.2 | 3.57e+03 |
| 6 | CaNi5 | AB5 | data-supported | 0.81 | 100 | 1.15 | 14.7 | 4.35e+03 |
| 7 | ZrFe0.6Mn1.4 | AB2 | data-supported | 0.79 | 57 | 0.8 | 12.4 | 6.25e+03 |
| 8 | LaNi4.8Sn0.2 | AB5 | data-supported | 0.79 | 91.7 | 1.4 | 17.1 | 3.57e+03 |

#A Proposed Characterisation Matrix

**Proposed future work only; none of these measurements was made in this project.** Source: `results/tables/characterisation_matrix.csv`.

TAB charmatrix | Proposed synthesis and characterisation techniques
| Technique | Families | Property measured | Gap it addresses |
|---|---|---|---|
| Arc melting (Ar, Ti getter, 4–5 remelts with flipping) | AB5, AB2, AB, BCC/SS | synthesis | produce the nominal compositions screened |
| Homogenisation anneal (sealed quartz under Ar, then quench) | AB5, AB2, AB | synthesis | remove segregation, so measured ΔH belongs to the intended phase |
| High-energy ball milling (Ar, sealed vials) | Mg-based, NaAlH4 (+Ti catalyst) | synthesis / nanostructuring | kinetic limitation of Mg and complex hydrides (Phase 7) |
| ICP-OES of dissolved alloy | all, esp. mischmetal alloys | bulk composition | nominal vs actual composition (ML uses nominal); Mm composition is unknown in Purdue |
| XRD + Rietveld refinement | all | phases, lattice parameters, C14/C15, hydride expansion | C14/C15 is invisible to composition features (Phase 4 limitation) |
| SEM/EDS (BSE imaging, point and map analysis) | all | microstructure, secondary phases, local composition | explains sloped plateaus / extra plateaus |
| Activation cycles in the Sieverts rig | AB (TiFe) especially; all | activation behaviour | TiFe activation is not in the data |
| Sieverts (volumetric) PCT, abs + des, ≥4 temperatures over ≥40 K | all | plateau P(T), capacity, slope, hysteresis | replaces literature/digitised data; gives ΔH, ΔS with uncertainty |
| Kinetic uptake / release curves at fixed P/Peq | all | rate constants, Ea (several T) | kinetics comparable across materials (Phase 7 found 7 orders of spread) |
| Cycling (≥100 abs/des cycles) with periodic PCT | selected candidates | capacity retention, plateau shift | cycle life is missing from the screening |
| DSC (heat-flux, high-pressure cell if needed) | all; Mg, NaAlH4 | reaction enthalpy; Kissinger Ea from heating-rate series | independent ΔH check of the Van't Hoff value |
| TGA / TPD-MS | Mg-based, NaAlH4 | desorption temperature, gravimetric capacity, impurity release | capacity definition (reversible vs total) |
| Thermal conductivity: transient plane source on powder beds/compacts | selected candidates | k_eff vs H2 pressure and compaction | only 14 Purdue materials have k_eff; heat removal limits refuelling |
| Bed density / tapped density | selected candidates | packing density | converts solid-basis volumetric capacity to bed basis (Phase 8) |
