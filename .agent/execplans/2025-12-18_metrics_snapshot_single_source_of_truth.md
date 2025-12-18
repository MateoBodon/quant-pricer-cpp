# ExecPlan — 2025-12-18 — Metrics snapshot (single source of truth)

## Goal (1–3 days)
Create a **single, artifact-derived metrics snapshot** so every “Results” claim becomes reproducible and interview-defensible.

This ExecPlan produces:
- `docs/artifacts/metrics_summary.json` (canonical numbers)
- `docs/artifacts/metrics_summary.md` (human-readable)
- FAST test coverage so snapshot generation can’t silently break
- Docs/README updates that link to the snapshot instead of hard-coding numbers

## Why this is the highest-ROI next move
- The repo already has strong engines + experiments; the risk is **credibility drift** (numbers in prose not provably tied to artifacts).
- A snapshot makes resume metrics defensible *without* needing new models yet.

## Scope (tight)
**In scope**
- Implement snapshot generator script and wire it into the existing reproducibility flow.
- Update docs to reference snapshot as the source-of-truth.

**Out of scope (explicitly NOT now)**
- Heston QE bias fixes
- WRDS panel expansion / new dates
- Any new pricing models or major refactors
- Performance optimizations beyond what’s needed for the snapshot script itself

---

## Implementation tasks (agent checklist)
> Follow repo conventions in `AGENTS.md` and style/lint rules.

### 1) Add snapshot generator (Python)
- [x] Add `scripts/generate_metrics_summary.py` (or similarly named) that:
  - reads `docs/artifacts/manifest.json`
  - reads known artifact CSV/JSON outputs under `docs/artifacts/`
  - computes a compact set of resume-relevant metrics (see “Required metrics” below)
  - writes:
    - `docs/artifacts/metrics_summary.json`
    - `docs/artifacts/metrics_summary.md` (table generated from JSON)
- [ ] Design principle: **never invent a number**. If an artifact is missing or schema changed:
  - record `"status": "missing"` or `"status": "parse_error"` with a reason
  - do not crash the whole run unless required artifacts are missing

**Required metrics to include (minimum)**
- Tri-engine agreement: max abs diff (BS vs PDE; BS vs MC mean), and whether MC CI contains BS (if CI columns exist).
  - Source: `docs/artifacts/tri_engine_agreement.csv`
- QMC vs PRNG equal-time: RMSE ratio (PRNG_RMSE / QMC_RMSE) at matched wall-clock, per payoff type if available.
  - Source: `docs/artifacts/qmc_vs_prng_equal_time.csv`
- PDE order: fitted slope (or compute from error-vs-grid columns), plus RMSE at finest grid if available.
  - Source: `docs/artifacts/pde_order_slope.csv`
- QuantLib parity: max abs price diff (cents) by product bucket; runtime ratio if present.
  - Source: `docs/artifacts/ql_parity/ql_parity.csv`
- Benchmarks: MC throughput and scaling efficiency if corresponding bench CSV exists; otherwise point to raw JSON.
  - Source: `docs/artifacts/bench/bench_*.json` and/or derived CSVs in `docs/artifacts/bench/`
- WRDS (sample-mode at minimum): pull aggregated metrics if files exist; clearly label them “sample bundle regression harness”.
  - Source: `docs/artifacts/wrds/wrds_agg_*.csv`

### 2) Wire snapshot generation into `scripts/reproduce_all.sh`
- [x] Ensure `WRDS_USE_SAMPLE=1 ./scripts/reproduce_all.sh` generates/updates `metrics_summary.json` and `metrics_summary.md`.
- [x] Ensure the run is recorded in `docs/artifacts/manifest.json` (via existing `manifest_utils.update_run` if that’s the repo standard).

- [x] Add a FAST-labeled test that runs the snapshot generator against the repo’s committed artifacts.
- [x] The test should assert:
  - output files exist
  - JSON is valid and contains required top-level keys (see Acceptance Criteria)
  - required metric blocks exist with `status in {ok,missing,parse_error}` (but **tri_engine + qmc + pde + ql_parity** should normally be `ok` if artifacts are committed)

- [x] Update `project_state/CURRENT_RESULTS.md` to:
  - link to `docs/artifacts/metrics_summary.md`
  - keep narrative but avoid stating numeric results unless copied from snapshot output and clearly labeled as snapshot-derived
- [x] Update `README.md` “Results at a Glance” (minimal change):
  - add a short “Metrics snapshot” bullet with the reproduction command
  - link to `docs/artifacts/metrics_summary.md`
  - do **not** introduce new numbers that aren’t snapshot-derived

---

## Acceptance criteria (must be true)
1) **Snapshot generation works**
- `python scripts/generate_metrics_summary.py --artifacts docs/artifacts --manifest docs/artifacts/manifest.json` completes with exit code 0.
- `docs/artifacts/metrics_summary.json` exists and is valid JSON.
- `docs/artifacts/metrics_summary.md` exists and is consistent with the JSON (generated, not hand-edited).

2) **Snapshot is integrated into reproducibility flow**
- `WRDS_USE_SAMPLE=1 ./scripts/reproduce_all.sh` produces/updates the snapshot files.

3) **Tests pass**
- `ctest --test-dir build -L FAST --output-on-failure` passes.

4) **No new overclaims**
- Any numeric results referenced in README/docs are either:
  - directly snapshot-derived, or
  - explicitly labeled “target”.

---

## Exact commands to run (copy/paste)
> Use Release unless debugging.

### Build + FAST tests
```bash
cmake -S . -B build -DCMAKE_BUILD_TYPE=Release
cmake --build build -j
ctest --test-dir build -L FAST --output-on-failure
```

### Reproduce artifacts (deterministic sample mode) + snapshot
```bash
WRDS_USE_SAMPLE=1 ./scripts/reproduce_all.sh
python scripts/generate_metrics_summary.py --artifacts docs/artifacts --manifest docs/artifacts/manifest.json
```

### Optional: bundle validation pack (release artifact)
```bash
python scripts/package_validation.py --artifacts docs/artifacts --output docs/validation_pack.zip
```

---

## Deliverables / where to look
- Snapshot files:
 - `docs/artifacts/metrics_summary.json`
  - `docs/artifacts/metrics_summary.md`
- Manifest:
  - `docs/artifacts/manifest.json` (should include snapshot run)
- Tests:
  - New FAST test file under `tests/` or Python test harness used by repo
- Docs updates:
  - `project_state/CURRENT_RESULTS.md`
  - `README.md`

## Notes / deviations
- Snapshot writes manifest entry `metrics_snapshot` when not run with `--skip-manifest`.

---

## Update protocol (required)
- Update this ExecPlan **in-place** as work completes:
  - mark checkboxes
  - add a short “Notes / deviations” section at the end if anything changed
- Append an entry to the repo logbook **per `AGENTS.md`** (do not invent a new logbook format if one already exists).
- Commit changes with a message referencing this ExecPlan filename:
  - `ExecPlan: 2025-12-18_metrics_snapshot_single_source_of_truth.md — metrics snapshot`
