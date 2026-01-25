# Prompt

Ticket: ticket-09d_closeout-metrics-ax162s

Goal: Close out ticket-09 by committing the missing run log + GPT bundle and aligning sprint status with PROGRESS/CURRENT_RESULTS, with a clean git tree.

Scope/constraints:
- Do not change pricing/math code; do not change docs/artifacts unless re-running is necessary to regenerate truthful run logs.
- Add docs/agent_runs/20260125_205850_ticket-09_refresh-metrics-ax162s/{PROMPT,COMMANDS,RESULTS,TESTS,META}.md/json.
- Add existing ticket-09 bundle zip under docs/gpt_bundles/.
- Update docs/CODEX_SPRINT_TICKETS.md to DONE.
- Ensure git status clean.

Acceptance criteria:
- Run log folder exists with required files.
- docs/CODEX_SPRINT_TICKETS marks ticket-09 DONE.
- ticket-09 GPT bundle zip committed under docs/gpt_bundles.
- PROGRESS run-log path is valid.
- git status --porcelain is clean.
- FAST tests pass.

Test command:
python3 -m venv .venv && . .venv/bin/activate && python -m pip install -r requirements-dev.txt && cmake -S . -B build -DCMAKE_BUILD_TYPE=Release -DPython3_EXECUTABLE=$PWD/.venv/bin/python3 && cmake --build build -j && PATH=$PWD/.venv/bin:$PATH ctest --test-dir build -L FAST --output-on-failure
