# quant-pricer-cpp – Long-Term Roadmap

This roadmap is organized around three goals:

1. Numerical robustness and coverage.
2. WRDS-based empirical results that are easy to quote on a resume.
3. First-class support for AI coding agents (Codex) to iterate safely and autonomously.

The roadmap assumes the current state:

- Black–Scholes analytics, Monte Carlo (variance reduction, QMC, pathwise & LR Greeks), Crank–Nicolson PDE with Rannacher, barriers, American, exotics, Heston analytic + QE MC.:contentReference[oaicite:0]{index=0}  
- Reproducible artifacts via `scripts/reproduce_all.sh`, `docs/artifacts/manifest.json`, and GitHub Pages (Results, coverage).:contentReference[oaicite:1]{index=1}  
- WRDS OptionMetrics pipeline for SPX (IvyDB) with vega-weighted Heston calibration and aggregated pricing/OOS/Δ‑hedged PnL metrics.:contentReference[oaicite:2]{index=2}  

---

## Phase 0 – Housekeeping & Baseline

**Objective:** Make the current state explicit and stable so future changes are easy to reason about and reproduce.

### 0.1. Document current state

- [ ] Add `docs/ROADMAP.md` (this file) and keep it updated per release.
- [ ] Add `AGENTS.md` at repo root with:
  - Setup instructions (build, test, WRDS env).
  - Preferred coding style and refactoring rules.
  - Canonical test commands and when to run them.
  - WRDS data-handling rules (no raw IvyDB in repo; only aggregated CSV/PNGs under `docs/artifacts/wrds/`).:contentReference[oaicite:3]{index=3}  

### 0.2. Confirm coverage & CI baselines

- [ ] Run full test suite locally in Release:
  - `cmake -S . -B build -DCMAKE_BUILD_TYPE=Release`
  - `cmake --build build -j`
  - `ctest --test-dir build --output-on-failure`
- [ ] Regenerate coverage & artifacts:
  - `WRDS_USE_SAMPLE=1 ./scripts/reproduce_all.sh`
  - Confirm `docs/artifacts/manifest.json` updated and coverage HTML deployed under `coverage/`.:contentReference[oaicite:4]{index=4}  
- [ ] Record current coverage numbers (lines, functions, branches) in `docs/ROADMAP.md` as “Baseline coverage (vX.Y.Z)”.

---

## Phase 1 – Numerical robustness & tests

**Objective:** Tighten numerical correctness of core engines and push branch coverage up in the critical paths, especially where behavior is most complex.

### 1.1. Heston QE – from “known biased” to “under control”

Current state: Results page explicitly notes “current QE runs still exhibit a large bias versus the analytic reference”; plot is there mainly to detect a future regression fix.:contentReference[oaicite:5]{index=5}  

**Plan:**

- [x] Deep‑dive `src/heston.cpp` QE implementation vs Andersen QE paper:
  - Checked regime selection, variance truncation, and correlation term; added integrated-variance drift (σ∫√v dW₁ identity) and documented the cross term.
- [x] Extend `scripts/heston_qe_vs_analytic.py`:
  - [x] Sweep over a wider parameter grid (κ, θ, σ_v, ρ, v0, T) including stress regimes.
  - [x] Compute bias and RMSE for both price and implied BS vol as a function of:
    - Number of time steps.
    - Number of paths.
  - [x] Emit CSV columns: `bias_price`, `rmse_price`, `bias_iv`, `rmse_iv`, `steps`, `paths`.
- [~] Fix or quantify QE bias:
  - Integrated-variance drift reduces near-Feller bias (<1 price unit at 8–16 steps), but ATM base/high-vol-of-vol scenarios still sit ~4–6 price units above the analytic CF. Needs further work on the analytic integrator or QE martingale correction.
- [x] Update artifacts:
  - [x] Replace `heston_qe_vs_analytic.png` with a price/IV RMSE convergence plot (log–log) across three scenarios and both QE/Euler.
  - [x] Update `docs/Results.html` text to describe the remaining bias.

**Target outcome:**

- Either:
  - QE is “good enough” (bias < ~0.5 tick and within 2σ of analytic MC error over a representative grid), or
  - QE is clearly marked experimental and not used in WRDS / critical examples.

### 1.2. Branch coverage in hard code paths

Coverage is already high for lines/functions; branch coverage is lower, especially in barrier, risk, and CLI logic. (Previous coverage report: ~82% lines, ~94% functions, ~45% branches overall, with some files much lower.)  

**Focus areas:**

- Barrier analytics and MC:
  - All barrier types (up/down, in/out).
  - Edge cases where spot starts near barrier or crosses between time steps (Brownian bridge).
  - Zero-vol and zero-time limits.
- Risk module:
  - VaR/CVaR quantile interpolation.
  - Kupiec pass/fail cases.
  - Corner cases with short PnL series and empty buckets.
- CLI:
  - Primary subcommands.
  - Error paths (missing args, invalid config, unknown product).

**Tasks:**

- [ ] Add focused GTest cases for barrier BS (`src/bs_barrier_rr.cpp`) covering:
  - Each barrier type.
  - Extreme strikes/moneyness.
  - Cases where barrier == spot, barrier → 0, barrier → ∞.
- [ ] Add tests for barrier MC:
  - [ ] Synthetic paths with deterministic hitting should match analytic within allowed MC error.
  - [ ] Use Brownian bridge crossing detection tests.
- [ ] Add tests for risk module:
  - [ ] Synthetic PnL series where VaR coverage is “by construction” at 95%, 99%.
  - [ ] Series that intentionally fails Kupiec (too many breaches).
  - [ ] Assert correct pass/fail decisions and p-values ordering.
- [ ] Add CLI integration tests:
  - [ ] Run `quant_cli` with representative sets of arguments (vanilla, barrier, American, Heston).
  - [ ] Verify it returns 0 and prints parseable JSON.
  - [ ] Add at least one test that validates error handling (missing required parameter yields non‑zero exit).

**Target outcome:**

- [ ] Achieve:
  - Branch coverage ≥ ~70% overall.
  - Branch coverage ≥ ~60% in barrier and risk modules.
- [ ] Document coverage deltas in `docs/ROADMAP.md` and link to coverage HTML.

---

## Phase 2 – WRDS OptionMetrics as flagship

**Objective:** Turn the WRDS pipeline into the main “real data” story with concrete, quotable metrics.

### 2.1. Harden WRDS pipeline

Current pipeline (SPX from IvyDB, secid via `optionm.secnmd`, `optionm.opprcdYYYY`, filtering stale quotes, recomputing IV, vega-weighted Heston calibration, OOS and Δ-hedged metrics) is solid but under‑documented at the metric level.:contentReference[oaicite:6]{index=6}  

**Tasks:**

- [ ] Add/confirm environment handling:
  - `WRDS_ENABLED`, `WRDS_USERNAME`, `WRDS_PASSWORD` as env flags.
  - `WRDS_USE_SAMPLE=1` for bundled sample run.
- [ ] Ensure:
  - [ ] WRDS live runs never write raw tables to disk under the repo.
  - [ ] Only aggregated CSV/PNGs under `docs/artifacts/wrds/` get committed.
- [x] Make sampling panel explicit:
  - [x] Document trade dates and regime (calm/stress) in `wrds_pipeline_dates_panel.yaml` (summarised in `docs/WRDS_Results.md`).
  - [x] Add a short narrative of why those dates (e.g., pre‑COVID, March 2020, 2022 inflation, recent quiet).

### 2.2. Heston vs Black–Scholes comparison

**Goal:** Show that Heston meaningfully improves IV fit and hedging relative to a simpler model.

**Tasks:**

- [x] Implement BS baseline:
  - [x] Per tenor bucket, estimate a single BS σ via vega-weighted least squares in IV space.
  - [x] Write aggregated metrics to `docs/artifacts/wrds/wrds_agg_pricing_bs.csv` and `wrds_agg_oos_bs.csv`.
- [ ] Compare BS vs Heston:
  - [ ] Use existing Heston artifacts (`wrds_agg_pricing.csv`, `wrds_agg_oos.csv`, `wrds_agg_pnl.csv`).:contentReference[oaicite:7]{index=7}  
  - [ ] Compute per-bucket differences:
    - ΔIV RMSE (vol pts).
    - ΔOOS IV MAE (bps).
    - Δprice RMSE (ticks).
    - ΔΔ‑hedged PnL σ and maybe mean.
- [ ] Add WRDS summary plots:
  - [ ] Bar chart (per bucket) of IV RMSE: BS vs Heston.
  - [ ] Heatmap of OOS IV MAE in bps vs tenor & moneyness (Heston).
  - [ ] Boxplots / violin plots of Δ‑hedged 1d PnL per bucket.

**Target outcome:**

- [ ] A 1–2 paragraph executive summary in `docs/WRDS_Results.md` with concrete numbers (you fill in):

  > On N SPX trade dates (2017–2024), vega‑weighted IV RMSE falls from X to Y vol pts (≈Z% improvement) when moving from BS to Heston in 30–90d tenors. OOS IV MAE drops from A to B bps, and Δ‑hedged 1d PnL σ shrinks by C% in ATMF buckets, with mean PnL statistically indistinguishable from 0.

- [x] Link to the WRDS section explicitly from `README.md` “Results at a Glance”.

### 2.3. Use real WRDS data in tests/CI (opt‑in)

**Tasks:**

- [ ] Introduce CTest label `MARKET` (or confirm existing) for WRDS-dependent tests.
- [ ] Add tests that:
  - [ ] Run the WRDS pipeline on a small subset of the panel (1–2 dates) when `WRDS_ENABLED=1`.
  - [ ] Assert that aggregated stats remain within a tolerance window (to guard against silent regressions).
- [ ] Describe in `AGENTS.md`:
  - Primary commands for WRDS runs:
    - `python -m wrds_pipeline.pipeline --dateset wrds_pipeline_dates_panel.yaml --use-sample`
    - Same without `--use-sample` when `WRDS_ENABLED=1`.
  - Guarantee that tests are **never** wired to push raw data into git.

---

## Phase 3 – Developer experience & documentation

**Objective:** Make it trivial for humans and agents to understand, extend, and validate the library.

### 3.1. README and docs “Highlights” section

**Tasks:**

- [ ] At the top of `README.md`, add “Highlights” (3–5 bullets), e.g.:

  - “Tri-engine BS/MC/PDE agreement <5 bps across strikes on 200k paths (MC CI overlaps PDE/analytic curves).”  
  - “Sobol QMC + Brownian bridge delivers ≈1.4× lower RMSE than PRNG at matched wall-clock on European and Asian payoffs.”  
  - “QuantLib parity: vanilla, barrier, and American prices within 1¢ of QuantLib reference engines.”  
  - “WRDS OptionMetrics SPX: Heston calibration + Δ‑hedged PnL across multiple regimes (see WRDS_Results).”

- [ ] Make sure each bullet links to the relevant plot / CSV / manifest entry on the Results page.

### 3.2. Results & WRDS docs tightening

**Tasks:**

- [ ] `docs/Results.html`:
  - [ ] Add a tiny metrics table per section (Tri-engine, QMC, PDE, MC Greeks, Heston QE, GBench, QuantLib parity).
- [ ] `docs/WRDS_Results.md`:
  - [ ] Add a table of headline WRDS metrics (pricing, OOS, PnL).
  - [ ] Add a “How to reproduce” section with exact commands and env expectations.

### 3.3. Per-module design notes (optional)

If time allows, add short design docs under `docs/`:

- `docs/MC_Design.md`: RNG choices, variance reduction, Greeks methods.
- `docs/PDE_Design.md`: grid structure, BCs, American LCP, convergence.
- `docs/Heston_Design.md`: analytic CF, QE scheme, calibration objective.

These are mainly for future you and senior reviewers.

---

## Phase 4 – Stretch numerical/features (optional, resume candy)

Only after Phases 1–3:

### 4.1. Local vol or SABR stub

- [ ] Implement Dupire local vol from a supplied IV surface grid (even toy surfaces).
- [ ] Provide a PDE pricer that takes a tabulated local vol and prices a vanilla option.
- [ ] Add one or two demo plots showing how local vol smiles differ from BS/Heston.

### 4.2. Calibration CLI

- [ ] Add a `quant_cli calibrate` subcommand:
  - Input: CSV of strikes, tenors, IVs.
  - Output: best-fit parameters and goodness-of-fit metrics.
- [ ] Wire this subcommand into WRDS pipeline instead of bespoke calibration code.

### 4.3. Risk analytics demo

- [ ] Create `docs/Risk_Results.md`:
  - Example VaR/CVaR using your MC engine.
  - At least one Kupiec test example (pass and fail) with interpretation.

---

## Phase 5 – Automation & Codex integration

**Objective:** Let Codex safely act as a co-maintainer.

### 5.1. AGENTS.md & Codex profile

- [ ] Maintain a concise but detailed `AGENTS.md` at repo root with:
  - Setup/test commands.
  - Conventions for running WRDS tests.
  - Rules for updating artifacts and docs.
  - Git/commit guidelines for agents.
- [ ] Create a Codex CLI profile (`quant-pricer-autopilot`) configured for:
  - Model: `gpt-5.1-codex-max`.  
  - `sandbox_mode = "workspace-write"`, network access enabled for WRDS and web search.  
  - `approval_policy = "never"` (or a slightly more cautious mode if you prefer).
  - Features: `web_search_request = true`, `streamable_shell = true`, `apply_patch_freeform = true`, `ghost_commit = true`.

### 5.2. “One command” reproducible runs

- [ ] Ensure `scripts/reproduce_all.sh` is the single entry point to regenerate all artifacts.
- [ ] Document this in `AGENTS.md` so Codex automatically finds and uses it.

---

## Versioning

Each release:

- Update this roadmap, marking completed items.
- Snapshot headline metrics (WRDS, QMC, PDE, coverage).
- Update `CHANGELOG.md` and, if relevant, `docs/WRDS_Results.md`.
