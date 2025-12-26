- Canonicalized default output paths in artifact-related scripts to `docs/artifacts/` (qmc_vs_prng_equal_time, parity_checks, greeks_reliability, american_consistency, Heston calibration/series, report), keeping manifest entries on the canonical root.
- Regenerated reproducible artifacts via `REPRO_FAST=1 WRDS_USE_SAMPLE=1 ./scripts/reproduce_all.sh`; `docs/artifacts/manifest.json`, `docs/artifacts/metrics_summary.{md,json}`, and `docs/validation_pack.zip` updated (metrics snapshot generated at 2025-12-26T20:16:23.004584+00:00).
- Synced `project_state/CURRENT_RESULTS.md` to the latest metrics snapshot and verified the non-canonical `artifacts/` root stayed untouched (`git status --short artifacts` returned empty).

Evidence:
- Canonical outputs: `docs/artifacts/manifest.json`, `docs/artifacts/metrics_summary.md`, `docs/artifacts/metrics_summary.json`, `docs/validation_pack.zip`.
- Non-canonical root check: `git status --short artifacts` returned no changes.

Caveats:
- `scripts/heston_qe_vs_analytic.py` emitted MC-vs-analytic deviation warnings during reproduce_all (diagnostic-only output).
- OpenMP not detected; `RngDeterminism.CounterRngThreadInvariant` skipped in FAST.
- reproduce_all ran FAST + SLOW (MARKET skipped) and wrote SLOW logs under `docs/artifacts/logs/` (untracked).
- First reproduce_all attempt failed at `metrics_snapshot_fast` because CURRENT_RESULTS lagged the snapshot; fixed by updating CURRENT_RESULTS and rerunning.

Review checklist:
- Scope: `git diff main...HEAD --stat` shows only ticket-01 changes (artifact defaults + artifacts refresh + run log/docs updates).
- Secrets: skimmed text diff (`git diff main...HEAD --patch -- . ':!docs/artifacts' ':!docs/validation_pack.zip'`) and scanned run log for credential-like strings; only WRDS_SAMPLE references present.
- Tests evidence: `docs/agent_runs/20251226_HHMMSS_ticket-01_unify-artifacts-root/TESTS.md` contains FAST ctest pass and reproduce_all pass (second run).
- Canonicalization: official outputs present under `docs/artifacts/` and `git status --short artifacts` returned empty.
- Docs updates: `PROGRESS.md` entry includes tests + artifacts; `project_state/KNOWN_ISSUES.md` marks split-root issue resolved.
- Run log integrity: `META.json` has git_sha_before `d4be0724a76d2cbd2aaa88e3387ed08694d6e02b` and git_sha_after `9f1d4d8476d5f94e52013fff1ba9e2d01a9693ca`.

Bundle:
- `docs/gpt_bundles/20251226T213025Z_ticket-01_20251226_HHMMSS_ticket-01_unify-artifacts-root.zip`
