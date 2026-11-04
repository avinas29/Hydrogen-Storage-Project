# Results and Discussion

## Data and model

The audit changed the analysis before any model was trained. The HydPARK file turned out to contain 772 records rather than the roughly 420 previously assumed. The two sources use opposite sign conventions, and the HydPARK entropies are back-calculated. Above all, most Purdue compositions are already in HydPARK. Training on one dataset and testing on the other would therefore have produced an apparently independent validation that in fact measured memorisation. Using HydPARK's ΔS or P~eq~(25 °C) as inputs would have leaked the target. Both errors are easy to make with these datasets, and either would have produced a much better-looking but meaningless model.

On the audited composition-level dataset, the random forest predicts ΔH with an MAE of 5.26 kJ mol⁻¹ under nested grouped cross-validation, 41% below the family-median rule, and the hold-out split confirms this (5.55 kJ mol⁻¹). This accuracy is about 2.4 times the inter-source scatter of the data. It is enough to sort compositions into stability classes but not to set a plateau pressure. The error depends strongly on the distance to the training data: within d~NN~ ≤ 0.05 the MAE is 2.6 kJ mol⁻¹, close to the measurement floor, while beyond 0.5 it is 16.9 kJ mol⁻¹. When a whole family is withheld, the model fails, and for three of six families it is worse than a constant. The model is therefore an interpolation tool for AB₅, AB₂ and related intermetallics. It is not a means of discovering new families, and the platform enforces this with its applicability-domain flag.

## Thermodynamic findings

The Van't Hoff analysis makes the central trade-off of hydride storage quantitative. Because ΔS lies in a narrow range (interquartile range 102.8–118.9 J mol⁻¹ K⁻¹ for the Purdue materials), the operating temperature and the reaction heat are both set by ΔH. Low-temperature materials need little heat: those that reach 1 bar with heat at 80 °C or below need a median of 15.1 MJ kg⁻¹ H₂, about 13% of the energy content of the hydrogen. They are, however, the transition-metal intermetallics with about 1–2 wt% (@tab:families). The light hydrides with higher capacity are too stable. MgH₂ holds 7.6 wt% but needs 302 °C for 1 bar and 38.8 MJ kg⁻¹, almost a third of the LHV. No material in the data combines high capacity with near-ambient operation. The digitised isotherms agree with the tabulated thermodynamics within a median of 1.76 kJ mol⁻¹, although this is a consistency check on partly shared data. The NaAlH₄ isotherm confirms which tabulated step belongs to which plateau.

## Mobile and stationary rankings

@tab:phase8 lists the five highest-ranked materials of the generic mobile and stationary screens of Section 6.2. In the mobile screen, Ti-based AB₂ Laves alloys and a Ti–V–Zr–Mn–Fe–Ni alloy lead, with 1.9–2.2 wt% at the material level, release at 1 bar below 0 °C and need 12.4–13.8 MJ kg⁻¹ H₂. The two highest-ranked AB₂ alloys run at about 19–22 bar at 25 °C, so they need a vessel rated accordingly. The stationary screen favours low-pressure alloys made of common metals: TiFe₀.₉Al₀.₁, Ti₀.₉Zr₀.₁Mn₁.₄, TiFe₀.₈Mn₀.₂ and, further down, CaNi₅ (rank 6). LaNi₅, the textbook reference, passes both screens but ranks only 58th of 232 for mobile use and 66th of 252 for stationary use, because of its modest capacity (1.49 wt%) and the rare-earth cost class. Several high-ranked entries carry caveats. The mobile rank-3 alloy has PCI curves that give a ΔH about 11 kJ mol⁻¹ lower than its tabulated value, and the rank-5 alloy cites an unverified reference. These flags are carried in the outputs, and any of these materials would need its own measurement before use.

TAB phase8 | Top five materials of the generic mobile and stationary screens (experimental data; reported capacities are material-level values)
| Screen | Rank | Material | Family | wt% | T(1 bar) (°C) | P(25 °C) (bar) | Q (MJ kg⁻¹) | Score |
|---|---|---|---|---|---|---|---|---|
| Mobile | 1 | Ti₁.₃Cr₁.₂Mn₀.₈ | AB₂ | 1.90 | −41.8 | 18.6 | 12.4 | 0.74 |
| Mobile | 2 | Ti₁.₂CrMn | AB₂ | 2.02 | −44.1 | 22.3 | 12.7 | 0.73 |
| Mobile | 3 | Ti₀.₅₆V₀.₃Zr₀.₁Mn₀.₉₄Fe₀.₀₆Ni₀.₀₄ † | AB | 2.20 | −5.7 | 3.63 | 13.8 | 0.72 |
| Mobile | 4 | Ti₀.₉Zr₀.₂Mn₁.₄Cr₀.₄Vf₀.₂ ‡ | AB₂ | 2.10 | −7.3 | 3.48 | 12.6 | 0.72 |
| Mobile | 5 | Ti₀.₈Zr₀.₂Mn₁.₅Cr₀.₅ § | AB₂ | 2.00 | −23.1 | 8.44 | 13.6 | 0.71 |
| Stationary | 1 | TiFe₀.₉Al₀.₁ | AB | 1.30 | 16.8 | 1.41 | 14.9 | 0.73 |
| Stationary | 2 | Ti₀.₉Zr₀.₁Mn₁.₄ | AB₂ | 1.91 | 29.7 | 0.80 | 17.2 | 0.72 |
| Stationary | 3 | Ti₀.₅Zr₀.₅Mn₁.₂Fe₀.₃ § | AB₂ | 1.90 | 111 | 0.01 | 24.2 | 0.70 |
| Stationary | 4 | TiFe₀.₈Mn₀.₂ | AB | 1.30 | 29.4 | 0.83 | 15.8 | 0.70 |
| Stationary | 5 | TiMn₁.₄ † | AB₂ | 1.75 | −4.9 | 3.58 | 14.1 | 0.70 |

† own PCI curves give a ΔH more than 5 kJ mol⁻¹ different from the tabulated value; ‡ contains ferrovanadium (Vf), whose exact composition is not defined; § unverified Sandia reference.

Two conclusions hold regardless of the exact order. First, no interstitial hydride comes close to the 5.5 wt% system target. With material-level capacities of about 2 wt%, metal hydrides suit uses where volume, pressure and safety matter more than mass. Second, the families that win are different for the two applications, and the reasons are physical: capacity and low heat for mobile use, low pressure and cheap elements for stationary use.

## Requirement-driven scenarios

To show how the Application Requirement Designer responds to a concrete brief, two illustrative scenarios were run with the real engines (@tab:scenarioreq). They are examples, not real design briefs.

TAB scenarioreq | Requirements of the two demonstration scenarios (illustrative inputs)
| Requirement | Scenario 1: mobile (PEMFC vehicle) | Scenario 2: industrial buffer |
|---|---|---|
| Ambient temperature | −10 to 40 °C | 5 to 40 °C |
| Heat source | PEMFC waste heat, 70 °C, 5 kW | industrial waste heat, 120 °C, 50 kW |
| Cooling for charging | – | cooling water, 20 °C |
| Hydrogen stored / flow | 1 kg / 0.5 kg h⁻¹ | 50 kg / 5 kg h⁻¹ |
| Delivery pressure | 3 bar | 5 bar |
| Maximum / charging pressure | 50 / 100 bar | 30 / 30 bar |
| Other limits | material mass ≤ 80 kg; capacity ≥ 1.5 wt% | – |
| Main weights | capacity 0.30, heat 0.20, kinetics 0.15 | kinetics 0.20, pressure fit 0.20, hysteresis 0.15, cost 0.15 |

In the mobile scenario, 278 of the 337 materials fail at least one hard constraint. The most common failures are the minimum capacity (221 materials), the mass limit (144) and delivery of 3 bar at 70 °C (112). Of the 59 remaining materials, 4 have insufficient evidence and are listed but not ranked, which leaves 55 ranked. In the industrial scenario, 222 materials fail, mostly because their pressure in a 120 °C bed would exceed 30 bar (164 materials); 115 remain, 6 of them with insufficient evidence, so 109 are ranked. @tab:scenariotop and @fig:scenarios show the results.

TAB scenariotop | Top five materials of the two scenarios (all evidence class "data-supported"; temperatures are those needed to deliver the required pressure)
| Scenario | Rank | Material | Family | T needed (°C) | wt% | Q (MJ kg⁻¹) | Score |
|---|---|---|---|---|---|---|---|
| Mobile | 1 | Ti₀.₉Zr₀.₂Mn₁.₄Cr₀.₄V₀.₂ | AB₂ | 33.1 | 2.10 | 13.2 | 0.64 |
| Mobile | 2 | Ti₀.₉Zr₀.₂Mn₁.₈V₀.₂ | AB₂ | 23.9 | 2.10 | 12.9 | 0.63 |
| Mobile | 3 | V₀.₈₅₅Ti₀.₀₉₅Fe₀.₀₅ | SS | 56.7 | 3.70 | 21.4 | 0.62 |
| Mobile | 4 | V₀.₈₄₅₅Ti₀.₁₀₄₅Fe₀.₀₅ | SS | 35.5 | 3.44 | 21.3 | 0.62 |
| Mobile | 5 | TiCrMn₀.₈₅Fe₀.₃V₀.₁₅ | AB₂ | −2.3 | 1.60 | 10.4 | 0.61 |
| Industrial | 1 | Ti₀.₉Zr₀.₁Mn₁.₄ | AB₂ | 69.8 | 1.91 | 17.2 | 0.87 |
| Industrial | 2 | Zr₀.₇Ti₀.₃CrFe | AB₂ | 74.3 | 1.70 | 14.6 | 0.86 |
| Industrial | 3 | TiFe₀.₉Al₀.₁ | AB | 59.6 | 1.30 | 14.9 | 0.85 |
| Industrial | 4 | TiFe₀.₈Mn₀.₂ | AB | 73.5 | 1.30 | 15.8 | 0.85 |
| Industrial | 5 | TiFe₀.₉Ni₀.₁ | AB | 78.3 | 1.40 | 17.2 | 0.84 |

FIG scenarios | report/figures/f_scenarios.png | 16 | Material-level capacity against reaction heat in the two scenarios: materials failing a hard constraint (grey), ranked materials (light blue), the top five (dark blue, numbered) and the Pareto front among ranked materials (red circles).

The two top-five lists have no material in common. The mobile brief rewards capacity at a temperature that 70 °C waste heat can reach. It selects Ti–Zr–Mn AB₂ alloys at about 2.1 wt% and two V-based BCC alloys whose higher capacity (3.4–3.7 wt%) comes with higher heat (21 MJ kg⁻¹). These two lie on the Pareto front, which shows the capacity–heat trade-off directly. The mobile top material needs about 48 kg of alloy for 1 kg of hydrogen and 1.8 kW of heat at 0.5 kg h⁻¹, within the 5 kW available. The industrial brief accepts more stable hydrides, because 120 °C heat is available, and rewards pressure fit, kinetics and cheap elements. Its top five are Ti–Zr–Mn and TiFe-type alloys that need 60–78 °C to deliver 5 bar, so they have a margin of more than 40 K on the heat source. Storing 50 kg of hydrogen in the top material requires about 2.6 t of alloy, a mass that is acceptable for a stationary buffer but would rule it out for a vehicle. The weight sensitivity in the platform output shows the difference in robustness. When each of the seven weights is in turn removed or doubled (14 cases), the industrial leader stays first in 9 cases, whereas the mobile leader stays first in only 4. The mobile ranking therefore depends much more on the user's priorities.

## ML-generated candidates

Each scenario also ran the Discovery Lab on two alloy systems near the training data. These results are separate from the experimental ranking. For the mobile case, 189 Ti–Zr–Mn–Cr compositions were generated; 49 were rejected, mainly for lying outside the applicability domain, and 140 remained inside the domain and the temperature window. The top-scored candidate, Ti₀.₇₅Zr₀.₂₅Mn₁.₅Cr₀.₅, has a predicted ΔH of 28.4 kJ mol⁻¹ (80% interval 24.1–31.4) at d~NN~ = 0.03, close to its nearest known composition (27.5 kJ mol⁻¹). For the industrial case, 143 La–Ce–Ni–Al compositions were generated and 133 retained. The top candidate, La₀.₉₅Ce₀.₀₅Ni₄.₅Al₀.₅, has a predicted ΔH of 36.1 kJ mol⁻¹ (31.8–39.0); with the assumed AB₅ ΔS it would deliver 5 bar at about 95 °C, with a band of 27–154 °C.

These compositions are *candidates for measurement, not discoveries*. They are close to known alloys by construction: the domain limit allows nothing else. Their predicted ΔH differs little from that of their neighbours, the entropy behind each temperature is assumed, and no capacity is predicted. Their value is to suggest which nearby compositions to synthesise first, together with a stated interval that a PCT measurement can confirm or refute (Section 8.3).

## Critical discussion of limitations

@tab:limits collects the main limitations, what each implies for the results, and what would be needed to remove it.

TAB limits | Main limitations of the work and the measurement or data that would address each
| Limitation | Consequence for the results | What would address it |
|---|---|---|
| No external validation set; the two sources share most values | the CV error is the only estimate of generalisation | an independent set of newly measured compositions |
| Composition-only descriptors (no structure, C14/C15, microstructure) | ΔH differences between polymorphs and processing routes are invisible | XRD phase data, structure-based descriptors |
| Model fails on unseen families | no ML screening of Mg-based, complex or new families | data for those families; physics-informed models |
| ΔS is not predicted, only assumed | T(1 bar) bands of about 105 K for new compositions | PCT isotherms at ≥ 4 temperatures |
| Capacities of unstated definition, material level only | capacity rankings are indicative; no system capacity | reversible capacity between the application's pressures; system design |
| Density stated for 37 materials only | volumetric capacity mostly not assessable | density and bed packing measurements |
| Kinetics and cost only as qualitative classes | no rate or price optimisation | standardised kinetic tests; cost data |
| No cycle-life data | durability is not screened | cycling tests (≥ 100 cycles) |
| Digitised, partly shifted isotherms | the PCI check is a consistency check only | original measured isotherms |
| No laboratory work in this project | all rankings remain screening results | the programme proposed in Section 8.3 |

Two of these points deserve emphasis. First, the prediction intervals are empirical: they summarise the out-of-fold errors of similar compositions and assume that new compositions behave like the training data at the same distance. They are useful for ordering experiments, not as guarantees. Second, every ranking in this chapter is a rule-based screening of literature data under stated assumptions. A different but defensible choice of weights or thresholds reorders the top group, although it rarely replaces it, as the sensitivity analysis shows.
