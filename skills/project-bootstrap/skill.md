# Skill: project-bootstrap

## Purpose

Bootstrap a new Atlas-derived project with clear scope, boundaries, adapters and validation rules before implementation starts.

## When to use

- when creating a new derived project from Atlas
- when a project needs a clean bootstrap plan
- when the first step should be structure, not code

## When NOT to use

- when the project already exists and only needs a local refactor
- when the work is a simple documentation update
- when the request is mainly runtime debugging

## Required inputs

- project goal
- scope and non-scope
- target runtime or stack
- constraints and approval boundaries
- explicit `output_dir` for scaffold execution

## Expected outputs

- bootstrap plan
- suggested project structure
- adapter boundaries
- validation checklist
- minimal derived-project scaffold only when execution is explicitly requested

## Recommended agent

- `orchestrator` for entry routing
- `planner` for the concrete bootstrap plan

## Recommended workflow

- `create_project`

## Recommended model

- `deep_reasoning`

## Risks

- over-designing too early
- mixing Atlas core with project-specific runtime
- creating empty structure without ownership

## Validations

- scope is explicit
- runtime stays in the derived repo
- human approval boundaries are clear
- rollback is simple

## Minimal scaffold contract

Canonical source:
- `skills/project-bootstrap/bootstrap_contract.json`

Required inputs for execution:
- `project_goal`
- `scope_and_non_scope`
- `target_runtime_or_stack`
- `constraints_and_approval_boundaries`
- `output_dir`

Optional quality input:
- `project_type`: `backend_service`, `frontend_app`, `fullstack`, `internal_tool`, `ai_agent_system`

Minimum generated structure:
- directories: `docs`, `memory`, `workflows`, `policies`, `tools`
- files: `README.md`, `AGENTS.md`, `.atlas-project.json`
- additional directories and content focus depend on the selected `project_type`

Safety limits:
- execution requires an explicit `output_dir`
- `output_dir` must be missing or empty before execution
- do not write inside REYESOFT or any derived-project runtime path unless that project is being intentionally created there
- do not install dependencies, connect MCPs or execute runtime code
- do not generate business logic, runtime modules or deployment artifacts

Manual rollback:
- inspect the generated scaffold before using it
- delete the generated `output_dir` manually if the scaffold is not needed
- if the filesystem blocks deletion, document the blocked cleanup and remove it later with explicit access

Validation checks:
- generated directories exist
- `README.md` exists
- `AGENTS.md` exists
- `.atlas-project.json` exists
- metadata declares `project_type = atlas-derived-project`

The execution helper must consume this contract from metadata rather than rebuilding it inline.
The execution preflight must decide safety from the real filesystem state of `output_dir`, not only from textual trigger matching.
The generated README and AGENTS files should include useful starter context, not empty placeholders.

## Examples

- "Create a new Atlas-derived project for an internal operations dashboard."
- "Bootstrap a new product repo from Atlas with clean adapters and no MCP."

## Relationship with the orchestrator

The orchestrator should recommend this skill when the task intent is `project_creation` or when the request is about starting, bootstrapping or scaffolding a project.
