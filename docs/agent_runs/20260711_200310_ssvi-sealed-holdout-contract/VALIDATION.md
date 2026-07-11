# Validation

- Parent panel: precommitted `wrds_panel_resume_v2`, SHA-256
  `51c0cb040a8f45d12bb7db5c1432b6371ff6d08402def442aee1709643af0a3c`.
- Derived sealed panel: exact 12/12 qanchor entries and only the two already-used
  stress entries excluded.
- Contract and panel hash guards: pass.
- Frozen implementation content-hash guards: pass for SSVI, independent
  reference, benchmark reducers, repaired Heston, and tenor-flat BS.
- Metadata-only vault preflight: pass for 24 unique surface dates, 39 compressed
  sources, 13 acquisition manifests, and 1,379,526,126 compressed bytes.
- Source mix: 24 quote-day files, 12 security-price month files, and one each
  dividend, security-name, and zero-curve table.
- Canonical inventory digest:
  `ca7fff944cc94c988e5c0b4d34cf7d99c2c46d9a8043c80fde297a464e818ca7`.
- Local aggregate inventory receipt SHA-256:
  `115281f3c4796a33c719f905e2fd479f8f3921875b07121c54bf1fba34d5f591`.
- Guard test: exact 10/12 dual-comparator pass, 9/12 fail, numerical-gate fail,
  publication readback fail, inventory mutation fail, exclusive one-use marker,
  and no-row-parser guard all pass.
- Outcome boundary: no compressed source was decompressed, no option row or
  aggregate surface outcome was opened, and no SSVI/Heston/BS metric was
  computed in this run.
- Execution remains stopped until authoritative exact-tree publication readback
  and release of the portfolio memory-heavy empirical slot.
