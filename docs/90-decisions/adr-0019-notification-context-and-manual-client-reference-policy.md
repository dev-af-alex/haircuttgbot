# ADR-0019: Notification context and manual-client reference policy

Date: 2026-02-10
Status: Accepted
Deciders: Backend maintainers, product owner

## Context

Current booking and cancellation notifications do not provide enough context to master/client participants.
EPIC-022 requires richer, readable notifications with exact appointment date/time, and manual booking must support arbitrary client text provided by master.
The product also requests phone inclusion "if possible", which introduces data-source and privacy boundaries for notification payloads and logs.

## Decision

- Define deterministic identity rendering precedence for notifications: explicit manual client text (for manual bookings), then Telegram nickname/username, then safe fallback label.
- Include phone in notifications only when it is present in trusted stored contact/profile data and allowed by privacy policy; otherwise omit phone field entirely.
- Keep phone/contact values out of structured logs except masked form where operationally required.
- Persist manual booking client text as a dedicated domain field to avoid overloading Telegram identity attributes.
- Keep all date/time in notifications rendered via existing localized readable formatter and business timezone policy.

## Alternatives considered

1. Always require phone for manual bookings.
   - Pros: complete contact context in every master notification.
   - Cons: blocks flow usability and conflicts with "if possible" requirement.
2. Allow free-form client text without storing it in booking model.
   - Pros: lower schema impact.
   - Cons: context cannot be reliably reproduced in schedule views and follow-up notifications.
3. Put phone and identity details into audit logs for traceability.
   - Pros: easier debugging.
   - Cons: privacy and security risk due to sensitive personal data exposure in logs.

## Consequences

Positive:

- Master and client notifications become actionable and understandable.
- Manual booking no longer depends on existing Telegram user records.
- Privacy constraints are explicit for phone usage and logging.

Negative:

- Adds schema/service complexity for context resolution and fallback handling.
- Requires additional regression checks for text contracts and log masking.

Follow-up actions:

- Implement regression matrix for identity/phone/fallback rendering scenarios.
- Update local/VM smoke docs to validate informative notifications and manual free-text booking.
