# Tests

- [x] Parse `wrds_pipeline_dates_panel_resume_v2.yaml` and count entries.
  ```bash
  python3 - <<'PY'
  import yaml
  from pathlib import Path

  panel_path = Path("wrds_pipeline_dates_panel_resume_v2.yaml")
  data = yaml.safe_load(panel_path.read_text(encoding="utf-8"))
  entries = data.get("dates") or data.get("entries") or []
  print(f"panel_id={data.get('panel_id')}")
  print(f"entries={len(entries)}")
  PY
  ```
  - Result: `panel_id=wrds_panel_resume_v2`, `entries=14`.

- [x] `WRDS_USE_SAMPLE=1 ./scripts/reproduce_wrds_local_metrics.sh --dateset wrds_pipeline_dates_panel.yaml --run-id wrds_local_ci_snippet`
  - Result: failed outside venv (`ModuleNotFoundError: No module named 'matplotlib'`).

- [x] `source .venv/bin/activate && WRDS_USE_SAMPLE=1 ./scripts/reproduce_wrds_local_metrics.sh --dateset wrds_pipeline_dates_panel.yaml --run-id wrds_local_ci_snippet`
  - Result: pass; wrote `artifacts/_local/wrds_local/wrds_local_ci_snippet/metrics_export_sample.{json,md}`.

- [x] `source .venv/bin/activate && python3 scripts/generate_wrds_resume_snippet.py --metrics-json artifacts/_local/wrds_local/wrds_local_ci_snippet/metrics_export_sample.json`
  - Result: pass; wrote `artifacts/_local/wrds_local/wrds_local_ci_snippet/resume_snippet_wrds_sample.md`.

- [x] `source .venv/bin/activate && WRDS_LOCAL_ROOT=/srv/data/wrds/wrds QUANT_MACHINE_LABEL="$(hostname)" MPLCONFIGDIR=/tmp/matplotlib PYTHONUNBUFFERED=1 ./scripts/reproduce_wrds_local_metrics.sh --dateset wrds_pipeline_dates_panel_resume_v2.yaml --run-id wrds_local_resume_v2`
  - Result: pass; wrote local parquet outputs including `metrics_export_local.{json,md}` and `manifest_local.json`.

- [x] `source .venv/bin/activate && python3 scripts/generate_wrds_resume_snippet.py --metrics-json artifacts/_local/wrds_local/wrds_local_resume_v2/metrics_export_local.json`
  - Result: pass; wrote `artifacts/_local/wrds_local/wrds_local_resume_v2/resume_snippet_wrds_local.md`.

- [x] Compute `(BS-Heston)/BS*100` from `metrics_export_local.json`.
  ```bash
  python3 - <<'PY'
  import json
  from pathlib import Path

  metrics_path = Path("artifacts/_local/wrds_local/wrds_local_resume_v2/metrics_export_local.json")
  data = json.loads(metrics_path.read_text(encoding="utf-8"))
  comparison = data["metrics"]["comparison"]
  bs = float(comparison["median_bs_iv_rmse_volpts"])
  heston = float(comparison["median_heston_iv_rmse_volpts"])
  improvement_pct = (bs - heston) / bs * 100.0
  print(f"heston_vs_bs_improvement_pct={improvement_pct}")
  PY
  ```
  - Result: pass; `heston_vs_bs_improvement_pct=66.51831115037523`.

- [x] `rg -n '/srv/data/wrds|\.parquet|\.csv' artifacts/_local/wrds_local/wrds_local_resume_v2/resume_snippet_wrds_local.md`
  - Result: pass; no banned-token matches.

- [x] `git status --porcelain`
  - Result: pass; tracked changes limited to dateset/run-log/`PROGRESS.md`; no `artifacts/_local/**` files staged/tracked.
