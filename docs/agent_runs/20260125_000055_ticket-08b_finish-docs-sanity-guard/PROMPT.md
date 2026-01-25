# PROMPT

Ticket: ticket-08b_finish-docs-sanity-guard
Goal: Finish ticket-08 cleanly (runbooks/backlog + docs_sanity_fast), revert scope creep
(artifacts/run-log rewrites), and get FAST tests green.

Scope/constraints:
- Revert unintended edits in docs/artifacts/*, project_state/CURRENT_RESULTS.md,
  project_state/KNOWN_ISSUES.md, and historical docs/agent_runs/**.
- Keep only PROGRESS.md conflict cleanup + minimal runbook/backlog edits.
- Add tests/test_docs_sanity_fast.py, docs/RUNBOOK.md, project_state/RUNBOOK.md,
  project_state/BACKLOG.md; fix .gitignore to not ignore docs/agent_runs.
- Ensure docs_sanity_fast scans tracked .md for conflict markers + template scaffolding,
  optionally banning HHMMSS only in PROGRESS/runbooks.
- Delete or leave untracked .bak/.append files.
- Create a new run log for this ticket if required.

Acceptance criteria:
- git status clean after commit; PROGRESS has no conflict markers or HHMMSS placeholders.
- Runbooks tracked with canonical commands; BACKLOG tracked with ranked items.
- docs_sanity_fast tracked and registered in CTest FAST.
- No changes remain in docs/artifacts/ or historical docs/agent_runs/**.
- ctest -L FAST passes.

Test command:
- cmake -S . -B build -DCMAKE_BUILD_TYPE=Release && cmake --build build -j
  && ctest --test-dir build -L FAST --output-on-failure
  && ctest --test-dir build -R docs_sanity_fast --output-on-failure
