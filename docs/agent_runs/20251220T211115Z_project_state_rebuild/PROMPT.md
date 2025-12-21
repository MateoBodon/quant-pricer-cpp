# Prompt

Rebuild `project_state/` to be self-describing for humans and GPT-5.2 Pro.

Key requirements (abridged):
- Generate `project_state/` docs (19 markdown files + `_generated` JSON/make targets).
- Use AST parsing for Python symbols and import graph.
- Include metadata header (timestamp, git SHA, branch, commands) in every doc.
- Avoid deep parsing of huge/excluded dirs; summarize where applicable.
- Create run log under `docs/agent_runs/<timestamp>_project_state_rebuild/`.
- Create bundle zip under `docs/gpt_bundles/` with `project_state/` and related docs.
- Update/create `PROGRESS.md` with entry referencing the zip.
- Commit on branch `chore/project_state_refresh` with message “Rebuild project_state @ <shortsha>”.
