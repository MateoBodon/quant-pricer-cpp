#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
BUILD_DIR="${BUILD_DIR:-${ROOT}/build}"
BUILD_TYPE="${BUILD_TYPE:-Release}"
ARTIFACT_DIR="${ROOT}/docs/artifacts"
LOG_DIR="${ARTIFACT_DIR}/logs"
BENCH_DIR="${ARTIFACT_DIR}/bench"
WRDS_DIR="${ARTIFACT_DIR}/wrds"
TIMESTAMP="$(date -u +%Y%m%dT%H%M%SZ)"
REPRO_FAST_FLAG="${REPRO_FAST:-0}"
SKIP_SLOW_FLAG="${SKIP_SLOW:-0}"
SKIP_WRDS_FLAG="${SKIP_WRDS:-0}"
BENCH_MIN_TIME="${BENCH_MIN_TIME:-0.05s}"

export PYTHONHASHSEED="${PYTHONHASHSEED:-0}"
export QUANT_BUILD_DIR="${BUILD_DIR}"
FAST_ARGS=()
if [[ "${REPRO_FAST_FLAG}" == "1" ]]; then
  FAST_ARGS=(--fast)
fi

maybe_clean_artifacts() {
  if [[ "${CLEAN_ARTIFACTS:-1}" == "1" ]]; then
    echo "[reproduce] cleaning ${ARTIFACT_DIR}"
    rm -rf "${ARTIFACT_DIR}"
  fi
  mkdir -p "${ARTIFACT_DIR}" "${LOG_DIR}" "${BENCH_DIR}" "${WRDS_DIR}"
}

multi_config=0
configure_build() {
  echo "[reproduce] configuring ${BUILD_TYPE} build in ${BUILD_DIR}"
  cmake -S "${ROOT}" -B "${BUILD_DIR}" -DCMAKE_BUILD_TYPE="${BUILD_TYPE}"
  if [[ -f "${BUILD_DIR}/CMakeCache.txt" ]] && grep -q "CMAKE_CONFIGURATION_TYPES" "${BUILD_DIR}/CMakeCache.txt"; then
    multi_config=1
  else
    multi_config=0
  fi
}

build_all() {
  local args=(--build "${BUILD_DIR}" --parallel)
  if [[ "${multi_config}" == "1" ]]; then
    args+=(--config "${BUILD_TYPE}")
  fi
  cmake "${args[@]}"
}

run_ctest_label() {
  local label="$1"
  shift || true
  local args=("--test-dir" "${BUILD_DIR}" "--output-on-failure" "-VV")
  if [[ "${multi_config}" == "1" ]]; then
    args+=("-C" "${BUILD_TYPE}")
  fi
  echo "[reproduce] running tests (label=${label})"
  CTEST_OUTPUT_ON_FAILURE=1 ctest "${args[@]}" -L "${label}" "$@"
}

find_binary() {
  local name="$1"
  local candidates=(
    "${BUILD_DIR}/${name}"
    "${BUILD_DIR}/${BUILD_TYPE}/${name}"
    "${BUILD_DIR}/${name}.exe"
    "${BUILD_DIR}/${BUILD_TYPE}/${name}.exe"
  )
  for candidate in "${candidates[@]}"; do
    if [[ -x "${candidate}" ]]; then
      echo "${candidate}"
      return 0
    fi
  done
  echo "error: ${name} not found under ${BUILD_DIR}" >&2
  exit 1
}

run_py() {
  local script="${1}"
  shift
  echo "[reproduce] python $(basename "${script}") $*"
  python3 "${script}" "$@"
}

run_py_fast() {
  local script="${1}"
  shift
  if [[ "${#FAST_ARGS[@]}" -gt 0 ]]; then
    run_py "${script}" "${FAST_ARGS[@]}" "$@"
  else
    run_py "${script}" "$@"
  fi
}

generate_figures() {
  local quant_cli="$1"
  run_py_fast "${ROOT}/scripts/qmc_vs_prng_equal_time.py" --output "${ARTIFACT_DIR}/qmc_vs_prng_equal_time.png" --csv "${ARTIFACT_DIR}/qmc_vs_prng_equal_time.csv"
  run_py_fast "${ROOT}/scripts/pde_order_slope.py" --skip-build --output "${ARTIFACT_DIR}/pde_order_slope.png" --csv "${ARTIFACT_DIR}/pde_order_slope.csv"
  run_py_fast "${ROOT}/scripts/mc_greeks_ci.py" --quant-cli "${quant_cli}" --output "${ARTIFACT_DIR}/mc_greeks_ci.png" --csv "${ARTIFACT_DIR}/mc_greeks_ci.csv"
  run_py_fast "${ROOT}/scripts/heston_qe_vs_analytic.py" --quant-cli "${quant_cli}" --output "${ARTIFACT_DIR}/heston_qe_vs_analytic.png" --csv "${ARTIFACT_DIR}/heston_qe_vs_analytic.csv"
  run_py_fast "${ROOT}/scripts/tri_engine_agreement.py" --quant-cli "${quant_cli}" --output "${ARTIFACT_DIR}/tri_engine_agreement.png" --csv "${ARTIFACT_DIR}/tri_engine_agreement.csv"
}

run_benchmarks() {
  mkdir -p "${BENCH_DIR}"
  local bench_mc bench_pde
  bench_mc="$(find_binary bench_mc)"
  bench_pde="$(find_binary bench_pde)"
  local mc_json="${BENCH_DIR}/bench_mc.json"
  local pde_json="${BENCH_DIR}/bench_pde.json"
  echo "[reproduce] running bench_mc -> ${mc_json}"
  "${bench_mc}" --benchmark_min_time="${BENCH_MIN_TIME}" --benchmark_out="${mc_json}" --benchmark_out_format=json
  echo "[reproduce] running bench_pde -> ${pde_json}"
  "${bench_pde}" --benchmark_min_time="${BENCH_MIN_TIME}" --benchmark_out="${pde_json}" --benchmark_out_format=json
  run_py "${ROOT}/scripts/generate_bench_artifacts.py" --mc-json "${mc_json}" --pde-json "${pde_json}" --out-dir "${BENCH_DIR}"
}

run_wrds_pipeline() {
  if [[ "${SKIP_WRDS_FLAG}" == "1" ]]; then
    echo "[reproduce] skipping WRDS pipeline (SKIP_WRDS=1)"
    return
  fi
  mkdir -p "${WRDS_DIR}"
  local -a extra=()
  local symbol_arg="${WRDS_SYMBOL:-SPX}"
  if [[ -n "${WRDS_SYMBOL:-}" ]]; then
    extra+=(--symbol "${WRDS_SYMBOL}")
  fi
  if [[ -n "${WRDS_TRADE_DATE:-}" ]]; then
    extra+=(--trade-date "${WRDS_TRADE_DATE}")
  fi
  if [[ "${WRDS_USE_SAMPLE:-0}" == "1" ]]; then
    extra+=(--use-sample)
  fi
  if [[ "${REPRO_FAST_FLAG}" == "1" ]]; then
    extra+=(--fast)
  fi
  local extra_desc="${extra[*]:-}"
  echo "[reproduce] running WRDS pipeline ${extra_desc}"
  if [[ "${#extra[@]}" -gt 0 ]]; then
    (cd "${ROOT}" && python3 -m wrds_pipeline.pipeline "${extra[@]}")
  else
    (cd "${ROOT}" && python3 -m wrds_pipeline.pipeline)
  fi

  local dateset_path="${WRDS_DATESET:-wrds_pipeline/dateset.yaml}"
  if [[ -f "${ROOT}/${dateset_path}" ]]; then
    local -a multi_extra=(--symbol "${symbol_arg}" --dateset "${dateset_path}")
    if [[ "${WRDS_USE_SAMPLE:-0}" == "1" ]]; then
      multi_extra+=(--use-sample)
    fi
    if [[ "${REPRO_FAST_FLAG}" == "1" ]]; then
      multi_extra+=(--fast)
    fi
    echo "[reproduce] running WRDS multi-date pipeline --dateset ${dateset_path}"
    (cd "${ROOT}" && python3 -m wrds_pipeline.pipeline "${multi_extra[@]}")
  else
    echo "[reproduce] skipping WRDS dateset (missing ${dateset_path})"
  fi
}

finalize_manifest() {
  ROOT_DIR="${ROOT}" python3 - <<'PY'
import os
import sys

root = os.environ["ROOT_DIR"]
scripts_dir = os.path.join(root, "scripts")
if scripts_dir not in sys.path:
    sys.path.insert(0, scripts_dir)
from manifest_utils import update_run

payload = {
    "timestamp": os.environ["TIMESTAMP"],
    "build_dir": os.environ["BUILD_DIR"],
    "build_type": os.environ["BUILD_TYPE"],
    "fast": os.environ.get("REPRO_FAST_FLAG", "0") == "1",
    "skip_slow": os.environ.get("SKIP_SLOW_FLAG", "0") == "1",
    "skip_wrds": os.environ.get("SKIP_WRDS_FLAG", "0") == "1",
    "bench_min_time": os.environ.get("BENCH_MIN_TIME"),
}
update_run("reproduce_all", payload)
PY
}

export BUILD_DIR BUILD_TYPE TIMESTAMP REPRO_FAST_FLAG SKIP_SLOW_FLAG SKIP_WRDS_FLAG BENCH_MIN_TIME

maybe_clean_artifacts
configure_build
build_all

run_ctest_label "FAST"

if [[ "${SKIP_SLOW_FLAG}" != "1" ]]; then
  slow_log="${LOG_DIR}/slow_${TIMESTAMP}.log"
  slow_junit="${LOG_DIR}/slow_${TIMESTAMP}.xml"
  run_ctest_label "SLOW" --output-junit "${slow_junit}" | tee "${slow_log}"
else
  echo "[reproduce] skipping SLOW tests (SKIP_SLOW=1)"
fi

quant_cli="$(find_binary quant_cli)"
generate_figures "${quant_cli}"
run_benchmarks
run_wrds_pipeline

if [[ "${RUN_MARKET_TESTS:-0}" == "1" ]]; then
  market_log="${LOG_DIR}/market_${TIMESTAMP}.log"
  market_junit="${LOG_DIR}/market_${TIMESTAMP}.xml"
  run_ctest_label "MARKET" --output-junit "${market_junit}" | tee "${market_log}"
else
  echo "[reproduce] skipping MARKET tests (RUN_MARKET_TESTS=0)"
fi

finalize_manifest
echo "[reproduce] artifacts available under ${ARTIFACT_DIR}"
