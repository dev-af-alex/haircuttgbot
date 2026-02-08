# Skill 02 — Lock inputs (answers → SSOT update → remove questions)

## Developer prompt

Provide answers to questions from `docs/01-product/open-questions.md`.

## Agent instructions

Read only:

- `docs/01-product/open-questions.md`
- `docs/01-product/requirements.md`
- `docs/01-product/glossary.md`
- `docs/02-nfr/*.md` (all)
- `docs/03-architecture/tech-stack.md`

Do:

1) Move each answer into the proper SSOT document.
2) Remove answered questions from `docs/01-product/open-questions.md`.
3) If answers impact stack/tooling, update `docs/03-architecture/tech-stack.md` and (if non-trivial) add/update ADR.

Stop condition:

- If any High priority questions remain, stop and ask for them.
