# State Index

## Repo Identity

`quant-pricer-cpp` is a C++20 option-pricing library with Python bindings, validation scripts, benchmark/reporting tools, and curated reproducibility artifacts.

## Major Areas

| Path | Purpose | Current status |
|---|---|---|
| `include/quant/` | Public C++ API headers | Active |
| `src/` | Pricing implementations and CLI | Active |
| `tests/` | C++ and Python FAST/MARKET tests | Active |
| `python/` | pybind11 module and Python examples | Active |
| `wrds_pipeline/` | WRDS/OptionMetrics sample/live pipeline | Active, live path gated |
| `scripts/` | Artifact, benchmark, report, policy, bundle helpers | Active |
| `docs/artifacts/` | Curated validation outputs | Current curated evidence root |
| `artifacts/_local/` | Local/scratch outputs | Ignored, not current truth |
| `docs/agent_runs/` | Pre-v2 historical run logs | Preserved history |
| `docs/_archive/pre_ai_os_v2/20260703/` | Pre-v2 archive index/copies | Historical |
| `docs/strategy/` | AI Project OS v2 strategy docs | Current canonical planning |
| `reports/_runs/` | Generated v2 run logs | Generated/local evidence |
| `reports/_bundles/` | Generated v2 bundles | Generated review/state artifacts |

## Current Metrics Snapshot

- Source: `docs/artifacts/metrics_summary.md`.
- Generated at: 2026-01-25T21:13:43.226947+00:00.
- Reported ok blocks: tri-engine agreement, QMC vs PRNG, PDE order, QuantLib parity, benchmarks, WRDS sample harness.

## Historical State

The old `project_state/*.md` documents remain in place. Many were generated in December 2025 or January 2026 and may still be useful, but this file and the new v2 docs are the canonical starting point for future sessions.

## Missing Or Awaiting Decision

- First Pro strategy package.
- Fresh decision on whether to refresh sample artifacts.
- Claim/evidence audit before any external/release push.
- Cleanup of stale pre-v2 open questions after Pro sets direction.
