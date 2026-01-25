# Prompt

Ticket: ticket-09_refresh-metrics-ax162s

Goal: Refresh resume-credible metrics on the Hetzner AX162-S by rerunning the official reproducible pipeline and updating the committed metrics snapshot (manifest + metrics_summary + validation pack) with clean run logs.

Constraints:
- Do not change pricing/math code unless a test/benchmark is broken.
- Create/activate repo-local .venv, install requirements-dev.txt.
- Run Release build + FAST tests.
- Run REPRO_FAST=1 WRDS_USE_SAMPLE=1 ./scripts/reproduce_all.sh to regenerate docs/artifacts/manifest.json + metrics_summary.{md,json} + docs/validation_pack.zip.
- Record hardware/compiler/python in META.json.
- Update project_state/CURRENT_RESULTS.md + PROGRESS.md with new headline numbers.
- Produce a fresh GPT bundle from a clean git status.

Acceptance criteria:
- FAST passes in Release build using repo-local .venv.
- reproduce_all.sh completes and updates manifest/metrics_summary/validation_pack.
- CURRENT_RESULTS + PROGRESS updated with new snapshot.
- No raw WRDS data committed; data-policy guard green.
- Run log contains PROMPT/COMMANDS/RESULTS/TESTS/META.
- git status clean.
- New gpt bundle zip committed under docs/gpt_bundles/.
