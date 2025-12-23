# Results

- Ran a single-date WRDS local smoke using `WRDS_LOCAL_ROOT=/Volumes/Storage/Data/wrds` with `--trade-date 2024-06-14` and `--fast`, writing outputs to `docs/artifacts/wrds_local` (gitignored).
- Local data was used (`source_today=local`, `source_next=local`).
- No changes to canonical artifacts under `docs/artifacts/` and no metrics snapshot updates; this run is for local smoke only.

Local outputs (untracked):
- `docs/artifacts/wrds_local/spx_2024-06-14_surface.csv`
- `docs/artifacts/wrds_local/spx_2024-06-17_surface.csv`
- `docs/artifacts/wrds_local/heston_fit.json`
- `docs/artifacts/wrds_local/heston_fit.png`
- `docs/artifacts/wrds_local/heston_fit_table.csv`
- `docs/artifacts/wrds_local/wrds_heston_insample.png`
- `docs/artifacts/wrds_local/wrds_heston_oos.png`
- `docs/artifacts/wrds_local/wrds_heston_hedge.png`
