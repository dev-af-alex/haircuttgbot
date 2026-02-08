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
- Trigger: every `pull_request` and push to `master`
- Python version: `3.12`
- Postgres service for migration checks in CI

Security tools:

- SAST: `bandit` (runs `bandit -q -r app`)
- Dependency scan: `pip-audit` (runs `pip-audit` and fails on known vulnerabilities)
- Secrets scan: `gitleaks/gitleaks-action@v2`

Schema regression check:

- CI applies migrations on fresh Postgres: `alembic upgrade head`
- Fails PR when migration scripts are broken or out of sync

## Local reproduction commands

Run from repository root:

1. `python -m pip install --upgrade pip`
2. `pip install -r requirements.txt`
3. `pip install pytest bandit pip-audit`
4. `docker compose up -d postgres`
5. `DATABASE_URL=postgresql+psycopg2://haircuttgbot:haircuttgbot@localhost:5432/haircuttgbot alembic upgrade head`
6. `pytest -q`
7. `bandit -q -r app`
8. `pip-audit`
9. `docker compose down`

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
