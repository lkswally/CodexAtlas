# Workflow: certify_project

## Purpose

Run a read-only certification pass over an Atlas-derived project without modifying its runtime or embedding Atlas core inside it.

## Checks

1. `.atlas-project.json` exists and declares a valid Atlas-derived relationship
2. `README.md` and `AGENTS.md` exist at the project root
3. Base directories `docs/`, `memory/`, `workflows/`, `policies/` and `tools/` exist
4. If `project_profile` is declared, profile-specific directories match the canonical bootstrap contract
5. The derived project does not carry Atlas core internals, `.claude` or `CLAUDE.md`
6. Dispatcher and governance artifacts remain in Atlas, not inside the derivative
7. Certification remains read-only and does not mutate the derived repo

## Gate framing

- Metadata integrity gate
- Boundary integrity gate
- Bootstrap/profile integrity gate
- Claude-only artifact gate
- Handoff readiness gate

## Output

- score
- findings
- blockers
- warnings
- recommendations

## Status

Executable in read-only mode through `tools/atlas_dispatcher.py --project <path> certify-project`.
