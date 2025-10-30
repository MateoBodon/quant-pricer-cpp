from __future__ import annotations

import json
import os
import platform
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List

MANIFEST_PATH = Path("artifacts/manifest.json")


def _git_info() -> Dict[str, Any]:
    def run(cmd: List[str]) -> str:
        return subprocess.check_output(cmd, text=True).strip()

    sha = run(["git", "rev-parse", "HEAD"])
    branch = run(["git", "rev-parse", "--abbrev-ref", "HEAD"])
    status = run(["git", "status", "--porcelain"])
    return {"sha": sha, "branch": branch, "dirty": bool(status)}


def _system_info() -> Dict[str, Any]:
    return {
        "platform": platform.system(),
        "release": platform.release(),
        "machine": platform.machine(),
        "processor": platform.processor(),
        "python": platform.python_version(),
        "cpu_count": os.cpu_count(),
    }


def load_manifest() -> Dict[str, Any]:
    if MANIFEST_PATH.exists():
        return json.loads(MANIFEST_PATH.read_text())
    return {"runs": {}}


def ensure_metadata(manifest: Dict[str, Any]) -> Dict[str, Any]:
    manifest["generated_at"] = datetime.now(timezone.utc).isoformat()
    manifest["git"] = _git_info()
    manifest["system"] = _system_info()
    manifest.setdefault("runs", {})
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
    MANIFEST_PATH.write_text(json.dumps(manifest, indent=2) + "\n")


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


__all__ = ["load_manifest", "save_manifest", "update_run", "MANIFEST_PATH"]
