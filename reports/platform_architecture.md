# METAL HYDRIDE AI: implementation architecture

## 1. Reused, unchanged
| Component | Used for |
|---|---|
| `results/models/dH_predictor_bundle.joblib` (the RF from `dH_final.joblib`, not retrained) | every ΔH prediction |
| `src/app/predictor.py`: parsing, `comp_key`, the 38-descriptor featuriser, nearest-neighbour distance, calibrated 80% interval, domain limit L1 ≤ 0.15 | Property Predictor, Discovery Lab |
| `src/thermodynamics/vant_hoff.py`: `peq_bar`, `T_at_P`, heat per kg H2 | all thermodynamic numbers |
| `results/tables/screening_candidates.csv` and `vant_hoff_purdue.csv` (Phases 6/8) | experimental material pool, flags, plateaus |
| `results/metrics/*`, `results/tables/*` | performance and evidence pages (read-only) |

## 2. New modules
| Module | Responsibility (no Streamlit inside) |
|---|---|
| `src/app/generator.py` | alloy-system presets (A-site / B-site templates), constrained composition grids, seeded sampling, duplicate removal |
| `src/app/discovery.py` | evaluates generated candidates: ML ΔH + interval + domain, Van't Hoff estimate with assumed ΔS, rejection reasons, ranking, Pareto |
| `src/app/recommend.py` | application requirements, experimental pool, hard constraints (pass / fail / unknown), weighted scoring, Pareto, evidence class, explanations, export |
| `src/app/ui.py` | theme CSS, page header, small reusable components |
| `src/app/pages*.py` | page renderers; `app.py` handles navigation only |

## 3. Data flow
```
user composition ─► predictor.parse ─► comp_key ─► featurise(38) ─► RF ─► ΔH ─► NN distance ─► interval / domain
generator(preset, ranges, step, seed) ─► compositions ─► predictor (as above) ─► discovery: + assumed ΔS ─► Van't Hoff estimate ─► reject / rank / Pareto
requirements ─► recommend: experimental pool (Purdue .mh ΔH, ΔS, reported wt%, flags)
                         ─► hard constraints ─► score passing ─► Pareto ─► evidence class + explanation ─► CSV
              (ML candidates from the Lab are evaluated separately and shown in a separate section)
```

## 4. Application structure
* One `app.py` with an 8-page navigation: Overview, Property Predictor, Candidate Discovery Lab, Application Requirement Designer,
  Material Comparison, Thermodynamic Explorer, Model Performance, Dataset & Evidence Explorer.
* Existing pages are kept and restyled. A custom theme is set in `.streamlit/config.toml`, and CSS lives in `ui.py`.

## 5. Testing
Engines are unit-tested without Streamlit:
* generator: validity, ranges, reproducibility, duplicates;
* discovery: consistency with the single-composition predictor;
* recommend: constraints, heat, missing data, weights, Pareto, classification, export.

Every page is exercised headlessly with `streamlit.testing.AppTest`, then checked manually in a browser.
