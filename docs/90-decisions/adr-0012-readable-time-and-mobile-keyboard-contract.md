# ADR-0012: Readable time localization and mobile keyboard layout contract

Date: 2026-02-09
Status: Accepted
Deciders: TBD

## Context

EPIC-015 requires replacing raw timestamp output in Telegram messages with readable localized (`ru`) time/date strings and constraining interactive keyboard layouts for mobile usability. The project already supports mixed 30/60-minute services and callback-first flows, so formatting/layout decisions must remain consistent across client/master/admin handlers and avoid regressions in idempotent callback processing.

## Decision

Define one shared presentation contract for:

- readable `ru` slot/date rendering used by booking/schedule notifications and interactive selection text;
- keyboard row-width constraints and action grouping rules for primary client/master/admin menus.

Formatting contract (UTC-based runtime):

- Date label: `DD.MM.YYYY` (example: `11.02.2026`).
- Datetime label: `DD.MM.YYYY HH:MM` (example: `11.02.2026 18:45`).
- Slot button label: `HH:MM-HH:MM` (examples: `10:00-10:30`, `10:00-11:00`).

Keyboard layout contract:

- Main menu/action blocks: maximum `2` buttons per row.
- Date/slot selection blocks: maximum `3` buttons per row.
- Navigation actions (`Назад`, `Главное меню`) remain explicit dedicated controls appended after selection/action rows.

Implement this contract through shared helper utilities referenced by message/keyboard builders, then roll out handler integrations incrementally by PR group.

## Alternatives considered

1. Keep per-handler formatting logic and ad-hoc keyboard composition.
   - Rejected: high drift risk and inconsistent user output.
2. Introduce per-user locale and dynamic keyboard variants in this epic.
   - Rejected: scope expansion beyond MVP (`ru` only) and higher regression risk.
3. Delay keyboard layout polish and ship formatting-only changes.
   - Rejected: epic acceptance requires phone-friendly button layouts across key flows.

## Consequences

- Positive: consistent user-visible time output and predictable menu usability on mobile devices.
- Positive: centralized helpers reduce future formatting/layout maintenance cost.
- Negative: initial refactor touches multiple message and keyboard builders, requiring regression tests.
- Follow-up: complete rollout of readable-time formatting in all client/master/admin notification texts in EPIC-015 groups 02-03.
