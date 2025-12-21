# Results

- Implemented WRDS parquet caching with optional cache root (`WRDS_CACHE_ROOT`) and automatic reuse in `wrds_pipeline/ingest_sppx_surface.py`.
- Added cache builder utility `scripts/build_wrds_cache.py` to bulk-download WRDS OptionMetrics slices and organize them under `/Volumes/Storage/Data/wrds_cache`.
- Populated a large SPX cache from 2010-01-04 through 2025-08-29 (latest available); missing dates are largely market holidays and post-2025-08-29 dates with no WRDS data yet.

## Cache location
- Root: `/Volumes/Storage/Data/wrds_cache/`
- Parquet layout: `/Volumes/Storage/Data/wrds_cache/optionm/SPX/<YYYY>/spx_<YYYY-MM-DD>.parquet`
- Index: `/Volumes/Storage/Data/wrds_cache/cache_index.jsonl`
- Manifest: `/Volumes/Storage/Data/wrds_cache/cache_manifest.json`

## Cache summary (from manifest)
- Cached dates: 3,939
- Rows total: 16,256,312
- Size on disk: ~146.6 MB
- Date span: 2010-01-04 → 2025-08-29
- Missing dates: 227 (primarily US market holidays + dates after 2025-08-29 with no data yet)

## Notes
- Cached data mirrors the pipeline’s WRDS query (calls only, limit 6000 rows/day, best_bid/best_offer filters). This is intentional to match current evaluation behavior.
- No raw WRDS tables were written into the repo; cache lives outside the repo per policy.

## Sources consulted
- None (WRDS direct access).
