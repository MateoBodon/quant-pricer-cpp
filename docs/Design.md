# quant-pricer-cpp Design Notes

## Pricing Engines
- **Black–Scholes (BS)**: Closed-form analytics for European options with full Greek support. Provides canonical comparisons for stochastic and PDE engines.
- **Monte Carlo (MC)**: GBM path simulator with variance reduction (antithetic, control variate) and QMC acceleration (Sobol with Brownian bridge). Directly exposes streaming statistics (mean/SE/CI) for prices and Greeks.
- **Finite-Difference PDE**: Crank–Nicolson in S- or log-space with optional tanh stretching near the strike. Supports Dirichlet and Neumann upper boundaries plus Rannacher start-up to stabilise non-smooth payoffs.
- **Barrier PDE/MC/BS**: Shared abstractions around `quant::BarrierSpec` drive analytic, PDE, and Monte Carlo barrier pricing for consistency checks.
- **American Options**: Threefold implementation—binomial (CRR), PSOR finite-difference, and LSMC—allowing cross-validation between tree, PDE, and Monte Carlo approaches.

## Grid Construction
- **Uniform & Log Grids**: Spatial grid generation supports linear S-space or log-space, driven by `GridSpec` (`num_space`, `num_time`, `s_max_mult`, `stretch`).
- **Stretch Mapping**: Optional tanh mapping clusters nodes around the strike to control truncation error without exploding grid size.
- **Time Discretisation**: Uniform time stepping with optional Rannacher (two implicit Euler steps) to damp initial payoff kinks.

## Boundary Conditions
- **Dirichlet**: Clamps the solution using analytic asymptotics (`max(0, S−K)` shaped) at the upper boundary.
- **Neumann**: Enforces derivative conditions for log-space grids (`∂V/∂S(S_max, t) = e^{−q(T−t)}`) via a modified final row in the tridiagonal system.
- **PSOR Early Exercise**: For American options, PSOR enforces `V ≥ intrinsic` after each sweep; the ω relaxation parameter is benchmarked to minimise iterations.

## Monte Carlo Architecture
- **Streaming Statistics**: Welford accumulators underpin every estimator, emitting mean, SE, and 95% CI without storing paths.
- **Threading**: Optional OpenMP parallelism with deterministic per-thread seeding. CLI exposes `--threads=` to tune at runtime.
- **Sampler Abstraction**: CLI switches between PRNG and Sobol (scrambled or not) while Brownian bridge reduces effective dimension when `num_steps > 1`.

## Module Layout
- `include/quant/` exposes engine APIs (`black_scholes`, `mc`, `pde`, `american`, etc.).
- `src/` contains engine implementations alongside shared utilities (grid builders, regression helpers).
- `tests/` holds GTest suites covering analytics parity, variance reduction, boundary conditions, and American cross-checks.
- `benchmarks/` hosts Google Benchmark entry points for MC throughput, MC RMSE comparisons, PDE wall-time, and PSOR iteration studies.
- `scripts/demo.sh` orchestrates reproducible builds/runs, capturing CSVs, PNGs, and a synthesized one-pager PDF.
