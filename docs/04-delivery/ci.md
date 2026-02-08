# CI / quality gates (mandatory)

Merge strategy: merge-commit.

## Required checks (merge gate)

- Build + unit tests
- Lint/format (if applicable)
- **SAST** (mandatory)
- **Dependency scan** (mandatory)
- **Secrets scan** (mandatory)

## Minimum expectations for security gates

- SAST: runs on every PR and on default branch
- Dependency scan: fails on critical/high according to your policy (define policy)
- Secrets scan: blocks on detected secrets; add allow-list policy if needed

## Suggested documentation to add per tool

For each gate, document:

- tool name + version
- config file path
- how to run locally (command)
- how to interpret failures

## Branch / PR policy

- PR required: YES
- Reviews required: TODO (set number)
- Merge method: merge-commit
