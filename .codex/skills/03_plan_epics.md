# Skill 03 — Plan epics (SSOT docs → roadmap)

## Developer prompt (optional)

- MVP date (if any)
- optimize for speed or quality
- any mandatory tools (CI platform, scanners)

## Agent instructions

Read only:

- `docs/01-product/requirements.md`
- `docs/02-nfr/security.md`
- `docs/02-nfr/performance.md`
- `docs/02-nfr/reliability.md`
- `docs/02-nfr/privacy.md`
- `docs/03-architecture/tech-stack.md`
- `docs/04-delivery/local-dev.md`
- `docs/04-delivery/deploy-vm.md`

Do:

1) Create/update `docs/05-planning/epics.md`:
    - 5–15 epics, ordered by dependency/value
    - must include: (a) compose runnable skeleton + CI security gates, (b) VM deploy baseline
    - each epic has goal + acceptance + dependencies + local-run impact
2) If planning is blocked by unknowns, add them to `docs/01-product/open-questions.md` and stop.
