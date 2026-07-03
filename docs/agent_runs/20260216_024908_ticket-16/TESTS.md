# Tests

- [x] Command: `PATH="$PWD/.venv/bin:$PATH" cmake -S . -B build -DCMAKE_BUILD_TYPE=Release`
  - Result: pass.

- [x] Command: `PATH="$PWD/.venv/bin:$PATH" cmake --build build -j`
  - Result: pass.

- [x] Command: `PATH="$PWD/.venv/bin:$PATH" ctest --test-dir build -L FAST --output-on-failure`
  - Result: first attempt failed at `docs_sanity_fast` due placeholder bullets in `docs/NOW.md`; after replacing placeholders with concrete bullets, rerun passed (`100% tests passed, 0 tests failed out of 64`).

- [x] Command: `PATH="$PWD/.venv/bin:$PATH" WRDS_USE_SAMPLE=1 ./scripts/reproduce_wrds_local_metrics.sh --run-id wrds_local_ci_snippet --dateset wrds_pipeline_dates_panel.yaml`
  - Result: pass (sample export generated under `artifacts/_local/wrds_local/wrds_local_ci_snippet/`).

- [x] Command: `PATH="$PWD/.venv/bin:$PATH" python3 scripts/generate_wrds_resume_snippet.py --metrics-json artifacts/_local/wrds_local/wrds_local_ci_snippet/metrics_export_sample.json`
  - Result: pass (`resume_snippet_wrds_sample.md` generated).

- [x] Command: `PATH="$PWD/.venv/bin:$PATH" python3 scripts/generate_wrds_resume_snippet.py --metrics-json artifacts/_local/wrds_local/wrds_local_20260216_024926_ticket16/metrics_export_local.json`
  - Result: pass (`resume_snippet_wrds_local.md` generated).

- [x] Command: `python3 - <<'PY'`
```python
from pathlib import Path

md_path = Path('artifacts/_local/wrds_local/wrds_local_20260216_024926_ticket16/metrics_export_local.md')
text = md_path.read_text().lower()
checks = {
    'has_csv_filename': any(token in text for token in [
        'wrds_agg_pricing.csv',
        'wrds_agg_oos.csv',
        'wrds_agg_pnl.csv',
        'wrds_bs_heston_comparison.csv',
    ]),
    'has_raw_root': '/srv/data/wrds' in text,
    'has_per_date': 'per_date' in text,
}
print(checks)
if any(checks.values()):
    raise SystemExit(1)
```
  - Result: pass (`{'has_csv_filename': False, 'has_raw_root': False, 'has_per_date': False}`).

- [x] Command: `for f in metrics_export_local.md metrics_export_local.json manifest_local.json; do test -f "artifacts/_local/wrds_local/wrds_local_20260216_024926_ticket16/$f"; done`
  - Result: pass.
