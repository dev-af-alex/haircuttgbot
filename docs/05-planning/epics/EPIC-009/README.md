# EPIC-009 — Security and operations hardening baseline

Status: IN_PROGRESS

## Goal

Close remaining MVP NFR gaps for abuse protection, secrets handling, retention policy, and operational SLO definitions on single-VM runtime.

## Scope

- Per-user abuse protection and command throttling baseline for Telegram-facing flows.
- Security policy finalization for secret handling and TLS ingress.
- Retention policy finalization for logs/audit and booking data.
- SLO/SLI definition aligned with alerts and operational runbooks.

## Out of scope

- Multi-node/high-availability architecture.
- Full WAF/bot-management platform integration.
- Major product-flow changes outside existing booking/schedule capabilities.

## Acceptance criteria

- Abuse-control baseline rejects burst traffic predictably and logs structured deny events.
- Security docs define secrets lifecycle and TLS termination policy for VM deployment.
- Reliability/privacy docs define SLO, error-budget expectations, and retention rules.
- Local docker-compose run and smoke path remain valid and reproducible.

## Dependencies

- EPIC-007 observability + backup/alerts baseline.
- EPIC-008 deployment baseline.

## Deliverables

- Application-level throttling/abuse-control baseline.
- Finalized NFR documentation for security/reliability/privacy/performance open items.
- Updated delivery docs and smoke checks for abuse-protection validation.

## Planned PR groups

- Group 01: abuse-control strategy + ADR + middleware baseline.
- Group 02: NFR policy finalization (SLO, retention, secrets/TLS) + doc sync.
- Group 03: smoke/acceptance hardening + closure checks.

## Notes

- Every PR group must keep local `docker compose` workflow operational.
- Merge method remains merge-commit per repository policy.

## Delivered (Group 01)

- Finalized abuse-control strategy and event contract in `docs/90-decisions/adr-0006-telegram-abuse-protection-strategy.md`.
- Added per-user sliding-window throttling middleware for `POST /internal/telegram/*` paths.
- Added structured deny event `abuse_throttle_deny` and abuse outcome metric `bot_api_abuse_outcomes_total`.
- Updated architecture/NFR/delivery docs to reflect throttling behavior and metric contract.
- Marked `T-001`, `T-002`, and `group-01` as `DONE`.
