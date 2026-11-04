# Datasets and Methodology

## Data sources

Two public datasets were used. Both are compilations of literature values; neither contains new measurements. @tab:datasets compares them.

TAB datasets | The two datasets as received (verified counts from the Phase 1 audit)
| Property | Purdue Metal Hydride Toolbox | ML-HydPARK v0.0.5 |
|---|---|---|
| Origin | Purdue Hydrogen Systems Laboratory, MATLAB toolbox [@voskuilen2014; @purduegit] | Sandia HydPARK database, cleaned for ML [@witman2020; @hydpark2024] |
| Records | 337 material files (.mh) | 772 rows, in 4 appended blocks (397 / 25 / 15 / 335) |
| Families | AB₅ 146, AB₂ 106, AB 29, SS 24, AB₃ 14, A₂B₇ 8, Misc 5, Mg 4, Complex 1 | AB₂ (incl. C14/C15) 454, AB₅ 106, SS 60, MIC 52, AB 33, Mg 32, A₂B 10, unlabelled 25 |
| ΔH, ΔS | desorption plateau(s), all 337; absorption for 83 | one value per row |
| Sign and unit | negative formation values, J mol⁻¹ H₂ | positive values, kJ mol⁻¹ H₂ |
| Capacity | wt% stated for 223, H/M stated for 114 | wt% for 741 rows |
| Other | 68 digitised PCI files; kinetics 31 abs / 26 des; density 37, Cp 28, k~eff~ 14 | one (T, P) point for 412 rows; reference DOI for 373 |

The Purdue toolbox stores each material as a text file with desorption (and sometimes absorption) ΔH and ΔS for each plateau, capacity, plateau slope, hysteresis, optional heat-transfer and kinetic parameters, and a reference. The toolbox's MATLAB classes were read to fix the conventions: the Van't Hoff function evaluates P = 101 325 · exp((ΔH~f~ − TΔS~f~)/(RT)) Pa with negative formation values, so the reference pressure is 1 atm. The "H/M" entry is hydrogen per *formula unit*, not per metal atom. ML-HydPARK reports ΔH and ΔS as positive magnitudes, together with derived columns (P~eq~ and ln P~eq~ at 25 °C, H/M). @fig:classes shows the class distributions.

FIG classes | report/figures/existing/fig01_class_distribution.png | 15 | Distribution of material classes in the Purdue toolbox (left) and ML-HydPARK v0.0.5 (right).

## Data audit

No model was trained before the audit was complete. Every record was kept and flagged rather than deleted, and the raw files were never modified. The findings that changed the analysis were the following.

*Opposite sign conventions.* Purdue stores negative formation values in J mol⁻¹ H₂; HydPARK stores positive decomposition values in kJ mol⁻¹ H₂. Both reproduce the Van't Hoff relation once the convention is known. All derived data in this work use positive desorption values, ΔH in kJ mol⁻¹ H₂ and ΔS in J mol⁻¹ H₂ K⁻¹ (@tab:conventions).

TAB conventions | Conventions adopted for all derived data
| Quantity | Convention in this work | Conversion from the sources |
|---|---|---|
| ΔH | positive, desorption, kJ mol⁻¹ H₂ | Purdue: −ΔH~f~/1000; HydPARK: unchanged |
| ΔS | positive, desorption, J mol⁻¹ H₂ K⁻¹, referred to P₀ = 1 atm | Purdue: −ΔS~f~; HydPARK: unchanged |
| Pressure | bar (1 atm = 1.01325 bar) | – |
| R | 8.314462618 J mol⁻¹ K⁻¹ | – |
| Missing value | NaN, never a default | toolbox type defaults are not used |

*Back-calculated entropy in HydPARK.* For 395 of the 412 rows that have a (T, P) point, ΔS = R ln P + ΔH/T holds to better than 0.01 J mol⁻¹ K⁻¹. These entropies are therefore not independent measurements but functions of ΔH and a single pressure–temperature point. Using ΔS, P~eq~(25 °C) or ln P~eq~(25 °C) as inputs for predicting ΔH would leak the target into the features, so they were excluded.

*Undefined capacities.* Only 8 Purdue files describe their capacity as reversible, and 17 describe it as assumed, approximate, theoretical or unconfirmed. Capacity is therefore treated as a reported, material-level value of uncertain definition.

*Default substitution.* When a property is missing, the toolbox substitutes a family-type default (for example for hysteresis, density or kinetics). These defaults were excluded, so missing properties stay missing: density is available for 37 materials, heat capacity for 28, effective thermal conductivity for 14, and kinetic parameters for 31 (absorption) and 26 (desorption).

*Digitised and shifted isotherms.* All 68 PCI files were digitised from published figures, and 14 were shifted along the composition axis by the curators. They are useful for consistency checks but are not raw measurements.

*References and compositions.* 102 Purdue files cite an unverified placeholder reference to the Sandia database; 49 use pseudo-elements (mischmetal Mm, lanthanum-rich mischmetal Lm, ferrovanadium Vf) whose exact composition is not defined; 12 have more than one plateau.

*Overlap between the datasets.* Of 288 Purdue compositions that could be parsed into real elements, 248 also occur in HydPARK, usually with the same value from the same original source (median ΔH difference 0.0 kJ mol⁻¹). For pairs whose Purdue entry cites an independent reference, the mean absolute ΔH difference is 2.2 kJ mol⁻¹. Two consequences follow. A model trained on one dataset cannot be validated on the other, because the test would measure memorisation of shared records. And about 2 kJ mol⁻¹ is a floor on the error that any model can be expected to reach with these data.

A missing-data map of both datasets is given in Appendix C (@fig:missing). The sparse properties (absorption data, hysteresis, density, kinetics and isotherms) limit what the screening in Chapter 6 can assess.

## Construction of the modelling dataset

The ΔH modelling set is a composition-level union of the two sources built by explicit rules (@fig:dataprep). Each composition was parsed with pymatgen [@ong2013] and reduced to normalised atomic fractions, which give a composition key; one row was kept per key. The Purdue single-plateau value was used where available, otherwise the median of the HydPARK values. Entries with pseudo-elements, multi-plateau entries, suspected HydPARK entry errors and entries that the Purdue curators had excluded were left out of the union but kept in the cleaned files. The source of each value, the spread between sources and the quality flags were stored with each row. The result has 725 compositions, 276 with Purdue values and 449 with HydPARK values. AB₂ dominates (401 compositions), followed by AB₅ (116), SS (59), AB (40), Mg (35) and MIC (33).

FIG dataprep | report/figures/f_dataprep.png | 16 | Data-preparation workflow from the two raw sources to the composition-level ΔH dataset.

## Composition descriptors

The inputs are computed from composition alone, and the build script checks that no thermodynamic, pressure, temperature or capacity value enters the feature table. Elemental properties were read from pymatgen's periodic table: atomic mass, Pauling electronegativity X, empirical atomic radius, melting point T~m~, molar volume and valence-electron count (group number for groups 1–12, group − 10 for groups 13–18, and 3 for lanthanides and actinides). All 52 elements in the data have values for these six properties, so no elemental value had to be filled in by hand. Metallic and calculated radii, which are missing for some elements, were not used.

For each property the fraction-weighted mean and standard deviation and the minimum and maximum over the elements present were computed. Four alloy descriptors were added: the number of elements; the ideal configurational entropy, in units of R,

EQ sconf | S~conf~ / R = − Σ~i~ x~i~ ln x~i~ ;

the atomic size mismatch [@zhang2008],

EQ delta | δ = [ Σ~i~ x~i~ (1 − r~i~ / r̄)² ]^1/2^, with r̄ = Σ~i~ x~i~ r~i~ ;

and the fraction of hydride-forming atoms (groups 1–5, lanthanides, actinides and Pd). Atomic fractions of the 12 elements that occur in at least 5% of the compositions (Zr, Ti, Mn, Fe, Ni, Cr, V, La, Co, Al, Mg, Cu) complete the set. Features were taken in order of interpretability, and a feature was dropped if its absolute Pearson correlation with one already kept exceeded 0.95. This removed the radius standard deviation (r = 0.999 with δ) and the maximum molar volume (r = 0.964 with the maximum radius), leaving 38 descriptors (@tab:descriptors; full list in Appendix A). A family one-hot encoding was prepared as an optional extra set.

TAB descriptors | Composition descriptors used by the ΔH model
| Group | Descriptors | Number |
|---|---|---|
| Elemental statistics | mean, std, min, max of mass, X, radius, T~m~, molar volume, valence electrons (radius std and volume max removed) | 22 |
| Alloy descriptors | number of elements, S~conf~/R, δ, fraction of hydride formers | 4 |
| Element fractions | x~Zr~, x~Ti~, x~Mn~, x~Fe~, x~Ni~, x~Cr~, x~V~, x~La~, x~Co~, x~Al~, x~Mg~, x~Cu~ | 12 |
| Total | | 38 |

No single descriptor correlates strongly with ΔH (largest absolute Spearman coefficient 0.54, for the mean molar volume), which is consistent with the absence of leakage. The sign of that correlation is positive, as expected from the hole-size rule [@lundin1977].

## Validation design

*Groups.* Compositions with the same elements and an L1 distance between their fraction vectors of at most 0.02 were joined into groups, giving 659 groups from 725 compositions. All splits keep a group on one side.

*Nested grouped cross-validation.* The generalisation error was estimated with an outer five-fold GroupKFold, shuffled and repeated three times. Inside each outer training part, an inner four-fold GroupKFold grid search chose the hyperparameters. The outer test folds were never used for any choice, which avoids the selection bias discussed in Section 2.6 [@varma2006].

*Baselines.* Two baselines were fitted on each training fold: the global mean, and the median ΔH of the material's family.

*Further tests.* A single grouped 80/20 split (seed 42) was kept for parity plots and permutation importance. Leave-one-family-out tests measured extrapolation [@meredig2018], and models were also refitted on data subsets.

*Metrics.* With y~i~ the reported and ŷ~i~ the predicted ΔH of n test compositions,

EQ mae | MAE = (1/n) Σ~i~ | y~i~ − ŷ~i~ |,   RMSE = [ (1/n) Σ~i~ (y~i~ − ŷ~i~)² ]^1/2^,   R² = 1 − Σ~i~ (y~i~ − ŷ~i~)² / Σ~i~ (y~i~ − ȳ)².

Results are reported as the mean ± standard deviation over the three repeats.
