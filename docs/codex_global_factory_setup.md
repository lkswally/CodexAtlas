# Codex Atlas Global Factory Setup

## Objective

Configure Codex Atlas as the default factory for Lucas projects so Codex does not operate as a plain direct coding agent unless that is explicitly requested.

The goal is:
- Atlas-first project entry
- mandatory governance checks before functional implementation
- consistent bootstrap for new projects
- explicit blocking when a project is missing the minimum Atlas governance surface

Canonical Atlas root:
- `C:\Proyectos\Codex-Atlas`

## Global Files

Codex global factory behavior depends on these files:

- `C:\Users\Lucas\.codex\AGENTS.md`
- `C:\Users\Lucas\.codex\config.toml`

### `C:\Users\Lucas\.codex\AGENTS.md`

This file defines the global operating rule:
- all Lucas projects should operate under CODEX ATLAS by default
- direct Codex work is not allowed unless Lucas asks for it explicitly
- the agent must audit governance before modifying files
- if a project lacks minimum Atlas governance, functional implementation is blocked

It also defines the operating modes:
- `ATLAS completo`
- `ATLAS gobernanza ligera`
- `Codex directo bloqueado`

### `C:\Users\Lucas\.codex\config.toml`

This file carries the global Codex configuration plus the Atlas factory section:

```toml
[atlas_factory]
enabled = true
atlas_root = 'C:\\Proyectos\\Codex-Atlas'
default_mode = 'atlas_required'
block_direct_codex_without_atlas = true
project_root_markers = ['.git', '.atlas-project.json', 'AGENTS.md', 'SPRINT_STATUS.md', 'PROJECT_STATUS.md', 'package.json', 'pyproject.toml']
```

This means Codex should:
- look for Atlas project markers first
- treat Atlas as the default factory root
- block direct feature work when the project does not satisfy minimum governance

## Root Markers

Current root markers configured in `config.toml`:

- `.git`
- `.atlas-project.json`
- `AGENTS.md`
- `SPRINT_STATUS.md`
- `PROJECT_STATUS.md`
- `package.json`
- `pyproject.toml`

These markers help Codex determine whether a directory is already under Atlas governance or still needs bootstrap.

## Operating Modes

### `ATLAS completo`

Use this mode when the project has:
- Git root
- local `AGENTS.md`
- local `.atlas-project.json`
- `SPRINT_STATUS.md` or `PROJECT_STATUS.md`
- Atlas registration and dispatcher surface available

In this mode, Atlas can allow:
- functional implementation under Atlas controls
- governance maintenance
- dispatcher-led audits
- Atlas entrypoint execution through `atlas_run.py` or `atlas.ps1`

### `ATLAS gobernanza ligera`

Use this mode when the project is partially governed but still incomplete.

Typical cases:
- local governance files exist, but Git is missing
- the project is linked to Atlas but lacks one required status/governance file
- bootstrap started but the repo is not ready for full Atlas execution

In this mode, Atlas should prefer:
- governance maintenance
- bootstrap completion
- audit/reporting

Functional implementation should stay blocked until the missing governance elements are completed.

### `Codex directo bloqueado`

Use this mode when Atlas minimum governance does not exist.

In this mode Codex must not implement features.

Only allowed work:
- create governance files
- prepare bootstrap
- audit the current surface
- suggest Git initialization if needed
- explain what is blocking progress

## Minimum Project Requirements

A project must have all of the following before Atlas allows functional implementation:

- Git root
- local `AGENTS.md`
- local `.atlas-project.json`
- `SPRINT_STATUS.md` or `PROJECT_STATUS.md`

Without those files, Codex should not move into direct feature work.

## Bootstrap a New Project

Use Atlas bootstrap instead of starting as direct Codex.

Primary tool:
- `C:\Proyectos\Codex-Atlas\tools\atlas_project_bootstrap.py`

Example:

```powershell
python C:\Proyectos\Codex-Atlas\tools\atlas_project_bootstrap.py --project C:\Proyectos\MyProject
```

What bootstrap creates:
- `AGENTS.md`
- `.atlas-project.json`
- `SPRINT_STATUS.md`

What bootstrap also does:
- infers a project profile
- writes minimum Atlas governance files
- registers the project in `memory/derived_projects.json`

If the project still lacks Git after bootstrap, Atlas should remain in `ATLAS gobernanza ligera` until Git is initialized.

## Audit an Existing Project

Use:
- `C:\Proyectos\Codex-Atlas\tools\atlas_context_audit.py`

Example:

```powershell
python C:\Proyectos\Codex-Atlas\tools\atlas_context_audit.py --project C:\Proyectos\SomeProject
```

This audit reports:
- Git root
- global and local instruction files read
- whether `.atlas-project.json` exists
- whether local `AGENTS.md` exists
- whether `SPRINT_STATUS.md` or `PROJECT_STATUS.md` exists
- whether the project is registered
- whether the dispatcher and command registry exist
- current operating mode
- whether functional work is allowed
- missing governance items

## Run a Project Through the Atlas Entrypoint

For Atlas-complete projects, the preferred entrypoint is:
- `C:\Proyectos\Codex-Atlas\tools\atlas_run.py`

Example:

```powershell
python C:\Proyectos\Codex-Atlas\tools\atlas_run.py --project-path C:\Proyectos\SomeProject --task "..." --mode plan --dry-run --require-dispatcher true
```

PowerShell wrapper:
- `C:\Proyectos\Codex-Atlas\tools\atlas.ps1`

Example:

```powershell
C:\Proyectos\Codex-Atlas\tools\atlas.ps1 -ProjectPath C:\Proyectos\SomeProject -Task "..." -Mode plan
```

This enforces:
- context audit first
- governance blockers before execution
- dispatcher requirement
- Atlas-first planning before Codex executor use

## Replicate on Another PC

To replicate this setup on another machine:

1. Clone or copy `C:\Proyectos\Codex-Atlas`.
2. Create `C:\Users\<user>\.codex\AGENTS.md` with the Atlas-first governance rule.
3. Create or update `C:\Users\<user>\.codex\config.toml`.
4. Add the Atlas factory block:

```toml
[atlas_factory]
enabled = true
atlas_root = 'C:\\Proyectos\\Codex-Atlas'
default_mode = 'atlas_required'
block_direct_codex_without_atlas = true
project_root_markers = ['.git', '.atlas-project.json', 'AGENTS.md', 'SPRINT_STATUS.md', 'PROJECT_STATUS.md', 'package.json', 'pyproject.toml']
```

5. Verify that the Atlas root path matches the new machine.
6. Use `atlas_project_bootstrap.py` to govern new or existing repos.
7. Use `atlas_context_audit.py` before functional work.

If needed, also replicate any local PowerShell convenience wrapper separately, but the factory rule itself depends on `AGENTS.md` and `config.toml`.

## What Codex Must Not Do Without Governance

If minimum governance is missing, Codex must not:
- implement product features
- perform major architecture changes
- add external integrations
- run hidden automation
- bypass Atlas entrypoints for functional work

Instead, Codex should:
- explain the missing governance pieces
- bootstrap the project if allowed
- suggest `git init` when Git is missing
- produce an audit report

## Practical Rule

If a project is not yet Atlas-complete, Codex should treat bootstrap and audit as the task.

If a project is Atlas-complete, Codex should still prefer the Atlas entrypoint and governance workflow over direct freeform implementation.
