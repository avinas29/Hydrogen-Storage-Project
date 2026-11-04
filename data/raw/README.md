# Raw data (not included)

The two source datasets are third-party and have no clear redistribution licence, so they are not committed.
Everything from Phase 2 onwards runs from the derived files in `data/interim/` and `data/processed/`, which are included.
To rerun Phase 1 (`python -m src.data.run_audit`) from scratch, place the files here:

| Path | Source |
|---|---|
| `data/raw/purdue/MetalHydrideToolbox/` | Purdue Metal Hydride Toolbox: `git clone https://github.com/PurdueH2Lab/MetalHydrideToolbox data/raw/purdue/MetalHydrideToolbox` (this project used commit `68e445f`) |
| `data/raw/hydpark/ML-HYDPARK_v0.0.5.csv` | ML-HydPARK v0.0.5, Zenodo record 10680097: https://zenodo.org/records/10680097 |
| `data/raw/purdue/MetalHydrideToolbox_database_337 (1).xlsx` | optional: an earlier private Excel export of the toolbox, used only for a cross-check. Without it the saved cross-check table is reused. |

Files in `data/raw/` are never modified by the code.
