# quant-pricer-cpp API Reference

Welcome to the generated reference for quant-pricer-cpp. v0.4.0 leads with
vectorized Black–Scholes portfolio risk and exact five-factor stress, while
retaining the library's analytic, Monte Carlo/QMC, PDE, Heston, SSVI, and exotic
pricing surfaces. These pages are built from the public tag source.

@image html portfolio-risk-v040.svg "Recorded v0.4.0 portfolio-risk and aggregate-stress speedups"

The chart is a presentation of the frozen
`portfolio_risk_benchmark_v1.json` receipt, not a rerun or universal throughput
claim. See the [v0.4.0 product and evidence hub](../product/DERIVATIVES_SYSTEM_HUB.md)
for workloads, independent parity, determinism, resource use, and limitations.

## How to Navigate

- Use the **left-hand sidebar** tree to jump between namespaces (`quant::bs`,
  `quant::mc`, `quant::pde`, etc.) and source files. The search box filters both
  symbols and pages in real time.
- The **Index** tab lists every documented class/function; choose *Modules* for a
  higher-level entry point (pricing engines, stochastic volatility helpers,
  grids, RNG utilities).
- Each engine page links back to the corresponding implementation file so you
  can inspect the exact algorithms compiled into the library.

## Frequently Visited Areas

- **Portfolio risk and stress**: `quant::portfolio` namespace – typed positions,
  quantity-weighted price/Greek aggregation, and exact scenario repricing with
  optional position attribution.
- **Black–Scholes analytics**: `quant::bs` namespace – closed-form prices,
  Greeks, parity, and implied volatility solvers used across the project.
- **Monte Carlo engine**: `quant::mc` namespace – deterministic counter-based
  RNG, Sobol/Brownian bridge drivers, variance-reduction estimators, and pathwise
  Greeks.
- **PDE stack**: `quant::pde` namespace – Crank–Nicolson solver, grid utilities,
  boundary conditions, and Rannacher smoothing used in the finite-difference
  pipelines.
- **Exotic payoffs**: `quant::barrier`, `quant::asian`, `quant::lookback`,
  `quant::american`, and `quant::digital` namespaces.
- **Stochastic volatility (Heston)**: `quant::heston` namespace – analytic
  characteristic-function pricing plus Andersen QE Monte Carlo.

## Reproduce Locally

```bash
cmake -S . -B build -DCMAKE_BUILD_TYPE=Release
cmake --build build --target quant_cli --parallel
doxygen Doxyfile
```

The HTML bundle is emitted under `docs/html/index.html`. The GitHub Actions job
(`Docs Pages`) runs the same steps and deploys the output to the project’s Pages
site.
