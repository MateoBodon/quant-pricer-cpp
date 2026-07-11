# Validation

- Python compilation: pass for repaired pricing, delta, independent reference,
  and both audit scripts.
- Independent QuantLib 27-case price/delta grid: pass.
- Full real five-date aggregate reference audit: pass, 1,239/1,239 deltas valid.
- Deterministic three-start calibration audit on both previously pathological
  dates: pass; one eligible fit and one correctly gated boundary fit.
- End-to-end sample local-metrics FAST test: pass. The higher-accuracy sample
  fits reached their 120-evaluation FAST cap and therefore remained
  diagnostic-only; 50/50 sampled Heston deltas were valid.
- Data-policy boundary: only aggregate scalar receipts and documentation are
  tracked; detailed real surfaces and receipts remain under ignored local paths.
