You are Codex working on quant-pricer-cpp.

READ FIRST (binding):
1) AGENTS.md
2) docs/PLAN_OF_RECORD.md
3) docs/DOCS_AND_LOGGING_SYSTEM.md
4) docs/CODEX_SPRINT_TICKETS.md

Ticket: ticket-07b — Data policy guard: make it real + mergeable

Goal
- Fix Ticket-07 so it is actually mergeable and defensible:
  - Ensure `scripts/check_data_policy.py` and `tests/test_data_policy_fast.py` are git-tracked and committed.
  - Ensure the policy cannot be bypassed by simply renaming columns (e.g., best_bid→bid).
  - Ensure FAST is green in the recorded run.
  - Produce a correct run log folder and a new bundle at the end.

Do NOT write a long plan. Do the work. Keep changes minimal and auditable.

Step 0 — Setup the run log
- Define:
  - TICKET=ticket-07b
  - RUN_NAME="$(date -u +%Y%m%d_%H%M%S)_ticket-07b_data-policy-guard-fix"
- Create: docs/agent_runs/${RUN_NAME}/
- Start docs/agent_runs/${RUN_NAME}/PROMPT.md with the exact prompt text (this message).

Step 1 — Inspect what happened in Ticket-07
- Read docs/agent_runs/20251222_044808_ticket-07_data-policy-guard/{RESULTS.md,TESTS.md,COMMANDS.md,META.json}
- Check whether these files exist in the repo and are tracked:
  - scripts/check_data_policy.py
  - tests/test_data_policy_fast.py
  - artifacts/heston/README* (if claimed)
- Run:
  - git status --porcelain
  - git ls-files scripts/check_data_policy.py tests/test_data_policy_fast.py || true
Record outputs in docs/agent_runs/${RUN_NAME}/RESULTS.md (short).

Step 2 — Implement fixes (minimal)
A) Make the guard + FAST test real (tracked)
- If missing or untracked, add/commit:
  - scripts/check_data_policy.py
  - tests/test_data_policy_fast.py
- Guard requirements:
  - Scan git-tracked files (use `git ls-files -z` to handle spaces).
  - Enforce restricted patterns at minimum:
    - `strike,.*market_iv`
    - `\bsecid\b`
    - `best_bid|best_ask|best_offer`
  - Only fail on *data/artifact* file extensions (.csv/.parquet/.json). Do NOT fail on code/docs.
  - On failure: print offending file paths + matching lines; exit non-zero.

B) Remove / fix the bypassable sample data situation
- Treat `wrds_pipeline/sample_data/spx_options_sample.csv` as potentially non-redistributable.
- Replace it with an explicitly SYNTHETIC sample (small) that preserves schema used by loaders, OR remove it and update sample-mode pipeline accordingly.
- Make the sample file self-identifying:
  - Add a first line comment like `# SYNTHETIC_DATA ...`
  - Update the loader to skip comment lines (e.g., pandas read_csv(comment="#") or manual skip).
- Update `scripts/check_data_policy.py` to enforce:
  - Any tracked CSV under `wrds_pipeline/sample_data/` MUST include the `# SYNTHETIC_DATA` marker (else fail).
  - This prevents “rename columns and keep real quotes” bypass.

C) Fix FAST failures due to missing matplotlib
- Find where Python dev/test deps are declared (requirements.txt / pyproject.toml / docs).
- Add `matplotlib` to the appropriate dev/test dependency list so FAST tests don’t fail with ModuleNotFoundError.
- If dependency management is not present, add the minimal file and document install in AGENTS.md / docs as appropriate.

Step 3 — Run the minimal sufficient tests (must be green)
Record every command (and key output) in docs/agent_runs/${RUN_NAME}/TESTS.md.

Minimum:
- python3 -m compileall scripts/check_data_policy.py tests/test_data_policy_fast.py
- python3 scripts/check_data_policy.py
- Configure/build if needed:
  - cmake -S . -B build -DCMAKE_BUILD_TYPE=Release
- FAST:
  - ctest --test-dir build -L FAST --output-on-failure

Real-data (no-credentials) smoke (must run):
- WRDS_USE_SAMPLE=1 python3 -m wrds_pipeline.pipeline --fast
  - Confirm it uses sample mode and does not access WRDS.

Step 4 — Update docs
- Update PROGRESS.md: mark Ticket-07 as FAIL (brief reason) and Ticket-07b as DONE with what changed.
- Update project_state/KNOWN_ISSUES.md: document the data policy guard + synthetic sample rule.
- If docs/CODEX_SPRINT_TICKETS.md exists, add Ticket-07b with acceptance criteria (objective).

Step 5 — Run log completeness
Write:
- docs/agent_runs/${RUN_NAME}/COMMANDS.md (commands executed, in order)
- docs/agent_runs/${RUN_NAME}/RESULTS.md (what changed + why + links to artifacts if any)
- docs/agent_runs/${RUN_NAME}/TESTS.md (tests + key outputs)
- docs/agent_runs/${RUN_NAME}/META.json with:
  - git_sha_before, git_sha_after
  - branch_before, branch_after
  - timestamp_local
  - dataset_id ("sample")
  - config_hash (if applicable)

Step 6 — Commit on a feature branch
- Create branch: feature/ticket-07b_data-policy-guard-fix
- Ensure `git status` is clean.
- Commit message: `ticket-07b: data policy guard mergeable + synthetic sample`
- Commit body MUST include:
  - Tests: <list the exact commands you ran>

Step 7 — Generate the next bundle
- make gpt-bundle TICKET=ticket-07b RUN_NAME=${RUN_NAME}
- Record the bundle path in docs/agent_runs/${RUN_NAME}/RESULTS.md

Suggested Codex invocation (safe mode; approvals on):
- codex --sandbox workspace-write --ask-for-approval on-request

Human merge checklist (include in RESULTS.md too):
- New guard + test files are tracked and appear in git diff
- No WRDS/raw market data committed
- FAST is green
- Sample-mode pipeline smoke succeeded
- Run log folder complete
- Bundle contains required items and correct SHAs
