# Commands

Working directory for all commands: `/Volumes/Storage/Projects/quant-pricer-cpp/repo`

1. Verify control/repo state and prior Project OS verification context.
2. Reconstruct the exact local-vault file set required by
   `wrds_pipeline_dates_panel.yaml`.
3. Launch the real-data run:

```bash
RUN_ID=wrds_local_20260711T113500Z_flagship_audit
LOG_DIR=/Volumes/Storage/Projects/quant-pricer-cpp/repo/artifacts/_local/wrds_local/$RUN_ID
mkdir -p "$LOG_DIR"
export WRDS_LOCAL_ROOT=/Volumes/Storage/Data/wrds
export QUANT_MACHINE_LABEL=codex-local
./scripts/reproduce_wrds_local_metrics.sh --dateset wrds_pipeline_dates_panel.yaml --run-id "$RUN_ID" 2>&1 | tee "$LOG_DIR/command.log"
```

4. Inspect generated:

```bash
sed -n '1,240p' artifacts/_local/wrds_local/wrds_local_20260711T113500Z_flagship_audit/metrics_export_local.md
python3 scripts/check_data_policy.py
python3 tests/test_docs_sanity_fast.py
git status --short
```

5. Audit per-date receipts and aggregate comparison CSVs.
6. Preserve a local milestone branch at the evidence commit:

```bash
git branch portfolio-os/wrds-local-flagship-20260711 50fdfdca2b655503d9aa1059d46f772c83dd6bfe
```

7. Attempt remote reconciliation/push dry runs (blocked by environment policy):

```bash
git fetch --dry-run origin
git push --dry-run origin recovery/quant-pre-v3-20260710
```

Full command output is preserved at:

- `artifacts/_local/wrds_local/wrds_local_20260711T113500Z_flagship_audit/command.log`

## Key Result Lines

The command log ends with:

```text
[wrds_pipeline] dateset=/Volumes/Storage/Projects/quant-pricer-cpp/repo/wrds_pipeline_dates_panel.yaml panel_id=wrds_panel_calm_stress_v1 entries=5
[wrds_pipeline] SPX 2020-03-16 source_today=local source_next=local
[wrds_pipeline] SPX 2020-03-17 source_today=local source_next=local
[wrds_pipeline] SPX 2022-06-13 source_today=local source_next=local
[wrds_pipeline] SPX 2022-06-14 source_today=local source_next=local
[wrds_pipeline] SPX 2024-06-14 source_today=local source_next=local
[wrds_export] wrote /Volumes/Storage/Projects/quant-pricer-cpp/repo/artifacts/_local/wrds_local/wrds_local_20260711T113500Z_flagship_audit/metrics_export_local.json
[wrds_export] wrote /Volumes/Storage/Projects/quant-pricer-cpp/repo/artifacts/_local/wrds_local/wrds_local_20260711T113500Z_flagship_audit/metrics_export_local.md
```
