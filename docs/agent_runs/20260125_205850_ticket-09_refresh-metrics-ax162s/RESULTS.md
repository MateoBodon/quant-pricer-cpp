# Results

- Created repo-local `.venv` and installed `requirements-dev.txt`.
- Release build completed; FAST tests passed in the local build.
- `REPRO_FAST=1 WRDS_USE_SAMPLE=1 ./scripts/reproduce_all.sh` succeeded (FAST+SLOW; MARKET skipped) and regenerated `docs/artifacts/manifest.json`, `docs/artifacts/metrics_summary.{md,json}`, and `docs/validation_pack.zip`.
- Updated `project_state/CURRENT_RESULTS.md` and `PROGRESS.md` to the snapshot generated at 2026-01-25T21:13:43.226947+00:00 (manifest sha 653b9e8e07364e5c682dabed5bae856a850c1136).
- Generated GPT bundle: `docs/gpt_bundles/20260125T212515Z_ticket-09_refresh-metrics-ax162s_20260125_205850_ticket-09_refresh-metrics-ax162s.zip`.
- Notes: first reproduce_all run failed on `metrics_snapshot_fast` due to stale `CURRENT_RESULTS.md`; reran after updating the snapshot. Matplotlib emitted cache-dir warnings for `/home/codex/.config`, and Heston MC diagnostic warnings were emitted (expected).
