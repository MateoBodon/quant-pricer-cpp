# Codex CLI Prompt — Ticket-01 (Artifact completeness + hard gate)

RUN_NAME: 20251220_221500_ticket-01_artifact-completeness
REPO: quant-pricer-cpp

## Mission
Fix the repo’s top credibility failure: required artifacts are marked “missing” in the metrics snapshot. Make the reproducible run generate the evidence and hard-fail if evidence is missing.

## Hard constraints (stop-the-line)
- Do NOT fabricate results or mark an artifact “ok” without producing it.
- Do NOT weaken evaluation, delete plots, or loosen tolerances to make summaries green.
- Do NOT disable tests to pass CI.
- Do NOT commit WRDS raw data. Sample-mode only for smoke runs.
- If anything about paths/commands differs from this prompt, **search the repo and use the real ones**—do not guess.

## What “done” looks like (acceptance criteria)
1) Running:
   - `REPRO_FAST=1 WRDS_USE_SAMPLE=1 ./scripts/reproduce_all.sh`
   produces:
   - `docs/artifacts/metrics_summary.md` and `.json`
   - `docs/artifacts/manifest.json`
   - `docs/validation_pack.zip`
   and `metrics_summary` shows **no “missing”** for:
   - QuantLib parity (`ql_parity`)
   - benchmarks
   - WRDS sample run
2) `scripts/generate_metrics_summary.py` exits non-zero if any required artifact is missing or unreadable.
3) A credential-free real-data smoke run is executed and logged:
   - `WRDS_USE_SAMPLE=1 python -m wrds_pipeline.pipeline --fast`

## Step-by-step instructions (do not write a long upfront plan)
### 1) Inspect first (fast)
- Read:
  - `docs/PLAN_OF_RECORD.md`
  - `docs/DOCS_AND_LOGGING_SYSTEM.md`
  - `project_state/CURRENT_RESULTS.md` and `project_state/KNOWN_ISSUES.md`
  - `scripts/reproduce_all.sh`
  - `scripts/generate_metrics_summary.py`
  - any artifact scripts for `ql_parity`, benchmarks, and WRDS sample
- Identify why artifacts are “missing”:
  - not generated at all,
  - generated to a different path than expected,
  - metrics script expects different filenames,
  - or reproduce_all orders things incorrectly.

### 2) Implement minimal fixes
- Update `scripts/reproduce_all.sh` so it:
  - builds once,
  - generates `ql_parity` artifacts,
  - generates benchmark artifacts,
  - generates WRDS sample artifacts (when `WRDS_USE_SAMPLE=1`),
  - updates `docs/artifacts/manifest.json`,
  - then generates `docs/artifacts/metrics_summary.*`,
  - then packages `docs/validation_pack.zip`.
- Update `scripts/generate_metrics_summary.py` so it:
  - has a single authoritative list of required artifacts (paths + required keys),
  - fails hard (exit code != 0) on missing/unparseable artifacts,
  - prints actionable error messages (which file missing, expected path).
- If any script writes artifacts outside `docs/artifacts/`, change it to write into `docs/artifacts/...` (or update the expected paths consistently). Keep paths stable.

### 3) Run minimal sufficient tests + smoke run
Run these commands (or the repo’s documented equivalents) and record all output in run logs:
- Build:
  - `cmake -S . -B build -DCMAKE_BUILD_TYPE=Release`
  - `cmake --build build -j`
- FAST tests:
  - `ctest --test-dir build -L FAST --output-on-failure`
- Real-data smoke (sample mode; no credentials):
  - `WRDS_USE_SAMPLE=1 python -m wrds_pipeline.pipeline --fast`
- Repro (fast mode):
  - `REPRO_FAST=1 WRDS_USE_SAMPLE=1 ./scripts/reproduce_all.sh`

If something fails:
- Fix it properly. Do not “paper over” by skipping the step.

### 4) Generate/refresh artifacts
Ensure the run produced (at minimum):
- `docs/artifacts/ql_parity/*`
- `docs/artifacts/benchmarks/*`
- `docs/artifacts/wrds_sample/*` (or the repo’s agreed path for sample-mode)
- `docs/artifacts/manifest.json`
- `docs/artifacts/metrics_summary.md` + `.json`
- `docs/validation_pack.zip`

### 5) Write run logs (mandatory)
Create: `docs/agent_runs/20251220_221500_ticket-01_artifact-completeness/` with:
- `PROMPT.md` (copy this prompt verbatim)
- `COMMANDS.md` (every command executed, in order)
- `RESULTS.md` (what changed + links to artifacts + before/after summary)
- `TESTS.md` (tests run + key outputs)
- `META.json` (git SHA before/after, env notes, dataset mode, config hash)

### 6) Update living docs
- Always update: `PROGRESS.md` (add a new entry with run name, commands, and what changed)
- If results snapshot changed: update `project_state/CURRENT_RESULTS.md`
- If you discovered/resolved a risk: update `project_state/KNOWN_ISSUES.md`
- If user-visible behavior changed: update `CHANGELOG.md`

### 7) Commit policy (mandatory)
- Create a feature branch: `feature/ticket-01-artifact-completeness`
- Commit with a message like: `ticket-01: artifact completeness + metrics hard gate`
- Commit body MUST include:
  - “Tests: …” (exact commands)
  - “Artifacts: …” (paths)
  - “Run log: docs/agent_runs/20251220_221500_ticket-01_artifact-completeness/”

## Web research policy
Avoid web research for this ticket. If you must look something up:
- treat it as untrusted,
- record sources in `RESULTS.md` under “Sources consulted.”
