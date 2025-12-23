# docs/CODEX_SPRINT_TICKETS.md — Next sprint (execution only)

Sprint intent: **validity first**, then “resume-credible” artifacts.

---

## ticket-01 — Canonicalize artifact root + manifest (single source of truth)

**Status:** **FAIL** (evidence missing in bundle; run log evidence not included).

**Goal (1 sentence):** Make `docs/artifacts/` the only canonical artifact root and ensure the official pipeline cannot silently write to `artifacts/`.

**Why (from Prompt-1 diagnosis):**
- The `docs/artifacts/` vs `artifacts/` split is a reproducibility footgun and credibility risk (“which numbers are real?”).

**Files/modules likely touched:**
- `scripts/reproduce_all.sh`
- `scripts/generate_metrics_summary.py`
- `scripts/manifest_utils.py`
- any artifact scripts that still write to `artifacts/` (search in `scripts/`)
- `tests/` (add a FAST guard test)
- `docs/DOCS_AND_LOGGING_SYSTEM.md`
- `PROGRESS.md`
- `project_state/DATAFLOW.md`, `project_state/OPEN_QUESTIONS.md`, `project_state/KNOWN_ISSUES.md` (as needed)

**Acceptance criteria (objective):**
- Running `REPRO_FAST=1 WRDS_USE_SAMPLE=1 ./scripts/reproduce_all.sh` produces **no new files** under `artifacts/` (except explicitly allowlisted gitignored temp, if any).
- `docs/artifacts/manifest.json` is the only manifest used by metrics summary generation.
- A FAST test fails if the pipeline writes to `artifacts/` during reproduce_all.

**Minimal tests/commands to run:**
- `cmake -S . -B build -DCMAKE_BUILD_TYPE=Release && cmake --build build -j`
- `ctest --test-dir build -L FAST --output-on-failure`
- `REPRO_FAST=1 WRDS_USE_SAMPLE=1 ./scripts/reproduce_all.sh`

**Expected artifacts/logs to produce:**
- `docs/artifacts/manifest.json` updated
- `docs/artifacts/metrics_summary.md` + `metrics_summary.json` updated (even if values unchanged)
- `docs/validation_pack.zip` updated
- Run log folder: `docs/agent_runs/<RUN_NAME>/` with PROMPT/COMMANDS/RESULTS/TESTS/META
- Documentation updates: `PROGRESS.md` (always), plus any impacted `project_state/*`

---

## ticket-01b — Bundle integrity + evidence repair (ticket-01)

**Goal (1 sentence):** Make `make gpt-bundle` reject empty run logs / incomplete evidence, produce a reviewable DIFF.patch for the ticket, and regenerate a correct ticket-01 bundle that includes the real implementation run evidence.

**Acceptance criteria (objective):**
- `make gpt-bundle ...` fails if any required run log file exists but is empty:
  - `PROMPT.md`, `COMMANDS.md`, `RESULTS.md`, `TESTS.md`, `META.json`
- `DIFF.patch` spans the ticket’s substantive changes (scripts/tests), not only doc-only last-commit diffs.
- The regenerated ticket-01 bundle uses the actual implementation run log folder (likely `20251222_204744_ticket-01_unify-artifacts`) and includes:
  - non-empty run log files
  - a `DIFF.patch` that includes the artifact-root/manifest/test changes
- Docs updated: `PROGRESS.md` and this sprint ticket list.

**Minimal tests/commands to run:**
- `python3 -m compileall scripts/gpt_bundle.py`
- Create a temporary run folder with empty required files and confirm `make gpt-bundle` fails (log the error snippet).

**Expected artifacts/logs to produce:**
- New bundle for ticket-01 with implementation run log evidence
- New bundle for ticket-01b with this run log evidence
- Run log folder under `docs/agent_runs/<RUN_NAME>/`

---

## ticket-02 — WRDS as-of correctness hard checks + poison-pill tests (sample mode)

**Goal (1 sentence):** Add automated checks that catch quote_date/trade_date mismatches and prevent lookahead in WRDS calibration and OOS evaluation.

**Why (from Prompt-1 diagnosis):**
- As-of leakage is the easiest way to embarrass the repo; must be testable and fail-closed.

**Files/modules likely touched:**
- `wrds_pipeline/ingest_*.py` (surface ingest)
- `wrds_pipeline/calibrate_*.py`
- `wrds_pipeline/oos_pricing.py`
- `wrds_pipeline/pipeline.py`
- `wrds_pipeline/sample_data/*` (add poison rows)
- `wrds_pipeline/tests/*`
- `docs/PLAN_OF_RECORD.md` (protocol section)
- `PROGRESS.md`, `project_state/KNOWN_ISSUES.md` (if issues discovered)

**Acceptance criteria (objective):**
- Calibration step hard-fails or filters-to-zero if any row has `quote_date != trade_date`.
- OOS evaluation hard-fails if any row has `quote_date != next_trade_date`.
- A FAST test injects a “poison” sample file and verifies the pipeline rejects it.
- Outputs include provenance fields for `trade_date` and `next_trade_date`.

**Minimal tests/commands to run:**
- `WRDS_USE_SAMPLE=1 python -m wrds_pipeline.pipeline --fast`
- `ctest --test-dir build -L FAST --output-on-failure` (or `pytest` if WRDS tests live in python)

**Expected artifacts/logs to produce:**
- Sample-mode WRDS outputs under `docs/artifacts/wrds/`
- Run logs under `docs/agent_runs/<RUN_NAME>/`
- Doc updates: `PROGRESS.md` + `project_state/KNOWN_ISSUES.md` if failures discovered/resolved

---

## ticket-03 — Eliminate dual WRDS panel configs (single source of truth)

**Goal (1 sentence):** Choose one WRDS date-panel config and remove/deprecate the other to prevent protocol drift.

**Why (from Prompt-1 diagnosis):**
- Two competing date-panel configs is silent protocol drift waiting to happen.

**Files/modules likely touched:**
- `wrds_pipeline/pipeline.py`
- `wrds_pipeline/dateset.yaml` (or equivalent)
- `wrds_pipeline_dates_panel.yaml` (or equivalent)
- `scripts/reproduce_all.sh`
- `project_state/CONFIG_REFERENCE.md`
- `PROGRESS.md`, `project_state/OPEN_QUESTIONS.md`

**Acceptance criteria (objective):**
- Only one panel/dateset config is used by the pipeline and documented.
- Pipeline logs the dataset/panel id and writes it into provenance.
- No dead parsing paths remain for the removed config.

**Minimal tests/commands to run:**
- `WRDS_USE_SAMPLE=1 python -m wrds_pipeline.pipeline --fast`
- `REPRO_FAST=1 WRDS_USE_SAMPLE=1 ./scripts/reproduce_all.sh`

**Expected artifacts/logs to produce:**
- Updated provenance in `docs/artifacts/wrds/*`
- Run logs under `docs/agent_runs/<RUN_NAME>/`
- Doc updates: `PROGRESS.md` and `project_state/CONFIG_REFERENCE.md`

---

## ticket-04 — Freeze synthetic validation grid + tolerances (pre-registered protocol)

**Goal (1 sentence):** Make all headline validation scripts consume a frozen scenario grid + tolerance config and record their hashes in the manifest.

**Why (from Prompt-1 diagnosis):**
- Tri-engine / parity numbers are meaningless if the scenario set is tiny or mutable.

**Files/modules likely touched:**
- `scripts/tri_engine_agreement.py`
- `scripts/pde_order_slope.py`
- `scripts/mc_greeks_ci.py`
- `scripts/ql_parity.py`
- `scripts/generate_metrics_summary.py`
- `docs/PLAN_OF_RECORD.md`
- `docs/artifacts/manifest.json` (generation logic)
- `PROGRESS.md`

**Acceptance criteria (objective):**
- Headline scripts require/consume config inputs for grid + tolerances (or use a fixed canonical path).
- Manifest records config hashes.
- FAST test fails if scripts run without config provenance.

**Minimal tests/commands to run:**
- `REPRO_FAST=1 WRDS_USE_SAMPLE=1 ./scripts/reproduce_all.sh`
- `ctest --test-dir build -L FAST --output-on-failure`

**Expected artifacts/logs to produce:**
- Config files committed under `configs/` (or a documented location)
- Updated `docs/artifacts/manifest.json`
- Run logs + PROGRESS.md update

---

## ticket-05 — QuantLib parity: grid summary (max/median/p95 by bucket)

**Goal (1 sentence):** Turn QuantLib parity into a resume-defensible grid table + distribution plot.

**Why (from Prompt-1 diagnosis):**
- One headline max-diff number can be cherry-picked; grid summary survives interviews.

**Files/modules likely touched:**
- `scripts/ql_parity.py`
- `scripts/generate_metrics_summary.py`
- `docs/artifacts/ql_parity/*` (generated)
- `docs/PLAN_OF_RECORD.md` (deliverables list)
- `PROGRESS.md`, `project_state/CURRENT_RESULTS.md` (if headline metrics change)

**Acceptance criteria (objective):**
- `docs/artifacts/ql_parity/ql_parity.csv` includes bucket columns and per-bucket error stats.
- Metrics summary reports both max and median errors over the full grid.
- A plot shows error distribution (not only scatter).

**Minimal tests/commands to run:**
- `python scripts/ql_parity.py`
- `python scripts/generate_metrics_summary.py --artifacts docs/artifacts --manifest docs/artifacts/manifest.json`
- `REPRO_FAST=1 WRDS_USE_SAMPLE=1 ./scripts/reproduce_all.sh` (if parity is part of official pipeline)

**Expected artifacts/logs to produce:**
- Updated parity CSV + plot under `docs/artifacts/ql_parity/`
- Run logs under `docs/agent_runs/<RUN_NAME>/`
- Doc updates: `PROGRESS.md` and `project_state/CURRENT_RESULTS.md` if metrics change

---
