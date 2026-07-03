# docs/DOCS_AND_LOGGING_SYSTEM.md — Self-auditing protocol

This repo is only “quant-interview-grade” if it is self-auditing: every result has provenance, every change has tests, and the docs never drift from reality.

---

## 1) Directory layout (source of truth)

### Prompts + outputs (human- and agent-facing)
- `docs/prompts/`
  - Immutable prompts used for Codex runs (one file per ticket/run prompt).
- `docs/gpt_outputs/`
  - Immutable GPT (ChatGPT) analysis outputs and audits (like Prompt-1, Prompt-2 outputs).

### Agent run logs (Codex execution records)
- `docs/agent_runs/<RUN_NAME>/`
  - One folder per Codex run. This is the auditable “lab notebook.”

### Artifacts (results evidence)
- `docs/artifacts/`
  - Canonical artifact root for plots/tables/metrics.
  - Must include:
    - `manifest.json` (provenance)
    - `metrics_summary.md` and `metrics_summary.json` (headline metrics + status)
- `docs/validation_pack.zip`
  - Bundled evidence for reviewers (artifacts + manifest + config hashes).

---

## 2) Run naming convention (required)

**RUN_NAME format (UTC date + time + ticket id + slug):**
Examples:
- `20251222_194500_ticket-01_unify-artifacts`
- `20251223_091200_ticket-03_wrds-asof-checks`

---

## 3) Required contents per run (must exist for every Codex run)

Inside `docs/agent_runs/<RUN_NAME>/`, create:

1) `PROMPT.md`
- Exact prompt text used (copy/paste), including ticket id and acceptance criteria.

2) `COMMANDS.md`
- Every command executed, **in order**, with notes on why.
- Include environment variables used (redact secrets).

3) `RESULTS.md`
- What changed, what passed/failed, what metrics moved.
- Link to artifacts under `docs/artifacts/...`.
- If results are unchanged, say so explicitly.

4) `TESTS.md`
- Tests/commands executed and their outcomes (pass/fail).
- Include any key failure output (truncated) and how it was resolved.

5) `META.json`
- Required fields:
  - `run_name`
  - `ticket_id`
  - `started_at_utc` / `finished_at_utc`
  - `git_sha_before` / `git_sha_after`
  - `branch_name`
  - `host_os` / `compiler` / `python_version`
  - `build_type` (Debug/Release)
  - `dataset_id` (e.g., `WRDS_SAMPLE`, `WRDS_LIVE_<panel>`, etc.)
  - `config_hashes` (scenario grid, tolerances, wrds panel config)
  - `tools` (Codex CLI version if available)
- Never store secrets in META.json.

Optional but recommended:
- `SOURCES.md` (if web research was used): list URLs + what you used them for; treat as untrusted.

---

## 4) Living docs update policy (when to update what)

### Always update
- `PROGRESS.md`
  - Every run must add a dated entry: what changed, tests run, artifacts updated.

### Update when results change
- `project_state/CURRENT_RESULTS.md`
  - Update only when headline metrics/artifacts change.
  - Must link to artifact paths under `docs/artifacts/`.

### Update when risks/bugs change
- `project_state/KNOWN_ISSUES.md`
  - If a bug/risk is discovered, add it the same day.
  - If resolved, mark resolved with reference to the run log folder and commit SHA.

### Update when user-visible behavior changes
- `CHANGELOG.md`
  - Any CLI behavior change, config change, or public API change requires a changelog entry.

---

## 5) Stop-the-line rules for documentation
- If evaluation validity is in doubt (lookahead/leakage/survivorship), **do not** publish or headline metrics.
- If artifacts are not reproducible, **do not** update CURRENT_RESULTS with “good-looking” numbers.
- If a script writes outside `docs/artifacts/` during the official pipeline, treat as a failure.

---

## 6) What “done” means for a ticket
A ticket is done only when:
- Code changes are merged on a feature branch with tests run
- Artifacts were regenerated if relevant
- Run logs exist under `docs/agent_runs/<RUN_NAME>/` with all required files
- PROGRESS.md updated
- CURRENT_RESULTS / KNOWN_ISSUES / CHANGELOG updated if applicable

---
