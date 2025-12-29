# Metrics Snapshot

Generated at: 2025-12-29T10:40:40.037202+00:00
Artifacts root: docs/artifacts
Manifest git sha: 2f98798eb30ca76082e277c66a9bbc523cf36f58

## Status overview
| Block | Status | Highlights |
| --- | --- | --- |
| tri engine agreement | ok | max|MC-BS|=0.00754518, max|PDE-BS|=0.00058701, MC CI covers BS=True |
| qmc vs prng equal time | ok | median PRNG/QMC RMSE ratio=4.17311 (asian: med=1.5918; call: med=6.75442) |
| pde order | ok | slope=-2.0124, rmse_finest=0.00115728 |
| ql parity | ok | max diff=0.861583 cents |
| benchmarks | ok | MC paths/sec (1t)=9.77574e+06, eff@max=0.118153 |
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
| rmse_ratio_overall_median | 4.17311 |
| payoffs | asian={'rows': 6, 'rmse_ratio_median': 1.5918021176, 'rmse_ratio_min': 1.5918021176, 'rmse_ratio_max': 1.5918021176}, call={'rows': 6, 'rmse_ratio_median': 6.7544169679, 'rmse_ratio_min': 6.7544169679, 'rmse_ratio_max': 6.7544169679} |

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
| runtime_ratio_median | 9.86534 |
| runtime_ratio_by_category | american=9.86534, barrier=14.0418, vanilla=1.56442 |

### Benchmarks
Status: ok

### Wrds
Status: ok
