# EPIC-012 callback contract and UX map (group-01)

Status: Accepted for group-01 foundation
Version: `hb1`

## UX map (button-first foundation)

`Client`:
- Root menu -> `Клиент` -> client menu scaffold
- Client menu scaffold -> `Назад` -> root menu

`Master`:
- Root menu -> `Мастер` -> master menu scaffold
- Master menu scaffold -> `Назад` -> root menu

Shared:
- Root/menu scaffold -> `Обновить`/`Главное меню` -> root menu refresh

Note:
- Business actions (booking/schedule writes) are intentionally out of group-01 and stay command-driven.

## Callback payload schema

Encoding:
- `hb1|<action>`
- `hb1|<action>|<context>`

Constraints:
- Max callback payload size: 64 bytes
- `context` regex: `^[A-Za-z0-9_-]{1,32}$`
- Unsupported prefix/version is rejected deterministically

Actions (group-01):
- `hm` -> open root menu
- `cm` -> open client menu scaffold (requires RBAC `client:book`)
- `mm` -> open master menu scaffold (requires RBAC `master:schedule`)
- `bk` -> back to root menu

Backward compatibility strategy:
- Existing slash-command handlers remain available during EPIC-012 rollout.
- Callback parser is versioned by prefix (`hb1`) so future formats can coexist.

## Stale action rules

- Router keeps short-lived menu state per Telegram user (`TTL=900s`).
- Action allowedness is validated against the current menu-state allowlist.
- If action is not allowed for current state, response is deterministic stale reply:
  - `Кнопка устарела. Откройте актуальное меню через /start.`
- Stale events are logged as `telegram_callback_stale`.

## Invalid action rules

- Malformed/oversized/unknown callback payloads get deterministic reply:
  - `Кнопка недействительна. Откройте меню заново через /start.`
- Invalid payload attempts are logged as `telegram_callback_invalid` with reason code.

## Localization keys used (ru)

- `unknown_user` (existing): `Пользователь не найден. Обратитесь к администратору салона.`
- `forbidden` (existing via RBAC): `Недостаточно прав для выполнения команды.`
- `invalid_callback` (new): invalid callback payload/stucture
- `stale_callback` (new): expired or out-of-state callback action

## Auditability expectations

- RBAC denials on callback path emit `rbac_deny` with `command=callback:<action>`.
- No secret values are included in callback events or response payloads.
