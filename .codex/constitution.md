# Agent constitution (repo-local)

Non-negotiables:

- Local run is via docker-compose and must remain working after every PR group.
- Mandatory CI gates must exist and remain enabled: SAST + dependency scan + secrets scan.
- If unknown requirements exist, create/keep questions in `docs/01-product/open-questions.md` (do not guess).
- Read only the documents listed by the invoked skill.
- Keep docs short and linked; avoid redundant copies.
- For non-trivial decisions, create ADRs in `docs/90-decisions/`.

Prohibitions:

- Do not commit secrets/tokens/credentials.
- Do not invent compliance/legal constraints without explicit input.
