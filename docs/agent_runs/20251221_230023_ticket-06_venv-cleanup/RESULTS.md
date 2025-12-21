# Results

- Resolved stash conflicts by keeping both PROGRESS entries and restoring the sample-only `docs/artifacts/manifest.json` (local WRDS entries moved to an untracked local manifest).
- Saved the local manifest to `docs/artifacts/wrds_local/manifest_local.json` (ignored).
- Removed tracked `.venv/` from git history and added `docs/artifacts/wrds_local/` to `.gitignore`.
- Local files and directories (including `.venv` and WRDS local artifacts) remain on disk.

## Artifacts / Local-only
- `docs/artifacts/wrds_local/manifest_local.json` (untracked)

## Notes
- Sources consulted: none.
