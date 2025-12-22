sounds good, now finish this chelist, make sure on main and push to origin, .agent should be on gitignore too. Stop-the-line checks

 Search diff for secrets: rg -n "WRDS_PASSWORD|WRDS_USERNAME|password|token|secret" -S .

 Confirm no raw WRDS/OptionMetrics-like quote surfaces were committed (look for strike,.*market_iv / secid / best_bid etc).

Reproducibility

 REPRO_FAST=1 WRDS_USE_SAMPLE=1 ./scripts/reproduce_all.sh produces snapshot with WRDS labeled “sample bundle” and no absolute paths.

 ctest --test-dir build -L FAST --output-on-failure passes.

 WRDS_USE_SAMPLE=1 python -m wrds_pipeline.pipeline --fast passes.

Protocol drift

 Local WRDS mode activates only via explicit env var/config (no /Volumes/... auto-detect).

 project_state/CONFIG_REFERENCE.md documents any new env vars.

Audit trail

 Run log folder name matches convention and includes full prompt + commands + tests + meta.

 Commit exists on a feature branch with Tests: lines in commit body.

 New bundle created with make gpt-bundle ... and path recorded in RESULTS.md.
