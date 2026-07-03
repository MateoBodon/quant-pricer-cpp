#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
DATESET="wrds_pipeline_dates_panel.yaml"
RUN_ID="wrds_local_$(date -u +%Y%m%d_%H%M%S)"

usage() {
  echo "Usage: $0 [--dateset <path>] [--run-id <id>]" >&2
}

resolve_path() {
  python3 -c 'import pathlib,sys; root=pathlib.Path(sys.argv[2]); path=pathlib.Path(sys.argv[1]).expanduser(); path = path if path.is_absolute() else root / path; print(path.resolve())' "$1" "$ROOT"
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --dateset)
      if [[ $# -lt 2 ]]; then
        echo "error: --dateset requires a value" >&2
        usage
        exit 1
      fi
      DATESET="$2"
      shift 2
      ;;
    --run-id)
      if [[ $# -lt 2 ]]; then
        echo "error: --run-id requires a value" >&2
        usage
        exit 1
      fi
      RUN_ID="$2"
      shift 2
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      echo "error: unknown argument $1" >&2
      usage
      exit 1
      ;;
  esac
done

OUT_ROOT="${ROOT}/artifacts/_local/wrds_local/${RUN_ID}"
OUT_ROOT_ABS="$(resolve_path "${OUT_ROOT}")"

if [[ -n "${QUANT_MANIFEST_PATH:-}" ]]; then
  MANIFEST_ABS="$(resolve_path "${QUANT_MANIFEST_PATH}")"
  case "${MANIFEST_ABS}" in
    "${OUT_ROOT_ABS}"/*) ;;
    *)
      echo "error: QUANT_MANIFEST_PATH must live under ${OUT_ROOT_ABS}" >&2
      exit 1
      ;;
  esac
fi

export QUANT_MANIFEST_PATH="${OUT_ROOT_ABS}/manifest_local.json"

mkdir -p "${OUT_ROOT_ABS}"

METRICS_JSON=""
METRICS_MD=""
if [[ "${WRDS_USE_SAMPLE:-0}" == "1" ]]; then
  export WRDS_USE_SAMPLE=1
  METRICS_JSON="${OUT_ROOT_ABS}/metrics_export_sample.json"
  METRICS_MD="${OUT_ROOT_ABS}/metrics_export_sample.md"
  (cd "${ROOT}" && python3 -m wrds_pipeline.pipeline --fast --dateset "${DATESET}" --output-root "${OUT_ROOT_ABS}")
  (cd "${ROOT}" && python3 scripts/wrds_realdata_metrics_export.py --wrds-root "${OUT_ROOT_ABS}" --use-sample --out "${METRICS_JSON}" --out-md "${METRICS_MD}")
else
  if [[ -z "${WRDS_LOCAL_ROOT:-}" ]]; then
    echo "error: WRDS_LOCAL_ROOT must be set for local parquet mode" >&2
    exit 1
  fi
  METRICS_JSON="${OUT_ROOT_ABS}/metrics_export_local.json"
  METRICS_MD="${OUT_ROOT_ABS}/metrics_export_local.md"
  (cd "${ROOT}" && WRDS_LOCAL_ROOT="${WRDS_LOCAL_ROOT}" python3 -m wrds_pipeline.pipeline --fast --dateset "${DATESET}" --output-root "${OUT_ROOT_ABS}")
  (cd "${ROOT}" && WRDS_LOCAL_ROOT="${WRDS_LOCAL_ROOT}" python3 scripts/wrds_realdata_metrics_export.py --wrds-root "${OUT_ROOT_ABS}" --out "${METRICS_JSON}" --out-md "${METRICS_MD}")
fi

echo "${METRICS_MD}"
