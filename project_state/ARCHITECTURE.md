# Architecture

quant-pricer-cpp is a C++20 option-pricing stack with three independent engines (analytic Black–Scholes, Monte Carlo, Crank–Nicolson PDE), exotics (barriers, Asians, lookbacks, American PSOR/LSMC), Heston analytic + QE MC, a CLI (`quant_cli`), Python bindings (`pyquant_pricer`), and a WRDS OptionMetrics pipeline for real-market diagnostics. Everything is reproducible through committed CSV/PNG artifacts and a manifest.

## Top-Level Layout
- `include/quant/` – Public C++ API headers for engines, utilities (math, rng, stats, grids, term structures).
- `src/` – Engine implementations and CLI entry (`main.cpp`).
- `python/` – pybind11 module exposing BS/MC/PDE/Heston plus enums/schedules; `examples/quickstart.py`.
- `wrds_pipeline/` – WRDS OptionMetrics ingestion, Heston/BS calibration, OOS pricing, Δ‑hedged PnL, comparison plots.
- `scripts/` – Experiment drivers (tri-engine agreement, QMC vs PRNG equal time, MC Greeks CI, Heston QE vs analytic, PDE convergence, QuantLib parity, WRDS helpers).
- `tests/` – GTest C++ unit suite plus Python FAST/MARKET smoke tests.
- `benchmarks/` – Google Benchmark entry points (MC throughput, PDE walltime/order, PSOR iterations).
- `docs/` – Results, design notes, coverage HTML, and committed artifacts under `docs/artifacts/`.
- `data/` – Sample/normalized option surfaces and schema docs; **no raw WRDS tables**.
- `cmake/`, `external/` – Build helpers and vendored gtest/benchmark/pcg.

## Main Components
- **Analytics (BS)**: Closed-form European calls/puts, all Greeks, implied-vol solver, Reiner–Rubinstein barrier formula.
- **Monte Carlo**: GBM with antithetic + control variate, counter-based RNG or MT19937, Sobol (scrambled) + Brownian bridge, pathwise/LRM Greeks, barrier MC with Brownian-bridge crossing fix, Asian/lookback, basket & Merton jump-diffusion, risk VaR/CVaR.
- **PDE**: Crank–Nicolson in S or log space, tanh stretching, Dirichlet/Neumann boundaries, Rannacher start-up, barrier PDE in log-space, American PSOR and LSMC.
- **Heston**: Analytic call via characteristic function (Gauss–Laguerre), implied vol helper, Andersen QE MC (Euler fallback).
- **Interfaces**: `quant_cli` multiplexes engines; pybind exposes the same primitives to Python.
- **WRDS pipeline**: Ingest OptionMetrics/IvyDB (or bundled sample), aggregate surfaces, calibrate Heston + BS baseline, compute OOS IV/price errors and Δ‑hedged PnL, aggregate across dates, plot summaries, and update `docs/artifacts/wrds/*`.

## Data Flow (high level)
```
market data (WRDS or sample CSV) 
    → wrds_pipeline.ingest_sppx_surface (filter DTE≥21d, 0.75–1.25 moneyness, compute IV/vega)
    → aggregated tenor×moneyness surface CSVs
    → calibrate_heston (least-squares in IV space, bootstrap CIs) & calibrate_bs (tenor σ baseline)
    → oos_pricing (next-day IV/price MAE), delta_hedge_pnl (Δ-hedged 1d PnL)
    → per-date artifacts + aggregated `wrds_agg_*.csv` + comparison plots under docs/artifacts/wrds
```
Other experiment flows:
- Synthetic/normalized CSVs (`data/`) → scripts/calibrate_heston.py → artifacts/heston/*.
- Deterministic scenarios → scripts/tri_engine_agreement.py, qmc_vs_prng_equal_time.py, pde_order_slope.py, mc_greeks_ci.py, heston_qe_vs_analytic.py, ql_parity.py → docs/artifacts/*.csv|png updated + manifest.

## Control/Execution Paths
- **CLI** (`build/quant_cli`): subcommands `bs`, `iv`, `mc`, `barrier bs|mc|pde`, `american binomial|psor|lsmc`, `pde`, `digital`, `asian`, `lookback`, `heston`, `risk`. Parses params, builds engine configs, prints scalar/JSON with optional CI and multi-thread override.
- **Python bindings**: construct structs (McParams, GridSpec, BarrierSpec, HestonParams, PiecewiseConstant) and call pricing/greeks functions directly.
- **Pipelines**: `python -m wrds_pipeline.pipeline --dateset wrds_pipeline_dates_panel.yaml [--use-sample|--fast] [--output-root …]`; `scripts/reproduce_all.sh` rebuilds Release, runs FAST/SLOW tests & experiments, regenerates docs/artifacts + manifest.
