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
| Next-day IV MAE (quotes-wtd) | 2143.33 | bps | [`wrds_agg_oos.csv`](artifacts/wrds_agg_oos.csv) |
| Next-day price MAE (quotes-wtd) | 2592.79 | ticks | [`wrds_agg_oos.csv`](artifacts/wrds_agg_oos.csv) |
| Δ-hedged mean ticks (30/60/90d) | −79.6 / −72.3 / −67.2 | ticks | [`wrds_agg_pnl.csv`](artifacts/wrds_agg_pnl.csv) |
| Δ-hedged σ ticks (30/60/90d) | 91.8 / 62.7 / 46.1 | ticks | [`wrds_agg_pnl.csv`](artifacts/wrds_agg_pnl.csv) |

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

## BS vs Heston comparison (sample panel)

`wrds_bs_heston_comparison.csv` summarizes per-tenor deltas between the single-σ BS baseline and the vega-weighted Heston calibration using only the committed sample data.

**In-sample fit (vega-weighted)**

| Tenor | BS IV RMSE (vol pts) | Heston IV RMSE (vol pts) | Δ (H−BS) | BS price RMSE (ticks) | Heston price RMSE (ticks) | Δ (ticks) |
| --- | --- | --- | --- | --- | --- | --- |
| 30d | 0.036 | 0.214 | +0.178 | 181.1 | 3351.5 | +3170.4 |
| 60d | 0.017 | 0.200 | +0.183 | 177.1 | 4035.2 | +3858.1 |
| 90d | 0.015 | 0.155 | +0.139 | 221.2 | 3610.4 | +3389.3 |

**OOS + Δ-hedged**

| Tenor | BS OOS IV MAE (bps) | Heston OOS IV MAE (bps) | Δ (H−BS) (bps) | BS OOS price MAE (ticks) | Heston OOS price MAE (ticks) | Δ (ticks) | Δ‑hedged σ (Heston, ticks) |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 30d | 248.6 | 3557.5 | +3308.9 | 145.5 | 2619.1 | +2474.6 | 96.1 |
| 60d | 129.5 | 2058.9 | +1929.3 | 142.8 | 3114.5 | +2971.7 | 64.2 |
| 90d | 131.4 | 1505.2 | +1373.9 | 194.6 | 2896.7 | +2702.2 | 47.0 |

**Narrative (sample data only):**
- On the bundled sample panel, the single-σ BS fit dominates Heston on both in-sample IV RMSE (+0.14–0.18 vol pts worse for Heston) and next-day IV MAE (+1.3–3.3k bps). Price errors show the same pattern.
- Δ‑hedged 1d σ remains in the 47–96 tick band, but the lack of IV fit improvement suggests the Heston calibration needs retuning before it can outperform BS on live IvyDB pulls. Use this as a regression guard; do not extrapolate these sample deltas to live data.

Artifacts: [`wrds_bs_heston_comparison.csv`](artifacts/wrds_bs_heston_comparison.csv), [`wrds_bs_heston_ivrmse.png`](artifacts/wrds_bs_heston_ivrmse.png), [`wrds_bs_heston_oos_heatmap.png`](artifacts/wrds_bs_heston_oos_heatmap.png), [`wrds_bs_heston_pnl_sigma.png`](artifacts/wrds_bs_heston_pnl_sigma.png).

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
