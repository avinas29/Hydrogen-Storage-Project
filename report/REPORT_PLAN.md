# B.Tech report: Stage 1 plan and evidence map

Status: **awaiting approval**. Nothing has been drafted yet.
Project path verified: `~/ongc-iitkgp/Hydrogen-Storage-Project`. The path in the brief (`~/Documents/avinashbishnoidmn/…`) does not exist.

## 1. Official format (extracted from `BTP_Report_Format_Word.docx`)

| Item | Requirement in the template |
|---|---|
| Page | US Letter, 8.5 × 11 in (12240 × 15840 twips) |
| Margins | top / right / bottom 0.91 in (23 mm), **left 1.06 in (27 mm)**, header/footer 0.5 in |
| Body text | Times New Roman 12 pt, justified, spacing after 6 pt, default line spacing (1.15) |
| Title page | centred; title 18 pt bold; "A B. Tech Project Report Submitted / in Partial Fulfillment of the Requirements / for the Degree of" 13 pt bold; "Bachelor of Technology" 14 pt bold; "by", student name 14 pt bold, "(Roll No.)", "under the guidance of", guide name 14 pt bold, "to the"; IITG logo; "SCHOOL OF ENERGY SCIENCE AND ENGINEERING / INDIAN INSTITUTE OF TECHNOLOGY GUWAHATI / GUWAHATI - 781039, ASSAM" 13 pt bold |
| Certificate | fixed wording ("This is to certify that the work contained in this thesis entitled … is a bona fide work of … carried out in the School of Energy Science and Engineering … under my supervision and that it has not been submitted elsewhere for a degree."), supervisor block right-aligned, Date / Guwahati |
| Preliminary sequence | Title → Certificate → Acknowledgements → Contents → List of Figures → List of Tables |
| Not in template | **Declaration, Abstract, List of abbreviations**: see question Q2 |
| Chapters | "Chapter N" 14 pt bold centred, then the chapter title 18 pt bold centred, each on a new page; sections use Heading 2 numbered "N.M" (template style: Calibri, 13 pt, bold, blue) |
| Fixed chapters | 1 Introduction (ends with "Organization of the Report"), 2 Literature Review (ends with "Summary"), middle chapters = own work, last = **Conclusion and Future Work**, then **References** |
| References | "Use APA or Vancouver format" (Q3) |
| Page numbers | centred footer PAGE field. The template has a single section; its sample contents page suggests roman numerals for preliminary pages (List of Figures "vii") and arabic numbers from Chapter 1 |
| Length | not specified, so the brief's 40–45-page target applies |

The template lets the middle chapters be the student's own work, so the brief's 8-chapter structure fits within it.

## 2. Structure and page budget (target ≈ 44 pages excluding appendices)

| Part | Pages | Main content |
|---|---|---|
| Title, Certificate, (Declaration), Acknowledgements, Abstract | 5 | Abstract ≈ 250 words |
| Contents, List of Figures, List of Tables, Abbreviations & Symbols | 4 | |
| Ch 1 Introduction | 3 | hydrogen storage options → metal hydrides → why composition and thermodynamics matter → problem, objectives, scope, organisation |
| Ch 2 Literature Review and Theoretical Background | 5.5 | absorption mechanism, α/β phases, PCT, Van't Hoff; engineering properties; AB5/AB2/AB/Mg/complex families; ML for materials, descriptors, RF, applicability domain, leakage; gap; summary |
| Ch 3 Datasets and Methodology | 5.5 | ML-HydPARK, Purdue toolbox, audit, sign conventions, cleaning, composition union, features, grouped CV |
| Ch 4 Machine Learning Model Development | 5.5 | target, RF, nested CV, metrics, baselines, leave-family-out, applicability domain, intervals, interpretation |
| Ch 5 Thermodynamic Analysis | 4 | Van't Hoff, representative materials, heat, hysteresis, multi-plateau, PCI consistency, ML-based estimates |
| Ch 6 Application-Specific Screening and Software Platform | 4.5 | constraints, evidence classes, scoring, Pareto, sensitivity; Discovery Lab; Requirement Designer; architecture |
| Ch 7 Results and Discussion | 4.5 | ML results, thermodynamic results, two scenarios, interpretation, critical discussion |
| Ch 8 Conclusion and Future Work | 2 | summary, engineering insights, proposed experiments (clearly labelled) |
| References | 2.5 | about 30–35 verified sources |
| **Total** | **≈ 46** | trimmed to about 44 in Stage 5 if needed |
| Appendices (outside the target) | — | A: 38 feature definitions; B: full CV / family tables; C: data-quality flags; D: Lab candidate lists; E: scenario tables; F: proposed characterisation matrix |

## 3. Evidence map (chapter → sources → verified numbers)

| Ch | Source files | Verified numbers to use |
|---|---|---|
| 3 | `reports/data_audit.md`, `hydpark_dataset_summary.md`, `purdue_dataset_summary.md`, `dataset_comparison.md`, `results/tables/composition_overlap.csv`, `cross_dataset_agreement_stats.csv` | HydPARK 772 rows in 4 blocks (397/25/15/335); Purdue 337 `.mh` files (AB5 146, AB2 106, AB 29, SS 24, AB3 14, A2B7 8, Misc 5, Mg 4, Complex 1); 68 PCI files, all digitised; 102 Sandia-unverified references; 49 pseudo-element alloys; 12 multi-plateau; 248 of 288 Purdue compositions shared with HydPARK; HydPARK ΔS back-calculated for 395 of 403 rows; inter-source MAE 2.2 kJ/mol (independently referenced pairs); union 725 compositions (276 Purdue, 449 HydPARK) |
| 3 | `reports/feature_engineering.md`, `results/tables/feature_list.csv` | 40 descriptors, 2 pruned (r > 0.95), 38 used; 659 near-composition CV groups (L1 ≤ 0.02) |
| 4 | `results/models/dH_predictor_manifest.json`, `results/metrics/*.csv`, `reports/ml_results.md` | RF: 300 trees, max_features 0.33, min_samples_leaf 1, random_state 0. CV MAE 5.26 ± 0.14 kJ/mol, RMSE 10.32, R² 0.715. GB 5.30 / R² 0.744. Ridge 7.09. Family-median 8.88. Mean 12.26. Hold-out RF 5.55 (R² 0.73). Ungrouped CV 5.12 vs grouped 5.26. Leave-family-out: AB5 5.86 vs mean 5.10; SS 20.98 vs 12.33; Mg 14.51 vs 36.01. Calibration MAE 2.62 (L1 ≤ 0.05) → 16.89 (> 0.5); domain limit L1 ≤ 0.15. wt% model 0.247 vs physics baseline 0.286 (not used). Top permutation importances: vol_mean 3.57, frac_hydride_former 2.10, vec_std 1.31 |
| 5 | `reports/thermodynamics.md`, `pci_kinetics.md`, `results/tables/vant_hoff_*.csv`, `pci_vant_hoff_fits.csv` | LaNi5: 32.15 kJ/mol, 112.8 J/(mol K), 1.84 bar at 25 °C, T(1 bar) 11.6 °C, 15.95 MJ/kg H2 (13.3% LHV). TiFe: 4.16 bar, −8.3 °C. TiCrMn: 107.5 bar. MgH2: 301.7 °C, 38.84 MJ/kg (32.4%). Mg2Ni: 255 °C. NaAlH4: 99.5 / 29.9 °C (two plateaus, confirmed by the 433 K PCI curve: ratios 0.74, 0.95). PCI-fit ΔH median deviation 1.76 kJ/mol. 85% of single-plateau materials reach 1 bar at ≤ 80 °C. ML band ≈ 100 K (≈ 65 K from ΔH, 25–43 K from ΔS) |
| 6–7 | `reports/screening.md`, `platform_architecture.md`, `platform_demo_scenarios.md`, `src/app/*.py` | Scenario 1 (mobile): 278 fail, 4 unranked (insufficient evidence), 55 ranked; top: Ti0.9Zr0.2Mn1.4Cr0.4V0.2, Ti0.9Zr0.2Mn1.8V0.2, V0.855Ti0.095Fe0.05. Scenario 2 (120 °C industrial buffer): 222 fail, 6 unranked, 109 ranked; top: Ti0.9Zr0.1Mn1.4, Zr0.7Ti0.3CrFe, TiFe0.9Al0.1. Top-5 overlap between scenarios: 0 |
| 8 | `reports/synthesis_characterization_plan.md` | 9 proposed alloys plus 2 blind ML tests (LaNi4.2Al0.8, predicted 38.7 [34.3–41.6] kJ/mol; TiFe0.75Mn0.25, predicted 32.0 [25.7–37.8]). Labelled **proposed only** |

**Discrepancy found:** TiCrMn pressure at 25 °C is 108 bar in the Phase 3 table (R = 8.314, 3 significant figures) and 107.5 bar in Phase 6 (CODATA R, `vant_hoff.py`). **Phase 6 is authoritative.** All thermodynamic numbers in the report will come from the Phase 6 tables.

## 4. Figures (≈ 16 in the main text, rest in appendices)

| # | Figure | Status |
|---|---|---|
| 1.1 | Project workflow: composition → descriptors → ML ΔH → Van't Hoff → constraints → recommendation | **new** schematic (drawn from the code's actual data flow) |
| 2.1 | Absorption/desorption mechanism and schematic PCT curve (α, α+β, β) | **new** schematic, labelled illustrative |
| 3.1 | Material-class distribution in both datasets | existing fig01 |
| 3.2 | Data-preparation workflow (audit → flags → union) | **new** schematic |
| 3.3 | Missing-data map | existing fig10 (or appendix) |
| 4.1 | Model comparison (CV MAE / R²) | existing fig11 |
| 4.2 | Parity and residual plots (hold-out) | existing fig12 |
| 4.3 | Leave-one-family-out | existing fig15 |
| 4.4 | Error vs nearest-neighbour distance (applicability domain) | **new** plot from `applicability_domain_calibration.csv` |
| 4.5 | Permutation importance | existing fig14 |
| 5.1 | Van't Hoff lines of representative materials | existing fig17 |
| 5.2 | Operating windows and reaction heat | existing fig18 |
| 5.3 | Heat vs T(1 bar) | existing fig19 |
| 5.4 | Digitised PCI isotherms | existing fig21 |
| 5.5 | ML-estimated substitution series (labelled ESTIMATE) | existing fig20 |
| 6.1 | Software architecture and data flow | **new** schematic |
| 6.2 | Screening workflow (hard constraints → score → Pareto → evidence) | **new** schematic |
| 6.3 | One or two app screenshots (Lab, Designer) | **new** captures from the running app |
| 7.1 | Scenario comparison: top-ranked materials and Pareto fronts for mobile vs industrial | **new** plot from the real demo outputs |

New plots are produced only from project data. Schematics are labelled as schematic.

## 5. Tables (≈ 12 in the main text)

Dataset comparison; property availability; family distribution; sign conventions and units; descriptor groups (full list in an appendix); model hyperparameters and grids; CV/hold-out/baseline metrics; leave-family-out; applicability calibration; representative thermodynamics; scenario requirements; scenario recommendations; limitations and the measurement each one requires.

## 6. References (all to be verified individually in Stage 3 before citing)

Candidates, each already used in the project reports or standard:
* Sandrock (1999) J. Alloys Compd. 293–295, 877; Schlapbach & Züttel (2001) Nature 414, 353; Züttel (2003) Mater. Today 6(9), 24; Sakintuna, Lamari-Darkrim, Hirscher (2007) Int. J. Hydrogen Energy 32, 1121.
* Lundin, Lynch, Magee (1977) J. Less-Common Met. 56, 19; Reilly & Wiswall (1974) Inorg. Chem. 13, 218; Bogdanović & Schwickardi (1997) J. Alloys Compd. 253–254, 1; Huot et al. (1999) J. Alloys Compd. 293–295, 495.
* ML-HydPARK: Witman et al. (2020) J. Phys. Chem. Lett. 11, 40; Sandia/DOE HydPARK database; Purdue Metal Hydride Toolbox (GitHub, PurdueH2Lab).
* Breiman (2001) Mach. Learn. 45, 5; Pedregosa et al. (2011) JMLR 12, 2825; Ong et al. (2013) Comput. Mater. Sci. 68, 314 (pymatgen); Ward et al. (2016) npj Comput. Mater. 2, 16028; Zhang et al. (2008) Adv. Eng. Mater. (size mismatch δ); Broom (2011) *Hydrogen Storage Materials* (Springer); US DOE onboard-storage technical targets; NIST H2 data.

Any reference that cannot be confirmed (title, authors, year, volume, pages, DOI) will be flagged to you rather than cited.

## 7. Production approach

* Build the report **inside the official template** with `python-docx` (added to the project environment), so the template's page size, margins, styles, title page, certificate and footer are used exactly.
* Generate the TOC, list of figures and list of tables as Word fields, with captions using the Caption style (number + text).
* Render to PDF with LibreOffice, then check pages visually and count them.
* Keep the sources in `report/`: build script, figures, a `references.bib`-style list, this evidence map, appendices.
* Stage 4: run `/humanizer` on prose only, then diff the result against the verified draft to confirm that numbers, citations and claims are unchanged.

## 8. Questions for you (placeholders are used until you answer)

* **Q1 Title:** has a title been approved? If not, the working title is "Machine Learning-Assisted Discovery and Application-Specific Screening of Metal Hydride Materials for Hydrogen Storage".
* **Q2 Extra preliminary pages:** the official template has no Declaration, Abstract or Abbreviations page. My recommendation is to add an Abstract and an Abbreviations & Symbols list (both standard and helpful), and a Declaration only if your department asks for one.
* **Q3 Citation style:** APA or Vancouver. My recommendation is Vancouver (numbered [1], compact for an engineering report).
* **Q4 Personal details:** student name, roll number, supervisor name and designation, submission month/year. These stay as placeholders if not given.
* **Q5 AI-assistance disclosure:** this project's code and analysis were developed with an AI coding assistant. Many institutes now require such use to be disclosed. I recommend a short factual statement in the Acknowledgements (or a separate note) that describes the tools used. Please confirm what IIT Guwahati or your supervisor requires.
