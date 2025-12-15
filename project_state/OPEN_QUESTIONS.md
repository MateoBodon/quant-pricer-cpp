# Open Questions

- **Heston QE bias** – Base/ATM scenarios still show several price units of bias vs analytic despite integrated-drift fix. Should we add martingale correction, adaptive stepping, or switch to Alfonsi/Quadratic Exponential with conditional moments for high vol-of-vol?
- **WRDS weighting choices** – Current calibration weights = vega × quotes with soft wing taper (moneyness >1.2). Would alternative liquidity/vega schemes or tenor-dependent tapers improve stability on live IvyDB pulls?
- **Barrier MC near-touch regime** – Crossing probability formula assumes log-Brownian bridge; how tight is bias when spot ≈ barrier and σ→0? Should extra analytical parity checks be added?
- **Sobol dimension cap** – Barrier MC with QMC uses 2 dims/step; num_steps>32 exceeds Sobol table. Is a higher-dim generator or Owen scrambling table needed for finer barrier discretization?
- **American LSMC regression robustness** – Current condition-number guard rejects ill-conditioned bases. Are alternative bases (Laguerre/orthogonal polynomials) or state scaling warranted for deep ITM/OTM regions?
- **Risk backtests** – Kupiec/Christoffersen implemented, but no systematic pass/fail thresholds documented. Should VaR coverage tests be integrated into CI with synthetic series?
- **Config surfacing** – PiecewiseConstant schedules exist for MC/PDE but CLI exposes only simple scalars. Should CLI/python add convenient schedule constructors and tests?
- **Pybind surface coverage** – Barrier PDE Greeks and risk portfolio functions are not exposed to Python; is exposure needed for notebooks/backtests?
