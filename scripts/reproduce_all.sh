#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
BUILD_DIR="${BUILD_DIR:-${ROOT}/build}"
BUILD_TYPE="${BUILD_TYPE:-Release}"
ARTIFACT_DIR="${ARTIFACT_DIR:-${ROOT}/docs/artifacts}"
LOG_DIR="${LOG_DIR:-${ARTIFACT_DIR}/logs}"
TIMESTAMP="$(date -u +%Y%m%dT%H%M%SZ)"

mkdir -p "${ARTIFACT_DIR}" "${LOG_DIR}"

echo "[reproduce] configuring ${BUILD_TYPE} build in ${BUILD_DIR}"
cmake -S "${ROOT}" -B "${BUILD_DIR}" -DCMAKE_BUILD_TYPE="${BUILD_TYPE}"
cmake --build "${BUILD_DIR}" --parallel

echo "[reproduce] running FAST tests (label=FAST)"
CTEST_OUTPUT_ON_FAILURE=1 ctest --test-dir "${BUILD_DIR}" -L FAST --output-on-failure -VV

if [[ "${SKIP_SLOW:-0}" != "1" ]]; then
  slow_log="${LOG_DIR}/slow_${TIMESTAMP}.log"
  slow_junit="${LOG_DIR}/slow_${TIMESTAMP}.xml"
  echo "[reproduce] running SLOW tests (label=SLOW) -> ${slow_log}"
  CTEST_OUTPUT_ON_FAILURE=1 ctest --test-dir "${BUILD_DIR}" -L SLOW --output-on-failure -VV --output-junit "${slow_junit}" | tee "${slow_log}"
else
  echo "[reproduce] skipping SLOW tests (SKIP_SLOW=1)"
fi

find_quant_cli() {
  local candidates=(
    "${BUILD_DIR}/quant_cli"
    "${BUILD_DIR}/${BUILD_TYPE}/quant_cli"
    "${BUILD_DIR}/quant_cli.exe"
    "${BUILD_DIR}/${BUILD_TYPE}/quant_cli.exe"
  )
  for candidate in "${candidates[@]}"; do
    if [[ -x "${candidate}" ]]; then
      echo "${candidate}"
      return 0
    fi
  done
  echo "error: quant_cli not found in ${BUILD_DIR}" >&2
  exit 1
}

QUANT_CLI="$(find_quant_cli)"
FAST_FLAGS=()
if [[ "${REPRO_FAST:-0}" == "1" ]]; then
  FAST_FLAGS=(--fast)
fi

run_py() {
  local script="${1}"
  shift
  echo "[reproduce] python $(basename "${script}") $*"
  python3 "${script}" "$@"
}

run_py "${ROOT}/scripts/qmc_vs_prng.py" "${FAST_FLAGS[@]}" --output "${ARTIFACT_DIR}/qmc_vs_prng.png" --csv "${ARTIFACT_DIR}/qmc_vs_prng.csv"
run_py "${ROOT}/scripts/pde_convergence.py" "${FAST_FLAGS[@]}" --skip-build --output "${ARTIFACT_DIR}/pde_convergence.png" --csv "${ARTIFACT_DIR}/pde_convergence.csv"
run_py "${ROOT}/scripts/mc_greeks_ci.py" "${FAST_FLAGS[@]}" --quant-cli "${QUANT_CLI}" --output "${ARTIFACT_DIR}/mc_greeks_ci.png" --csv "${ARTIFACT_DIR}/mc_greeks_ci.csv"
run_py "${ROOT}/scripts/heston_qe_vs_analytic.py" "${FAST_FLAGS[@]}" --quant-cli "${QUANT_CLI}" --output "${ARTIFACT_DIR}/heston_qe_vs_analytic.png" --csv "${ARTIFACT_DIR}/heston_qe_vs_analytic.csv"

if [[ "${RUN_WRDS_PIPELINE:-0}" == "1" ]]; then
  extra_flags=()
  if [[ "${WRDS_ENABLED:-0}" != "1" ]]; then
    extra_flags+=(--use-sample)
  fi
  echo "[reproduce] running WRDS pipeline ${extra_flags[*]}"
  python3 "${ROOT}/wrds_pipeline/pipeline.py" "${extra_flags[@]}"
else
  echo "[reproduce] skipping WRDS pipeline (set RUN_WRDS_PIPELINE=1 to enable with sample or credentials)."
fi

echo "[reproduce] artifacts available under ${ARTIFACT_DIR}"
