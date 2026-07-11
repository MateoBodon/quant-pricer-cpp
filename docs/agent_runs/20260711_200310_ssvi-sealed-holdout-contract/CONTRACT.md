# Sealed SSVI Temporal Holdout Contract

## Evidence class

The holdout is SSVI-unseen but not dataset-blind. The qanchor selection rule and
earlier Heston/Black-Scholes aggregate work predate the current SSVI model, but
no SSVI calibration or score has been opened on these twelve pairs.

## Exact date rule

Take every qanchor entry from the precommitted 14-pair
`wrds_panel_resume_v2`. Exclude only 2020-03-16/17 and 2020-03-17/18 because
both were already used in SSVI development. The resulting sealed pairs are:

- 2020-01-06/07 and 2020-07-06/07;
- 2021-01-04/05 and 2021-07-06/07;
- 2022-01-03/04 and 2022-07-05/06;
- 2023-01-03/04 and 2023-07-03/05;
- 2024-01-02/03 and 2024-07-01/02;
- 2025-01-02/03 and 2025-07-01/02.

Panel SHA-256:
`301aced837431eff2276067d08e12581918d85a498d8e9d0ef33e338a69dc974`.

Contract SHA-256:
`2b042a32bbaad3f7a83be88721e7b0c4c1d0f50db417a88209c8de1342c276a0`.

## Frozen primary decision

All twelve SSVI fits must pass the published analytic sufficient conditions,
dense numerical static-arbitrage audit, finite-row gate, and independent
QuantLib price check. SSVI must also achieve strict lower next-day price MAE on
at least 10 of 12 dates versus repaired Heston and at least 10 of 12 versus
tenor-flat Black-Scholes, with a negative paired median relative change against
both. Ties do not count as wins.

Ten or more wins in twelve fixed comparisons has one-sided exact sign
probability `0.019287109375` under an equal-win null. Both comparator gates and
every numerical gate must pass. IV and calibration metrics remain mandatory
secondary reporting with no post-outcome threshold.

## One-use execution boundary

The runner validates the exact contract and code hashes, authoritative remote
publication receipt, metadata inventory receipt, post-publication dateset
manifest, exact per-date source receipts, and all sealed source hashes before
opening any aggregate surface. It then atomically creates an exclusive consumed
marker before evaluation; an existing marker or output is a hard failure. Any
later model, date, reducer, threshold, or gate change permanently turns this
holdout into development data.
