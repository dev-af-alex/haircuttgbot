# PR checklist (merge gate)

Before opening PR:

- `docker compose up -d` succeeds (local)
- Smoke test passes (local)
- No embedded inline smoke scripts are added to docs (`python - <<'PY'`, heredoc blocks for smoke)
- Docs updated if behavior/interfaces/constraints changed
- No debug leftovers
- No secrets committed

Before merge:

- CI is green
- SAST + dependency scan + secrets scan ran and passed
- Reviewer verified `docs/04-delivery/local-dev.md` is still accurate
- Any non-trivial decision has an ADR
- Merge method is merge-commit (per policy)
