TICKET: ticket-03
RUN_NAME: 20251229_HHMMSS_ticket-03_wrds-panel-single-source

You are Codex working in the quant-pricer-cpp repo. AGENTS.md is binding.

FIRST (read before doing anything):
- AGENTS.md
- docs/PLAN_OF_RECORD.md
- docs/DOCS_AND_LOGGING_SYSTEM.md
- docs/CODEX_SPRINT_TICKETS.md
- project_state/CONFIG_REFERENCE.md
- project_state/KNOWN_ISSUES.md

Do NOT write a long upfront plan. Execute with a tight inspect→edit→test→log loop.

Ticket to implement: ticket-03 — Eliminate dual WRDS panel configs (single source of truth)

Hard constraints (stop-the-line):
- Do not fabricate results/metrics. Only update CURRENT_RESULTS if produced by a logged run.
- Do not commit raw WRDS data, credentials, or any restricted columns. Use WRDS_USE_SAMPLE=1 unless credentials are explicitly present AND the run is safe and documented.
- Do not make live/unsafe behavior the default.
- Keep docs/artifacts as canonical output root. Do not write to artifacts/ (non-canonical) except allowlisted temp (if any), and document the allowlist.

1) Inspect (fast, concrete):
- Locate all “WRDS dateset/panel” config files (expected canonical: wrds_pipeline_dates_panel.yaml; find any legacy alternative).
- Identify every loader/parser and override mechanism:
  - wrds_pipeline/pipeline.py
  - scripts/reproduce_all.sh
  - any YAML schemas / CLI flags / env vars
- Identify the drift risk: competing defaults, schema differences, or divergent panel_id semantics.

2) Implement (single source of truth, fail-closed):
- Make wrds_pipeline_dates_panel.yaml the only canonical panel config (as described in project_state/CONFIG_REFERENCE.md).
- Remove/deprecate the legacy config:
  - Prefer deleting it if truly unused.
  - If you must keep a stub for migration, make it hard-error with a clear message + the one correct replacement path. No silent fallback.
- Remove dead parsing paths for the removed config (no hidden "if file exists then parse old schema").
- Ensure provenance captures and records (at minimum):
  - panel_id
  - dateset config path OR config hash
  - sample vs live mode indicator
  - date range used
  Write these into docs/artifacts/manifest.json under the relevant runs.* keys and any WRDS pipeline outputs.

3) Update docs:
- project_state/CONFIG_REFERENCE.md: describe ONLY the canonical dateset/panel config + ONLY the supported override paths (CLI + env var).
- project_state/KNOWN_ISSUES.md: mark the dual-config issue resolved (if resolved) with a reference to this run log folder.
- PROGRESS.md: add a dated entry including Tests:, Artifacts:, Run log:.

4) Tests / commands (record everything you run):
- Build + FAST tests:
  - cmake -S . -B build -DCMAKE_BUILD_TYPE=Release
  - cmake --build build -j
  - ctest --test-dir build -L FAST --output-on-failure
- WRDS sample smoke (must run):
  - WRDS_USE_SAMPLE=1 python -m wrds_pipeline.pipeline --fast
- Repro smoke (must run):
  - REPRO_FAST=1 WRDS_USE_SAMPLE=1 ./scripts/reproduce_all.sh
- Confirm non-canonical artifacts root remains unused via filesystem check (not just git status):
  - if [ -d artifacts ]; then (find artifacts -type f | head -n 50; exit 1); fi

If any test fails: stop, fix, and re-run the minimal failing command(s). Do not “green by disabling.”

5) Run logs (MANDATORY):
Create docs/agent_runs/<RUN_NAME_NEXT>/ with:
- PROMPT.md (this exact prompt)
- COMMANDS.md (every command, in order, with cwd)
- RESULTS.md (what changed + what proved it; include links/paths to artifacts)
- TESTS.md (tests run + pass/fail + failure snippet if any)
- META.json (git_sha_before, git_sha_after=HEAD AFTER FINAL COMMIT, branch, env summary, dataset_id, config hashes)

6) Git hygiene:
- Create branch: codex/ticket-03-wrds-panel-single-source
- Make small logical commits.
- Final commit message MUST include:
  - Tests: <exact commands>
  - Artifacts: <paths changed/produced>
  - Run log: docs/agent_runs/<RUN_NAME_NEXT>/

7) Bundle for review:
- Run:
  make gpt-bundle TICKET=ticket-03 RUN_NAME=<RUN_NAME_NEXT>
- Record the produced bundle path in docs/agent_runs/<RUN_NAME_NEXT>/RESULTS.md
