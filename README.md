# Machine Learning-Assisted Discovery and Application-Specific Screening of Metal Hydride Materials for Hydrogen Storage

B.Tech project, School of Energy Science and Engineering, IIT Guwahati.
Avinash (230151005), supervised by Dr. Saket Verma.

Metal hydrides store hydrogen at a few bar near room temperature. Whether an alloy suits an application depends
mainly on its desorption enthalpy ΔH, which together with ΔS fixes the temperature at which hydrogen is released.
This project:

1. **audits** two public hydride databases (Purdue Metal Hydride Toolbox, ML-HydPARK v0.0.5) and builds a clean,
   composition-level dataset of 725 alloys;
2. trains a **Random Forest** on 38 composition descriptors to predict ΔH, with grouped, nested cross-validation,
   an 80% prediction interval and an applicability-domain flag;
3. converts ΔH and ΔS into **operating windows and heat demand** with the Van't Hoff relation;
4. **screens** the measured alloys against mobile and stationary requirements (hard constraints, weighted scores,
   Pareto fronts, evidence classes, sensitivity analysis);
5. packages all of this in an interactive **Streamlit app**, "METAL HYDRIDE AI".

No laboratory work was done. A synthesis and characterisation plan is proposed in the report.

## Key results

| | |
|---|---|
| ML dataset | 725 compositions (276 Purdue, 449 HydPARK values); 248 of 288 parseable Purdue compositions also occur in HydPARK, so there is no external validation set |
| ΔH model | Random Forest MAE **5.26 ± 0.14 kJ/mol** (R² 0.72), nested grouped CV; family-median baseline 8.88; inter-source scatter ≈ 2.2 |
| Reliability | MAE 2.6 kJ/mol near the training data, 16.9 far from it; domain limit L1 ≤ 0.15; the model fails when a whole family is held out |
| Thermodynamics | LaNi₅: 1.84 bar at 25 °C, 1 bar at 11.6 °C, 15.95 MJ/kg H₂; MgH₂ needs 302 °C; 85% of single-plateau alloys reach 1 bar at ≤ 80 °C |
| Screening | mobile: Ti-based AB₂/AB alloys lead; stationary: TiFe-type and Ti–Zr–Mn alloys. Rankings are material-level screening results, not recommendations for use |

**To run it on your own computer, follow [RUNNING.md](RUNNING.md)** (install, start the app, what to try, troubleshooting; printable copy: [Running_Guide.pdf](Running_Guide.pdf)).

## Documents

| File | Contents |
|---|---|
| [`report/BTP_Report.pdf`](report/BTP_Report.pdf) / [`.docx`](report/BTP_Report.docx) | the B.Tech report (official IITG format, 44 pages + appendices); built by `python -m report.build_report` |
| [`viva-guide/Viva_Guide_Metal_Hydride_Project.pdf`](viva-guide/Viva_Guide_Metal_Hydride_Project.pdf) | 35-page explanation of every component, with likely viva questions and answers |
| [`reports/`](reports/) | phase-by-phase technical notes (audit, comparison, EDA, features, ML, thermodynamics, PCI, screening, plan, platform) |
| [`report/references.md`](report/references.md) | bibliography with verification status |

## Repository layout

```
app.py                 Streamlit entry point (8 pages)
src/data/              Phase 1-2: parsing, audit, cleaning, cross-dataset comparison
src/features/          Phase 4: composition descriptors
src/models/            Phase 5: training, nested grouped CV, model bundle
src/thermodynamics/    Phase 6-7: Van't Hoff, PCI isotherms, kinetics
src/screening/         Phase 8-9: constraints, rankings, sensitivity, experimental plan
src/app/               platform engines (predictor, generator, discovery, recommend, pareto) and pages
src/visualization/     all figures
data/interim, data/processed   derived data (raw data not included, see data/raw/README.md)
results/               figures, tables, metrics, saved model + manifest
report/                report sources (content/*.md), figures, build scripts, output
viva-guide/            viva guide sources (HTML + KaTeX) and PDF
tests/                 77 pytest tests
```

## Data sources

The raw datasets are not redistributed here; [`data/raw/README.md`](data/raw/README.md) explains how to obtain them.

* Purdue Metal Hydride Toolbox: https://github.com/PurdueH2Lab/MetalHydrideToolbox (Voskuilen TG, Waters EL, Pourpoint TL.
  Int J Hydrogen Energy 2014;39:13240–54).
* ML-HydPARK v0.0.5: https://zenodo.org/records/10680097 (Witman M et al. J Phys Chem Lett 2020;11:40–7).

## Setup and run

```bash
python3 -m venv .venv && .venv/bin/pip install -r requirements.txt
.venv/bin/python -m src.data.run_audit      # Phase 1: extraction + audit (needs data/raw, see data/raw/README.md)
.venv/bin/python -m src.data.clean          # Phase 2: cleaned copies
.venv/bin/python -m src.data.compare        # Phase 2: overlap, comparison, dH union
.venv/bin/python -m src.data.compare_report # Phase 2: reports/dataset_comparison.md
MPLCONFIGDIR=.mplcache .venv/bin/python -m src.visualization.eda   # Phase 3: figures + reports/eda_summary.md
.venv/bin/python -m src.features.build      # Phase 4: feature tables + reports/feature_engineering.md
.venv/bin/python -m src.models.train        # Phase 5: nested grouped CV (~6 min) -> results/metrics, results/models
.venv/bin/python -m src.models.report       # Phase 5: reports/ml_results.md
MPLCONFIGDIR=.mplcache .venv/bin/python -m src.visualization.ml_plots  # Phase 5: fig11-fig16
.venv/bin/python -m src.thermodynamics.analysis   # Phase 6: Van't Hoff tables (+ ML-estimate series)
.venv/bin/python -m src.thermodynamics.report     # Phase 6: reports/thermodynamics.md
MPLCONFIGDIR=.mplcache .venv/bin/python -m src.visualization.thermo_plots  # Phase 6: fig17-fig20
.venv/bin/python -m src.thermodynamics.pci_kinetics   # Phase 7: PCI plateaus, fits, kinetics tables
.venv/bin/python -m src.thermodynamics.pci_report     # Phase 7: reports/pci_kinetics.md
MPLCONFIGDIR=.mplcache .venv/bin/python -m src.visualization.pci_plots  # Phase 7: fig21-fig23
.venv/bin/python -m src.screening.screen     # Phase 8: constraints, rankings, sensitivity
.venv/bin/python -m src.screening.report     # Phase 8: reports/screening.md
MPLCONFIGDIR=.mplcache .venv/bin/python -m src.visualization.screening_plots  # Phase 8: fig24-fig26
.venv/bin/python -m src.screening.plan       # Phase 9: reports/synthesis_characterization_plan.md (proposed work)
.venv/bin/python -m pytest -q tests
```

## METAL HYDRIDE AI (interactive platform)

*Intelligent Discovery & Application-Specific Hydrogen Storage Materials Selection.* A Streamlit app with 8 pages:

| Page | What it does |
|---|---|
| Overview | model metrics (read from files), dataset coverage, workflow shortcuts, session activity |
| Property Predictor | live ΔH, 80% interval, applicability domain, 5 nearest experimental neighbours, thermodynamic estimate |
| Candidate Discovery Lab | constrained alloy grids (A/B-site templates or free fractions), ML screening, rejection reasons, ranking, Pareto front, CSV export |
| Application Requirement Designer | 7-step requirements → hard constraints (pass / fail / unknown) → weighted ranking, Pareto, evidence class, explanations, weight sensitivity, CSV/JSON export |
| Material Comparison | experimental properties with provenance; missing data shown as missing |
| Thermodynamic Explorer | Van't Hoff estimate with ΔS sensitivity and experimental neighbour lines |
| Model Performance | CV, hold-out, parity/residuals, leave-family-out, applicability calibration |
| Dataset & Evidence Explorer | dataset overlap, evidence flags, missing data, provenance legend |

Engines (no Streamlit): `src/app/generator.py`, `src/app/discovery.py`, `src/app/recommend.py` and `src/app/pareto.py`.
Architecture: `reports/platform_architecture.md`. The demonstration scenarios (`src/app/demo.py`) write
`reports/platform_demo_scenarios.md`.

```bash
cd Hydrogen-Storage-Project
python3 -m venv .venv && .venv/bin/pip install -r requirements.txt
.venv/bin/python -m src.models.export_bundle   # only if results/models/dH_predictor_bundle.joblib is missing
.venv/bin/streamlit run app.py                 # opens http://localhost:8501
```

* Model: the CV-selected Random Forest saved by `src/models/train.py` (`results/models/dH_final.joblib`). It is **not retrained**.
  `src/models/export_bundle.py` packages it, unchanged, with the training compositions, the applicability calibration and
  the ΔS assumption into `results/models/dH_predictor_bundle.joblib`. SHA-256 hashes and package versions are recorded in
  `results/models/dH_predictor_manifest.json`.
* Prediction core (no Streamlit): `src/app/predictor.py`. UI: `app.py`, `src/app/pages*.py`, `src/app/ui.py`, `src/app/data.py`,
  `.streamlit/config.toml`.
* Tests: `tests/test_app_predictor.py` covers parsing and consistency with the training pipeline. `tests/test_platform.py` covers
  generator, discovery, constraints, scoring, Pareto, evidence, export and all page workflows.

## Conventions used in derived data

* dH, dS are reported as **positive desorption magnitudes**: dH in kJ/mol H2, dS in J/(mol H2 K).
  Van't Hoff: `ln(P/P0) = -dH/(RT) + dS/R`, with P0 = 1 atm and R = 8.314 J/(mol K).
* Purdue raw values are negative formation values in J/mol H2. They are converted only in the derived copies.
* Missing means NaN. The toolbox's type-default substitutions are not used as data.

## Progress

| Phase | Status | Main outputs |
|---|---|---|
| 1. Extraction and audit | done | `reports/data_audit.md`, `reports/purdue_dataset_summary.md`, `reports/hydpark_dataset_summary.md`, `results/tables/*` |
| 2. Cleaning and cross-dataset comparison | done | `data/processed/{purdue,hydpark}_cleaned.csv`, `data/processed/dH_union_by_composition.csv`, `reports/dataset_comparison.md`, `results/tables/{composition_overlap,cross_dataset_comparison}.csv` |
| 3. EDA | done | `results/figures/fig01–fig10` (PNG + PDF), `reports/eda_summary.md`, `results/tables/eda_*.csv` |
| 4. Composition features | done | `data/processed/features_dH.csv` (725), `features_wt.csv` (181), `reports/feature_engineering.md`, `results/tables/feature_*.csv` |
| 5. ML (dH, wt%) | done | `reports/ml_results.md`, `results/metrics/*`, `results/models/dH_final.joblib`, `fig11–fig16`. ΔH: RF MAE 5.26 ± 0.14 kJ/mol (R² 0.72) vs family-median 8.88; does not extrapolate to unseen families. wt%: barely beats physics baseline → not used |
| 6. Van't Hoff thermodynamics | done | `reports/thermodynamics.md`, `results/tables/vant_hoff_*.csv`, `applicability_domain_calibration.csv`, `fig17–fig20` |
| 7. PCI / kinetics | done | `reports/pci_kinetics.md`, `results/tables/pci_*.csv`, `kinetics_purdue.csv`, `fig21–fig23` |
| 8. Stationary vs mobile screening | done | `reports/screening.md`, `results/tables/screening_*.csv`, `fig24–fig26` |
| 9. Synthesis and characterization plan | done (proposed work only, no experiments) | `reports/synthesis_characterization_plan.md`, `results/tables/proposed_experimental_candidates.csv`, `characterisation_matrix.csv` |
| 10. Documentation and B.Tech report | done (slides pending) | `report/BTP_Report.pdf` (official IITG template, 44 pages + appendices), `viva-guide/`, `report/README.md`, `report/references.md`; rebuild with `python -m report.build_report` |
