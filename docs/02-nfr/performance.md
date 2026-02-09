# Performance NFR

## 1) Expected scale (assumptions)

- MAU: ~800 clients + up to 20 masters.
- DAU: 80-150 users/day.
- Peak concurrent: up to 30 simultaneous bot interactions during evening windows.
- Peak RPS:
  - steady: 2-5 RPS
  - short bursts: up to 15 RPS for Telegram webhook events
- Data growth/day:
  - bookings + schedule updates: 200-500 rows/day
  - audit/security events: 1k-5k rows/day depending on activity and throttling denies

## 2) Latency targets (p50/p95)

- Critical (availability/booking/schedule write paths):
  - p50 <= 300 ms
  - p95 <= 1200 ms
- Non-critical (metrics/log-oriented endpoints and non-blocking flows):
  - p50 <= 500 ms
  - p95 <= 2000 ms

## 3) Constraints

- External API limits:
  - Telegram API/network can degrade independently from app health; webhook retries and backoff must tolerate temporary failures.
  - Internal write paths must remain idempotent/retry-safe for repeated webhook deliveries.
- Heavy operations:
  - Availability recalculation is bounded to one master + one day for MVP interactive paths.
  - Multi-day or multi-master aggregation is deferred from synchronous bot response path.
