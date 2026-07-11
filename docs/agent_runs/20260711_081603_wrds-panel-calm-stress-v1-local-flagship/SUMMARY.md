# WRDS Panel Calm-Stress V1 Local Flagship Run

- Run timestamp (UTC): `2026-07-11T08:16:03Z`
- Run id: `wrds_local_20260711T113500Z_flagship_audit`
- Git SHA: `9fe8da46237a6a9a973791804512f648adc3db03`
- Evidence commit SHA: `50fdfdca2b655503d9aa1059d46f772c83dd6bfe`
- Local milestone branch: `portfolio-os/wrds-local-flagship-20260711`
- Dateset: `wrds_pipeline_dates_panel.yaml`
- Dateset SHA256: `3c592a51ec12d37211ef0f0f4550609732662f6b707b63681b3e090c1cda85c5`
- Panel id: `wrds_panel_calm_stress_v1`
- Local root: `/Volumes/Storage/Data/wrds`
- Snapshot: `20260707_045553_global_project_priority`
- Output root: `artifacts/_local/wrds_local/wrds_local_20260711T113500Z_flagship_audit/`

## Scope Verification

The delegated frozen-scope description was verified against the live partitioned
vault:

- 5 trade-date pairs
- 8 unique surface dates
- 40 partition references
- 14 unique compressed input files
- 449,572,051 total compressed input bytes

Verified unique inputs:

- `raw/optionm/opprcd2020/.../day=2020-03-16/data.csv.gz`
- `raw/optionm/opprcd2020/.../day=2020-03-17/data.csv.gz`
- `raw/optionm/opprcd2020/.../day=2020-03-18/data.csv.gz`
- `raw/optionm/opprcd2022/.../day=2022-06-13/data.csv.gz`
- `raw/optionm/opprcd2022/.../day=2022-06-14/data.csv.gz`
- `raw/optionm/opprcd2022/.../day=2022-06-15/data.csv.gz`
- `raw/optionm/opprcd2024/.../day=2024-06-14/data.csv.gz`
- `raw/optionm/opprcd2024/.../day=2024-06-17/data.csv.gz`
- `raw/optionm/secprd2020/.../month=2020-03/data.csv.gz`
- `raw/optionm/secprd2022/.../month=2022-06/data.csv.gz`
- `raw/optionm/secprd2024/.../month=2024-06/data.csv.gz`
- `raw/optionm/secnmd/.../data.csv.gz`
- `raw/optionm/zerocd/.../data.csv.gz`
- `raw/optionm/idxdvd/.../data.csv.gz`

Each used file bound to exactly one acquisition-manifest item with
`item_status=ok`. The three static-table bindings (`secnmd`, `zerocd`,
`idxdvd`) resolve through the accepted predeclared manifest with overall status
`operator_paused_at_boundary`.

An external summary referenced aggregate input fingerprint prefix
`bc54c8fc...`. The repo does not define that hash recipe. Local reconstruction
confirmed the same file cardinality, partition counts, byte total, and
per-manifest bindings, but no documented in-repo serialization reproduced that
exact prefix. Treat the upstream prefix as externally asserted unless its hash
recipe is supplied.

## Execution Outcome

Command completed successfully:

```bash
WRDS_LOCAL_ROOT=/Volumes/Storage/Data/wrds QUANT_MACHINE_LABEL=codex-local \
./scripts/reproduce_wrds_local_metrics.sh \
  --dateset wrds_pipeline_dates_panel.yaml \
  --run-id wrds_local_20260711T113500Z_flagship_audit
```

Pipeline log reported all five entries as `source_today=local` and
`source_next=local`, then wrote:

- `metrics_export_local.json`
- `metrics_export_local.md`
- aggregate CSVs for pricing, OOS, PnL, and BS/Heston comparison
- per-date `source_receipt.json` files under `per_date/<trade_date>/`

## Aggregate Metrics

Heston pricing/OOS aggregate export, with the hedge rows relabeled below:

- Pricing median IV RMSE (vega-wtd): `0.0721060` vol pts
- Pricing median IV MAE (vega-wtd): `0.0207862` vol pts
- Pricing median price RMSE: `257.802` ticks
- OOS weighted IV MAE: `370.669` bps
- OOS weighted price MAE: `376.343` ticks
- Market-IV Black-Scholes-delta hedge PnL mean: `-13.4599`
- Market-IV Black-Scholes-delta hedge PnL mean ticks: `-269.198`
- Market-IV Black-Scholes-delta hedge PnL median sigma: `289.319`

BS vs Heston tenor medians from `wrds_bs_heston_comparison.csv`:

- 1y and 6m favor Heston on IV RMSE and OOS IV MAE.
- 30d, 60d, and 90d favor BS on in-sample IV RMSE.
- Heston improves OOS IV MAE at 1y, 6m, and 90d, but is worse at 30d and 60d.
- The PnL sigma is not Heston-specific. It uses a Black-Scholes delta computed
  from observed market IV and remains large, especially in stress.

## Independent Correction

Independent review accepted the exact 14-file provenance and frozen execution,
but rejected the original risk/performance attribution:

- `delta_hedge_pnl.py` computed a Black-Scholes delta from market IV; downstream
  comparison code mislabeled that diagnostic as Heston PnL sigma;
- 10 of the 25 fitted Heston parameters hit exact calibration bounds, including
  all five parameters on 2020-03-16;
- therefore the run proves real-vault execution and provenance, while the
  pricing/OOS results and hedge diagnostic remain diagnostic-only and cannot
  support Heston risk or superiority promotion.

The corrective implementation renames the hedge fields, persists convergence
and active-bound diagnostics, and adds a fail-closed claim gate. Numerical
pricing, OOS, and hedge values are to remain unchanged under exact replay; only
their attribution and promotion eligibility change.

## Promotion Gate Decision

This run is real, local, and provenance-clean, but it is not auto-promoted to
public headline evidence:

- the result is mixed rather than a clean Heston-superiority story;
- existing public docs intentionally forbid upgrading Heston into a superiority
  headline without locked-protocol review;
- independent review rejected risk/superiority promotion because of the hedge
  attribution error and boundary-saturated fits;
- local outputs remain under ignored scratch paths.

Decision: preserve the run as reviewable evidence and update repo claim/state
docs, but do not promote local aggregate artifacts into `docs/artifacts/` or
public-facing headline copy.

## Remote Publication Status

The local evidence was committed and anchored to local branch
`portfolio-os/wrds-local-flagship-20260711`, but remote reconciliation and push
could not be executed from this environment.

Blocked commands:

```text
git fetch --dry-run origin
git push --dry-run origin recovery/quant-pre-v3-20260710
```

Exact blocker:

```text
Rejected("approval required by policy, but AskForApproval is set to Never")
```

Implication: the milestone is locally reviewable and branch-addressable, but
not remotely published from this run.

## License-Safety Notes

- No raw WRDS/OptionMetrics rows were copied into tracked files.
- Only aggregate scalar metrics, file metadata, and receipt/provenance summaries
  are recorded here.
- Restricted detailed outputs remain under ignored `artifacts/_local/`.
