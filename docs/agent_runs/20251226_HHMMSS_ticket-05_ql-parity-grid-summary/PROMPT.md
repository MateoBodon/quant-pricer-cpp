TICKET: ticket-05
RUN_NAME: 20251226_HHMMSS_ticket-05_ql-parity-grid-summary

You are Codex working in the quant-pricer-cpp repo. Follow AGENTS.md as binding.

FIRST: Read these files before doing anything else:
- AGENTS.md
- docs/PLAN_OF_RECORD.md
- docs/DOCS_AND_LOGGING_SYSTEM.md
- docs/CODEX_SPRINT_TICKETS.md

Do NOT write a long upfront plan. Execute the ticket with a tight inspect→edit→test→log loop.

Ticket to implement:
- docs/CODEX_SPRINT_TICKETS.md :: “ticket-05 — QuantLib parity: grid summary (max/median/p95 by bucket)”

Hard constraints:
- No fabricated results. Only claim tests/metrics/artifacts that you actually ran/produced in this workspace.
- Do not change evaluation protocol / grids / tolerances unless explicitly required by ticket-05; if you must, document it.
- No raw WRDS/OptionMetrics data committed. License-safe tiny derived samples only if policy allows.

Required workflow:
1) Inspect current parity pipeline
   - Locate how scripts/ql_parity.py writes outputs (CSV/plots) and where scripts/generate_metrics_summary.py pulls from.
   - Find current artifact paths used by the official pipeline (AGENTS.md section 3).

2) Implement ticket-05 requirements (make minimal, reviewable diffs)
   A) Parity CSV improvements
   - Ensure docs/artifacts/ql_parity/ql_parity.csv includes:
     - bucket columns (define explicitly; e.g., maturity_bucket, moneyness_bucket, vol_bucket if applicable)
     - per-row error values (abs error and/or rel error; be consistent with existing metric)
   - Also output a per-bucket summary table (either:
     - a second CSV like docs/artifacts/ql_parity/ql_parity_bucket_summary.csv, OR
     - a clearly delimited section inside metrics_summary.md generated downstream).
   - Summary stats per bucket must include at least: max, median, p95 (and count).

   B) Metrics summary updates
   - Update scripts/generate_metrics_summary.py so the metrics summary reports:
     - full-grid max error AND median error (and p95 if available) for QuantLib parity.
   - Ensure it reads the canonical docs/artifacts/manifest.json and artifacts paths (no writing to ./artifacts).

   C) Distribution plot
   - Create an error distribution plot (histogram or ECDF) showing the full-grid error distribution
   - Save under docs/artifacts/ql_parity/ (e.g., ql_parity_error_dist.png).
   - Plot must be based on the same CSV used for the summary (no separate hidden filtering).

3) Run minimal sufficient tests/commands (log everything)
   - Build + FAST tests (AGENTS.md):
     - cmake -S . -B build -DCMAKE_BUILD_TYPE=Release
     - cmake --build build -j
     - ctest --test-dir build -L FAST --output-on-failure
   - Run parity + summary scripts:
     - python scripts/ql_parity.py
     - python scripts/generate_metrics_summary.py --artifacts docs/artifacts --manifest docs/artifacts/manifest.json
   - If ql_parity is part of the official reproduction pipeline, also run:
     - REPRO_FAST=1 WRDS_USE_SAMPLE=1 ./scripts/reproduce_all.sh

4) Artifacts + docs updates
   - Update/refresh any affected files under docs/artifacts/ (CSV + plot + metrics summary outputs).
   - If headline parity metrics changed, update:
     - PROGRESS.md (always)
     - project_state/CURRENT_RESULTS.md (only if results changed)
   - Keep docs/CODEX_SPRINT_TICKETS.md unchanged except marking ticket status if you actually finish it in this run.

5) Run logging (required)
   Create: docs/agent_runs/<RUN_NAME>/
   Must include:
   - PROMPT.md  (paste this exact prompt)
   - COMMANDS.md (commands executed, in order)
   - RESULTS.md (what changed + key numbers + artifact paths)
   - TESTS.md (test commands + key outputs)
   - META.json (git SHA before/after, env notes, dataset id, config hash)

6) Commit + bundle
   - Create branch: codex/ticket-05-ql-parity-grid-summary
   - Commit message: "ticket-05: QuantLib parity grid summary"
   - Commit body MUST include:
     - Tests: <exact commands you ran>
     - Artifacts: <paths updated>
     - Run log: docs/agent_runs/<RUN_NAME>/
   - Generate the bundle and record its path in RESULTS.md:
     make gpt-bundle TICKET=ticket-05 RUN_NAME=<RUN_NAME>

Suggested safe Codex invocation (human runs this, not you):
- codex --sandbox workspace-write --ask-for-approval untrusted

Human merge checklist:
- FAST tests green (ctest -L FAST)
- ql_parity CSV includes bucket columns + per-bucket max/median/p95
- metrics_summary reports max + median (and p95 if added)
- distribution plot exists under docs/artifacts/ql_parity/
- run log folder complete
- bundle generated and path recorded
