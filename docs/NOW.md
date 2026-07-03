# NOW

One page that answers:
- what are we doing this week?
- what is blocked?
- what is next?

## Focus
- Land ticket-16 WRDS resume-snippet workflow (generator + FAST guard + runbook update).
- Keep local parquet exports under `artifacts/_local/wrds_local/` and track only audit-safe run evidence.

## Blockers
- Local parquet validation requires licensed WRDS access (`WRDS_LOCAL_ROOT`) and cannot be exercised in CI.

## Next
- Re-run `ctest --test-dir build -L FAST --output-on-failure` after ticket-16 closeout.
- Use `scripts/generate_wrds_resume_snippet.py` after each WRDS export to refresh resume bullets.
