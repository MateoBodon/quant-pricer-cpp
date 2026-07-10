# T-### - Title

## Status

planned | selected | active | blocked | executed | review-ready | fix-required | approved | archived

## Owner Flow

Pro planned -> Heavy dispatched -> Codex executes -> Heavy reviews -> Pro recenter only if needed.

## Goal

Describe the target outcome, not implementation micro-steps.

## Why This Matters

Explain project value, goal alignment, and why this ticket is worth doing now.

## Scope

In scope:

- ...

Out of scope:

- ...

## Context Files

- `AGENTS.md`
- `PROJECT.md`
- `docs/strategy/GOAL_CONTEXT.md`
- `docs/strategy/PLAN_OF_RECORD.md`
- `docs/strategy/CONTEXT_CARRYOVER.md`
- `project_state/RUNBOOK.md`
- `project_state/VALIDATION_MATRIX.md`
- Relevant source/tests/configs

## Acceptance Criteria

- ...

## Validation Level

L0 smoke / L1 targeted / L2 full fast suite / L3 integration-reproduction / L4 release-claim audit

Required or expected commands:

```bash
...
```

If a command cannot be run, state why and provide the next-best check.

## Review Artifacts Required

- Original work order.
- Changed file list.
- Diff or commit range.
- Run log.
- Exact command outputs.
- Validation summary JSON if available.
- Updated docs if relevant.
- Generated artifacts required for review.
- Compact review bundle with manifest and index.

## Stop-The-Line Conditions

- Unsupported external-facing claim.
- Failing required validation.
- Suspected data leakage or chronology violation.
- Raw restricted data exposure.
- Broad unrelated changes.
- Strategic ambiguity requiring Pro.
- Hidden generated prose/artifacts not represented in the bundle.

## Notes For Codex

Use autonomous codebase exploration. Solve the ticket end to end. Prefer robust, maintainable changes. Do not ask for clarification unless missing information would materially change implementation or create serious risk. Record what you did and how you validated it.
