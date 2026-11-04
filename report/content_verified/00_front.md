@@ABSTRACT
Metal hydrides store hydrogen at low pressure and close to room temperature, but choosing an alloy for an application requires its desorption enthalpy (ΔH) and entropy (ΔS), because together they fix the temperature and pressure at which hydrogen is released. This project builds an audited, composition-level dataset from two public sources, the Purdue Metal Hydride Toolbox (337 materials) and ML-HydPARK v0.0.5 (772 records), and uses it for three tasks: predicting ΔH from composition, converting thermodynamic data into operating windows, and screening materials against application requirements.

The audit found opposite sign conventions, entropies back-calculated from a single pressure–temperature point, capacities of unstated definition, and a large overlap between the sources: 248 of 288 parseable Purdue compositions also appear in HydPARK, so one dataset cannot validate the other. A random forest using 38 composition descriptors predicts ΔH with a mean absolute error (MAE) of 5.26 ± 0.14 kJ mol⁻¹ H₂ under nested grouped cross-validation (R² = 0.72), compared with 8.88 kJ mol⁻¹ for a family-median rule. The error rises from 2.6 to 16.9 kJ mol⁻¹ as the distance to the nearest training composition grows, and the model fails when a whole alloy family is held out. Predictions are therefore reported with an 80% interval and an applicability-domain flag. Van't Hoff analysis of the experimental ΔH and ΔS shows, for example, that LaNi₅ reaches 1 bar at 11.6 °C and needs 15.9 MJ of heat per kg of H₂ released, whereas MgH₂ needs 302 °C and 38.8 MJ kg⁻¹.

A rule-based screening (hard constraints, weighted criteria, Pareto fronts and evidence classes) ranks the experimental materials for mobile and stationary requirements and is implemented in an interactive Streamlit application. The rankings are material-level screening results, and the compositions generated with the model are candidates for measurement, not discoveries. No laboratory work was carried out; a synthesis and characterisation plan is proposed as future work.

**Keywords:** metal hydrides; hydrogen storage; machine learning; random forest; Van't Hoff; applicability domain; materials screening

@@ACK
I thank my supervisor, Dr. Saket Verma, Assistant Professor, School of Energy Science and Engineering, and my teaching assistant, Dr. Joy Nondy, for their guidance throughout this project.

The Purdue Hydrogen Systems Laboratory made the Metal Hydride Toolbox publicly available, and Sandia National Laboratories released the ML-HydPARK dataset. This work would not have been possible without these open data sources.

Avinash
November 2026

@@ABBR
| Abbreviation | Meaning |
|---|---|
| AB, AB₂, AB₅ | intermetallic families by A:B stoichiometry (A = hydride-forming element) |
| BCC | body-centred cubic |
| CV | cross-validation |
| DOE | U.S. Department of Energy |
| GB | gradient boosting |
| LHV | lower heating value of hydrogen (119.96 MJ kg⁻¹) |
| MAE | mean absolute error |
| MIC | multicomponent intermetallic (HydPARK class) |
| ML | machine learning |
| Mm | mischmetal (mixture of rare-earth metals) |
| NN | nearest neighbour |
| PCI / PCT | pressure–composition isotherm / pressure–composition–temperature |
| PEMFC | proton-exchange-membrane fuel cell |
| RF | random forest |
| RMSE | root-mean-square error |
| SS | solid solution (mainly BCC, V-based) |
| wt% | weight per cent of hydrogen in the hydride |

| Symbol | Meaning | Unit |
|---|---|---|
| ΔH | enthalpy of hydride decomposition (positive desorption value) | kJ mol⁻¹ H₂ |
| ΔS | entropy of hydride decomposition (positive desorption value) | J mol⁻¹ H₂ K⁻¹ |
| P~eq~, P~abs~, P~des~ | equilibrium, absorption and desorption plateau pressure | bar |
| P₀ | reference pressure, 1 atm = 1.01325 bar | bar |
| R | gas constant, 8.314462618 | J mol⁻¹ K⁻¹ |
| T | absolute temperature | K |
| T(1 bar) | temperature at which P~des~ = 1 bar | °C |
| Q | reaction heat per kg of H₂ (= ΔH / M~H₂~) | MJ kg⁻¹ H₂ |
| x~i~ | atomic fraction of element i | – |
| δ | atomic size mismatch | – |
| d~NN~ | L1 distance to the nearest training composition | – |
| R² | coefficient of determination | – |
