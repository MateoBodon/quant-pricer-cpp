TICKET: ticket-01
RUN_NAME: $(date -u +%Y%m%d_%H%M%S)_ticket-01_unify-artifacts-root

You are Codex working in repo: quant-pricer-cpp.

FIRST: Read these files (in this order) and treat them as binding:
- AGENTS.md
- docs/PLAN_OF_RECORD.md
- docs/DOCS_AND_LOGGING_SYSTEM.md
- docs/CODEX_SPRINT_TICKETS.md

Do NOT write a long upfront plan. Do the work.

Goal (ticket-01): Make the artifact/provenance system interview-grade:
- One canonical artifact root: docs/artifacts/
- Manifest + metrics summary are coherent and portable (no machine-specific absolute temp paths as “official” artifact locations)
- A single reproducible command produces the validation pack in sample mode
- Tests + logs + docs updated per AGENTS.md and DOCS_AND_LOGGING_SYSTEM.md

Work steps (do in order):

1) Setup + branch
- Ensure working tree is clean.
- Create a feature branch: codex/ticket-01_unify-artifacts-root
- Start the run log folder:
  docs/agent_runs/${RUN_NAME}/
  - PROMPT.md (paste this prompt verbatim)
  - COMMANDS.md (append commands as you run them)
  - RESULTS.md (what changed + why + links to artifacts)
  - TESTS.md (tests/commands and key outputs)
  - META.json (git SHA before/after, env notes, config hashes)

2) Inspect current state (keep notes in RESULTS.md)
- Find ANY code/scripts/tests that write to a non-canonical artifacts path:
  - "artifacts/" (repo root), "/tmp", "/var/folders", $TMPDIR usage, hardcoded user paths
- Inspect provenance outputs:
  - docs/artifacts/manifest.json
  - docs/artifacts/metrics_summary.json + .md
  - docs/artifacts/validation_pack.zip (if present)
- Identify why manifest.json contains absolute temp paths (if it does):
  - Is reproduce_all.sh running scripts with --output/--csv into temp?
  - Are scripts defaulting to temp outputs?
  - Are tests accidentally regenerating + rewriting manifest?

3) Implement fixes (minimum surface area; prefer deterministic + portable)
- Enforce canonical artifact root:
  - Script CLIs should default outputs under docs/artifacts/ (or under docs/artifacts/<script>/...)
  - If temporary working dirs are used, copy final outputs into docs/artifacts and record ONLY the repo-relative final paths in the committed manifest.
- Make committed manifest portable:
  - Normalize recorded paths so any “official output path” is repo-relative (or under docs/artifacts).
  - If you need to retain local temp paths for debugging, store them under a clearly named field like "local_temp_paths" and ensure it is NOT committed (or is omitted when writing the canonical manifest).
- Add/upgrade a FAST guard test:
  - Fail if docs/artifacts/manifest.json contains absolute paths outside the repo (unless explicitly allowed and documented).
  - Fail if any new files are created under repo-root "artifacts/" during reproduce_all/sample runs.
  - Keep the test fast and deterministic.

4) Reproduce artifacts (sample-only) to validate end-to-end
Run the repo’s official reproducible command(s) in sample-fast mode (per PLAN_OF_RECORD / AGENTS).
Minimum expected:
- build + FAST tests
- a sample-mode reproduce-all run that generates/updates:
  - docs/artifacts/manifest.json
  - docs/artifacts/metrics_summary.json + docs/artifacts/metrics_summary.md
  - docs/artifacts/validation_pack.zip
- a minimal WRDS sample pipeline smoke run (WRDS_USE_SAMPLE=1), if applicable to the ticket acceptance.

As you run commands:
- Append each command line to docs/agent_runs/${RUN_NAME}/COMMANDS.md
- Record key stdout snippets and pass/fail to TESTS.md

5) Documentation updates (required)
- Update PROGRESS.md (always): what changed + how to reproduce + link to run log folder
- If snapshot/results changed: update project_state/CURRENT_RESULTS.md to match the committed metrics snapshot
- If you discovered/fixed a bug/risk: update project_state/KNOWN_ISSUES.md

6) Commits
- Make small logical commits (e.g., “normalize manifest paths”, “add FAST guard for manifest portability”, “refresh sample artifacts”).
- Commit message body MUST include:
  - Tests: <exact commands you ran>
  - Artifacts: <paths updated>
- Do NOT commit raw WRDS data or credentials.

7) Generate the review bundle (mandatory final step)
- Run:
  make gpt-bundle TICKET=ticket-01 RUN_NAME=${RUN_NAME}
- Record the resulting bundle path in docs/agent_runs/${RUN_NAME}/RESULTS.md

Human merge checklist (you must include this exact checklist at the bottom of RESULTS.md):
- [ ] FAST tests pass
- [ ] Sample reproduce-all run produces validation_pack.zip
- [ ] manifest.json contains no machine-specific absolute temp paths for official artifacts
- [ ] No files written under repo-root artifacts/
- [ ] PROGRESS.md + relevant project_state docs updated
- [ ] No secrets / credentials / raw WRDS committed
