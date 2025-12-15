# Roadmap

## Short Term (next release)
- Harden Heston QE: investigate martingale correction/alternative discretisation to remove remaining ATM bias; add regression tests against analytic CF.
- Increase coverage in barrier, risk, and CLI error paths; add unit tests for RR barrier edge cases, Brownian-bridge crossing, VaR backtests.
- Surface WRDS pipeline expectations in docs: clarify weighting choices, ensure live runs never persist raw IvyDB; keep sample panel deterministic.
- Improve CLI/pybind usability: expose piecewise schedules and barrier PDE Greeks in Python; tighten flag validation.

## Medium Term
- WRDS analytics: broaden dateset beyond current panel, add liquidity-aware weights, and quantify BS vs Heston deltas (IV RMSE, OOS IV MAE, Δ-hedged σ) with confidence intervals; update WRDS_Results narrative with concrete improvements.
- Benchmark refresh: extend OpenMP scaling plots to higher core counts; add GPU/no-SIMD comparison if available.
- Robust American/Barrier coverage: alternative regression bases for LSMC, optional stochastic mesh; higher-dim Sobol table or fallback for barrier QMC.
- CI artifacts: automate `scripts/reproduce_all.sh` in nightly job with sample data; publish deltas in manifest diff.

## Long Term
- Model extensions: SABR slice calibration (script exists), stochastic rates, local vol, variance-gamma / Bates hybrids.
- Data integrations: plug additional datasets (e.g., CBOE, SPY surface history) via schema adapters while keeping deterministic bundles small.
- Performance: vectorized RNG kernels, SIMD-friendly path loops, optional GPU backend; explore quasi-random generators beyond Sobol.
- Developer experience: richer docs/diagrams for agents, auto-generated API reference refresh, interactive notebooks leveraging pybind bindings.

### Suggested Order
1. Fix QE bias and add tests → stabilizes stochastic-vol outputs used in WRDS analysis.  
2. Strengthen barrier/risk/CLI tests → raises branch coverage and regression safety.  
3. Expand WRDS comparisons with live data → gives headline metrics for communications.  
4. Add schedule/Greek bindings + improved pipeline docs → better user ergonomics.  
5. Pursue performance/model extensions once correctness baseline is solid.
