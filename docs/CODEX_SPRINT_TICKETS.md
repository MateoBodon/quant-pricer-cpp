
3) ## File: docs/CODEX_SPRINT_TICKETS.md
```md
# CODEX SPRINT TICKETS (Next sprint only)

## Sprint objective (non-negotiable)
Make the repo interview-safe by eliminating “missing evidence” and enforcing artifact + validity gates.

**Process note:** The prior `ticket-06_checklist-final` GPT bundle is marked **FAIL** due to missing run logs (process-only).
**Process note:** Ticket-06b is marked **FAIL** due to missing negative-test evidence and unrelated diff churn (see Ticket-06c).

---

## Ticket-01 — Artifact completeness + hard gate (reproduce_all)
**Goal (1 sentence):** `./scripts/reproduce_all.sh` must generate all required artifacts (including QuantLib parity, benchmarks, WRDS sample) and `metrics_summary` must hard-fail if anything required is missing.

**Why (ties to diagnosis):**
- Prompt-1 diagnosis flagged that the repo’s own metrics snapshot marks **QuantLib parity**, **benchmarks**, and **WRDS artifacts** as **missing**, which kills credibility.

**Files/modules likely touched (exact):**
- `scripts/reproduce_all.sh`
- `scripts/generate_metrics_summary.py`
- `scripts/manifest_utils.py`
- `scripts/package_validation.py` (if the validation pack depends on artifact list)
- `docs/artifacts/manifest.json` (generated)
- `docs/artifacts/metrics_summary.md` + `.json` (generated)
- `project_state/CURRENT_RESULTS.md`
- `project_state/KNOWN_ISSUES.md`
- `PROGRESS.md`

**Acceptance criteria (objective):**
- Running `REPRO_FAST=1 WRDS_USE_SAMPLE=1 ./scripts/reproduce_all.sh` produces:
  - `docs/artifacts/metrics_summary.md/json` with **no “missing”** status for:
    - `ql_parity`
    - `benchmarks`
    - `wrds` (sample mode)
- `python scripts/generate_metrics_summary.py ...` exits non-zero if any required artifact file is absent or unreadable.
- A `docs/validation_pack.zip` exists and includes the required evidence set.

**Minimal tests/commands to run:**
- `cmake -S . -B build -DCMAKE_BUILD_TYPE=Release && cmake --build build -j`
- `ctest --test-dir build -L FAST --output-on-failure`
- `WRDS_USE_SAMPLE=1 python -m wrds_pipeline.pipeline --fast` (real-data smoke, sample mode)
- `REPRO_FAST=1 WRDS_USE_SAMPLE=1 ./scripts/reproduce_all.sh`

**Expected artifacts/logs to produce:**
- `docs/artifacts/metrics_summary.md`
- `docs/artifacts/metrics_summary.json`
- `docs/artifacts/manifest.json`
- `docs/validation_pack.zip`
- `docs/agent_runs/<RUN_NAME>/*` (see DOCS_AND_LOGGING_SYSTEM.md)

**Exit checklist (must be completed):**
- Tests run: ✅ recorded in `docs/agent_runs/<RUN_NAME>/TESTS.md`
- Artifacts/logs: ✅ recorded in `docs/agent_runs/<RUN_NAME>/RESULTS.md` + manifest updated
- Docs updates: ✅ `PROGRESS.md` + `project_state/*` updated as applicable

---

## Ticket-02 — FAST artifact gate tests (CI cannot be green with missing evidence)
**Goal (1 sentence):** FAST tests must fail if required artifacts are missing/unparseable after the standard “fast repro” run.

**Why:**
- Missing artifacts currently slip through; we need an automated credibility gate.

**Files/modules likely touched:**
- `tests/test_metrics_snapshot_fast.py`
- `tests/test_cli_fast.py` (if it verifies CLI JSON output)
- `scripts/generate_metrics_summary.py` (for schema/keys)
- `docs/artifacts/metrics_summary.json` (generated)
- `PROGRESS.md`, `CHANGELOG.md` (if user-visible)

**Acceptance criteria:**
- `ctest -L FAST` fails when required artifacts are absent or malformed.
- `ctest -L FAST` passes after Ticket-01 on a clean run.
- The test asserts presence of required keys in `metrics_summary.json` (not just file existence).

**Minimal tests/commands to run:**
- `ctest --test-dir build -L FAST --output-on-failure`

**Expected artifacts/logs:**
- Updated tests + run logs under `docs/agent_runs/<RUN_NAME>/`
- Any new/updated “required artifacts list” documented in `docs/PLAN_OF_RECORD.md`

**Exit checklist:**
- Tests run: ✅
- Artifacts/logs: ✅
- Docs updates: ✅

---

## Ticket-03 — QuantLib parity suite: grid-based, summarized, regression-safe
**Goal (1 sentence):** QuantLib parity must be a grid (not cherry-picked cases) and summarized into `metrics_summary` with max/median error.

**Why:**
- QuantLib parity is the single strongest external credibility anchor for a pricing library.

**Files/modules likely touched:**
- `scripts/ql_parity.py`
- `scripts/generate_metrics_summary.py`
- `docs/artifacts/ql_parity/*` (generated)
- `project_state/CURRENT_RESULTS.md`
- `PROGRESS.md`

**Acceptance criteria:**
- Parity script outputs a CSV with a declared grid (moneyness × tenor; plus product params).
- `metrics_summary.json` includes `max_abs_error` and `median_abs_error` for parity.
- Any regression beyond tolerance fails CI (either via tests or by metrics gate).

**Minimal tests/commands:**
- `python scripts/ql_parity.py`
- `python scripts/generate_metrics_summary.py --artifacts docs/artifacts --manifest docs/artifacts/manifest.json`
- `ctest --test-dir build -L FAST --output-on-failure`

**Expected artifacts/logs:**
- `docs/artifacts/ql_parity/ql_parity.csv`
- `docs/artifacts/ql_parity/ql_parity.png`
- Run logs in `docs/agent_runs/<RUN_NAME>/`

**Exit checklist:**
- Tests run: ✅
- Artifacts/logs: ✅
- Docs updates: ✅

---

## Ticket-04 — Benchmarks: produce artifacts from C++ benchmark output (not Python timing)
**Goal (1 sentence):** Bench artifacts must be generated from C++ benchmark outputs and appear in `metrics_summary` (and not be marked “missing”).

**Why:**
- Performance credibility requires benchmark-grade measurement, not ad-hoc Python timing.

**Files/modules likely touched:**
- `benchmarks/*.cpp`
- `scripts/generate_bench_artifacts.py`
- `scripts/reproduce_all.sh`
- `scripts/generate_metrics_summary.py`
- `docs/artifacts/benchmarks/*` (generated)
- `PROGRESS.md`

**Acceptance criteria:**
- A benchmark run produces machine-readable output (JSON/CSV) stored under `docs/artifacts/benchmarks/`.
- `generate_bench_artifacts.py` produces at least one plot/table derived from that output.
- `metrics_summary` reports at least:
  - runtime per price (or throughput),
  - and the benchmark configuration used.

**Minimal tests/commands:**
- Build + run benchmarks (use repo’s documented target; do not invent):
  - e.g., `cmake --build build --target benchmarks` then run the benchmark binary
- `python scripts/generate_bench_artifacts.py`
- `ctest --test-dir build -L FAST --output-on-failure`

**Expected artifacts/logs:**
- `docs/artifacts/benchmarks/*`
- Run logs in `docs/agent_runs/<RUN_NAME>/`

**Exit checklist:**
- Tests run: ✅
- Artifacts/logs: ✅
- Docs updates: ✅

---

## Ticket-05 — WRDS sample regression + as-of invariants (no lookahead)
**Goal (1 sentence):** WRDS sample mode must be deterministic and must fail fast on any as-of / date leakage.

**Why:**
- Real-data pipelines are interview traps; we need enforceable no-leakage invariants and a credential-free smoke run.

**Files/modules likely touched:**
- `wrds_pipeline/pipeline.py`
- `wrds_pipeline/ingest_sppx_surface.py`
- `wrds_pipeline/oos_pricing.py`
- `wrds_pipeline/tests/test_wrds_pipeline.py`
- `wrds_pipeline_dates_panel.yaml`
- `scripts/reproduce_all.sh`
- `docs/artifacts/wrds_sample/*` (generated)
- `project_state/KNOWN_ISSUES.md`
- `PROGRESS.md`

**Acceptance criteria:**
- `WRDS_USE_SAMPLE=1 python -m wrds_pipeline.pipeline --fast` produces deterministic outputs under `docs/artifacts/wrds_sample/`.
- Unit tests assert:
  - calibration quote dates == trade_date,
  - OOS quote dates == next_trade_date,
  - contract universe rule is explicit and recorded.
- `metrics_summary` includes a WRDS sample section and is not “missing.”

**Minimal tests/commands:**
- `WRDS_USE_SAMPLE=1 python -m wrds_pipeline.pipeline --fast`
- `ctest --test-dir build -L FAST --output-on-failure`

**Expected artifacts/logs:**
- `docs/artifacts/wrds_sample/*` (+ provenance JSON)
- Run logs in `docs/agent_runs/<RUN_NAME>/`

**Exit checklist:**
- Tests run: ✅
- Artifacts/logs: ✅
- Docs updates: ✅

---

## Ticket-06b — Bundle + run-log completeness hard gate
**Status:** FAIL — missing negative-test evidence and unrelated diff churn (see Ticket-06c).
**Goal (1 sentence):** `make gpt-bundle` must produce an auditable bundle that always contains the required run log files, and it must fail fast if anything required is missing.

**Why:**
- Review bundles must be self-auditing; missing run logs break traceability.

**Files/modules likely touched:**
- `scripts/gpt_bundle.py`
- `Makefile` (gpt-bundle target)
- `docs/CODEX_SPRINT_TICKETS.md`
- `PROGRESS.md`
- `docs/agent_runs/<RUN_NAME>/`

**Acceptance criteria (objective):**
1) `make gpt-bundle TICKET=ticket-06b RUN_NAME=<RUN_NAME>` produces a zip that contains:
   - `AGENTS.md`
   - `docs/PLAN_OF_RECORD.md`
   - `docs/DOCS_AND_LOGGING_SYSTEM.md`
   - `docs/CODEX_SPRINT_TICKETS.md`
   - `PROGRESS.md`
   - `project_state/CURRENT_RESULTS.md`
   - `project_state/KNOWN_ISSUES.md`
   - `project_state/CONFIG_REFERENCE.md`
   - `DIFF.patch`
   - `LAST_COMMIT.txt`
   - `docs/agent_runs/<RUN_NAME>/{PROMPT.md,COMMANDS.md,RESULTS.md,TESTS.md,META.json}`
2) Bundling fails (exit code != 0) with a clear message listing missing files if any of the above are absent.
3) Bundling fails (exit code != 0) if `docs/CODEX_SPRINT_TICKETS.md` does not contain an entry for the ticket id (string match on `Ticket-06b` or `ticket-06b`).
4) `PROGRESS.md` and `docs/CODEX_SPRINT_TICKETS.md` are updated for this ticket, and the run is logged under `docs/agent_runs/<RUN_NAME>/`.

**Minimal tests/commands to run:**
- `python3 -m compileall scripts/gpt_bundle.py`
- `make gpt-bundle TICKET=ticket-06b RUN_NAME=<RUN_NAME>`
- Verify contents:
  - `python3 - << 'PY'`
    `import zipfile, sys`
    `z = zipfile.ZipFile(next(p for p in __import__("glob").glob("docs/gpt_bundles/*.zip")))`
    `print("\\n".join(z.namelist()))`
    `PY`

**Expected artifacts/logs to produce:**
- `docs/gpt_bundles/<timestamp>_ticket-06b_<RUN_NAME>.zip`
- `docs/agent_runs/<RUN_NAME>/*`

**Exit checklist:**
- Tests run: ✅
- Artifacts/logs: ✅
- Docs updates: ✅

---

## Ticket-06c — Prove bundler hard-gate + clean the diff
**Goal (1 sentence):** Prove `make gpt-bundle` fail-fast behavior for missing inputs and missing ticket IDs, complete META provenance, and remove unrelated diff churn.

**Why:**
- Bundles must be audit-safe with explicit negative-test evidence and clean diffs.

**Files/modules likely touched:**
- `scripts/gpt_bundle.py`
- `Makefile` (gpt-bundle target)
- `docs/CODEX_SPRINT_TICKETS.md`
- `PROGRESS.md`
- `docs/agent_runs/<RUN_NAME>/`

**Acceptance criteria (objective):**
1) Logged negative tests prove:
   - bundling fails (exit code != 0) and prints a clear list of missing required files when any required item is absent.
   - bundling fails (exit code != 0) when the ticket id is not present in `docs/CODEX_SPRINT_TICKETS.md`.
2) `META.json` includes `git_sha_before` and `git_sha_after` (matches HEAD after commit).
3) Diff excludes unrelated `artifacts/heston/**` churn (revert on this branch; move to separate ticket if needed).
4) A new bundle is generated and includes all required items.

**Minimal tests/commands to run:**
- `python3 -m compileall scripts/gpt_bundle.py`
- `python3 scripts/gpt_bundle.py --self-test`
- `make gpt-bundle TICKET=ticket-06c RUN_NAME=<RUN_NAME>`
- Verify contents:
  - `python3 - << 'PY'`
    `import zipfile, glob`
    `zpath = sorted(glob.glob("docs/gpt_bundles/*ticket-06c*.zip"))[-1]`
    `z = zipfile.ZipFile(zpath)`
    `print("\\n".join(z.namelist()))`
    `PY`

**Expected artifacts/logs to produce:**
- `docs/gpt_bundles/<timestamp>_ticket-06c_<RUN_NAME>.zip`
- `docs/agent_runs/<RUN_NAME>/*`

**Exit checklist:**
- Tests run: ✅
- Artifacts/logs: ✅
- Docs updates: ✅
