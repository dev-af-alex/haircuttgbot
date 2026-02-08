# Epics roadmap (SSOT)

Status values: TODO / IN_PROGRESS / DONE / BLOCKED.

Rules:

- Each epic must keep the system runnable locally via docker-compose.
- Every epic must state acceptance criteria.
- Include deployment to a single VM as a first-class deliverable.

## Epics

- EPIC-001 — Project bootstrap (compose + CI gates + skeleton) — Status: TODO
    - Goal: replace placeholder compose with real project compose; have a runnable skeleton.
    - Acceptance:
        - `docker compose up -d` runs the real app
        - smoke test passes
        - CI has SAST + dep scan + secrets scan
    - Depends on: tech stack selected (`docs/03-architecture/tech-stack.md`)

- EPIC-002 — VM deployment baseline — Status: TODO
    - Goal: deploy working project to a single VM.
    - Acceptance:
        - documented steps in `docs/04-delivery/deploy-vm.md`
        - deploy uses docker-compose on VM
        - rollback steps documented

(Add product epics derived from `docs/01-product/requirements.md` below.)
