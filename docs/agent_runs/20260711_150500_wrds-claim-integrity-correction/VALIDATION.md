# Validation

- Python compile check: passed.
- Analytic Heston-delta bump-halving stability regression: passed.
- Sample one-command local metrics test: passed.
- Export schema/data-policy negative guard: passed.
- Metrics snapshot/current-results consistency: passed.
- Data-policy guard: passed.
- Documentation sanity: passed.
- CMake build: passed.
- FAST CTest: 68/68 passed; one separately enumerated RNG test skipped by its
  existing platform condition.
- Real five-date replay: pending implementation commit.
- First real replay from `0dbcd666`: fail-closed at 2024-06-14 on an analytic
  Heston delta of `1.1369`; follow-up audit found 37/233 invalid surface rows.
- Numerical gate regression: stable interior derivative accepted; a synthetic
  no-arbitrage-violating derivative rejected without clipping; partial-validity
  aggregate remains invalid.
- Stable v3 real replay: completed 5/5 dates from `2ccbf543`; claim gate
  `diagnostic_only`; 5/5 converged, 3/5 boundary-saturated, 37/1,212 invalid
  Heston surface derivatives retained and gated.
- Stable v3 metrics receipt SHA-256:
  `83bc58fc44f44e5214787603053bce98d9ce1a7379a113c3469459b2a7585750`.
