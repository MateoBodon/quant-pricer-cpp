#!/usr/bin/env python3
"""AI Project OS v2 archive and bundle helper.

This tool is intentionally small and repo-local. It creates:
- a pre-AI-OS-v2 archive index/manifest without moving source files;
- a Project State Audit Bundle for Pro/strategy review;
- a compact ticket review bundle for T-000.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import subprocess
import sys
import tempfile
import zipfile
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


REPO_NAME = "quant-pricer-cpp"

TEXT_SUFFIXES = {
    ".cmake",
    ".conf",
    ".cfg",
    ".cff",
    ".cpp",
    ".csv",
    ".h",
    ".hpp",
    ".in",
    ".json",
    ".md",
    ".py",
    ".rst",
    ".sh",
    ".txt",
    ".yaml",
    ".yml",
}

ARCHIVE_COPY_PATHS = [
    "PROJECT.md",
    "AGENTS.md",
    "PROGRESS.md",
    "TRACKING_POLICY.md",
    "ROADMAP (1).md",
    ".agent/execplans/2025-12-18_metrics_snapshot_single_source_of_truth.md",
    "docs/CODEX_SPRINT_TICKETS.md",
    "docs/DECISIONS.md",
    "docs/DOCS_AND_LOGGING_SYSTEM.md",
    "docs/NOW.md",
    "docs/PLAN_OF_RECORD.md",
    "docs/RUNBOOK.md",
    "docs/TICKETS.md",
    "docs/WORKLOG.md",
    "docs/history_cleanup_plan.md",
    "docs/agent_runs/README.md",
    "docs/tickets/README.md",
]

PRODUCT_DOCS = [
    "README.md",
    "CHANGELOG.md",
    "CONTRIBUTING.md",
    "CITATION.cff",
    "LICENSE",
    "docs/Design.md",
    "docs/Greeks.md",
    "docs/Results.md",
    "docs/Validation.md",
    "docs/ValidationHighlights.md",
    "docs/WRDS_Results.md",
    "docs/api/index.md",
    "data/README.md",
    "docs/artifacts/README.md",
]

CANONICAL_DOCS = [
    "PROJECT.md",
    "AGENTS.md",
    "PROGRESS.md",
    "docs/strategy/GOAL_CONTEXT.md",
    "docs/strategy/STRATEGIC_OVERVIEW.md",
    "docs/strategy/PLAN_OF_RECORD.md",
    "docs/strategy/DECISIONS.md",
    "docs/strategy/RISK_REGISTER.md",
    "docs/strategy/TICKET_LEDGER.md",
    "docs/strategy/CODEX_GOALS.md",
    "docs/strategy/CONTEXT_CARRYOVER.md",
    "docs/tickets/T-000_install_ai_project_os_v2.md",
    "docs/tickets/TEMPLATE_codex_ticket.md",
    "project_state/STATE_INDEX.md",
    "project_state/RUNBOOK.md",
    "project_state/VALIDATION_MATRIX.md",
    "project_state/CLAIMS_AND_EVIDENCE.md",
]

SELECTED_CONFIGS = [
    ".github/workflows/ci.yml",
    ".github/workflows/docs-pages.yml",
    ".github/workflows/nightly.yml",
    ".github/workflows/release.yml",
    ".github/workflows/wheels.yml",
    ".clang-format",
    ".clang-tidy",
    ".gitignore",
    ".gitmodules",
    ".pre-commit-config.yaml",
    "CMakeLists.txt",
    "Makefile",
    "Doxyfile",
    "pyproject.toml",
    "setup.cfg",
    "requirements-dev.txt",
    "requirements-artifacts.txt",
    "vcpkg.json",
    "conanfile.py",
    "configs/scenario_grids/synthetic_validation_v1.json",
    "configs/tolerances/synthetic_validation_v1.json",
    "wrds_pipeline_dates_panel.yaml",
    "wrds_pipeline_dates_panel_resume_v2.yaml",
    "TRACKING_POLICY.md",
]

SELECTED_ARTIFACT_DOCS = [
    "docs/artifacts/manifest.json",
    "docs/artifacts/metrics_summary.md",
    "docs/artifacts/metrics_summary.json",
]


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def run(cmd: list[str], cwd: Path) -> tuple[int, str]:
    try:
        out = subprocess.check_output(cmd, cwd=str(cwd), stderr=subprocess.STDOUT)
        return 0, out.decode("utf-8", errors="replace")
    except subprocess.CalledProcessError as exc:
        return exc.returncode, exc.output.decode("utf-8", errors="replace")


def git_root(start: Path) -> Path:
    code, out = run(["git", "rev-parse", "--show-toplevel"], start)
    if code != 0:
        raise SystemExit(f"not a git repository: {start}")
    return Path(out.strip())


def rel(path: Path, repo: Path) -> str:
    return path.relative_to(repo).as_posix()


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def file_size(path: Path) -> int:
    try:
        return path.stat().st_size
    except OSError:
        return 0


def is_text_like(path: Path) -> bool:
    return path.suffix.lower() in TEXT_SUFFIXES or path.name in {"Makefile", "Doxyfile", "LICENSE"}


def safe_copy(src: Path, dst: Path) -> None:
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, dst)


def archive_entry(
    repo: Path,
    original: str,
    classification: str,
    description: str,
    reason: str,
    archived_path: str | None = None,
    action: str = "indexed",
    migrated_to: str | None = None,
    useful_historical_context: bool = True,
) -> dict[str, Any]:
    p = repo / original
    entry = {
        "original_path": original,
        "archived_path": archived_path,
        "title_or_description": description,
        "classification": classification,
        "action": action,
        "reason": reason,
        "migrated_to": migrated_to,
        "may_contain_useful_historical_context": useful_historical_context,
        "size_bytes": file_size(p) if p.exists() else None,
        "sha256": sha256_file(p) if p.exists() and p.is_file() else None,
    }
    return entry


def discover_process_files(repo: Path) -> list[str]:
    found: set[str] = set()
    for raw in ARCHIVE_COPY_PATHS:
        if (repo / raw).exists():
            found.add(raw)
    for pattern in ("project_state/*.md", "docs/tickets/*.md"):
        for p in repo.glob(pattern):
            if p.is_file():
                found.add(rel(p, repo))
    return sorted(found)


def build_archive(repo: Path, date: str) -> Path:
    archive_root = repo / "docs" / "_archive" / "pre_ai_os_v2" / date
    files_root = archive_root / "files"
    archive_root.mkdir(parents=True, exist_ok=True)

    entries: list[dict[str, Any]] = []
    for raw in discover_process_files(repo):
        src = repo / raw
        dst = files_root / raw
        safe_copy(src, dst)
        migrated_to = None
        if raw == "PROJECT.md":
            migrated_to = "PROJECT.md"
        elif raw == "AGENTS.md":
            migrated_to = "AGENTS.md"
        elif raw == "PROGRESS.md":
            migrated_to = "PROGRESS.md"
        elif raw.startswith("project_state/RUNBOOK.md"):
            migrated_to = "project_state/RUNBOOK.md"
        elif raw.startswith("docs/DECISIONS.md"):
            migrated_to = "docs/strategy/DECISIONS.md"
        elif raw.startswith("docs/PLAN_OF_RECORD.md"):
            migrated_to = "docs/strategy/PLAN_OF_RECORD.md"
        elif raw.startswith("docs/CODEX_SPRINT_TICKETS.md") or raw.startswith("docs/TICKETS.md"):
            migrated_to = "docs/strategy/TICKET_LEDGER.md"
        entries.append(
            archive_entry(
                repo=repo,
                original=raw,
                archived_path=(archive_root / "files" / raw).relative_to(repo).as_posix(),
                classification="useful historical",
                description=describe_path(raw),
                reason="Pre-AI-OS-v2 process/state document copied before canonical v2 installation.",
                action="copied",
                migrated_to=migrated_to,
                useful_historical_context=True,
            )
        )

    for raw in PRODUCT_DOCS:
        if not (repo / raw).exists():
            continue
        entries.append(
            archive_entry(
                repo=repo,
                original=raw,
                classification="canonical/current",
                description=describe_path(raw),
                reason="Product-facing or release-facing document remains active and was not archived as superseded.",
                action="preserved in place",
                useful_historical_context=True,
            )
        )

    for run_dir in sorted((repo / "docs" / "agent_runs").glob("*")):
        if not run_dir.is_dir():
            continue
        entries.append(
            archive_entry(
                repo=repo,
                original=rel(run_dir, repo),
                classification="useful historical",
                description=f"Historical Codex/agent run log: {run_dir.name}",
                reason="Run-log directory is already accessible in place; indexed rather than duplicated.",
                action="preserved in place",
                useful_historical_context=True,
            )
        )

    large_dirs = [
        ("docs/artifacts", "large artifacts", "Curated result artifacts; indexed by path/size/hash and left active."),
        ("docs/coverage", "generated/redundant/stale", "Generated coverage HTML; useful for inspection but not current planning truth."),
        ("artifacts/_local", "large artifacts", "Ignored local/scratch WRDS and bundle outputs; should not be treated as canonical."),
        ("build", "large artifacts", "Generated CMake build tree; excluded from docs/archive copies."),
        (".venv", "large artifacts", "Local Python virtual environment; excluded from docs/archive copies."),
        ("external", "do-not-touch", "Vendored/submodule dependencies required by the build."),
    ]
    for raw, classification, reason in large_dirs:
        p = repo / raw
        if not p.exists():
            continue
        entries.append(
            archive_entry(
                repo=repo,
                original=raw,
                classification=classification,
                description=describe_path(raw),
                reason=reason,
                action="indexed only",
                useful_historical_context=classification != "do-not-touch",
            )
        )

    manifest = {
        "schema_version": "ai-project-os-v2-archive-manifest-1",
        "created_at_utc": utc_now(),
        "archive_root": rel(archive_root, repo),
        "policy": {
            "deleted_files": [],
            "moved_files": [],
            "copy_strategy": "Copy key pre-v2 process docs; index large/generated/history areas in place.",
        },
        "entry_count": len(entries),
        "entries": entries,
    }
    (archive_root / "ARCHIVE_MANIFEST.json").write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    (archive_root / "ARCHIVE_INDEX.md").write_text(render_archive_index(manifest), encoding="utf-8")
    return archive_root


def describe_path(path: str) -> str:
    names = {
        "PROJECT.md": "Pre-v2 root project profile placeholder",
        "AGENTS.md": "Repo-specific agent rules and validation expectations",
        "PROGRESS.md": "Chronological project progress log",
        "TRACKING_POLICY.md": "Repo output tracking and data policy",
        "ROADMAP (1).md": "Existing roadmap source with nonstandard filename",
        "docs/CODEX_SPRINT_TICKETS.md": "Pre-v2 sprint ticket queue",
        "docs/DECISIONS.md": "Pre-v2 decision log",
        "docs/DOCS_AND_LOGGING_SYSTEM.md": "Pre-v2 docs/run-log protocol",
        "docs/NOW.md": "Pre-v2 current focus page",
        "docs/PLAN_OF_RECORD.md": "Pre-v2 plan of record and evaluation protocol",
        "docs/RUNBOOK.md": "Pre-v2 operational runbook",
        "docs/TICKETS.md": "Pre-v2 ticket index",
        "docs/WORKLOG.md": "Historical worklog",
        "docs/history_cleanup_plan.md": "Draft plan for possible history rewrite",
        "docs/artifacts": "Curated validation/result artifacts",
        "docs/coverage": "Generated coverage HTML",
        "artifacts/_local": "Ignored local/scratch artifacts",
        "build": "Generated build tree",
        ".venv": "Local virtual environment",
        "external": "External dependencies/submodules",
    }
    if path in names:
        return names[path]
    if path.startswith("project_state/"):
        return "Pre-v2 project_state memory document"
    if path.startswith("docs/tickets/"):
        return "Historical ticket document"
    return path


def render_archive_index(manifest: dict[str, Any]) -> str:
    counts = Counter(entry["classification"] for entry in manifest["entries"])
    lines = [
        "# Pre-AI-OS-v2 Archive Index",
        "",
        f"Created UTC: {manifest['created_at_utc']}",
        f"Archive root: `{manifest['archive_root']}`",
        "",
        "## Summary",
        "",
    ]
    for key in sorted(counts):
        lines.append(f"- {key}: {counts[key]}")
    lines.extend(
        [
            "",
            "No files were deleted or moved. Key pre-v2 process/state docs were copied into this archive; active product docs, run logs, generated artifacts, dependencies, and build outputs remain in place and are indexed here.",
            "",
            "## Entries",
            "",
            "| Original path | Archived path | Classification | Migrated to | Reason | Useful historical context |",
            "|---|---|---|---|---|---|",
        ]
    )
    for entry in manifest["entries"]:
        lines.append(
            "| {original} | {archived} | {classification} | {migrated} | {reason} | {useful} |".format(
                original=f"`{entry['original_path']}`",
                archived=f"`{entry['archived_path']}`" if entry["archived_path"] else "",
                classification=entry["classification"],
                migrated=f"`{entry['migrated_to']}`" if entry["migrated_to"] else "",
                reason=entry["reason"].replace("|", "/"),
                useful="yes" if entry["may_contain_useful_historical_context"] else "no",
            )
        )
    lines.append("")
    return "\n".join(lines)


def git_info(repo: Path) -> dict[str, Any]:
    _, sha = run(["git", "rev-parse", "HEAD"], repo)
    _, branch = run(["git", "branch", "--show-current"], repo)
    _, status = run(["git", "status", "--short"], repo)
    _, log = run(["git", "log", "--oneline", "-12"], repo)
    return {
        "sha": sha.strip(),
        "branch": branch.strip(),
        "dirty": bool(status.strip()),
        "status_short": status.rstrip(),
        "recent_log": log.rstrip(),
    }


def copy_into_stage(
    repo: Path,
    stage: Path,
    source_rel: str,
    dest_prefix: str,
    included: list[dict[str, Any]],
    purpose: str,
    max_bytes: int = 300_000,
) -> None:
    src = repo / source_rel
    if not src.exists() or not src.is_file():
        return
    if file_size(src) > max_bytes:
        return
    dst = stage / dest_prefix / source_rel
    safe_copy(src, dst)
    included.append(
        {
            "path": f"{dest_prefix}/{source_rel}",
            "source_path": source_rel,
            "purpose": purpose,
            "source": "repo",
            "size_bytes": file_size(src),
            "sha256": sha256_file(src),
        }
    )


def write_stage_file(
    stage: Path,
    rel_path: str,
    content: str,
    included: list[dict[str, Any]],
    purpose: str,
    source: str = "generated",
) -> None:
    dst = stage / rel_path
    dst.parent.mkdir(parents=True, exist_ok=True)
    dst.write_text(content, encoding="utf-8")
    included.append(
        {
            "path": rel_path,
            "source_path": None,
            "purpose": purpose,
            "source": source,
            "size_bytes": file_size(dst),
            "sha256": sha256_file(dst),
        }
    )


def zip_stage(stage: Path, out_zip: Path) -> None:
    out_zip.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(out_zip, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        for p in sorted(stage.rglob("*")):
            if p.is_file():
                zf.write(p, p.relative_to(stage).as_posix())


def artifact_rows(repo: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    roots = [repo / "docs" / "artifacts", repo / "artifacts" / "_local"]
    for root in roots:
        if not root.exists():
            continue
        for p in sorted(root.rglob("*")):
            if not p.is_file():
                continue
            path = rel(p, repo)
            status = "current curated" if path.startswith("docs/artifacts/") else "local scratch"
            rows.append(
                {
                    "path": path,
                    "status": status,
                    "size_bytes": file_size(p),
                    "sha256": sha256_file(p),
                    "include_in_state_bundle": path in SELECTED_ARTIFACT_DOCS,
                }
            )
    return rows


def excluded_large_artifacts(repo: Path) -> list[dict[str, Any]]:
    items: list[dict[str, Any]] = []
    for raw, reason in [
        (".venv", "local virtual environment"),
        ("build", "generated build tree"),
        ("external", "vendored/submodule dependencies"),
        ("docs/coverage", "generated coverage HTML"),
        ("artifacts/_local", "ignored local scratch artifacts"),
        ("docs/artifacts", "curated artifacts summarized by manifest/metrics files"),
    ]:
        p = repo / raw
        if p.exists():
            items.append(
                {
                    "path": raw,
                    "reason": reason,
                    "size_bytes": dir_size(p),
                    "replacement": "summarized in ARTIFACT_RESULT_INDEX.md or file purpose index",
                }
            )
    return items


def dir_size(path: Path) -> int:
    if path.is_file():
        return file_size(path)
    total = 0
    for p in path.rglob("*"):
        if p.is_file():
            total += file_size(p)
    return total


def render_state_summary(repo: Path, info: dict[str, Any]) -> str:
    tracked_count = run(["git", "ls-files"], repo)[1].splitlines()
    return f"""# State Summary

Repo: {REPO_NAME}
Created UTC: {utc_now()}
Branch: `{info['branch']}`
HEAD: `{info['sha']}`
Dirty working tree at bundle time: `{info['dirty']}`

## Project Identity

`quant-pricer-cpp` is a modern C++20 option-pricing library with a Python binding surface and a reproducible validation/artifact pipeline. Its core engines cover Black-Scholes analytics, Monte Carlo/QMC, PDE, barrier, American, Asian, lookback, digital, Heston, risk, and multi-asset pricing.

## Current Phase

Pre-Pro AI Project OS v2 installation. The repo already contains a substantial pre-v2 agentic/project_state scaffold and validation artifacts. T-000 installs the canonical v2 strategy/state docs, preserves the old docs, and creates the first Project State Audit Bundle for a Pro strategy pass.

## Current Evidence Baseline

Latest committed metrics snapshot is `docs/artifacts/metrics_summary.md`, generated at 2026-01-25T21:13:43.226947+00:00. It reports ok status for tri-engine agreement, QMC vs PRNG, PDE order, QuantLib parity, benchmarks, and WRDS sample harness.

## Repo Scale

- Tracked files: {len(tracked_count)}
- Core C++ source files: {len(list((repo / 'src').glob('*.cpp')))}
- Public headers: {len(list((repo / 'include' / 'quant').rglob('*.hpp')))}
- Test files: {len(list((repo / 'tests').glob('*')))}

## Pro Should Decide Next

- Whether the next strategic phase is resume/paper polish, numerical robustness, market-data validation, packaging/release, or architecture cleanup.
- Which claims are allowed externally versus kept as sample/regression harness evidence.
- Whether old pre-v2 docs should remain in place indefinitely or gradually collapse into the canonical v2 files.
"""


def render_file_purpose_index(repo: Path) -> str:
    rows = [
        ("README.md", "docs", "Public project overview, claims, install, results links", "core", "current public face"),
        ("PROJECT.md", "docs", "Canonical AI OS v2 project identity and scope", "core", "current canonical"),
        ("AGENTS.md", "docs", "Agent operating rules, validation, data/security constraints", "core", "current canonical"),
        ("PROGRESS.md", "docs", "Chronological project log", "docs", "current canonical"),
        ("include/quant/", "source", "Public C++ headers", "core", "active"),
        ("src/", "source", "C++ implementation and CLI", "core", "active"),
        ("tests/", "tests", "C++ and Python FAST/MARKET tests", "validation", "active"),
        ("python/", "source", "pybind11 module and Python example", "support", "active"),
        ("wrds_pipeline/", "source", "OptionMetrics/WRDS sample/live pipeline", "core", "active but credential-gated"),
        ("scripts/reproduce_all.sh", "script", "Official sample-mode artifact reproduction pipeline", "validation", "active"),
        ("scripts/generate_metrics_summary.py", "script", "Produces metrics_summary from artifacts", "validation", "active"),
        ("scripts/check_data_policy.py", "script", "Data-leak/restricted-field guard", "validation", "active"),
        ("docs/artifacts/", "artifacts", "Curated reproducible validation outputs", "generated", "current curated"),
        ("artifacts/_local/", "artifacts", "Ignored local WRDS/scratch outputs", "generated", "not current truth"),
        ("project_state/", "docs", "AI planning/state docs, now with v2 canonical state files", "docs", "mixed current + historical"),
        ("docs/_archive/pre_ai_os_v2/", "docs", "Preserved old process docs and archive manifest", "docs", "historical"),
    ]
    lines = [
        "# File Purpose Index",
        "",
        "| Path | Type | Purpose | Strategic importance | Known status |",
        "|---|---|---|---|---|",
    ]
    for row in rows:
        lines.append("| `{}` | {} | {} | {} | {} |".format(*row))
    lines.append("")
    return "\n".join(lines)


def render_artifact_index(repo: Path) -> str:
    rows = artifact_rows(repo)
    lines = [
        "# Artifact Result Index",
        "",
        "This index summarizes result artifacts without bundling every generated or local file.",
        "",
        "| Artifact | Status | Size bytes | SHA256 | Bundle treatment |",
        "|---|---|---:|---|---|",
    ]
    for row in rows:
        treatment = "included" if row["include_in_state_bundle"] else "indexed only"
        lines.append(
            f"| `{row['path']}` | {row['status']} | {row['size_bytes']} | `{row['sha256']}` | {treatment} |"
        )
    lines.append("")
    return "\n".join(lines)


def render_validation_baseline(repo: Path, run_dir: Path | None) -> str:
    validation = None
    if run_dir and (run_dir / "VALIDATION.json").exists():
        validation = json.loads((run_dir / "VALIDATION.json").read_text(encoding="utf-8"))
    lines = [
        "# Validation Baseline",
        "",
        "## Canonical Checks",
        "",
        "| Command | What it proves | Expected cost | Latest T-000 status |",
        "|---|---|---|---|",
    ]
    checks = [
        ("git status --short", "Repo dirty/changed-file state", "fast"),
        ("python3 -m compileall tools/agentic/ai_os_bundle.py", "Bundle/archive helper parses", "fast"),
        ("python3 scripts/check_data_policy.py", "Tracked data/artifacts avoid restricted raw WRDS fields", "fast"),
        ("cmake -S . -B build -DCMAKE_BUILD_TYPE=Release", "Build system configures", "fast if cache warm"),
        ("cmake --build build -j", "C++ targets still compile", "medium"),
        ("ctest --test-dir build -L FAST --output-on-failure", "FAST unit, docs, data, artifact, and pipeline guards", "medium"),
    ]
    status_by_cmd: dict[str, str] = {}
    if validation:
        for item in validation.get("commands", []):
            status_by_cmd[item["command"]] = item["status"]
    for cmd, proves, cost in checks:
        lines.append(f"| `{cmd}` | {proves} | {cost} | {status_by_cmd.get(cmd, 'not recorded in bundle run')} |")
    lines.extend(
        [
            "",
            "## Not Run By T-000",
            "",
            "- `REPRO_FAST=1 WRDS_USE_SAMPLE=1 ./scripts/reproduce_all.sh`: not run for this docs/tooling ticket to avoid unnecessary artifact churn; use before changing headline results.",
            "- `ctest --test-dir build -L MARKET --output-on-failure`: opt-in and credential/local-data gated.",
            "",
        ]
    )
    return "\n".join(lines)


def render_docs_index(repo: Path, archive_index: str | None) -> str:
    lines = [
        "# Docs Index",
        "",
        "## Canonical AI OS v2 Docs",
        "",
    ]
    for path in CANONICAL_DOCS:
        status = "present" if (repo / path).exists() else "missing"
        lines.append(f"- `{path}` - {status}")
    lines.extend(
        [
            "",
            "## Active Product Docs",
            "",
        ]
    )
    for path in PRODUCT_DOCS:
        if (repo / path).exists():
            lines.append(f"- `{path}`")
    lines.extend(
        [
            "",
            "## Historical Docs",
            "",
            f"- Archive index: `{archive_index or 'not provided'}`",
            "- Existing pre-v2 run logs remain under `docs/agent_runs/`.",
            "- Existing pre-v2 tickets remain under `docs/tickets/`.",
            "",
        ]
    )
    return "\n".join(lines)


def render_git_state(info: dict[str, Any]) -> str:
    return f"""# Git State

Branch: `{info['branch']}`
HEAD: `{info['sha']}`
Dirty: `{info['dirty']}`

## Status

```text
{info['status_short'] or '(clean)'}
```

## Recent Commits

```text
{info['recent_log']}
```
"""


def render_recent_progress(repo: Path) -> str:
    progress = repo / "PROGRESS.md"
    tail = ""
    if progress.exists():
        lines = progress.read_text(encoding="utf-8", errors="replace").splitlines()
        tail = "\n".join(lines[-80:])
    run_dirs = sorted((repo / "docs" / "agent_runs").glob("*"), key=lambda p: p.name)[-12:]
    run_list = "\n".join(f"- `{rel(p, repo)}/`" for p in run_dirs if p.is_dir())
    return f"""# Recent Progress

## Latest Historical Run Logs

{run_list}

## Tail Of PROGRESS.md

```md
{tail}
```
"""


def build_project_state_bundle(repo: Path, timestamp: str, run_dir: Path | None, archive_index: str | None) -> Path:
    info = git_info(repo)
    out_zip = repo / "reports" / "_bundles" / f"{timestamp}_{REPO_NAME}_project-state_initial.zip"
    with tempfile.TemporaryDirectory(prefix="project_state_audit_", dir=str((run_dir or repo / "reports" / "_runs"))) as td:
        stage = Path(td)
        included: list[dict[str, Any]] = []

        write_stage_file(stage, "STATE_SUMMARY.md", render_state_summary(repo, info), included, "Project identity and status summary")
        write_stage_file(stage, "FILE_PURPOSE_INDEX.md", render_file_purpose_index(repo), included, "File purpose map")
        write_stage_file(stage, "ARTIFACT_RESULT_INDEX.md", render_artifact_index(repo), included, "Artifact/result inventory")
        write_stage_file(stage, "VALIDATION_BASELINE.md", render_validation_baseline(repo, run_dir), included, "Validation command baseline")
        write_stage_file(stage, "DOCS_INDEX.md", render_docs_index(repo, archive_index), included, "Documentation map")
        write_stage_file(stage, "GIT_STATE.md", render_git_state(info), included, "Git state at bundle time")
        write_stage_file(stage, "RECENT_PROGRESS.md", render_recent_progress(repo), included, "Recent progress summary")

        if archive_index and (repo / archive_index).exists():
            copy_into_stage(repo, stage, archive_index, "", included, "Archive index copy")
            manifest_path = Path(archive_index).with_name("ARCHIVE_MANIFEST.json").as_posix()
            copy_into_stage(repo, stage, manifest_path, "", included, "Archive manifest copy")

        for path in CANONICAL_DOCS:
            copy_into_stage(repo, stage, path, "canonical_docs", included, "Canonical AI OS v2 doc")
        for path in PRODUCT_DOCS:
            copy_into_stage(repo, stage, path, "product_docs", included, "Active product-facing doc")
        for path in SELECTED_CONFIGS + SELECTED_ARTIFACT_DOCS:
            copy_into_stage(repo, stage, path, "selected_configs", included, "Important config/artifact state file")

        for p in sorted((repo / "include").rglob("*")) + sorted((repo / "src").rglob("*")):
            if p.is_file() and is_text_like(p):
                copy_into_stage(repo, stage, rel(p, repo), "selected_source", included, "Selected source file")
        for p in sorted((repo / "tests").glob("*")):
            if p.is_file() and is_text_like(p):
                copy_into_stage(repo, stage, rel(p, repo), "selected_tests", included, "Selected test file")
        for p in sorted((repo / "wrds_pipeline").rglob("*")):
            if p.is_file() and is_text_like(p) and "__pycache__" not in p.parts:
                copy_into_stage(repo, stage, rel(p, repo), "selected_source", included, "Selected WRDS pipeline file")
        for p in sorted((repo / "tools" / "agentic").glob("*.py")):
            copy_into_stage(repo, stage, rel(p, repo), "selected_tools", included, "Agentic support tool")

        manifest = {
            "schema_version": "context-bundle-v2",
            "created_at_utc": utc_now(),
            "repo_name": REPO_NAME,
            "repo_root": str(repo),
            "git_branch": info["branch"],
            "git_sha": info["sha"],
            "dirty": info["dirty"],
            "profile": "project_state_audit",
            "consumer": "pro",
            "ticket_id": None,
            "phase": "initial",
            "run_dir": rel(run_dir, repo) if run_dir and run_dir.exists() else None,
            "included_files": included,
            "excluded_large_artifacts": excluded_large_artifacts(repo),
            "validation_summary": load_validation_summary(run_dir),
            "artifact_summary": {
                "current_artifacts": [r["path"] for r in artifact_rows(repo) if r["status"] == "current curated"],
                "stale_or_superseded_artifacts": [r["path"] for r in artifact_rows(repo) if r["status"] == "local scratch"],
            },
            "known_limitations": [
                "This bundle summarizes large generated artifacts instead of including all of them.",
                "Live WRDS/market-data validation is credential/local-data gated.",
                "Initial strategy docs are pre-Pro placeholders where explicit strategy is not yet known.",
            ],
            "recommended_reader_focus": [
                "PROJECT.md and docs/strategy/GOAL_CONTEXT.md for scope/goals.",
                "STATE_SUMMARY.md, CLAIMS_AND_EVIDENCE.md, and VALIDATION_BASELINE.md for current truth boundaries.",
                "ARCHIVE_INDEX.md for pre-v2 historical context.",
            ],
        }
        write_stage_file(stage, "bundle_manifest.json", json.dumps(manifest, indent=2, sort_keys=True) + "\n", included, "Bundle manifest")
        write_stage_file(stage, "BUNDLE_INDEX.md", render_project_bundle_index(manifest), included, "Human bundle index")
        zip_stage(stage, out_zip)
    return out_zip


def load_validation_summary(run_dir: Path | None) -> dict[str, Any]:
    if run_dir and (run_dir / "VALIDATION.json").exists():
        data = json.loads((run_dir / "VALIDATION.json").read_text(encoding="utf-8"))
        status = data.get("overall_status", "partial")
        commands = [
            {"command": item.get("command"), "status": item.get("status"), "log_path": item.get("log_path")}
            for item in data.get("commands", [])
        ]
        return {"status": status, "commands": commands}
    return {"status": "not_run", "commands": []}


def render_project_bundle_index(manifest: dict[str, Any]) -> str:
    return f"""# Bundle Index

## Identity

- Repo: {manifest['repo_name']}
- Branch/SHA: `{manifest['git_branch']}` / `{manifest['git_sha']}`
- Profile: `{manifest['profile']}`
- Consumer: `{manifest['consumer']}`
- Ticket: n/a
- Created: {manifest['created_at_utc']}

## Purpose

Initial AI Project OS v2 Project State Audit Bundle for Pro Extended strategy planning.

## How To Review

Start with `STATE_SUMMARY.md`, `PROJECT.md` inside `canonical_docs/`, `project_state/CLAIMS_AND_EVIDENCE.md`, and `VALIDATION_BASELINE.md`. Use `ARCHIVE_INDEX.md` for old-process context without treating it as current truth.

## Included Files By Category

- Generated state files: STATE_SUMMARY, FILE_PURPOSE_INDEX, ARTIFACT_RESULT_INDEX, VALIDATION_BASELINE, DOCS_INDEX, GIT_STATE, RECENT_PROGRESS.
- Canonical docs: root AI OS docs, strategy docs, T-000 ticket/template, canonical project_state docs.
- Selected source/tests/configs: C++ core, tests, WRDS pipeline, build configs, workflows, metrics manifest/summary.

## Important Excluded Files

See `bundle_manifest.json` field `excluded_large_artifacts`.

## Validation Summary

Status: `{manifest['validation_summary']['status']}`

## Known Limitations

{chr(10).join('- ' + item for item in manifest['known_limitations'])}

## Recommended Next Consumer Action

Pro should use this bundle to produce the first real strategy package, claim/evidence judgment, and goal-level ticket ledger.
"""


def changed_files(repo: Path) -> list[str]:
    _, out = run(["git", "status", "--porcelain"], repo)
    files: list[str] = []
    for line in out.splitlines():
        if not line.strip():
            continue
        path = line[3:].strip()
        if " -> " in path:
            path = path.split(" -> ", 1)[1]
        expanded = expand_changed_path(repo, path)
        for item in expanded:
            if item not in files:
                files.append(item)
    return files


def expand_changed_path(repo: Path, path: str) -> list[str]:
    p = repo / path
    if p.is_file():
        return [path]
    if not p.is_dir():
        return [path]
    expanded: list[str] = []
    for child in sorted(p.rglob("*")):
        if not child.is_file():
            continue
        child_rel = rel(child, repo)
        if should_skip_changed_file(child_rel):
            continue
        expanded.append(child_rel)
    return expanded or [path]


def should_skip_changed_file(path: str) -> bool:
    skip_prefixes = (
        "reports/_runs/",
        "__pycache__/",
    )
    if any(path.startswith(prefix) for prefix in skip_prefixes):
        return True
    if "/__pycache__/" in path:
        return True
    if path.startswith("reports/_bundles/") and path.endswith(".zip"):
        return True
    if path.endswith(".pyc"):
        return True
    return False


def build_patch_for_review(repo: Path, files: list[str]) -> str:
    parts: list[str] = []
    _, diff = run(["git", "diff", "--no-ext-diff", "--binary"], repo)
    if diff.strip():
        parts.append(diff)
    _, cached = run(["git", "diff", "--cached", "--no-ext-diff", "--binary"], repo)
    if cached.strip():
        parts.append("\n# Staged diff\n\n" + cached)
    for path in files:
        p = repo / path
        if not p.exists() or not p.is_file():
            continue
        if path.startswith("reports/_bundles/") and p.suffix == ".zip":
            continue
        if p.suffix == ".zip" or file_size(p) > 500_000 or not is_text_like(p):
            continue
        code, out = run(["git", "diff", "--no-index", "--", "/dev/null", path], repo)
        if out.strip() and path in out:
            parts.append(f"\n# Untracked file: {path}\n\n{out}")
    return "\n".join(parts).strip() + "\n"


def build_review_bundle(repo: Path, timestamp: str, run_dir: Path, archive_index: str | None) -> Path:
    info = git_info(repo)
    out_zip = repo / "reports" / "_bundles" / f"{timestamp}_{REPO_NAME}_review_T-000.zip"
    with tempfile.TemporaryDirectory(prefix="review_T000_", dir=str(run_dir)) as td:
        stage = Path(td)
        included: list[dict[str, Any]] = []
        files = changed_files(repo)
        patch = build_patch_for_review(repo, files)

        manifest = {
            "schema_version": "context-bundle-v2",
            "created_at_utc": utc_now(),
            "repo_name": REPO_NAME,
            "repo_root": str(repo),
            "git_branch": info["branch"],
            "git_sha": info["sha"],
            "dirty": info["dirty"],
            "profile": "review",
            "consumer": "heavy",
            "ticket_id": "T-000",
            "phase": "review",
            "run_dir": rel(run_dir, repo),
            "included_files": included,
            "excluded_large_artifacts": excluded_large_artifacts(repo),
            "validation_summary": load_validation_summary(run_dir),
            "artifact_summary": {
                "current_artifacts": [str(out_zip.relative_to(repo))],
                "stale_or_superseded_artifacts": [],
            },
            "known_limitations": [
                "Review bundle excludes generated zip payloads from DIFF.patch.",
                "reports/_runs files are generated run evidence and may be gitignored.",
            ],
            "recommended_reader_focus": [
                "Check DIFF.patch and changed_files.txt for scope.",
                "Check archive/ for preservation behavior.",
                "Check VALIDATION.json and VALIDATION.md for command outcomes.",
            ],
        }

        for name in ["PROMPT.md", "COMMANDS.md", "RESULTS.md", "VALIDATION.md", "VALIDATION.json", "SUMMARY.md"]:
            if (run_dir / name).exists():
                dst = stage / name
                safe_copy(run_dir / name, dst)
                included.append(
                    {
                        "path": name,
                        "source_path": rel(run_dir / name, repo),
                        "purpose": "T-000 run log evidence",
                        "source": "generated",
                        "size_bytes": file_size(dst),
                        "sha256": sha256_file(dst),
                    }
                )
        write_stage_file(stage, "git_status.txt", info["status_short"] + "\n", included, "Git status at review bundle time")
        write_stage_file(stage, "changed_files.txt", "\n".join(files) + "\n", included, "Changed/untracked file list")
        write_stage_file(stage, "DIFF.patch", patch, included, "Working tree patch/diff evidence")
        write_stage_file(stage, "docs_created_updated_archived.md", render_docs_changed_summary(files, archive_index), included, "Docs change summary")
        write_stage_file(stage, "known_residual_risks.md", render_residual_risks(), included, "Residual risks for Heavy")

        if archive_index and (repo / archive_index).exists():
            copy_into_stage(repo, stage, archive_index, "archive", included, "Archive index")
            archive_manifest = Path(archive_index).with_name("ARCHIVE_MANIFEST.json").as_posix()
            copy_into_stage(repo, stage, archive_manifest, "archive", included, "Archive manifest")

        for path in files:
            p = repo / path
            if not p.exists() or not p.is_file():
                continue
            if path.startswith("reports/_bundles/") and p.suffix == ".zip":
                continue
            if path.startswith("reports/_runs/"):
                continue
            if p.suffix == ".zip" or file_size(p) > 250_000 or not is_text_like(p):
                continue
            copy_into_stage(repo, stage, path, "changed_files", included, "Changed file snapshot")

        manifest["included_files"] = included
        write_stage_file(stage, "bundle_manifest.json", json.dumps(manifest, indent=2, sort_keys=True) + "\n", included, "Bundle manifest")
        write_stage_file(stage, "BUNDLE_INDEX.md", render_review_bundle_index(manifest), included, "Human bundle index")

        zip_stage(stage, out_zip)
    return out_zip


def render_docs_changed_summary(files: list[str], archive_index: str | None) -> str:
    docs = [p for p in files if p.endswith(".md") or p.endswith(".json") or p.startswith("docs/") or p.startswith("project_state/")]
    lines = [
        "# Docs Created, Updated, Or Archived",
        "",
        f"Archive index: `{archive_index or 'not provided'}`",
        "",
        "## Changed/Added Docs And State Files",
        "",
    ]
    for path in docs:
        lines.append(f"- `{path}`")
    if not docs:
        lines.append("- none recorded by git status")
    lines.append("")
    return "\n".join(lines)


def render_residual_risks() -> str:
    return """# Known Residual Risks

- Initial strategy docs are factual/pre-Pro placeholders; Pro still needs to set the real long-term strategy and priority order.
- Old pre-v2 docs remain in place and may contain stale status; new canonical docs mark the v2 sources of truth.
- T-000 does not rerun the full sample artifact reproduction pipeline to avoid result churn.
- Live WRDS/market checks remain credential/local-data gated and are not proven by this installation ticket.
"""


def render_review_bundle_index(manifest: dict[str, Any]) -> str:
    return f"""# T-000 Review Bundle Index

## Identity

- Repo: {manifest['repo_name']}
- Branch/SHA: `{manifest['git_branch']}` / `{manifest['git_sha']}`
- Profile: `{manifest['profile']}`
- Consumer: `{manifest['consumer']}`
- Ticket: `{manifest['ticket_id']}`
- Created: {manifest['created_at_utc']}

## Purpose

Review evidence for T-000: install AI Project OS v2, archive pre-v2 docs, and generate the first Project State Audit Bundle.

## How To Review

1. Read `PROMPT.md`, `SUMMARY.md`, and `RESULTS.md`.
2. Inspect `DIFF.patch`, `changed_files.txt`, and `changed_files/`.
3. Check `archive/ARCHIVE_INDEX.md` and `archive/ARCHIVE_MANIFEST.json`.
4. Check `VALIDATION.json` / `VALIDATION.md` for exact command outcomes.

## Validation Summary

Status: `{manifest['validation_summary']['status']}`

## Known Limitations

{chr(10).join('- ' + item for item in manifest['known_limitations'])}
"""


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="cmd", required=True)

    p_archive = sub.add_parser("archive", help="Build pre-AI-OS-v2 archive manifest/index.")
    p_archive.add_argument("--date", default=datetime.now(timezone.utc).strftime("%Y%m%d"))

    p_state = sub.add_parser("project-state", help="Build Project State Audit Bundle.")
    p_state.add_argument("--timestamp", required=True)
    p_state.add_argument("--run-dir", default=None)
    p_state.add_argument("--archive-index", default=None)

    p_review = sub.add_parser("review-t000", help="Build T-000 review bundle.")
    p_review.add_argument("--timestamp", required=True)
    p_review.add_argument("--run-dir", required=True)
    p_review.add_argument("--archive-index", default=None)

    args = parser.parse_args()
    repo = git_root(Path.cwd())

    if args.cmd == "archive":
        archive_root = build_archive(repo, args.date)
        print(archive_root.relative_to(repo).as_posix())
        return 0
    if args.cmd == "project-state":
        run_dir = repo / args.run_dir if args.run_dir else None
        out = build_project_state_bundle(repo, args.timestamp, run_dir, args.archive_index)
        print(out.relative_to(repo).as_posix())
        return 0
    if args.cmd == "review-t000":
        out = build_review_bundle(repo, args.timestamp, repo / args.run_dir, args.archive_index)
        print(out.relative_to(repo).as_posix())
        return 0
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
