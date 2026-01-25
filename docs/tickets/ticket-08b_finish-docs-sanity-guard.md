# ticket-08b_finish-docs-sanity-guard

## Goal
Finish ticket-08 cleanly: commit runbooks/backlog + docs_sanity_fast, revert scope creep
(artifacts/run-log rewrites), and get FAST tests green.

## Scope
- Revert unintended edits in `docs/artifacts/*`, `project_state/CURRENT_RESULTS.md`,
  `project_state/KNOWN_ISSUES.md`, and historical `docs/agent_runs/**`.
- Keep PROGRESS conflict cleanup and update runbooks/backlog.
- Add `tests/test_docs_sanity_fast.py`, register it with CTest FAST, and ensure
  docs_sanity_fast scans tracked `.md` for conflict markers + template scaffolding.
- Update `.gitignore` to avoid ignoring `docs/agent_runs/`.
- Create a new run log for this ticket.

## Acceptance Criteria
- `git status --porcelain` is empty after commit.
- `PROGRESS.md` contains no conflict markers or `HHMMSS` placeholders.
- `docs/RUNBOOK.md` and `project_state/RUNBOOK.md` are tracked and contain canonical
  build/test/repro/WRDS sample commands.
- `project_state/BACKLOG.md` is tracked with 5-10 ranked concrete items.
- `tests/test_docs_sanity_fast.py` is tracked and registered in CTest FAST.
- No changes remain in `docs/artifacts/` or historical `docs/agent_runs/**`
  beyond what existed pre-ticket.
- `ctest --test-dir build -L FAST --output-on-failure` passes.

## Plan
1. Revert scope creep in artifacts, project_state, and historical run logs; delete
   `.bak`/`.append` leftovers.
2. Update docs sanity test + CTest registration; adjust runbooks/backlog and PROGRESS.
3. Create run log, run FAST tests, and generate the GPT bundle.

## Notes
- Test command: `cmake -S . -B build -DCMAKE_BUILD_TYPE=Release && cmake --build build -j && ctest --test-dir build -L FAST --output-on-failure && ctest --test-dir build -R docs_sanity_fast --output-on-failure`.
