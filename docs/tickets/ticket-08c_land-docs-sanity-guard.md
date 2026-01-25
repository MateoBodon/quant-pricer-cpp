# ticket-08c_land-docs-sanity-guard

## Goal
Land ticket-08b cleanly: keep docs sanity guard + runbooks/backlog/runlog tracked,
keep artifacts untouched, and verify FAST is green.

## Scope
- Keep `CMakeLists.txt` docs_sanity_fast registration and `tests/test_docs_sanity_fast.py`.
- Ensure `docs/RUNBOOK.md`, `project_state/RUNBOOK.md`, and
  `project_state/BACKLOG.md` are tracked with real content.
- Keep ticket-08b run log folder under
  `docs/agent_runs/20260125_000055_ticket-08b_finish-docs-sanity-guard/`.
- Revert `docs/artifacts/manifest.json` and `docs/artifacts/metrics_summary.{md,json}`
  to match main (no artifact refresh).
- Add run log + progress updates for this ticket.

## Acceptance Criteria
- No changes remain under `docs/artifacts/`.
- `tests/test_docs_sanity_fast.py` is tracked and registered as a FAST CTest.
- `docs/RUNBOOK.md`, `project_state/RUNBOOK.md`, and `project_state/BACKLOG.md`
  are tracked and non-template.
- ticket-08b run log folder is tracked.
- `git status --porcelain` is empty after commit.
- `ctest --test-dir build -L FAST --output-on-failure` and
  `ctest --test-dir build -R docs_sanity_fast --output-on-failure` pass.

## Plan
1. Confirm no artifact diffs; keep `docs/artifacts/*` untouched.
2. Add ticket doc `docs/tickets/ticket-08c_land-docs-sanity-guard.md` and
   run log files under `docs/agent_runs/20260125_201700_ticket-08c_land-docs-sanity-guard/`.
3. Update `PROGRESS.md` Done section.
4. Run build + FAST tests (CMake + `ctest`).
5. Generate the GPT bundle for ticket-08c.

## Notes
- Test command: `cmake -S . -B build -DCMAKE_BUILD_TYPE=Release && cmake --build build -j && ctest --test-dir build -L FAST --output-on-failure && ctest --test-dir build -R docs_sanity_fast --output-on-failure`.
