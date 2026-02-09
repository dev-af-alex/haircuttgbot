# EPIC-017 tasks

Each task is scoped to 1-3 dev-days and mapped to mergeable PR groups.

| Task ID | Title | Scope | Estimate | Depends on | Planned PR group | Status |
|---|---|---|---|---|---|---|
| T-001 | Define master display identity policy ADR | Document master-name source and fallback order for client-facing texts, including missing-data behavior | 1 day | EPIC-013, EPIC-015 | group-01 | DONE |
| T-002 | Implement role-first `/start` routing baseline | Remove intermediate main menu from start path and route resolved users directly into role panels | 1-2 days | EPIC-012, EPIC-013 | group-01 | DONE |
| T-003 | Add localized greeting contract for `/start` | Replace command-list style start response with barbershop greeting while preserving role-aware branching | 1 day | T-002 | group-01 | DONE |
| T-004 | Integrate master display name into client master selection | Replace `Master ID` representation with display-name rendering in client master-choice flow | 1-2 days | T-001 | group-02 | DONE |
| T-005 | Integrate master display name into booking confirmation texts | Ensure booking confirmation/cancel-adjacent client texts consistently use master display name | 1-2 days | T-001, T-004 | group-02 | DONE |
| T-006 | Expand regression tests for role-first entry and name rendering | Add automated coverage for direct role landing, greeting response, and master-name output contracts | 2-3 days | T-003, T-005 | group-03 | DONE |
| T-007 | Synchronize local and VM smoke validation docs | Update delivery docs with Telegram checks for role-direct start flow and master-name texts | 1 day | T-006 | group-03 | DONE |
| T-008 | Epic closure and checklist/doc-sync prep | Verify epic artifact status alignment and readiness for close workflow | 1 day | T-007 | group-03 | DONE |

## Notes

- Grouping keeps `docker compose up -d` runnable after every merge.
- Group-01 isolates entry/routing foundation before client text contract rewiring.
