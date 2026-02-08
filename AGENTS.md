# Repository Guidelines

## Project Structure & Module Organization
This repository is currently a delivery template and knowledge base. Core content lives in:
- `docs/`: source of truth for product, architecture, delivery, and planning.
- `checklists/`: merge and completion gates (`pr.md`, `definition-of-done.md`, `doc-sync.md`).
- `docker-compose.yml`: placeholder local runtime entrypoint; replace during the first implementation epic.

Use `docs/index.md` as the navigation hub. Epic workspaces follow `docs/05-planning/epics/EPIC-###/`.

## Build, Test, and Development Commands
- `docker compose up -d`: start the local stack (required local run path).
- `docker compose down`: stop local services.
- `docker compose ps`: inspect container health/state.
- `docker compose logs -f`: stream service logs while debugging.

Current smoke test steps are documented in `docs/04-delivery/local-dev.md` and must pass before PR/merge.

## Coding Style & Naming Conventions
Code style tools are not fixed yet (see `docs/03-architecture/tech-stack.md`), so keep changes minimal and explicit.
- Use descriptive, small commits and keep docs synchronized with behavior changes.
- Follow existing naming patterns: `EPIC-001`, task IDs like `T-001`, and kebab-case Markdown filenames.
- Prefer one concern per file edit; update relevant SSOT docs in the same PR.

## Testing Guidelines
Framework and coverage thresholds are TBD, but quality gates are not optional:
- Unit/build checks must pass in CI.
- SAST, dependency scan, and secrets scan must run and pass on PRs.
- Add tests for behavior changes, or document why tests are not added (DoD requirement).

## Commit & Pull Request Guidelines
Git history currently contains a single bootstrap commit (`init`), so no mature commit convention exists yet. Adopt concise imperative subjects (example: `Add smoke test for auth login`).

For every PR:
- Ensure local run works via `docker compose up -d`.
- Pass smoke test and CI gates.
- Update docs when interfaces, constraints, or workflows change.
- Use merge commits (repository policy) and reference related epic/task IDs.

## Security & Configuration Notes
Never commit secrets or PII. Treat `docs/04-delivery/ci.md` as mandatory policy for security scanning behavior and failure handling.
