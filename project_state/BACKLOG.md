# Backlog

Ranked, short.
1. Automate CURRENT_RESULTS sync when `docs/artifacts/metrics_summary.*` changes to avoid manual drift.
2. Restore missing run logs for 2025-12-26 entries or document why the logs are unavailable.
3. Add a CI workflow to run `ctest --test-dir build -L FAST --output-on-failure` on PRs.
4. Document the WRDS local cache configuration (paths, sample mode, guardrails) in `docs/`.
5. Add a small regression test for manifest canonicalization to prevent absolute paths in new artifacts.
6. Expand PDE order coverage with a fast grid-sweep sanity check.
7. Track runtime benchmarks over time with a baseline JSON under `docs/artifacts/`.
