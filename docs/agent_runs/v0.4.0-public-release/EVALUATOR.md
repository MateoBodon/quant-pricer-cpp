# v0.4.0 public-release evaluator

Goal: publish a truthful, polished quant-pricer-cpp v0.4.0 GitHub release that
makes the verified portfolio-risk and exact-stress APIs the public project's
strongest story without weakening v0.3.7 packaging or prior numerical evidence.

The release is complete only when all of the following are provider-verified:

1. The reviewed integration branch is based on GitHub's current public main and
   contains only the reconciled v0.4.0 implementation, evidence, presentation,
   and release changes.
2. Native, Python, installed-wheel, sdist, data-policy, sanitizer, and relevant
   regression checks pass; any inherited SSVI locked-hash failures are unchanged
   and do not appear in public CI.
3. Public main, tag `v0.4.0`, and the GitHub release identify one exact commit.
4. CI, Docs Pages, Wheels, and release workflows succeed for that commit/tag.
5. Release assets contain the supported cross-platform wheel matrix, one sdist,
   deterministic release manifest, artifact manifest, and validation payload;
   provider digests and the manifest agree.
6. Live GitHub README, release page, and Pages are inspected at desktop and
   narrow widths with no broken image, clipped content, page-level horizontal
   overflow, stale lead copy, or misleading claim.
7. The canonical dirty checkout's non-ledger diff and untracked-byte digests
   match the pre-release preservation snapshot.

Final provider URLs, commit/tag, run conclusions, asset inventory/digests,
visual-QA result, and preservation digests are recorded in the Project OS goal
receipt before the goal is finished.
