# Metrics Snapshot

Generated at: 2025-12-18T06:16:47.523501+00:00
Artifacts root: /Users/mateobodon/Documents/Programming/Projects/quant-pricer-cpp/docs/artifacts
Manifest git sha: 45bbd3c7fbd40b878cc85dfae88a4738eab8ca33

## Status overview
| Block | Status | Highlights |
| --- | --- | --- |
| tri engine agreement | ok | max|MC-BS|=0.00959304, max|PDE-BS|=0.00014696, MC CI covers BS=True |
| qmc vs prng equal time | ok | median PRNG/QMC RMSE ratio=10.8467 (asian: med=3.54743; call: med=18.146) |
| pde order | ok | slope=-2.01195, rmse_finest=0.000127279 |
| ql parity | ok | max diff=0.861583 cents |
| benchmarks | ok | MC paths/sec (1t)=1.38427e+07, eff@max=0.121756 |
| wrds | ok | median iv_rmse=0.0160071 (sample bundle) |

### Tri Engine Agreement
Status: ok

| Metric | Value |
| --- | --- |
| rows | 7 |
| max_abs_error_mc | 0.00959304 |
| max_abs_error_pde | 0.00014696 |
| mc_ci_coverage_fraction | 1 |
| mc_ci_covers_bs | True |

### Qmc Vs Prng Equal Time
Status: ok

| Metric | Value |
| --- | --- |
| rmse_ratio_overall_median | 10.8467 |
| payoffs | asian={'rows': 6, 'rmse_ratio_median': 3.5474333381, 'rmse_ratio_min': 3.5474333381, 'rmse_ratio_max': 3.5474333381}, call={'rows': 6, 'rmse_ratio_median': 18.1459914802, 'rmse_ratio_min': 18.1459914802, 'rmse_ratio_max': 18.1459914802} |

### Pde Order
Status: ok

| Metric | Value |
| --- | --- |
| rows | 5 |
| slope | -2.01195 |
| r2 | 0.999999 |
| rmse_finest | 0.000127279 |
| nodes_finest | 1201 |
| timesteps_finest | 1200 |

### Ql Parity
Status: ok

| Metric | Value |
| --- | --- |
| max_abs_diff_cents_overall | 0.861583 |
| by_category | american={'max_abs_diff_cents': 0.79875157, 'rows': 1}, barrier={'max_abs_diff_cents': 0.0410715241, 'rows': 1}, vanilla={'max_abs_diff_cents': 0.8615834347, 'rows': 2} |
| runtime_ratio_median | 45.3031 |
| runtime_ratio_by_category | american=60.4785, barrier=30.1277, vanilla=47.935 |

### Benchmarks
Status: ok

### Wrds
Status: ok
