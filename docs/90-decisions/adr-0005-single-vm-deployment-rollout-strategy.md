# ADR-0005: Single-VM deployment rollout strategy baseline

Date: 2026-02-09
Status: Proposed
Deciders: Engineering

## Context

EPIC-008 requires a reproducible deployment and rollback baseline for a single Linux VM. We need a default release transport and rollback strategy that fits current docker-compose architecture and keeps operational complexity low.

## Decision

TODO in EPIC-008 Group 01.
Candidate direction: ship a versioned compose bundle with environment file templates, deploy with deterministic `docker compose` commands, and rollback by re-running previous known-good bundle.

## Alternatives considered

- Build/pull container image directly from registry on VM without versioned compose bundle.
- Full configuration-management approach (Ansible/Terraform + remote orchestration).
- Ad-hoc manual container restart process without formal release artifact.

## Consequences

Positive, negative, and follow-up actions will be finalized during EPIC-008 after deployment command path and rollback checks are validated.
