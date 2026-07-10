# T-000 - Install AI Project OS v2

## Status

review-ready

## Owner Flow

Pro planned -> Heavy dispatches -> Codex executes -> Heavy reviews -> Pro recenter if needed.

## Goal

Install AI Project OS v2 in this repo, preserve old process/state docs, create a clean canonical documentation system, and generate the first Project State Audit Bundle plus T-000 Review Bundle.

## Scope

In scope:

- Inspect and classify existing docs, run logs, bundles, reports, tickets, and state artifacts.
- Archive/index pre-v2 docs under `docs/_archive/pre_ai_os_v2/20260703/`.
- Add/update canonical v2 docs and project_state docs.
- Add reusable bundle/archive tooling.
- Generate required bundles under `reports/_bundles/`.
- Record commands and validation under `reports/_runs/`.

Out of scope:

- Product behavior changes.
- Numerical model changes.
- Artifact metric refresh unless required for validation.
- Raw/live data movement.

## Acceptance Criteria

- Canonical docs exist at the paths specified by the T-000 work order.
- Old docs are not deleted or hidden.
- Archive index and manifest explain classifications and migrations.
- Project State Audit Bundle includes state summary, file purpose index, artifact/result index, validation baseline, docs index, git state, recent progress, archive index, canonical docs, and selected source/test/config files.
- T-000 Review Bundle includes prompt, changed files, diff/patch, git status, run log, commands, validation, archive index/manifest, summary, and residual risks.
- Fast meaningful validation is run and recorded.

## Validation

Expected T-000 checks:

```bash
git status --short
python3 -m compileall tools/agentic/ai_os_bundle.py
python3 scripts/check_data_policy.py
cmake -S . -B build -DCMAKE_BUILD_TYPE=Release
cmake --build build -j
ctest --test-dir build -L FAST --output-on-failure
python3 tools/agentic/ai_os_bundle.py project-state ...
python3 tools/agentic/ai_os_bundle.py review-t000 ...
```

## Review Artifacts

- `reports/_runs/<timestamp>_T-000_install_ai_project_os_v2/`
- `reports/_bundles/<timestamp>_quant-pricer-cpp_project-state_initial.zip`
- `reports/_bundles/<timestamp>_quant-pricer-cpp_review_T-000.zip`
- `docs/_archive/pre_ai_os_v2/20260703/ARCHIVE_INDEX.md`
- `docs/_archive/pre_ai_os_v2/20260703/ARCHIVE_MANIFEST.json`
