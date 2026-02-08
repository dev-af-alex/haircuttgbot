---
name: 01_bootstrap_project
description: Bootstrap project knowledge base from initial requirements and select a concrete tech stack.
---

# Skill 01 — Bootstrap knowledge base (FR intake → questions → initial docs → choose stack)

## Developer prompt (paste after calling the skill)

Provide short functional requirements:

- target users/roles
- 3–7 core journeys
- key integrations
- hard constraints (hosting=single VM, budget, preferred languages, etc.)

## Agent instructions

Read only:

- `docs/index.md`
- `docs/00-start-here.md`
- `docs/01-product/requirements.md`
- `docs/01-product/glossary.md`
- `docs/01-product/open-questions.md`
- `docs/02-nfr/security.md`
- `docs/02-nfr/performance.md`
- `docs/02-nfr/reliability.md`
- `docs/02-nfr/privacy.md`
- `docs/03-architecture/tech-stack.md`
- `docs/90-decisions/adr-0000-template.md`

Do:

1) Insert the developer’s FR text into `docs/01-product/requirements.md` (sections 1–6).
2) Extract domain terms and update `docs/01-product/glossary.md`.
3) Generate missing critical questions and write them into `docs/01-product/open-questions.md` (prioritized).
4) Fill NFR docs with TODO placeholders derived from FRs (do not guess values).
5) **LAST STEP: propose and fix the tech stack** in `docs/03-architecture/tech-stack.md`:
    - pick a concrete backend/frontend/db/ops toolchain suitable for docker-compose + single VM
    - justify the choice with 3–7 bullet points
    - list any assumptions
    - specify security tools placeholders (SAST/dep/secrets)
    - create an ADR: `docs/90-decisions/adr-0001-tech-stack.md` using the template

Stop condition:

- If any High priority questions exist that block a reasonable stack choice, stop and ask the developer to answer them,
  then re-run Skill 01.
