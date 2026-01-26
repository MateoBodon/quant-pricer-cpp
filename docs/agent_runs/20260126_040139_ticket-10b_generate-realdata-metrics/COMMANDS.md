# Commands

- bash -lc 'python3 -m venv .venv && . .venv/bin/activate && python -m pip install -r requirements-dev.txt && cmake -S . -B build -DCMAKE_BUILD_TYPE=Release -DPython3_EXECUTABLE=$PWD/.venv/bin/python3 && cmake --build build -j && PATH=$PWD/.venv/bin:$PATH ctest --test-dir build -L FAST --output-on-failure && RUN_ID=wrds_local_$(date +%Y%m%d_%H%M%S) && WRDS_LOCAL_ROOT=/srv/data/wrds python3 -m wrds_pipeline.pipeline --fast --dateset wrds_pipeline_dates_panel.yaml --output-root docs/artifacts/wrds_local/$RUN_ID && WRDS_LOCAL_ROOT=/srv/data/wrds QUANT_MACHINE_LABEL=AX162-S python3 scripts/wrds_realdata_metrics_export.py --wrds-root docs/artifacts/wrds_local/$RUN_ID --out docs/artifacts/wrds_local/$RUN_ID/metrics_export_local.json --out-md docs/artifacts/wrds_local/$RUN_ID/metrics_export_local.md && python3 - <<"PY"\nimport json\nfrom pathlib import Path\np=Path("docs/artifacts/wrds_local")\nlatest=sorted([d for d in p.iterdir() if d.is_dir()])[-1]\nj=json.loads((latest/"metrics_export_local.json").read_text())\nassert j["provenance"]["data_mode"] in ("local","live")\nassert "metrics" in j\nprint("OK:", latest)\nPY'
- bash -lc '. .venv/bin/activate && RUN_ID=wrds_local_$(date +%Y%m%d_%H%M%S) && WRDS_LOCAL_ROOT=/srv/data/wrds/wrds python3 -m wrds_pipeline.pipeline --fast --dateset wrds_pipeline_dates_panel.yaml --output-root docs/artifacts/wrds_local/$RUN_ID && WRDS_LOCAL_ROOT=/srv/data/wrds/wrds QUANT_MACHINE_LABEL=AX162-S python3 scripts/wrds_realdata_metrics_export.py --wrds-root docs/artifacts/wrds_local/$RUN_ID --out docs/artifacts/wrds_local/$RUN_ID/metrics_export_local.json --out-md docs/artifacts/wrds_local/$RUN_ID/metrics_export_local.md && python3 - <<"PY"\nimport json\nfrom pathlib import Path\np=Path("docs/artifacts/wrds_local")\nlatest=sorted([d for d in p.iterdir() if d.is_dir()])[-1]\nj=json.loads((latest/"metrics_export_local.json").read_text())\nassert j["provenance"]["data_mode"] in ("local","live")\nassert "metrics" in j\nprint("OK:", latest)\nPY'
- bash -lc '. .venv/bin/activate && python -m pip install pyarrow'
- bash -lc '. .venv/bin/activate && RUN_ID=wrds_local_$(date +%Y%m%d_%H%M%S) && WRDS_LOCAL_ROOT=/srv/data/wrds python3 -m wrds_pipeline.pipeline --fast --dateset docs/agent_runs/20260126_040139_ticket-10b_generate-realdata-metrics/wrds_pipeline_dates_panel_local.yaml --output-root docs/artifacts/wrds_local/$RUN_ID && WRDS_LOCAL_ROOT=/srv/data/wrds QUANT_MACHINE_LABEL=AX162-S python3 scripts/wrds_realdata_metrics_export.py --wrds-root docs/artifacts/wrds_local/$RUN_ID --out docs/artifacts/wrds_local/$RUN_ID/metrics_export_local.json --out-md docs/artifacts/wrds_local/$RUN_ID/metrics_export_local.md && python3 - <<"PY"\nimport json\nfrom pathlib import Path\np=Path("docs/artifacts/wrds_local")\nlatest=sorted([d for d in p.iterdir() if d.is_dir()])[-1]\nj=json.loads((latest/"metrics_export_local.json").read_text())\nassert j["provenance"]["data_mode"] == "local"\nassert "metrics" in j\nprint("OK:", latest)\nPY'
- python3 - <<"PY"
import json
from pathlib import Path

run_dir = Path('docs/artifacts/wrds_local/wrds_local_20260126_040817')
export_path = run_dir / 'metrics_export_local.json'

payload = json.loads(export_path.read_text())
metrics = payload['metrics']
prov = payload['provenance']

pricing = metrics['pricing']
oos = metrics['oos']
comp = metrics['comparison']

trade_range = prov.get('trade_date_range', {})
trade_range_str = f"{trade_range.get('start')}–{trade_range.get('end')}" if trade_range else 'unknown'
panel_id = prov.get('panel_id', 'unknown')

lines = [
    "# Resume snippet (WRDS local metrics)",
    "",
    f"- WRDS SPX local panel `{panel_id}` ({trade_range_str}); 5 trade dates, 25 tenor buckets.",
    (
        "- Pricing fit: median IV RMSE {iv_rmse:.4g} vol pts (vega-weighted), "
        "median IV MAE {iv_mae:.4g} bps; median price RMSE {price_rmse:.4g} ticks."
    ).format(
        iv_rmse=pricing['median_iv_rmse_volpts_vega_wt'],
        iv_mae=pricing['median_iv_mae_bps'],
        price_rmse=pricing['median_price_rmse_ticks'],
    ),
    (
        "- OOS errors: weighted IV MAE {oos_iv_mae:.4g} bps; weighted price MAE {oos_price_mae:.4g} ticks."
    ).format(
        oos_iv_mae=oos['weighted_iv_mae_bps'],
        oos_price_mae=oos['weighted_price_mae_ticks'],
    ),
    (
        "- Heston vs BS: median ΔIV RMSE {delta_iv:.4g} vol pts, ΔOOS IV MAE {delta_oos:.4g} bps, "
        "Δprice RMSE {delta_price:.4g} ticks."
    ).format(
        delta_iv=comp['median_delta_iv_rmse_volpts'],
        delta_oos=comp['median_delta_oos_iv_mae_bps'],
        delta_price=comp['median_delta_price_rmse_ticks'],
    ),
]

(run_dir / 'resume_snippet.md').write_text("\n".join(lines) + "\n")
print(run_dir / 'resume_snippet.md')
PY
- python3 tools/agentic/gpt_bundle.py --zip --ticket ticket-10b_generate-realdata-metrics-and-resume-snippet
- bash -lc 'python3 -m venv .venv && . .venv/bin/activate && python -m pip install -r requirements-dev.txt pyarrow && cmake -S . -B build -DCMAKE_BUILD_TYPE=Release -DPython3_EXECUTABLE=$PWD/.venv/bin/python3 && cmake --build build -j && PATH=$PWD/.venv/bin:$PATH ctest --test-dir build -L FAST --output-on-failure && RUN_ID=wrds_local_$(date +%Y%m%d_%H%M%S) && WRDS_LOCAL_ROOT=/srv/data/wrds/wrds python3 -m wrds_pipeline.pipeline --fast --dateset wrds_pipeline_dates_panel.yaml --output-root docs/artifacts/wrds_local/$RUN_ID && WRDS_LOCAL_ROOT=/srv/data/wrds/wrds QUANT_MACHINE_LABEL=AX162-S python3 scripts/wrds_realdata_metrics_export.py --wrds-root docs/artifacts/wrds_local/$RUN_ID --out docs/artifacts/wrds_local/$RUN_ID/metrics_export_local.json --out-md docs/artifacts/wrds_local/$RUN_ID/metrics_export_local.md && test -s docs/artifacts/wrds_local/$RUN_ID/metrics_export_local.md && git checkout -- docs/artifacts/manifest.json && git diff --exit-code docs/artifacts/manifest.json && git diff --exit-code -- docs/artifacts/wrds'
