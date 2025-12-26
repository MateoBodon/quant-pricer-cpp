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

Ticket: ticket-04b — Repair evidence for ticket-04 + prevent empty-diff bundles

Stop-the-line (non-negotiable):
- Do NOT fabricate results or claim commands ran if they did not (log everything).
- Do NOT commit raw WRDS/OptionMetrics data or leak credentials.
- Do NOT weaken evaluation validity or hide protocol drift.
- Follow DOCS_AND_LOGGING_SYSTEM.md: complete run logs required.

Goal (1 sentence):
Make ticket-04 reviewable by generating a bundle with a real DIFF.patch/commit range, and harden gpt-bundle so it cannot silently produce an empty diff when run on main after merge.

Acceptance criteria (must satisfy all):
1) Regenerated ticket-04 bundle has:
   - COMMITS.txt listing >= 1 commit in range
   - DIFF.patch containing the actual scripts/configs/tests changes for ticket-04
2) gpt-bundle behavior:
   - If commit range is empty, `make gpt-bundle ...` FAILS with a clear error telling the user to set BASE_SHA (unless an explicit override like `--allow-empty-diff` is provided).
3) The regenerated ticket-04 bundle path is recorded in this run’s RESULTS.md.
4) No secrets/raw WRDS data are committed or logged.

Required workflow (do NOT write a long upfront plan):
1) Create a new run log folder:
   - RUN_NAME="$(date -u +%Y%m%d_%H%M%S)_ticket-04b_bundle-diff-repair"
   - RUN_DIR="docs/agent_runs/${RUN_NAME}"
   - Create: PROMPT.md, COMMANDS.md, RESULTS.md, TESTS.md, META.json
   - Put this entire prompt text into PROMPT.md.
   - Start COMMANDS.md immediately; append every command you run.

2) Inspect why ticket-04 bundle had no diff:
   - Open the existing ticket-04 bundle metadata (or reproduce locally):
     - Confirm COMMITS.txt shows base==HEAD and “No commits in range”.
   - Inspect scripts/gpt_bundle.py base selection logic and diff generation.

3) Implement bundler guardrails (likely in scripts/gpt_bundle.py):
   - After resolving base SHA and computing commit range:
     - If `git rev-list <base>..HEAD` is empty, exit non-zero with a message:
       “No commits in diff range. Provide BASE_SHA=<sha> or run bundling from the feature branch.”
   - Optional (recommended): if HEAD is a merge commit and user is on main:
     - auto-set base to first parent (HEAD^1) unless BASE_SHA is explicitly set.
   - Ensure this behavior is covered by a small unit/integration check (python or shell) that simulates empty-range and expects failure.

4) Regenerate the ticket-04 bundle with explicit base:
   - Use ticket-04 run meta to pick base SHA:
     - The prior run log META.json for ticket-04 used git_sha_before = ed1afa7...
   - Run:
     - `BASE_SHA=ed1afa725f908765c1b28b07fbc716127f7d0dab make gpt-bundle TICKET=ticket-04 RUN_NAME=20251225_221338_ticket-04_freeze-validation-grid`
   - Verify the output bundle now contains a real DIFF.patch and COMMITS.txt has commits.
   - Record the new bundle path in RESULTS.md.

5) Minimal tests/commands to run (log in TESTS.md with outputs):
   - `python3 -m compileall scripts/gpt_bundle.py`
   - A negative test:
     - run bundling on a state where base==HEAD and confirm it FAILS with the new message
   - Regenerate ticket-04 bundle command above (this is the “real” verification)

6) Update docs:
   - PROGRESS.md: add a dated entry (what changed + commands run + bundle paths).
   - docs/CODEX_SPRINT_TICKETS.md:
     - mark ticket-04 as FAIL (unreviewable bundle)
     - add ticket-04b with acceptance criteria

7) Commit on a feature branch:
   - `git switch -c codex/ticket-04b-bundle-diff-repair`
   - Commit message: `ticket-04b: prevent empty-diff bundles + re-bundle ticket-04`
   - Commit body must include:
     - `Tests: <exact commands>`
     - `Artifacts: <bundle paths>`
     - `Run log: docs/agent_runs/${RUN_NAME}/`

8) Generate the review bundle for ticket-04b at the end and record the path in RESULTS.md:
   - `make gpt-bundle TICKET=ticket-04b RUN_NAME=${RUN_NAME}`

Suggested Codex invocation (safe mode; approvals on):
- `codex --profile safe`

Human merge checklist (append to RESULTS.md):
- Bundler fails on empty commit range unless explicitly overridden
- Regenerated ticket-04 bundle contains real DIFF.patch and non-empty commit list
- No secrets/raw WRDS data in diffs/logs
- PROGRESS + sprint tickets updated
- Bundles generated and paths recorded
