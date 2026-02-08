---
name: 04_start_next_epic
description: Select the next epic, create its workspace, and decompose it into mergeable PR groups.
---

# Skill 04 — Start next epic (select epic → workspace + tasks + PR groups)

## Developer prompt

Optionally pin an epic id (e.g., EPIC-003). If omitted, pick the first epic with Status=TODO.

## Agent instructions

Read only:

- `docs/05-planning/epics.md`
- `docs/01-product/requirements.md`
- `docs/02-nfr/*.md` (all)
- `docs/03-architecture/tech-stack.md`
- `docs/04-delivery/local-dev.md`
- `docs/04-delivery/deploy-vm.md`
- `docs/90-decisions/adr-0000-template.md`

Do:

1) Select the epic (pinned or first TODO). Set Status=IN_PROGRESS.
2) Create epic workspace:
    - `docs/05-planning/epics/<EPIC-ID>/README.md`
    - `docs/05-planning/epics/<EPIC-ID>/tasks.md` (each 1–3 dev-days)
    - `docs/05-planning/epics/<EPIC-ID>/pr-groups/group-01.md`
3) Group tasks so each PR group:
    - is mergeable via merge-commit
    - keeps docker-compose local run working
    - has acceptance checks
4) If the epic requires a non-trivial decision, create an ADR stub.

Stop condition:

- If decomposition needs new info, add questions and stop.
