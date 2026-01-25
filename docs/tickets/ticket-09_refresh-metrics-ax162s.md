# Ticket: ticket-09_refresh-metrics-ax162s

## Goal
Refresh resume-credible metrics on the Hetzner AX162-S by rerunning the official reproducible pipeline and updating the committed metrics snapshot (manifest + metrics_summary + validation pack) with clean run logs.

## Scope
- Do not change pricing/math code unless a test/benchmark is broken.
- Create/activate repo-local `.venv` and install `requirements-dev.txt`.
- Run Release build + FAST tests.
- Run `REPRO_FAST=1 WRDS_USE_SAMPLE=1 ./scripts/reproduce_all.sh` to regenerate:
  - `docs/artifacts/manifest.json`
  - `docs/artifacts/metrics_summary.{md,json}`
  - `docs/validation_pack.zip`
- Record hardware/compiler/python in `META.json`.
- Update `project_state/CURRENT_RESULTS.md` + `PROGRESS.md` with new headline numbers.
- Produce a fresh GPT bundle from a clean git status.

## Acceptance Criteria
- `ctest -L FAST` passes in Release build using repo-local `.venv`.
- `REPRO_FAST=1 WRDS_USE_SAMPLE=1 ./scripts/reproduce_all.sh` completes and updates:
  - `docs/artifacts/manifest.json`
  - `docs/artifacts/metrics_summary.{md,json}`
- `docs/validation_pack.zip` updated.
- `project_state/CURRENT_RESULTS.md` reflects the new snapshot (generated_at + key metrics).
- `PROGRESS.md` updated with new performance/correctness headline numbers.
- No raw WRDS data committed and data-policy guard remains green.
- `docs/agent_runs/<RUN_NAME>/` contains `PROMPT/COMMANDS/RESULTS/TESTS/META`.
- `git status --porcelain` is clean.
- A new GPT bundle zip is committed under `docs/gpt_bundles/`.

## Plan
1. Create run log scaffold under `docs/agent_runs/<RUN_NAME>/` and capture prompt + environment.
2. Create repo-local `.venv`, install `requirements-dev.txt`, configure Release build, and run FAST tests.
3. Run `REPRO_FAST=1 WRDS_USE_SAMPLE=1 ./scripts/reproduce_all.sh` and verify artifact updates.
4. Update `project_state/CURRENT_RESULTS.md` + `PROGRESS.md` with new headline metrics and timestamps.
5. Generate GPT bundle via `python3 tools/agentic/gpt_bundle.py --zip --ticket ticket-09_refresh-metrics-ax162s` from a clean git status.

## Notes
- Follow repo logging protocol and include hardware/compiler/python details in `META.json`.
- Keep diffs minimal; avoid unrelated refactors.
