# Commands

- 2026-01-25: `python3 /home/codex/.codex/skills/repo-bootstrap/scripts/bootstrap_repo.py --force`
- 2026-01-25: `cp AGENTS.md.bak.20260125_234006 AGENTS.md` (restore repo instructions)
- 2026-01-25: `cp PROGRESS.md.bak.20260125_234006 PROGRESS.md` (restore progress log)
- 2026-01-25: `cp Makefile.bak.20260125_234006 Makefile`
- 2026-01-25: `cp docs/PLAN_OF_RECORD.md.bak.20260125_234006 docs/PLAN_OF_RECORD.md`
- 2026-01-25: `cp docs/RUNBOOK.md.bak.20260125_234006 docs/RUNBOOK.md`
- 2026-01-25: `cp docs/prompts/GPT_PROMPT_{1,2,3}.md.bak.20260125_234006 docs/prompts/`
- 2026-01-25: `rm AGENTS.md.bak.20260125_234006 PROGRESS.md.bak.20260125_234006 Makefile.bak.20260125_234006 docs/PLAN_OF_RECORD.md.bak.20260125_234006 docs/RUNBOOK.md.bak.20260125_234006 docs/prompts/GPT_PROMPT_{1,2,3}.md.bak.20260125_234006 .gitignore.append`
- 2026-01-25: edited `.gitignore` to remove `docs/agent_runs/` ignore entry.
- 2026-01-25: `rm docs/NOW.md docs/TICKETS.md docs/tickets/README.md`
- 2026-01-25: `git switch -c codex/ticket-09d-closeout-metrics-ax162s`
- 2026-01-25: created `docs/tickets/ticket-09d_closeout-metrics-ax162s.md`
- 2026-01-25: created run log scaffold under `docs/agent_runs/20260125_234515_ticket-09d_closeout-metrics-ax162s/`
- 2026-01-25: `python3 tools/agentic/project_state_refresh.py --zip`
- 2026-01-25: `python3 -m venv .venv && . .venv/bin/activate && python -m pip install -r requirements-dev.txt && cmake -S . -B build -DCMAKE_BUILD_TYPE=Release -DPython3_EXECUTABLE=$PWD/.venv/bin/python3 && cmake --build build -j && PATH=$PWD/.venv/bin:$PATH ctest --test-dir build -L FAST --output-on-failure`
- 2026-01-25: `uname -a; .venv/bin/python3 --version; cmake --version | head -n 1; c++ --version | head -n 1`
- 2026-01-25: `python3 tools/agentic/gpt_bundle.py --zip --ticket ticket-09d_closeout-metrics-ax162s`
- 2026-01-25: `git show HEAD:docs/artifacts/manifest.json > docs/artifacts/manifest.json` (restore manifest after tests)
