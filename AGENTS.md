# AGENTS.md - quant-pricer-cpp

This file is the repo-specific operating contract for Codex, Heavy, Pro, and human contributors.

## Non-Negotiable Rules

- No fabricated results. Do not claim a build, test, benchmark, reproduction run, plot, or bundle exists unless it actually ran or was generated in this workspace and is logged.
- Validity beats nicer metrics. Any lookahead, leakage, survivorship, mutable-grid, or silent-default risk must be fixed or explicitly documented before treating a result as evidence.
- No p-hacking. Scenario grids, tolerances, filters, date panels, seeds, and claim boundaries must not be tuned to improve a story without a documented protocol change.
- No raw WRDS/OptionMetrics data in git, bundles, logs, prompts, or public docs. Commit only license-safe tiny samples and aggregate artifacts that pass the data-policy guard.
- Curated official artifacts live under `docs/artifacts/` with provenance. Local/live/scratch outputs live under ignored paths such as `artifacts/_local/`.
- Product behavior should not change during documentation/infrastructure tickets unless the work order explicitly calls for it.

## AI Project OS v2 Sources Of Truth

- `PROJECT.md` - project identity, scope, audience, and layout.
- `docs/strategy/GOAL_CONTEXT.md` - durable goals and non-goals; initially pre-Pro.
- `docs/strategy/STRATEGIC_OVERVIEW.md` - current strategic understanding.
- `docs/strategy/PLAN_OF_RECORD.md` - active execution plan and recenter triggers.
- `docs/strategy/DECISIONS.md` - durable decisions.
- `docs/strategy/RISK_REGISTER.md` - risks that matter beyond a single bug.
- `docs/strategy/TICKET_LEDGER.md` - ticket inventory and review status.
- `docs/strategy/CODEX_GOALS.md` - future goal-level Codex work candidates.
- `docs/strategy/CONTEXT_CARRYOVER.md` - compact context for fresh sessions.
- `project_state/STATE_INDEX.md` - factual repo map and state.
- `project_state/RUNBOOK.md` - setup/build/test/repro/bundle commands.
- `project_state/VALIDATION_MATRIX.md` - what each check proves.
- `project_state/CLAIMS_AND_EVIDENCE.md` - claim/evidence boundaries.

Pre-v2 planning docs remain accessible in `docs/_archive/pre_ai_os_v2/20260703/`. Do not treat archived docs or copied pre-v2 files as current truth unless a canonical doc points to them.

## Default Validation Commands

Use the lightest checks that prove the ticket, but do not invent commands.

Typical fast path:

```bash
git status --short
python3 -m compileall tools/agentic/ai_os_bundle.py
python3 scripts/check_data_policy.py
cmake -S . -B build -DCMAKE_BUILD_TYPE=Release
cmake --build build -j
ctest --test-dir build -L FAST --output-on-failure
```

Official sample reproduction, when claims/artifacts change:

```bash
REPRO_FAST=1 WRDS_USE_SAMPLE=1 ./scripts/reproduce_all.sh
python3 scripts/package_validation.py --artifacts docs/artifacts --output docs/validation_pack.zip
```

WRDS/live validation is opt-in and environment-gated. Do not run or claim it unless credentials/local data are explicitly available and the command is logged.

## Data And Artifact Policy

- Never print credentials or raw restricted paths in logs.
- Never include raw data, `.env`, `.venv`, `build/`, `external/`, `docs/coverage/`, or `artifacts/_local/` payloads in model bundles unless explicitly required and sanitized.
- State bundles may include manifest/hash/size entries for large artifacts instead of raw files.
- If a local WRDS run mutates `docs/artifacts/manifest.json`, document and revert or intentionally promote the change with evidence.

## Run Logging

For T-000 and future v2 work, generated run logs go under:

```text
reports/_runs/<timestamp>_<ticket_slug>/
```

Each substantial run log should include:

- `PROMPT.md`
- `COMMANDS.md`
- `RESULTS.md`
- `VALIDATION.md` or `VALIDATION.json`
- `SUMMARY.md`

Existing pre-v2 run logs under `docs/agent_runs/` are preserved as history and may still be useful when reconstructing past decisions.

## Bundle Policy

Use `reports/_bundles/` for generated AI OS v2 bundles:

- Project State Audit Bundle: for Pro strategy/reset work.
- Review Bundle: for Heavy ticket review.

Do not bundle dependency folders, build trees, virtual environments, raw datasets, old bundle zips, huge logs, or local scratch outputs. Include indexes, manifests, hashes, and reasons for exclusion instead.

## Editing Discipline

- Keep changes scoped to the ticket.
- Prefer existing repo patterns and command surfaces.
- Update canonical docs only when durable state changes.
- Update `PROGRESS.md` for completed tickets or meaningful strategy/release/review events.
- Do not use destructive git commands unless explicitly requested and logged.
