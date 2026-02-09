# CI / quality gates (mandatory)

Merge strategy: merge-commit.

## Required checks (merge gate)

- Build + unit tests
- Lint/format (if applicable)
- **SAST** (mandatory)
- **Dependency scan** (mandatory)
- **Secrets scan** (mandatory)

## Implemented baseline

- Workflow file: `.github/workflows/ci.yml`
- Checkout policy: full git history in CI checkout (`fetch-depth: 0`) to support commit-range scanners (Gitleaks) on pull requests.
- Dependency update automation: `.github/dependabot.yml` (weekly grouped `pip` + GitHub Actions updates to reduce incompatible single-package bumps)
- Trigger: every `pull_request` and push to `master`
- Python version: `3.12`
- Postgres service for migration checks in CI

Security tools:

- SAST: `bandit` (runs `bandit -q -r app`)
- Dependency scan: `pip-audit` (runs `pip-audit` and fails on known vulnerabilities)
- Secrets scan: `gitleaks/gitleaks-action@v2`

Dependency policy baseline:

- Keep direct runtime dependencies pinned in `requirements.txt`.
- Do not pin transitive packages manually unless there is an active incident with no parent-package fix.
- Dependabot opens grouped updates so dependency graph changes are validated together by CI.

Schema regression check:

- CI applies migrations on fresh Postgres: `alembic upgrade head`
- Fails PR when migration scripts are broken or out of sync

## Local reproduction commands

Run from repository root:

1. `python -m venv .venv`
2. `.venv/bin/python -m pip install --upgrade pip`
3. `.venv/bin/pip install -r requirements.txt`
4. `.venv/bin/pip install pytest bandit pip-audit`
5. `docker compose up -d postgres`
6. `DATABASE_URL=postgresql+psycopg2://haircuttgbot:haircuttgbot@127.0.0.1:5432/haircuttgbot .venv/bin/alembic upgrade head`
7. `.venv/bin/pytest -q`
8. `.venv/bin/bandit -q -r app`
9. `.venv/bin/pip-audit`
10. `docker compose down`

## Failure interpretation

- `alembic upgrade head` failure: migration script issue or schema incompatibility.
- `pytest` failure: regression in runtime skeleton contract or imports.
- `bandit` failure: potential code security issue in `app/`.
- `pip-audit` failure: vulnerable dependency detected; upgrade dependency or document approved exception.
- `gitleaks` failure: potential secret committed; remove secret and rotate if exposed.

## Branch / PR policy

- PR required: YES
- Reviews required: TODO (set number)
- Merge method: merge-commit
