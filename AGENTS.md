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
