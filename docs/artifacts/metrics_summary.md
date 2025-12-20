# Metrics Snapshot

Generated at: 2025-12-20T22:51:28.540185+00:00
Artifacts root: /Users/mateobodon/Documents/Programming/Projects/quant-pricer-cpp/docs/artifacts
Manifest git sha: cf1d770d18d26b8db15c0638c692ac50f5f2747e

## Status overview
| Block | Status | Highlights |
| --- | --- | --- |
| tri engine agreement | ok | max|MC-BS|=0.00754518, max|PDE-BS|=0.00058701, MC CI covers BS=True |
| qmc vs prng equal time | ok | median PRNG/QMC RMSE ratio=5.97083 (asian: med=2.75711; call: med=9.18455) |
| pde order | ok | slope=-2.0124, rmse_finest=0.00115728 |
| ql parity | ok | max diff=0.861583 cents |
| benchmarks | ok | MC paths/sec (1t)=1.07301e+07, eff@max=0.145201 |
| wrds | ok | median iv_rmse=0.0160071 (sample bundle) |

### Tri Engine Agreement
Status: ok

| Metric | Value |
| --- | --- |
| rows | 4 |
| max_abs_error_mc | 0.00754518 |
| max_abs_error_pde | 0.00058701 |
| mc_ci_coverage_fraction | 1 |
| mc_ci_covers_bs | True |

### Qmc Vs Prng Equal Time
Status: ok

| Metric | Value |
| --- | --- |
| rmse_ratio_overall_median | 5.97083 |
| payoffs | asian={'rows': 6, 'rmse_ratio_median': 2.7571124724, 'rmse_ratio_min': 2.7571124724, 'rmse_ratio_max': 2.7571124724}, call={'rows': 6, 'rmse_ratio_median': 9.1845487453, 'rmse_ratio_min': 9.1845487453, 'rmse_ratio_max': 9.1845487453} |

### Pde Order
Status: ok

| Metric | Value |
| --- | --- |
| rows | 3 |
| slope | -2.0124 |
| r2 | 0.999997 |
| rmse_finest | 0.00115728 |
| nodes_finest | 401 |
| timesteps_finest | 400 |

### Ql Parity
Status: ok

| Metric | Value |
| --- | --- |
| max_abs_diff_cents_overall | 0.861583 |
| by_category | american={'max_abs_diff_cents': 0.79875157, 'rows': 1}, barrier={'max_abs_diff_cents': 0.0410715241, 'rows': 1}, vanilla={'max_abs_diff_cents': 0.8615834347, 'rows': 1} |
| runtime_ratio_median | 32.5066 |
| runtime_ratio_by_category | american=61.7547, barrier=32.5066, vanilla=8.3802 |

### Benchmarks
Status: ok

### Wrds
Status: ok
