# Deployment to a single VM

## Target

A single VM hosts the “working project”.

## Recommended baseline approach

- Build a container image (or compose bundle)
- Copy release artifacts to VM (image registry or tarball)
- Run via docker-compose on the VM
- Use systemd to keep compose up (or a simple supervisor)
- Add a reverse proxy (optional): Nginx/Caddy/Traefik

## What must be documented for deploy

- VM OS and minimum specs
- Required open ports
- How to provision secrets/config
- Backup strategy (especially DB volumes)
- Rollback steps

## Minimal deploy outline (fill in)

1) Provision VM (TODO)
2) Install Docker + Compose (TODO)
3) Configure env/secrets (TODO)
4) Run `docker compose up -d` (TODO)
5) Verify smoke test (TODO)
6) Configure restart on reboot (TODO)
