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
import math
import os
import pathlib
import re
import subprocess
import sys

try:
    import matplotlib.pyplot as plt
    import matplotlib.image as mpimg
    from matplotlib.backends.backend_pdf import PdfPages
except ImportError:  # pragma: no cover - dependency bootstrap
    subprocess.check_call([sys.executable, "-m", "pip", "install", "--quiet", "matplotlib"])
    import matplotlib.pyplot as plt
    import matplotlib.image as mpimg
    from matplotlib.backends.backend_pdf import PdfPages

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

def run_cli_json(args):
    output = run_cli([*args, "--json"])
    return json.loads(output)

MC_OUTPUT_RE = re.compile(r"^([0-9eE+\-.]+) \(se=([0-9eE+\-.]+), 95% CI=\[([0-9eE+\-.]+), ([0-9eE+\-.]+)\]\)$")
PDE_OUTPUT_RE = re.compile(r"^([0-9eE+\-.]+) \(delta=([0-9eE+\-.]+), gamma=([0-9eE+\-.]+)(?:, theta=([0-9eE+\-.]+))?\)$")

def mc_price_and_error(params):
    args = [
        "mc",
        params["spot"],
        params["strike"],
        params["rate"],
        params["dividend"],
        params["vol"],
        params["tenor"],
        params["paths"],
        params["seed"],
        1 if params.get("antithetic", 0) else 0,
        params.get("qmc_mode", "none"),
    ]
    bridge_mode = params.get("bridge_mode", "none")
    if bridge_mode is not None:
        args.append(bridge_mode)
    num_steps = params.get("num_steps", 1)
    if num_steps is not None:
        args.append(int(num_steps))

    # Prefer JSON output for determinism metadata and robust parsing
    res = run_cli_json(args)
    price = float(res.get("price"))
    std_error = float(res.get("std_error", 0.0))
    ci_low = float(res.get("ci_low", price))
    ci_high = float(res.get("ci_high", price))
    return price, std_error, ci_low, ci_high

SQRT_2PI = math.sqrt(2.0 * math.pi)

def normal_pdf(x: float) -> float:
    return math.exp(-0.5 * x * x) / SQRT_2PI

def normal_cdf(x: float) -> float:
    return 0.5 * math.erfc(-x / math.sqrt(2.0))

def bs_d1(S, K, r, q, sigma, T):
    return (math.log(S / K) + (r - q + 0.5 * sigma * sigma) * T) / (sigma * math.sqrt(T))

def bs_delta_call(S, K, r, q, sigma, T):
    return math.exp(-q * T) * normal_cdf(bs_d1(S, K, r, q, sigma, T))

def bs_delta_put(S, K, r, q, sigma, T):
    return bs_delta_call(S, K, r, q, sigma, T) - math.exp(-q * T)

def bs_gamma(S, K, r, q, sigma, T):
    return math.exp(-q * T) * normal_pdf(bs_d1(S, K, r, q, sigma, T)) / (S * sigma * math.sqrt(T))

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
    "antithetic": True,
    "qmc_mode": "none",
    "bridge_mode": "none",
    "num_steps": 1,
}
mc_price, mc_std_error, mc_ci_low, mc_ci_high = mc_price_and_error(mc_params)
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

atm_params = {
    "spot": 100.0,
    "strike": 100.0,
    "rate": 0.02,
    "dividend": 0.0,
    "vol": 0.2,
    "tenor": 1.0,
}
atm_reference = float(run_cli([
    "bs",
    atm_params["spot"],
    atm_params["strike"],
    atm_params["rate"],
    atm_params["dividend"],
    atm_params["vol"],
    atm_params["tenor"],
    "call",
]))

paths_grid = [20000, 40000, 80000, 160000, 320000]
rmse_rows = []
prng_rmse_values = []
qmc_rmse_values = []

for paths in paths_grid:
    common = {
        "spot": atm_params["spot"],
        "strike": atm_params["strike"],
        "rate": atm_params["rate"],
        "dividend": atm_params["dividend"],
        "vol": atm_params["vol"],
        "tenor": atm_params["tenor"],
        "paths": paths,
        "seed": mc_seed,
        "antithetic": True,
        "num_steps": 64,
    }

    prng_params = dict(common)
    prng_params["qmc_mode"] = "none"
    prng_params["bridge_mode"] = "none"

    qmc_params = dict(common)
    qmc_params["qmc_mode"] = "sobol"
    qmc_params["bridge_mode"] = "bb"

    prng_price, prng_se, prng_ci_low, prng_ci_high = mc_price_and_error(prng_params)
    qmc_price, qmc_se, qmc_ci_low, qmc_ci_high = mc_price_and_error(qmc_params)

    prng_err = abs(prng_price - atm_reference)
    qmc_err = abs(qmc_price - atm_reference)
    prng_rmse = math.sqrt(prng_err * prng_err + prng_se * prng_se)
    qmc_rmse = math.sqrt(qmc_err * qmc_err + qmc_se * qmc_se)

    rmse_rows.append({
        "paths": paths,
        "prng_price": prng_price,
        "prng_se": prng_se,
        "qmc_price": qmc_price,
        "qmc_se": qmc_se,
        "prng_ci_low": prng_ci_low,
        "prng_ci_high": prng_ci_high,
        "qmc_ci_low": qmc_ci_low,
        "qmc_ci_high": qmc_ci_high,
        "prng_rmse": prng_rmse,
        "qmc_rmse": qmc_rmse,
        "rmse_ratio": prng_rmse / qmc_rmse if qmc_rmse > 0 else float("inf"),
    })
    prng_rmse_values.append(prng_rmse)
    qmc_rmse_values.append(qmc_rmse)

with open(artifact_dir / "qmc_vs_prng.csv", "w", newline="") as fh:
    writer = csv.DictWriter(fh, fieldnames=[
        "paths", "prng_price", "prng_se", "prng_ci_low", "prng_ci_high",
        "qmc_price", "qmc_se", "qmc_ci_low", "qmc_ci_high",
        "prng_rmse", "qmc_rmse", "rmse_ratio"
    ])
    writer.writeheader()
    for row in rmse_rows:
        writer.writerow({
            "paths": row["paths"],
            "prng_price": f"{row['prng_price']:.6f}",
            "prng_se": f"{row['prng_se']:.6f}",
            "qmc_price": f"{row['qmc_price']:.6f}",
            "qmc_se": f"{row['qmc_se']:.6f}",
            "prng_ci_low": f"{row['prng_ci_low']:.6f}",
            "prng_ci_high": f"{row['prng_ci_high']:.6f}",
            "qmc_ci_low": f"{row['qmc_ci_low']:.6f}",
            "qmc_ci_high": f"{row['qmc_ci_high']:.6f}",
            "prng_rmse": f"{row['prng_rmse']:.6f}",
            "qmc_rmse": f"{row['qmc_rmse']:.6f}",
            "rmse_ratio": f"{row['rmse_ratio']:.3f}",
        })

plt.figure(figsize=(6.0, 4.0))
plt.loglog(paths_grid, prng_rmse_values, marker="o", label="PRNG (Euler)")
plt.loglog(paths_grid, qmc_rmse_values, marker="o", label="Sobol + Brownian bridge")
plt.xlabel("Paths")
plt.ylabel("RMSE")
plt.title("ATM call RMSE vs paths (num_steps=64)")
plt.grid(True, which="both", linestyle="--", alpha=0.4)
plt.legend()
plt.tight_layout()
plt.savefig(artifact_dir / "qmc_vs_prng.png", dpi=200)
plt.close()

rmse_ratio_values = [row["rmse_ratio"] for row in rmse_rows]

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
pde_output = run_cli([
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
    2.5,
    1,
])
pde_match = PDE_OUTPUT_RE.match(pde_output)
if not pde_match:
    raise RuntimeError(f"Unexpected PDE output format: {pde_output}")
pde_price = float(pde_match.group(1))
pde_delta = float(pde_match.group(2))
pde_gamma = float(pde_match.group(3))
pde_theta = float(pde_match.group(4)) if pde_match.group(4) is not None else None
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
bs_delta_reference = bs_delta_call(
    pde_params["spot"],
    pde_params["strike"],
    pde_params["rate"],
    pde_params["dividend"],
    pde_params["vol"],
    pde_params["tenor"],
)
bs_gamma_reference = bs_gamma(
    pde_params["spot"],
    pde_params["strike"],
    pde_params["rate"],
    pde_params["dividend"],
    pde_params["vol"],
    pde_params["tenor"],
)
pde_delta_err = abs(pde_delta - bs_delta_reference)
pde_gamma_err = abs(pde_gamma - bs_gamma_reference)

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
        "engine", "spot", "strike", "rate", "dividend", "vol", "tenor", "paths", "seed", "antithetic", "qmc_mode", "bridge", "num_steps", "price", "std_error", "ci_low", "ci_high", "reference", "abs_error"
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
        "qmc_mode": mc_params["qmc_mode"],
        "bridge": mc_params["bridge_mode"],
        "num_steps": mc_params["num_steps"],
        "price": f"{mc_price:.6f}",
        "std_error": f"{mc_std_error:.6f}",
        "ci_low": f"{mc_ci_low:.6f}",
        "ci_high": f"{mc_ci_high:.6f}",
        "reference": f"{mc_reference:.6f}",
        "abs_error": f"{abs(mc_price - mc_reference):.6f}",
    })

with open(artifact_dir / "pde.csv", "w", newline="") as fh:
    writer = csv.DictWriter(fh, fieldnames=[
        "engine", "spot", "strike", "rate", "dividend", "vol", "tenor", "type", "m", "n", "smax_mult", "log_space", "upper_boundary", "stretch", "price", "delta", "gamma", "theta", "reference", "abs_error"
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
        "stretch": 2.5,
        "price": f"{pde_price:.6f}",
        "delta": f"{pde_delta:.6f}",
        "gamma": f"{pde_gamma:.6f}",
        "theta": f"{pde_theta:.6f}" if pde_theta is not None else "",
        "reference": f"{pde_reference:.6f}",
        "abs_error": f"{abs(pde_price - pde_reference):.6f}",
    })

grids = [
    (101, 100),
    (201, 200),
    (401, 400),
    (801, 400),
]
pde_conv_rows = []
price_errors = []
for M_nodes, N_steps in grids:
    output = run_cli([
        "pde",
        pde_params["spot"],
        pde_params["strike"],
        pde_params["rate"],
        pde_params["dividend"],
        pde_params["vol"],
        pde_params["tenor"],
        pde_params["type"],
        M_nodes,
        N_steps,
        pde_params["smax_mult"],
        1,
        1,
        2.5,
        1,
    ])
    match = PDE_OUTPUT_RE.match(output)
    if not match:
        raise RuntimeError(f"Unexpected PDE output format in convergence study: {output}")
    price = float(match.group(1))
    delta_val = float(match.group(2))
    gamma_val = float(match.group(3))
    price_err = abs(price - pde_reference)
    delta_err = abs(delta_val - bs_delta_reference)
    gamma_err = abs(gamma_val - bs_gamma_reference)
    price_errors.append(price_err)
    pde_conv_rows.append({
        "M": M_nodes,
        "N": N_steps,
        "price": price,
        "delta": delta_val,
        "gamma": gamma_val,
        "price_err": price_err,
        "delta_err": delta_err,
        "gamma_err": gamma_err,
    })

with open(artifact_dir / "pde_convergence.csv", "w", newline="") as fh:
    writer = csv.DictWriter(fh, fieldnames=["M", "N", "price", "delta", "gamma", "price_err", "delta_err", "gamma_err"])
    writer.writeheader()
    for row in pde_conv_rows:
        writer.writerow({
            "M": row["M"],
            "N": row["N"],
            "price": f"{row['price']:.6f}",
            "delta": f"{row['delta']:.6f}",
            "gamma": f"{row['gamma']:.6f}",
            "price_err": f"{row['price_err']:.6e}",
            "delta_err": f"{row['delta_err']:.6e}",
            "gamma_err": f"{row['gamma_err']:.6e}",
        })

def log_slope(xs, ys):
    logx = [math.log(x) for x in xs]
    logy = [math.log(y) for y in ys]
    x_mean = sum(logx) / len(logx)
    y_mean = sum(logy) / len(logy)
    numerator = sum((lx - x_mean) * (ly - y_mean) for lx, ly in zip(logx, logy))
    denominator = sum((lx - x_mean) ** 2 for lx in logx)
    return numerator / denominator if denominator > 0 else float("nan")

slope = log_slope([row["M"] for row in pde_conv_rows], price_errors)

plt.figure(figsize=(6.0, 4.0))
plt.loglog([row["M"] for row in pde_conv_rows], price_errors, marker="o", label=f"Price error (slope~{slope:.2f})")
plt.xlabel("Spatial nodes (M)")
plt.ylabel("|Price - BS|")
plt.title("Crank–Nicolson with Rannacher start")
plt.grid(True, which="both", linestyle="--", alpha=0.4)
plt.legend()
plt.tight_layout()
plt.savefig(artifact_dir / "pde_convergence.png", dpi=200)
plt.close()

american_params = {
    "spot": 100.0,
    "strike": 100.0,
    "rate": 0.05,
    "dividend": 0.02,
    "vol": 0.25,
    "tenor": 1.0,
    "type": "put",
}

psor_reference = run_cli_json([
    "american", "psor", american_params["type"],
    american_params["spot"], american_params["strike"], american_params["rate"],
    american_params["dividend"], american_params["vol"], american_params["tenor"],
    241, 240, 5.0, 1, 1, 2.5, 1.5, 9000, 1e-8,
])
psor_ref_price = psor_reference["price"]
psor_ref_iterations = psor_reference["iterations"]
psor_ref_residual = psor_reference["max_residual"]

binomial_steps = [32, 64, 128, 256, 512]
binomial_rows = []
for steps in binomial_steps:
    result = run_cli_json([
        "american", "binomial", american_params["type"],
        american_params["spot"], american_params["strike"], american_params["rate"],
        american_params["dividend"], american_params["vol"], american_params["tenor"],
        steps,
    ])
    price = result["price"]
    error = abs(price - psor_ref_price)
    binomial_rows.append({"steps": steps, "price": price, "abs_err": error})

psor_configs = [
    (121, 120, 1.8),
    (181, 180, 2.0),
    (241, 240, 2.5),
]
psor_rows = []
for M_nodes, N_steps, stretch in psor_configs:
    result = run_cli_json([
        "american", "psor", american_params["type"],
        american_params["spot"], american_params["strike"], american_params["rate"],
        american_params["dividend"], american_params["vol"], american_params["tenor"],
        M_nodes, N_steps, 5.0, 1, 1, stretch, 1.5, 9000, 1e-8,
    ])
    price = result["price"]
    error = abs(price - psor_ref_price)
    psor_rows.append({
        "M": M_nodes,
        "N": N_steps,
        "stretch": stretch,
        "price": price,
        "abs_err": error,
        "iterations": result["iterations"],
        "residual": result["max_residual"],
    })

lsmc_result = run_cli_json([
    "american", "lsmc", american_params["type"],
    american_params["spot"], american_params["strike"], american_params["rate"],
    american_params["dividend"], american_params["vol"], american_params["tenor"],
    200000, 50, 20250217, 0,
])
lsmc_price = lsmc_result["price"]
lsmc_std_error = lsmc_result["std_error"]

with open(artifact_dir / "american_validation.csv", "w", newline="") as fh:
    writer = csv.DictWriter(fh, fieldnames=[
        "method", "resolution", "price", "abs_error", "extra"
    ])
    writer.writeheader()
    writer.writerow({
        "method": "psor_reference",
        "resolution": "241x240",
        "price": f"{psor_ref_price:.6f}",
        "abs_error": "0.000000",
        "extra": f"iterations={psor_ref_iterations}, residual={psor_ref_residual:.2e}",
    })
    for row in psor_rows:
        writer.writerow({
            "method": "psor",
            "resolution": f"{row['M']}x{row['N']}",
            "price": f"{row['price']:.6f}",
            "abs_error": f"{row['abs_err']:.6f}",
            "extra": f"iterations={row['iterations']}, residual={row['residual']:.2e}",
        })
    for row in binomial_rows:
        writer.writerow({
            "method": "binomial",
            "resolution": row["steps"],
            "price": f"{row['price']:.6f}",
            "abs_error": f"{row['abs_err']:.6f}",
            "extra": "",
        })
    writer.writerow({
        "method": "lsmc",
        "resolution": 200000,
        "price": f"{lsmc_price:.6f}",
        "abs_error": f"{abs(lsmc_price - psor_ref_price):.6f}",
        "extra": f"std_error={lsmc_std_error:.6f}",
    })

plt.figure(figsize=(6.0, 4.0))
plt.loglog([row["steps"] for row in binomial_rows], [row["abs_err"] for row in binomial_rows], marker="o", label="Binomial |error|")
plt.loglog([row["M"] for row in psor_rows], [row["abs_err"] for row in psor_rows], marker="s", label="PSOR |error|")
plt.axhline(lsmc_std_error, color="tab:green", linestyle="--", label="LSMC SE")
plt.xlabel("Resolution (steps or spatial nodes)")
plt.ylabel("|Price - PSOR_ref|")
plt.title("American put convergence")
plt.grid(True, which="both", linestyle="--", alpha=0.4)
plt.legend()
plt.tight_layout()
plt.savefig(artifact_dir / "american_convergence.png", dpi=200)
plt.close()

barrier_cases = [
    {
        "name": "down_out_call",
        "opt": "call",
        "dir": "down",
        "style": "out",
        "spot": 100.0,
        "strike": 95.0,
        "barrier": 90.0,
        "rebate": 0.0,
        "rate": 0.02,
        "dividend": 0.0,
        "vol": 0.20,
        "tenor": 1.0,
    },
    {
        "name": "up_out_put",
        "opt": "put",
        "dir": "up",
        "style": "out",
        "spot": 100.0,
        "strike": 105.0,
        "barrier": 120.0,
        "rebate": 0.0,
        "rate": 0.02,
        "dividend": 0.0,
        "vol": 0.25,
        "tenor": 1.0,
    },
]

barrier_rows = []
barrier_labels = []
barrier_mc_abs_errors = []
barrier_pde_abs_errors = []

for case in barrier_cases:
    args_bs = [
        "barrier", "bs", case["opt"], case["dir"], case["style"],
        case["spot"], case["strike"], case["barrier"], case["rebate"],
        case["rate"], case["dividend"], case["vol"], case["tenor"],
    ]
    bs_barrier = float(run_cli(args_bs))

    mc_cli = [
        "barrier", "mc", case["opt"], case["dir"], case["style"],
        case["spot"], case["strike"], case["barrier"], case["rebate"],
        case["rate"], case["dividend"], case["vol"], case["tenor"],
        mc_paths, mc_seed, 1, "none", "bb", 32,
    ]
    mc_out = run_cli(mc_cli)
    mc_match = MC_OUTPUT_RE.match(mc_out)
    if not mc_match:
        raise RuntimeError(f"Unexpected barrier MC output: {mc_out}")
    mc_barrier = float(mc_match.group(1))
    mc_barrier_se = float(mc_match.group(2))
    mc_barrier_ci_low = float(mc_match.group(3))
    mc_barrier_ci_high = float(mc_match.group(4))

    pde_cli = [
        "barrier", "pde", case["opt"], case["dir"], case["style"],
        case["spot"], case["strike"], case["barrier"], case["rebate"],
        case["rate"], case["dividend"], case["vol"], case["tenor"],
        201, 200, 4.0,
    ]
    pde_barrier = float(run_cli(pde_cli))

    mc_abs_err = abs(mc_barrier - bs_barrier)
    pde_abs_err = abs(pde_barrier - bs_barrier)

    barrier_rows.append({
        "name": case["name"],
        "option": case["opt"],
        "direction": case["dir"],
        "style": case["style"],
        "spot": case["spot"],
        "strike": case["strike"],
        "barrier": case["barrier"],
        "rebate": case["rebate"],
        "rate": case["rate"],
        "dividend": case["dividend"],
        "vol": case["vol"],
        "tenor": case["tenor"],
        "bs": bs_barrier,
        "mc": mc_barrier,
        "mc_se": mc_barrier_se,
        "pde": pde_barrier,
        "mc_abs_err": mc_abs_err,
        "pde_abs_err": pde_abs_err,
        "mc_ci_low": mc_barrier_ci_low,
        "mc_ci_high": mc_barrier_ci_high,
    })
    barrier_labels.append(case["name"])
    barrier_mc_abs_errors.append(mc_abs_err)
    barrier_pde_abs_errors.append(pde_abs_err)

with open(artifact_dir / "barrier_validation.csv", "w", newline="") as fh:
    writer = csv.DictWriter(fh, fieldnames=[
        "name", "option", "direction", "style", "spot", "strike", "barrier", "rebate",
        "rate", "dividend", "vol", "tenor", "bs", "mc", "mc_se", "mc_ci_low", "mc_ci_high",
        "pde", "mc_abs_err", "pde_abs_err"
    ])
    writer.writeheader()
    for row in barrier_rows:
        writer.writerow({
            "name": row["name"],
            "option": row["option"],
            "direction": row["direction"],
            "style": row["style"],
            "spot": f"{row['spot']:.2f}",
            "strike": f"{row['strike']:.2f}",
            "barrier": f"{row['barrier']:.2f}",
            "rebate": f"{row['rebate']:.2f}",
            "rate": f"{row['rate']:.4f}",
            "dividend": f"{row['dividend']:.4f}",
            "vol": f"{row['vol']:.4f}",
            "tenor": f"{row['tenor']:.4f}",
            "bs": f"{row['bs']:.6f}",
            "mc": f"{row['mc']:.6f}",
            "mc_se": f"{row['mc_se']:.6f}",
            "mc_ci_low": f"{row['mc_ci_low']:.6f}",
            "mc_ci_high": f"{row['mc_ci_high']:.6f}",
            "pde": f"{row['pde']:.6f}",
            "mc_abs_err": f"{row['mc_abs_err']:.6f}",
            "pde_abs_err": f"{row['pde_abs_err']:.6f}",
        })

plt.figure(figsize=(6.0, 4.0))
indices = range(len(barrier_labels))
plt.bar([i - 0.15 for i in indices], barrier_mc_abs_errors, width=0.3, label="|MC - RR|")
plt.bar([i + 0.15 for i in indices], barrier_pde_abs_errors, width=0.3, label="|PDE - RR|")
plt.xticks(list(indices), barrier_labels, rotation=15)
plt.ylabel("Absolute error")
plt.title("Barrier pricing validation")
plt.yscale("log")
plt.grid(True, which="both", axis="y", linestyle="--", alpha=0.4)
plt.legend()
plt.tight_layout()
plt.savefig(artifact_dir / "barrier_validation.png", dpi=200)
plt.close()

pdf_path = artifact_dir / "onepager.pdf"
with PdfPages(pdf_path) as pdf:
    fig, axes = plt.subplots(2, 2, figsize=(11.0, 8.5))
    plots = [
        (artifact_dir / "qmc_vs_prng.png", "MC RMSE (PRNG vs Sobol)"),
        (artifact_dir / "pde_convergence.png", "PDE convergence"),
        (artifact_dir / "american_convergence.png", "American convergence"),
        (artifact_dir / "barrier_validation.png", "Barrier validation"),
    ]
    for ax, (img_path, title) in zip(axes.flatten(), plots):
        img = mpimg.imread(img_path)
        ax.imshow(img)
        ax.set_title(title)
        ax.axis("off")
    pdf.savefig(fig)
    plt.close(fig)

# Generate extra figures (Greeks variance, multi-asset)
try:
    # Greeks variance (requires bindings)
    subprocess.check_call([sys.executable, str(root / 'scripts' / 'greeks_variance.py'), '--artifacts', str(artifact_dir)])
except Exception as e:
    print('warn: greeks variance figure failed:', e)

try:
    # Multi-asset (requires bindings)
    subprocess.check_call([sys.executable, str(root / 'scripts' / 'multiasset_figures.py'), '--artifacts', str(artifact_dir)])
except Exception as e:
    print('warn: multiasset figures failed:', e)

# Two-pager PDF with extra figures (if present)
twopager = artifact_dir / 'twopager.pdf'
with PdfPages(twopager) as pdf2:
    # Page 1: reuse onepager content
    fig, axes = plt.subplots(2, 2, figsize=(11.0, 8.5))
    for ax, (img_path, title) in zip(axes.flatten(), plots):
        img = mpimg.imread(img_path)
        ax.imshow(img)
        ax.set_title(title)
        ax.axis('off')
    pdf2.savefig(fig)
    plt.close(fig)
    # Page 2: new figures if available
    extra_imgs = []
    for name, title in [
        ('greeks_variance.png', 'Gamma estimator variance'),
        ('basket_correlation.png', 'Basket price vs correlation'),
        ('merton_lambda.png', 'Merton price vs lambda'),
    ]:
        path = artifact_dir / name
        if path.exists():
            extra_imgs.append((path, title))
    if extra_imgs:
        rows = 1
        cols = len(extra_imgs)
        fig, axes = plt.subplots(rows, cols, figsize=(11.0, 4.5))
        if cols == 1:
            axes = [axes]
        for ax, (img_path, title) in zip(axes, extra_imgs):
            img = mpimg.imread(img_path)
            ax.imshow(img)
            ax.set_title(title)
            ax.axis('off')
        pdf2.savefig(fig)
        plt.close(fig)

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
        "qmc_mode": mc_params["qmc_mode"],
        "bridge": mc_params["bridge_mode"],
        "seed": mc_seed,
        "paths": mc_paths,
        "antithetic": True,
        "num_steps": mc_params["num_steps"],
        "price": round(mc_price, 6),
        "std_error": round(mc_std_error, 6),
        "ci_low": round(mc_ci_low, 6),
        "ci_high": round(mc_ci_high, 6),
        # capture threads used via JSON query
        "threads": run_cli_json([
            "mc",
            mc_params["spot"], mc_params["strike"], mc_params["rate"], mc_params["dividend"], mc_params["vol"], mc_params["tenor"],
            mc_params["paths"], mc_params["seed"], 1, mc_params["qmc_mode"], mc_params["bridge_mode"], mc_params["num_steps"],
        ]).get("threads", 1),
    },
    "qmc_vs_prng": {
        "paths": paths_grid,
        "prng_rmse": [round(v, 6) for v in prng_rmse_values],
        "qmc_rmse": [round(v, 6) for v in qmc_rmse_values],
        "rmse_ratio": [round(v, 3) for v in rmse_ratio_values],
        "prng_ci_low": [round(row["prng_ci_low"], 6) for row in rmse_rows],
        "prng_ci_high": [round(row["prng_ci_high"], 6) for row in rmse_rows],
        "qmc_ci_low": [round(row["qmc_ci_low"], 6) for row in rmse_rows],
        "qmc_ci_high": [round(row["qmc_ci_high"], 6) for row in rmse_rows],
    },
    "pde": {
        "engine": "pde",
        "spot": round(pde_params["spot"], 6),
        "strike": round(pde_params["strike"], 6),
        "rate": round(pde_params["rate"], 6),
        "dividend": round(pde_params["dividend"], 6),
        "vol": round(pde_params["vol"], 6),
        "tenor": round(pde_params["tenor"], 6),
        "type": pde_params["type"],
        "m": pde_params["m"],
        "n": pde_params["n"],
        "smax_mult": round(pde_params["smax_mult"], 6),
        "log_space": bool(pde_params["log_space"]),
        "upper_boundary": "neumann" if pde_params["neumann"] else "dirichlet",
        "stretch": 2.5,
        "price": round(pde_price, 6),
        "delta": round(pde_delta, 6),
        "gamma": round(pde_gamma, 6),
        "theta": round(pde_theta, 6) if pde_theta is not None else None,
        "price_abs_error": round(abs(pde_price - pde_reference), 6),
        "delta_abs_error": round(pde_delta_err, 6),
        "gamma_abs_error": round(pde_gamma_err, 6),
    },
    "pde_convergence": {
        "nodes": [row["M"] for row in pde_conv_rows],
        "price_error": [round(v, 6) for v in price_errors],
        "slope": round(slope, 2),
    },
    "american": {
        "reference_price": round(psor_ref_price, 6),
        "reference_iterations": psor_ref_iterations,
        "reference_residual": psor_ref_residual,
        "binomial_steps": [row["steps"] for row in binomial_rows],
        "binomial_abs_error": [round(row["abs_err"], 6) for row in binomial_rows],
        "psor_nodes": [row["M"] for row in psor_rows],
        "psor_abs_error": [round(row["abs_err"], 6) for row in psor_rows],
        "lsmc_price": round(lsmc_price, 6),
        "lsmc_std_error": round(lsmc_std_error, 6),
    },
    "barrier_validation": {
        "cases": barrier_labels,
        "mc_abs_error": [round(v, 6) for v in barrier_mc_abs_errors],
        "pde_abs_error": [round(v, 6) for v in barrier_pde_abs_errors],
        "mc_ci_low": [round(row["mc_ci_low"], 6) for row in barrier_rows],
        "mc_ci_high": [round(row["mc_ci_high"], 6) for row in barrier_rows],
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
