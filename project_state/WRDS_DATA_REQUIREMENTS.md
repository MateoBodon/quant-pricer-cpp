# WRDS Data Requirements

Analysis timestamp UTC: 2026-07-07T04:38:18Z

This document maps the WRDS and WRDS-adjacent data needed to reproduce, validate, and extend `quant-pricer-cpp`. It is planning metadata only: no raw WRDS or OptionMetrics data is stored here, and no credentials are referenced.

The current project evidence boundary is important. Current public pricing and performance claims are not live-market claims. The repo has historical artifact snapshots, a synthetic/sample WRDS regression path, and a local/live WRDS pipeline that is gated until reviewed evidence is produced. The current sample reproduction attempt from the T-001/T-101 audit did not complete as a fresh current-HEAD metrics promotion, so current production-grade live WRDS claims still require the P0 data below plus a locked reproduction run.

## Human Summary

### What Is Required Now

The minimum data needed for this project today is narrow but high precision:

- Synthetic/sample WRDS fixtures for current fast reproduction and CI-style regression checks.
- OptionMetrics IvyDB US option quotes for the exact SPX panel dates used by the current WRDS pipeline.
- OptionMetrics underlying/index prices for the next-trading-day OOS pricing checks.
- OptionMetrics security-name metadata to resolve SPX `secid` as of each date.
- Risk-free curves and index dividend/yield inputs so Black-Scholes and Heston runs do not rely on fallback constants.
- Distribution/corporate-action adjustment metadata so prices, strikes, and returns can be interpreted correctly.
- A clean manifest of which local partitions exist, their row counts or hashes, and which claim they support.

The current repo can only treat sample WRDS artifacts as regression evidence. Live/local WRDS evidence needs a reviewed run against real OptionMetrics data, without committing raw quotes or derived restricted rows.

### What Is Foundational For A Serious Version

After the current P0 panel is locked, the core institutional data layer should include:

- Full modern OptionMetrics options and underlying panels, not only SPX.
- CRSP daily stock returns, names, delistings, distributions, and index membership.
- CRSP/OptionMetrics and CRSP/Compustat link tables.
- Compustat fundamentals for valuation, accounting controls, and index constituent checks.
- Fama-French and liquidity factors for baseline benchmarking.
- Independent rates and index return series for sanity checks.

This gives the project enough point-in-time identity control, survivorship-bias control, delisting handling, corporate-action handling, baseline factor attribution, and benchmark comparison scaffolding to support public claims credibly.

### What Improves Publication Quality

The highest-value expansion layer is research robustness:

- IBES estimates, actuals, recommendations, and price targets for event and expectation controls.
- Capital IQ key developments and identifiers for corporate events and cross-vendor linking.
- Short interest and borrow/cost proxies for feasibility and friction-aware diagnostics.
- Holdings and 13F data for institutional demand/liquidity controls.
- CBOE EOD options as an independent options-data benchmark where entitled.
- Index constituent history to avoid survivorship and benchmark-construction errors.

These are not required to rerun the current sample path, but they materially strengthen out-of-sample validation, feature research, and public-safe research narratives.

### What Is Specialized Or Expensive

TAQ, TRACE, SDC, transcripts, global data, ESG/news, and securities-finance datasets are valuable only after the core panel is clean. They are large, entitlement-sensitive, and easy to misuse without a strict point-in-time protocol.

### Local Catalog Grounding

Local WRDS catalog files were found under `/Volumes/Storage/Data/WRDS/_catalog/`, including `20260706_223405_tables.csv`, `20260706_223405_columns.csv`, and `20260706_223405_full_catalog.json`. The schema/table names marked `confirmed_in_catalog` below are grounded in that local catalog snapshot. Date coverage, row counts, entitlements, and local-vault completeness still need verification before a dataset is used as claim evidence.

### Policy Boundary

Raw WRDS/OptionMetrics data must stay in `/Volumes/Storage/Data/WRDS` or another approved restricted vault. The repo may track small synthetic fixtures, manifests, review logs, and public-safe aggregate metrics only. Any table containing `secid`, option bid/ask quotes, identifiable option rows, or raw returns should be treated as restricted unless transformed into an approved aggregate.

## Machine-Readable Requirements

```yaml
project:
  name: "quant-pricer-cpp"
  repo_path: "/Volumes/Storage/Projects/quant-pricer-cpp/repo"
  analysis_timestamp_utc: "2026-07-07T04:38:18Z"
  purpose: "Map all WRDS and WRDS-adjacent data needed to reproduce current sample evidence, validate current live/local claims, and support future option-pricing research expansions without placing raw restricted data in the repo."
  current_claims_or_results_summary: "Current repo evidence separates build/FAST validation, historical metrics snapshots, synthetic/sample WRDS regression evidence, and live/local WRDS claims. Fresh current-HEAD sample reproduction was previously attempted and failed before artifact promotion, so live WRDS numerical claims remain gated until a reviewed run succeeds. Heston is not a public superiority headline. Package/release claims remain unpromoted unless separately tested."
  data_policy_notes:
    raw_wrds_must_not_enter_repo: true
    shared_vault_root: "/Volumes/Storage/Data/WRDS"

requirements:
  - requirement_id: "QPC_P0_SAMPLE_REPRO_WRDS_SYNTHETIC_PANEL"
    priority: "P0_BLOCKING"
    project_need: "Reproduce the repo's intended fast sample mode without WRDS credentials or raw licensed data."
    quant_use_case: "CI-safe regression test for the WRDS pricing pipeline, claim-boundary checks, and command-level reproduction."
    wrds_availability: "not_wrds"
    wrds_schema: "wrds_pipeline"
    wrds_table: "sample_data synthetic CSV fixtures"
    wrds_product_or_library: "repo synthetic sample fixtures"
    logical_dataset: "Synthetic SPX-like option panel, underlying prices, and pipeline config fixtures"
    required_for_current_reproduction: true
    required_for_current_claim_validation: true
    useful_for_future_expansion: false
    date_range:
      minimum_required: "Only the synthetic fixture dates committed to the repo."
      optimal: "Stable deterministic fixtures covering at least calm, stress, holiday-gap, and malformed-row cases."
      tier_split: "table_level"
    frequency: "daily"
    expected_size_class: "tiny"
    partition_strategy: "table"
    key_columns:
      identifiers: ["synthetic underlying id", "option id", "call_put", "strike", "expiry"]
      dates: ["trade_date", "next_trade_date", "expiry_date"]
      measures: ["bid", "ask", "mid", "underlying_close", "implied_volatility", "rate", "dividend_yield"]
    joins:
      required_link_tables: []
      joins_to_project_data: ["wrds_pipeline_dates_panel.yaml", "scripts/reproduce_all.sh", "wrds_pipeline"]
      point_in_time_risks: ["Must stay obviously synthetic and must not be confused with live WRDS evidence."]
    bias_risks:
      survivorship: "None for synthetic regression evidence, but it cannot validate market representativeness."
      lookahead: "Fixture generation must not use target OOS values to tune thresholds or scenario parameters."
      restatement: "None unless fixtures are silently regenerated without manifest updates."
      delisting: "Not represented unless explicit synthetic cases are added."
      corporate_actions: "Not represented unless explicit synthetic cases are added."
    notes: "This is required for current reproduction because the public-safe sample path is the only mode that should run without restricted data. A sample pass is regression evidence only, not live-market proof."

  - requirement_id: "QPC_P0_OPTIONM_SPX_OPTIONS_PANEL"
    priority: "P0_BLOCKING"
    project_need: "Validate live/local WRDS pricing claims for the current SPX calibration and OOS date panel."
    quant_use_case: "Calibrate Black-Scholes and Heston models on same-day SPX option surfaces and evaluate next-day OOS option prices and IV errors."
    wrds_availability: "confirmed_in_catalog"
    wrds_schema: "optionm"
    wrds_table: "opprcdYYYY"
    wrds_product_or_library: "OptionMetrics IvyDB US"
    logical_dataset: "SPX option end-of-day quotes by year"
    required_for_current_reproduction: false
    required_for_current_claim_validation: true
    useful_for_future_expansion: true
    date_range:
      minimum_required: "Current pipeline panel: 2020-03-16, 2020-03-17, 2022-06-13, 2022-06-14, 2024-06-14 and their next trading dates."
      optimal: "2005-present for robust SPX calm/stress/holdout panels, with 2018-present as recent critical."
      tier_split: "recent_critical"
    frequency: "daily"
    expected_size_class: "huge"
    partition_strategy: "year"
    key_columns:
      identifiers: ["secid", "optionid", "symbol", "root", "suffix", "cp_flag", "strike_price", "exdate"]
      dates: ["date", "exdate", "last_date"]
      measures: ["best_bid", "best_offer", "volume", "open_interest", "impl_volatility", "delta", "gamma", "vega", "theta", "forward_price", "cfadj", "contract_size"]
    joins:
      required_link_tables: ["optionm.secnmd", "optionm.optionmnames", "wrdsapps.opcrsphist if joining to CRSP"]
      joins_to_project_data: ["wrds_pipeline/pipeline.py", "wrds_pipeline/ingest_sppx_surface.py", "wrds_pipeline/oos_pricing.py"]
      point_in_time_risks: ["Resolve SPX secid as of trade date", "Use quote date strictly before OOS evaluation date", "Do not tune filters after observing results"]
    bias_risks:
      survivorship: "Low for SPX index itself, higher when expanding to equity options without historical universe controls."
      lookahead: "High if next-day quotes, final cleaned surfaces, or future expiries are used to choose calibration filters."
      restatement: "Vendor corrections can alter historical quotes; manifests should capture extract date and file hashes."
      delisting: "Not central for SPX but essential for equity-option expansion."
      corporate_actions: "Use cfadj, contract_size, distributions, and security metadata for split and special-distribution correctness."
    notes: "Catalog confirms optionm.opprcdYYYY columns including secid, date, exdate, cp_flag, strike_price, best_bid, best_offer, impl_volatility, greeks, and forward_price. Local vault appears to contain 2005-2025 yearly parquet partitions, but row counts and hashes must be verified before evidence promotion."

  - requirement_id: "QPC_P0_OPTIONM_UNDERLYING_PRICES_PANEL"
    priority: "P0_BLOCKING"
    project_need: "Validate next-day OOS pricing and delta-hedged PnL for the current WRDS panel."
    quant_use_case: "Provide same-day and next-day underlying close, return, volume, and adjustment data for SPX or equity underlyings."
    wrds_availability: "confirmed_in_catalog"
    wrds_schema: "optionm"
    wrds_table: "secprdYYYY"
    wrds_product_or_library: "OptionMetrics IvyDB US"
    logical_dataset: "Underlying security/index prices by year"
    required_for_current_reproduction: false
    required_for_current_claim_validation: true
    useful_for_future_expansion: true
    date_range:
      minimum_required: "Current pipeline panel trade dates and next trading dates."
      optimal: "2005-present, synchronized to opprcdYYYY option partitions."
      tier_split: "recent_critical"
    frequency: "daily"
    expected_size_class: "large"
    partition_strategy: "year"
    key_columns:
      identifiers: ["secid"]
      dates: ["date"]
      measures: ["open", "low", "high", "close", "volume", "return", "cfadj", "cfret", "shrout"]
    joins:
      required_link_tables: ["optionm.secnmd", "wrdsapps.opcrsphist for CRSP joins"]
      joins_to_project_data: ["wrds_pipeline/oos_pricing.py", "wrds_pipeline/delta_hedge_pnl.py"]
      point_in_time_risks: ["OOS date must be strictly after calibration date", "Holiday and weekend next-trading-day logic must be locked before evaluation"]
    bias_risks:
      survivorship: "Low for SPX index; material for equity expansion unless dead securities remain included."
      lookahead: "High if next-day close is used to tune calibration filters."
      restatement: "Vendor corrections can change returns or adjustment factors."
      delisting: "Not central for index panel; equity expansion needs delisting returns from CRSP."
      corporate_actions: "Use adjustment factors consistently with option contract adjustments."
    notes: "Catalog confirms optionm.secprdYYYY columns including secid, date, close, return, cfadj, open, volume, and shares outstanding."

  - requirement_id: "QPC_P0_OPTIONM_SECURITY_NAMES"
    priority: "P0_BLOCKING"
    project_need: "Resolve SPX and other underlyings to the correct OptionMetrics secid through time."
    quant_use_case: "Point-in-time security identity, ticker/class history, and issuer metadata for option and underlying joins."
    wrds_availability: "confirmed_in_catalog"
    wrds_schema: "optionm"
    wrds_table: "secnmd"
    wrds_product_or_library: "OptionMetrics IvyDB US"
    logical_dataset: "OptionMetrics security name master"
    required_for_current_reproduction: false
    required_for_current_claim_validation: true
    useful_for_future_expansion: true
    date_range:
      minimum_required: "As-of rows covering all current panel dates."
      optimal: "Full available history synchronized to option partitions."
      tier_split: "table_level"
    frequency: "static"
    expected_size_class: "small"
    partition_strategy: "table"
    key_columns:
      identifiers: ["secid", "cusip", "ticker", "class", "issuer", "issue", "sic"]
      dates: ["effect_date"]
      measures: []
    joins:
      required_link_tables: ["optionm.opprcdYYYY", "optionm.secprdYYYY", "optionm.optionmnames"]
      joins_to_project_data: ["SPX secid resolver in wrds_pipeline/pipeline.py"]
      point_in_time_risks: ["Use effect_date as an as-of boundary; do not use future ticker mappings."]
    bias_risks:
      survivorship: "Using current tickers only would drop renamed or inactive securities in expansions."
      lookahead: "Future name records can leak identifiers backward."
      restatement: "Name-master corrections should be versioned."
      delisting: "Name table alone does not preserve delisting outcomes."
      corporate_actions: "Does not encode all contract adjustments."
    notes: "Catalog confirms optionm.secnmd with secid, effect_date, cusip, ticker, class, issuer, issue, and sic."

  - requirement_id: "QPC_P0_OPTIONM_ZERO_CURVE"
    priority: "P0_BLOCKING"
    project_need: "Replace fallback risk-free constants in current pricing runs with documented market inputs."
    quant_use_case: "Risk-free term structure for Black-Scholes and Heston discounting and forwards."
    wrds_availability: "confirmed_in_catalog"
    wrds_schema: "optionm"
    wrds_table: "zerocd"
    wrds_product_or_library: "OptionMetrics IvyDB US"
    logical_dataset: "OptionMetrics zero-coupon rate curve"
    required_for_current_reproduction: false
    required_for_current_claim_validation: true
    useful_for_future_expansion: true
    date_range:
      minimum_required: "Each current calibration date and OOS date."
      optimal: "2005-present daily curve history."
      tier_split: "modern_research"
    frequency: "daily"
    expected_size_class: "medium"
    partition_strategy: "year"
    key_columns:
      identifiers: ["days"]
      dates: ["date"]
      measures: ["rate"]
    joins:
      required_link_tables: ["optionm.opprcdYYYY via date and maturity interpolation"]
      joins_to_project_data: ["pricing engines using rate inputs", "wrds_pipeline/calibrate_bs.py", "wrds_pipeline/calibrate_heston.py"]
      point_in_time_risks: ["Use curve as known on quote date; avoid revising rates with future curve versions unless documented."]
    bias_risks:
      survivorship: "Not applicable."
      lookahead: "Using revised or future curves can alter pricing evidence."
      restatement: "Rate vendor revisions should be versioned in manifests."
      delisting: "Not applicable."
      corporate_actions: "Not applicable."
    notes: "Catalog confirms optionm.zerocd columns date, days, and rate. This is P0 because fallback constants weaken current live/local pricing claims."

  - requirement_id: "QPC_P0_OPTIONM_INDEX_DIVIDENDS"
    priority: "P0_BLOCKING"
    project_need: "Replace fallback dividend-yield constants for SPX pricing with documented index dividend inputs."
    quant_use_case: "Dividend yield or projected dividend assumptions for index option pricing, forwards, and Heston/BS comparison."
    wrds_availability: "confirmed_in_catalog"
    wrds_schema: "optionm"
    wrds_table: "idxdvd; index_dividend"
    wrds_product_or_library: "OptionMetrics IvyDB US"
    logical_dataset: "OptionMetrics index dividend rates/projections"
    required_for_current_reproduction: false
    required_for_current_claim_validation: true
    useful_for_future_expansion: true
    date_range:
      minimum_required: "Each current SPX calibration and OOS date."
      optimal: "2005-present daily history for all index-option underlyings used."
      tier_split: "modern_research"
    frequency: "daily"
    expected_size_class: "medium"
    partition_strategy: "table"
    key_columns:
      identifiers: ["secid"]
      dates: ["date"]
      measures: ["rate", "dividend estimate fields if present"]
    joins:
      required_link_tables: ["optionm.secnmd", "optionm.opprcdYYYY"]
      joins_to_project_data: ["calibration input builder", "forward/discount calculations"]
      point_in_time_risks: ["Use only dividend estimates available as of quote date; do not infer realized future dividends unless explicitly evaluating realized PnL."]
    bias_risks:
      survivorship: "Low for SPX, material for multi-index expansion if discontinued indexes are omitted."
      lookahead: "High if realized future distributions are used as pricing inputs."
      restatement: "Projected dividends may be revised; extract vintage should be recorded."
      delisting: "Not applicable to index unless expanding universe."
      corporate_actions: "Dividend assumptions are central to forward and option-price interpretation."
    notes: "Catalog confirms optionm.idxdvd and optionm.index_dividend. Exact preferred table and field semantics need method review."

  - requirement_id: "QPC_P0_OPTIONM_DISTRIBUTIONS_ADJUSTMENTS"
    priority: "P0_BLOCKING"
    project_need: "Support corporate-action and distribution correctness for option quotes, underlyings, and any equity-option expansion."
    quant_use_case: "Adjust strikes, contract sizes, distributions, and underlying returns around splits, dividends, and special events."
    wrds_availability: "confirmed_in_catalog"
    wrds_schema: "optionm"
    wrds_table: "distrd; distribution; distribution_projection"
    wrds_product_or_library: "OptionMetrics IvyDB US"
    logical_dataset: "OptionMetrics distributions and adjustment records"
    required_for_current_reproduction: false
    required_for_current_claim_validation: true
    useful_for_future_expansion: true
    date_range:
      minimum_required: "Current SPX panel dates and surrounding expiries."
      optimal: "2005-present for all option underlyings used."
      tier_split: "modern_research"
    frequency: "event"
    expected_size_class: "medium"
    partition_strategy: "year"
    key_columns:
      identifiers: ["securityid", "linksecurityid", "distributiontype", "frequency"]
      dates: ["declaredate", "exdate", "paymentdate", "recorddate", "rundate"]
      measures: ["amount", "adjustmentfactor", "currency"]
    joins:
      required_link_tables: ["optionm.secnmd", "optionm.secprdYYYY", "optionm.opprcdYYYY"]
      joins_to_project_data: ["pricing input normalizer", "corporate-action diagnostics"]
      point_in_time_risks: ["Distribution projections must be joined by run date/as-of date, not by future realized ex-date only."]
    bias_risks:
      survivorship: "Omitting dead or adjusted contracts biases option-universe expansion."
      lookahead: "Using realized future distributions as pricing inputs can leak."
      restatement: "Distribution corrections and projections can be revised."
      delisting: "Distribution data alone does not solve delisting return bias."
      corporate_actions: "This dataset is the primary mitigation for split/special-distribution errors."
    notes: "Catalog confirms OptionMetrics distribution tables, including distrd with record_date and distribution/projection tables with declare, ex, payment, and record dates."

  - requirement_id: "QPC_P1_OPTIONM_CRSP_LINK"
    priority: "P1_CORE"
    project_need: "Link OptionMetrics secids to CRSP permnos for returns, delistings, market data, and benchmark controls."
    quant_use_case: "Cross-vendor point-in-time identity linkage for option underlyings."
    wrds_availability: "confirmed_in_catalog"
    wrds_schema: "wrdsapps; wrdsapps_link_crsp_optionm"
    wrds_table: "opcrsphist"
    wrds_product_or_library: "WRDS link tables"
    logical_dataset: "OptionMetrics to CRSP historical link"
    required_for_current_reproduction: false
    required_for_current_claim_validation: false
    useful_for_future_expansion: true
    date_range:
      minimum_required: "All dates covered by any real WRDS panel."
      optimal: "Full available history."
      tier_split: "table_level"
    frequency: "static"
    expected_size_class: "small"
    partition_strategy: "table"
    key_columns:
      identifiers: ["secid", "permno", "score or link quality field if present"]
      dates: ["sdate", "edate"]
      measures: []
    joins:
      required_link_tables: ["optionm.secnmd", "crsp.dsf", "crsp.dsenames"]
      joins_to_project_data: ["future equity-option validation and CRSP return baselines"]
      point_in_time_risks: ["Use link date intervals and link-quality filters; do not use current mappings backward."]
    bias_risks:
      survivorship: "Critical for keeping inactive and renamed securities in the panel."
      lookahead: "Future link intervals can leak if not bounded by date."
      restatement: "WRDS link tables can be revised; extract version should be logged."
      delisting: "Enables join to CRSP delisting data but does not by itself include delisting returns."
      corporate_actions: "Helps reconcile split-adjusted series across vendors."
    notes: "Catalog confirms opcrsphist in both wrdsapps and wrdsapps_link_crsp_optionm. Local vault appears to contain optionm/wrdsapps_opcrsphist.parquet."

  - requirement_id: "QPC_P1_CRSP_DAILY_EQUITY_RETURNS"
    priority: "P1_CORE"
    project_need: "Provide independent underlying returns, liquidity measures, and market data for equity-option expansion and benchmark checks."
    quant_use_case: "Daily returns, prices, volume, spreads, and adjustment factors for underlyings."
    wrds_availability: "confirmed_in_catalog"
    wrds_schema: "crsp"
    wrds_table: "dsf; dsf_v2"
    wrds_product_or_library: "CRSP US Stock"
    logical_dataset: "CRSP daily stock file"
    required_for_current_reproduction: false
    required_for_current_claim_validation: false
    useful_for_future_expansion: true
    date_range:
      minimum_required: "2005-present for equity-option expansion matching OptionMetrics local coverage."
      optimal: "Full CRSP history for long-window baselines, with 2018-present as recent critical."
      tier_split: "modern_research"
    frequency: "daily"
    expected_size_class: "huge"
    partition_strategy: "year"
    key_columns:
      identifiers: ["permno", "permco", "cusip", "ticker"]
      dates: ["date", "dlycaldt"]
      measures: ["ret", "retx", "prc", "bid", "ask", "vol", "shrout", "cfacpr", "cfacshr", "openprc", "numtrd", "dlyret", "dlyclose", "dlybid", "dlyask", "dlyvol"]
    joins:
      required_link_tables: ["wrdsapps.opcrsphist", "crsp.dsenames", "crsp.dsedelist"]
      joins_to_project_data: ["future underlying-return baselines", "delta-hedging diagnostics", "liquidity filters"]
      point_in_time_risks: ["Use CRSP date and security-name intervals; do not use current ticker membership for historical panels."]
    bias_risks:
      survivorship: "High if only current securities are selected."
      lookahead: "High if future index membership or names determine historical inclusion."
      restatement: "CRSP corrections can revise historical returns and identifiers."
      delisting: "Need dsedelist/msedelist to include delisting outcomes."
      corporate_actions: "Use CRSP adjustment factors consistently with OptionMetrics adjustments."
    notes: "Catalog confirms crsp.dsf and crsp.dsf_v2. Local vault appears to contain yearly partitions through 2024, but local partition completeness should be verified."

  - requirement_id: "QPC_P1_CRSP_SECURITY_NAMES_HISTORY"
    priority: "P1_CORE"
    project_need: "Control ticker, CUSIP, exchange, share-code, and company-name changes through time."
    quant_use_case: "Point-in-time universe construction and security identity for CRSP-linked option research."
    wrds_availability: "confirmed_in_catalog"
    wrds_schema: "crsp"
    wrds_table: "dsenames; stocknames; stocknames_v2; stksecurityinfohist"
    wrds_product_or_library: "CRSP US Stock"
    logical_dataset: "CRSP historical security names and identifiers"
    required_for_current_reproduction: false
    required_for_current_claim_validation: false
    useful_for_future_expansion: true
    date_range:
      minimum_required: "All dates covered by CRSP and OptionMetrics joins."
      optimal: "Full available history."
      tier_split: "table_level"
    frequency: "static"
    expected_size_class: "medium"
    partition_strategy: "table"
    key_columns:
      identifiers: ["permno", "permco", "cusip", "ticker", "share code", "exchange code"]
      dates: ["namedt", "nameendt", "begdt", "enddt"]
      measures: []
    joins:
      required_link_tables: ["crsp.dsf", "crsp.dsedelist", "wrdsapps.opcrsphist"]
      joins_to_project_data: ["universe filters", "survivorship diagnostics", "security identity audit"]
      point_in_time_risks: ["Historical inclusion must use date-valid names and share codes."]
    bias_risks:
      survivorship: "Critical mitigation."
      lookahead: "Future ticker/name records leak identity if joined without date bounds."
      restatement: "Identifier corrections should be versioned."
      delisting: "Pairs with delisting tables for complete exits."
      corporate_actions: "Supports split/name-event interpretation but does not replace adjustment tables."
    notes: "Catalog confirms the listed CRSP name/history tables."

  - requirement_id: "QPC_P1_CRSP_DELISTINGS"
    priority: "P1_CORE"
    project_need: "Avoid survivorship and exit-bias in any equity-option or stock-return validation."
    quant_use_case: "Delisting returns, delisting dates, and exit reasons for complete OOS return/PnL accounting."
    wrds_availability: "confirmed_in_catalog"
    wrds_schema: "crsp"
    wrds_table: "dsedelist; msedelist"
    wrds_product_or_library: "CRSP US Stock"
    logical_dataset: "CRSP daily and monthly delisting events"
    required_for_current_reproduction: false
    required_for_current_claim_validation: false
    useful_for_future_expansion: true
    date_range:
      minimum_required: "2005-present for OptionMetrics-linked equity panels."
      optimal: "Full CRSP history."
      tier_split: "full_history"
    frequency: "event"
    expected_size_class: "medium"
    partition_strategy: "table"
    key_columns:
      identifiers: ["permno", "permco"]
      dates: ["dlstdt"]
      measures: ["dlret", "dlretx", "dlstcd", "dlprc"]
    joins:
      required_link_tables: ["crsp.dsf", "crsp.dsenames", "wrdsapps.opcrsphist"]
      joins_to_project_data: ["future PnL/return panel construction", "survivorship-bias audit"]
      point_in_time_risks: ["Delisting return should be included only when known in evaluation period accounting, not as a selection filter."]
    bias_risks:
      survivorship: "Primary mitigation for dead-stock omission."
      lookahead: "Do not remove securities because a future delisting is known."
      restatement: "Delisting returns and codes may be corrected."
      delisting: "This is the required source."
      corporate_actions: "Some exits interact with mergers and distributions."
    notes: "Required before any public claim about equity-option universe performance, drawdowns, or tradability."

  - requirement_id: "QPC_P1_CRSP_CORPORATE_ACTIONS_DISTRIBUTIONS"
    priority: "P1_CORE"
    project_need: "Control distributions, splits, and share adjustments outside OptionMetrics metadata."
    quant_use_case: "Corporate-action reconciliation between CRSP returns, Compustat securities, and OptionMetrics contracts."
    wrds_availability: "confirmed_in_catalog"
    wrds_schema: "crsp"
    wrds_table: "dse; dsedist"
    wrds_product_or_library: "CRSP US Stock"
    logical_dataset: "CRSP distribution and event data"
    required_for_current_reproduction: false
    required_for_current_claim_validation: false
    useful_for_future_expansion: true
    date_range:
      minimum_required: "2005-present for equity-option expansion."
      optimal: "Full CRSP history."
      tier_split: "full_history"
    frequency: "event"
    expected_size_class: "large"
    partition_strategy: "table"
    key_columns:
      identifiers: ["permno", "permco", "distribution/event code"]
      dates: ["date", "exdt", "rcrddt", "paydt"]
      measures: ["divamt", "facpr", "facshr"]
    joins:
      required_link_tables: ["crsp.dsf", "crsp.dsenames", "wrdsapps.opcrsphist"]
      joins_to_project_data: ["corporate-action diagnostics", "option contract adjustment checks"]
      point_in_time_risks: ["Do not use future distributions as ex-ante pricing inputs unless the research design explicitly permits announced distributions."]
    bias_risks:
      survivorship: "Events for inactive names must remain available."
      lookahead: "Future corporate events can leak into universe or pricing filters."
      restatement: "Corrections are possible."
      delisting: "Some delisting/merger events require joint handling with delisting tables."
      corporate_actions: "Primary mitigation source."
    notes: "Needed to make equity-option extensions credible under splits, special dividends, mergers, and share adjustments."

  - requirement_id: "QPC_P1_CRSP_INDEX_MEMBERSHIP_AND_RETURNS"
    priority: "P1_CORE"
    project_need: "Benchmark SPX results, build point-in-time index universes, and compare against index returns."
    quant_use_case: "S&P 500 membership history, index-level returns, and market benchmark controls."
    wrds_availability: "confirmed_in_catalog"
    wrds_schema: "crsp"
    wrds_table: "dsp500list; dsp500list_v2; msp500list; dsp500; dsp500_v2; dsi; wrds_dailyindexret_query; wrds_monthlyindexret_query"
    wrds_product_or_library: "CRSP Indexes"
    logical_dataset: "CRSP index constituents and index returns"
    required_for_current_reproduction: false
    required_for_current_claim_validation: false
    useful_for_future_expansion: true
    date_range:
      minimum_required: "2005-present for OptionMetrics-linked SPX/equity-option research."
      optimal: "Full available history."
      tier_split: "modern_research"
    frequency: "daily"
    expected_size_class: "large"
    partition_strategy: "table"
    key_columns:
      identifiers: ["permno", "index id", "ticker"]
      dates: ["date", "start", "ending", "mbrstartdt", "mbrenddt"]
      measures: ["index return", "level", "weight if available"]
    joins:
      required_link_tables: ["crsp.dsf", "crsp.dsenames", "crsp.dsedelist"]
      joins_to_project_data: ["benchmark comparison tables", "holdout universe construction"]
      point_in_time_risks: ["Membership must be as-of date, not current constituents."]
    bias_risks:
      survivorship: "Critical for avoiding current-constituent backtests."
      lookahead: "Future index additions/deletions leak if not date-bounded."
      restatement: "Index files can be revised."
      delisting: "Dropped members need delisting handling."
      corporate_actions: "Index return series incorporates corporate actions but constituent panels need explicit handling."
    notes: "Catalog confirms CRSP S&P 500 membership and index return tables."

  - requirement_id: "QPC_P1_CCM_LINKS"
    priority: "P1_CORE"
    project_need: "Join CRSP securities to Compustat fundamentals with date-valid link rules."
    quant_use_case: "Accounting and valuation controls for option universe research."
    wrds_availability: "confirmed_in_catalog"
    wrds_schema: "crsp"
    wrds_table: "ccmxpf_linktable; ccmxpf_lnkhist"
    wrds_product_or_library: "CRSP/Compustat Merged"
    logical_dataset: "CRSP-Compustat link history"
    required_for_current_reproduction: false
    required_for_current_claim_validation: false
    useful_for_future_expansion: true
    date_range:
      minimum_required: "2005-present for equity-option expansion."
      optimal: "Full available history."
      tier_split: "table_level"
    frequency: "static"
    expected_size_class: "medium"
    partition_strategy: "table"
    key_columns:
      identifiers: ["gvkey", "lpermno", "lpermco", "linktype", "linkprim"]
      dates: ["linkdt", "linkenddt"]
      measures: []
    joins:
      required_link_tables: ["crsp.dsf", "comp.funda", "comp.fundq"]
      joins_to_project_data: ["future feature joins", "fundamental baselines"]
      point_in_time_risks: ["Use link date intervals and accepted link types only."]
    bias_risks:
      survivorship: "Incorrect links can drop or misassign inactive firms."
      lookahead: "Using future gvkey/permno relations leaks identity."
      restatement: "Link corrections should be logged."
      delisting: "Links help connect delisted firms to fundamentals but do not include delisting returns."
      corporate_actions: "Helps track issuer continuity through corporate events."
    notes: "Catalog confirms CCM link tables."

  - requirement_id: "QPC_P1_COMPUSTAT_FUNDAMENTALS"
    priority: "P1_CORE"
    project_need: "Provide fundamentals, accounting controls, size/value/profitability features, and issuer metadata."
    quant_use_case: "Fundamental controls and baseline features for option pricing/volatility cross sections."
    wrds_availability: "confirmed_in_catalog"
    wrds_schema: "comp"
    wrds_table: "funda; fundq; company; security; secm; namesq"
    wrds_product_or_library: "Compustat North America"
    logical_dataset: "Compustat annual, quarterly, company, and security data"
    required_for_current_reproduction: false
    required_for_current_claim_validation: false
    useful_for_future_expansion: true
    date_range:
      minimum_required: "2005-present for modern option-research features."
      optimal: "Full available history, with point-in-time reporting lag policy."
      tier_split: "modern_research"
    frequency: "quarterly"
    expected_size_class: "large"
    partition_strategy: "year"
    key_columns:
      identifiers: ["gvkey", "iid", "cusip", "tic", "conm"]
      dates: ["datadate", "rdq", "fyear", "fqtr"]
      measures: ["at", "ceq", "sale", "ni", "ib", "oancf", "lt", "dltt", "dlc", "csho", "prcc_f", "prccq", "mkvalt"]
    joins:
      required_link_tables: ["crsp.ccmxpf_linktable", "crsp.ccmxpf_lnkhist", "crsp.dsf"]
      joins_to_project_data: ["future feature generation", "baseline controls", "fundamental risk diagnostics"]
      point_in_time_risks: ["Use report dates or conservative lags; do not use restated fields as if known on datadate."]
    bias_risks:
      survivorship: "Use historical company/security files and CCM links."
      lookahead: "High if datadate is used without reporting lag."
      restatement: "High because Compustat values may be restated; document point-in-time policy."
      delisting: "Must pair with CRSP delisting for complete return outcomes."
      corporate_actions: "Security and share fields need adjustment and link checks."
    notes: "Catalog confirms Compustat core tables. Local vault appears to contain 2005-2025 annual and quarterly partitions."

  - requirement_id: "QPC_P1_FAMA_FRENCH_FACTORS"
    priority: "P1_CORE"
    project_need: "Benchmark returns, PnL, and factor exposures against standard academic baselines."
    quant_use_case: "Market, size, value, profitability, investment, momentum, industry, and liquidity factor controls."
    wrds_availability: "confirmed_in_catalog"
    wrds_schema: "ff"
    wrds_table: "factors_daily; fivefactors_daily; factors_monthly; industry48; liq_ps; liq_sadka"
    wrds_product_or_library: "Fama-French and liquidity factors"
    logical_dataset: "Academic factor benchmark data"
    required_for_current_reproduction: false
    required_for_current_claim_validation: false
    useful_for_future_expansion: true
    date_range:
      minimum_required: "2005-present for modern option-research baselines."
      optimal: "Full available history."
      tier_split: "full_history"
    frequency: "daily"
    expected_size_class: "small"
    partition_strategy: "table"
    key_columns:
      identifiers: ["factor name", "industry portfolio id"]
      dates: ["date", "month"]
      measures: ["mktrf", "smb", "hml", "rmw", "cma", "rf", "umd", "liquidity factors", "industry returns"]
    joins:
      required_link_tables: ["CRSP date calendar"]
      joins_to_project_data: ["future benchmark and attribution reports"]
      point_in_time_risks: ["Use the factor vintage/extract date consistently for public evidence."]
    bias_risks:
      survivorship: "Handled by factor construction but external methodology should be cited."
      lookahead: "Factor revisions/vintages can matter for strict live simulations."
      restatement: "Factors can be revised."
      delisting: "Handled indirectly by provider methodology."
      corporate_actions: "Handled indirectly by provider methodology."
    notes: "Catalog confirms daily, five-factor, monthly, industry, and liquidity tables."

  - requirement_id: "QPC_P1_CRSP_TREASURY_RISK_FREE"
    priority: "P1_CORE"
    project_need: "Independent rate sanity checks and alternative discount curves outside OptionMetrics."
    quant_use_case: "Treasury curve, risk-free rate, CPI, and bond-yield controls for option-pricing diagnostics."
    wrds_availability: "confirmed_in_catalog"
    wrds_schema: "crsp"
    wrds_table: "riskfree; tfz_dly; tfz_dly_cd; tfz_dly_rf2; tfz_dly_ts2; bmyield; bxyield"
    wrds_product_or_library: "CRSP Treasury and fixed income"
    logical_dataset: "CRSP risk-free and Treasury term structure data"
    required_for_current_reproduction: false
    required_for_current_claim_validation: false
    useful_for_future_expansion: true
    date_range:
      minimum_required: "2005-present for OptionMetrics comparison."
      optimal: "Full available history."
      tier_split: "full_history"
    frequency: "daily"
    expected_size_class: "medium"
    partition_strategy: "table"
    key_columns:
      identifiers: ["maturity", "curve id", "term"]
      dates: ["date", "caldt"]
      measures: ["risk-free rate", "zero yield", "Treasury yield", "CPI"]
    joins:
      required_link_tables: ["calendar date"]
      joins_to_project_data: ["rate sensitivity diagnostics", "model-input robustness checks"]
      point_in_time_risks: ["Use the curve known at quote date; document whether revised histories are acceptable."]
    bias_risks:
      survivorship: "Not central."
      lookahead: "Using future or revised rates can leak."
      restatement: "Rate histories may be revised."
      delisting: "Not applicable."
      corporate_actions: "Not applicable."
    notes: "Not a replacement for OptionMetrics zero curve in the current pipeline, but useful for independent model-input checks."

  - requirement_id: "QPC_P2_OPTIONM_FULL_UNDERLYING_UNIVERSE"
    priority: "P2_HIGH_VALUE"
    project_need: "Move beyond SPX sample panels toward broad index and equity-option out-of-sample validation."
    quant_use_case: "Cross-sectional option-pricing validation, liquidity-stratified diagnostics, and model generalization tests."
    wrds_availability: "confirmed_in_catalog"
    wrds_schema: "optionm"
    wrds_table: "opprcdYYYY; secprdYYYY; secnmd; optionmnames"
    wrds_product_or_library: "OptionMetrics IvyDB US"
    logical_dataset: "Full US listed option quote and underlying panel"
    required_for_current_reproduction: false
    required_for_current_claim_validation: false
    useful_for_future_expansion: true
    date_range:
      minimum_required: "2018-present for recent critical holdouts."
      optimal: "2005-present modern research panel; full available history only after protocol stabilizes."
      tier_split: "modern_research"
    frequency: "daily"
    expected_size_class: "huge"
    partition_strategy: "year"
    key_columns:
      identifiers: ["secid", "optionid", "ticker", "cusip", "cp_flag", "strike_price", "exdate"]
      dates: ["date", "exdate", "effect_date"]
      measures: ["best_bid", "best_offer", "impl_volatility", "open_interest", "volume", "greeks", "underlying close", "return"]
    joins:
      required_link_tables: ["optionm.secnmd", "optionm.optionmnames", "wrdsapps.opcrsphist", "crsp.dsf", "crsp.dsenames", "crsp.dsedelist"]
      joins_to_project_data: ["future broad validation matrix", "liquidity filters", "holdout generator"]
      point_in_time_risks: ["Universe filters, liquidity screens, and date panels must be fixed before result inspection."]
    bias_risks:
      survivorship: "High without CRSP names/delisting and OptionMetrics dead-security coverage."
      lookahead: "High if filters are chosen after seeing performance."
      restatement: "Vendor corrections require extract manifests."
      delisting: "Equity options require delisting and dead-underlying handling."
      corporate_actions: "Contract adjustments and special distributions must be audited."
    notes: "This is the natural next prestige expansion after the P0 SPX panel is locked."

  - requirement_id: "QPC_P2_IBES_EARNINGS_ESTIMATES_ACTUALS"
    priority: "P2_HIGH_VALUE"
    project_need: "Control for earnings expectations and event risk in equity-option pricing and volatility studies."
    quant_use_case: "Expected/actual earnings, analyst dispersion, surprise, and announcement-event windows."
    wrds_availability: "confirmed_in_catalog"
    wrds_schema: "ibes"
    wrds_table: "statsumu_epsus; detu_epsus; actu_epsus"
    wrds_product_or_library: "IBES"
    logical_dataset: "IBES US EPS summary, detail estimates, and actuals"
    required_for_current_reproduction: false
    required_for_current_claim_validation: false
    useful_for_future_expansion: true
    date_range:
      minimum_required: "2005-present for OptionMetrics-linked equity options."
      optimal: "Full available history with point-in-time estimate revision handling."
      tier_split: "modern_research"
    frequency: "event"
    expected_size_class: "large"
    partition_strategy: "year"
    key_columns:
      identifiers: ["ticker", "cusip", "oftic", "estimator", "analys", "measure", "fpi"]
      dates: ["statpers", "fpedats", "actdats", "revdats", "anndats", "anntims", "acttims"]
      measures: ["numest", "numup", "numdown", "medest", "meanest", "stdev", "highest", "lowest", "value", "actual"]
    joins:
      required_link_tables: ["IBES-CRSP link if available", "CRSP names", "CCM links"]
      joins_to_project_data: ["event controls", "earnings-volatility diagnostics", "holdout stratification"]
      point_in_time_risks: ["Use estimate revision timestamps; do not use final consensus after announcement for pre-announcement pricing."]
    bias_risks:
      survivorship: "Analyst coverage is non-random and can omit failed/small firms."
      lookahead: "Very high if revised estimates or actuals are available before event time."
      restatement: "Actuals and estimates can be revised."
      delisting: "Needs CRSP delisting controls for post-event returns."
      corporate_actions: "Ticker/CUSIP changes require robust links."
    notes: "Catalog confirms the listed IBES EPS tables and timestamp fields."

  - requirement_id: "QPC_P2_IBES_RECOMMENDATIONS_PRICE_TARGETS"
    priority: "P2_HIGH_VALUE"
    project_need: "Add analyst sentiment and target-price controls for option-implied move and volatility research."
    quant_use_case: "Recommendation changes, consensus recommendations, and price-target revisions as event and sentiment controls."
    wrds_availability: "confirmed_in_catalog"
    wrds_schema: "ibes"
    wrds_table: "recdsum; recddet; recdid; recdidsum; recdstp; ptgdet; ptgsum"
    wrds_product_or_library: "IBES"
    logical_dataset: "IBES recommendations and price targets"
    required_for_current_reproduction: false
    required_for_current_claim_validation: false
    useful_for_future_expansion: true
    date_range:
      minimum_required: "2005-present."
      optimal: "Full available history."
      tier_split: "modern_research"
    frequency: "event"
    expected_size_class: "large"
    partition_strategy: "year"
    key_columns:
      identifiers: ["ticker", "cusip", "broker", "analyst", "recommendation id"]
      dates: ["announcement date", "revision date", "statistical period"]
      measures: ["recommendation level", "price target", "number of analysts", "consensus measures"]
    joins:
      required_link_tables: ["IBES-CRSP link if available", "CRSP names", "CCM links"]
      joins_to_project_data: ["event controls", "sentiment diagnostics", "feature experiments"]
      point_in_time_risks: ["Use announcement/revision timestamps; avoid consensus values computed after the trade date."]
    bias_risks:
      survivorship: "Coverage is non-random."
      lookahead: "High without strict revision-date handling."
      restatement: "Vendor histories can be backfilled."
      delisting: "Needs CRSP delisting and dead-firm retention."
      corporate_actions: "Identifier changes must be linked."
    notes: "Useful after core pricing validation, not needed for current SPX claims."

  - requirement_id: "QPC_P2_CIQ_EVENTS_IDENTIFIERS"
    priority: "P2_HIGH_VALUE"
    project_need: "Add corporate event controls and richer cross-vendor identifiers."
    quant_use_case: "Key developments, event studies, issuer mapping, and event-day volatility diagnostics."
    wrds_availability: "confirmed_in_catalog"
    wrds_schema: "ciq"
    wrds_table: "wrds_keydev; ciqcompany; ciqsecurity; ciqtradingitem; ciqgvkeyiid"
    wrds_product_or_library: "Capital IQ"
    logical_dataset: "CIQ key developments and identifier master"
    required_for_current_reproduction: false
    required_for_current_claim_validation: false
    useful_for_future_expansion: true
    date_range:
      minimum_required: "2005-present for equity-option event controls."
      optimal: "Full available history."
      tier_split: "modern_research"
    frequency: "event"
    expected_size_class: "large"
    partition_strategy: "year"
    key_columns:
      identifiers: ["companyid", "securityid", "tradingitemid", "gvkey", "iid", "ticker"]
      dates: ["announceddate", "eventdate", "startdate", "enddate"]
      measures: ["key development type", "headline/category fields", "event status"]
    joins:
      required_link_tables: ["ciqgvkeyiid", "CCM links", "CRSP names"]
      joins_to_project_data: ["event exclusion windows", "regime/event diagnostics", "future feature generation"]
      point_in_time_risks: ["Use announcement timestamps and avoid events loaded from future corrections as ex-ante signals."]
    bias_risks:
      survivorship: "Coverage varies by firm size and period."
      lookahead: "Event databases are often backfilled; timestamp policy is required."
      restatement: "Event records can be corrected."
      delisting: "Event data must be linked to CRSP exits."
      corporate_actions: "Useful for mergers/spinoffs but needs identity controls."
    notes: "Catalog confirms the listed CIQ tables."

  - requirement_id: "QPC_P2_SHORT_INTEREST"
    priority: "P2_HIGH_VALUE"
    project_need: "Control for crowded short demand, squeeze risk, and stock-borrow friction proxies."
    quant_use_case: "Short-interest features, liquidity/friction diagnostics, and feasibility screens for equity-option strategies."
    wrds_availability: "confirmed_in_catalog"
    wrds_schema: "comp"
    wrds_table: "sec_shortint; sec_shortint_legacy"
    wrds_product_or_library: "Compustat securities short interest"
    logical_dataset: "Security-level short interest"
    required_for_current_reproduction: false
    required_for_current_claim_validation: false
    useful_for_future_expansion: true
    date_range:
      minimum_required: "2005-present."
      optimal: "Full available history."
      tier_split: "modern_research"
    frequency: "monthly"
    expected_size_class: "medium"
    partition_strategy: "table"
    key_columns:
      identifiers: ["gvkey", "iid", "cusip", "ticker"]
      dates: ["datadate", "settlement date if present"]
      measures: ["short interest", "shares outstanding", "days to cover if present"]
    joins:
      required_link_tables: ["CCM links", "CRSP names", "Compustat security"]
      joins_to_project_data: ["future borrow/crowding diagnostics", "liquidity filters"]
      point_in_time_risks: ["Short interest has publication lag; do not treat settlement values as known immediately unless lagged."]
    bias_risks:
      survivorship: "Coverage and identifier continuity matter."
      lookahead: "Publication lag is a major risk."
      restatement: "Corrections can occur."
      delisting: "Needs CRSP delisting controls."
      corporate_actions: "Share changes affect interpretation."
    notes: "Catalog confirms Compustat short-interest tables."

  - requirement_id: "QPC_P2_HOLDINGS_AND_13F"
    priority: "P2_HIGH_VALUE"
    project_need: "Add institutional ownership and crowding controls."
    quant_use_case: "Institutional demand, ownership concentration, liquidity, and factor-crowding diagnostics."
    wrds_availability: "confirmed_in_catalog"
    wrds_schema: "tfn; tr_13f; secsamp_all; ftse; ftse_russell_us"
    wrds_table: "s34; s34names; wrds_13f_holdings; wrds_13f_link; idx_holdings_us"
    wrds_product_or_library: "Thomson/Refinitiv 13F, SEC 13F, FTSE Russell holdings"
    logical_dataset: "Institutional holdings and index holdings"
    required_for_current_reproduction: false
    required_for_current_claim_validation: false
    useful_for_future_expansion: true
    date_range:
      minimum_required: "2005-present with reporting lag."
      optimal: "Full available history."
      tier_split: "modern_research"
    frequency: "quarterly"
    expected_size_class: "large"
    partition_strategy: "year"
    key_columns:
      identifiers: ["mgrno", "cusip", "permno", "gvkey", "issuer", "index id"]
      dates: ["rdate", "fdate", "report date", "membership date"]
      measures: ["shares held", "market value", "weight", "shares outstanding"]
    joins:
      required_link_tables: ["CRSP names", "CCM links", "13F link tables"]
      joins_to_project_data: ["future crowding controls", "liquidity diagnostics", "index benchmark attribution"]
      point_in_time_risks: ["Use filing/publication lag; avoid using quarter-end holdings before disclosure."]
    bias_risks:
      survivorship: "Manager and security coverage changes matter."
      lookahead: "Filing lag is central."
      restatement: "Amended filings can revise holdings."
      delisting: "Needs dead security identity handling."
      corporate_actions: "CUSIP/security changes require links."
    notes: "Catalog confirms tfn.s34, tr_13f S34-style tables, SEC 13F holdings/link tables, and FTSE Russell holdings tables. Verify whether available SEC tables are sample-only or full entitlement before use."

  - requirement_id: "QPC_P2_CBOE_EOD_OPTIONS_BENCHMARK"
    priority: "P2_HIGH_VALUE"
    project_need: "Provide an independent options-data cross-check outside OptionMetrics."
    quant_use_case: "Cross-vendor validation of option quotes, implied volatility, borrow proxies, and end-of-day option surfaces."
    wrds_availability: "confirmed_in_catalog"
    wrds_schema: "cboe"
    wrds_table: "optprice; optprice_YYYY; optcontract; eqprice; eqhvol; ivborrowrate; eqmaster"
    wrds_product_or_library: "CBOE DataShop via WRDS"
    logical_dataset: "CBOE option and equity end-of-day data"
    required_for_current_reproduction: false
    required_for_current_claim_validation: false
    useful_for_future_expansion: true
    date_range:
      minimum_required: "2018-present for recent critical cross-checks."
      optimal: "2005-present if entitled and comparable to OptionMetrics coverage."
      tier_split: "recent_critical"
    frequency: "daily"
    expected_size_class: "huge"
    partition_strategy: "year"
    key_columns:
      identifiers: ["option contract id", "underlying symbol", "expiration", "strike", "put_call"]
      dates: ["trade date", "expiration date"]
      measures: ["bid", "ask", "price", "volume", "open interest", "implied volatility", "borrow rate", "historical volatility"]
    joins:
      required_link_tables: ["CBOE contract master", "CRSP names if linking to equities"]
      joins_to_project_data: ["cross-vendor quote validation", "fallback benchmark datasets"]
      point_in_time_risks: ["Do not pick the vendor with better results after the fact; define cross-check protocol before comparison."]
    bias_risks:
      survivorship: "Depends on contract master and dead-contract retention."
      lookahead: "Cross-vendor selection after results is a research-design risk."
      restatement: "Vendor corrections possible."
      delisting: "Equity underlying delistings still need CRSP."
      corporate_actions: "Contract-adjustment consistency must be checked."
    notes: "Catalog confirms CBOE option/equity/borrow-rate tables. Entitlement and coverage should be checked before planning around it."

  - requirement_id: "QPC_P2_COMPUSTAT_INDEX_CONSTITUENTS"
    priority: "P2_HIGH_VALUE"
    project_need: "Construct point-in-time benchmark universes and compare index membership sources."
    quant_use_case: "Survivorship-bias control, benchmark definition, and S&P/sector membership diagnostics."
    wrds_availability: "confirmed_in_catalog"
    wrds_schema: "comp"
    wrds_table: "idx_index; indexcst_his; spidx_cst; wrds_idx_cst_current"
    wrds_product_or_library: "Compustat Index Constituents"
    logical_dataset: "Compustat index membership history"
    required_for_current_reproduction: false
    required_for_current_claim_validation: false
    useful_for_future_expansion: true
    date_range:
      minimum_required: "2005-present."
      optimal: "Full available history."
      tier_split: "modern_research"
    frequency: "event"
    expected_size_class: "medium"
    partition_strategy: "table"
    key_columns:
      identifiers: ["gvkey", "iid", "index id", "ticker", "cusip"]
      dates: ["from date", "through date", "datadate"]
      measures: ["constituent weight if present", "index level metadata"]
    joins:
      required_link_tables: ["CCM links", "CRSP names", "Compustat security"]
      joins_to_project_data: ["benchmark universe construction", "index comparison diagnostics"]
      point_in_time_risks: ["Use historical constituent intervals, not current constituent files, for backtests."]
    bias_risks:
      survivorship: "Primary risk if current index files are used historically."
      lookahead: "Future index membership leaks if intervals are ignored."
      restatement: "Index histories may be revised."
      delisting: "Dropped constituents need exit handling."
      corporate_actions: "Index membership changes often coincide with corporate events."
    notes: "Catalog confirms Compustat index constituent tables."

  - requirement_id: "QPC_P3_TAQ_INTRADAY_QUOTES_TRADES"
    priority: "P3_SPECIALIZED"
    project_need: "Support intraday liquidity, execution, bid-ask spread, and microstructure diagnostics."
    quant_use_case: "NBBO and trade-level validation for option-underlying execution assumptions and liquidity filters."
    wrds_availability: "confirmed_in_catalog"
    wrds_schema: "taqmsec; taqm_YYYY"
    wrds_table: "complete_nbbo_YYYY; ctm_YYYYMMDD; cqm_YYYYMMDD"
    wrds_product_or_library: "NYSE TAQ"
    logical_dataset: "Intraday trades, quotes, and NBBO"
    required_for_current_reproduction: false
    required_for_current_claim_validation: false
    useful_for_future_expansion: true
    date_range:
      minimum_required: "Selected event windows only, after a strict protocol is defined."
      optimal: "2018-present recent critical windows; full history only for specialized microstructure studies."
      tier_split: "recent_critical"
    frequency: "intraday"
    expected_size_class: "huge"
    partition_strategy: "date_range"
    key_columns:
      identifiers: ["symbol", "exchange", "condition codes", "participant ids if present"]
      dates: ["date", "time", "timestamp"]
      measures: ["bid", "ask", "bid size", "ask size", "trade price", "trade size", "NBBO"]
    joins:
      required_link_tables: ["CRSP names", "exchange symbol history"]
      joins_to_project_data: ["execution-cost diagnostics", "liquidity filters", "high-frequency validation extensions"]
      point_in_time_risks: ["Intraday timestamps, corrections, and condition-code filters must be fixed before analysis."]
    bias_risks:
      survivorship: "Symbol mapping and exchange changes are major risks."
      lookahead: "Condition-code filtering after seeing results can bias execution estimates."
      restatement: "TAQ corrections and late records can change data."
      delisting: "Requires historical symbol support."
      corporate_actions: "Intraday symbol continuity around events must be handled."
    notes: "Huge and not needed for current evidence. Download only targeted windows unless a microstructure ticket explicitly requires more."

  - requirement_id: "QPC_P3_TRACE_BOND_MARKET"
    priority: "P3_SPECIALIZED"
    project_need: "Add credit-market controls and corporate bond liquidity/spread diagnostics for equity-option research."
    quant_use_case: "Credit spread, debt-market stress, and issuer credit-event controls."
    wrds_availability: "confirmed_in_catalog"
    wrds_schema: "trace; trace_enhanced; wrdsapps"
    wrds_table: "trace_enhanced; trace_enhanced_clean"
    wrds_product_or_library: "TRACE"
    logical_dataset: "Corporate bond trades and cleaned enhanced TRACE"
    required_for_current_reproduction: false
    required_for_current_claim_validation: false
    useful_for_future_expansion: true
    date_range:
      minimum_required: "2018-present for recent stress/regime controls."
      optimal: "Full enhanced TRACE available history."
      tier_split: "modern_research"
    frequency: "intraday"
    expected_size_class: "huge"
    partition_strategy: "date_range"
    key_columns:
      identifiers: ["cusip", "issuer id", "bond id"]
      dates: ["trd_exctn_dt", "trd_exctn_tm"]
      measures: ["price", "yield", "trade size", "side", "cleaning flags"]
    joins:
      required_link_tables: ["Mergent/FISD bond master if entitled", "CRSP/Compustat issuer links"]
      joins_to_project_data: ["credit-regime diagnostics", "event controls"]
      point_in_time_risks: ["Use cleaned protocol consistently; do not mix revised clean data with ex-ante claims without disclosure."]
    bias_risks:
      survivorship: "Issuer/bond availability and inactive bonds matter."
      lookahead: "Cleaned enhanced data may include corrections not known intraday."
      restatement: "Trade corrections and cleaning revisions possible."
      delisting: "Bond maturity/default handling needed."
      corporate_actions: "Issuer events and reorganizations complicate links."
    notes: "Specialized; valuable for regime diagnostics but not for core option-pricing evidence."

  - requirement_id: "QPC_P3_SDC_ISSUANCE_MA"
    priority: "P3_SPECIALIZED"
    project_need: "Control for M&A, issuance, and corporate finance event regimes."
    quant_use_case: "M&A announcement effects, equity issuance dilution, and event-window option behavior."
    wrds_availability: "confirmed_in_catalog"
    wrds_schema: "sdc"
    wrds_table: "wrds_ma_details; wrds_ni_details"
    wrds_product_or_library: "SDC Platinum"
    logical_dataset: "M&A and new-issues event data"
    required_for_current_reproduction: false
    required_for_current_claim_validation: false
    useful_for_future_expansion: true
    date_range:
      minimum_required: "2005-present for OptionMetrics-linked issuers."
      optimal: "Full available history."
      tier_split: "modern_research"
    frequency: "event"
    expected_size_class: "large"
    partition_strategy: "year"
    key_columns:
      identifiers: ["cusip", "ticker", "gvkey if available", "deal id", "issuer id"]
      dates: ["announcement date", "completion date", "filing date"]
      measures: ["deal value", "offer type", "status", "payment type", "proceeds"]
    joins:
      required_link_tables: ["CRSP names", "CCM links", "CIQ identifiers if used"]
      joins_to_project_data: ["event exclusion windows", "corporate action diagnostics"]
      point_in_time_risks: ["Announcement and completion statuses must be date-stamped; final outcomes cannot be used as ex-ante signals."]
    bias_risks:
      survivorship: "Deal coverage varies by size and period."
      lookahead: "Final deal status can leak."
      restatement: "Deal terms and status can be revised."
      delisting: "M&A exits must be reconciled with CRSP delistings."
      corporate_actions: "Highly relevant."
    notes: "Specialized event-control dataset."

  - requirement_id: "QPC_P3_CBOE_BORROW_RATE_PROXY"
    priority: "P3_SPECIALIZED"
    project_need: "Improve borrow/cost modeling when evaluating option strategies on hard-to-borrow underlyings."
    quant_use_case: "Borrow-rate proxy, short-sale friction controls, and option mispricing diagnostics."
    wrds_availability: "confirmed_in_catalog"
    wrds_schema: "cboe"
    wrds_table: "ivborrowrate"
    wrds_product_or_library: "CBOE"
    logical_dataset: "CBOE implied borrow rate"
    required_for_current_reproduction: false
    required_for_current_claim_validation: false
    useful_for_future_expansion: true
    date_range:
      minimum_required: "2018-present for recent critical equity-option diagnostics."
      optimal: "Full available history if entitled."
      tier_split: "recent_critical"
    frequency: "daily"
    expected_size_class: "large"
    partition_strategy: "year"
    key_columns:
      identifiers: ["underlying symbol", "security id if present"]
      dates: ["date"]
      measures: ["implied borrow rate", "supporting option or equity fields if present"]
    joins:
      required_link_tables: ["CBOE master", "CRSP names"]
      joins_to_project_data: ["borrow-friction diagnostics", "future strategy feasibility reports"]
      point_in_time_risks: ["Borrow proxy construction must be documented before using it as evidence."]
    bias_risks:
      survivorship: "Borrow data may be missing for less liquid/dead names."
      lookahead: "Derived rates may reflect contemporaneous option surfaces; use date-consistent joins."
      restatement: "Vendor corrections possible."
      delisting: "Needs dead-security handling."
      corporate_actions: "Identifier continuity and split handling matter."
    notes: "Confirmed in catalog but not a substitute for true securities-lending data if the project later models borrow costs explicitly."

  - requirement_id: "QPC_P3_MARKIT_SECURITIES_FINANCE"
    priority: "P3_SPECIALIZED"
    project_need: "Add direct securities-lending supply, fee, and utilization data for friction-aware option strategy research."
    quant_use_case: "Borrow fees, lendable supply, utilization, recall risk, and hard-to-borrow controls."
    wrds_availability: "entitlement_gap"
    wrds_schema: "markit or securities finance product"
    wrds_table: "needs catalog and entitlement verification"
    wrds_product_or_library: "Markit Securities Finance or equivalent"
    logical_dataset: "Securities lending and borrow cost data"
    required_for_current_reproduction: false
    required_for_current_claim_validation: false
    useful_for_future_expansion: true
    date_range:
      minimum_required: "2018-present for recent critical strategy feasibility checks."
      optimal: "2005-present if available and licensed."
      tier_split: "recent_critical"
    frequency: "daily"
    expected_size_class: "huge"
    partition_strategy: "year"
    key_columns:
      identifiers: ["cusip", "isin", "ticker", "loan/security id"]
      dates: ["date"]
      measures: ["borrow fee", "utilization", "lendable value", "on-loan value", "rebate", "short supply"]
    joins:
      required_link_tables: ["CRSP names", "CCM links", "security lending identifier link"]
      joins_to_project_data: ["future transaction-cost model", "strategy feasibility diagnostics"]
      point_in_time_risks: ["Fees and utilization must be observed as of trade date; publication lag and vendor coverage must be documented."]
    bias_risks:
      survivorship: "Coverage skew toward lendable/institutional names."
      lookahead: "Future borrow conditions cannot be used for entry decisions."
      restatement: "Vendor corrections possible."
      delisting: "Needs dead-security handling."
      corporate_actions: "CUSIP/ISIN changes matter."
    notes: "Conceptually very useful, but local catalog confirmation was not established as a concrete table in this analysis. Treat as entitlement-dependent."

  - requirement_id: "QPC_P3_CIQ_TRANSCRIPTS_KEYDEVS"
    priority: "P3_SPECIALIZED"
    project_need: "Support text/event research around earnings calls and corporate announcements."
    quant_use_case: "Transcript sentiment, management guidance, event classification, and volatility-event studies."
    wrds_availability: "confirmed_in_catalog"
    wrds_schema: "ciq"
    wrds_table: "wrds_transcript_detail; wrds_keydev"
    wrds_product_or_library: "Capital IQ Transcripts and Key Developments"
    logical_dataset: "Corporate transcripts and key developments"
    required_for_current_reproduction: false
    required_for_current_claim_validation: false
    useful_for_future_expansion: true
    date_range:
      minimum_required: "2018-present if doing modern NLP/event work."
      optimal: "Full available transcript history."
      tier_split: "recent_critical"
    frequency: "event"
    expected_size_class: "huge"
    partition_strategy: "year"
    key_columns:
      identifiers: ["companyid", "transcriptid", "keydevid", "securityid"]
      dates: ["event date", "transcript date", "announced date"]
      measures: ["speaker text", "event type", "headline", "transcript component fields"]
    joins:
      required_link_tables: ["ciqgvkeyiid", "CCM links", "CRSP names"]
      joins_to_project_data: ["future NLP features", "event windows", "volatility-event diagnostics"]
      point_in_time_risks: ["Transcripts may be corrected after the event; use availability timestamp if modeling ex-ante use."]
    bias_risks:
      survivorship: "Transcript coverage varies by firm and period."
      lookahead: "Corrected transcript text and future event categories can leak."
      restatement: "Transcript corrections are possible."
      delisting: "Needs dead-firm links."
      corporate_actions: "Company identifiers can change through mergers/spinoffs."
    notes: "Not needed before the core pricing evidence is trustworthy."

  - requirement_id: "QPC_P3_MACRO_REGIME_CONTROLS"
    priority: "P3_SPECIALIZED"
    project_need: "Classify market regimes and macro states for stress/calm validation panels."
    quant_use_case: "Inflation, yield-curve, macro factor, and market stress controls for holdout stratification."
    wrds_availability: "confirmed_in_catalog"
    wrds_schema: "macrofin; crsp"
    wrds_table: "q_factors_daily; q_factors_weekly; q_factors_monthly; tfz_dly_cpi; tfz_mth_cpi"
    wrds_product_or_library: "WRDS Macro Finance and CRSP macro/rates"
    logical_dataset: "Macro and regime-control data"
    required_for_current_reproduction: false
    required_for_current_claim_validation: false
    useful_for_future_expansion: true
    date_range:
      minimum_required: "2005-present for modern option panels."
      optimal: "Full available history."
      tier_split: "modern_research"
    frequency: "daily"
    expected_size_class: "medium"
    partition_strategy: "table"
    key_columns:
      identifiers: ["factor id", "macro series id"]
      dates: ["date", "month", "week"]
      measures: ["macro factors", "CPI", "yield curve", "market state variables"]
    joins:
      required_link_tables: ["calendar date"]
      joins_to_project_data: ["regime labels", "stress/calm panel design", "benchmark reports"]
      point_in_time_risks: ["Macro releases and revisions must be lagged if used as ex-ante features."]
    bias_risks:
      survivorship: "Not central."
      lookahead: "Macro revisions and final vintages can leak."
      restatement: "High for macro series unless vintage data is used."
      delisting: "Not applicable."
      corporate_actions: "Not applicable."
    notes: "Catalog confirms macrofin q-factor tables and CRSP CPI/rates tables. For strict real-time macro work, FRED/ALFRED vintage data may be external."

  - requirement_id: "QPC_P4_GLOBAL_OPTIONS_AND_INDEXES"
    priority: "P4_LONG_TAIL"
    project_need: "Extend pricing research beyond US options into global markets after US evidence is locked."
    quant_use_case: "Cross-market robustness, global index-option validation, and currency/regime comparisons."
    wrds_availability: "likely_wrds"
    wrds_schema: "optionm_europe or global vendor schemas; comp_global; crsp_global variants"
    wrds_table: "needs catalog verification by licensed product"
    wrds_product_or_library: "OptionMetrics Europe or global equity/fundamental products"
    logical_dataset: "Global option, equity, index, and fundamental data"
    required_for_current_reproduction: false
    required_for_current_claim_validation: false
    useful_for_future_expansion: true
    date_range:
      minimum_required: "2018-present after US protocol is stable."
      optimal: "2005-present or full available history by market."
      tier_split: "recent_critical"
    frequency: "daily"
    expected_size_class: "huge"
    partition_strategy: "year"
    key_columns:
      identifiers: ["local security id", "isin", "sedol", "ticker", "exchange", "currency"]
      dates: ["date", "exdate", "effective date"]
      measures: ["option quote fields", "underlying returns", "FX rates", "index levels", "fundamentals"]
    joins:
      required_link_tables: ["global security master", "FX rates", "global fundamentals links"]
      joins_to_project_data: ["future global validation matrix"]
      point_in_time_risks: ["Local calendars, currency conversion, stale quotes, and corporate actions must be market-specific."]
    bias_risks:
      survivorship: "High across global markets."
      lookahead: "High if index membership or identifiers are not date-bounded."
      restatement: "Vendor corrections and fundamental restatements matter."
      delisting: "Global delisting/exit handling is complex."
      corporate_actions: "Very high complexity across currencies and local market rules."
    notes: "Long-tail until US evidence and methodology are mature."

  - requirement_id: "QPC_P4_NEWS_SENTIMENT_AND_ALT_DATA"
    priority: "P4_LONG_TAIL"
    project_need: "Explore event sentiment, news intensity, and alternative data as future features."
    quant_use_case: "News/event sentiment controls, volatility-event prediction, and narrative risk diagnostics."
    wrds_availability: "uncertain_or_external"
    wrds_schema: "ravenpack, truvalue, audit_analytics, boardex, or external vendor schemas"
    wrds_table: "needs catalog and entitlement verification"
    wrds_product_or_library: "News, ESG, governance, audit, or alternative-data products"
    logical_dataset: "News sentiment, ESG/governance, audit events, and text-derived features"
    required_for_current_reproduction: false
    required_for_current_claim_validation: false
    useful_for_future_expansion: true
    date_range:
      minimum_required: "2018-present only after a feature protocol is written."
      optimal: "Full available history with vintage/availability timestamps."
      tier_split: "recent_critical"
    frequency: "event"
    expected_size_class: "huge"
    partition_strategy: "year"
    key_columns:
      identifiers: ["company id", "ticker", "cusip", "isin", "article id", "event id"]
      dates: ["publication timestamp", "event date", "availability timestamp"]
      measures: ["sentiment score", "relevance", "novelty", "event category", "text fields"]
    joins:
      required_link_tables: ["CRSP names", "CCM links", "vendor identifier links"]
      joins_to_project_data: ["future text/event features", "event-exclusion diagnostics"]
      point_in_time_risks: ["Availability timestamp is mandatory; later article corrections or classifications can leak."]
    bias_risks:
      survivorship: "Coverage is vendor- and media-dependent."
      lookahead: "Very high without publication timestamps and archive vintages."
      restatement: "Classifications and sentiment scores may be revised."
      delisting: "Needs dead-firm identity handling."
      corporate_actions: "Company identity changes and mergers affect joins."
    notes: "Useful but not urgent; should not be downloaded until a specific hypothesis and evaluation plan exists."

wrds_catalog_checks_needed:
  - "Verify local row counts, date coverage, file hashes, and extract timestamps for optionm.opprcdYYYY and optionm.secprdYYYY partitions before any live/local WRDS claim is promoted."
  - "Verify whether optionm.opprcd2026 and optionm.secprd2026 are available and entitled before adding current-year holdouts."
  - "Confirm the exact SPX secid and historical name-resolution rule from optionm.secnmd for each current panel date."
  - "Review OptionMetrics zerocd rate conventions and interpolation rules before replacing fallback rate constants."
  - "Review OptionMetrics idxdvd versus index_dividend semantics and availability timestamps before replacing fallback dividend-yield constants."
  - "Confirm distribution/projection table fields and as-of behavior for SPX and equity-option corporate-action handling."
  - "Validate wrdsapps.opcrsphist versus wrdsapps_link_crsp_optionm.opcrsphist preference, link-quality fields, and date-interval semantics."
  - "Reconcile local WRDS P1 vault run failures or partial partitions before treating the shared vault as complete."
  - "Verify whether SEC 13F tables in secsamp or secsamp_all are full entitlement, sample-only, or documentation examples."
  - "Confirm CBOE EOD options, CBOE borrow-rate, TAQ, TRACE, CIQ, IBES, SDC, and securities-finance entitlements before planning heavy downloads."
  - "Check whether strict point-in-time macro vintages are available on WRDS; otherwise use external ALFRED/FRED vintage data and mark as external."

entitlement_questions:
  - "Does the WRDS account have full OptionMetrics IvyDB US including index options, equity options, underlying prices, zero curves, index dividends, and distributions through the desired current year?"
  - "Is CBOE DataShop via WRDS entitled for optprice_YYYY, option contract master, equity prices, historical volatility, and implied borrow-rate tables?"
  - "Are CRSP daily stock, CRSP indexes, CRSP Treasury/risk-free, and CRSP/Compustat Merged link products fully entitled?"
  - "Are Compustat North America annual, quarterly, security, index constituent, and short-interest products entitled?"
  - "Are IBES EPS summary/detail/actuals, recommendations, and price-target datasets entitled?"
  - "Are Capital IQ key developments, identifiers, and transcript tables entitled?"
  - "Are Thomson/Refinitiv 13F, SEC 13F full holdings, FTSE Russell holdings, SDC Platinum, TAQ, TRACE, and Markit Securities Finance available under the current license?"
  - "Is `/Volumes/Storage/Data/WRDS` the authoritative shared vault for future downloads, or should a project-specific restricted vault be declared?"
  - "Can derived aggregate artifacts leave the restricted vault, and what minimum aggregation or suppression rule should be used for option quotes and security-level panels?"

highest_priority_download_order:
  - requirement_id: "QPC_P0_SAMPLE_REPRO_WRDS_SYNTHETIC_PANEL"
    reason: "No WRDS download; first confirm the public-safe reproduction path and current-HEAD regression status."
  - requirement_id: "QPC_P0_OPTIONM_SECURITY_NAMES"
    reason: "Needed to resolve the correct SPX secid and prevent identifier lookahead."
  - requirement_id: "QPC_P0_OPTIONM_SPX_OPTIONS_PANEL"
    reason: "Primary live/local quote evidence for current pricing claims."
  - requirement_id: "QPC_P0_OPTIONM_UNDERLYING_PRICES_PANEL"
    reason: "Required for next-day OOS price and PnL validation."
  - requirement_id: "QPC_P0_OPTIONM_ZERO_CURVE"
    reason: "Removes fallback risk-free-rate constants from public-evidence runs."
  - requirement_id: "QPC_P0_OPTIONM_INDEX_DIVIDENDS"
    reason: "Removes fallback dividend-yield constants and improves SPX forward consistency."
  - requirement_id: "QPC_P0_OPTIONM_DISTRIBUTIONS_ADJUSTMENTS"
    reason: "Protects against corporate-action and special-distribution errors before broader claims."
  - requirement_id: "QPC_P1_OPTIONM_CRSP_LINK"
    reason: "Unlocks point-in-time joins to CRSP for serious equity-option expansion."
  - requirement_id: "QPC_P1_CRSP_DAILY_EQUITY_RETURNS"
    reason: "Core independent underlying return, liquidity, and benchmark dataset."
  - requirement_id: "QPC_P1_CRSP_SECURITY_NAMES_HISTORY"
    reason: "Required to avoid ticker and survivorship errors."
  - requirement_id: "QPC_P1_CRSP_DELISTINGS"
    reason: "Required before any equity universe performance or PnL claim."
  - requirement_id: "QPC_P1_CCM_LINKS"
    reason: "Required before Compustat fundamentals can be joined safely."
  - requirement_id: "QPC_P1_COMPUSTAT_FUNDAMENTALS"
    reason: "Foundational controls and future features for cross-sectional research."
  - requirement_id: "QPC_P1_FAMA_FRENCH_FACTORS"
    reason: "Small, standard, high-value benchmark factor data."
  - requirement_id: "QPC_P2_OPTIONM_FULL_UNDERLYING_UNIVERSE"
    reason: "After the SPX panel is locked, broaden validation without changing the model narrative prematurely."

dedupe_keys_for_global_merge:
  - "wrds_pipeline.sample_data:fixture_name+trade_date+expiry_date+strike+call_put"
  - "optionm.opprcdYYYY:date+secid+optionid"
  - "optionm.secprdYYYY:date+secid"
  - "optionm.secnmd:secid+effect_date"
  - "optionm.optionmnames:secid+optionid+effect_date"
  - "optionm.zerocd:date+days"
  - "optionm.idxdvd:secid+date"
  - "optionm.index_dividend:secid+date"
  - "optionm.distrd:record_date+secid_or_securityid+distribution_identifier"
  - "optionm.distribution:securityid+sequencenumber"
  - "optionm.distribution_projection:securityid+exdate+rundate+amount"
  - "wrdsapps.opcrsphist:secid+permno+sdate+edate"
  - "wrdsapps_link_crsp_optionm.opcrsphist:secid+permno+sdate+edate"
  - "crsp.dsf:permno+date"
  - "crsp.dsf_v2:permno+dlycaldt"
  - "crsp.dsenames:permno+namedt+nameendt"
  - "crsp.stocknames:permno+namedt+nameendt"
  - "crsp.dsedelist:permno+dlstdt"
  - "crsp.dse:permno+date+event_code"
  - "crsp.dsp500list_v2:permno+mbrstartdt+mbrenddt"
  - "crsp.dsi:date"
  - "crsp.ccmxpf_lnkhist:gvkey+lpermno+linkdt+linkenddt+linktype+linkprim"
  - "comp.funda:gvkey+datadate+indfmt+consol+popsrc+datafmt"
  - "comp.fundq:gvkey+datadate+indfmt+consol+popsrc+datafmt"
  - "comp.security:gvkey+iid+datadate_or_effective_date"
  - "comp.indexcst_his:index_id+gvkey+iid+from_date+through_date"
  - "ff.factors_daily:date"
  - "ff.fivefactors_daily:date"
  - "ibes.statsumu_epsus:ticker+cusip+statpers+measure+fpi+fpedats"
  - "ibes.detu_epsus:ticker+cusip+actdats+estimator+analys+measure+fpi+fpedats"
  - "ibes.actu_epsus:ticker+cusip+anndats+measure+fpedats"
  - "ciq.wrds_keydev:companyid+keydevid+announceddate"
  - "ciq.wrds_transcript_detail:transcriptid+componentid_or_sequence"
  - "comp.sec_shortint:gvkey+iid+datadate"
  - "tfn.s34:mgrno+rdate+cusip"
  - "tr_13f.s34:mgrno+rdate+cusip"
  - "secsamp_all.wrds_13f_holdings:accession_number+cusip+report_date"
  - "cboe.optprice_YYYY:trade_date+option_contract_id_or_underlying_expiry_strike_putcall"
  - "cboe.ivborrowrate:date+underlying_symbol_or_security_id"
  - "taqmsec.complete_nbbo_YYYY:date+time+symbol+exchange+sequence_number"
  - "taqm_YYYY.ctm_YYYYMMDD:date+time+symbol+exchange+sequence_number"
  - "taqm_YYYY.cqm_YYYYMMDD:date+time+symbol+exchange+sequence_number"
  - "trace.trace_enhanced:cusip+trd_exctn_dt+trd_exctn_tm+reporting_sequence_or_trade_id"
  - "trace_enhanced.trace_enhanced:cusip+trd_exctn_dt+trd_exctn_tm+reporting_sequence_or_trade_id"
  - "sdc.wrds_ma_details:deal_number_or_transaction_id"
  - "sdc.wrds_ni_details:issue_id_or_deal_number"
```

## Admin Notes

- The project does not need every dataset above to finish the current evidence sprint. It needs the P0 lane clean first.
- The local shared vault appears to have substantial OptionMetrics, CRSP, Compustat, and Fama-French coverage, but local file presence is not the same as claim-ready evidence. Each promoted result still needs command logs, manifests, row-count checks, hash/version checks, and public-safe aggregation.
- The most important near-term architectural decision is to keep raw data extraction, restricted joins, and public aggregate publishing as separate stages. This prevents the repo from accidentally becoming a licensed-data container.
- The optimal long-run data architecture should treat `/Volumes/Storage/Data/WRDS` as the restricted immutable-ish raw/cache layer, a project-specific restricted derived layer for row-level joins, and the repo as a public-safe evidence and source-code layer.
