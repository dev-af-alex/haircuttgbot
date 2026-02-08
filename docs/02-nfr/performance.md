# Performance NFR

## 1) Expected scale (assumptions)

- MAU: TODO (expected unique monthly clients + masters).
- DAU: TODO.
- Peak concurrent: TODO (especially evening/weekend booking peaks).
- Peak RPS: TODO (Telegram webhook/event bursts).
- Data growth/day: TODO (new bookings, schedule updates, audit entries).

## 2) Latency targets (p50/p95)

- Critical: TODO (bot command to response for availability/booking actions).
- Non-critical: TODO (reporting, non-blocking notifications).

## 3) Constraints

- External API limits: Telegram Bot API limits and retry behavior TODO.
- Heavy operations: availability recalculation across multiple masters and date ranges TODO.
