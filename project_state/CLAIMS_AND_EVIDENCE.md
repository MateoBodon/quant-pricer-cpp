# Claims And Evidence

This file is the current claim/evidence boundary for public, portfolio, release, and future agent work. Archived pre-v2 docs and local scratch artifacts are historical context, not current truth.

## Claim Status Legend

| Status | Meaning |
|---|---|
| `supported_current_head` | Verified in this workspace on current HEAD or current dirty working tree with logged commands. |
| `supported_historical_snapshot` | Supported by committed artifacts, but not by a successful current-HEAD reproduction in this ticket. |
| `sample_only` | Supported only as deterministic sample/regression evidence, not live-market proof. |
| `live_gated` | Requires explicit WRDS/live/local data evidence before public use. |
| `stale` | Wording or evidence reference predates the current artifact set or strategy. |
| `unsupported` | No adequate evidence found in the audited current surfaces. |
| `missing_artifact` | Public docs or manifest reference an artifact absent from the tracked curated set. |
| `needs_protocol_review` | Evidence may exist, but promotion requires Heavy/Pro review of protocol, units, or methodology. |
| `not_checked` | In scope for a later ticket, not verified here. |

## T-001/T-101 Reproduction Status

On 2026-07-03, current-HEAD sample reproduction was attempted with:

```bash
REPRO_FAST=1 WRDS_USE_SAMPLE=1 ./scripts/reproduce_all.sh
```

Result: `failed`.

Evidence: `reports/_runs/20260703_220951_T-001_T-101_evidence_claim_audit/logs/010_reproduce_all_sample.log`.

Failure: FAST test `metrics_snapshot_fast` failed because partial reproduction regenerated `docs/artifacts/metrics_summary.*` with `generated_at=2026-07-03T22:11:49.716641+00:00`, while `project_state/CURRENT_RESULTS.md` still pointed at the older 2026-01-25 snapshot. The partial artifact diff was captured and the curated artifact tree was restored from the before-snapshot; no regenerated artifacts were promoted.

Implication: the 2026-01-25 metrics snapshot remains the committed public evidence baseline unless Heavy intentionally runs a repair/promotion ticket that updates artifacts, manifest, validation pack, and current-results state consistently.

## 2026-07-11 Local WRDS Flagship Run Status

On 2026-07-11, a real local-vault execution of `wrds_panel_calm_stress_v1`
completed successfully on current HEAD with:

```bash
WRDS_LOCAL_ROOT=/Volumes/Storage/Data/wrds QUANT_MACHINE_LABEL=codex-local \
./scripts/reproduce_wrds_local_metrics.sh \
  --dateset wrds_pipeline_dates_panel.yaml \
  --run-id wrds_local_20260711T113500Z_flagship_audit
```

Evidence:

- local scratch outputs:
  `artifacts/_local/wrds_local/wrds_local_20260711T113500Z_flagship_audit/`
- tracked run log:
  `docs/agent_runs/20260711_081603_wrds-panel-calm-stress-v1-local-flagship/`

What is now supported:

- current HEAD can execute the locked local-vault panel in real-data mode
  against snapshot `20260707_045553_global_project_priority`;
- every trade-date pair produced manifest-bound per-date source receipts;
- the delegated frozen scope counts were matched locally:
  5 trade-date pairs, 8 unique surface dates, 40 partition references,
  14 unique compressed inputs, and 449,572,051 compressed bytes.

What is still not promoted:

- these local real-data results are not yet public headline truth;
- they remain `live_gated` / `needs_protocol_review` for promotion because the
  result is mixed and local-only, the hedge diagnostic was originally
  misattributed as Heston-specific, and 10 of 25 fitted parameters hit exact
  calibration bounds;
- no local aggregate artifacts were promoted into `docs/artifacts/`.

## Current Claim Classes

| Claim | Current evidence | Status | Caveat / next evidence |
|---|---|---|---|
| C++20 option-pricing library with analytic, MC/QMC, PDE, Heston, exotics, risk, and multi-asset components | `include/quant/`, `src/`, `tests/`; current CMake build and FAST passed in this sprint | `supported_current_head` | Feature breadth is source/test supported; package install remains separate. |
| FAST validation baseline | `ctest --test-dir build -L FAST --output-on-failure` passed 64/64 with one skipped RNG thread-invariance test | `supported_current_head` | Re-run after source, artifact, or state changes. |
| Data-policy guard | `python3 scripts/check_data_policy.py` passed before and after failed reproduction capture | `supported_current_head` | Guard covers tracked data/artifacts; ignored local/generated files are not public evidence. |
| Tri-engine agreement across analytic, MC, PDE | `docs/artifacts/tri_engine_agreement.*`, `docs/artifacts/metrics_summary.md` | `supported_historical_snapshot` | Metrics snapshot generated 2026-01-25; current-HEAD reproduction did not complete. |
| QMC vs PRNG equal-time improvement | `docs/artifacts/qmc_vs_prng_equal_time.*`, `metrics_summary.md` | `supported_historical_snapshot` | Current public wording should use the artifact metric definition: PRNG/QMC RMSE ratio, not vague universal superiority. |
| PDE second-order behavior | `docs/artifacts/pde_order_slope.*`, `metrics_summary.md` | `supported_historical_snapshot` | Smooth-regime/grid-specific. |
| QuantLib parity within about one cent | `docs/artifacts/ql_parity/*`, `metrics_summary.md` | `supported_historical_snapshot` | Must preserve product/grid/bucket context. |
| Benchmarks and MC paths/sec | `docs/artifacts/bench/*`, `metrics_summary.md`, manifest hardware fields | `supported_historical_snapshot` | Hardware/compiler/protocol specific; do not present as general performance. |
| WRDS sample pipeline and as-of guards | FAST as-of/poison tests, `wrds_pipeline/`, tracked sample aggregate artifacts | `sample_only` | Sample bundle supports regression/reproducibility, not live-market performance. |
| Live/local WRDS execution on current HEAD | `docs/agent_runs/20260711_081603_wrds-panel-calm-stress-v1-local-flagship/`, local receipts and aggregate exports under `artifacts/_local/wrds_local/wrds_local_20260711T113500Z_flagship_audit/` | `supported_current_head` | Supported as local execution evidence only; no public promotion yet. |
| Live/local WRDS performance or superiority | 2026-07-11 local run exists; independent review accepted provenance but rejected promotion because fits are boundary-saturated and the original hedge diagnostic was misattributed | `live_gated` | Requires an exact corrected replay, an eligible calibration panel, genuine model-specific hedging, and sanitized reviewed aggregates before public use. |
| Heston superiority over BS | 2026-07-11 local comparison is mixed by tenor; 10/25 fit parameters hit exact bounds and the reported hedge PnL was actually market-IV Black-Scholes-delta PnL | `unsupported` | Do not headline Heston superiority or risk performance unless a locked protocol passes calibration and model-specific hedge gates. |
| Heston QE Monte Carlo production accuracy | `docs/artifacts/heston_qe_vs_analytic.*`; known bias remains | `needs_protocol_review` | Treat QE as experimental/caveated; WRDS pipeline uses analytic Heston, not QE. |
| Curated artifact reproducibility | `scripts/reproduce_all.sh` exists and partial reproduction regenerated artifacts | `stale` | Official current-HEAD reproduction failed in this sprint; repair before promotion. |
| Validation pack release asset availability | README/release references, `scripts/package_validation.py` | `not_checked` | Local pack generation was not rerun after failed reproduction; release asset claims need T-106/T-105 verification. |
| `pip install pyquant-pricer` public install | `pyproject.toml`, README | `not_checked` | Package availability/installability was not verified in this sprint; T-106 should smoke-test. |
| Manifest references to WRDS per-date/detail files | `docs/artifacts/manifest.json`; generated ignored files during failed reproduction | `missing_artifact` | Ignored detail files are not tracked curated evidence; public docs should cite tracked aggregate/comparison files only. |
| `wrds_agg_pricing_bs.csv` / `wrds_agg_oos_bs.csv` as public artifacts | Generated during reproduction but ignored and not tracked in curated artifacts | `missing_artifact` | Do not cite as current public evidence unless tracking policy deliberately promotes safe aggregates. |

## Evidence Roots

- Curated tracked artifacts: `docs/artifacts/`
- Metrics snapshot: `docs/artifacts/metrics_summary.md` and `docs/artifacts/metrics_summary.json`
- Manifest: `docs/artifacts/manifest.json`
- Claim audit reports: `reports/_runs/20260703_220951_T-001_T-101_evidence_claim_audit/`
- Tests: `tests/` and CTest labels
- Historical run logs: `docs/agent_runs/`
- Local/scratch outputs: `artifacts/_local/` and ignored/generated WRDS detail files; not public truth
- Current real-data local run log:
  `docs/agent_runs/20260711_081603_wrds-panel-calm-stress-v1-local-flagship/`

## Public Claim Rules

- Do not strengthen a public claim unless the supporting artifact/command exists and is cited.
- Mark sample WRDS results as sample/regression evidence, not live market evidence.
- Mark local/live WRDS outputs as scratch unless intentionally promoted with sanitized aggregate artifacts and review.
- Do not cite ignored WRDS detail files as curated public artifacts.
- Do not claim Heston superiority over BS without locked-protocol evidence and L4 review.
- Do not claim package availability or release validation-pack assets until install/release evidence is verified.
- Update this file when public-facing claims, metrics, artifacts, validation protocols, or package/release claims change.
