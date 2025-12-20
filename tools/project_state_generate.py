#!/usr/bin/env python3
"""Generate project_state/_generated artifacts (repo inventory, symbol index, import graph, make targets)."""
from __future__ import annotations

import ast
import json
import os
import re
import subprocess
from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Tuple

REPO_ROOT = Path(__file__).resolve().parents[1]
OUTPUT_DIR = REPO_ROOT / "project_state" / "_generated"

PYTHON_ROOTS = [
    "src",
    "experiments",
    "tools",
    "scripts",
    "wrds_pipeline",
    "python",
    "tests",
]

EXCLUDE_DIRS = {
    ".git",
    ".venv",
    "__pycache__",
    "build",
    "build-omp",
    "reports",
    "data",
    "artifacts",
    "docs/agent_runs",
    "external",
}

EXCLUDE_PATTERNS = [
    re.compile(r"experiments/.*/outputs_.*"),
]

EXCLUDE_INVENTORY_PREFIXES = {
    "docs/gpt_bundles",
}


@dataclass
class SymbolInfo:
    name: str
    kind: str
    signature: str
    docstring: Optional[str]
    lineno: int


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _git(cmd: List[str]) -> str:
    return subprocess.check_output(cmd, cwd=REPO_ROOT, text=True).strip()


def _rg_files() -> List[str]:
    proc = subprocess.run(
        ["rg", "--files", "-0"],
        cwd=REPO_ROOT,
        check=True,
        capture_output=True,
    )
    raw = proc.stdout.split(b"\0")
    return [p.decode("utf-8") for p in raw if p]


def _role_for_path(path: Path) -> str:
    if not path.parts:
        return "unknown"
    top = path.parts[0]
    if top == "include":
        return "cpp_headers"
    if top == "src":
        return "cpp_sources"
    if top == "tests":
        return "tests"
    if top == "benchmarks":
        return "benchmarks"
    if top == "scripts":
        return "scripts"
    if top == "wrds_pipeline":
        return "wrds_pipeline"
    if top == "python":
        return "python_bindings"
    if top == "docs":
        return "docs"
    if top == "cmake":
        return "cmake"
    if top == "external":
        return "external"
    if top == "data":
        return "data"
    if top == "artifacts":
        return "artifacts"
    if top == "project_state":
        return "project_state"
    if path.name in {
        "CMakeLists.txt",
        "Makefile",
        "README.md",
        "CHANGELOG.md",
        "LICENSE",
        "CONTRIBUTING.md",
        "Doxyfile",
        "pyproject.toml",
        "setup.cfg",
        "conanfile.py",
        "vcpkg.json",
        "CITATION.cff",
    }:
        return "repo_meta"
    return "misc"


def _inventory() -> Dict[str, object]:
    files = []
    role_counts: Dict[str, int] = defaultdict(int)
    role_sizes: Dict[str, int] = defaultdict(int)
    for rel in _rg_files():
        if any(rel == prefix or rel.startswith(prefix + "/") for prefix in EXCLUDE_INVENTORY_PREFIXES):
            continue
        path = REPO_ROOT / rel
        if not path.exists():
            continue
        try:
            stat = path.stat()
        except OSError:
            continue
        role = _role_for_path(Path(rel))
        entry = {
            "path": rel,
            "size_bytes": stat.st_size,
            "role": role,
            "ext": path.suffix.lstrip("."),
        }
        files.append(entry)
        role_counts[role] += 1
        role_sizes[role] += stat.st_size
    return {
        "generated_at": _utc_now(),
        "git_sha": _git(["git", "rev-parse", "HEAD"]),
        "root": str(REPO_ROOT),
        "files": sorted(files, key=lambda e: e["path"]),
        "summary": {
            "role_counts": dict(sorted(role_counts.items())),
            "role_sizes_bytes": dict(sorted(role_sizes.items())),
        },
    }


def _should_skip(path: Path) -> bool:
    rel = str(path.as_posix())
    for excl in EXCLUDE_DIRS:
        if rel == excl or rel.startswith(excl + "/"):
            return True
    for pattern in EXCLUDE_PATTERNS:
        if pattern.search(rel):
            return True
    return False


def _iter_python_files() -> List[Path]:
    files: List[Path] = []
    for root in PYTHON_ROOTS:
        root_path = REPO_ROOT / root
        if not root_path.exists():
            continue
        for path in root_path.rglob("*.py"):
            if _should_skip(path.relative_to(REPO_ROOT)):
                continue
            files.append(path)
    return sorted(set(files))


def _format_signature(node: ast.AST) -> str:
    if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
        return "()"

    args = node.args
    parts: List[str] = []

    def add_arg(arg: ast.arg, default: Optional[ast.AST]) -> None:
        name = arg.arg
        if default is not None:
            try:
                default_text = ast.unparse(default)
            except Exception:
                default_text = "..."
            parts.append(f"{name}={default_text}")
        else:
            parts.append(name)

    posonly = list(args.posonlyargs)
    normal = list(args.args)
    defaults = list(args.defaults)
    total = posonly + normal
    pad = [None] * (len(total) - len(defaults)) + defaults
    for arg, default in zip(total, pad):
        add_arg(arg, default)
    if posonly:
        parts.insert(len(posonly), "/")

    if args.vararg is not None:
        parts.append("*" + args.vararg.arg)
    elif args.kwonlyargs:
        parts.append("*")

    kw_defaults = list(args.kw_defaults)
    for arg, default in zip(args.kwonlyargs, kw_defaults):
        add_arg(arg, default)

    if args.kwarg is not None:
        parts.append("**" + args.kwarg.arg)

    return "(" + ", ".join(parts) + ")"


def _collect_symbols(
    path: Path,
) -> Tuple[List[SymbolInfo], List[SymbolInfo], List[str], List[Dict[str, object]]]:
    text = path.read_text(encoding="utf-8", errors="ignore")
    try:
        tree = ast.parse(text)
    except SyntaxError:
        return [], [], []

    functions: List[SymbolInfo] = []
    classes: List[SymbolInfo] = []
    imports: List[str] = []
    import_records: List[Dict[str, object]] = []

    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            doc = ast.get_docstring(node)
            functions.append(
                SymbolInfo(
                    name=node.name,
                    kind="function",
                    signature=_format_signature(node),
                    docstring=doc.splitlines()[0] if doc else None,
                    lineno=node.lineno,
                )
            )
        elif isinstance(node, ast.ClassDef):
            doc = ast.get_docstring(node)
            classes.append(
                SymbolInfo(
                    name=node.name,
                    kind="class",
                    signature="",
                    docstring=doc.splitlines()[0] if doc else None,
                    lineno=node.lineno,
                )
            )
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            names = [alias.name for alias in node.names]
            imports.extend(names)
            import_records.append(
                {"type": "import", "module": None, "names": names, "level": 0}
            )
        elif isinstance(node, ast.ImportFrom):
            names = [alias.name for alias in node.names]
            level = node.level or 0
            module = node.module
            if module:
                prefix = "." * level if level else ""
                imports.append(prefix + module)
            else:
                imports.append("." * level + ",".join(names))
            import_records.append(
                {"type": "from", "module": module, "names": names, "level": level}
            )
    return functions, classes, imports, import_records


def _module_name(path: Path) -> str:
    rel = path.relative_to(REPO_ROOT)
    parts = list(rel.parts)
    if parts[-1] == "__init__.py":
        parts = parts[:-1]
    else:
        parts[-1] = parts[-1][:-3]
    return ".".join(parts)


def _symbol_index() -> Dict[str, object]:
    files = _iter_python_files()
    modules: Dict[str, str] = {}
    for path in files:
        modules[_module_name(path)] = str(path.relative_to(REPO_ROOT))

    index: Dict[str, object] = {
        "generated_at": _utc_now(),
        "git_sha": _git(["git", "rev-parse", "HEAD"]),
        "python_roots": PYTHON_ROOTS,
        "files": {},
    }

    for path in files:
        rel = str(path.relative_to(REPO_ROOT))
        functions, classes, imports, import_records = _collect_symbols(path)
        index["files"][rel] = {
            "module": _module_name(path),
            "functions": [
                {
                    "name": f.name,
                    "signature": f.signature,
                    "docstring": f.docstring,
                    "lineno": f.lineno,
                }
                for f in functions
            ],
            "classes": [
                {
                    "name": c.name,
                    "docstring": c.docstring,
                    "lineno": c.lineno,
                }
                for c in classes
            ],
            "imports": sorted(set(imports)),
            "imports_detail": import_records,
        }
    index["modules"] = modules
    return index


def _resolve_internal(module: str, modules: Dict[str, str]) -> Optional[str]:
    if module in modules:
        return module
    # Try dotted prefix resolution
    for candidate in sorted(modules.keys(), key=len, reverse=True):
        if module.startswith(candidate + "."):
            return candidate
    return None


def _resolve_relative(current: str, level: int, module: Optional[str], name: Optional[str]) -> Optional[str]:
    parts = current.split(".")
    if level > len(parts):
        return None
    base = parts[:-level]
    if module:
        base.extend(module.split("."))
    if name:
        base.append(name)
    return ".".join(base) if base else None


def _import_graph(symbol_index: Dict[str, object]) -> Dict[str, object]:
    files = symbol_index.get("files", {})
    modules = symbol_index.get("modules", {})
    graph: Dict[str, List[str]] = {}

    for rel, data in files.items():
        module = data.get("module")
        imports_detail = data.get("imports_detail", [])
        internal: List[str] = []
        for entry in imports_detail:
            if entry.get("type") == "import":
                for name in entry.get("names", []):
                    resolved = _resolve_internal(name, modules)
                    if resolved:
                        internal.append(resolved)
                continue

            if entry.get("type") == "from":
                level = int(entry.get("level", 0) or 0)
                module_name = entry.get("module")
                names = entry.get("names", [])
                if level > 0:
                    if module_name:
                        resolved = _resolve_relative(module, level, module_name, None)
                        resolved = _resolve_internal(resolved, modules) if resolved else None
                        if resolved:
                            internal.append(resolved)
                    for name in names:
                        resolved = _resolve_relative(module, level, module_name, name)
                        resolved = _resolve_internal(resolved, modules) if resolved else None
                        if resolved:
                            internal.append(resolved)
                else:
                    if module_name:
                        resolved = _resolve_internal(module_name, modules)
                        if resolved:
                            internal.append(resolved)
                    for name in names:
                        if module_name:
                            candidate = f"{module_name}.{name}"
                            resolved = _resolve_internal(candidate, modules)
                            if resolved:
                                internal.append(resolved)
        graph[module] = sorted(set(internal))

    return {
        "generated_at": _utc_now(),
        "git_sha": _git(["git", "rev-parse", "HEAD"]),
        "nodes": graph,
        "modules": modules,
    }


def _make_targets() -> List[str]:
    makefile = REPO_ROOT / "Makefile"
    if not makefile.exists():
        return []
    targets: List[str] = []
    for line in makefile.read_text(encoding="utf-8", errors="ignore").splitlines():
        if line.startswith("."):
            continue
        if ":" in line and not line.startswith("\t"):
            name = line.split(":", 1)[0].strip()
            if name:
                targets.append(name)
    return sorted(set(targets))


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    inventory = _inventory()
    (OUTPUT_DIR / "repo_inventory.json").write_text(
        json.dumps(inventory, indent=2, sort_keys=True) + "\n"
    )

    symbol_index = _symbol_index()
    (OUTPUT_DIR / "symbol_index.json").write_text(
        json.dumps(symbol_index, indent=2, sort_keys=True) + "\n"
    )

    import_graph = _import_graph(symbol_index)
    (OUTPUT_DIR / "import_graph.json").write_text(
        json.dumps(import_graph, indent=2, sort_keys=True) + "\n"
    )

    make_targets = _make_targets()
    (OUTPUT_DIR / "make_targets.txt").write_text("\n".join(make_targets) + "\n")


if __name__ == "__main__":
    main()
