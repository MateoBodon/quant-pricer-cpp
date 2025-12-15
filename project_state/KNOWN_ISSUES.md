# Known Issues & Limitations

- **Heston QE residual bias** – QE MC still over-prices the analytic CF in base/ATM scenarios (see `heston_qe_vs_analytic` results). Treat QE outputs as diagnostic; analytic CF is source of truth for European calls.
- **Sobol dimension limit** – QMC tables cap at 64 dims; barrier MC consumes 2 dims/step (normal + uniform), so `num_steps > 32` is unsupported with Sobol and will throw.
- **Branch coverage gaps** – Barrier edge cases, risk backtest paths, and CLI error handling have lower branch coverage; regressions may slip without targeted tests.
- **WRDS sample bundle** – Bundled data under `wrds_pipeline/sample_data` and `docs/artifacts/wrds` is synthetic/deterministic; live IvyDB pulls (opt-in via env) are needed for production conclusions.
- **Degenerate parameter guards** – Several solvers clamp/clip (e.g., implied vol upper bound 5.0, IV clipping 0.05–3.0 in WRDS ingest, PSOR omega must be (0,2)). Extreme inputs outside these ranges may throw or silently clamp.
- **CLI backward compatibility** – Legacy positional parsing remains; misuse of optional flags (e.g., mismatched qmc/bridge/steps ordering) can lead to confusing errors. JSON output is preferred for automation.
