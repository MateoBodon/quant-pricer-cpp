# Metrics Snapshot

Generated at: 2025-12-22T21:02:46.901536+00:00
Artifacts root: docs/artifacts
Manifest git sha: aeb31c63c19ae8671a3be1f31bf7b003c4492c06

## Status overview
| Block | Status | Highlights |
| --- | --- | --- |
| tri engine agreement | ok | max|MC-BS|=0.00754518, max|PDE-BS|=0.00058701, MC CI covers BS=True |
| qmc vs prng equal time | ok | median PRNG/QMC RMSE ratio=7.41202 (asian: med=2.62594; call: med=12.1981) |
| pde order | ok | slope=-2.0124, rmse_finest=0.00115728 |
| ql parity | ok | max diff=0.861583 cents |
| benchmarks | ok | MC paths/sec (1t)=1.30364e+07, eff@max=0.124117 |
| wrds | ok | median iv_rmse=0.00120828 (sample bundle regression harness) |

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
| rmse_ratio_overall_median | 7.41202 |
| payoffs | asian={'rows': 6, 'rmse_ratio_median': 2.6259412744, 'rmse_ratio_min': 2.6259412744, 'rmse_ratio_max': 2.6259412744}, call={'rows': 6, 'rmse_ratio_median': 12.1981002298, 'rmse_ratio_min': 12.1981002298, 'rmse_ratio_max': 12.1981002298} |

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
| runtime_ratio_median | 4.57535 |
| runtime_ratio_by_category | american=13.2178, barrier=4.57535, vanilla=1.56224 |

### Benchmarks
Status: ok

### Wrds
Status: ok
