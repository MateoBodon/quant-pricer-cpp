# Prompt
Create or update `project_state/` so that:
- A fresh GPT session can understand the repo quickly.
- The docs stay accurate and practical.

Preferred:
- Invoke skill $project-state-refresh.

Fallback:
- Run `python3 tools/agentic/project_state_refresh.py --zip`

Then:
- Ensure `project_state/` contains accurate architecture + runbook info (edit files as needed).
- Keep it high-signal: what exists, how to run, where results live, what’s broken, what’s next.

Output:
- What you updated
- The path to the created `project_state.zip`
