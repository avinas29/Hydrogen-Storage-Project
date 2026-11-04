# Literature Review and Theoretical Background

## Hydrogen absorption in metals

A metal M reacts with gaseous hydrogen in several steps: physisorption of H₂ on the surface, dissociation into atoms, and diffusion of the atoms into interstitial (tetrahedral or octahedral) sites of the lattice [@zuttel2003; @broom2011]. At low concentration the hydrogen forms a solid solution, the α phase, in which the lattice expands only slightly. Above a critical concentration the hydrogen–hydrogen interaction, mediated by the lattice expansion, makes it favourable to nucleate a hydride phase, β, with a much higher hydrogen content. While α and β coexist, the system has two components (metal and hydrogen) and three phases (α, β and gas). By the Gibbs phase rule it has one degree of freedom, so at a fixed temperature the equilibrium pressure is fixed. This is the *plateau* of the pressure–composition isotherm (PCI, also called PCT). Once the metal has been converted to β, the pressure rises steeply again [@sandrock1999].

For desorption, written per mole of H₂,

EQ reaction | (2/x) MH~x~ ⇌ (2/x) M + H~2~,

the reaction absorbs heat (it is endothermic), and the reverse reaction, absorption, releases the same amount of heat apart from hysteresis effects. Real materials deviate from the ideal picture in three ways that matter for engineering. Plateaus are *sloped*, because composition gradients and lattice strain spread the transition over a range of pressures. They show *hysteresis*: absorption takes place at a higher pressure than desorption at the same temperature, which costs compressor work or a larger temperature swing in each cycle. And some materials show *several plateaus*, each a different reaction step with its own ΔH and ΔS, as in the complex hydride NaAlH₄ [@bogdanovic2000].

## Pressure–composition isotherms and the Van't Hoff relation

At equilibrium on the plateau, the Gibbs energy of the desorption reaction is zero, ΔG = ΔH − TΔS + RT ln(P~eq~/P₀) = 0, with ΔH and ΔS taken as positive desorption values. Rearranging gives the Van't Hoff relation,

EQ vh | ln(P~eq~ / P₀) = − ΔH / (R T) + ΔS / R,

where P₀ is the reference pressure of ΔS. A plot of ln P~eq~ against 1/T is a straight line with slope −ΔH/R and intercept ΔS/R (@fig:pct). Measuring isotherms at several temperatures therefore gives both quantities [@broom2011]. Solving @eq:vh for temperature gives the temperature at which the hydride delivers a pressure P,

EQ tp | T(P) = ΔH / (ΔS − R ln(P / P₀)),

and the heat needed per kilogram of hydrogen released is

EQ q | Q = ΔH / M~H₂~,

with M~H₂~ = 2.01588 g mol⁻¹. ΔS is dominated by the loss of the entropy of gaseous H₂ (its standard molar entropy is about 130.7 J mol⁻¹ K⁻¹), which is why it varies relatively little between hydrides [@zuttel2003]. As a consequence, the operating temperature at a given pressure is roughly proportional to ΔH, and so is the heat demand. A hydride that releases hydrogen near room temperature cannot at the same time be very stable. This coupling appears again and again in the results of this work.

FIG pct | report/figures/f_pct_schematic.png | 15 | Schematic pressure–composition isotherms with the α, α + β and β regions (a), and the Van't Hoff plot built from the plateau pressures (b). Illustrative shapes, not measured data.

The relation assumes that ΔH and ΔS do not depend on temperature and that the plateau is flat. Both assumptions are approximations. The first is usually adequate over the few tens of kelvin covered by a set of isotherms; the second is not, for strongly sloped plateaus, and an operating window computed from the plateau midpoint is then optimistic at low state of charge.

## Engineering properties of hydride storage

Thermodynamics fixes the operating point, but a storage system also depends on several other properties [@broom2011; @sakintuna2007].

*Gravimetric and volumetric capacity.* Capacity is quoted as wt% hydrogen or as H/M (hydrogen atoms per metal atom or per formula unit). Literature values differ in definition: total uptake, reversible capacity between two pressures, or capacity of the first plateau only. They also refer to the material, not to a system with its vessel, heat exchanger and bed porosity, whose capacity is substantially lower. The DOE targets are system targets [@doe2017]. Volumetric capacity requires the density of the hydride or of the powder bed, which is often not reported.

*Reaction heat and heat transfer.* Desorption needs heat Q (@eq:q), and absorption releases the same amount of heat, which must be removed during refuelling. Powder beds conduct heat poorly, so heat transfer, not the intrinsic kinetics, often limits the flow rate.

*Kinetics and activation.* Rates depend on surface condition, particle size, catalysts and the driving force P/P~eq~. Many alloys, notably TiFe, need an activation treatment before the first absorption [@reilly1974]. Mg-based hydrides are kinetically slow without nanostructuring or catalysts [@huot1999].

*Hysteresis, plateau slope and cycle life.* Hysteresis raises the charging pressure; plateau slope lowers the pressure available near the end of discharge; and capacity loss over many cycles limits the life of the store.

*Cost and safety.* Rare earths, Co, V and minor metals raise cost. Operation at low pressure and the endothermic release are safety advantages.

## Families of metal hydrides

Hydride-forming alloys are usually grouped by structure and stoichiometry. A is an element that forms a stable binary hydride (rare earths, Ti, Zr, Mg, Ca); B is a non-hydride-forming element (Ni, Fe, Mn, Cr, Co, Al) that weakens the binding and adjusts the plateau [@sandrock1999]. @tab:families summarises the main families as they appear in the Purdue data used in this work.

TAB families | Main hydride families in the Purdue Metal Hydride Toolbox (single-plateau materials; medians computed in this work from the experimental ΔH, ΔS and reported capacities)
| Family | Examples | n | Median ΔH (kJ mol⁻¹) | Median ΔS (J mol⁻¹ K⁻¹) | Median wt% (max) | Median T(1 bar) (°C) |
|---|---|---|---|---|---|---|
| AB₅ | LaNi₅, MmNi₄.₅Al₀.₅, CaNi₅ | 146 | 33.0 | 111.2 | 1.2 (1.9) | 24.1 |
| AB₂ (Laves) | TiCr₂₋ₓMnₓ, ZrMn₂, Ti–Zr–Mn–V | 104 | 29.0 | 109.7 | 1.7 (2.9) | −3.8 |
| AB | TiFe, TiFe₁₋ₓMnₓ | 29 | 34.7 | 108.8 | 1.5 (2.2) | 32.0 |
| SS (BCC) | V–Ti–Fe, V–Ti–Cr | 24 | 30.8 | 96.7 | 0.7 (3.7) | 49.1 |
| Mg-based | MgH₂, Mg₂Ni | 4 | 72.4 | 133.6 | 5.6 (7.6) | 265.5 |

**AB₅ compounds.** The discovery that LaNi₅ absorbs large amounts of hydrogen reversibly at room temperature [@vanvucht1970] made AB₅ alloys the reference hydride. They activate easily, have flat plateaus and small hysteresis, and their plateau can be tuned by substituting Al, Sn, Mn or Co for Ni, or mischmetal (Mm) for La. Their capacity is low, about 1.2–1.5 wt%, and La and Co are costly.

**AB₂ Laves phases.** Ti- and Zr-based AB₂ alloys with hexagonal C14 or cubic C15 structures form the largest family in both datasets. They are lighter than AB₅ alloys, so their capacity is higher (up to about 2 wt% at the material level), and their plateau can be moved over several orders of magnitude by changing the Ti/Zr and Cr/Mn/V/Fe ratios. Many have sloped plateaus and noticeable hysteresis.

**AB compounds.** TiFe forms a hydride at near-ambient conditions from cheap and abundant elements [@reilly1974]. It shows two plateaus and is difficult to activate; Mn and other substitutions ease activation and adjust the plateau.

**BCC solid solutions.** V-based alloys can absorb close to 4 wt%, but only part of it is reversible at ambient conditions, because the first, very stable hydride does not decompose [@sakintuna2007].

**Mg-based and complex hydrides.** MgH₂ contains 7.6 wt% hydrogen, but its high ΔH requires about 300 °C for a desorption pressure of 1 bar, and its kinetics are slow without ball milling and catalysts [@huot1999]. Complex hydrides such as NaAlH₄ became reversible after Ti doping [@bogdanovic1997]. They decompose in two steps with different thermodynamics [@bogdanovic2000]. These families are poorly represented in the datasets used here.

## Composition–property relationships

Empirical rules link composition to hydride stability. Lundin, Lynch and Magee correlated ΔH with the size of the interstitial holes in intermetallic compounds: larger holes give more stable hydrides [@lundin1977]. In high-entropy and multicomponent alloys the atomic size mismatch δ is used as a descriptor of lattice strain and phase stability [@zhang2008]. Such rules explain trends within a family but are not accurate enough for quantitative design, which motivates data-driven models.

## Machine learning for materials properties

Machine-learning models for inorganic materials usually represent a composition by statistics of elemental properties, such as fraction-weighted means, spreads, minima and maxima of atomic mass, radius, electronegativity, melting point and valence-electron count, together with a few alloy descriptors [@ward2016]. Libraries such as pymatgen supply the elemental data and composition parsing [@ong2013]. Tree ensembles are well suited to such small, tabular and non-linear problems. A random forest averages many decision trees, each grown on a bootstrap sample and with a random subset of features at each split, which reduces variance without much tuning [@breiman2001]. Standard implementations are available in scikit-learn [@pedregosa2011].

For metal hydrides, Witman et al. cleaned the Sandia HydPARK database into ML-HydPARK and trained gradient-boosted trees on composition descriptors. Feature importance showed a strong dependence of the equilibrium pressure on a volume-based descriptor, which they linked to a log-linear relation between ln P~eq~ and the volume per atom [@witman2020]. This agrees with the hole-size correlation of Lundin et al. [@lundin1977].

Several methodological issues decide whether such models can be trusted.

*Leakage and duplicates.* Literature compilations contain the same or nearly the same composition several times. If near-duplicates are split between training and test folds, the test error is optimistic. Grouping near-identical compositions before splitting avoids this.

*Model selection bias.* Choosing hyperparameters by cross-validated error and reporting that same error biases the estimate downwards. Nested cross-validation, in which the hyperparameters are tuned only inside each outer training fold, removes most of this bias [@varma2006].

*Extrapolation.* Random cross-validation measures interpolation among materials like those in the training data. Discovery needs extrapolation. Meredig et al. showed that leaving out whole clusters of materials gives much larger errors than random cross-validation [@meredig2018].

*Applicability domain and uncertainty.* A prediction is only as reliable as the training data near the query. A practical domain measure is the distance from the query composition to the nearest training composition, with an error estimate calibrated as a function of that distance.

## Research gap

Published ML studies on hydrides concentrate on predictive accuracy. Three gaps remain that matter for an engineering student project with public data. First, the main public datasets are rarely audited before use. Their overlap, sign conventions and derived columns can make validation misleading, for instance when an entropy computed from the same (T, P) point as the target is used as an input. Second, predictions are seldom accompanied by a calibrated, distance-dependent uncertainty and an explicit applicability domain. Third, the path from a predicted or measured ΔH to an application decision, through operating windows, heat demand and explicit engineering constraints, is usually left implicit. This work addresses all three, and makes the resulting workflow usable through a transparent software tool.

## Summary

Metal hydrides store hydrogen at moderate pressure, with the plateau pressure fixed by ΔH and ΔS through the Van't Hoff relation. Because ΔS is nearly constant, ΔH controls both the operating temperature and the heat demand, and it depends strongly on composition. AB₅, AB₂ and AB intermetallics operate near ambient conditions with about 1–2 wt%, while Mg-based and complex hydrides store more but need higher temperatures. Composition-based machine learning can estimate ΔH, provided leakage, model-selection bias and extrapolation are handled and the uncertainty is reported. The following chapters build such a workflow on audited public data.
