# Receipt Audit

Each per-date directory contains `source_receipt.json` with schema
`quant-pricer-wrds-vault-receipt/v1` and two surface receipts: one for the
trade date and one for the next trade date used by OOS/PnL.

## Trade-Date Pair Coverage

| trade_date | next_trade_date | receipt file |
| --- | --- | --- |
| 2020-03-16 | 2020-03-17 | `per_date/2020-03-16/source_receipt.json` |
| 2020-03-17 | 2020-03-18 | `per_date/2020-03-17/source_receipt.json` |
| 2022-06-13 | 2022-06-14 | `per_date/2022-06-13/source_receipt.json` |
| 2022-06-14 | 2022-06-15 | `per_date/2022-06-14/source_receipt.json` |
| 2024-06-14 | 2024-06-17 | `per_date/2024-06-14/source_receipt.json` |

## Receipt Checks

Verified from the generated receipts:

- snapshot always equals `20260707_045553_global_project_priority`
- resolved ticker is SPX only
- every surface receipt contains five source files:
  `idxdvd`, `opprcdYYYY`, `secnmd`, `secprdYYYY`, `zerocd`
- every file entry includes bytes, SHA256, manifest path, manifest SHA256,
  item rows, and item status
- every manifest-bound item used by the run has `item_status=ok`

Static-table manifests:

- `_manifests/20260707T141203Z_resume_90m_fast_csvgz/manifest.json`
  - `secnmd`
  - `zerocd`
  - `idxdvd`
  - overall manifest status: `operator_paused_at_boundary`
  - accepted because the adapter explicitly allowlists the used items when their
    individual manifest item status is `ok`

Dynamic day/month manifests:

- `_manifests/20260708T014000Z_worker64_optionm_opprcd2020_day_csvgz/manifest.json`
- `_manifests/20260708T013900Z_worker62_optionm_opprcd2022_day_csvgz/manifest.json`
- `_manifests/20260708T013900Z_worker60_optionm_opprcd2024_day_csvgz/manifest.json`
- `_manifests/20260708T063600Z_worker415_optionm_secprd2020_month_csvgz/manifest.json`
- `_manifests/20260708T063600Z_worker413_optionm_secprd2022_month_csvgz/manifest.json`
- `_manifests/20260708T063600Z_worker411_optionm_secprd2024_month_csvgz/manifest.json`

## Aggregate Scope Summary

- unique surface dates: `8`
- partition references: `40`
- unique compressed files: `14`
- compressed bytes: `449,572,051`

These counts match the delegated frozen-scope description. The repo does not
expose a canonical serializer for the external aggregate fingerprint prefix
`bc54c8fc...`, so this audit treats file-count, byte-count, SHA-bound manifest
links, and receipt materialization as the authoritative local proof.
