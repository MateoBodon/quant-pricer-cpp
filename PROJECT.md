# quant-pricer-cpp project intent

## Project profile

- **Purpose:** a C++20 and Python derivatives-pricing library with reproducible,
  artifact-bound numerical evidence.
- **Product type:** open-source library and research-validation system.
- **Risk tier:** medium. The library computes prices and conditional risk
  measures, but it is not a trading or live-risk system.
- **Primary languages:** C++20, Python, CMake, and shell.
- **External services:** GitHub Actions, GitHub Releases, and GitHub Pages.

## Goals

- Make deterministic Black–Scholes portfolio valuation and exact user-supplied
  stress scenarios a production-shaped, first-class C++/Python surface.
- Preserve the broader analytic, Monte Carlo/QMC, PDE, Heston, SSVI, exotic,
  VaR/ES, and reproducibility capabilities without inflating their claims.
- Ship supported Python wheels and a build-complete source distribution through
  a green cross-platform release workflow.
- Bind accuracy, determinism, performance, and package claims to inspectable
  tests, receipts, manifests, and frozen artifacts.

## Non-goals

- Trading alpha, return forecasts, order execution, or live P&L.
- Probabilistic market-risk validation or claims that user-supplied stress
  scenarios represent future market distributions.
- Unqualified benchmark claims across hardware, compilers, or workloads.
- PyPI or TestPyPI availability unless the corresponding provider state has
  been separately verified.

## Current product state

- **v0.4.0 lead surface:** `bs_portfolio_risk` and
  `bs_portfolio_scenarios` for mixed European call/put portfolios.
- **Risk output:** position price/value/Greeks plus quantity-weighted portfolio
  value, delta, gamma, vega, theta, and rho.
- **Stress output:** exact five-factor repricing for spot, volatility, rate,
  dividend, and elapsed-time shocks, with aggregate or position detail.
- **Evidence:** independent QuantLib parity, exact zero-shock identity,
  concurrent deterministic replay, sanitizers, package validation, and frozen
  hardware-bound benchmark receipts.
- **Distribution:** source builds and GitHub release assets are authoritative;
  the project does not claim a PyPI package.

## Quickstart

```bash
cmake -S . -B build -DCMAKE_BUILD_TYPE=Release -DQUANT_ENABLE_PYBIND=ON
cmake --build build --parallel
ctest --test-dir build --output-on-failure
python python/examples/quickstart.py
python python/examples/portfolio_risk.py
```

For an installed Python package, use a wheel matching the running Python and
platform from the GitHub release, then run
`python python/scripts/cibw_test_suite.py`.

## Architecture and invariants

- `include/quant/` and `src/` contain the native pricing and risk engines.
- `python/pybind_module.cpp` exposes the supported Python API.
- `tests/` owns native, Python, package, documentation, and release gates.
- `docs/artifacts/` contains frozen evidence; `docs/product/` explains the
  product contract and claim boundaries.
- `.github/workflows/` owns CI, Pages, validation-pack, wheel, sdist, manifest,
  and GitHub release automation.
- Public claims must remain reproducible or artifact-bound, and public package
  availability must be proven by provider evidence.

## Links

- [README and quickstart](README.md)
- [v0.4.0 product and evidence hub](docs/product/DERIVATIVES_SYSTEM_HUB.md)
- [v0.4.0 release notes](docs/releases/v0.4.0.md)
- [Generated documentation](https://mateobodon.github.io/quant-pricer-cpp/)
- [GitHub releases](https://github.com/MateoBodon/quant-pricer-cpp/releases)
