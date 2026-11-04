# Phase 1 data audit

All numbers are produced by `src/data/run_audit.py`. Raw files are untouched.

## Files found

| Item | Location | Status |
|---|---|---|
| Purdue Metal Hydride Toolbox (MATLAB, git HEAD 68e445f) | `~/Documents/MATLAB/MetalHydrideToolbox` | Found. Snapshot in `data/raw/purdue/MetalHydrideToolbox/` (179 files were iCloud placeholders and are now downloaded) |
| `.mh` material files | `data/*.mh` | 337 |
| PCI isotherms | `data/supporting/*_PCI.csv` | 68 |
| MATLAB classes | `@MetalHydride` (18 .m), `@Element`, `@KineticsModel`, `@Reference` | Read and used to fix conventions |
| Toolbox docs | `README.md`, `doc/Demo.m`, `doc/dbSummary.csv`, `doc/refs.txt`, `doc/hydrideRefs.bib` | Found |
| Excel export (prior verbatim extraction) | `~/Downloads/MetalHydrideToolbox_database_337 (1).xlsx` (54 cols) and `...337.xlsx` (50 cols) | Used only as a cross-check |
| ML-HydPARK v0.0.5 | `~/Downloads/ML-HYDPARK_v0.0.5.csv` | Found, 772 rows |
| Untracked user scratch files in toolbox | `untitled*.mlx`, `doc1.m` | Not part of the toolbox; not copied |

Nothing that was required is missing.

## Key findings that change the analysis plan

1. **HydPARK has 772 rows in 4 appended blocks, not ~420.** The block number is kept
   as provenance.
2. **Opposite sign conventions.** Purdue: negative formation dH/dS in J/mol H2.
   HydPARK: positive magnitudes, dH in kJ/mol H2. Both were verified against the
   Van't Hoff relation, so the analytical copies are converted to one convention
   (positive desorption magnitudes, kJ/mol H2).
3. **HydPARK dS is back-calculated** from dH and one (T, P) point for
   395 rows. Peq(25 C), ln Peq(25 C) and HtoM are all derived. None of them may
   be used as features for dH or wt% prediction.
4. **The Purdue "H/M" input is H per formula unit**, not per metal atom (verified in
   `ReadThermo.m` and by the value ranges). wt% derived from it is reproduced with
   the toolbox's own molar masses and flagged `capacity_basis = derived_from_HM_per_formula_unit`.
5. **Purdue capacity is mostly of unstated definition.** Only
   8 comments say "reversible", and 17 are assumed, approximate,
   theoretical or unconfirmed.
6. **The toolbox fills missing properties with type defaults.** Defaults are excluded here.
   Density is present for 37, Cp for 28, keff for 14, and kinetics for 31 (abs) / 26 (des) materials.
7. **All 68 PCI files are digitized from literature figures**; 14 were also shifted by the curator.
8. **102 Purdue materials cite unverified SandiaDBRef placeholders**, and 51 have ambiguous compositions
   (Mm/Lm/Vf, trade names, approximate notes, NaAlH4 written as NaAlH).

## Previously reported statistics vs. verified

| Statistic | Reported | Verified | Note |
|---|---|---|---|
| Purdue .mh files | ~337 | 337 | |
| AB5 / AB2 / AB / SS / AB3 / A2B7 / Misc / Mg / Complex | 146/106/29/24/14/8/5/4/1 | 146/106/29/24/14/8/5/4/1 | matches |
| Entries with dH and dS | ~325 | 337 (all); 325 single-plateau | 12 multi-plateau |
| Direct reversible capacity | ~223 | 223 stated wt% + 114 via H/M; 8 explicitly "reversible" | definition mostly unstated |
| PCI files | ~68 | 68 | all digitized |
| Kinetics abs / des | 31 / 26 | 31 / 26 | |
| Density / Cp / keff | 37 / 28 / 14 | 37 / 28 / 14 | |
| Sandia placeholder refs | ~102 | 102 | |
| Ambiguous formulas | ~49 | 49 pseudo-element; 51 incl. trade names/approx./NaAlH | |
| HydPARK records | ~420 | 772 | 4 blocks |

## Outputs

* `data/interim/purdue_extracted.csv`: 337 x 103, raw values plus flags
* `data/interim/purdue_pci_index.csv`: index of the 68 PCI files
* `data/interim/hydpark_flagged.csv`: 772 x 30, raw columns plus block plus flags
* `results/tables/material_class_distribution.csv`
* `results/tables/missing_value_summary.csv`
* `results/tables/purdue_parser_vs_xlsx_crosscheck.csv`
* `reports/purdue_dataset_summary.md`, `reports/hydpark_dataset_summary.md`

## Material class distribution

| dataset | material_class | n_records | pct_of_dataset |
|---|---|---|---|
| Purdue | AB5 | 146 | 43.3 |
| Purdue | AB2 | 106 | 31.5 |
| Purdue | AB | 29 | 8.6 |
| Purdue | SS | 24 | 7.1 |
| Purdue | AB3 | 14 | 4.2 |
| Purdue | A2B7 | 8 | 2.4 |
| Purdue | Misc | 5 | 1.5 |
| Purdue | Mg | 4 | 1.2 |
| Purdue | Complex | 1 | 0.3 |
| HydPARK | AB2(C14) | 268 | 34.7 |
| HydPARK | AB2 | 119 | 15.4 |
| HydPARK | AB5 | 106 | 13.7 |
| HydPARK | AB2(C15) | 67 | 8.7 |
| HydPARK | SS | 60 | 7.8 |
| HydPARK | MIC | 52 | 6.7 |
| HydPARK | AB | 33 | 4.3 |
| HydPARK | Mg | 32 | 4.1 |
| HydPARK | (missing) | 25 | 3.2 |
| HydPARK | A2B | 10 | 1.3 |

## Missing values

| dataset | property | n_present | n_missing | pct_present | toolbox_substitutes_default_if_missing |
|---|---|---|---|---|---|
| Purdue | capacity (wt% stated) | 223 | 114 | 66.2 | False |
| Purdue | capacity (H/M stated) | 114 | 223 | 33.8 | False |
| Purdue | capacity (either; wt% derived by toolbox) | 337 | 0 | 100 | False |
| Purdue | desorption dH | 337 | 0 | 100 | False |
| Purdue | desorption dS | 337 | 0 | 100 | False |
| Purdue | absorption dH | 83 | 254 | 24.6 | True |
| Purdue | absorption dS | 83 | 254 | 24.6 | True |
| Purdue | hysteresis ln(Pa/Pd) | 42 | 295 | 12.5 | True |
| Purdue | critical temperature Tc | 12 | 325 | 3.6 | True |
| Purdue | plateau slope | 115 | 222 | 34.1 | True |
| Purdue | density rho | 37 | 300 | 11 | True |
| Purdue | heat capacity Cp | 28 | 309 | 8.3 | True |
| Purdue | thermal conductivity keff | 14 | 323 | 4.2 | True |
| Purdue | absorption kinetics Ea | 31 | 306 | 9.2 | True |
| Purdue | desorption kinetics Ea | 26 | 311 | 7.7 | True |
| Purdue | PCI isotherm file | 68 | 269 | 20.2 | False |
| HydPARK | Material_Class | 747 | 25 | 96.8 | False |
| HydPARK | Composition_Formula | 772 | 0 | 100 | False |
| HydPARK | Hydrogen_Weight_Percent | 741 | 31 | 96 | False |
| HydPARK | Heat_of_Formation_kJperMolH2 | 772 | 0 | 100 | False |
| HydPARK | Temperature_oC | 412 | 360 | 53.4 | False |
| HydPARK | Pressure_Atmospheres_Absolute | 403 | 369 | 52.2 | False |
| HydPARK | Entropy_of_Formation_JperMolH2perK | 772 | 0 | 100 | False |
| HydPARK | Equilibrium_Pressure_25C | 770 | 2 | 99.7 | False |
| HydPARK | LnEquilibrium_Pressure_25C | 772 | 0 | 100 | False |
| HydPARK | HtoM | 741 | 31 | 96 | False |
| HydPARK | Reference | 373 | 399 | 48.3 | False |
