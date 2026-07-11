# SSVI Temporal Holdout v1 — Confirmed

The published one-use contract was executed once on the fixed twelve-pair
2020–2025 Q1/Q3 panel. The result is SSVI-unseen but not dataset-blind: earlier
Heston and tenor-flat Black–Scholes aggregate work existed before SSVI, and the
post-publication input-generation pass necessarily read the raw rows and
reconstructed the aggregate surfaces.

## Primary result

- Status: `confirmed`.
- Rows: 2,808 calibration and 2,806 next-day aggregate surface rows.
- All twelve SSVI fits passed analytic sufficient conditions, dense numerical
  static-arbitrage, finite-row, and independent QuantLib gates.
- Against repaired Heston, SSVI won strict next-day price MAE on 11/12 dates;
  median relative change was `-8.8825159082%`, mean was `-14.9785125494%`, and
  the exact one-sided sign probability was `0.003173828125`.
- Against tenor-flat Black–Scholes, SSVI won 12/12; median relative change was
  `-79.9032508882%`, mean was `-76.8461299987%`, and the exact one-sided sign
  probability was `0.000244140625`.
- Across all six fixed metrics and twelve dates, SSVI won 59/72 comparisons,
  repaired Heston 12/72, and tenor-flat Black–Scholes 1/72.

## Retained adverse evidence

- The only primary loss was 2020-01-06: SSVI next-day price MAE was
  `87.3484286661` ticks versus Heston `81.7428090967`, a `+6.8576302079%`
  relative change. The Heston fit was boundary-saturated and ineligible, but
  the comparison remains a counted SSVI loss.
- Heston narrowly beat SSVI on next-day IV MAE on 2021-01-04 (`87.9572` vs
  `88.9886` bps) and 2024-07-01 (`45.1644` vs `46.0972` bps).
- SSVI's worst absolute next-day price MAE was `617.9373578310` ticks on
  2022-01-03. Its worst next-day IV MAE was `510.7925908176` bps on
  2023-01-03.
- Four Heston comparator fits were boundary-saturated: 2020-01-06,
  2022-01-03, 2022-07-05, and 2024-01-02.
- SSVI reached `3.8416 / 4.0` of the sufficient-curvature limit on the most
  constrained dates. Every analytic and dense numerical gate still passed.
- Hedge behavior was not evaluated. This is not a strategy, return, universal
  superiority, or future-market claim.

## Provenance and resources

- Contract SHA-256: `2b042a32bbaad3f7a83be88721e7b0c4c1d0f50db417a88209c8de1342c276a0`.
- Panel SHA-256: `301aced837431eff2276067d08e12581918d85a498d8e9d0ef33e338a69dc974`.
- Published code commit/tree: `246bf2c8a71053dbe2f78aa3810e77c7872e1f17` /
  `8d77178bc9cf85d0263c8451e866d98f45732e8c`.
- Consumed-marker SHA-256:
  `2cc16980708b66ee5bbad37c779f04514ad8a3c53e39384b98efe1b72e5646f7`.
- Full local result SHA-256:
  `385e67995d6b58235e458d95e8339e6aa93aa7f5cede5311b4f3c286ed45b30b`.
- Input generation: PID 329, 2,934.11 seconds, 534,724,608-byte max RSS,
  zero swaps.
- Sealed evaluation: PID 92768, 1,091.73 seconds, 196,280,320-byte max RSS,
  zero swaps.

The tracked aggregate-only machine-readable result is
[`docs/artifacts/ssvi_temporal_holdout_v1_summary.json`](../../artifacts/ssvi_temporal_holdout_v1_summary.json).
Raw OptionMetrics rows, aggregate quote surfaces, and model parameters remain
outside Git.
