# EPIC-011 / PR Group 01

Status: DONE

## Objective

Land a mergeable runtime baseline for real Telegram updates: decide ingress mode and add aiogram lifecycle bootstrap without breaking existing compose smoke path.

## Included tasks

- T-001 — Decide Telegram updates ingress mode and runtime contract
- T-002 — Implement aiogram runtime bootstrap in service lifecycle

## Why this grouping

- Locks the most important architecture decision (`polling` vs `webhook`) before handler implementation.
- Delivers immediate runtime capability while keeping scope small and mergeable.
- Preserves existing internal endpoint contracts used by current smoke and tests.

## Acceptance checks

- ADR exists for updates ingress mode with alternatives and consequences.
- aiogram runtime lifecycle starts/stops deterministically with selected mode.
- `docker compose up -d --build` remains healthy; existing smoke path remains runnable.
- Missing Telegram token/config yields explicit safe behavior (no crash loop).

## Merge readiness gates

- Local compose run remains healthy and reproducible.
- Security gates (Bandit, pip-audit, Gitleaks) remain green.
- Documentation is synchronized for new runtime/env behavior.

## Task status

- T-001: DONE
- T-002: DONE
