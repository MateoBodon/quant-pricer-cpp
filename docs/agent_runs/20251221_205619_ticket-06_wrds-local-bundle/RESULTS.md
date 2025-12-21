# Results

- Ran the WRDS pipeline in explicit local mode with `WRDS_LOCAL_ROOT=/Volumes/Storage/Data/wrds` and `--output-root docs/artifacts/wrds_local` (completed successfully).
- Local artifacts were written under `docs/artifacts/wrds_local/`, including aggregated CSVs/PNGs and per-date outputs for 2020-03-16, 2020-03-17, 2022-06-13, 2022-06-14, and 2024-06-14.
- `docs/artifacts/manifest.json` was updated by the pipeline and now contains `wrds_local` paths (working tree is dirty); left uncommitted to avoid mixing local data metadata with the sample bundle.
- No code or config changes were made in this run.

## Artifacts (local-only; do not commit)
- `docs/artifacts/wrds_local/`
- `docs/artifacts/wrds_local/per_date/2020-03-16/`
- `docs/artifacts/wrds_local/per_date/2020-03-17/`
- `docs/artifacts/wrds_local/per_date/2022-06-13/`
- `docs/artifacts/wrds_local/per_date/2022-06-14/`
- `docs/artifacts/wrds_local/per_date/2024-06-14/`

## Notes
- Outputs are derived from local WRDS data; per policy, they are not committed.
- Sources consulted: none.
