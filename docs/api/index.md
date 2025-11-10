# quant-pricer-cpp API Reference

Welcome to the generated reference for the quant-pricer-cpp library. These pages are
published automatically from the main branch and mirror the exact code that ships
in the repository.

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
