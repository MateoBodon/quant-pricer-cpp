# Non-WRDS Data Requirements

Analysis timestamp UTC: 2026-07-08T01:10:45Z

This document maps the non-WRDS data needed to reproduce, validate, and extend `quant-pricer-cpp`. It is planning metadata only. No data was downloaded, no credentials were used, and no private/vendor raw data was copied into the repository.

## Human Summary

### Current Non-WRDS Baseline

The current non-WRDS dependency set is mostly local and public-safe:

- Synthetic option-surface fixtures under `data/` and `wrds_pipeline/sample_data/`.
- Frozen scenario grids, tolerances, and date-panel configs under `configs/` and `wrds_pipeline_dates_panel*.yaml`.
- Curated aggregate artifacts under `docs/artifacts/`, including metrics summaries, manifests, benchmark JSON/CSV/PNG outputs, QuantLib parity outputs, and sample WRDS aggregate outputs.
- Historical and current run evidence under `docs/agent_runs/` and `reports/_runs/`.
- Build, CI, package, release, and validation-pack metadata from local commands and GitHub workflows.

These are enough to preserve the current public-safe project state, but they are not enough to prove live market performance. Live market evidence still requires restricted WRDS or non-WRDS vendor/account data plus reviewed aggregation.

### Data Needed To Validate Current Claims

The non-WRDS data that matters immediately is not a new market-data feed. It is evidence data:

- Reproducible synthetic inputs and frozen configs.
- Current build and test logs.
- Current benchmark machine/compiler metadata.
- Current artifact manifests and before/after metrics.
- Release/package validation evidence if package or release claims are promoted.

If those are stale or missing, the project can still be technically strong but public claims remain weaker.

### Public Core Data Worth Adding

The best public/free non-WRDS additions are:

- FRED/ALFRED macro and rate series.
- U.S. Treasury yield/bill curve archives.
- Cboe VIX index history.
- Kenneth French factor files.
- SEC EDGAR submissions and XBRL company facts.
- Exchange calendars/holiday schedules.
- OCC contract adjustment memos and product specifications.
- OpenFIGI identifier mapping.

These datasets are small to medium, useful for rates, regime controls, identifiers, event filters, and benchmark comparisons. They should be versioned with source URLs, retrieval timestamps, hashes, and transformation scripts.

### Private Or Platform Data

Useful but gated data includes:

- GitHub Actions, Codecov, GitHub Releases, PyPI/TestPyPI, and Pages deployment exports for package/release truth.
- Broker/account exports for future execution-cost or real fill diagnostics.
- Direct Cboe DataShop, direct OptionMetrics, Bloomberg, Refinitiv, FactSet, S&P Global, Databento, Polygon, ThetaData, and other private vendor feeds.

These must stay in a private account archive or shared restricted vault. Only public-safe aggregate outputs should enter the repo.

### Storage Rule

Use three layers:

- Repo: synthetic fixtures, config, small public-safe aggregate artifacts, manifests, and documentation.
- Shared vault: public bulk data, licensed vendor data, account exports, raw logs, and row-level derived panels.
- Repo artifacts: only derived aggregates that pass data policy and have manifests.

## Machine-Readable Requirements

```yaml
project:
  name: "quant-pricer-cpp"
  repo_path: "/Volumes/Storage/Projects/quant-pricer-cpp/repo"
  analysis_timestamp_utc: "2026-07-08T01:10:45Z"
  purpose: "Map all non-WRDS data needed to reproduce current project state, validate public claims, preserve account/project truth, and support future option-pricing and quant-finance research without placing private, vendor, or account-level raw data in the repo."
  current_non_wrds_dependency_summary: "Current non-WRDS dependencies are primarily synthetic fixtures, normalized example surfaces, frozen scenario/tolerance configs, curated aggregate artifacts, manifests, run logs, benchmark outputs, CI/release metadata, and package metadata. Public/free data can strengthen rates, macro, regime, calendar, identifier, and benchmark controls. Private/vendor/platform data is useful but gated and should remain outside the repo except as public-safe aggregate evidence."

requirements:
  - requirement_id: "NWRDS_N0_REPO_SYNTHETIC_OPTION_FIXTURES"
    priority: "N0_BLOCKING"
    dataset_name: "Repository synthetic option fixtures"
    source_type: "local_artifact"
    source_owner_or_provider: "quant-pricer-cpp repo"
    source_url_or_location: "/Volumes/Storage/Projects/quant-pricer-cpp/repo/data and /Volumes/Storage/Projects/quant-pricer-cpp/repo/wrds_pipeline/sample_data"
    access_status: "available_now"
    data_policy_status: "safe_public"
    project_need: "Reproduce sample-mode examples, tests, and documentation without external market data."
    quant_use_case: "Synthetic option surfaces for Heston calibration examples, WRDS sample regression, as-of poison tests, and smoke checks."
    required_for_current_reproduction: true
    required_for_current_claim_validation: true
    useful_for_future_expansion: false
    date_range:
      minimum_required: "Committed fixture dates only: synthetic 2023-06-01, 2024-06-14, and WRDS sample panel dates."
      optimal: "Deterministic synthetic calm, stress, holiday-gap, low-liquidity, bad-row, and boundary-condition fixtures."
    frequency: "daily"
    expected_size_class: "tiny"
    refresh_cadence: "ad_hoc"
    storage_target: "project repo: data/, data/samples/, data/normalized/, wrds_pipeline/sample_data/"
    safe_to_commit_to_repo: true
    required_user_action: "None unless new fixtures are generated."
    acquisition_method: "Generated by repo scripts or manually curated as synthetic fixtures with clear markers."
    validation_method: "Run data-policy guard, sample pipeline tests, as-of poison tests, and YAML/CSV schema checks."
    joins_to_wrds_or_project_data: ["wrds_pipeline_dates_panel.yaml", "scripts/data/schema.md", "wrds_pipeline/pipeline.py", "scripts/calibrate_heston.py"]
    bias_or_leakage_risks: ["Must remain labeled synthetic", "Cannot be used as live-market proof", "Fixture tuning after seeing target metrics would bias validation"]
    notes: "Files in wrds_pipeline/sample_data require the # SYNTHETIC_DATA marker because the data-policy guard treats WRDS-like columns as restricted unless explicitly synthetic."

  - requirement_id: "NWRDS_N0_NORMALIZED_OPTION_SURFACE_SCHEMA"
    priority: "N0_BLOCKING"
    dataset_name: "Normalized option surface CSV schema and example surfaces"
    source_type: "derived_dataset"
    source_owner_or_provider: "quant-pricer-cpp repo"
    source_url_or_location: "/Volumes/Storage/Projects/quant-pricer-cpp/repo/scripts/data/schema.md; /Volumes/Storage/Projects/quant-pricer-cpp/repo/data/normalized"
    access_status: "available_now"
    data_policy_status: "derived_safe_if_aggregated"
    project_need: "Provide the canonical non-WRDS input format for Heston calibration and future Cboe/vendor adapters."
    quant_use_case: "Single-day option-surface calibration, model-fit diagnostics, and public-safe example workflows."
    required_for_current_reproduction: true
    required_for_current_claim_validation: true
    useful_for_future_expansion: true
    date_range:
      minimum_required: "Current committed example surfaces."
      optimal: "Versioned schema fixtures for SPX, SPY, single-name equity, index, rates, dividends, and bad-input cases."
    frequency: "daily"
    expected_size_class: "tiny"
    refresh_cadence: "ad_hoc"
    storage_target: "project repo for synthetic or sanitized examples; shared vault for raw/vendor-derived row-level surfaces"
    safe_to_commit_to_repo: true
    required_user_action: "Approve any real-vendor-derived normalized surface before it is committed."
    acquisition_method: "Generated by scripts/data/cboe_csv.py or future adapters from raw exports outside the repo."
    validation_method: "Schema validation for date, ttm_years, strike, mid_iv, put_call, spot, r, q, bid, ask; data-policy guard; calibration smoke tests."
    joins_to_wrds_or_project_data: ["scripts/calibrate_heston.py", "scripts/calibrate_heston_series.py", "data/README.md"]
    bias_or_leakage_risks: ["Normalized row-level surfaces derived from real vendor data may still be licensed", "Default r/q values can weaken pricing claims", "Raw bid/ask rows should not be public unless synthetic or licensed for redistribution"]
    notes: "The schema is reusable for Cboe, broker, or vendor exports, but raw exports belong outside the repo."

  - requirement_id: "NWRDS_N0_FROZEN_VALIDATION_PROTOCOL_CONFIGS"
    priority: "N0_BLOCKING"
    dataset_name: "Frozen synthetic validation grids, tolerances, and date panels"
    source_type: "local_artifact"
    source_owner_or_provider: "quant-pricer-cpp repo"
    source_url_or_location: "/Volumes/Storage/Projects/quant-pricer-cpp/repo/configs and /Volumes/Storage/Projects/quant-pricer-cpp/repo/wrds_pipeline_dates_panel*.yaml"
    access_status: "available_now"
    data_policy_status: "safe_public"
    project_need: "Prevent validation drift and preserve pre-registered scenarios for public claims."
    quant_use_case: "Tri-engine agreement, PDE order, Greeks confidence intervals, QuantLib parity, sample WRDS panel selection, and tolerance gates."
    required_for_current_reproduction: true
    required_for_current_claim_validation: true
    useful_for_future_expansion: true
    date_range:
      minimum_required: "Current committed config versions."
      optimal: "Versioned calm/stress/holdout panels with frozen hashes and migration notes."
    frequency: "mixed"
    expected_size_class: "tiny"
    refresh_cadence: "ad_hoc"
    storage_target: "project repo: configs/ and root panel YAML files"
    safe_to_commit_to_repo: true
    required_user_action: "None for current configs; Heavy/Pro review before scenario or tolerance changes used in claims."
    acquisition_method: "Repo-authored config files."
    validation_method: "Manifest hashes, reproduce_all, FAST tests, and metrics snapshot consistency checks."
    joins_to_wrds_or_project_data: ["docs/artifacts/manifest.json", "scripts/reproduce_all.sh", "project_state/CLAIMS_AND_EVIDENCE.md"]
    bias_or_leakage_risks: ["Changing panels after seeing results creates lookahead", "Relaxing tolerances after failures weakens evidence", "Multiple panel configs can create protocol ambiguity"]
    notes: "This is data in the scientific-protocol sense and is blocking for evidence credibility."

  - requirement_id: "NWRDS_N0_CURATED_ARTIFACTS_MANIFEST_METRICS"
    priority: "N0_BLOCKING"
    dataset_name: "Curated artifact manifest and metrics snapshot"
    source_type: "local_artifact"
    source_owner_or_provider: "quant-pricer-cpp repo"
    source_url_or_location: "/Volumes/Storage/Projects/quant-pricer-cpp/repo/docs/artifacts"
    access_status: "available_now"
    data_policy_status: "derived_safe_if_aggregated"
    project_need: "Support every public numerical claim with a manifest, artifact file, command, and snapshot timestamp."
    quant_use_case: "Validation evidence for tri-engine agreement, QMC/PRNG, PDE order, QuantLib parity, Heston QE, benchmarks, and sample WRDS aggregates."
    required_for_current_reproduction: true
    required_for_current_claim_validation: true
    useful_for_future_expansion: true
    date_range:
      minimum_required: "Committed snapshot generated 2026-01-25 plus current run reports."
      optimal: "Current-HEAD regenerated snapshots with before/after diff for every promoted artifact."
    frequency: "mixed"
    expected_size_class: "small"
    refresh_cadence: "ad_hoc"
    storage_target: "project repo: docs/artifacts/"
    safe_to_commit_to_repo: true
    required_user_action: "Review before promoting regenerated metrics that change public claims."
    acquisition_method: "Generated by scripts/reproduce_all.sh and artifact helper scripts."
    validation_method: "YAML/JSON parsing, data-policy guard, metrics snapshot tests, manifest diff, and claim audit."
    joins_to_wrds_or_project_data: ["project_state/CLAIMS_AND_EVIDENCE.md", "docs/Results.md", "docs/ValidationHighlights.md", "README.md"]
    bias_or_leakage_risks: ["Historical snapshot may be stale versus current HEAD", "Sample WRDS aggregates can be mistaken for live evidence", "Hardware-specific benchmark numbers can be overgeneralized"]
    notes: "Current artifact truth is historical until sample reproduction is repaired and promoted consistently."

  - requirement_id: "NWRDS_N0_REVIEW_RUN_LOGS_AND_BUNDLES"
    priority: "N0_BLOCKING"
    dataset_name: "Run logs, review bundles, and project-state evidence"
    source_type: "local_artifact"
    source_owner_or_provider: "quant-pricer-cpp repo"
    source_url_or_location: "/Volumes/Storage/Projects/quant-pricer-cpp/repo/reports and /Volumes/Storage/Projects/quant-pricer-cpp/repo/docs/agent_runs"
    access_status: "available_now"
    data_policy_status: "derived_safe_if_aggregated"
    project_need: "Preserve command history, validation outcomes, failed reproduction evidence, and reviewable state transitions."
    quant_use_case: "Evidence recovery, audit trails, reproducibility review, and public-claim governance."
    required_for_current_reproduction: false
    required_for_current_claim_validation: true
    useful_for_future_expansion: true
    date_range:
      minimum_required: "T-000 and T-001/T-101 run reports plus historical agent runs referenced by current docs."
      optimal: "Every evidence-changing ticket has COMMANDS, RESULTS, VALIDATION, diffs, and policy outputs."
    frequency: "event"
    expected_size_class: "medium"
    refresh_cadence: "ad_hoc"
    storage_target: "project repo for compact reports; external/private archive for bulky logs"
    safe_to_commit_to_repo: true
    required_user_action: "None unless a bundle includes private data or secrets."
    acquisition_method: "Generated by tools/agentic/ai_os_bundle.py or manual run-log creation."
    validation_method: "Inspect bundle manifest, data-policy output, git status, and excluded-file notes."
    joins_to_wrds_or_project_data: ["project_state/STATE_INDEX.md", "project_state/VALIDATION_MATRIX.md", "project_state/CLAIMS_AND_EVIDENCE.md"]
    bias_or_leakage_risks: ["Logs can accidentally include credentials or restricted paths", "Partial runs can be misread as passes", "Old archived docs can be mistaken for current truth"]
    notes: "These are project/account truth artifacts, not market data."

  - requirement_id: "NWRDS_N0_BUILD_BENCHMARK_ENVIRONMENT_METADATA"
    priority: "N0_BLOCKING"
    dataset_name: "Build, benchmark, compiler, and hardware metadata"
    source_type: "derived_dataset"
    source_owner_or_provider: "local machine, GitHub Actions, benchmark executables"
    source_url_or_location: "docs/artifacts/manifest.json; docs/artifacts/bench; build logs; GitHub Actions artifacts"
    access_status: "available_now"
    data_policy_status: "safe_public"
    project_need: "Make performance claims reviewable and machine-specific."
    quant_use_case: "Benchmark reproducibility, paths/sec comparisons, OpenMP scaling, compiler flag attribution, and performance regression diagnosis."
    required_for_current_reproduction: false
    required_for_current_claim_validation: true
    useful_for_future_expansion: true
    date_range:
      minimum_required: "For every benchmark snapshot cited publicly."
      optimal: "Per-run hardware, OS, compiler, flags, CPU governor, thread count, seed, workload, and benchmark version."
    frequency: "event"
    expected_size_class: "small"
    refresh_cadence: "ad_hoc"
    storage_target: "project repo for aggregate benchmark artifacts; private archive for full CI logs if bulky"
    safe_to_commit_to_repo: true
    required_user_action: "Provide machine label and approval before using local/server benchmark numbers publicly."
    acquisition_method: "Generated by CMake, Google Benchmark JSON, scripts/generate_bench_artifacts.py, sysctl/lscpu equivalents, and CI logs."
    validation_method: "Compare manifest metadata, rerun benchmark target, verify repeat count/min time/thread settings, and check hardware/compiler fields."
    joins_to_wrds_or_project_data: ["docs/artifacts/bench/bench_mc.json", "docs/artifacts/bench/bench_pde.json", "docs/artifacts/metrics_summary.json"]
    bias_or_leakage_risks: ["Benchmark cherry-picking", "Comparing different hardware as if identical", "Thermal or CI variability", "Stale benchmark snapshots"]
    notes: "Required before strengthening prestige/performance claims."

  - requirement_id: "NWRDS_N0_VALIDATION_PACK_AND_RELEASE_ASSETS"
    priority: "N0_BLOCKING"
    dataset_name: "Validation pack and GitHub release evidence"
    source_type: "platform_export"
    source_owner_or_provider: "GitHub Releases and local packaging scripts"
    source_url_or_location: "https://github.com/MateoBodon/quant-pricer-cpp/releases; docs/validation_pack.zip"
    access_status: "needs_user_export"
    data_policy_status: "derived_safe_if_aggregated"
    project_need: "Verify release-pack and artifact-availability claims before public promotion."
    quant_use_case: "Reviewer bundle for artifact diffs, release evidence, and reproducibility packets."
    required_for_current_reproduction: false
    required_for_current_claim_validation: true
    useful_for_future_expansion: true
    date_range:
      minimum_required: "Current release/tag or current local validation-pack build."
      optimal: "Every public release has matching tag, manifest, validation_pack.zip, checksums, and release notes."
    frequency: "event"
    expected_size_class: "small"
    refresh_cadence: "ad_hoc"
    storage_target: "project repo for generated validation_pack.zip when intentionally promoted; GitHub release assets for published packs"
    safe_to_commit_to_repo: true
    required_user_action: "Confirm release asset availability or authorize a release-pack verification run."
    acquisition_method: "Run scripts/package_validation.py locally and inspect/export GitHub release assets."
    validation_method: "Unzip, list files, compare manifest SHA, run data-policy guard, and verify release asset hashes."
    joins_to_wrds_or_project_data: ["docs/artifacts/manifest.json", "docs/artifacts/metrics_summary.md", ".github/workflows/release.yml"]
    bias_or_leakage_risks: ["Validation pack can include stale artifacts", "Release asset can diverge from tagged source", "Bundle must exclude raw WRDS/vendor data"]
    notes: "T-001/T-101 marked release-pack availability as not checked."

  - requirement_id: "NWRDS_N0_PACKAGE_REGISTRY_AND_INSTALL_EVIDENCE"
    priority: "N0_BLOCKING"
    dataset_name: "PyPI/TestPyPI/GitHub package install evidence"
    source_type: "platform_export"
    source_owner_or_provider: "PyPI, TestPyPI, GitHub Actions, cibuildwheel"
    source_url_or_location: "https://pypi.org/project/pyquant-pricer/; https://test.pypi.org/project/pyquant-pricer/; .github/workflows/wheels.yml"
    access_status: "needs_user_export"
    data_policy_status: "safe_public"
    project_need: "Validate package/install claims before README, release, or portfolio promotion."
    quant_use_case: "Installability smoke tests, wheel matrix evidence, package metadata verification, and downstream consumer examples."
    required_for_current_reproduction: false
    required_for_current_claim_validation: true
    useful_for_future_expansion: true
    date_range:
      minimum_required: "Current package version 0.3.2 metadata and latest wheel build logs if public claims mention installability."
      optimal: "Per-release PyPI/TestPyPI metadata, wheel hashes, install smoke logs, and consumer CMake/Python examples."
    frequency: "event"
    expected_size_class: "small"
    refresh_cadence: "ad_hoc"
    storage_target: "project repo for smoke-test logs and docs; platform for registry metadata; private archive for token-bearing CI logs"
    safe_to_commit_to_repo: true
    required_user_action: "Provide/export platform status if registry access or CI secrets are needed; do not expose tokens."
    acquisition_method: "Use public package pages, GitHub Actions artifacts, local pip install smoke tests, and cibuildwheel logs."
    validation_method: "Fresh venv install, import/smoke test, wheel metadata inspection, version consistency check, and token-free CI log review."
    joins_to_wrds_or_project_data: ["pyproject.toml", "setup.cfg", ".github/workflows/wheels.yml", "README.md"]
    bias_or_leakage_risks: ["Confusing TestPyPI with PyPI", "Claiming package availability without live install evidence", "CI logs can expose secret names or accidental tokens"]
    notes: "Package/install claims were not verified in the prior audit and should stay caveated until tested."

  - requirement_id: "NWRDS_N1_FRED_ALFRED_MACRO_RATES"
    priority: "N1_PUBLIC_CORE"
    dataset_name: "FRED and ALFRED macro, rates, and volatility series"
    source_type: "public_api"
    source_owner_or_provider: "Federal Reserve Bank of St. Louis"
    source_url_or_location: "https://fred.stlouisfed.org/docs/api/fred/"
    access_status: "needs_credentials"
    data_policy_status: "safe_public"
    project_need: "Add public macro/rate/regime controls and independently verifiable benchmark series."
    quant_use_case: "Risk-free rates, yield curve proxies, SOFR, CPI, recession/regime variables, VIX via FRED, and macro stress controls."
    required_for_current_reproduction: false
    required_for_current_claim_validation: false
    useful_for_future_expansion: true
    date_range:
      minimum_required: "2005-present for OptionMetrics-era research."
      optimal: "Full available history plus ALFRED vintages when point-in-time macro features matter."
    frequency: "daily"
    expected_size_class: "small"
    refresh_cadence: "daily"
    storage_target: "shared vault: /Volumes/Storage/Data/Public/fred; repo only for small derived summaries and source manifests"
    safe_to_commit_to_repo: true
    required_user_action: "Provide a FRED API key only if API acquisition is needed; do not place it in repo files."
    acquisition_method: "FRED API observations endpoint or manual CSV download; ALFRED for vintage-aware macro data."
    validation_method: "Record series IDs, retrieval timestamp, frequency, units, transformation, source URL, and hash; compare key series to official page."
    joins_to_wrds_or_project_data: ["calendar date", "wrds_pipeline_dates_panel.yaml", "future macro regime labels"]
    bias_or_leakage_risks: ["Final revised macro data can leak", "Series transformations can change units", "API key must not be logged"]
    notes: "FRED API documentation says it can retrieve observations and full series histories; use ALFRED vintages for ex-ante macro claims."

  - requirement_id: "NWRDS_N1_US_TREASURY_CURVES"
    priority: "N1_PUBLIC_CORE"
    dataset_name: "U.S. Treasury daily yield, bill, and real yield curves"
    source_type: "public_bulk_download"
    source_owner_or_provider: "U.S. Department of the Treasury"
    source_url_or_location: "https://home.treasury.gov/resource-center/data-chart-center/interest-rates/daily-treasury-rate-archives"
    access_status: "available_now"
    data_policy_status: "safe_public"
    project_need: "Provide transparent public rate curves for examples and independent checks of pricing inputs."
    quant_use_case: "Discount curve sanity checks, rate interpolation tests, scenario examples, and public demonstration curves."
    required_for_current_reproduction: false
    required_for_current_claim_validation: false
    useful_for_future_expansion: true
    date_range:
      minimum_required: "2005-present for current project-era examples."
      optimal: "Full Treasury archive history by curve type."
    frequency: "daily"
    expected_size_class: "small"
    refresh_cadence: "monthly"
    storage_target: "shared vault: /Volumes/Storage/Data/Public/treasury; repo only for tiny fixtures or aggregate examples"
    safe_to_commit_to_repo: true
    required_user_action: "None for public download; review terms before bulk mirroring."
    acquisition_method: "Official Treasury CSV/XML archive download."
    validation_method: "Hash archives, validate date monotonicity and tenor columns, compare recent rows to Treasury page, and record units."
    joins_to_wrds_or_project_data: ["calendar date", "option maturity tenor", "pricing input builders"]
    bias_or_leakage_risks: ["Using par yields as zero rates without conversion", "Calendar mismatch", "Future revised archives can change historical rows"]
    notes: "Useful even if WRDS/OptionMetrics zero curves are the source of truth for live claim validation."

  - requirement_id: "NWRDS_N1_CBOE_VIX_HISTORY"
    priority: "N1_PUBLIC_CORE"
    dataset_name: "Cboe VIX and volatility index history"
    source_type: "public_bulk_download"
    source_owner_or_provider: "Cboe"
    source_url_or_location: "https://www.cboe.com/tradable_products/vix/vix_historical_data/"
    access_status: "available_now"
    data_policy_status: "safe_public"
    project_need: "Add public volatility regime labels and sanity checks for SPX option panels."
    quant_use_case: "Stress/calm labeling, vol-regime controls, VIX versus fitted-implied-vol diagnostics, and public examples."
    required_for_current_reproduction: false
    required_for_current_claim_validation: false
    useful_for_future_expansion: true
    date_range:
      minimum_required: "1990-present for VIX; 2005-present for matching option panels."
      optimal: "All available Cboe volatility index histories relevant to SPX/SPY."
    frequency: "daily"
    expected_size_class: "small"
    refresh_cadence: "daily"
    storage_target: "shared vault: /Volumes/Storage/Data/Public/cboe_vix; repo only for source manifest and small derived regime labels"
    safe_to_commit_to_repo: true
    required_user_action: "None for public VIX history."
    acquisition_method: "Official Cboe historical data CSV download."
    validation_method: "Hash CSV, check date coverage, compare to FRED VIXCLS spot checks, and record update date."
    joins_to_wrds_or_project_data: ["wrds_pipeline_dates_panel.yaml", "calendar date", "future regime labels"]
    bias_or_leakage_risks: ["Regime labels selected after model results can bias comparisons", "VIX close timing may not align with option quote timing"]
    notes: "Cboe publishes VIX daily closing history; FRED also exposes VIXCLS as an alternative public source."

  - requirement_id: "NWRDS_N1_KENNETH_FRENCH_FACTORS"
    priority: "N1_PUBLIC_CORE"
    dataset_name: "Kenneth French research factors and portfolios"
    source_type: "public_bulk_download"
    source_owner_or_provider: "Kenneth R. French Data Library"
    source_url_or_location: "https://mba.tuck.dartmouth.edu/pages/faculty/ken.french/data_library.html"
    access_status: "available_now"
    data_policy_status: "safe_public"
    project_need: "Provide standard public factor benchmarks without relying on WRDS."
    quant_use_case: "Market, size, value, profitability, investment, momentum, industry, and portfolio benchmark attribution."
    required_for_current_reproduction: false
    required_for_current_claim_validation: false
    useful_for_future_expansion: true
    date_range:
      minimum_required: "2005-present daily and monthly factors."
      optimal: "Full available current and historical archives with version timestamps."
    frequency: "daily"
    expected_size_class: "small"
    refresh_cadence: "monthly"
    storage_target: "shared vault: /Volumes/Storage/Data/Public/kenneth_french; repo only for manifests and small derived summaries"
    safe_to_commit_to_repo: true
    required_user_action: "None."
    acquisition_method: "Official Data Library CSV/TXT downloads."
    validation_method: "Hash downloads, parse footers carefully, verify date ranges, record archive/current vintage, and compare against WRDS FF if available."
    joins_to_wrds_or_project_data: ["calendar date", "future benchmark attribution"]
    bias_or_leakage_risks: ["Factors can be revised", "Monthly factors cannot be treated as known before month end", "Portfolio construction methodology changes can affect history"]
    notes: "The Data Library provides current and historical benchmark return files, including daily factor files."

  - requirement_id: "NWRDS_N1_SEC_EDGAR_COMPANY_FACTS_FILINGS"
    priority: "N1_PUBLIC_CORE"
    dataset_name: "SEC EDGAR submissions, company facts, and filing metadata"
    source_type: "public_api"
    source_owner_or_provider: "U.S. Securities and Exchange Commission"
    source_url_or_location: "https://www.sec.gov/search-filings/edgar-application-programming-interfaces"
    access_status: "available_now"
    data_policy_status: "safe_public"
    project_need: "Provide public fundamentals, filing-event timestamps, issuer identifiers, and corporate-event evidence outside WRDS."
    quant_use_case: "Earnings/10-Q/10-K event controls, filing lag checks, public-company fundamentals, restatement/event filters, and issuer mapping."
    required_for_current_reproduction: false
    required_for_current_claim_validation: false
    useful_for_future_expansion: true
    date_range:
      minimum_required: "2009-present for XBRL company facts; filing metadata as available."
      optimal: "Full EDGAR history with accession-level manifests."
    frequency: "event"
    expected_size_class: "large"
    refresh_cadence: "daily"
    storage_target: "shared vault: /Volumes/Storage/Data/Public/sec_edgar; repo only for derived aggregate event calendars"
    safe_to_commit_to_repo: true
    required_user_action: "None, but set a compliant User-Agent in acquisition scripts."
    acquisition_method: "SEC data.sec.gov submissions and companyfacts APIs; bulk archives when appropriate."
    validation_method: "Record CIK, accession, filing date, accepted timestamp, form type, taxonomy, units, and source URL; obey SEC rate/fair-access guidance."
    joins_to_wrds_or_project_data: ["CIK to ticker/CUSIP/FIGI mapping", "future CRSP/Compustat links", "event calendar"]
    bias_or_leakage_risks: ["Using filing period end date instead of accepted timestamp creates lookahead", "Restated company facts can revise history", "Ticker changes require identifier mapping"]
    notes: "SEC APIs expose company submissions and extracted XBRL data in JSON."

  - requirement_id: "NWRDS_N1_EXCHANGE_TRADING_CALENDARS"
    priority: "N1_PUBLIC_CORE"
    dataset_name: "Exchange trading calendars, holidays, and early closes"
    source_type: "public_bulk_download"
    source_owner_or_provider: "Nasdaq Trader, NYSE, Cboe, OCC, pandas-market-calendars"
    source_url_or_location: "https://www.nasdaqtrader.com/trader.aspx?id=calendar"
    access_status: "available_now"
    data_policy_status: "safe_public"
    project_need: "Make next-trading-day logic, holiday gaps, and OOS date selection explicit."
    quant_use_case: "Trading-day calendars for option quote dates, next-day OOS evaluation, benchmark return alignment, and early-close controls."
    required_for_current_reproduction: false
    required_for_current_claim_validation: false
    useful_for_future_expansion: true
    date_range:
      minimum_required: "2005-present for modern option panels."
      optimal: "Full available exchange holiday/early-close history and future calendars used by tests."
    frequency: "event"
    expected_size_class: "tiny"
    refresh_cadence: "annual"
    storage_target: "project repo for small versioned calendar fixtures; shared vault for downloaded raw calendars"
    safe_to_commit_to_repo: true
    required_user_action: "None."
    acquisition_method: "Official exchange calendar pages, public packages, or manually curated calendar fixture with source citations."
    validation_method: "Cross-check next_trade_date fields, early closes, Good Friday and US holiday edge cases, and calendar package version."
    joins_to_wrds_or_project_data: ["wrds_pipeline_dates_panel.yaml", "wrds_pipeline_dates_panel_resume_v2.yaml", "OOS pricing date logic"]
    bias_or_leakage_risks: ["Incorrect holiday handling can create false OOS joins", "Future calendar files should not retroactively change historical panels without review"]
    notes: "Nasdaq Trader publishes US equity/options market holiday schedules; early-close handling still needs explicit tests."

  - requirement_id: "NWRDS_N1_OCC_CONTRACT_ADJUSTMENT_MEMOS"
    priority: "N1_PUBLIC_CORE"
    dataset_name: "OCC information memos and option product specifications"
    source_type: "public_bulk_download"
    source_owner_or_provider: "Options Clearing Corporation"
    source_url_or_location: "https://infomemo.theocc.com/infomemo/search"
    access_status: "available_now"
    data_policy_status: "safe_public"
    project_need: "Provide public evidence for option contract adjustments and deliverable changes outside vendor corporate-action feeds."
    quant_use_case: "Adjusted-contract diagnostics, special dividend/split/merger handling, and corporate-action validation."
    required_for_current_reproduction: false
    required_for_current_claim_validation: false
    useful_for_future_expansion: true
    date_range:
      minimum_required: "Events overlapping any equity-option research period."
      optimal: "Full searchable memo archive with symbol/event metadata."
    frequency: "event"
    expected_size_class: "medium"
    refresh_cadence: "weekly"
    storage_target: "shared vault: /Volumes/Storage/Data/Public/occ_memos; repo only for memo IDs and derived adjustment test cases"
    safe_to_commit_to_repo: true
    required_user_action: "None for public memos; review terms before bulk mirroring PDFs."
    acquisition_method: "Manual export or scripted metadata fetch from OCC memo search if permitted."
    validation_method: "Record memo number, posted date, effective date, symbols, deliverables, and source URL; compare against vendor adjustment fields."
    joins_to_wrds_or_project_data: ["option contract symbol", "underlying ticker", "corporate action event dates"]
    bias_or_leakage_risks: ["Not every ordinary dividend has an adjustment memo", "Using memo posted after trade date as ex-ante data can leak", "Parsing PDFs can introduce errors"]
    notes: "OCC memos are especially useful for explaining adjusted option contracts in public-safe terms."

  - requirement_id: "NWRDS_N1_OPENFIGI_IDENTIFIER_MAPPING"
    priority: "N1_PUBLIC_CORE"
    dataset_name: "OpenFIGI identifier mapping"
    source_type: "public_api"
    source_owner_or_provider: "Bloomberg OpenFIGI"
    source_url_or_location: "https://www.openfigi.com/api/documentation"
    access_status: "available_now"
    data_policy_status: "safe_public"
    project_need: "Support public identifier mapping across tickers, CUSIPs, FIGIs, exchanges, and vendor exports."
    quant_use_case: "Cross-source joins for SEC, public prices, vendor exports, broker logs, and future non-WRDS panels."
    required_for_current_reproduction: false
    required_for_current_claim_validation: false
    useful_for_future_expansion: true
    date_range:
      minimum_required: "Current and historical identifiers used by non-WRDS datasets."
      optimal: "Versioned mapping snapshots for every symbol in project panels."
    frequency: "static"
    expected_size_class: "medium"
    refresh_cadence: "monthly"
    storage_target: "shared vault: /Volumes/Storage/Data/Public/openfigi; repo only for small mapping fixtures"
    safe_to_commit_to_repo: true
    required_user_action: "Optional API key for higher rate limits; do not commit it."
    acquisition_method: "OpenFIGI API batch mapping from known identifiers."
    validation_method: "Record request payload, FIGI response, exchange/composite fields, timestamp, and unresolved mappings."
    joins_to_wrds_or_project_data: ["ticker", "CUSIP", "ISIN", "CIK", "vendor symbols", "broker symbols"]
    bias_or_leakage_risks: ["Current mappings may not be point-in-time", "Ambiguous tickers require exchange filters", "API rate limits affect reproducibility"]
    notes: "OpenFIGI documentation states unauthenticated access is free but lower rate-limited."

  - requirement_id: "NWRDS_N1_PUBLIC_INDEX_ETF_HOLDINGS_DISTRIBUTIONS"
    priority: "N1_PUBLIC_CORE"
    dataset_name: "Public ETF holdings, distributions, and index proxy metadata"
    source_type: "public_bulk_download"
    source_owner_or_provider: "ETF issuers and index/issuer public websites"
    source_url_or_location: "Provider pages for SPY, IVV, VOO, QQQ, sector ETFs, and public distribution histories"
    access_status: "available_now"
    data_policy_status: "safe_public"
    project_need: "Provide public proxy data for dividends, constituents, weights, and index/ETF sanity checks when WRDS/vendor data is gated."
    quant_use_case: "ETF dividend-yield examples, constituent proxy checks, sector benchmark controls, and public demos."
    required_for_current_reproduction: false
    required_for_current_claim_validation: false
    useful_for_future_expansion: true
    date_range:
      minimum_required: "2018-present for recent public examples."
      optimal: "Full issuer-published histories with archive snapshots."
    frequency: "daily"
    expected_size_class: "medium"
    refresh_cadence: "monthly"
    storage_target: "shared vault: /Volumes/Storage/Data/Public/etf_issuer; repo only for small derived summary fixtures"
    safe_to_commit_to_repo: false
    required_user_action: "Review provider terms before storing or redistributing holdings files."
    acquisition_method: "Manual download or documented public file fetch from issuer pages."
    validation_method: "Hash files, record provider, as-of date, ticker, shares/weights, cash rows, and distribution dates."
    joins_to_wrds_or_project_data: ["ticker", "calendar date", "future benchmark/index proxy datasets"]
    bias_or_leakage_risks: ["Holdings publication timing can lag", "ETF proxy does not equal index truth", "Provider terms can limit redistribution"]
    notes: "Useful for public demos, not a replacement for reviewed index constituent data."

  - requirement_id: "NWRDS_N1_PUBLIC_EQUITY_PRICE_EXAMPLES"
    priority: "N1_PUBLIC_CORE"
    dataset_name: "Public OHLCV equity/index price examples"
    source_type: "public_api"
    source_owner_or_provider: "Stooq, Nasdaq public pages, Yahoo Finance, or equivalent public sources"
    source_url_or_location: "Provider-specific public endpoints; verify terms before use"
    access_status: "available_now"
    data_policy_status: "safe_public"
    project_need: "Support public examples and smoke tests when WRDS or broker data is unavailable."
    quant_use_case: "Underlying price paths, simple realized volatility examples, demo returns, and sanity checks."
    required_for_current_reproduction: false
    required_for_current_claim_validation: false
    useful_for_future_expansion: true
    date_range:
      minimum_required: "Small example windows only."
      optimal: "2005-present for selected public demo tickers if provider terms allow."
    frequency: "daily"
    expected_size_class: "medium"
    refresh_cadence: "monthly"
    storage_target: "shared vault: /Volumes/Storage/Data/Public/equity_prices; repo only for tiny synthetic or permissively licensed fixtures"
    safe_to_commit_to_repo: false
    required_user_action: "Approve provider and license before committing any downloaded raw prices."
    acquisition_method: "Public CSV/API download with source manifest, not scraped ad hoc into repo."
    validation_method: "Record provider, URL, retrieval timestamp, adjusted/unadjusted flag, split/dividend adjustment policy, and hash."
    joins_to_wrds_or_project_data: ["ticker", "calendar date", "data/spy_returns.csv"]
    bias_or_leakage_risks: ["Free provider adjustments can change silently", "Terms may forbid redistribution", "Ticker survivorship and adjusted-close semantics vary"]
    notes: "Good for demos; not sufficient for institutional equity-option claims."

  - requirement_id: "NWRDS_N1_NBER_EPU_REGIME_LABELS"
    priority: "N1_PUBLIC_CORE"
    dataset_name: "NBER recession dates and economic policy uncertainty/regime labels"
    source_type: "public_bulk_download"
    source_owner_or_provider: "NBER, policyuncertainty.com, public academic providers"
    source_url_or_location: "Official NBER recession page and Economic Policy Uncertainty public downloads"
    access_status: "available_now"
    data_policy_status: "safe_public"
    project_need: "Add transparent regime labels for stress/calm validation panels."
    quant_use_case: "Macro regime stratification, crisis labels, event-window interpretation, and robustness tables."
    required_for_current_reproduction: false
    required_for_current_claim_validation: false
    useful_for_future_expansion: true
    date_range:
      minimum_required: "2005-present."
      optimal: "Full available history."
    frequency: "monthly"
    expected_size_class: "tiny"
    refresh_cadence: "quarterly"
    storage_target: "shared vault: /Volumes/Storage/Data/Public/regime_labels; repo only for derived small labels and source manifests"
    safe_to_commit_to_repo: true
    required_user_action: "None."
    acquisition_method: "Manual/public CSV download with citations."
    validation_method: "Record source, vintage, date definitions, and transformation to daily labels."
    joins_to_wrds_or_project_data: ["calendar date", "wrds_pipeline_dates_panel.yaml", "future holdout panels"]
    bias_or_leakage_risks: ["NBER recession labels are known with delay", "Regime labels chosen after results can bias narratives", "Monthly series cannot be used as same-day signals without lagging"]
    notes: "Useful for public narrative and holdout stratification, but not current reproduction."

  - requirement_id: "NWRDS_N2_GITHUB_ACTIONS_CI_ARTIFACTS"
    priority: "N2_PLATFORM_EXPORTS"
    dataset_name: "GitHub Actions logs, artifacts, and status checks"
    source_type: "platform_export"
    source_owner_or_provider: "GitHub"
    source_url_or_location: "https://github.com/MateoBodon/quant-pricer-cpp/actions"
    access_status: "needs_user_export"
    data_policy_status: "private_account_data"
    project_need: "Validate CI, release, docs, wheels, coverage, and cross-platform package claims."
    quant_use_case: "Build matrix evidence, sanitizer logs, coverage artifacts, Doxygen/Page deployments, release reproducibility, and wheel validation."
    required_for_current_reproduction: false
    required_for_current_claim_validation: true
    useful_for_future_expansion: true
    date_range:
      minimum_required: "Latest relevant workflow runs for claims being promoted."
      optimal: "Per-release run artifacts, logs, job summaries, commit SHA, and workflow version."
    frequency: "event"
    expected_size_class: "medium"
    refresh_cadence: "ad_hoc"
    storage_target: "private account archive for raw logs; repo for summarized token-free validation evidence"
    safe_to_commit_to_repo: false
    required_user_action: "Export logs/artifacts or grant connector access if account-private data is required."
    acquisition_method: "GitHub UI/API export; no secrets copied into repo."
    validation_method: "Check workflow name, commit SHA, job status, artifact hashes, OS matrix, and absence of secret values."
    joins_to_wrds_or_project_data: [".github/workflows/ci.yml", ".github/workflows/release.yml", ".github/workflows/wheels.yml", "project_state/VALIDATION_MATRIX.md"]
    bias_or_leakage_risks: ["Failed or skipped jobs can be overlooked", "Logs may contain secret names", "Artifacts expire", "CI environment differs from local performance environment"]
    notes: "Raw platform exports are account data; summarize only what is needed."

  - requirement_id: "NWRDS_N2_CODECOV_COVERAGE_EXPORTS"
    priority: "N2_PLATFORM_EXPORTS"
    dataset_name: "Codecov and local coverage reports"
    source_type: "platform_export"
    source_owner_or_provider: "Codecov and GitHub Actions"
    source_url_or_location: "https://codecov.io/gh/MateoBodon/quant-pricer-cpp"
    access_status: "needs_user_export"
    data_policy_status: "private_account_data"
    project_need: "Substantiate coverage badges and code-quality claims if used publicly."
    quant_use_case: "Coverage trend analysis, uncovered module prioritization, and CI badge verification."
    required_for_current_reproduction: false
    required_for_current_claim_validation: false
    useful_for_future_expansion: true
    date_range:
      minimum_required: "Latest release or PR coverage report if coverage is claimed."
      optimal: "Coverage history by commit and branch."
    frequency: "event"
    expected_size_class: "medium"
    refresh_cadence: "ad_hoc"
    storage_target: "private account archive for full reports; repo for small summarized coverage snapshots"
    safe_to_commit_to_repo: false
    required_user_action: "Export report or provide platform access if needed."
    acquisition_method: "Codecov UI/API export or GitHub coverage artifacts."
    validation_method: "Match commit SHA, branch, flags, lcov file, and coverage percentage to workflow output."
    joins_to_wrds_or_project_data: [".github/workflows/ci.yml", "build-cov/coverage.* if generated"]
    bias_or_leakage_risks: ["Coverage can exclude files via filters", "Badge can point to default branch while docs cite another commit", "Raw reports can be bulky"]
    notes: "Useful for project quality narrative, not financial model validation."

  - requirement_id: "NWRDS_N2_CLOUD_AND_LOCAL_BENCHMARK_LOGS"
    priority: "N2_PLATFORM_EXPORTS"
    dataset_name: "Cloud/server/local benchmark environment logs"
    source_type: "platform_export"
    source_owner_or_provider: "User machines, GitHub runners, Hetzner/AWS/GCP or other compute providers"
    source_url_or_location: "Private/local machine logs and cloud console exports"
    access_status: "needs_user_export"
    data_policy_status: "private_account_data"
    project_need: "Make high-performance claims reproducible across named hardware."
    quant_use_case: "Throughput comparison, scalability analysis, compiler/runtime sensitivity, and benchmark reproducibility."
    required_for_current_reproduction: false
    required_for_current_claim_validation: true
    useful_for_future_expansion: true
    date_range:
      minimum_required: "Every run used in public benchmark claims."
      optimal: "Per-run environment packet with CPU, RAM, OS, compiler, flags, thread topology, power governor, and run timing."
    frequency: "event"
    expected_size_class: "small"
    refresh_cadence: "ad_hoc"
    storage_target: "private account archive for raw logs; repo for sanitized benchmark manifests and aggregates"
    safe_to_commit_to_repo: false
    required_user_action: "Provide or approve collection of machine metadata; avoid hostnames/secrets if sensitive."
    acquisition_method: "sysctl/lscpu, compiler --version, cmake cache, Google Benchmark JSON, cloud instance metadata summaries."
    validation_method: "Compare machine label, commit SHA, run command, benchmark min_time/repetitions, temperature/noise notes, and manifest hashes."
    joins_to_wrds_or_project_data: ["docs/artifacts/bench", "docs/artifacts/manifest.json"]
    bias_or_leakage_risks: ["Cherry-picked hardware", "Thermal throttling", "Noisy cloud neighbors", "Compiler/library version differences"]
    notes: "This is critical for prestige/performance, but raw platform logs should be sanitized."

  - requirement_id: "NWRDS_N2_BROKER_ACCOUNT_EXPORTS"
    priority: "N2_PLATFORM_EXPORTS"
    dataset_name: "Broker option chains, quotes, orders, fills, and account exports"
    source_type: "platform_export"
    source_owner_or_provider: "Interactive Brokers, Schwab, Fidelity, Robinhood, broker APIs, or user account statements"
    source_url_or_location: "Private broker account export location to be specified by user"
    access_status: "needs_user_export"
    data_policy_status: "private_account_data"
    project_need: "Support future execution-cost, fill-quality, and real-world feasibility diagnostics if the project expands beyond pricing."
    quant_use_case: "Bid/ask slippage, fill models, latency/marketability checks, margin/commission estimates, and live paper-trade validation."
    required_for_current_reproduction: false
    required_for_current_claim_validation: false
    useful_for_future_expansion: true
    date_range:
      minimum_required: "Only event windows tied to a specific future execution-cost study."
      optimal: "Full account-approved history with account identifiers removed or hashed."
    frequency: "event"
    expected_size_class: "medium"
    refresh_cadence: "ad_hoc"
    storage_target: "private account archive only; public repo only for anonymized aggregate execution diagnostics"
    safe_to_commit_to_repo: false
    required_user_action: "Explicitly export and approve use; redact account numbers, balances, and personal information."
    acquisition_method: "Manual broker export or API pull in a private environment."
    validation_method: "Hash original exports, redact PII, reconcile timestamps/time zones, commissions, fills, and corporate-action adjustments."
    joins_to_wrds_or_project_data: ["ticker/option symbol", "trade timestamp", "future vendor quotes", "calendar"]
    bias_or_leakage_risks: ["Private account leakage", "Fill data is user-specific and not generalizable", "Paper fills differ from live fills", "Post-trade selection bias"]
    notes: "Not part of current project claims and not a trading-system requirement."

  - requirement_id: "NWRDS_N2_RESEARCH_PLATFORM_EXPORTS"
    priority: "N2_PLATFORM_EXPORTS"
    dataset_name: "Research platform exports such as Numerai, WorldQuant, Kaggle, or internal notebooks"
    source_type: "platform_export"
    source_owner_or_provider: "User-controlled platform accounts"
    source_url_or_location: "Private platform exports; project-specific location to be specified"
    access_status: "needs_user_export"
    data_policy_status: "private_account_data"
    project_need: "Optional future comparison to external quant-research platforms or contest-style benchmark workflows."
    quant_use_case: "Feature-engineering transfer, external benchmark discipline, tournament-style validation, and account-specific result preservation."
    required_for_current_reproduction: false
    required_for_current_claim_validation: false
    useful_for_future_expansion: true
    date_range:
      minimum_required: "None for current project."
      optimal: "Only exports tied to a defined future research ticket."
    frequency: "event"
    expected_size_class: "large"
    refresh_cadence: "ad_hoc"
    storage_target: "private account archive; repo only for high-level public-safe summaries"
    safe_to_commit_to_repo: false
    required_user_action: "Explicitly export and approve use; respect platform terms and no-upload/no-mutation policies."
    acquisition_method: "Manual account export or platform API in a private environment."
    validation_method: "Record platform, export timestamp, account/model id policy, file hashes, and terms constraints."
    joins_to_wrds_or_project_data: ["none by default", "future feature panels only if separately designed"]
    bias_or_leakage_risks: ["Platform data terms may forbid redistribution", "Account-specific results can be mistaken for general evidence", "Leaderboard leakage and target leakage risks"]
    notes: "Useful only if the repo later expands into broader quant-research workflows."

  - requirement_id: "NWRDS_N3_CBOE_DATASHOP_OPTIONS"
    priority: "N3_PRIVATE_VENDOR"
    dataset_name: "Cboe DataShop historical options and volatility products"
    source_type: "private_vendor"
    source_owner_or_provider: "Cboe DataShop"
    source_url_or_location: "https://datashop.cboe.com/"
    access_status: "needs_subscription"
    data_policy_status: "licensed_restricted"
    project_need: "Provide a non-WRDS direct vendor path for SPX/SPY/equity option quotes and cross-vendor validation."
    quant_use_case: "Independent option surface validation, quote comparison, market data robustness, and Cboe-native SPX/VIX datasets."
    required_for_current_reproduction: false
    required_for_current_claim_validation: false
    useful_for_future_expansion: true
    date_range:
      minimum_required: "Current SPX panel dates if used to validate claims."
      optimal: "2005-present or full purchased history for selected underlyings."
    frequency: "daily"
    expected_size_class: "huge"
    refresh_cadence: "ad_hoc"
    storage_target: "shared restricted vault: /Volumes/Storage/Data/Vendor/cboe_datashop"
    safe_to_commit_to_repo: false
    required_user_action: "Confirm subscription, license, redistribution rights, and approved storage path."
    acquisition_method: "Vendor download/API in restricted environment."
    validation_method: "Verify schema, quote time, bid/ask/iv fields, option symbol parsing, source hashes, entitlement, and license notes."
    joins_to_wrds_or_project_data: ["normalized option surface schema", "calendar", "OptionMetrics/WRDS comparison if available"]
    bias_or_leakage_risks: ["Vendor coverage differences", "Quote timestamp mismatch", "License leakage", "Cross-vendor cherry-picking"]
    notes: "High-value but not needed before P0 WRDS/sample evidence is repaired."

  - requirement_id: "NWRDS_N3_DIRECT_OPTIONMETRICS"
    priority: "N3_PRIVATE_VENDOR"
    dataset_name: "Direct OptionMetrics IvyDB data outside WRDS"
    source_type: "private_vendor"
    source_owner_or_provider: "OptionMetrics"
    source_url_or_location: "https://optionmetrics.com/"
    access_status: "needs_subscription"
    data_policy_status: "licensed_restricted"
    project_need: "Alternative acquisition path for the same conceptual data used by the WRDS pipeline."
    quant_use_case: "SPX/equity option quotes, underlying prices, zero curves, dividends, distributions, and cross-checks when WRDS access is unavailable."
    required_for_current_reproduction: false
    required_for_current_claim_validation: false
    useful_for_future_expansion: true
    date_range:
      minimum_required: "Current panel dates if replacing WRDS."
      optimal: "2005-present or full licensed history."
    frequency: "daily"
    expected_size_class: "huge"
    refresh_cadence: "ad_hoc"
    storage_target: "shared restricted vault: /Volumes/Storage/Data/Vendor/optionmetrics_direct"
    safe_to_commit_to_repo: false
    required_user_action: "Confirm license and whether direct data may be transformed into repo-safe aggregates."
    acquisition_method: "Vendor-provided files/API in restricted environment."
    validation_method: "Compare schema to WRDS map, verify date coverage, hashes, adjustment fields, rates/dividends, and entitlement notes."
    joins_to_wrds_or_project_data: ["wrds_pipeline", "project_state/WRDS_DATA_REQUIREMENTS.md", "normalized option surface schema"]
    bias_or_leakage_risks: ["Same vendor via different channel can still have version differences", "Raw secid/quotes cannot enter repo", "License terms may differ from WRDS"]
    notes: "Classified non-WRDS only when sourced directly from OptionMetrics rather than through WRDS."

  - requirement_id: "NWRDS_N3_BLOOMBERG_REFINITIV_FACTSET_MARKETDATA"
    priority: "N3_PRIVATE_VENDOR"
    dataset_name: "Bloomberg, Refinitiv, FactSet, and similar institutional market data"
    source_type: "private_vendor"
    source_owner_or_provider: "Bloomberg, LSEG Refinitiv, FactSet, or equivalent"
    source_url_or_location: "Vendor terminals/APIs; exact product to be specified"
    access_status: "needs_subscription"
    data_policy_status: "licensed_restricted"
    project_need: "Provide high-quality identifiers, prices, corporate actions, fundamentals, estimates, and benchmark data when WRDS coverage is insufficient."
    quant_use_case: "Cross-vendor validation, identifier truth, corporate-action correctness, rates/dividend curves, benchmark constituents, and event calendars."
    required_for_current_reproduction: false
    required_for_current_claim_validation: false
    useful_for_future_expansion: true
    date_range:
      minimum_required: "Only panels tied to specific future claims."
      optimal: "2005-present for selected universes with point-in-time fields where licensed."
    frequency: "mixed"
    expected_size_class: "huge"
    refresh_cadence: "daily"
    storage_target: "shared restricted vault: /Volumes/Storage/Data/Vendor/institutional_marketdata"
    safe_to_commit_to_repo: false
    required_user_action: "Confirm subscription, API access, field entitlements, and redistribution limits."
    acquisition_method: "Vendor API/export under license."
    validation_method: "Capture field mnemonics, entitlement, extraction timestamp, point-in-time settings, vendor version, and row/file hashes."
    joins_to_wrds_or_project_data: ["ticker", "CUSIP", "ISIN", "FIGI", "calendar", "future WRDS cross-checks"]
    bias_or_leakage_risks: ["Point-in-time flags are easy to misuse", "Terminal exports can contain licensed raw rows", "Vendor corrections and survivorship settings vary"]
    notes: "Do not use to strengthen claims unless the license and reproducibility path are reviewable."

  - requirement_id: "NWRDS_N3_SP_GLOBAL_INDEX_DIVIDENDS_CONSTITUENTS"
    priority: "N3_PRIVATE_VENDOR"
    dataset_name: "S&P Global index constituents, index levels, and dividend points"
    source_type: "private_vendor"
    source_owner_or_provider: "S&P Global or licensed index data provider"
    source_url_or_location: "S&P Global/index provider portal or vendor API"
    access_status: "needs_subscription"
    data_policy_status: "licensed_restricted"
    project_need: "Provide authoritative SPX constituent, index dividend, and index methodology data outside WRDS."
    quant_use_case: "SPX dividend assumptions, index membership, benchmark construction, survivorship controls, and index-option pricing diagnostics."
    required_for_current_reproduction: false
    required_for_current_claim_validation: false
    useful_for_future_expansion: true
    date_range:
      minimum_required: "Current SPX panel dates if used for pricing-input validation."
      optimal: "2005-present with point-in-time constituent and dividend data."
    frequency: "daily"
    expected_size_class: "large"
    refresh_cadence: "daily"
    storage_target: "shared restricted vault: /Volumes/Storage/Data/Vendor/sp_global_index"
    safe_to_commit_to_repo: false
    required_user_action: "Confirm subscription and redistribution rights."
    acquisition_method: "Vendor export/API."
    validation_method: "Verify as-of dates, effective dates, index ids, weights, dividend points/yields, and methodology notes."
    joins_to_wrds_or_project_data: ["SPX symbol/index id", "calendar date", "option pricing input builders"]
    bias_or_leakage_risks: ["Current constituents create survivorship bias", "Final index files can leak future additions/deletions", "Dividend point vintages matter"]
    notes: "Especially useful if SPX pricing claims depend on index dividends."

  - requirement_id: "NWRDS_N3_OPTIONS_API_VENDOR_FEEDS"
    priority: "N3_PRIVATE_VENDOR"
    dataset_name: "Modern options API vendors"
    source_type: "private_vendor"
    source_owner_or_provider: "Databento, Polygon.io, ThetaData, ORATS, Nasdaq Data Link, or equivalent"
    source_url_or_location: "Vendor-specific API documentation and subscription portals"
    access_status: "needs_subscription"
    data_policy_status: "licensed_restricted"
    project_need: "Support faster, narrower, or more developer-friendly option data ingestion outside WRDS."
    quant_use_case: "OPRA-style quotes/trades, EOD option chains, implied volatility surfaces, greeks, and real-time/delayed diagnostics."
    required_for_current_reproduction: false
    required_for_current_claim_validation: false
    useful_for_future_expansion: true
    date_range:
      minimum_required: "Selected current panels or recent holdouts."
      optimal: "2018-present for recent critical option research; intraday only for targeted windows."
    frequency: "intraday"
    expected_size_class: "huge"
    refresh_cadence: "daily"
    storage_target: "shared restricted vault: /Volumes/Storage/Data/Vendor/options_api"
    safe_to_commit_to_repo: false
    required_user_action: "Select vendor, confirm license, provide credentials in secret store only, and approve storage policy."
    acquisition_method: "Vendor API pull into restricted vault with request manifests."
    validation_method: "Log schema, timestamps, quote conditions, root/symbol conventions, corrections, entitlements, request ids, and hashes."
    joins_to_wrds_or_project_data: ["normalized option surface schema", "calendar", "ticker/option symbol", "future cross-vendor validation"]
    bias_or_leakage_risks: ["OPRA data is large and condition-code heavy", "Vendor greeks may use hidden assumptions", "Subscription limits can cause missing data", "Raw rows are licensed"]
    notes: "Can be more operationally convenient than WRDS but does not remove licensing obligations."

  - requirement_id: "NWRDS_N3_RATE_VOL_CREDIT_VENDOR_DATA"
    priority: "N3_PRIVATE_VENDOR"
    dataset_name: "Vendor rates, volatility, credit curves, and macro calendars"
    source_type: "private_vendor"
    source_owner_or_provider: "ICE, CME, Bloomberg, Refinitiv, S&P, Markit, or equivalent"
    source_url_or_location: "Vendor-specific terminals/APIs"
    access_status: "needs_subscription"
    data_policy_status: "licensed_restricted"
    project_need: "Improve model inputs and stress controls when public Treasury/FRED data is insufficient."
    quant_use_case: "OIS/SOFR curves, vol surfaces, credit spreads, funding curves, economic calendars, and regime diagnostics."
    required_for_current_reproduction: false
    required_for_current_claim_validation: false
    useful_for_future_expansion: true
    date_range:
      minimum_required: "2018-present for modern holdouts."
      optimal: "2005-present or full licensed history."
    frequency: "daily"
    expected_size_class: "large"
    refresh_cadence: "daily"
    storage_target: "shared restricted vault: /Volumes/Storage/Data/Vendor/rates_vol_credit"
    safe_to_commit_to_repo: false
    required_user_action: "Confirm license, field entitlements, and permitted derived-output policy."
    acquisition_method: "Vendor API/export in restricted environment."
    validation_method: "Record curve construction, tenor grid, calendar, units, time of day, corrections, and hash."
    joins_to_wrds_or_project_data: ["calendar date", "option maturity tenor", "pricing input builders", "macro regime labels"]
    bias_or_leakage_risks: ["Using end-of-day curves after option quote time can leak", "Curve methodology differs by vendor", "Redistribution restrictions are strict"]
    notes: "Useful for production-grade pricing inputs but not required for current sample evidence."

  - requirement_id: "NWRDS_N4_PUBLIC_NEWS_EVENT_SENTIMENT"
    priority: "N4_EXPERIMENTAL_ALT"
    dataset_name: "Public news, event, and sentiment feeds"
    source_type: "public_api"
    source_owner_or_provider: "GDELT, public news APIs, RSS feeds, Wikipedia, or similar public sources"
    source_url_or_location: "Provider-specific APIs and public bulk downloads"
    access_status: "available_now"
    data_policy_status: "safe_public"
    project_need: "Explore event/news controls for volatility and jump-risk research after core evidence is stable."
    quant_use_case: "News intensity, event clustering, macro shock labels, sentiment proxies, and volatility-event diagnostics."
    required_for_current_reproduction: false
    required_for_current_claim_validation: false
    useful_for_future_expansion: true
    date_range:
      minimum_required: "2018-present for recent exploratory work."
      optimal: "Full available history with publication timestamps."
    frequency: "event"
    expected_size_class: "huge"
    refresh_cadence: "daily"
    storage_target: "shared vault: /Volumes/Storage/Data/Public/news_events; repo only for aggregate event counts or labels"
    safe_to_commit_to_repo: false
    required_user_action: "Choose provider and approve terms before storage."
    acquisition_method: "Public API/bulk download with source and timestamp manifests."
    validation_method: "Record publication timestamp, source, language, relevance filters, dedupe keys, and text-retention policy."
    joins_to_wrds_or_project_data: ["calendar date", "ticker/company mapping", "future event panels"]
    bias_or_leakage_risks: ["Backfilled articles can leak", "Text licenses vary", "Sentiment models can be unstable", "Coverage varies by company size"]
    notes: "Do not add until there is a specific hypothesis and a text-retention policy."

  - requirement_id: "NWRDS_N4_SOCIAL_RETAIL_ATTENTION"
    priority: "N4_EXPERIMENTAL_ALT"
    dataset_name: "Social, retail attention, and web interest data"
    source_type: "public_api"
    source_owner_or_provider: "Reddit, StockTwits, X, Google Trends, Wikipedia pageviews, app/platform APIs"
    source_url_or_location: "Provider-specific APIs and exports"
    access_status: "needs_credentials"
    data_policy_status: "unknown"
    project_need: "Explore attention and crowding controls for future volatility/jump studies."
    quant_use_case: "Retail-attention proxies, event-risk diagnostics, and option-volume/volatility anomaly research."
    required_for_current_reproduction: false
    required_for_current_claim_validation: false
    useful_for_future_expansion: true
    date_range:
      minimum_required: "Only windows tied to a specific future hypothesis."
      optimal: "2018-present with timestamped availability and provider terms archived."
    frequency: "event"
    expected_size_class: "huge"
    refresh_cadence: "daily"
    storage_target: "private or public-data vault depending on provider terms; repo only for aggregate public-safe labels"
    safe_to_commit_to_repo: false
    required_user_action: "Approve provider, credentials, privacy policy, and retention rules."
    acquisition_method: "API export using approved credentials and rate-limit compliance."
    validation_method: "Record query terms, timestamps, rate limits, terms, dedupe, language filters, and aggregation method."
    joins_to_wrds_or_project_data: ["ticker/company mapping", "calendar date", "future event/volatility panels"]
    bias_or_leakage_risks: ["Survivorship and ticker ambiguity", "API policy changes", "Deleted/private content", "Lookahead from final popularity ranks"]
    notes: "Experimental and far below current evidence priorities."

  - requirement_id: "NWRDS_N4_PRIVATE_NEWS_TRANSCRIPTS_ANALYTICS"
    priority: "N4_EXPERIMENTAL_ALT"
    dataset_name: "Private news, transcript, and NLP analytics vendors"
    source_type: "private_vendor"
    source_owner_or_provider: "RavenPack, AlphaSense, FactSet, Bloomberg, Refinitiv, S&P CIQ, or similar"
    source_url_or_location: "Vendor portal/API to be specified"
    access_status: "needs_subscription"
    data_policy_status: "licensed_restricted"
    project_need: "Add event text and sentiment features for ambitious volatility research."
    quant_use_case: "Transcript sentiment, guidance events, news shocks, event classification, and jump-risk controls."
    required_for_current_reproduction: false
    required_for_current_claim_validation: false
    useful_for_future_expansion: true
    date_range:
      minimum_required: "2018-present for recent event studies."
      optimal: "Full licensed history with availability timestamps."
    frequency: "event"
    expected_size_class: "huge"
    refresh_cadence: "daily"
    storage_target: "shared restricted vault: /Volumes/Storage/Data/Vendor/news_text"
    safe_to_commit_to_repo: false
    required_user_action: "Confirm subscription, terms, text-retention rules, and allowed derived outputs."
    acquisition_method: "Vendor API/export into restricted vault."
    validation_method: "Capture event id, publication timestamp, availability timestamp, entity mapping, sentiment version, and license notes."
    joins_to_wrds_or_project_data: ["ticker/company id", "calendar date", "future event panels"]
    bias_or_leakage_risks: ["Backfilled/curated event labels can leak", "NLP model version changes", "Text redistribution restrictions", "Coverage bias"]
    notes: "Private version of the public news/event lane; not urgent."

  - requirement_id: "NWRDS_N4_DERIVED_FEATURE_STORE_NON_WRDS"
    priority: "N4_EXPERIMENTAL_ALT"
    dataset_name: "Non-WRDS derived feature store"
    source_type: "derived_dataset"
    source_owner_or_provider: "quant-pricer-cpp future research pipeline"
    source_url_or_location: "/Volumes/Storage/Data/Derived/quant-pricer-cpp/non_wrds_features"
    access_status: "unknown"
    data_policy_status: "derived_safe_if_aggregated"
    project_need: "Create a clean boundary between raw public/vendor/account data and public-safe research artifacts."
    quant_use_case: "Feature panels for rates, macro, calendars, events, identifiers, benchmark labels, and model diagnostics."
    required_for_current_reproduction: false
    required_for_current_claim_validation: false
    useful_for_future_expansion: true
    date_range:
      minimum_required: "Only after source datasets and protocols are selected."
      optimal: "Versioned feature snapshots by research ticket, with raw-source hashes and transformation code."
    frequency: "mixed"
    expected_size_class: "large"
    refresh_cadence: "ad_hoc"
    storage_target: "shared derived vault; repo only for public-safe aggregate summaries and schemas"
    safe_to_commit_to_repo: false
    required_user_action: "Approve derived-vault location and public-safe aggregation rules."
    acquisition_method: "Build from approved non-WRDS raw/public/vendor/account sources using versioned scripts."
    validation_method: "Source manifest, row counts, hashes, schema contracts, leakage checks, point-in-time tests, and reproducible transforms."
    joins_to_wrds_or_project_data: ["calendar date", "ticker/security id", "option surface ids", "artifact manifests"]
    bias_or_leakage_risks: ["Feature leakage from final revisions", "Mixed licensing contamination", "Silent source refresh drift", "Overwriting old feature snapshots"]
    notes: "This is the right destination for future non-WRDS features before any aggregate is promoted to docs/artifacts."

highest_priority_acquisition_order:
  - requirement_id: "NWRDS_N0_REPO_SYNTHETIC_OPTION_FIXTURES"
    reason: "Already available and required for public-safe sample reproduction."
  - requirement_id: "NWRDS_N0_FROZEN_VALIDATION_PROTOCOL_CONFIGS"
    reason: "Locks scenarios, tolerances, and date panels before any evidence refresh."
  - requirement_id: "NWRDS_N0_CURATED_ARTIFACTS_MANIFEST_METRICS"
    reason: "Current claim validation depends on artifact and manifest truth."
  - requirement_id: "NWRDS_N0_REVIEW_RUN_LOGS_AND_BUNDLES"
    reason: "Preserves exact command/validation evidence and failed reproduction context."
  - requirement_id: "NWRDS_N0_BUILD_BENCHMARK_ENVIRONMENT_METADATA"
    reason: "Needed before strengthening performance/prestige claims."
  - requirement_id: "NWRDS_N0_VALIDATION_PACK_AND_RELEASE_ASSETS"
    reason: "Needed before release validation-pack claims are promoted."
  - requirement_id: "NWRDS_N0_PACKAGE_REGISTRY_AND_INSTALL_EVIDENCE"
    reason: "Needed before package/install claims are promoted."
  - requirement_id: "NWRDS_N1_US_TREASURY_CURVES"
    reason: "Public, small, directly useful for rate-input examples and sanity checks."
  - requirement_id: "NWRDS_N1_FRED_ALFRED_MACRO_RATES"
    reason: "Public macro/rates/regime data materially improves benchmark context."
  - requirement_id: "NWRDS_N1_EXCHANGE_TRADING_CALENDARS"
    reason: "Improves OOS next-trading-day correctness and holiday-gap tests."
  - requirement_id: "NWRDS_N1_CBOE_VIX_HISTORY"
    reason: "Small public volatility-regime control for SPX panels."
  - requirement_id: "NWRDS_N1_KENNETH_FRENCH_FACTORS"
    reason: "Small public factor benchmark useful for any future return/PnL analysis."
  - requirement_id: "NWRDS_N1_SEC_EDGAR_COMPANY_FACTS_FILINGS"
    reason: "Public event/fundamental data for future equity-option controls."
  - requirement_id: "NWRDS_N1_OCC_CONTRACT_ADJUSTMENT_MEMOS"
    reason: "Public support for contract-adjustment correctness in equity-option expansion."
  - requirement_id: "NWRDS_N3_CBOE_DATASHOP_OPTIONS"
    reason: "Highest-value non-WRDS private option-data alternative, but only after core evidence protocol is clean."

user_access_questions:
  - "Should `/Volumes/Storage/Data/Public` be the canonical shared vault for public non-WRDS bulk data, parallel to `/Volumes/Storage/Data/WRDS`?"
  - "Do you want public macro/rates/calendar datasets mirrored locally now, or only listed until the next execution ticket?"
  - "Do you have or want a FRED API key stored outside the repo for public macro/rate refreshes?"
  - "Should package/install claims be validated against PyPI, TestPyPI, GitHub Releases, or only local wheel builds?"
  - "Can Codex use GitHub/Codecov connectors later to export CI, release, coverage, and Pages evidence?"
  - "Are broker/account exports in scope for future execution-cost diagnostics, or should this remain a pure pricing/research project?"
  - "Do you have direct Cboe DataShop, OptionMetrics, Bloomberg, Refinitiv, FactSet, S&P, Databento, Polygon, ThetaData, or other non-WRDS vendor entitlements?"
  - "What minimum aggregation rule should govern derived option-surface outputs before they are safe for `docs/artifacts/`?"
  - "Should future public/free downloaded raw data be committed when license-safe and tiny, or should all raw external data stay in a vault with only derived summaries in repo?"

non_wrds_data_policy_notes:
  - "Do not commit private account exports, vendor raw data, broker statements, API tokens, credentials, or raw platform logs."
  - "Synthetic fixtures are safe to commit only when clearly marked and not derived from restricted raw rows."
  - "Public/free does not automatically mean safe to redistribute; record provider terms and prefer vault storage for raw downloads."
  - "Small public derived summaries can enter the repo when they have source URLs, retrieval timestamps, hashes, and no license conflict."
  - "Row-level option quotes, bid/ask surfaces, account fills, and vendor identifiers should stay restricted unless explicitly synthetic or licensed for redistribution."
  - "Every promoted non-WRDS dataset should have source, timestamp, hash, schema, transformation command, and validation notes."
  - "Do not use final revised macro/fundamental/event data as ex-ante model features unless the design explicitly allows it and labels it as revised-history evidence."
  - "Keep raw, derived row-level, and public-safe aggregate layers separate."
  - "Run `python3 scripts/check_data_policy.py` after adding or regenerating any tracked data/artifact files."
```

## Source Notes

Official public sources checked for this planning map include the FRED API documentation, U.S. Treasury rate archive pages, Kenneth French Data Library, SEC EDGAR APIs, Cboe VIX historical data page, Nasdaq Trader calendar, OCC information memos, and OpenFIGI API documentation. These sources should still be re-checked during an execution ticket before building automated downloaders.
