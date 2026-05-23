# SPRINT_STATUS - Codex-Atlas

## Governance
- Atlas root: `C:\Proyectos\Codex-Atlas`
- Operating mode: `ATLAS completo`
- Project profile: `backend_service`
- Project type: `atlas-factory-core`

## Current Sprint
- Status: `factory-governance-bootstrap`
- Goal: enable ATLAS governance for the factory itself without changing functional code.

## In Scope Now
- Create or repair `.atlas-project.json`.
- Create or repair `SPRINT_STATUS.md`.
- Audit factory governance status.
- Document infrastructure bugs and planning notes.

## Out of Scope Now
- Functional code changes.
- Executor bug fixes.
- Dispatcher changes.
- Registry changes.
- Workflow changes.
- Test changes.
- Hidden automation or MCP activation.

## Known Infrastructure Bug
- `atlas_run.py` in `execute` mode currently attempts to invoke `codex exec` with `--ask-for-approval`.
- The installed local `codex exec` CLI does not support that flag.
- Do not fix this bug in this bootstrap block.

## Functional Work Gate
Functional implementation is allowed only when:
1. The task fits an explicitly approved factory maintenance scope.
2. ATLAS context audit passes first.
3. Dispatcher, registry, and phase gate are checked.
4. No governance or dirty-worktree blocker is present.

## Required Checks
- `python C:\Proyectos\Codex-Atlas\tools\atlas_context_audit.py --project "C:\Proyectos\Codex-Atlas"`
- `python C:\Proyectos\Codex-Atlas\tools\atlas_run.py --project-path "C:\Proyectos\Codex-Atlas" --task "<task>" --mode plan --dry-run --require-dispatcher true`
- Targeted tests only when a later approved task changes functional code.

## Next Step
- Run final Atlas context audit.
- Plan the executor feature-detection fix in a separate task before touching code.
- Do not commit this bootstrap unless explicitly approved.
