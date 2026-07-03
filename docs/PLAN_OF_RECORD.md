# quant-pricer-cpp — PLAN OF RECORD (PoR)

Date: 2025-12-22
Repo: quant-pricer-cpp

This PoR is the contract for what this repo is trying to prove and how we will prove it **without p-hacking**.

---

## 1) Core claim (what this repo is trying to prove)

**Primary claim (pricing library):**
- This is a **C++20 option pricing library** where *independent pricing engines* (analytic / Monte Carlo (PRNG+QMC) / PDE) are **numerically correct, stable, and reproducible**, verified against **external baselines** (QuantLib) and analytic truths on a **pre-registered test grid**.

**Secondary claim (optional; only if validity gates pass):**
- The WRDS/OptionMetrics pipeline supports **as-of-correct** calibration and **next-trading-day OOS** evaluation with explicit assumptions and automated checks that catch lookahead and protocol drift.

---

## 2) Estimands / target metrics (what we measure)

### A) Numerical correctness (synthetic + reference)
**Target metrics (must be computed on a pre-registered grid):**
- **QuantLib parity (price):** max / median / p95 absolute price error vs QuantLib across buckets (moneyness × tenor × product).
- **Tri-engine agreement:** max absolute diff between (analytic vs MC) and (analytic vs PDE); plus **MC CI coverage** of analytic.
- **Convergence behavior:**
  - PDE convergence slope for price (and later Δ/Γ): expected ~2 for standard second-order schemes in smooth regimes.
  - MC error vs compute budget; QMC vs PRNG **error vs walltime** (not “ratio-only”).
- **Greek reliability:** empirical CI coverage for MC Greeks (Pathwise/LR) against analytic Greeks on the pre-registered grid.

### B) Performance (speed/throughput)
**Target metrics:**
- Paths/sec for MC engines; scaling efficiency by threads (honest: show where it’s bad).
- **Error vs walltime frontier** for PRNG vs QMC (bench-driven timing).

### C) Market-data evaluation (WRDS OptionMetrics; gated)
**Target metrics (only after validity checks are automated and passing):**
- **In-sample fit (per day):** IV-RMSE (and optionally vega-weighted price RMSE) for BS and Heston.
- **OOS pricing error (t+1):** abs error distribution by buckets; report median/p95 and RMSE.
- **Parameter stability:** day-to-day parameter drift distributions (sanity check).
- **PnL (optional, not headline unless costs are explicit):** Δ-hedged gross and net PnL with spread/fees/financing/borrow assumptions.

---

## 3) Baselines (what “good” means)

### Synthetic/reference
- **Analytic Black–Scholes** (ground truth for European vanilla).
- **QuantLib** for cross-library parity (price-level checks across a grid).
- **Internal cross-check:** analytic vs MC vs PDE on overlapping products.

### WRDS
- **BS fit baseline** (per day) vs **Heston fit** baseline (per day).
- **Naive baseline (sanity):** carry-forward implied vol / flat vol within day buckets.

---

## 4) Evaluation protocol (how we prevent invalid wins)

### A) Pre-registered synthetic protocol (no cherry-picking)
- Maintain a **frozen scenario grid** (config file) for:
  - moneyness, tenor, vol, r, q ranges
  - product set (Euro; add American/barrier later once validated)
- Maintain a **frozen tolerance config** (what constitutes pass/fail).
- Any headline metrics must be produced by the official pipeline and appear in:
  - `docs/artifacts/manifest.json`
  - `docs/artifacts/metrics_summary.md` + `metrics_summary.json`

### B) WRDS protocol (no lookahead, no protocol drift)
Hard gates (must be automated tests):
- **As-of correctness:** calibration uses only `quote_date == trade_date`.
- **OOS correctness:** OOS eval uses only `quote_date == next_trade_date`.
- **Universe selection:** contract set is determined only from t-available fields and serialized per date.
- **Assumptions logged:** underlying price source, quote type, rate/dividend sources are emitted into provenance.

Splits / tuning policy:
- Any hyperparameters (filters, cleaning thresholds, optimizer controls) must be tuned **only on TRAIN dates**.
- Results reported on a locked **TEST panel** exactly once per configuration hash.
- For multi-date studies, prefer walk-forward (train→validate→test), but **never mix** panels.

### C) “No p-hacking” rules
- If you change the scenario grid, tolerances, filters, or panel definition, you must:
  - bump a config version / hash
  - regenerate artifacts
  - update CURRENT_RESULTS and PROGRESS with the reason

---

## 5) What counts as “resume-credible” (hard checklist)

A result is resume-credible **only if all apply**:
- Reproducible from a clean clone with a single command (sample-mode acceptable):
  - `REPRO_FAST=1 WRDS_USE_SAMPLE=1 ./scripts/reproduce_all.sh`
- FAST test suite passes:
  - `ctest --test-dir build -L FAST --output-on-failure`
- Metrics are backed by artifacts under **one canonical root**:
  - `docs/artifacts/` (no competing `artifacts/` truth)
- QuantLib parity is presented as a **grid summary** (not a single cherry-picked diff).
- If WRDS is mentioned:
  - as-of correctness tests exist and pass (sample mode at minimum),
  - no raw WRDS data is committed,
  - assumptions and dataset/panel ids are logged into provenance.

---

## 6) Main commands (official pipeline)

Build + tests:
- `cmake -S . -B build -DCMAKE_BUILD_TYPE=Release`
- `cmake --build build -j`
- `ctest --test-dir build -L FAST --output-on-failure`

Reproduce artifacts (canonical):
- `REPRO_FAST=1 WRDS_USE_SAMPLE=1 ./scripts/reproduce_all.sh`

WRDS sample pipeline fast smoke:
- `WRDS_USE_SAMPLE=1 python -m wrds_pipeline.pipeline --fast`

Validation pack (should be produced by reproduce_all):
- `python scripts/package_validation.py --artifacts docs/artifacts --output docs/validation_pack.zip`

---

## 7) Roadmap (concrete tasks → commands → expected artifacts)

### Horizon: next 1–2 weeks (validity + one credible demo run)
**Goal:** one-command run produces a defensible validation pack with zero ambiguity.

1) **Canonicalize artifact root + manifest**
- Task: ensure all scripts write to `docs/artifacts/` only; add a FAST guard test.
- Run:
  - `REPRO_FAST=1 WRDS_USE_SAMPLE=1 ./scripts/reproduce_all.sh`
- Expected artifacts:
  - `docs/artifacts/manifest.json`
  - `docs/artifacts/metrics_summary.md` + `metrics_summary.json`
  - `docs/validation_pack.zip`

2) **WRDS as-of correctness checks (sample mode)**
- Task: poison-pill tests + hard assertions for quote_date logic.
- Run:
  - `WRDS_USE_SAMPLE=1 python -m wrds_pipeline.pipeline --fast`
- Expected artifacts/logs:
  - `docs/artifacts/wrds/*` (sample outputs only)
  - test logs showing misdated rows are rejected

3) **Freeze the synthetic validation grid + tolerances**
- Task: create scenario-grid config + tolerance config; make scripts consume them and record hashes in manifest.
- Run:
  - `REPRO_FAST=1 WRDS_USE_SAMPLE=1 ./scripts/reproduce_all.sh`
- Expected artifacts:
  - `docs/artifacts/<experiment>/*.csv` regenerated using the frozen grid
  - manifest updated with config hash

4) **QuantLib parity: grid summary**
- Task: expand parity output to include bucket stats (max/median/p95).
- Expected artifacts:
  - `docs/artifacts/ql_parity/ql_parity.csv` (with bucket columns)
  - `docs/artifacts/ql_parity/ql_parity.png` (distribution/heatmap)

### Horizon: next 4–8 weeks (full experiment grid + robustness)
**Goal:** strengthen claims without widening attack surface.

- MC Greeks CI coverage across grid (FAST subset + SLOW full).
- PDE Δ/Γ convergence + boundary sensitivity suite.
- QMC vs PRNG: RMSE vs walltime curves from C++ benchmarks.
- Heston QE bias: bias map + convergence; quarantine from headline until bounded/fixed.
- WRDS live panel (optional): pre-registered date panels + locked test; publish bucketed OOS error distributions.

### Longer-term (“institution-grade” polish)
- Nightly broad-grid QuantLib regression (FAST PR subset + nightly full).
- Containerized reproducibility (Docker/devcontainer).
- Perf dashboard (error vs time vs threads) with provenance and regression alerts.
- Calibration diagnostics suite (residual plots, stability, regime splits).

---
