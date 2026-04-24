# Policy: project_boundary_check_policy

## Goal

Keep Atlas core separate from derived runtimes and prevent double sources of truth.

## Rules

- Atlas core lives only in `C:\Proyectos\Codex-Atlas`.
- Derived projects may expose `.atlas-project.json` and project-local adapters only.
- Atlas dispatcher, governance check, registries and mother policies must not live inside derived projects as active runtime files.
- Derived projects must not require `.claude`, `CLAUDE.md`, Engram or Atlas internals to function.
- Atlas must operate on derived projects from outside through `--project`.

## Checks to prefer

- `audit-repo` for structural allowlist drift
- `certify-project` for derivative integrity and Claude-only residue detection
- governance review before moving any shared file into a derived repo

## Blockers

- embedded Atlas core under a derived project
- mirrored command registry inside a product repo
- Claude-only runtime artifacts in Atlas or in a Codex-native derivative
