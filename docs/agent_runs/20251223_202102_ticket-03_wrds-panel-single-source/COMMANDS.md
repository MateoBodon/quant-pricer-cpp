RUN_NAME="$(date -u +%Y%m%d_%H%M%S)_ticket-03_wrds-panel-single-source"
RUN_DIR="docs/agent_runs/${RUN_NAME}"
mkdir -p "$RUN_DIR"
cat <<'EOF' > "$RUN_DIR/PROMPT.md"
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
EOF
touch "$RUN_DIR/RESULTS.md" "$RUN_DIR/TESTS.md" "$RUN_DIR/META.json"
printf '%s\n' "$CMD" > "$RUN_DIR/COMMANDS.md"
ls -td docs/agent_runs/* | head -n 1
sed -n '1,200p' AGENTS.md
sed -n '1,200p' docs/PLAN_OF_RECORD.md
sed -n '1,200p' docs/DOCS_AND_LOGGING_SYSTEM.md
sed -n '1,200p' docs/CODEX_SPRINT_TICKETS.md
rg --files -g 'wrds_pipeline_dates_panel.yaml' -g 'dateset.yaml'
sed -n '1,200p' wrds_pipeline_dates_panel.yaml
sed -n '1,200p' wrds_pipeline/dateset.yaml

rg -n 'dateset|dates_panel|panel' wrds_pipeline scripts
sed -n '200,360p' wrds_pipeline/pipeline.py
sed -n '480,760p' wrds_pipeline/pipeline.py
sed -n '760,880p' wrds_pipeline/pipeline.py
sed -n '120,220p' scripts/reproduce_all.sh
sed -n '1,220p' wrds_pipeline/tests/test_wrds_pipeline.py
sed -n '1,120p' wrds_pipeline/ingest_sppx_surface.py
sed -n '1,220p' scripts/build_wrds_cache.py
rg -n 'wrds_pipeline_dates_panel.yaml|dateset.yaml'
sed -n '1,220p' scripts/manifest_utils.py
rg -n 'describe_inputs' wrds_pipeline/pipeline.py scripts
sed -n '1,120p' wrds_pipeline/pipeline.py
sed -n '1,200p' project_state/CONFIG_REFERENCE.md
sed -n '1,200p' PROGRESS.md
sed -n '1,200p' project_state/OPEN_QUESTIONS.md
sed -n '1,120p' project_state/PIPELINE_FLOW.md
sed -n '1,120p' project_state/ARCHITECTURE.md
sed -n '120,200p' 'ROADMAP (1).md'
sed -n '40,120p' README.md
sed -n '100,170p' docs/WRDS_Results.md
sed -n '100,160p' docs/Results.md
rm wrds_pipeline/dateset.yaml
rg -n 'wrds_pipeline/dateset.yaml'
sed -n '1,200p' CHANGELOG.md
cmake -S . -B build -DCMAKE_BUILD_TYPE=Release
cmake --build build -j
ctest --test-dir build -L FAST --output-on-failure
WRDS_USE_SAMPLE=1 python3 -m wrds_pipeline.pipeline --fast
REPRO_FAST=1 WRDS_USE_SAMPLE=1 ./scripts/reproduce_all.sh
rg -n 'wrds_dateset|panel_id' docs/artifacts/manifest.json
sed -n '950,1010p' docs/artifacts/manifest.json
sed -n '1,200p' docs/agent_runs/20251223_183500_ticket-02_wrds-asof-checks/META.json
sed -n '1,120p' docs/agent_runs/20251223_183500_ticket-02_wrds-asof-checks/COMMANDS.md
git status -sb
ls -la docs/artifacts/logs
rg -n 'artifacts/logs' .gitignore
git switch -c codex/ticket-03-wrds-panel-single-source
git rev-parse HEAD
uname -a
c++ --version | head -n 1
python3 -V
cmake --version | head -n 1
shasum -a 256 wrds_pipeline_dates_panel.yaml
git status -sb
ls -la docs/artifacts/wrds
REPRO_FAST=1 WRDS_USE_SAMPLE=1 ./scripts/reproduce_all.sh
git status -sb
ls -la docs/agent_runs/20251223_202102_ticket-03_wrds-panel-single-source
git status -sb
git ls-files docs/artifacts/logs
sed -n '1,80p' docs/agent_runs/20251223_054210_ticket-01_finalize/META.json
sed -n '1,40p' docs/agent_runs/20251222_014941_ticket-06b_bundle-integrity/META.json
date -u +%Y-%m-%dT%H:%M:%SZ
make gpt-bundle TICKET=ticket-03 RUN_NAME=20251223_202102_ticket-03_wrds-panel-single-source
date -u +%Y-%m-%dT%H:%M:%SZ
git status -sb
ls -la docs/gpt_bundles | tail -n 5
rg -n 'gpt_bundles' .gitignore
rm -rf docs/artifacts/logs
git status -sb
git add -A
git status -sb

cat <<'EOF' > /tmp/ticket-03-commit-msg.txt
ticket-03: single WRDS panel config + provenance panel id

Tests: cmake -S . -B build -DCMAKE_BUILD_TYPE=Release; cmake --build build -j; ctest --test-dir build -L FAST --output-on-failure; WRDS_USE_SAMPLE=1 python3 -m wrds_pipeline.pipeline --fast; REPRO_FAST=1 WRDS_USE_SAMPLE=1 ./scripts/reproduce_all.sh
Artifacts: docs/artifacts/bench/*, docs/artifacts/manifest.json, docs/artifacts/metrics_summary.md, docs/artifacts/metrics_summary.json, docs/artifacts/ql_parity/*, docs/artifacts/qmc_vs_prng_equal_time.*; docs/validation_pack.zip
Run log: docs/agent_runs/20251223_202102_ticket-03_wrds-panel-single-source/
EOF
git commit -F /tmp/ticket-03-commit-msg.txt
git status -sb
make gpt-bundle TICKET=ticket-03 RUN_NAME=20251223_202102_ticket-03_wrds-panel-single-source
date -u +%Y-%m-%dT%H:%M:%SZ
git rev-parse HEAD
git status -sb
git add docs/agent_runs/20251223_202102_ticket-03_wrds-panel-single-source/COMMANDS.md docs/agent_runs/20251223_202102_ticket-03_wrds-panel-single-source/META.json docs/agent_runs/20251223_202102_ticket-03_wrds-panel-single-source/RESULTS.md docs/artifacts/manifest.json docs/artifacts/metrics_summary.json docs/artifacts/metrics_summary.md
cat <<'EOF' > /tmp/ticket-03-commit-msg-2.txt
ticket-03: update run log + metrics snapshot

Tests: ctest --test-dir build -L FAST --output-on-failure; WRDS_USE_SAMPLE=1 python3 -m wrds_pipeline.pipeline --fast
Artifacts: docs/artifacts/manifest.json, docs/artifacts/metrics_summary.md, docs/artifacts/metrics_summary.json
Run log: docs/agent_runs/20251223_202102_ticket-03_wrds-panel-single-source/
EOF
git commit -F /tmp/ticket-03-commit-msg-2.txt
git status -sb
rg -n 'wrds_pipeline/dateset.yaml|wrds_pipeline_dates_panel.yaml'
rg -n 'wrds_dateset|panel_id' docs/artifacts/manifest.json
git show -s --format=fuller 8bddc8d10fcb10ab32919f45b985bb97db7a5dd8
rg -n 'cmake -S \.' docs/agent_runs/20251223_202102_ticket-03_wrds-panel-single-source/COMMANDS.md
rg -n 'ctest --test-dir build -L FAST|WRDS_USE_SAMPLE=1 python3 -m wrds_pipeline.pipeline --fast|REPRO_FAST=1 WRDS_USE_SAMPLE=1 ./scripts/reproduce_all.sh' docs/agent_runs/20251223_202102_ticket-03_wrds-panel-single-source/COMMANDS.md
sed -n '1,200p' project_state/CURRENT_RESULTS.md
sed -n '1,200p' docs/artifacts/metrics_summary.md
rg -n 'WRDS_PASSWORD=|WRDS_USERNAME=|WRDS_PASSWORD|WRDS_USERNAME' docs/agent_runs/20251223_202102_ticket-03_wrds-panel-single-source
git diff --name-status main..HEAD
date -u +%Y-%m-%dT%H:%M:%SZ
git status -sb
git add docs/agent_runs/20251223_202102_ticket-03_wrds-panel-single-source/COMMANDS.md docs/agent_runs/20251223_202102_ticket-03_wrds-panel-single-source/RESULTS.md project_state/CURRENT_RESULTS.md
cat <<'EOF' > /tmp/ticket-03-commit-msg-4.txt
ticket-03: sync current results with metrics snapshot

Tests: ctest --test-dir build -L FAST --output-on-failure; WRDS_USE_SAMPLE=1 python3 -m wrds_pipeline.pipeline --fast; REPRO_FAST=1 WRDS_USE_SAMPLE=1 ./scripts/reproduce_all.sh
Artifacts: none (doc sync only)
Run log: docs/agent_runs/20251223_202102_ticket-03_wrds-panel-single-source/
EOF
git commit -F /tmp/ticket-03-commit-msg-4.txt
git rev-parse HEAD
date -u +%Y-%m-%dT%H:%M:%SZ
sed -n '1,40p' docs/agent_runs/20251223_202102_ticket-03_wrds-panel-single-source/META.json
git status -sb
git add docs/agent_runs/20251223_202102_ticket-03_wrds-panel-single-source/COMMANDS.md docs/agent_runs/20251223_202102_ticket-03_wrds-panel-single-source/META.json
cat <<'EOF' > /tmp/ticket-03-commit-msg-5.txt
ticket-03: refresh run log metadata

Tests: ctest --test-dir build -L FAST --output-on-failure; WRDS_USE_SAMPLE=1 python3 -m wrds_pipeline.pipeline --fast; REPRO_FAST=1 WRDS_USE_SAMPLE=1 ./scripts/reproduce_all.sh
Artifacts: none (run log metadata only)
Run log: docs/agent_runs/20251223_202102_ticket-03_wrds-panel-single-source/
EOF
git commit -F /tmp/ticket-03-commit-msg-5.txt
tail -n 5 docs/agent_runs/20251223_202102_ticket-03_wrds-panel-single-source/COMMANDS.md
git status -sb
