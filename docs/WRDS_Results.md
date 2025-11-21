# WRDS Results

This appendix tracks the deterministic WRDS OptionMetrics bundle that lives under `docs/artifacts/wrds/`. Each refresh runs the same ingest → aggregate → vega-weighted Heston calibration → next-day OOS diagnostics → Δ-hedged P&L pipeline that MARKET tests exercise. All scalar metrics are written to CSV/JSON artifacts so reviewers can diff successive runs.

## Units & Metric Legend

| Shorthand | Definition |
| --- | --- |
| `vol pts` | Absolute implied-vol percentage points (0.01 = 1%). Used for all in-sample vega-weighted RMSE/MAE stats. |
| `bps` | One basis point (1e-4). Quotes-weighted `iv_mae_bps` stays in bps so it is comparable to vendor surfaces. |
| `ticks` | Price increments of 0.05 USD (SPX option tick size). Price RMSE stays in ticks for quick intuition. |
| `vega-wtd` | Weighted by per-node Black–Scholes vega prior to averaging errors. |
| `quotes-wtd` | Weighted by the bucketed quote counts; used for OOS MAE and hedge histograms. |

## Headline Metrics (sample panel)

Sample bundle spans five SPX trade dates (`2020-03-16`, `2020-03-17`, `2022-06-13`, `2022-06-14`, `2024-06-14`) mixed calm/stress. Median values across those dates/tenor buckets:

| Metric (median) | Value | Units | Source |
| --- | --- | --- | --- |
| In-sample vega-wtd IV RMSE | 0.167 | vol pts | [`wrds_agg_pricing.csv`](artifacts/wrds_agg_pricing.csv) |
| In-sample vega-wtd IV MAE | 0.145 | vol pts | [`wrds_agg_pricing.csv`](artifacts/wrds_agg_pricing.csv) |
| In-sample 90th pct IV error | 2384.74 | bps | [`wrds_agg_pricing.csv`](artifacts/wrds_agg_pricing.csv) |
| In-sample price RMSE | 2643.44 | ticks | [`wrds_agg_pricing.csv`](artifacts/wrds_agg_pricing.csv) |
| Next-day IV MAE (quotes-wtd) | 1942.83 | bps | [`wrds_agg_oos.csv`](artifacts/wrds_agg_oos.csv) |
| Next-day price MAE (quotes-wtd) | 2072.23 | ticks | [`wrds_agg_oos.csv`](artifacts/wrds_agg_oos.csv) |
| Δ-hedged mean ticks (30/60/90d) | −12.3 / −12.6 / −12.0 | ticks | [`wrds_agg_pnl.csv`](artifacts/wrds_agg_pnl.csv) |
| Δ-hedged σ ticks (30/60/90d) | 96.1 / 64.2 / 47.0 | ticks | [`wrds_agg_pnl.csv`](artifacts/wrds_agg_pnl.csv) |

## BS baseline (single σ per tenor bucket)

For comparison, a vega-weighted least-squares BS fit per tenor bucket is now emitted as `wrds_agg_pricing_bs.csv` and `wrds_agg_oos_bs.csv`.

| Metric (median) | BS | Units | Heston ref |
| --- | --- | --- | --- |
| In-sample vega-wtd IV RMSE | 0.016 | vol pts | 0.167 |
| In-sample vega-wtd IV MAE | 0.0126 | vol pts | 0.145 |
| In-sample price RMSE | 182.25 | ticks | 2643.44 |
| OOS IV error (quotes-wtd) | 117 | bps | 1943 |

Artifacts: [`wrds_agg_pricing_bs.csv`](artifacts/wrds_agg_pricing_bs.csv), [`wrds_agg_oos_bs.csv`](artifacts/wrds_agg_oos_bs.csv).

These numbers come from the bundled **sample IvyDB snapshot**; live WRDS runs (with `WRDS_ENABLED=1`) will shift depending on the trade-date panel and calibration seed.

## Vega-weighted Calibration Snapshot

| Metric | Definition | Units | Artifact |
| --- | --- | --- | --- |
| `iv_rmse_volpts_vega_wt` | Vega-weighted RMSE between model and market IVs. | `vol pts` | [`docs/artifacts/wrds/wrds_agg_pricing.csv`](artifacts/wrds/wrds_agg_pricing.csv) |
| `iv_mae_volpts_vega_wt` | Vega-weighted MAE in vol space. | `vol pts` | [`docs/artifacts/wrds/wrds_agg_pricing.csv`](artifacts/wrds/wrds_agg_pricing.csv) |
| `iv_p90_bps` | Vega-weighted 90th percentile absolute IV error. | `bps` | [`docs/artifacts/wrds/wrds_agg_pricing.csv`](artifacts/wrds/wrds_agg_pricing.csv) |
| `price_rmse_ticks` | RMSE of price errors, quoted in ticks. | `ticks` | [`docs/artifacts/wrds/wrds_agg_pricing.csv`](artifacts/wrds/wrds_agg_pricing.csv) |

## Out-of-sample & Hedge Diagnostics

| Metric | Definition | Units | Artifact |
| --- | --- | --- | --- |
| `iv_mae_bps` | Quotes-weighted MAE of next-day IV errors. | `bps` | [`docs/artifacts/wrds/wrds_agg_oos.csv`](artifacts/wrds/wrds_agg_oos.csv) |
| `price_mae_ticks` | Quotes-weighted MAE of next-day price errors. | `ticks` | [`docs/artifacts/wrds/wrds_agg_oos.csv`](artifacts/wrds/wrds_agg_oos.csv) |
| `mean_ticks` | Quotes-weighted mean Δ-hedged P&L per tenor bucket. | `ticks` | [`docs/artifacts/wrds/wrds_agg_pnl.csv`](artifacts/wrds/wrds_agg_pnl.csv) |
| `pnl_sigma` | Standard deviation of Δ-hedged ticks per bucket. | `ticks` | [`docs/artifacts/wrds/wrds_agg_pnl.csv`](artifacts/wrds/wrds_agg_pnl.csv) |

## Multi-date Dashboard (≥5 trade dates)

The batch runner iterates every entry in [`wrds_pipeline_dates_panel.yaml`](../wrds_pipeline_dates_panel.yaml)—mixing calm and stress labels—and writes one row per trade date under:

- [`docs/artifacts/wrds/wrds_agg_pricing.csv`](artifacts/wrds/wrds_agg_pricing.csv): vega-weighted fit metrics, labels, and provenance.
- [`docs/artifacts/wrds/wrds_agg_oos.csv`](artifacts/wrds/wrds_agg_oos.csv): tenor-by-date OOS IV/price MAE with quote counts.
- [`docs/artifacts/wrds/wrds_agg_pnl.csv`](artifacts/wrds/wrds_agg_pnl.csv): Δ-hedged P&L stats per tenor bucket.
- [`docs/artifacts/wrds/wrds_multi_date_summary.png`](artifacts/wrds/wrds_multi_date_summary.png): overview figure (vega-wtd IV RMSE bars, OOS MAE heatmap, hedge mean ±σ ticks).

![WRDS multi-date summary](artifacts/wrds/wrds_multi_date_summary.png)

Run `python -m wrds_pipeline.pipeline --dateset wrds_pipeline_dates_panel.yaml --use-sample` for the deterministic bundle, or drop `--use-sample` (with `WRDS_ENABLED=1`) to pull live IvyDB data.

## Reproducing this bundle

1. `./scripts/reproduce_all.sh` – builds Release, runs FAST+SLOW tests, and refreshes every artifact (WRDS sample bundle runs without credentials).
2. `python wrds_pipeline/pipeline.py --symbol SPX --trade-date YYYY-MM-DD` – direct control for ad-hoc WRDS dates. Set `WRDS_ENABLED=1` with `WRDS_USERNAME`/`WRDS_PASSWORD` to hit live IvyDB; otherwise the committed sample runs.

Each run appends to [`docs/artifacts/manifest.json`](artifacts/manifest.json) with the git SHA, compiler, seed pack, CPU info, and the command used to regenerate the WRDS bundle.
