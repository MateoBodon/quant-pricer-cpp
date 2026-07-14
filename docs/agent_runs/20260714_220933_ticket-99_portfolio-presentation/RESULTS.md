# Results

- Rebuilt the README around the supported product surface, feature map, C++ and Python first-price paths, architecture, frozen numerical evidence, deterministic design, validation pack, and limitations.
- Added `docs/evidence/heston_grid_candidate_2026-07-14.md` to isolate the verified candidate-major calibration grid and compact-input 14.2x measurement from the public v0.3.2 release.
- Explicitly states that no PyPI distribution is currently available and that release assets are validation artifacts rather than wheels.
- No numerical implementation, scenario grid, tolerance, canonical artifact, or package version was changed.
- The baseline FAST suite has an unrelated repository-documentation failure: `gpt_bundle_empty_diff_fast` exits early because `docs/PLAN_OF_RECORD.md` and `docs/DOCS_AND_LOGGING_SYSTEM.md` are absent from the current default branch. The portfolio diff does not change that script or those files.
- Assumption: a verified candidate receipt may be summarized as next-release evidence only when commit, wheel hash, verification id, scope, and non-claims are stated together.
