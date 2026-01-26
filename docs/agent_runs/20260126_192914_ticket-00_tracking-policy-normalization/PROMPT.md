# Prompt

Goal: Enforce TRACKING_POLICY.md conventions, ensure agent run logs are tracked, and stop zip bundles from polluting git state.

Steps:
- Baseline status and .git/info/exclude.
- Ensure scaffold dirs + README placeholders.
- Enforce .gitignore rules (ignore scratch; keep docs/agent_runs tracked; ignore gpt bundles + validation_pack).
- Move ignore rules from .git/info/exclude into .gitignore.
- Track untracked docs/agent_runs logs.
- Stop tracking docs/gpt_bundles/*.zip and docs/validation_pack.zip.
- Stage only normalization changes and commit.
- Run history audit (count-objects + top blobs); write cleanup plan if needed.
