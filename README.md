# AI-agent project template (developer-in-the-loop)

Template repository to build a product from scratch with an AI agent guided by a developer.

Key constraints baked in:

- Local run **must be via docker-compose**
- “Working project” deployment target is **a single VM**
- Security gates are mandatory: **SAST + dependency scan + secrets scan**
- Merge strategy: **merge-commit**
- Skills live in `/.codex/skills` (no other framework required)

## Quick start (workflow)

1) Run **Skill 01: Bootstrap** and paste short FRs.
2) Answer questions in `docs/01-product/open-questions.md`, then run **Skill 02: Lock Inputs**.
3) Run **Skill 03: Plan Epics** to generate `docs/05-planning/epics.md`.
4) Run **Skill 04: Start Next Epic** to create epic workspace + tasks + PR groups.
5) Run **Skill 05: Implement Next PR Group** repeatedly until the epic is done.
6) Open PR. Use `checklists/pr.md` as a merge gate.
7) Run **Skill 06: Close Epic** when the epic is complete.

## Knowledge base entrypoint

- `docs/index.md`

## Notes

This template includes a placeholder `docker-compose.yml` so `docker compose up` works immediately.
It must be replaced by the project’s real compose setup during the first implementation epic.
