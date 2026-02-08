# Glossary (SSOT)

- Client — end user who books or cancels barber services through Telegram bot.
- Master — barber who owns and manages their own working schedule.
- Booking — reserved time slot between a client and a master for a selected service.
- Service option — selected work type: haircut, beard, or haircut + beard.
- Time slot — discrete time interval available for booking.
- Working-hours window — daily period when a master accepts bookings (10:00-21:00 by current SSOT).
- Manual booking — booking created by a master for an order accepted outside the bot.
- Day off — master-defined unavailable date/period where booking is disabled.
- Lunch break — daily one-hour unavailable period for each master.
- Default lunch break — initial daily lunch interval set to 13:00-14:00, editable by a master.
- Localization — language configuration for user-facing bot messages (Russian in MVP).
- Cancellation reason — mandatory explanation provided by a master when canceling a client booking.
- Availability calendar — computed schedule view that excludes occupied slots, day-off periods, and lunch break.

Rules:

- If you introduce a new term anywhere, add it here.
- Prefer fewer, sharper terms.
