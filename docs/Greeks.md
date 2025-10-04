# Greeks Implementation Notes

## Black–Scholes
Closed-form Greeks are implemented in `quant::bs` and used both for validation and as control variates:
- Delta/Theta parity validated to machine precision.
- Finite-difference spot/vol bumps (tests) guard against regression drifts.

## Monte Carlo Greeks
- **Delta & Vega**: Pathwise estimators using discounted terminal sensitivities. Antithetic variates reduce variance without biasing derivatives.
- **Gamma (LRM)**: Likelihood-ratio estimator is retained for completeness; its variance scales with the payoff indicator and is highest near at-the-money strikes.
- **Gamma (Mixed)**: Combines pathwise delta with the LR score, minus the analytic correction `Δ/S`. Variance is typically 4× lower than pure LRM (see README table). Both estimators share Welford stats (mean/SE/CI).

## PDE Greeks
- Δ/Γ computed via three-point central differences on the final slice. Truncation errors are \(\mathcal{O}(\Delta S^2)\) and documented in the README.
- Optional Θ uses a backward difference (\(\mathcal{O}(\Delta t)\)); useful for validating MC Θ estimators.

## American Greeks
- PSOR/LSMC are currently focused on price parity; first-derivative Greeks are obtained via bump-and-reprice in validation scripts when needed.

## Reporting
- CLI `--json` mode surfaces price statistics and (for MC) the accompanying SE/CI values, enabling external tools to reason about Greek uncertainty.
- Demo one-pager summarises MC vs BS Greek agreements and compares Γ estimator variance to aid method selection.
