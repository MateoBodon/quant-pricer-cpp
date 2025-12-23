You are a coding agent operating in the `quant-pricer-cpp` repository.

BEGIN by reading these files (in order):
- AGENTS.md
- docs/PLAN_OF_RECORD.md
- docs/DOCS_AND_LOGGING_SYSTEM.md
- docs/CODEX_SPRINT_TICKETS.md

Ticket: ticket-03 — Eliminate dual WRDS panel configs (single source of truth)

Non-negotiable (stop-the-line):
- Do NOT fabricate results or claim commands ran if they did not (log everything).
- Do NOT commit raw WRDS/OptionMetrics data or leak credentials into logs.
- Do NOT weaken evaluation validity (no silent protocol changes).
- Follow DOCS_AND_LOGGING_SYSTEM.md: create a complete run log folder.

Goal (1 sentence):
Choose one WRDS date-panel/dateset config as the single source of truth, remove/deprecate the other, and ensure the pipeline logs + records the panel id in provenance to prevent protocol drift.

Acceptance criteria (must satisfy all):
1) Only one panel/dateset config is used by the pipeline and documented (no ambiguity).
2) Pipeline logs the dataset/panel id and writes it into provenance (manifest or WRDS provenance outputs).
3) No dead parsing paths remain for the removed config (no “still half-supported” legacy code).

Required workflow (do NOT write a long upfront plan):
1) Create a new run log folder:
   - RUN_NAME="$(date -u +%Y%m%d_%H%M%S)_ticket-03_wrds-panel-single-source"
   - RUN_DIR="docs/agent_runs/${RUN_NAME}"
   - Create: PROMPT.md, COMMANDS.md, RESULTS.md, TESTS.md, META.json (and SOURCES.md only if web research used).
   - Put this entire prompt text into PROMPT.md.
   - Start COMMANDS.md immediately and append every command you run (verbatim).

2) Inspect current WRDS panel config usage:
   - Identify both configs and their schemas:
     - `wrds_pipeline_dates_panel.yaml`
     - `wrds_pipeline/dateset.yaml` (or equivalent)
   - Find where each is parsed/loaded:
     - `wrds_pipeline/pipeline.py`
     - `scripts/reproduce_all.sh`
     - any helper modules under `wrds_pipeline/`
   - Determine which one is currently the “real” default path used by:
     - `REPRO_FAST=1 WRDS_USE_SAMPLE=1 ./scripts/reproduce_all.sh`
     - `WRDS_USE_SAMPLE=1 python3 -m wrds_pipeline.pipeline --fast`

3) Implement single-source-of-truth behavior (minimal, reviewable changes):
   - Pick ONE canonical config file to keep (prefer whichever is already used by reproduce_all + docs).
   - Remove/deprecate the other:
     - Option A (preferred): delete legacy parsing path and update docs/scripts accordingly.
     - Option B: keep file but make it a strict alias with an explicit warning + hard failure unless a documented migration flag is used (log it).
   - Ensure the pipeline:
     - prints/logs the panel id (e.g., `panel_id` / `dataset_id`) at run start
     - writes it into provenance:
       - `docs/artifacts/manifest.json` entries for WRDS runs OR a WRDS-specific provenance JSON under `docs/artifacts/wrds/`
   - Update `project_state/CONFIG_REFERENCE.md` to document:
     - the single canonical config path
     - how to override it (env var or CLI flag), if supported
     - what “panel id” means and where it appears in provenance

4) Run minimal sufficient tests (log in TESTS.md with outcomes + key output snippets):
   - Build + FAST tests:
     - `cmake -S . -B build -DCMAKE_BUILD_TYPE=Release`
     - `cmake --build build -j`
     - `ctest --test-dir build -L FAST --output-on-failure`
   - WRDS sample smoke:
     - `WRDS_USE_SAMPLE=1 python3 -m wrds_pipeline.pipeline --fast`
     - Confirm logs show the panel/dataset id and that provenance includes it.
   - Official pipeline fast reproduce:
     - `REPRO_FAST=1 WRDS_USE_SAMPLE=1 ./scripts/reproduce_all.sh`
     - Confirm it still completes and writes canonical artifacts under `docs/artifacts/`.

5) Docs updates (required):
   - `PROGRESS.md`: add a dated entry including:
     - what changed (single config)
     - exact tests/commands run
     - where panel id appears in provenance
   - If you remove a legacy config path: update `project_state/OPEN_QUESTIONS.md` if it was previously ambiguous.
   - If behavior is user-visible: update `CHANGELOG.md`.

6) Commit on a feature branch:
   - `git switch -c codex/ticket-03-wrds-panel-single-source`
   - Commit message: `ticket-03: single WRDS panel config + provenance panel id`
   - Commit body must include:
     - `Tests: <exact commands>`
     - `Artifacts: <paths updated or 'none'>`
     - `Run log: docs/agent_runs/${RUN_NAME}/`

7) Generate the next review bundle at the end (and record the bundle path in RESULTS.md):
   - `make gpt-bundle TICKET=ticket-03 RUN_NAME=${RUN_NAME}`

Suggested Codex invocation (safe mode; approvals on):
- `codex --profile safe`

Human merge checklist (append to RESULTS.md):
- Only one WRDS panel config remains authoritative; the other is removed or a clearly documented alias
- Pipeline prints/logs panel id and provenance contains it
- Sample WRDS smoke ran (WRDS_USE_SAMPLE=1) and reproduce_all ran (REPRO_FAST=1 WRDS_USE_SAMPLE=1)
- No raw WRDS/OptionMetrics data or credentials in diffs/logs
- PROGRESS.md + CONFIG_REFERENCE.md updated
- Bundle generated via make gpt-bundle and contains complete non-empty run logs
