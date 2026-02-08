---
name: skill_template
description: Template for creating new Codex skills with required metadata and workflow structure.
---

# <skill-name>

## Purpose
One-sentence description of what this skill does and when to use it.

## Trigger
Use this skill when the user asks for <type of task> or when <condition>.

## Inputs
- Required:
  - `<input-1>`
- Optional:
  - `<input-2>`

## Workflow
1. Collect minimal context from repository files.
2. Validate assumptions and constraints.
3. Execute the task using scripts/templates in this skill folder when possible.
4. Update or generate artifacts in the target repository.
5. Verify outputs and report what changed.

## Outputs
- Primary artifact(s): `<path-or-type>`
- Validation artifact(s): `<tests/checks/logs>`

## Guardrails
- Keep changes minimal and repository-specific.
- Prefer deterministic commands over manual repetition.
- Do not modify unrelated files.

## References
- `references/` (add only files needed for this skill)
- `scripts/` (automation helpers)
- `assets/` (reusable templates)
