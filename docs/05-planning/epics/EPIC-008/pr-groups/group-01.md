# EPIC-008 / PR Group 01

Status: TODO

## Objective

Define deployment baseline contract and decide release/rollback approach before implementing full VM runbook steps.

## Included tasks

- T-001 - Define single-VM deployment contract and release artifact shape

## Why this grouping

- Establishes deployment boundaries and decisions needed by all later implementation tasks.
- Keeps first PR small, documentation-first, and safely mergeable.
- Reduces risk of rework in deploy/rollback command authoring.

## Acceptance checks

- VM deployment contract is documented with explicit prerequisites and runtime assumptions.
- Secret/config strategy is documented with no secrets added to repository files.
- ADR stub exists for non-trivial deployment decision path.
- Local docker-compose runbook remains valid and unchanged in behavior.

## Merge readiness gates

- No runtime regressions in local smoke path.
- Docs are synchronized with `checklists/doc-sync.md` targets impacted by deployment planning.
- Merge method remains merge-commit.

## Task status

- T-001: TODO
