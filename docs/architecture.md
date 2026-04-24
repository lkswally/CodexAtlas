# Codex-Atlas Architecture

## Core idea

Atlas is the reusable parent factory.
It governs capabilities, workflows and validation rules for future derived projects.

## Layers

- `commands/`, `policies/`, `memory/`: root-first canonical governance metadata
- `tools/`: executable validator and dispatcher
- `agents/`, `workflows/`, `docs/`: documentary operating system of the factory
- `adapters/`: derived-project integration notes and contracts
- `templates/`, `skills/`, `validators/`, `commands/`: controlled extension points

## Legacy layer

- `00_SISTEMA/_meta/atlas/` remains as a compatibility mirror
- it is not the primary home of the mother configuration
- it should stay aligned with the root-first canonical files while compatibility is needed

## Boundary with derived projects

- Atlas owns reusable rules, contracts and standards
- derived repos own runtime, business logic and local adapters
- shared concepts should move through templates, registries or documented adapter contracts
- derived repos can expose `.atlas-project.json` so Atlas tools can audit them externally with `--project`

## Current executable surface

- governance check
- minimal dispatcher with `audit-repo`

Everything else in Level 1 is intentionally documentary.
