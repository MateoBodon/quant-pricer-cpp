# AGENTS.md instructions for /Users/mateobodon/Documents/Programming/Projects/quant-pricer-cpp

<INSTRUCTIONS>
# AGENTS.md — quant-pricer-cpp (Repository instructions for Codex + contributors)

This file defines hard rules and the execution protocol for agent-assisted work in this repo.

---

## 1) Stop-the-line rules (non-negotiable)

- **No fabricated results.** Never claim a test passed, a benchmark ran, or a plot was generated unless it actually ran in this workspace and is logged.
- **Validity > metrics.** If there is any sign of:
  - lookahead / leakage / survivorship bias (WRDS),
  - mutable/cherry-picked grids (synthetic),
  - silent defaults that change evaluation,
  you must fix it or clearly document the limitation before proceeding.
- **No p-hacking.** Do not tune scenario grids, tolerances, filters, or date panels to make numbers look better. Any change to evaluation protocol must:
  - update config version/hash,
  - regenerate artifacts,
  - be documented in PROGRESS and (if relevant) CURRENT_RESULTS.
- **No raw WRDS/OptionMetrics data committed.** Ever. Only license-safe derived tiny samples may be committed, and must pass the repo data policy guard.
- **Artifacts must be reproducible.** Official results must live under `docs/artifacts/` with provenance (`manifest.json` + `metrics_summary.*`).

---

## 2) How to build and test (default commands)

### Build (Release)
- `cmake -S . -B build -DCMAKE_BUILD_TYPE=Release`
- `cmake --build build -j`

### Fast unit tests
- `ctest --test-dir build -L FAST --output-on-failure`

### WRDS / market-data tests (only when enabled)
- `ctest --test-dir build -L MARKET --output-on-failure`
- Or Python test entrypoints as documented by the repo (prefer `--fast` modes)

---

## 3) Official reproduction run (the only pipeline allowed for headline results)

Run (fast + sample mode):
- `REPRO_FAST=1 WRDS_USE_SAMPLE=1 ./scripts/reproduce_all.sh`

This run must:
- generate/update `docs/artifacts/manifest.json`
- generate/update `docs/artifacts/metrics_summary.md` + `metrics_summary.json`
- generate/update `docs/validation_pack.zip` (if configured)

If anything writes to `artifacts/` during the official pipeline, treat as a failure.

---

## 4) Documentation + run logging protocol (required)

### Where things go
- Prompts: `docs/prompts/`
- GPT analysis outputs: `docs/gpt_outputs/`
- Codex run logs: `docs/agent_runs/<RUN_NAME>/`
- Artifacts: `docs/artifacts/`

### Run naming convention
- `YYYYMMDD_HHMMSS_ticket-XX_<slug>`

### Required files per run
Inside `docs/agent_runs/<RUN_NAME>/`:
- `PROMPT.md`
- `COMMANDS.md`
- `RESULTS.md`
- `TESTS.md`
- `META.json`
- `SOURCES.md` (only if web research used)

### Living docs update rules
- Always: `PROGRESS.md`
- If results change: `project_state/CURRENT_RESULTS.md`
- If risks/bugs change: `project_state/KNOWN_ISSUES.md`
- If user-visible behavior changes: `CHANGELOG.md`

---

## 5) Data policy (WRDS handling)

- WRDS credentials must never be printed in logs.
- Raw WRDS extracts must never be committed.
- Any cache must live in gitignored directories.
- Run the repo’s data policy guard (or its FAST test) after touching any data scripts.

---

## 6) Branch + commit policy

- Create a feature branch per ticket: `codex/ticket-XX-<slug>`
- Commit message starts with `ticket-XX: ...`
- Commit body must include:
  - `Tests: <exact commands>`
  - `Artifacts: <paths updated>`
- Do not use destructive git commands (`reset --hard`, `clean -fdx`) unless explicitly asked and logged.

---

## 7) If uncertain policy (don’t spam questions)

- Make assumptions explicit in `docs/agent_runs/<RUN_NAME>/RESULTS.md`.
- Prefer minimal safe changes.
- If blocked, implement the smallest diagnostic to unblock (e.g., a failing test that demonstrates the issue).
- Ask a question only if progress is impossible without it.

---


## Skills
These skills are discovered at startup from multiple local sources. Each entry includes a name, description, and file path so you can open the source for full instructions.
- skill-creator: Guide for creating effective skills. This skill should be used when users want to create a new skill (or update an existing skill) that extends Codex's capabilities with specialized knowledge, workflows, or tool integrations. (file: /Users/mateobodon/.codex/skills/.system/skill-creator/SKILL.md)
- skill-installer: Install Codex skills into $CODEX_HOME/skills from a curated list or a GitHub repo path. Use when a user asks to list installable skills, install a curated skill, or install a skill from another repo (including private repos). (file: /Users/mateobodon/.codex/skills/.system/skill-installer/SKILL.md)
- Discovery: Available skills are listed in project docs and may also appear in a runtime "## Skills" section (name + description + file path). These are the sources of truth; skill bodies live on disk at the listed paths.
- Trigger rules: If the user names a skill (with `$SkillName` or plain text) OR the task clearly matches a skill's description, you must use that skill for that turn. Multiple mentions mean use them all. Do not carry skills across turns unless re-mentioned.
- Missing/blocked: If a named skill isn't in the list or the path can't be read, say so briefly and continue with the best fallback.
- How to use a skill (progressive disclosure):
  1) After deciding to use a skill, open its `SKILL.md`. Read only enough to follow the workflow.
  2) If `SKILL.md` points to extra folders such as `references/`, load only the specific files needed for the request; don't bulk-load everything.
  3) If `scripts/` exist, prefer running or patching them instead of retyping large code blocks.
  4) If `assets/` or templates exist, reuse them instead of recreating from scratch.
- Description as trigger: The YAML `description` in `SKILL.md` is the primary trigger signal; rely on it to decide applicability. If unsure, ask a brief clarification before proceeding.
- Coordination and sequencing:
  - If multiple skills apply, choose the minimal set that covers the request and state the order you'll use them.
  - Announce which skill(s) you're using and why (one short line). If you skip an obvious skill, say why.
- Context hygiene:
  - Keep context small: summarize long sections instead of pasting them; only load extra files when needed.
  - Avoid deeply nested references; prefer one-hop files explicitly linked from `SKILL.md`.
- When variants exist (frameworks, providers, domains), pick only the relevant reference file(s) and note that choice.
- Safety and fallback: If a skill can't be applied cleanly (missing files, unclear instructions), state the issue, pick the next-best approach, and continue.
</INSTRUCTIONS>

<environment_context>
  <cwd>/Users/mateobodon/Documents/Programming/Projects/quant-pricer-cpp</cwd>
  <approval_policy>never</approval_policy>
  <sandbox_mode>danger-full-access</sandbox_mode>
  <network_access>enabled</network_access>
  <shell>zsh</shell>
</environment_context>

You are a coding agent operating in the `quant-pricer-cpp` repository.

BEGIN by reading these files (in order):
- AGENTS.md
- docs/PLAN_OF_RECORD.md
- docs/DOCS_AND_LOGGING_SYSTEM.md
- docs/CODEX_SPRINT_TICKETS.md

Ticket: ticket-04 — Freeze synthetic validation grid + tolerances (pre-registered protocol)

Stop-the-line (non-negotiable):
- Do NOT fabricate results or claim commands ran if they did not (log everything).
- Do NOT commit raw WRDS/OptionMetrics data or leak credentials into logs.
- Do NOT weaken evaluation validity (no silent protocol changes).
- Follow DOCS_AND_LOGGING_SYSTEM.md: create a complete run log folder with non-empty files.

Goal (1 sentence):
Make every headline synthetic validation script consume a frozen scenario grid + tolerance config, and record config hashes in the artifact manifest so results cannot be silently cherry-picked.

Acceptance criteria (must satisfy all):
1) Headline scripts require/consume config inputs for scenario grid + tolerances (or use a fixed canonical path that is committed):
   - scripts/tri_engine_agreement.py
   - scripts/pde_order_slope.py
   - scripts/mc_greeks_ci.py
   - scripts/ql_parity.py
2) The manifest records config hashes (at least sha256) for:
   - scenario grid config
   - tolerance config
   and the metrics snapshot references those hashes (directly or via manifest).
3) A FAST guardrail fails if any headline script runs without config provenance (no silent defaults).
4) Official fast reproducibility still works:
   - REPRO_FAST=1 WRDS_USE_SAMPLE=1 ./scripts/reproduce_all.sh
   produces artifacts under docs/artifacts and updates docs/artifacts/manifest.json and metrics_summary.*.

Required workflow (do NOT write a long upfront plan):
1) Create a new run log folder (must follow naming convention):
   - RUN_NAME="$(date -u +%Y%m%d_%H%M%S)_ticket-04_freeze-validation-grid"
   - RUN_DIR="docs/agent_runs/${RUN_NAME}"
   - Create: PROMPT.md, COMMANDS.md, RESULTS.md, TESTS.md, META.json (and SOURCES.md only if web research used).
   - Put this entire prompt text into PROMPT.md.
   - Start COMMANDS.md immediately and append every command you run (verbatim).

2) Inspect current behavior:
   - Locate how each headline script currently selects its scenario set / tolerances.
   - Identify any silent defaults or “tiny grid” fast paths that could change results.

3) Implement protocol freezing:
   A) Add committed configs (prefer under configs/):
     - configs/scenario_grids/<name>.yaml (or .json)
     - configs/tolerances/<name>.yaml (or .json)
     Keep them minimal but explicit and versionable.
   B) Update headline scripts to:
     - accept `--scenario-grid <path>` and `--tolerances <path>` OR
     - accept a single `--protocol <path>` that includes both,
     - and log/emit their config hashes into the manifest/provenance.
   C) Update scripts/generate_metrics_summary.py (or manifest utilities) so:
     - the manifest includes hashes for these configs,
     - the metrics snapshot output includes those hashes or references the manifest fields.

4) Add FAST guardrail test:
   - Add/extend a FAST test that:
     - runs the relevant scripts in a minimal mode but WITHOUT providing config paths (or with configs temporarily removed),
     - asserts they hard-fail with a clear error (“missing protocol config provenance”).
   - Also add a positive-path test that runs with the canonical configs and succeeds.

5) Run minimal sufficient tests (log in TESTS.md with outcomes + key snippets):
   - Build + FAST:
     - cmake -S . -B build -DCMAKE_BUILD_TYPE=Release
     - cmake --build build -j
     - ctest --test-dir build -L FAST --output-on-failure
   - Official pipeline (required because this ticket touches headline scripts/provenance):
     - REPRO_FAST=1 WRDS_USE_SAMPLE=1 ./scripts/reproduce_all.sh
   - Real-data-ish smoke (sample is acceptable here):
     - WRDS_USE_SAMPLE=1 python3 -m wrds_pipeline.pipeline --fast

6) Docs updates (required):
   - PROGRESS.md: add a dated entry summarizing:
     - what changed (configs added + scripts now require them)
     - how provenance is recorded (manifest fields + hashes)
     - exact tests/commands run
     - artifact paths updated
   - project_state/CONFIG_REFERENCE.md: document the canonical protocol config paths + CLI flags.
   - If this changes what metrics mean or how they’re produced:
     - docs/PLAN_OF_RECORD.md (only if needed)
     - project_state/CURRENT_RESULTS.md (only if headline values changed)

7) Commit on a feature branch:
   - git switch -c codex/ticket-04-freeze-validation-grid
   - Commit message: ticket-04: freeze scenario grid + tolerances with provenance
   - Commit body must include:
     - Tests: <exact commands>
     - Artifacts: <paths updated>
     - Run log: docs/agent_runs/${RUN_NAME}/

8) Generate the next review bundle at the end (and record the bundle path in RESULTS.md):
   - make gpt-bundle TICKET=ticket-04 RUN_NAME=${RUN_NAME}

Suggested Codex invocation (safe mode; approvals on):
- codex --profile safe

Do NOT use full-autonomy unless the human explicitly requests it.

Human merge checklist (also include in RESULTS.md):
- Headline scripts fail closed without protocol configs (no silent defaults)
- Config hashes appear in docs/artifacts/manifest.json and are referenced by metrics snapshot
- FAST tests pass and include the new guardrail
- REPRO_FAST pipeline passes and writes only to docs/artifacts
- WRDS sample smoke still passes
- PROGRESS.md + CONFIG_REFERENCE.md updated
- No secrets/raw WRDS data in diffs/logs
- Bundle generated and contains non-empty run logs + DIFF.patch
