from __future__ import annotations

import hashlib
import json
import os
import platform
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List

ARTIFACTS_ROOT = Path("docs") / "artifacts"
MANIFEST_PATH = ARTIFACTS_ROOT / "manifest.json"


def _git_info() -> Dict[str, Any]:
    def run(cmd: List[str]) -> str:
        return subprocess.check_output(cmd, text=True).strip()

    sha = run(["git", "rev-parse", "HEAD"])
    branch = run(["git", "rev-parse", "--abbrev-ref", "HEAD"])
    status = run(["git", "status", "--porcelain"])
    return {"sha": sha, "branch": branch, "dirty": bool(status)}


def _cpu_brand() -> str:
    generic_tokens = {"", "arm", "amd64", "x86_64", "unknown"}
    brand = platform.processor()
    if brand and brand.lower() not in generic_tokens:
        return brand
    system = platform.system()
    try:
        if system == "Darwin":
            return subprocess.check_output(
                ["sysctl", "-n", "machdep.cpu.brand_string"], text=True
            ).strip()
        if system == "Linux":
            with open("/proc/cpuinfo", "r", encoding="utf-8", errors="ignore") as fh:
                for line in fh:
                    if "model name" in line:
                        return line.split(":", 1)[1].strip()
    except Exception:
        pass
    return platform.machine()


def _system_info() -> Dict[str, Any]:
    return {
        "platform": platform.system(),
        "release": platform.release(),
        "machine": platform.machine(),
        "processor": platform.processor(),
        "cpu_brand": _cpu_brand(),
        "python": platform.python_version(),
        "cpu_count": os.cpu_count(),
    }


def _omp_threads() -> int:
    value = os.environ.get("OMP_NUM_THREADS")
    if value and value.isdigit():
        return int(value)
    return os.cpu_count() or 1


def _cmake_value(lines: List[str], key: str) -> str | None:
    prefix = f"{key}:"
    for line in lines:
        if line.startswith(prefix):
            return line.split("=", 1)[1].strip()
    return None


def _compile_info() -> Dict[str, Any]:
    cache = Path("build") / "CMakeCache.txt"
    if not cache.exists():
        return {"available": False}
    try:
        lines = cache.read_text(encoding="utf-8", errors="ignore").splitlines()
    except Exception:
        return {"available": False}
    info = {
        "available": True,
        "generator": _cmake_value(lines, "CMAKE_GENERATOR") or "",
        "compiler_id": _cmake_value(lines, "CMAKE_CXX_COMPILER_ID") or "",
        "compiler_version": _cmake_value(lines, "CMAKE_CXX_COMPILER_VERSION") or "",
        "compiler_path": _cmake_value(lines, "CMAKE_CXX_COMPILER") or "",
        "cxx_flags": _cmake_value(lines, "CMAKE_CXX_FLAGS") or "",
        "cxx_flags_release": _cmake_value(lines, "CMAKE_CXX_FLAGS_RELEASE") or "",
    }
    if not info["compiler_id"]:
        info["compiler_id"] = "unknown"
    if not info["compiler_version"]:
        info["compiler_version"] = "unknown"
    return info


def load_manifest() -> Dict[str, Any]:
    if MANIFEST_PATH.exists():
        return json.loads(MANIFEST_PATH.read_text())
    return {"runs": {}}


def ensure_metadata(manifest: Dict[str, Any]) -> Dict[str, Any]:
    manifest["generated_at"] = datetime.now(timezone.utc).isoformat()
    manifest["git"] = _git_info()
    manifest["system"] = _system_info()
    manifest.setdefault("runs", {})
    manifest["omp_threads"] = _omp_threads()
    manifest["build"] = _compile_info()
    legacy_keys = [
        "git_sha",
        "build_type",
        "compiler",
        "flags",
        "monte_carlo",
        "qmc_vs_prng",
        "pde",
        "pde_convergence",
        "american",
        "barrier_validation",
        "executables",
        "american_validation",
        "figures",
    ]
    for key in legacy_keys:
        manifest.pop(key, None)
    return manifest


def save_manifest(manifest: Dict[str, Any]) -> None:
    manifest = ensure_metadata(manifest)
    MANIFEST_PATH.parent.mkdir(parents=True, exist_ok=True)
    MANIFEST_PATH.write_text(json.dumps(manifest, sort_keys=True, indent=2) + "\n")


def describe_inputs(paths: Iterable[str | Path]) -> List[Dict[str, Any]]:
    entries: List[Dict[str, Any]] = []
    for raw in paths:
        path = Path(raw)
        if not path:
            continue
        record: Dict[str, Any] = {"path": str(path)}
        if path.exists() and path.is_file():
            try:
                record["sha256"] = hashlib.sha256(path.read_bytes()).hexdigest()
                record["size_bytes"] = path.stat().st_size
            except Exception:
                record["sha256"] = None
        entries.append(record)
    return entries


def update_run(
    key: str,
    data: Dict[str, Any],
    append: bool = False,
    id_field: str | None = None,
) -> Dict[str, Any]:
    manifest = load_manifest()
    runs = manifest.setdefault("runs", {})
    if append:
        items: List[Dict[str, Any]] = runs.get(key, [])
        if not isinstance(items, list):
            items = []
        if id_field is not None:
            items = [item for item in items if item.get(id_field) != data.get(id_field)]
        items.append(data)
        if id_field is not None:
            items.sort(key=lambda x: x.get(id_field, ""))
        runs[key] = items
    else:
        runs[key] = data
    save_manifest(manifest)
    return runs[key]


__all__ = [
    "ARTIFACTS_ROOT",
    "load_manifest",
    "save_manifest",
    "update_run",
    "describe_inputs",
    "MANIFEST_PATH",
]
