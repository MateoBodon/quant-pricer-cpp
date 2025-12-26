# Metrics Snapshot

Generated at: 2025-12-26T20:16:23.004584+00:00
Artifacts root: docs/artifacts
Manifest git sha: d4be0724a76d2cbd2aaa88e3387ed08694d6e02b
Protocol synthetic_validation: scenario_grid sha256=ac79e61f4ff636a0260771164fa2e641882f7addbe4d974fb9be90e9f8da18cf, tolerances sha256=6222819e4b23355e3b6ff366350455083b0776299e2203991207ffd81202abe1

## Status overview
| Block | Status | Highlights |
| --- | --- | --- |
| tri engine agreement | ok | max|MC-BS|=0.00754518, max|PDE-BS|=0.00058701, MC CI covers BS=True |
| qmc vs prng equal time | ok | median PRNG/QMC RMSE ratio=4.90648 (asian: med=2.27004; call: med=7.54293) |
| pde order | ok | slope=-2.0124, rmse_finest=0.00115728 |
| ql parity | ok | max diff=0.861583 cents, median=0.798752 cents, p95=0.8553 cents |
| benchmarks | ok | MC paths/sec (1t)=1.17968e+07, eff@max=0.120271 |
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
| rmse_ratio_overall_median | 4.90648 |
| payoffs | asian={'rows': 6, 'rmse_ratio_median': 2.2700411007, 'rmse_ratio_min': 2.2700411007, 'rmse_ratio_max': 2.2700411007}, call={'rows': 6, 'rmse_ratio_median': 7.5429281698, 'rmse_ratio_min': 7.5429281698, 'rmse_ratio_max': 7.5429281698} |

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
| rows | 3 |
| max_abs_diff_cents_overall | 0.861583 |
| median_abs_diff_cents_overall | 0.798752 |
| p95_abs_diff_cents_overall | 0.8553 |
| by_category | american={'max_abs_diff_cents': 0.79875157, 'median_abs_diff_cents': 0.79875157, 'p95_abs_diff_cents': 0.79875157, 'rows': 1}, barrier={'max_abs_diff_cents': 0.0410715241, 'median_abs_diff_cents': 0.0410715241, 'p95_abs_diff_cents': 0.0410715241, 'rows': 1}, vanilla={'max_abs_diff_cents': 0.8615834347, 'median_abs_diff_cents': 0.8615834347, 'p95_abs_diff_cents': 0.8615834347, 'rows': 1} |
| runtime_ratio_median | 10.8536 |
| runtime_ratio_by_category | american=14.124, barrier=10.8536, vanilla=1.60645 |

### Benchmarks
Status: ok

### Wrds
Status: ok
