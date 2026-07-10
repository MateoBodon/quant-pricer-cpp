# DECISIONS

Record non-obvious decisions. Keep it short.

Template:
- Date:
- Decision:
- Context:
- Options considered:
- Why:
- Consequences:

- Date: 2026-01-25
  Decision: Restore pre-bootstrap repo docs from backups while keeping PROJECT.md + tools/agentic scaffold.
  Context: The bootstrap script overwrote existing repo-specific instructions and logs.
  Options considered: Keep scaffold templates as-is; restore prior files and retain only required scaffold pieces.
  Why: Preserve existing repo guidance/history while satisfying the scaffold requirement.
  Consequences: Added PROJECT.md/tools/agentic, retained original AGENTS/PROGRESS/RUNBOOK/PLAN content.

- Date: 2026-01-26
  Decision: Enforce allowlisted columns plus restricted-token checks in the WRDS real-data exporter.
  Context: The exporter must fail closed if aggregated CSV schemas drift or raw WRDS fields leak in.
  Options considered: Accept any columns; blocklist-only; allowlist plus restricted tokens.
  Why: Favor license safety over silent acceptance of new/unreviewed fields.
  Consequences: Exporter will require updates if aggregate headers legitimately change.

- Date: 2026-01-26
  Decision: Use a run-specific dateset clone with `wrds_local_root=/srv/data/wrds/wrds` and install `pyarrow` in the venv for local parquet access.
  Context: `WRDS_LOCAL_ROOT=/srv/data/wrds` lacks `raw/optionm`, and initial runs fell back to sample mode with missing parquet engines.
  Options considered: Edit the canonical dateset; create symlinks under `/srv/data/wrds`; use a run-local dateset clone pointing at the nested parquet root.
  Why: Keeps repo configs unchanged and avoids modifying external paths while ensuring local-mode provenance.
  Consequences: The run log includes a local dateset clone under `docs/agent_runs/` and requires `pyarrow` installed in the venv.

- Date: 2026-01-26
  Decision: Document worker_default's `/srv/data/wrds` allowlist and require a dateset clone to point at `/srv/data/wrds/wrds`, while keeping manifest churn from local runs out of git.
  Context: The nested parquet root conflicted with host allowlists, and local runs can update `docs/artifacts/manifest.json` with gitignored paths.
  Options considered: Keep a single WRDS_LOCAL_ROOT path in docs; edit the canonical dateset; commit manifest updates from local runs.
  Why: Ensures both AX162-S and worker_default can run locally without altering tracked configs or committing local-only artifacts.
  Consequences: Operators must use a dateset clone on worker_default and explicitly revert manifest changes after local runs.

- Date: 2026-01-26
  Decision: Route local WRDS outputs and manifests to `artifacts/_local` instead of the legacy docs artifacts local path.
  Context: TRACKING_POLICY requires scratch outputs under `artifacts/_local` and keeps curated artifacts in `docs/artifacts`.
  Options considered: Keep using the legacy docs artifacts local path; rely on manual manifest cleanup; redirect defaults to scratch with a local manifest.
  Why: Aligns local WRDS workflows with the tracking policy and avoids mutating tracked manifests by default.
  Consequences: Local runs now write to `artifacts/_local/wrds_local` with `manifest_local.json`; docs and runbook guidance updated.

- Date: 2026-07-10
  Decision: Interpret risk-backtest `alpha` as VaR confidence and use `1-alpha` as the Bernoulli exception probability.
  Context: The public API documents values such as `alpha=0.95` as 95% VaR, but the Kupiec likelihood had assigned `alpha` to exceptions and `1-alpha` to non-exceptions. The Christoffersen likelihood also multiplied failure terms by total transitions from each state.
  Options considered: Preserve the implementation and rename the parameter; correct the likelihoods to match the documented API and standard tests.
  Why: The documented confidence convention is already used by the rest of the risk API and by callers.
  Consequences: On-target exception rates now produce high POF p-values, excess rates fail, clustering is tested independently, and empty/non-binary/non-finite inputs fail explicitly.

- Date: 2026-07-10
  Decision: Bind local OptionMetrics research to the explicit partitioned-vault snapshot and fail closed on provenance or market-input gaps.
  Context: The canonical loader expected monolithic parquet, silently downgraded local failures to sample data, and filled missing spot/rate/dividend values with constants; the authoritative shared vault is partitioned CSV.GZ with acquisition manifests.
  Options considered: Repack the restricted vault into repo-specific parquet; retain fallback constants and label them; adapt the canonical pipeline directly to the manifest-bound vault.
  Why: Direct adaptation preserves one restricted-data authority and makes a claimed real-data run mechanically distinguishable from a sample/proxy run.
  Consequences: Local loads require snapshot `20260707_045553_global_project_priority`, exact as-of SPX identity, exact spot/dividend rows, an interpolable exact-date zero curve, and ok source-manifest items. Every successful date pair writes an ignored source receipt; legacy parquet is not eligible for a new headline run.
