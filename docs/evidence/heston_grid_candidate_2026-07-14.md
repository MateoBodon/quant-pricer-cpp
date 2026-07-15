# Heston call-metrics grid — verification note

Status: accepted candidate integrated into public v0.3.3; not a claim of
calibration quality or market performance

Verified: 2026-07-14

## Interface contract

`heston_call_metrics_grid` accepts:

- market matrix `(m,5)`;
- Heston parameter matrix `(p,5)`;
- a bounded worker count.

It returns one contiguous candidate-major `(p,m,2)` array containing analytic
call price and implied volatility. The binding validates every input row and
rejects Cartesian item-count overflow before allocating the output.

## Verified evidence

- Implementation commit: `bfc9f7cc2d25be751524f5aec70ba8ce9acd1a53`
- Installed wheel SHA-256: `ec198c0ea4c86924f623df58be71aebd6ffcd9d2348355a4be92ea4d3997664d`
- Focused verification: `val_20260714T090752512766Z_d35b4759`
- Verification receipt SHA-256: `e36acf6fa9eabb8f768da4f7705c14a35b40f70285d6187a5e46526234bf2d4d`

The installed-wheel evaluator passed five checks:

1. exact equality with `heston_call_metrics_batch` for every candidate/market cell;
2. focused Ruff validation;
3. Python bytecode compilation of the evaluator;
4. tracked-data policy validation;
5. `clang-format --dry-run --Werror` on the binding.

It also exercised deterministic eight-way caller concurrency under the shared
four-worker process policy.

## What `14.2×` means

For the frozen evaluator case, passing separate `(m,5)` market and `(p,5)`
parameter matrices required **14.2× less input materialization** than explicitly
constructing the full Cartesian candidate/market input.

It does **not** mean:

- 14.2× faster pricing;
- 14.2× faster calibration;
- better numerical accuracy;
- better empirical fit;
- any hedge, PnL, return, live-data, or trading result.

The exact accepted implementation was integrated into v0.3.3 after the recorded
Project OS work finished with no active owner. Release artifacts are validated
separately; this receipt remains the provenance for the 14.2× representation
claim.
