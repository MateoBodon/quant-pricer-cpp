# Metrics Snapshot

Generated at: 2025-12-22T00:19:37.698292+00:00
Artifacts root: docs/artifacts
Manifest git sha: ae2691df74d6b813e23a231ee5308a6573456f45

## Status overview
| Block | Status | Highlights |
| --- | --- | --- |
| tri engine agreement | ok | max|MC-BS|=0.00754518, max|PDE-BS|=0.00058701, MC CI covers BS=True |
| qmc vs prng equal time | ok | median PRNG/QMC RMSE ratio=5.58787 (asian: med=2.54774; call: med=8.62801) |
| pde order | ok | slope=-2.0124, rmse_finest=0.00115728 |
| ql parity | ok | max diff=0.861583 cents |
| benchmarks | ok | MC paths/sec (1t)=1.1417e+07, eff@max=0.135165 |
| wrds | ok | median iv_rmse=0.0160071 (sample bundle regression harness) |

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
| rmse_ratio_overall_median | 5.58787 |
| payoffs | asian={'rows': 6, 'rmse_ratio_median': 2.5477375238, 'rmse_ratio_min': 2.5477375238, 'rmse_ratio_max': 2.5477375238}, call={'rows': 6, 'rmse_ratio_median': 8.6280067686, 'rmse_ratio_min': 8.6280067686, 'rmse_ratio_max': 8.6280067686} |

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
| runtime_ratio_median | 2.67438 |
| runtime_ratio_by_category | american=12.8176, barrier=2.67438, vanilla=1.81767 |

### Benchmarks
Status: ok

### Wrds
Status: ok
