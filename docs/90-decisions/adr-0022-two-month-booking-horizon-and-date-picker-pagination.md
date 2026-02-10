# ADR-0022: Two-month booking horizon and paginated date-picker strategy

Date: 2026-02-10
Status: Accepted
Deciders: Backend maintainers

## Context

Current callback date selection is optimized for short windows. Extending booking to a full rolling 2-month horizon risks overloading Telegram UI if all dates are rendered at once. Both client and master manual booking flows must keep navigation compact and deterministic.

## Decision

- Use a rolling 60-day horizon (`today .. today+59`) in business timezone for booking-date selection in:
  - client booking flow;
  - master manual booking flow.
- Use shared callback pagination contract:
  - date selection actions remain `csd|<YYYYMMDD>` and `mbd|<YYYYMMDD>`;
  - page navigation actions are `cdp|p<index>` and `mbp|p<index>`.
- Use fixed page size of 7 date buttons per page with explicit navigation buttons:
  - `Назад по датам` for previous page when available;
  - `Вперед по датам` for next page when available.
- Out-of-range or malformed page/date tokens are handled by existing deterministic invalid-callback response (`ru`).
- Shared helper functions own horizon bounds/page slicing to keep client/master behavior aligned.

## Alternatives considered

- Render full 2-month date list in one keyboard.  
  Rejected: poor Telegram UX and callback payload overhead.
- Keep short date window and require typed date input for far dates.  
  Rejected: inconsistent UX and higher input-error rate.
- Separate paging implementations per role.  
  Rejected: duplication and regression risk.

## Consequences

- Callback action surface expands with two new paged-navigation actions (`cdp`, `mbp`) under existing `hb1` version.
- Regression coverage must include:
  - first/last page navigation boundaries;
  - far-horizon booking success;
  - invalid page token handling.
- Runtime/deployment shape is unchanged; changes are limited to callback UX/state and tests/docs.
