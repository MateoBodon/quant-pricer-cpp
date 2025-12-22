---
generated_at: 2025-12-22T19:13:19Z
git_sha: 5265c6de1a7e13f4bfc8708f188986cee30b18ed
branch: feature/ticket-00_project_state_refresh
commands:
  - date -u +%Y-%m-%dT%H:%M:%SZ
  - git rev-parse HEAD
  - git rev-parse --abbrev-ref HEAD
  - python3 -V
  - c++ --version
  - cmake --version
  - uname -a
  - rg --files
  - rg --files -g '*.py'
  - rg --files tests
  - rg -n "argparse|click|typer" scripts wrds_pipeline python tests tools
  - python3 tools/project_state_generate.py
---

# Project State Index

## How to read this folder
- Start with `project_state/ARCHITECTURE.md` for the system map and core components.
- Use `project_state/MODULE_SUMMARIES.md` and `project_state/FUNCTION_INDEX.md` for APIs and symbol inventory.
- Check `project_state/PIPELINE_FLOW.md` and `project_state/DATAFLOW.md` for build/test/artifact flows.
- Consult `project_state/CURRENT_RESULTS.md`, `project_state/KNOWN_ISSUES.md`, and `project_state/OPEN_QUESTIONS.md` before quoting results.
- Generated machine indices live under `project_state/_generated/`.

## Contents
- `project_state/ARCHITECTURE.md` — high-level system architecture (C++ core, CLI, Python, WRDS pipeline).
- `project_state/MODULE_SUMMARIES.md` — module inventory + summaries (C++ headers/sources + Python modules).
- `project_state/FUNCTION_INDEX.md` — AST-derived Python functions/classes + C++ API highlights.
- `project_state/DEPENDENCY_GRAPH.md` — Python internal import graph + C++ dependency notes.
- `project_state/PIPELINE_FLOW.md` — build/test/repro pipelines and CLI entrypoints.
- `project_state/DATAFLOW.md` — data lineage from inputs to artifacts.
- `project_state/EXPERIMENTS.md` — experiments and artifact-producing scripts.
- `project_state/CURRENT_RESULTS.md` — latest artifact snapshot and status (from committed metrics summary).
- `project_state/RESEARCH_NOTES.md` — research/validation notes from docs.
- `project_state/OPEN_QUESTIONS.md` — unresolved items/ambiguities.
- `project_state/KNOWN_ISSUES.md` — known gaps and constraints.
- `project_state/ROADMAP.md` — condensed roadmap (from `ROADMAP (1).md`).
- `project_state/CONFIG_REFERENCE.md` — config files, env vars, build flags.
- `project_state/SERVER_ENVIRONMENT.md` — environment snapshot used for generation.
- `project_state/TEST_COVERAGE.md` — test suites and coverage notes.
- `project_state/STYLE_GUIDE.md` — coding conventions and repo style.
- `project_state/CHANGELOG.md` — project changelog summary.

## Generated data
- `project_state/_generated/repo_inventory.json` — file list + roles + sizes.
- `project_state/_generated/symbol_index.json` — AST-derived Python symbols.
- `project_state/_generated/import_graph.json` — internal Python import adjacency.
- `project_state/_generated/make_targets.txt` — Makefile targets.
