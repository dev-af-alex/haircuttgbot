---
name: 05_implement_next_pr_group
description: Implement the next PR group with tests and synchronized documentation updates.
---

# Skill 05 — Implement next PR group (code + tests + doc sync)

## Developer prompt

- EPIC-ID
- PR group to implement (default: first incomplete)
- any constraints for this iteration

## Agent instructions

Read only:

- `docs/05-planning/epics/<EPIC-ID>/README.md`
- `docs/05-planning/epics/<EPIC-ID>/tasks.md`
- `docs/05-planning/epics/<EPIC-ID>/pr-groups/<GROUP>.md`
- `checklists/doc-sync.md`
- `checklists/definition-of-done.md`
- `checklists/pr.md`
- `docs/04-delivery/local-dev.md`

Do:

1) Implement only tasks in the selected PR group.
2) Update docs per `checklists/doc-sync.md`.
3) Ensure docker-compose local run + smoke test still pass (update `docs/04-delivery/local-dev.md` if needed).
4) Mark tasks DONE in group file and tasks.md.

Output:

- summary of changes
- list of files changed
- follow-ups/risks
