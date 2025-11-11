#!/usr/bin/env python3
"""Bundle reproducible artifacts into validation_pack.zip."""
from __future__ import annotations

import argparse
import sys
import zipfile
from pathlib import Path


def gather_files(artifacts: Path, allowed_exts: set[str]) -> list[Path]:
    files: list[Path] = []
    for path in sorted(artifacts.rglob("*")):
        if not path.is_file():
            continue
        if path.name.startswith("."):
            continue
        suffix = path.suffix.lower()
        if suffix in allowed_exts or path.name == "manifest.json":
            files.append(path)
    return files


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(
        description="Create validation_pack.zip from docs/artifacts.",
    )
    parser.add_argument(
        "--artifacts",
        type=Path,
        default=Path("docs") / "artifacts",
        help="Directory containing committed artifacts (default: docs/artifacts)",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("docs") / "validation_pack.zip",
        help="Path to the zip archive to create (default: docs/validation_pack.zip)",
    )
    parser.add_argument(
        "--include-ext",
        nargs="*",
        default=None,
        help="Optional overrides for allowed file extensions (e.g., --include-ext .csv .png .json)",
    )
    args = parser.parse_args(argv)

    artifacts_dir = args.artifacts.resolve()
    if not artifacts_dir.is_dir():
        raise SystemExit(f"Artifacts directory not found: {artifacts_dir}")

    if args.include_ext:
        allowed_exts = {ext.lower() for ext in args.include_ext}
    else:
        allowed_exts = {".csv", ".png", ".json"}

    files = gather_files(artifacts_dir, allowed_exts)
    if not files:
        raise SystemExit(f"No files with extensions {sorted(allowed_exts)} under {artifacts_dir}")

    output_path = args.output.resolve()
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with zipfile.ZipFile(output_path, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as zf:
        for path in files:
            arcname = Path("artifacts") / path.relative_to(artifacts_dir)
            zf.write(path, arcname)

    total_bytes = sum(f.stat().st_size for f in files)
    print(f"[validation-pack] wrote {output_path} ({len(files)} files, {total_bytes} bytes)")


if __name__ == "__main__":  # pragma: no cover
    main()
