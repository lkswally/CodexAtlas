# Codex-Atlas Mother Factory

## Mission

Codex-Atlas is the canonical parent system for reusable Codex setups.
Its job is to define and govern:
- agents
- skills
- workflows
- policies
- templates
- validators
- command contracts
- memory conventions

ATLAS is not a product runtime and is not REYESOFT.

## Scope Rules

- Keep the Atlas core reusable and project-agnostic.
- Do not add REYESOFT business logic to this repo.
- Derived projects may keep adapters, local registries and runtime-specific docs.
- Prefer minimal, auditable, reversible changes.

## Working Mode

- Evaluate first, then design, then implement only what has clear fit.
- Prefer documentation, metadata and stdlib tooling before frameworks.
- Avoid feature sprawl, hidden automation and external dependencies.
- Use manual validation and explicit human approval for risky changes.

## Hard Restrictions

- No MCP in this stage.
- No automatic hooks.
- No `.claude` directories or Claude-only files.
- No Engram or Pixel Bridge.
- No automatic deploy flows.
- Do not modify REYESOFT runtime from this repo.

## Canonical Boundaries

- Canonical Atlas core lives in `C:\Proyectos\Codex-Atlas`.
- REYESOFT is a derived project and may consume Atlas through adapters or copied templates.
- If the same concept exists in both places, Atlas is the source of truth unless the file is explicitly a REYESOFT adapter.
- Root-level directories are the primary Codex-native home of Atlas.
- `00_SISTEMA/_meta/atlas/` is legacy compatibility only.

## Main Executable Surface

- `tools/atlas_governance_check.py`
- `tools/atlas_dispatcher.py`

## Documentary Surface

- `adapters/`
- `agents/`
- `workflows/`
- `policies/`
- `memory/`
- `docs/`
- `commands/`
- `validators/`
- `templates/`
- `skills/`

## Decision Rule

When in doubt, choose the smallest change that improves Atlas as a governed factory rather than as an app.
