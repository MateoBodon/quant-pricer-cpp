# Derivatives Pricing and Risk System

Status: **v0.4.0 public product contract and evidence hub**.

## What v0.4.0 ships

The release adds two production-shaped Black–Scholes European portfolio APIs:

- `bs_portfolio_risk`: vectorized price, value, delta, gamma, vega, theta, and
  rho with quantity-weighted portfolio totals;
- `bs_portfolio_scenarios`: exact five-factor stress repricing with compact
  aggregate-only output or optional position attribution.

The same release retains the established analytic, Monte Carlo/QMC, PDE,
Heston, SSVI, exotic-option, VaR/ES, C++/CMake, Python, and reproducible
artifact surfaces from v0.3.7. It does not replace those engines or inflate
their claim boundaries.

The recorded Apple M3 Pro evaluator measured `20.18x` risk-batch speedup and
`27.92x` aggregate-scenario speedup, with independent QuantLib errors no worse
than `3.91e-14` for price, `3.40e-12` for Greeks, and `2.66e-13` for portfolio
scenario P&L. Exact zero-shock identity and 32/32 concurrent replay identity
also passed. These numbers remain bound to their host, workloads, and receipts.

Download signed-off wheels, the source distribution, validation payload, and
machine-readable release manifest from the
[v0.4.0 GitHub release](https://github.com/MateoBodon/quant-pricer-cpp/releases/tag/v0.4.0).

## API contract

The selected surface accepts a contiguous `float64` position matrix with eight
columns:

`option_type, quantity, spot, strike, rate, dividend, volatility, time`

`option_type` is `1` for a call and `-1` for a put. A risk batch returns
position-level columns:

`price, value, delta, gamma, vega, theta, rho`

Portfolio-total columns are the quantity-weighted fields:

`value, delta, gamma, vega, theta, rho`

Position sensitivities are quantity-weighted except `price`. Vega is per 1.0
absolute volatility and theta is the analytic Black-Scholes calendar-time
sensitivity already used by the library.

A scenario matrix has five columns:

`spot_return, volatility_shift, rate_shift, dividend_shift, time_elapsed`

Each scenario performs exact repricing with `spot * (1 + spot_return)`, additive
rate/dividend/volatility shifts, and `max(time - time_elapsed, 0)`. It returns
scenario-level portfolio P&L and may optionally return the contiguous
scenario-major position P&L matrix. Inputs that are non-finite, have an unknown
option type, make spot/strike/volatility invalid, use negative time or elapsed
time, or would overflow an output allocation fail closed before pricing.

## Evaluator

The capability is promotable only if all of the following pass without changing
the frozen tolerances after seeing results:

- **Independent correctness:** deterministic calm, skew, carry, near-expiry,
  deep-ITM/OTM, long/short, call/put cases agree with QuantLib analytic European
  prices and available Greeks to `1e-10` absolute or `1e-10` relative tolerance;
  exact scenario P&L agrees with an independently constructed QuantLib repricer
  to `1e-9` absolute tolerance.
- **Internal identities:** portfolio totals equal the exact sum of returned
  position contributions; zero shocks produce exactly zero P&amp;L; scenario order,
  position order, and repeated/concurrent calls are deterministic.
- **Robustness:** invalid shapes, values, option types, post-shock states, and
  oversized allocations fail before partial output is returned. Expiry behavior
  agrees with intrinsic-value conventions.
- **Performance:** on the recorded host/toolchain, the native Python risk batch
  is at least `10x` faster than equivalent existing scalar binding calls for a
  fixed 100,000-position canary, and exact aggregate-only scenario repricing is
  at least `10x` faster than scalar binding orchestration on a fixed workload.
  Median of at least seven measured repetitions is used after warm-up.
- **Resources:** wall time, throughput, peak RSS, input/output sizes, CPU model,
  OS, compiler, Python, NumPy, QuantLib, and package version are recorded in a
  deterministic JSON receipt. Detailed scenario output must document its
  `scenario_count * position_count * 8`-byte payload; aggregate-only mode must
  avoid allocating that matrix.
- **Product surface:** public C++ declarations, installed Python bindings,
  focused native tests, an independent Python/QuantLib test, a runnable example,
  and concise README/limitations agree on units and shapes.
- **Regression:** focused tests, the relevant FAST suite, data-policy guard, and
  an installed-wheel smoke test pass. Sanitizer coverage is required for the new
  native core unless the current toolchain cannot support it, in which case the
  exact limitation is recorded.

## Claim boundary

This is deterministic Black-Scholes valuation and stress infrastructure, not a
market-risk model validation, forecast, hedge-profit, P&L, or live-trading
claim. Scenario outputs are conditional on user-provided shocks and unchanged
model assumptions. Model risk, volatility-surface dynamics, early exercise,
barriers, counterparty exposure, and cross-asset correlation remain outside the
first contract.

## Verified outcome

| Evaluator | Frozen gate | Current evidence | Result |
|---|---:|---:|---|
| QuantLib price/Greek parity | abs or rel `<=1e-10` | worst price `3.91e-14`; worst Greek `3.40e-12` (theta) | pass |
| QuantLib exact scenario P&L | abs `<=1e-9` | position `2.06e-13`; portfolio `2.66e-13` | pass |
| Zero-shock identity | exact zero | exact zero | pass |
| Concurrent determinism | bitwise identical | 32/32 concurrent replays identical | pass |
| Risk-batch speedup | `>=10x` | `20.18x`; 20.25M positions/s | pass |
| Scenario speedup | `>=10x` | `27.92x`; 32.13M cells/s | pass |
| Installed API | exact v0.4.0 wheel | wheel import, API smoke, version identity | pass |
| Native sanitizers | ASan + UBSan | five focused tests pass | pass |

The installed-wheel benchmark used an Apple M3 Pro, Apple clang 21.0.0,
Python 3.12.2, NumPy 2.5.0, and QuantLib 1.42.1. It measured medians after one
warm-up over seven repetitions. The risk workload contains 100,000 positions;
the scenario workload contains 20,000 positions by 16 shocks. Peak process RSS
was 121,831,424 bytes. Aggregate scenario output was 128 bytes; requesting full
attribution for that workload would create a 2,560,000-byte matrix.

The first unfused risk implementation reached only `9.94x` and failed the
frozen `10x` gate. The promoted fused analytic path reuses `d1`, `d2`, discount,
and density terms across price and all six Greeks; the gate was not relaxed.

Evidence:

- [`portfolio_risk_quantlib_parity_v1.json`](../artifacts/portfolio_risk_quantlib_parity_v1.json)
- [`portfolio_risk_benchmark_v1.json`](../artifacts/portfolio_risk_benchmark_v1.json)
- [`portfolio_risk_release_v040.json`](../artifacts/portfolio_risk_release_v040.json)
- implementation commit `60c4e9daefbbe481b3002eaa6c1429b069ae79b3`

## Before and after

| Product surface | Before v0.4.0 | v0.4.0 |
|---|---|---|
| Portfolio valuation | user-maintained scalar Python loop | one native `(n,8)` batch |
| Portfolio Greeks | no aggregate API | value, delta, gamma, vega, theta, rho |
| Stress testing | no cross-position scenario API | five-factor exact repricing |
| Attribution memory | user-controlled/unbounded | explicit aggregate-only or detailed mode |
| Correctness proof | scalar BS tests | independent QuantLib portfolio and scenario parity |
| Packaging | v0.3.7 cross-platform wheel baseline | v0.4.0 wheels + build-complete sdist + installed smoke + release manifest |

## Verification inherited by the release

- Five focused native tests passed in Release and under AddressSanitizer plus
  UndefinedBehaviorSanitizer. Apple leak detection is unsupported, so only
  `detect_leaks` was disabled; ASan/UBSan stayed active.
- The independent Python evaluator passed 60 mixed position cases and 72
  scenario cells, four invalid-position cases, one invalid post-shock case,
  exact aggregation, expiry behavior, and concurrent replay.
- The full FAST selection produced 89 passes, one existing RNG skip, and the
  same two locked SSVI hedge failures. Those one-use tests reject any changed
  `CMakeLists.txt`; the consumed hedge contract was not altered or reopened.
- The data-policy guard passed. No WRDS query, raw data, simulation, or cloud
  work was needed to establish the deterministic v0.4.0 product evidence.
- The exact local wheel SHA-256 is
  `bfc005727c385f8c7978e670cc0de6295f7540746040dbd1c92771602a6760d1`;
  the build-complete sdist SHA-256 is
  `ae4d41b9a3b283a7a401ca169f6702a9de5ea6ee9774433c499876b934296a3c`.
  Those hashes cover the original macOS arm64 evaluator build. The GitHub
  release's `release-manifest.json` separately binds every cross-platform wheel
  and source distribution to the public tag commit. PyPI is not claimed.

## Limitations

- The engine is Black-Scholes European vanilla risk, not volatility-surface or
  model-risk dynamics.
- Inputs use one spot per position; shared-underlier normalization/netting is a
  caller concern in v0.4.0.
- Scenario shocks are deterministic and user supplied. They have no
  probability, correlation, forecast, VaR, hedge, or economic-optimality claim.
- Detailed attribution is intentionally materialized as a dense matrix; large
  users should prefer aggregate-only mode or chunk scenarios.
- Early exercise, barriers, path dependence, counterparty exposure, and XVA are
  outside this first portfolio contract.
