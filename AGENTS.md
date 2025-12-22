# AGENTS.md — quant-pricer-cpp

Codex (and humans) must treat this repo as **quant-interview-grade** engineering: correctness, reproducibility, and defensible evaluation are the product.

---

## 0) Stop-the-line rules (non-negotiable)
- **No fabricated results.** Never claim an artifact/metric exists unless it was generated in the current run and logged.
- **No “green by deletion.”** Do not delete failing plots/tables or loosen checks to hide missing evidence.
- **No evaluation weakening.** Do not change splits/panels/tolerances after seeing results without:
  1) updating `docs/PLAN_OF_RECORD.md`,
  2) explaining the change in `docs/agent_runs/<RUN>/RESULTS.md`,
  3) updating `project_state/CURRENT_RESULTS.md`.
- **No raw WRDS data committed.** Ever. Only license-safe derived summaries or small synthetic samples may be committed.
- **No dangerous autonomy.** Do signal if a task would require:
  - network access,
  - running commands outside sandbox,
  - or destructive git/FS operations.
  Prefer safe defaults.

If any of the above would be violated: STOP and document why in the run log.

---

## 1) How to build + test (canonical)
### Build (Release)
- `cmake -S . -B build -DCMAKE_BUILD_TYPE=Release`
- `cmake --build build -j`

### Tests
- FAST:
  - `ctest --test-dir build -L FAST --output-on-failure`
- Full:
  - `ctest --test-dir build --output-on-failure`
- MARKET / WRDS integration (opt-in):
  - `ctest --test-dir build -L MARKET --output-on-failure`

### Reproducible artifact run
- `./scripts/reproduce_all.sh`
- For fast CI-like runs, use any repo-supported fast flags/env (e.g., `REPRO_FAST=1`).
- For sample-mode WRDS smoke:
  - `WRDS_USE_SAMPLE=1 python -m wrds_pipeline.pipeline --fast`

---

## 2) Documentation + run logging protocol (mandatory)
Follow `docs/DOCS_AND_LOGGING_SYSTEM.md`.

Every meaningful change must include a run log folder:
- `docs/agent_runs/YYYYMMDD_HHMMSS_ticket-XX_slug/`
  - `PROMPT.md`
  - `COMMANDS.md`
  - `RESULTS.md`
  - `TESTS.md`
  - `META.json`

Always update:
- `PROGRESS.md` (one entry per run)

Update when relevant:
- `project_state/CURRENT_RESULTS.md` (when metrics/artifacts change)
- `project_state/KNOWN_ISSUES.md` (when a risk/bug is found or fixed)
- `CHANGELOG.md` (user-visible changes)

---

## 3) Data policy (WRDS / OptionMetrics)
- Credentials must be provided via environment variables; do not print them to logs.
- Cache directories must be outside the repo or in gitignored paths.
- Commit policy:
  - ✅ OK: tiny license-safe derived summaries (aggregated error tables), synthetic samples, config YAMLs.
  - ❌ NOT OK: raw WRDS extracts, quote-level data, anything that violates WRDS/OptionMetrics licensing.
- Data-policy guard: `python3 scripts/check_data_policy.py` must pass; tracked artifacts/data under `artifacts/`, `docs/artifacts/`, `data/`, and `wrds_pipeline/sample_data/` may not contain restricted columns (`strike,.*market_iv`, `secid`, `best_bid/ask/offer`). Any tracked CSV under `wrds_pipeline/sample_data/` must begin with `# SYNTHETIC_DATA`.

---

## 4) Branch + commit policy
- Work on feature branches: `feature/ticket-XX_short-slug`
- Each commit must include in the body:
  - `Tests: <exact commands run>`
  - `Artifacts: <paths generated/updated>`
  - `Run log: docs/agent_runs/<RUN_NAME>/`

Do not force-push. Do not rewrite history unless explicitly instructed.

---

## 5) If uncertain policy (don’t spam questions)
- Make assumptions explicit in `docs/agent_runs/<RUN>/RESULTS.md` and proceed with the minimal safe change.
- If a change risks breaking evaluation validity or leaking data: STOP and explain.
- Prefer small, reviewable diffs over broad refactors.
