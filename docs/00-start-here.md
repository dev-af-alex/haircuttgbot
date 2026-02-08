# How to read and maintain this knowledge base

## Layering rule (minimize irrelevant reading)

1) Product (docs/01-product): what must be built
2) NFR (docs/02-nfr): constraints
3) Architecture (docs/03-architecture): solutions + stack
4) Delivery (docs/04-delivery): local run + CI + deploy
5) Planning (docs/05-planning): epics/tasks
6) Decisions (docs/90-decisions): ADRs for non-trivial choices

An agent must only read the documents listed in the invoked skill.

## Single source of truth (SSOT)

- Terms: `docs/01-product/glossary.md`
- Scope and FR: `docs/01-product/requirements.md`
- Tech stack: `docs/03-architecture/tech-stack.md`
- Local run: `docs/04-delivery/local-dev.md`
- Epics status: `docs/05-planning/epics.md`

## “Must run locally” rule

No PR is merged unless:

- docker-compose run steps succeed (`docs/04-delivery/local-dev.md`)
- smoke test succeeds (defined there)

## Non-trivial decisions

Create an ADR in `docs/90-decisions/`.
