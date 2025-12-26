TICKET: ticket-01
RUN_NAME: 20251226_HHMMSS_ticket-01_unify-artifacts-root

You are Codex working in the quant-pricer-cpp repo. Follow AGENTS.md as binding.

FIRST: Read these files before doing anything else:
- AGENTS.md
- docs/PLAN_OF_RECORD.md
- docs/DOCS_AND_LOGGING_SYSTEM.md
- docs/CODEX_SPRINT_TICKETS.md
- project_state/KNOWN_ISSUES.md

Do NOT write a long upfront plan. Execute the ticket with a tight inspect→edit→test→log loop.

Ticket to implement:
- docs/CODEX_SPRINT_TICKETS.md :: “ticket-01 — Canonicalize artifact root + manifest (single source of truth)”

Hard constraints (must obey):
- No fabricated results. Log every command you run.
- Validity > metrics. Don’t change evaluation protocol while doing this ticket.
- No raw WRDS data committed. No credentials or secrets in repo/logs.
- Do NOT “fix” by disabling functionality; fix root causes.

1) Inspect (prove what’s broken)
- Search for any hard-coded writes to `artifacts/` vs `docs/artifacts/`:
  - ripgrep for: "artifacts/" "docs/artifacts" "--artifacts" "ARTIFACT" "manifest.json"
  - Identify which scripts write where (especially scripts invoked by ./scripts/reproduce_all.sh).
- Inspect current artifact helpers:
  - scripts/reproduce_all.sh
  - scripts/manifest_utils.py (or equivalent)
  - scripts/generate_metrics_summary.py
- Confirm what KNOWN_ISSUES says about split defaults, and locate the actual offending defaults.

2) Implement ticket-01 (minimal, reviewable diffs)
Goal: `docs/artifacts/` is the ONLY canonical artifact root. The official pipeline must not silently write to `artifacts/`.

A) Canonical root wiring
- Make `docs/artifacts/` the default artifact output for the official pipeline.
- Remove/stop any fallback logic where summaries/manifest can accidentally read from `artifacts/`.
- Ensure scripts called by reproduce_all either:
  - accept an explicit output root argument, OR
  - use a shared helper (single source of truth) that resolves to docs/artifacts.
- If you need an env var, pick ONE name (e.g., ARTIFACTS_ROOT) and thread it consistently.

B) Guardrail test (FAST)
- Add a FAST test that fails if the official pipeline writes anything under the non-canonical root.
  - Prefer a test that:
    - runs a minimal “fast” artifact generation in a temp dir or controlled environment, OR
    - asserts that after a fast repro run there are zero modified/created files under `artifacts/` (excluding allowed gitignored scratch, if any).
- The test should fail with a clear message telling the dev what to run/fix.

C) Docs + issues
- Update project_state/KNOWN_ISSUES.md:
  - If the split-root issue is fixed, mark it RESOLVED with date, commit SHA, and run log path.
- Update PROGRESS.md with today’s entry:
  - What changed
  - Tests run (exact commands)
  - Artifacts updated (paths)
- If this changes any “how to run” behavior, update docs/DOCS_AND_LOGGING_SYSTEM.md accordingly.

3) Tests / runs (log everything)
Run at minimum:
- cmake -S . -B build -DCMAKE_BUILD_TYPE=Release
- cmake --build build -j
- ctest --test-dir build -L FAST --output-on-failure

Then run the official pipeline fast mode:
- REPRO_FAST=1 WRDS_USE_SAMPLE=1 ./scripts/reproduce_all.sh

Acceptance checks you must explicitly verify (and write into RESULTS.md):
- The pipeline’s canonical outputs land under docs/artifacts/ (manifest + metrics summary + validation pack).
- The non-canonical `artifacts/` root is not used/created/modified by the official pipeline.

4) Run log (required)
Create/update: docs/agent_runs/<RUN_NAME>/
- PROMPT.md (this prompt, verbatim)
- COMMANDS.md (every command, in order)
- RESULTS.md (what changed + key evidence + any caveats)
- TESTS.md (commands + pass/fail + any failure snippet)
- META.json with required fields (from DOCS_AND_LOGGING_SYSTEM.md)
  - IMPORTANT: set git_sha_after to the post-commit HEAD that contains your changes

5) Commit policy
- Create a feature branch: codex/ticket-01-unify-artifacts-root
- Use small logical commits.
- Final commit message: "ticket-01: canonicalize artifact root"
- Commit body MUST include:
  - Tests: <exact commands you ran>
  - Artifacts: <paths updated>
  - Run log: docs/agent_runs/<RUN_NAME>/

6) Bundle for review
- Generate the bundle and record its path in docs/agent_runs/<RUN_NAME>/RESULTS.md:
  make gpt-bundle TICKET=ticket-01 RUN_NAME=<RUN_NAME>

Suggested safe Codex invocation (human runs this, not you):
- codex --sandbox workspace-write --ask-for-approval untrusted

Optional higher autonomy (ONLY if the human explicitly wants it):
- codex --sandbox workspace-write --ask-for-approval auto

Human merge checklist:
- FAST tests green (ctest -L FAST)
- REPRO_FAST=1 WRDS_USE_SAMPLE=1 ./scripts/reproduce_all.sh passes
- No writes to non-canonical artifacts root (`artifacts/`) by official pipeline
- KNOWN_ISSUES updated if the split-root issue is resolved
- PROGRESS updated with tests + artifacts
- Run log folder complete (PROMPT/COMMANDS/RESULTS/TESTS/META)
- Bundle generated and path recorded in RESULTS.md
