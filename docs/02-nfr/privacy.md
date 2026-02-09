# Privacy NFR

## 1) Data minimization

- Only collect: Telegram identifiers needed for role mapping and notifications, booking metadata, schedule blocks, cancellation reasons.
- Avoid collecting: unnecessary profile data, payment data, and free-text personal notes not required for scheduling.

## 2) User rights (if applicable)

- Export:
  - On verified request, provide user booking history export (JSON/CSV) for last 12 months.
  - Target fulfillment window: up to 7 calendar days.
- Deletion:
  - Account delete request removes direct Telegram linkage and anonymizes historical booking records where legally allowed.
  - Operational/security records needed for incident and fraud analysis may be retained for bounded retention window.
- Consent:
  - First interaction must include short privacy notice (data categories + purpose + support contact).
  - If jurisdiction requires explicit consent, bot flow must capture and persist consent flag before processing non-essential interactions.

## 3) Retention

- Retention policy:
  - Booking/schedule operational records: 24 months.
  - Security/audit event logs: 180 days hot, then archival or purge per incident needs.
  - Throttling deny telemetry in metrics store: rolling 30 days.
- Deletion policy:
  - Application entities use soft-delete/anonymization first to preserve referential integrity.
  - Hard delete is allowed for auxiliary user metadata after retention expiry or approved deletion request.
