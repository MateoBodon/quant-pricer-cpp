# Results

## Implementation checkpoint

- The market-IV Black-Scholes delta diagnostic has explicit field names.
- A genuine calibrated-Heston analytic delta is computed by a stable central
  difference of the same analytic pricer used during calibration.
- Export schema v2 reports both hedge baselines separately.
- Every fit persists convergence, evaluation, optimality, and exact active-bound
  evidence.
- The aggregate claim gate is `diagnostic_only` unless every fit converges and
  no fit is boundary-saturated, every Heston delta is evaluated, and every
  evaluated delta passes bump-stability and European-call bounds.
- Invalid Heston deltas are preserved as candidate/stability/reason diagnostics;
  affected aggregate hedge metrics are null and the estimates are never clipped.

## Sample evidence

The deterministic five-date sample run has 5/5 converged fits, 5/5
boundary-saturated fits, and 0/5 promotion-eligible fits, so the new gate fails
closed as intended. Its median hedge PnL sigma is 239.069 ticks for the
market-IV Black-Scholes delta and 249.249 ticks for the calibrated Heston delta.

## First real replay finding

The exact replay from implementation commit `0dbcd666` stopped at 2024-06-14
because 37 of 233 surface-row Heston derivatives exceeded the call delta bound.
This is a genuine numerical/pricer pathology, concentrated in a converged but
upper-sigma-bound-saturated fit, not an infrastructure failure. The replay is
being repeated with explicit fail-closed row and aggregate diagnostics; no
real-data promotion claim is made.

## Completed real replay

The fail-closed v3 replay completed all five frozen dates from commit
`2ccbf54305a40925e5ed9c8003e3ae803000b41d`. Provenance remains local-vault,
panel-bound, and public-safe. The result is `diagnostic_only`:

- 5/5 fits converged, but only 2/5 were promotion-eligible and 3/5 were
  boundary-saturated;
- 1,212 Heston surface derivatives were evaluated, 1,175 were valid, and the
  same 37 invalid 2024-06-14 derivatives remained explicit;
- invalid derivatives carried quote weight 908 of 24,342 and null the affected
  Heston hedge aggregates;
- median Heston IV RMSE was `0.0654333` versus Black-Scholes `0.0511854`
  (Heston worse by `0.0142479` vol points);
- median Heston next-day IV MAE was `405.319` bps versus Black-Scholes
  `493.704` bps (Heston better by `88.3844` bps);
- median Heston price RMSE was `596.643` ticks versus Black-Scholes `496.469`
  ticks, so the pricing evidence is mixed rather than a superiority result.

The aggregate metrics receipt SHA-256 is
`83bc58fc44f44e5214787603053bce98d9ce1a7379a113c3469459b2a7585750`;
the local manifest SHA-256 is
`5c5d4bd63c7d3be5293d05f38384bb7697b512da1caadb91fbb276bbd6f58d27`.
No restricted input or detailed row is promoted into Git.
