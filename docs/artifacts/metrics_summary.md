# Metrics Snapshot

Generated at: 2025-12-21T21:34:11.595989+00:00
Artifacts root: docs/artifacts
Manifest git sha: 718e430b0e1ad6085274fcbfe9eb0231372512ad

## Status overview
| Block | Status | Highlights |
| --- | --- | --- |
| tri engine agreement | ok | max|MC-BS|=0.00754518, max|PDE-BS|=0.00058701, MC CI covers BS=True |
| qmc vs prng equal time | ok | median PRNG/QMC RMSE ratio=6.19927 (asian: med=3.03888; call: med=9.35967) |
| pde order | ok | slope=-2.0124, rmse_finest=0.00115728 |
| ql parity | ok | max diff=0.861583 cents |
| benchmarks | ok | MC paths/sec (1t)=1.33885e+07, eff@max=0.12541 |
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
| rmse_ratio_overall_median | 6.19927 |
| payoffs | asian={'rows': 6, 'rmse_ratio_median': 3.0388772979, 'rmse_ratio_min': 3.0388772979, 'rmse_ratio_max': 3.0388772979}, call={'rows': 6, 'rmse_ratio_median': 9.3596716111, 'rmse_ratio_min': 9.3596716111, 'rmse_ratio_max': 9.3596716111} |

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
| runtime_ratio_median | 5.96364 |
| runtime_ratio_by_category | american=13.0431, barrier=5.96364, vanilla=1.74599 |

### Benchmarks
Status: ok

### Wrds
Status: ok
