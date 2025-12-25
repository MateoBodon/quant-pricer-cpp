from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, Tuple

from manifest_utils import describe_inputs, load_manifest, save_manifest

REPO_ROOT = Path(__file__).resolve().parents[1]

CANONICAL_SCENARIO_GRID = (
    REPO_ROOT / "configs" / "scenario_grids" / "synthetic_validation_v1.json"
)
CANONICAL_TOLERANCES = (
    REPO_ROOT / "configs" / "tolerances" / "synthetic_validation_v1.json"
)
PROTOCOL_NAME = "synthetic_validation"


def _load_json(path: Path) -> Dict[str, Any]:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:
        raise SystemExit(f"failed to read protocol config: {path} ({exc})") from exc


def _input_record(path: Path) -> Dict[str, Any]:
    record = describe_inputs([path.resolve()])
    if record:
        return record[0]
    return {"path": str(path)}


def _require_paths(
    scenario_grid: str | Path | None, tolerances: str | Path | None
) -> tuple[Path, Path]:
    if scenario_grid is None or tolerances is None:
        raise SystemExit(
            "missing protocol config provenance: pass --scenario-grid <path> "
            "--tolerances <path>"
        )
    scenario_path = Path(scenario_grid).expanduser()
    tolerances_path = Path(tolerances).expanduser()
    if not scenario_path.is_file():
        raise SystemExit(f"scenario grid config not found: {scenario_path}")
    if not tolerances_path.is_file():
        raise SystemExit(f"tolerances config not found: {tolerances_path}")
    return scenario_path, tolerances_path


def load_protocol_configs(
    scenario_grid: str | Path | None,
    tolerances: str | Path | None,
) -> Tuple[Dict[str, Any], Dict[str, Any], Dict[str, Any]]:
    scenario_path, tolerances_path = _require_paths(scenario_grid, tolerances)
    scenario_config = _load_json(scenario_path)
    tolerance_config = _load_json(tolerances_path)
    provenance = {
        "scenario_grid": _input_record(scenario_path),
        "tolerances": _input_record(tolerances_path),
    }
    if "id" in scenario_config:
        provenance["scenario_grid_id"] = scenario_config["id"]
    if "id" in tolerance_config:
        provenance["tolerances_id"] = tolerance_config["id"]
    return scenario_config, tolerance_config, provenance


def record_protocol_manifest(
    scenario_config: Dict[str, Any],
    tolerance_config: Dict[str, Any],
    provenance: Dict[str, Any],
    protocol_name: str = PROTOCOL_NAME,
) -> Dict[str, Any]:
    manifest = load_manifest()
    protocols = manifest.setdefault("protocols", {})
    record = {
        "scenario_grid": provenance.get("scenario_grid"),
        "tolerances": provenance.get("tolerances"),
        "scenario_grid_id": scenario_config.get("id"),
        "tolerances_id": tolerance_config.get("id"),
    }
    protocols[protocol_name] = record
    save_manifest(manifest)
    return record


def select_grid_block(
    scenario_config: Dict[str, Any], key: str, fast: bool
) -> Dict[str, Any]:
    if key not in scenario_config:
        raise SystemExit(f"scenario grid missing '{key}' block")
    block = dict(scenario_config[key])
    if fast:
        fast_block = block.get("fast")
        if not isinstance(fast_block, dict):
            raise SystemExit(f"scenario grid missing '{key}.fast' overrides for --fast")
        merged = dict(block)
        merged.update(fast_block)
        merged.pop("fast", None)
        return merged
    block.pop("fast", None)
    return block


__all__ = [
    "CANONICAL_SCENARIO_GRID",
    "CANONICAL_TOLERANCES",
    "PROTOCOL_NAME",
    "load_protocol_configs",
    "record_protocol_manifest",
    "select_grid_block",
]
