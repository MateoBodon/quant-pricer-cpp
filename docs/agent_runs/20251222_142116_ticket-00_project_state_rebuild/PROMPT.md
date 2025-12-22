# Prompt

AGENTS.md instructions for /Users/mateobodon/Documents/Programming/Projects/quant-pricer-cpp

<INSTRUCTIONS>
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
</INSTRUCTIONS>

<environment_context>
  <cwd>/Users/mateobodon/Documents/Programming/Projects/quant-pricer-cpp</cwd>
  <approval_policy>never</approval_policy>
  <sandbox_mode>danger-full-access</sandbox_mode>
  <network_access>enabled</network_access>
  <shell>zsh</shell>
</environment_context>

# PROJECT_STATE REBUILD (Codex CLI)
You are Codex running inside the repo workspace (Codex CLI). Follow AGENTS.md instructions (they are injected automatically).
Your task is to (re)build a complete, accurate `project_state/` folder that makes this repository self-describing for humans and GPT-5.2 Pro.

IMPORTANT: Do not waste tokens on a big upfront plan. Just execute end-to-end and finish. (No intermediate “status updates” requirements.)

========================
GOAL
========================
Produce a fully populated `project_state/` directory that (1) is accurate (grounded in actual files), (2) is internally consistent, and (3) is optimized for LLM reading without direct repo access.

This is documentation/analysis work only. Preserve code behavior.

========================
SCOPE / EXCLUSIONS (HARD)
========================
- DO NOT recursively read huge directories or binary artifacts.
- Exclude from deep parsing:
  - .git/, .venv/, __pycache__/
  - reports/, data/ (only read small metadata files, registries, README, config; sample at most 1–2 small representative outputs)
  - experiments/**/outputs_*/ (only list + sample a tiny subset)
  - docs/agent_runs/** (do NOT parse every run; summarize index + last N runs only)
- You MAY list directory trees and file counts/sizes for excluded dirs.

========================
ACCURACY RULES
========================
- Do not guess. If uncertain, mark as “unclear” and cite the file path(s) that caused ambiguity.
- Prefer machine-derived indices (AST + import parsing) over manual extraction when possible.
- Every project_state doc must include a metadata header with:
  - generation timestamp
  - git SHA (HEAD)
  - branch
  - the command(s) used for generation

========================
DELIVERABLES
========================
Create/update ALL of the following files in `project_state/` (keep stable headings so diffs are clean):

1) ARCHITECTURE.md
2) MODULE_SUMMARIES.md
3) FUNCTION_INDEX.md
4) DEPENDENCY_GRAPH.md
5) PIPELINE_FLOW.md
6) DATAFLOW.md
7) EXPERIMENTS.md
8) CURRENT_RESULTS.md
9) RESEARCH_NOTES.md
10) OPEN_QUESTIONS.md
11) KNOWN_ISSUES.md
12) ROADMAP.md
13) CONFIG_REFERENCE.md
14) SERVER_ENVIRONMENT.md
15) TEST_COVERAGE.md
16) STYLE_GUIDE.md
17) CHANGELOG.md

ALSO create:
18) INDEX.md  (one-page navigation + “how to read this folder”)
19) _generated/ (directory)
    - _generated/repo_inventory.json (file list + roles + sizes)
    - _generated/symbol_index.json (AST-derived: file -> classes/functions + docstring first line)
    - _generated/import_graph.json (internal imports adjacency list)
    - _generated/make_targets.txt (Make targets extracted from Makefile)

========================
PROCEDURE (DO THIS)
========================
A) Collect metadata
- Record: git SHA, branch, timestamp, python version, installed deps if quickly available.
- Do NOT run heavy environment installs.

B) Fast repo scan
- Use `rg --files` to enumerate files quickly.
- Identify roots: src/, experiments/, tools/, tests/, docs/, configs, Makefile, README.

C) Build machine-derived indices (preferred)
- Write a small helper script (stdlib only) under tools/ (or run ad-hoc in a temp file) to:
  1) enumerate python files under src/, experiments/, tools/
  2) AST-parse each to extract:
     - top-level classes and functions
     - signatures (best-effort; ok if partial)
     - docstring first line
  3) parse imports to build internal dependency adjacency list
- Write results to `project_state/_generated/*.json`

D) Write/update the 17+2 markdown docs
- Use the generated JSON as ground truth for MODULE_SUMMARIES / FUNCTION_INDEX / DEPENDENCY_GRAPH.
- For PIPELINE_FLOW, extract entrypoints from:
  - Makefile targets
  - CLI scripts (argparse/typer/click)
  - experiments/*/run*.py
- For CURRENT_RESULTS / KNOWN_ISSUES:
  - Prefer summaries from PROGRESS.md + project_state itself + latest docs/agent_runs (last 3 runs)
  - Do NOT invent results; cite the artifact path(s).
- Keep each doc structured and scannable:
  - bullets, short paragraphs, tables where appropriate
  - lots of explicit file paths and “entrypoint command examples”
  - avoid giant walls of text

E) Consistency check (required)
- Verify every required file exists.
- Spot-check that:
  - key modules mentioned in ARCHITECTURE appear in MODULE_SUMMARIES
  - PIPELINE_FLOW entrypoints exist
  - CONFIG_REFERENCE keys point to real config files
- Fix contradictions before finishing.

F) Packaging for upload (artifact; do not commit zip)
- Create `docs/gpt_bundles/project_state_<timestamp>_<shortsha>.zip` containing:
  - project_state/
  - REPO_PLAN.md (if present)
  - docs/PLAN_OF_RECORD.md + docs/DOCS_AND_LOGGING_SYSTEM.md (if present)
  - PROGRESS.md
- Do NOT add the zip to git.

G) Run log + commit
- Create a run log directory:
  docs/agent_runs/<timestamp>_project_state_rebuild/
  with: PROMPT.md, COMMANDS.md, RESULTS.md, TESTS.md, META.json
- Update PROGRESS.md with a one-paragraph entry + paths to the zip.
- Commit only documentation + scripts needed for generation:
  - branch name: chore/project_state_refresh
  - commit message includes: “Rebuild project_state @ <shortsha>”
  - commit body includes Tests: (if any)

========================
TESTS (OPTIONAL)
========================
Only run quick commands that are safe:
- `make test-fast` if it is known to be fast; otherwise skip and note why.

========================
FINAL RESPONSE (your final assistant message)
========================
Return:
- files created/updated (paths)
- commands run (including zip command)
- where the zip artifact is located
- any exclusions made (what you didn’t parse deeply)
- known uncertainties you couldn’t resolve (with file references)
