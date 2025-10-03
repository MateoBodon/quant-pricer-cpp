#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
BUILD_TYPE="Release"
BUILD_DIR="${ROOT}/build/demo"
ARTIFACT_DIR="${ROOT}/artifacts"
MC_PATHS=250000
MC_SEED=424242

cmake -S "${ROOT}" -B "${BUILD_DIR}" -DCMAKE_BUILD_TYPE="${BUILD_TYPE}"
cmake --build "${BUILD_DIR}" --config "${BUILD_TYPE}"

CLI=""
for candidate in \
  "${BUILD_DIR}/quant_cli" \
  "${BUILD_DIR}/${BUILD_TYPE}/quant_cli" \
  "${BUILD_DIR}/quant_cli.exe" \
  "${BUILD_DIR}/${BUILD_TYPE}/quant_cli.exe"; do
  if [[ -x "${candidate}" ]]; then
    CLI="${candidate}"
    break
  fi
done

if [[ -z "${CLI}" ]]; then
  echo "error: quant_cli executable not found after build" >&2
  exit 1
fi

rm -rf "${ARTIFACT_DIR}"
mkdir -p "${ARTIFACT_DIR}"

CACHE_FILE="${BUILD_DIR}/CMakeCache.txt"
if [[ ! -f "${CACHE_FILE}" ]]; then
  echo "error: expected CMake cache at ${CACHE_FILE}" >&2
  exit 1
fi

GIT_SHA=$(git -C "${ROOT}" rev-parse HEAD)

ROOT="${ROOT}" \
CLI="${CLI}" \
ARTIFACT_DIR="${ARTIFACT_DIR}" \
CACHE_FILE="${CACHE_FILE}" \
BUILD_TYPE="${BUILD_TYPE}" \
MC_PATHS="${MC_PATHS}" \
MC_SEED="${MC_SEED}" \
GIT_SHA="${GIT_SHA}" \
python3 - <<'PY'
import csv
import datetime as dt
import json
import os
import pathlib
import re
import subprocess

root = pathlib.Path(os.environ["ROOT"])
cli = pathlib.Path(os.environ["CLI"])
artifact_dir = pathlib.Path(os.environ["ARTIFACT_DIR"])
cache_file = pathlib.Path(os.environ["CACHE_FILE"])
build_type = os.environ["BUILD_TYPE"]
mc_paths = int(os.environ["MC_PATHS"])
mc_seed = int(os.environ["MC_SEED"])
git_sha = os.environ["GIT_SHA"]

def run_cli(args):
    result = subprocess.check_output([str(cli), *map(str, args)], text=True)
    return result.strip()

# Parse compiler info from CMake cache
cache_entries = {}
for line in cache_file.read_text().splitlines():
    if not line or line.startswith("//") or line.startswith("#"):
        continue
    if ":" not in line or "=" not in line:
        continue
    key_type, value = line.split("=", 1)
    key, *_ = key_type.split(":", 1)
    cache_entries[key] = value

compiler_info = {
    "id": cache_entries.get("CMAKE_CXX_COMPILER_ID", ""),
    "version": cache_entries.get("CMAKE_CXX_COMPILER_VERSION", ""),
    "path": cache_entries.get("CMAKE_CXX_COMPILER", ""),
}

if not compiler_info["id"] or not compiler_info["version"]:
    compiler_cmake = None
    comp_dir = cache_file.parent / "CMakeFiles"
    if comp_dir.exists():
        candidates = list(comp_dir.glob("**/CMakeCXXCompiler.cmake"))
        if candidates:
            compiler_cmake = candidates[0]
    if compiler_cmake and compiler_cmake.is_file():
        text = compiler_cmake.read_text()
        if not compiler_info["id"]:
            match = re.search(r'set\(CMAKE_CXX_COMPILER_ID "([^"]+)"\)', text)
            if match:
                compiler_info["id"] = match.group(1)
        if not compiler_info["version"]:
            match = re.search(r'set\(CMAKE_CXX_COMPILER_VERSION "([^"]+)"\)', text)
            if match:
                compiler_info["version"] = match.group(1)

flags_info = {
    "cxx_flags": cache_entries.get("CMAKE_CXX_FLAGS", ""),
    "cxx_flags_release": cache_entries.get("CMAKE_CXX_FLAGS_RELEASE", ""),
}

# Black-Scholes validation (analytic)
bs_params = {
    "spot": 100.0,
    "strike": 100.0,
    "rate": 0.05,
    "dividend": 0.0,
    "vol": 0.2,
    "tenor": 1.0,
    "type": "call",
}
bs_reference = 10.4506
bs_price = float(run_cli([
    "bs",
    bs_params["spot"],
    bs_params["strike"],
    bs_params["rate"],
    bs_params["dividend"],
    bs_params["vol"],
    bs_params["tenor"],
    bs_params["type"],
]))

# Monte Carlo validation
mc_params = {
    "spot": 100.0,
    "strike": 105.0,
    "rate": 0.03,
    "dividend": 0.01,
    "vol": 0.25,
    "tenor": 0.75,
    "paths": mc_paths,
    "seed": mc_seed,
    "antithetic": 1,
    "qmc": 0,
}
mc_output = run_cli([
    "mc",
    mc_params["spot"],
    mc_params["strike"],
    mc_params["rate"],
    mc_params["dividend"],
    mc_params["vol"],
    mc_params["tenor"],
    mc_params["paths"],
    mc_params["seed"],
    mc_params["antithetic"],
    mc_params["qmc"],
])
mc_match = re.match(r"^([0-9eE+\-.]+) \(se=([0-9eE+\-.]+)\)$", mc_output)
if not mc_match:
    raise RuntimeError(f"Unexpected Monte Carlo output format: {mc_output}")
mc_price = float(mc_match.group(1))
mc_std_error = float(mc_match.group(2))
mc_reference = float(run_cli([
    "bs",
    mc_params["spot"],
    mc_params["strike"],
    mc_params["rate"],
    mc_params["dividend"],
    mc_params["vol"],
    mc_params["tenor"],
    "call",
]))

# PDE validation
pde_params = {
    "spot": 100.0,
    "strike": 100.0,
    "rate": 0.02,
    "dividend": 0.0,
    "vol": 0.2,
    "tenor": 1.0,
    "type": "call",
    "m": 201,
    "n": 200,
    "smax_mult": 4.0,
    "log_space": 1,
    "neumann": 1,
}
pde_price = float(run_cli([
    "pde",
    pde_params["spot"],
    pde_params["strike"],
    pde_params["rate"],
    pde_params["dividend"],
    pde_params["vol"],
    pde_params["tenor"],
    pde_params["type"],
    pde_params["m"],
    pde_params["n"],
    pde_params["smax_mult"],
    pde_params["log_space"],
    pde_params["neumann"],
]))
pde_reference = float(run_cli([
    "bs",
    pde_params["spot"],
    pde_params["strike"],
    pde_params["rate"],
    pde_params["dividend"],
    pde_params["vol"],
    pde_params["tenor"],
    pde_params["type"],
]))

# Write CSV artifacts
with open(artifact_dir / "black_scholes.csv", "w", newline="") as fh:
    writer = csv.DictWriter(fh, fieldnames=[
        "engine", "spot", "strike", "rate", "dividend", "vol", "tenor", "type", "price", "reference", "abs_error"
    ])
    writer.writeheader()
    writer.writerow({
        "engine": "black_scholes",
        "spot": f"{bs_params['spot']:.2f}",
        "strike": f"{bs_params['strike']:.2f}",
        "rate": f"{bs_params['rate']:.4f}",
        "dividend": f"{bs_params['dividend']:.4f}",
        "vol": f"{bs_params['vol']:.4f}",
        "tenor": f"{bs_params['tenor']:.4f}",
        "type": bs_params["type"],
        "price": f"{bs_price:.6f}",
        "reference": f"{bs_reference:.6f}",
        "abs_error": f"{abs(bs_price - bs_reference):.6f}",
    })

with open(artifact_dir / "monte_carlo.csv", "w", newline="") as fh:
    writer = csv.DictWriter(fh, fieldnames=[
        "engine", "spot", "strike", "rate", "dividend", "vol", "tenor", "paths", "seed", "antithetic", "rng", "price", "std_error", "reference", "abs_error"
    ])
    writer.writeheader()
    writer.writerow({
        "engine": "monte_carlo",
        "spot": f"{mc_params['spot']:.2f}",
        "strike": f"{mc_params['strike']:.2f}",
        "rate": f"{mc_params['rate']:.4f}",
        "dividend": f"{mc_params['dividend']:.4f}",
        "vol": f"{mc_params['vol']:.4f}",
        "tenor": f"{mc_params['tenor']:.4f}",
        "paths": mc_params["paths"],
        "seed": mc_params["seed"],
        "antithetic": bool(mc_params["antithetic"]),
        "rng": "pseudorandom",
        "price": f"{mc_price:.6f}",
        "std_error": f"{mc_std_error:.6f}",
        "reference": f"{mc_reference:.6f}",
        "abs_error": f"{abs(mc_price - mc_reference):.6f}",
    })

with open(artifact_dir / "pde.csv", "w", newline="") as fh:
    writer = csv.DictWriter(fh, fieldnames=[
        "engine", "spot", "strike", "rate", "dividend", "vol", "tenor", "type", "m", "n", "smax_mult", "log_space", "upper_boundary", "price", "reference", "abs_error"
    ])
    writer.writeheader()
    writer.writerow({
        "engine": "pde",
        "spot": f"{pde_params['spot']:.2f}",
        "strike": f"{pde_params['strike']:.2f}",
        "rate": f"{pde_params['rate']:.4f}",
        "dividend": f"{pde_params['dividend']:.4f}",
        "vol": f"{pde_params['vol']:.4f}",
        "tenor": f"{pde_params['tenor']:.4f}",
        "type": pde_params["type"],
        "m": pde_params["m"],
        "n": pde_params["n"],
        "smax_mult": f"{pde_params['smax_mult']:.2f}",
        "log_space": bool(pde_params["log_space"]),
        "upper_boundary": "neumann" if pde_params["neumann"] else "dirichlet",
        "price": f"{pde_price:.6f}",
        "reference": f"{pde_reference:.6f}",
        "abs_error": f"{abs(pde_price - pde_reference):.6f}",
    })

# Manifest JSON
try:
    cli_rel = str(cli.relative_to(root))
except ValueError:
    cli_rel = str(cli)

manifest = {
    "generated_at": dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
    "git_sha": git_sha,
    "build_type": build_type,
    "compiler": compiler_info,
    "flags": flags_info,
    "monte_carlo": {
        "rng": "pseudorandom",
        "seed": mc_seed,
        "paths": mc_paths,
        "antithetic": True,
        "price": round(mc_price, 6),
        "std_error": round(mc_std_error, 6),
    },
    "executables": {
        "quant_cli": cli_rel,
    },
}

with open(artifact_dir / "manifest.json", "w") as fh:
    json.dump(manifest, fh, indent=2)
    fh.write("\n")

PY

echo "Artifacts written to ${ARTIFACT_DIR}"
