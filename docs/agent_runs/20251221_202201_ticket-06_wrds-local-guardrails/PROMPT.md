You are Codex working on quant-pricer-cpp. FIRST read these files (in this order) and treat them as binding constraints:
- AGENTS.md
- docs/PLAN_OF_RECORD.md
- docs/DOCS_AND_LOGGING_SYSTEM.md
- docs/CODEX_SPRINT_TICKETS.md

Task: implement NEW Ticket-06 (“Roll back local-mode drift + make WRDS local support explicit + restore sample reproducibility”).

Do NOT write a long upfront plan. Instead:
1) Inspect the current repo state and the recent changes referenced by DIFF.patch in the last bundle (especially wrds_pipeline/ingest_sppx_surface.py, scripts/generate_metrics_summary.py, docs/artifacts/*, Makefile).
2) Implement the minimal set of changes to satisfy Ticket-06 acceptance criteria:
   A) WRDS local mode must be explicit-only:
      - Remove any auto-detection that activates local mode based on hardcoded paths like /Volumes/Storage/Data/wrds.
      - Local mode should activate ONLY if WRDS_LOCAL_ROOT is explicitly set (env var) OR an explicit config entry is present in a committed config file.
      - Ensure sample mode (WRDS_USE_SAMPLE=1) is unaffected by local mode and remains the canonical reproducible path.
      - Ensure logs clearly state which data source was used (sample/cache/live/local) for each run.
   B) Restore committed artifacts to sample-mode reproducibility:
      - Regenerate docs/artifacts/metrics_summary.md + metrics_summary.json + manifest.json + validation_pack.zip using WRDS_USE_SAMPLE=1 (and REPRO_FAST=1 where supported).
      - Ensure committed artifacts do NOT embed absolute local paths like /Users/<name>/...; write repo-relative paths instead.
      - If local-run artifacts are useful, write them to a separate location (e.g. docs/artifacts/wrds_local/) and make sure metrics_summary defaults to sample-mode unless explicitly requested.
   C) Documentation and config reference updates:
      - Update project_state/CONFIG_REFERENCE.md (or the generator inputs) to document WRDS_LOCAL_ROOT if it remains supported.
      - Update project_state/KNOWN_ISSUES.md if any risks/behavior changes are discovered (especially license/redistribution risk).
      - Update PROGRESS.md with a new entry pointing to this run folder.
3) Run the minimal sufficient verification required by AGENTS.md and Ticket-06:
   - Build:
     cmake -S . -B build -DCMAKE_BUILD_TYPE=Release
     cmake --build build -j
   - Tests:
     ctest --test-dir build -L FAST --output-on-failure
   - WRDS sample smoke (must be deterministic and credential-free):
     WRDS_USE_SAMPLE=1 python -m wrds_pipeline.pipeline --fast
   - Full artifact gate (fast mode):
     REPRO_FAST=1 WRDS_USE_SAMPLE=1 ./scripts/reproduce_all.sh
4) Create a run log folder following docs/DOCS_AND_LOGGING_SYSTEM.md naming:
   - RUN_NAME="$(date -u +%Y%m%d_%H%M%S)_ticket-06_wrds-local-guardrails"
   - Write:
     docs/agent_runs/$RUN_NAME/PROMPT.md  (paste this entire prompt verbatim)
     docs/agent_runs/$RUN_NAME/COMMANDS.md (exact commands executed, in order; no ellipsizing)
     docs/agent_runs/$RUN_NAME/RESULTS.md  (what changed + key metrics + links to artifacts)
     docs/agent_runs/$RUN_NAME/TESTS.md    (tests + pass/fail outputs)
     docs/agent_runs/$RUN_NAME/META.json   (git SHA before/after, branch, env notes, dataset mode, config hash)
5) Commit on a feature branch:
   - Create/checkout: feature/ticket-06-wrds-local-guardrails
   - Commit message must include “Tests:” lines in the body with the exact commands you ran.
6) Generate the next review bundle and record the path in RESULTS.md:
   - make gpt-bundle TICKET=ticket-06 RUN_NAME=$RUN_NAME

Security / data policy:
- Do NOT add or commit raw WRDS/OptionMetrics/IvyDB tables, parquet, or strike-by-strike quote surfaces unless you have explicit license-safe justification documented.
- If you find files in the repo that look like redistributed market data (e.g., columns like strike, maturity, market_iv), STOP and write it up in project_state/KNOWN_ISSUES.md + propose a safe alternative (synthetic/public).
- Do not print any secrets. Never echo WRDS_USERNAME/WRDS_PASSWORD values.

Suggested Codex invocation (safe):
- codex --sandbox workspace-write --ask-for-approval untrusted
  (These flags are documented in the Codex CLI reference + security guide.) :contentReference[oaicite:1]{index=1}

Full-autonomy mode is NOT requested. Do not use --yolo / dangerously-bypass-approvals-and-sandbox unless a human explicitly asks and you are inside an isolated runner. :contentReference[oaicite:2]{index=2}

Human merge checklist to include at end of RESULTS.md:
- No raw data or secrets committed
- Sample-mode reproduce_all passes
- FAST tests pass
- metrics_summary shows “sample bundle” and has no absolute paths
- Docs updated (PROGRESS + project_state as needed)
