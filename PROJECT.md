# PROJECT.md

## Identity

- Name: `quant-pricer-cpp`
- Type: C++20 quantitative finance library with Python bindings, validation scripts, benchmarks, and reproducible research artifacts.
- One-liner: A modern option-pricing toolkit that cross-checks analytic, Monte Carlo/QMC, PDE, and external-reference methods while keeping result claims tied to reproducible artifacts.
- Primary languages: C++20 and Python.
- Primary audience: quant/research engineering reviewers, open-source users of the C++/Python library, future Pro/Heavy/Codex sessions, and release/reproducibility reviewers.

## What This Repo Is

This repo implements and validates option-pricing engines:

- Black-Scholes analytics and Greeks.
- Monte Carlo GBM engines, variance reduction, deterministic RNG, QMC, and Brownian bridge.
- PDE solvers, barrier pricing, American options, digitals, Asians, lookbacks, Heston, risk, and multi-asset pieces.
- A CLI, optional Python bindings, benchmark harnesses, WRDS/OptionMetrics sample/live pipelines, and artifact-generation scripts.

The project is both a software library and a numerical/research evidence package. The public-facing results should always be read through the claim/evidence boundary in `project_state/CLAIMS_AND_EVIDENCE.md`.

## What This Repo Is Not

- Not a trading system.
- Not a live alpha/performance track record.
- Not a place to commit raw WRDS/OptionMetrics data, credentials, or unrestricted market-data extracts.
- Not a claim that sample WRDS artifacts prove live-market superiority.
- Not a process-document archive where every old planning note is current truth.

## Success Definition

A successful version of this repo is:

- buildable from a clean checkout;
- validated by a fast deterministic test suite;
- able to regenerate a curated sample-mode validation/artifact pack;
- honest about which claims are synthetic/reference-backed, sample-backed, or live-data-gated;
- easy for a new Pro/Heavy/Codex session to understand from canonical docs and bundles.

## Current State

What works:

- CMake Release build and FAST CTest suite are the canonical local validation path.
- Curated sample artifacts and metrics live under `docs/artifacts/`.
- The latest committed metrics snapshot reports ok status for tri-engine agreement, QMC vs PRNG, PDE order, QuantLib parity, benchmarks, and WRDS sample harness.
- Existing `project_state/` and `docs/agent_runs/` history provides substantial prior context.

What is incomplete or requires care:

- Pro has not yet produced the first AI Project OS v2 strategy package.
- Several pre-v2 docs contain stale status and are preserved for history rather than current truth.
- Live WRDS/market validation is credential/local-data gated.
- Heston QE bias remains a known numerical/research risk.

## Layout

- `include/quant/` - public C++ headers.
- `src/` - C++ implementation and CLI.
- `tests/` - C++ and Python FAST/MARKET tests.
- `python/` - pybind11 binding and examples.
- `wrds_pipeline/` - OptionMetrics/WRDS sample/live pipeline.
- `scripts/` - artifact, validation, report, bundle, and data-policy scripts.
- `docs/artifacts/` - curated validation outputs and manifest.
- `docs/strategy/` - AI Project OS v2 strategy/current-planning docs.
- `docs/tickets/` - ticket specs and templates.
- `docs/_archive/pre_ai_os_v2/` - indexed copies/pointers for old process docs.
- `project_state/` - factual state, validation, and claim/evidence docs.
- `reports/_runs/` - generated run logs for local execution.
- `reports/_bundles/` - generated review/state bundles.

## Canonical Context

Start here for future work:

1. `AGENTS.md`
2. `docs/strategy/CONTEXT_CARRYOVER.md`
3. `docs/strategy/PLAN_OF_RECORD.md`
4. `project_state/STATE_INDEX.md`
5. `project_state/RUNBOOK.md`
6. `project_state/VALIDATION_MATRIX.md`
7. `project_state/CLAIMS_AND_EVIDENCE.md`

Historical pre-v2 material remains accessible through `docs/_archive/pre_ai_os_v2/20260703/ARCHIVE_INDEX.md`.
