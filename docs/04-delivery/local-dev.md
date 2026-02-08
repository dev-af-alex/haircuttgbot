# Local development via docker-compose (SSOT)

## Definition: “system runs locally”

A developer can run:

- `docker compose up -d`
- a smoke test
  and get a successful result.

## Prerequisites

- Docker Engine
- Docker Compose v2 (`docker compose`)
- Make sure required ports are free (document them below)

## Local run steps (must be kept current)

1) `docker compose up -d`
2) Wait for healthy services (document health checks)
3) Run smoke test (below)
4) `docker compose down` to stop

## Ports

- 8080: placeholder (replace with real app ports)

## Smoke test (must pass on every PR)

- TODO: describe a minimal end-to-end check (curl/http call / UI step)

## Notes

This repo ships with a placeholder `docker-compose.yml` to validate the workflow.
Replace it with the project’s real compose setup in the first implementation epic.
