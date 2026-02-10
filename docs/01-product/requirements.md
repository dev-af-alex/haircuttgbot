# Product requirements (FR) and scope (SSOT)

## 1) One-paragraph summary

Telegram bot for a barbershop with two roles, `Client` and `Master` (multiple masters supported). A client can view available time slots, choose service type (haircut, beard trim, or both), create/cancel bookings, and receive notifications. A master can view and manage their schedule, create manual bookings received outside the bot, set days off, define a daily lunch break, and cancel a client booking with a mandatory cancellation reason sent to the client. Booking slots are 60 minutes, with master working hours from 10:00 to 21:00. Default lunch break is 13:00-14:00 and can be changed by the master.

## 2) Users and roles

- Client: browses availability, creates/cancels own booking, selects service type.
- Master: manages own working calendar, adds external/manual bookings, sets day-off and lunch break, cancels bookings with reason.
- System bot: validates booking rules and sends service notifications to clients and masters.

## 3) Core user journeys (3–7)

- Client opens bot and selects a master.
- Client views available dates/time slots for selected service.
- Client creates a booking and receives confirmation.
- Client cancels own booking and receives cancellation confirmation.
- Master reviews upcoming schedule.
- Master blocks availability by setting day-off and daily lunch break.
- Master adds manual bookings and can cancel existing client booking with reason notification.

## 4) Functional requirements (FR)

Write as “The system shall ...”

- FR-001: The system shall support two roles: `Client` and `Master`.
- FR-002: The system shall support more than one master profile.
- FR-003: The system shall allow a client to view available booking dates and time slots for a selected master.
- FR-004: The system shall allow a client to choose a service option: haircut only, beard only, or haircut + beard.
- FR-005: The system shall allow a client to create a booking for an available slot.
- FR-006: The system shall prevent booking into occupied, day-off, or lunch-break time slots.
- FR-007: The system shall allow a client to cancel their own active booking.
- FR-008: The system shall allow a master to view and manage their schedule.
- FR-009: The system shall allow a master to create manual bookings for requests accepted outside the bot.
- FR-010: The system shall allow a master to set day-off periods during which clients cannot book that master.
- FR-011: The system shall allow a master to configure a daily one-hour lunch break during which clients cannot book that master.
- FR-012: The system shall allow a master to cancel a client booking and require a cancellation reason.
- FR-013: The system shall send the client a cancellation notification that includes the reason when a master cancels a booking.
- FR-014: The system shall send booking creation/cancellation confirmations to relevant participants.
- FR-015: The system shall use a default booking slot duration of 60 minutes.
- FR-016: The system shall use a master working-hours window from 10:00 to 21:00.
- FR-017: The system shall restrict a client to at most one active future booking at a time.
- FR-018: The system shall provide master schedule management through Telegram bot interactions only in MVP.
- FR-019: The system shall apply a default lunch break from 13:00 to 14:00 for each master.
- FR-020: The system shall allow the master to change their lunch-break time.
- FR-021: The system shall provide Russian (`ru`) localization for bot messages in MVP.
- FR-022: The system shall include client identity context in master booking notifications (Telegram nickname when available, and phone when available).
- FR-023: The system shall include exact booking date/time in client notifications when booking is cancelled by a master.
- FR-024: The system shall allow masters to provide arbitrary free-text client reference in manual booking flow and persist it for schedule/notification rendering.

## 5) Non-goals (explicit exclusions)

- NG-001: Online payments are out of scope.
- NG-002: Loyalty programs, promotions, and coupons are out of scope.
- NG-003: Multi-branch salon management is out of scope for initial version.
- NG-004: Native mobile/web applications are out of scope; Telegram bot is the primary interface.

## 6) External integrations

- Telegram Bot API
    - Auth: Bot token; role assignment by internal mapping of Telegram user ID to role.
    - Rate limits: TODO (confirm expected request volume and retry policy).
    - Data: Incoming user messages/callbacks; outgoing notifications and menu states.

## 7) Data handled (high level)

- Data types: Telegram user IDs, display names/usernames, role mapping, booking records (master, service type, slot, status), schedule blocks (day-off, lunch break), cancellation reasons, bot interaction metadata.
- Sensitivity: Internal/confidential (personal schedule and contact metadata, but no payment card data in scope).

Links:

- Open questions: `docs/01-product/open-questions.md`
- Glossary: `docs/01-product/glossary.md`
- Security NFR: `docs/02-nfr/security.md`
