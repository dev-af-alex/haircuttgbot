# ADR-0001: Select Python/FastAPI/aiogram stack for Telegram barbershop bot

Date: 2026-02-08
Status: Accepted
Deciders: Product/Engineering

## Context

We need to implement a Telegram bot for a barbershop with two roles (`Client`, `Master`), multi-master schedule management, booking and cancellation flows, manual bookings by masters, day-off and lunch-break constraints, and notification delivery. Deployment constraint is local docker-compose and later single VM deployment. We need low operational complexity and quick iteration speed.

## Decision

Adopt the following baseline stack:

- Python 3.12 backend with FastAPI + aiogram 3 in one service.
- PostgreSQL 16 as primary relational datastore for bookings/schedules/users/roles.
- Redis 7 for lightweight state and rate-limiting support.
- Docker Compose for local/dev runtime and VM runtime packaging.
- GitHub Actions CI with Bandit (SAST), pip-audit (dependency scan), and Gitleaks (secrets scan).

## Alternatives considered

- Node.js + Telegraf + NestJS + PostgreSQL: viable, but team bootstrap/docs currently do not indicate JS preference; Python is faster for bot-first MVP here.
- Python + python-telegram-bot without FastAPI: simpler initially, but weaker foundation for clean webhook/API/health endpoint structure.
- Go + Telegram libs + PostgreSQL: strong performance, but higher implementation overhead for rapid MVP delivery and less flexible ecosystem for quick bot iterations.

## Consequences

Positive:

- Fast MVP delivery for Telegram-centric flows.
- Simple single-VM operational model with compose.
- Clear path to enforce security checks in CI.

Negative:

- Python runtime may require careful concurrency tuning under peak load.
- Redis adds one extra service to operate.

Follow-up actions:

- Define exact DB schema and slot-conflict guarantees.
- Finalize webhook ingress/TLS approach for production VM.
- Define CI thresholds and ignorelist policy for security scanners.
