# Application-Specific Screening and Software Platform

## Screening principles

The screening turns the thermodynamic results of Chapter 5 into a ranked list of materials for a stated requirement. Four principles were applied throughout.

1. *Experimental data first.* Screening uses the 337 Purdue materials with their experimental ΔH and ΔS. ML predictions are evaluated separately and never mixed into the ranking of experimental materials.
2. *Material level only.* Capacity is the reported, material-level value, whose definition varies. A real store adds a vessel, a heat exchanger and bed porosity, so its system capacity is considerably lower. The DOE system target of 5.5 wt% [@doe2017] is shown only for orientation.
3. *Missing is not failing.* A constraint is evaluated as pass, fail, *unknown* (the material value is missing) or *not specified* (no requirement given). A material is rejected only on an evaluated failure; missing evidence is reported and never counts against it.
4. *Transparent and tested choices.* Constraints, criteria and weights are listed in the output, and the rankings are tested for sensitivity to the weights and thresholds.

## Mobile and stationary screening of the experimental materials

The first screen compares two generic applications. A data-quality gate removes records with an atypical ΔS (outside 70–170 J mol⁻¹ K⁻¹) or an assumed or unconfirmed capacity. Hard constraints then encode the engineering limits of each application (@tab:constraints). For multi-plateau materials, the most stable plateau is used for T(1 bar), because the full capacity is needed, and the highest-pressure plateau for the pressure limits.

TAB constraints | Hard constraints of the mobile and stationary screens
| Application | Constraint | Engineering reason |
|---|---|---|
| both | 70 ≤ ΔS ≤ 170 J mol⁻¹ K⁻¹; capacity not assumed or unconfirmed | data-quality gate |
| mobile | T(1 bar, full capacity) ≤ 80 °C | desorption with PEM fuel-cell waste heat (stack at 60–80 °C) |
| mobile | P(50 °C) ≤ 50 bar | moderate tank pressure on a hot day |
| mobile | charging pressure at 25 °C ≤ 100 bar | refuelling without very high compression |
| stationary | T(1 bar, full capacity) ≤ 150 °C | low-grade industrial, electrolyser or boiler heat |
| stationary | P(25 °C) ≤ 10 bar | low-pressure storage at room temperature |
| stationary | P(50 °C) ≤ 30 bar | warm-day pressure limit |
| stationary | charging pressure at 25 °C ≤ 30 bar | direct filling from a PEM electrolyser (30 bar delivery assumed) |

Materials that pass are scored on criteria normalised to 0–1 among the passing materials: reported capacity, reaction heat, a family-level kinetics class (AB₅, AB₂, AB, AB₃ = 1; complex = 0.25; Mg = 0; families without data = 0.5 and flagged), hysteresis (missing = 0.5, neutral), pressure fit (1 for 1–10 bar at 25 °C, falling to 0 one decade outside), pressure safety (stationary only) and a qualitative cost class. The cost class is an element indicator, not a price model: common metals score 1; rare earths, mischmetal, Co, V and minor metals 0.5; precious metals 0. The weights reflect the applications (@tab:weights). Mobile use emphasises capacity and heat, and stationary use emphasises cost, low pressure and cycling loss.

TAB weights | Criterion weights of the mobile and stationary screens (each column sums to 1)
| Criterion | Mobile | Stationary |
|---|---|---|
| capacity | 0.35 | 0.10 |
| reaction heat | 0.20 | 0.10 |
| kinetics class | 0.15 | 0.10 |
| hysteresis | 0.10 | 0.15 |
| pressure fit | 0.10 | 0.10 |
| cost class | 0.10 | 0.25 |
| pressure safety | – | 0.20 |

Of the 337 materials, 319 pass the data-quality gate; 232 pass all mobile constraints and 252 all stationary constraints (@fig:screenmap). The mobile screen rejects 56 materials whose T(1 bar) is too high and 35 whose pressure at 50 °C is too high. The stationary screen rejects mainly materials with too high a pressure: 57 at 25 °C and 51 at 50 °C. No Mg-based material passes either screen, because all need well over 150 °C.

FIG screenmap | report/figures/existing/fig24_screening_map.png | 16 | Hard-constraint screening of the 337 Purdue materials for mobile (left) and stationary (right) use. Reported material-level capacity against T(1 bar); the grey line marks the DOE 2025 *system* target, shown for orientation only.

The weights are a judgement, so their influence was tested with 2000 weight vectors drawn from a Dirichlet distribution centred on the base weights (concentration 20), 2000 from a uniform Dirichlet (any weights), one-at-a-time changes (each weight set to zero or doubled) and varied thresholds. The *composition* of the top group proved robust: Ti-based AB₂ and AB alloys for mobile use, and TiFe-type and Ti–Zr–Mn alloys for stationary use. The leading mobile material stays in the top ten in 88% of the perturbed draws and 72% of the uniform draws. The order within the top group is not robust. The largest one-at-a-time effects are removing the capacity weight for mobile use (Kendall τ = 0.71 against the base ranking) and doubling the pressure-safety weight or removing the cost weight for stationary use (τ = 0.65 each). The rankings should therefore be read as tiers, not as a single winner. The results are presented in Chapter 7.

## Software platform

The model, the thermodynamic functions and the screening were combined into an interactive application, *METAL HYDRIDE AI*, written in Python with Streamlit. The application computes nothing of its own: every prediction is made live by the saved random forest, and every thermodynamic number comes from the Van't Hoff functions of Chapter 5. @fig:arch shows the architecture: page renderers call engine modules that contain no user-interface code, and the engines read the model bundle and the project data in read-only mode. The application has eight pages: an overview, the Property Predictor, the Candidate Discovery Lab, the Application Requirement Designer, a material comparison, a thermodynamic explorer, a model-performance page that reproduces the validation results of Chapter 4, and a dataset and evidence explorer that shows the overlap, quality flags and missing data of Chapter 3.

FIG arch | report/figures/f_architecture.png | 13.5 | Architecture and data flow of the METAL HYDRIDE AI platform.

*Property Predictor.* A composition typed by the user is converted to the 38 descriptors and passed to the model. The page shows the predicted ΔH with the 80% interval of its distance bin, the distance to the nearest training composition with a domain flag, and the five nearest experimental compositions with their measured ΔH. It warns when the input contains an element absent from the training data, and its Van't Hoff estimate states that ΔS is an assumed family median.

*Candidate Discovery Lab.* The user chooses an alloy system and composition ranges, either from site templates or as free atomic fractions. Templates are available for TiFe₁₋ₓMnₓ, Ti–Zr–Mn–Cr and Ti–Cr–Mn Laves phases, La–Ni–Al, La–Ni–Sn and La–Ce–Ni–Al AB₅ alloys, and V–Ti–Cr solid solutions. The generator builds a reproducible grid and removes duplicates. Each candidate is predicted and then rejected with an explicit reason if it contains elements the model has not seen, if it lies outside the applicability domain, or if even the most favourable end of its temperature band misses the target window. The remaining candidates are ranked and their Pareto front is marked. Every output is labelled as a proposed candidate: ΔH is predicted, ΔS is assumed, and capacity is not predicted.

*Application Requirement Designer.* The user describes an application in seven steps: application type, operating environment, hydrogen requirements, optional engineering constraints, weights, review and results (@fig:screenflow). Five application presets (stationary, mobile, fuel-cell waste-heat integration, industrial buffering and renewable-energy storage) supply default weights. The derived operating conditions follow from the inputs. The highest bed temperature available for delivery is the heat-source temperature if there is a heat source, and otherwise the coldest ambient temperature. The charging temperature is the cooling-water or hottest ambient temperature. The constraints are then evaluated for each experimental material: delivery of the required pressure at the available temperature, maximum pressure on the hottest day, charging pressure (including stated hysteresis), minimum capacity, mass and volume limits, heating power and thermal energy. Cycle life is always "unknown", because no cycle-life data exist.

FIG screenflow | report/figures/f_screening_flow.png | 14 | Screening workflow of the Application Requirement Designer.

Each material receives an evidence class. *Insufficient evidence* means that the material fails the data-quality gate; such materials are shown but never ranked. *Provisional* means that the material passes the gate but carries a caveat: its own PCI curves disagree with the tabulated ΔH by more than 5 kJ mol⁻¹, its reference is an unverified Sandia placeholder, its data are identical to another file, it contains a pseudo-element, or its capacity is approximated, theoretical or first-plateau only. *Data-supported* means experimental ΔH and ΔS with a literature capacity and none of these caveats. The evidence class enters the score with a weight of 0.1. The Pareto front is computed among the ranked materials on two objectives chosen by the user, by default capacity (maximised) and reaction heat (minimised). For the top material the page states which requirements are met, which could not be evaluated, its main advantages and limitations, and the measurements still needed before use.

*Testing and reproducibility.* The engines contain no Streamlit code and are covered by 77 automated tests, from parsing and consistency with the training pipeline to constraints, scoring, Pareto fronts, evidence classes, export and a headless run of every page. A review of the demonstration output during this work showed that unranked insufficient-evidence materials could dominate the Pareto front and leave the front among ranked materials empty. The front is now computed among ranked materials only, and a test guards this.
