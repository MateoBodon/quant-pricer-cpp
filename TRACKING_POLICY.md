# Tracking policy

## Goals
- Clean working tree by default (no untracked junk).
- Maximum consistency across projects.
- Maximum reviewability (diffable, curated outputs).
- Optimal future ChatGPT/agent context (tickets, decisions, curated results, run manifests).

## Definitions
- Tracked = source-of-truth or curated output we want in repo history.
- Ignored = scratch, generated, local-only, large/churny, or environment-specific.

## Canonical output zones (DO NOT INVENT NEW ONES)

### Curated (tracked)
These are the only places where “results” should be committed.
- docs/tickets/              (work items, acceptance criteria, decisions)
- docs/agent_runs/           (small run logs: PROMPT/RESULTS/TESTS/META)
- docs/artifacts/            (curated metrics/plots/tables + manifest)

Rules:
- Keep content small + stable.
- Prefer .md/.json/.csv/.png; avoid binaries like .zip unless LFS + explicit reason.
- Every curated result set should include a run manifest:
  - commit hash
  - command(s) run
  - key inputs (config paths, dataset version identifiers)
  - timestamp (UTC)
  - environment notes if relevant

### Scratch (ignored)
These are allowed to be messy and are never committed.
- reports/_runs/             (timestamped run dumps)
- reports/_bundles/*.zip     (generated AI/context/review bundle deliverables)
- artifacts/_local/          (scratch artifacts)
- .cache/                    (local caches)
- tmp/                       (temporary)

Rules:
- If an agent/tool produces lots of files, direct it here.
- If something in scratch becomes important, promote it by copying a summary into docs/artifacts/.
- Keep bundle manifests/indexes inside the zip and durable state in canonical docs.

## Data policy
Default: do NOT commit raw or derived datasets.
- data/raw/                  ignored
- data/derived/              ignored
- data/samples/              tracked (small, redistributable samples only)
- data/schema/               tracked (schemas, README, manifests)

If you need large data:
- store externally and track a manifest + fetch script
- or use Git LFS only when absolutely necessary

## Local-only policy
- Anything named *_local.* is local-only and must be ignored.
- .env, .env.* are ignored; commit only .env.example (and optionally .env.local.example).

## Agent rules (Codex/ChatGPT MUST FOLLOW)
- Do not create new top-level directories.
- Any generated output MUST go under one of:
  - reports/_runs/
  - reports/_bundles/
  - artifacts/_local/
  - docs/agent_runs/  (small, structured logs only)
  - docs/artifacts/   (curated output only)
- Tickets go in docs/tickets/ and are tracked.

## Consistency rule
- Do not use .git/info/exclude for shared policy.
  Only use it for truly personal ignores that must not affect other clones.
