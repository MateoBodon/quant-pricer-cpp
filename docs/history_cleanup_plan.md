# History Cleanup Plan (draft)

## Why
`git rev-list --objects --all` shows large historical blobs dominated by `docs/validation_pack.zip` plus `.venv` binaries. These inflate repo size and are already ignored by policy. Consider a one-time history rewrite to purge them.

## Candidates to remove
- `docs/validation_pack.zip`
- `docs/gpt_bundles/*.zip`
- `.venv/**` (historical venv binaries)

## Proposed approach (no execution yet)
1. Coordinate with the team; history rewrite requires force-push and everyone to re-clone or reset.
2. Create a backup clone.
3. Run `git filter-repo` in the backup clone:

```bash
git filter-repo \
  --path docs/validation_pack.zip \
  --path-glob docs/gpt_bundles/*.zip \
  --path-glob .venv/** \
  --invert-paths
```

4. Verify with `git count-objects -vH` and the top-blob report.
5. Force-push the rewritten history and notify all collaborators.

## Warnings
- This is destructive to history; only proceed after approvals.
- All contributors must rebase or re-clone after the rewrite.
