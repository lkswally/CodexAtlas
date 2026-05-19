# Repo Graph Readiness Policy

## Purpose

`repo_graph_readiness` defines when Atlas should recommend a local repository graph as a manual optimization layer before deep file-by-file exploration.

This layer is advisory and read-only.
It does not install CodeGraph, does not initialize `.codegraph/`, does not activate MCP, does not modify Codex runtime, and does not assume any graph tool is already safe or approved.

## When to use it

Use this readiness layer when Atlas needs to answer:

- whether a repository is large or structurally complex enough that graph-first exploration may save time and tokens
- whether a task is dominated by navigation, impact analysis, route tracing or cross-module understanding
- whether current work is likely to cause expensive exploratory tool-call loops
- whether manual graph initialization could be justified later under explicit approval

## When not to use it

Do not use this layer to:

- justify installing CodeGraph or any other repo-graph runtime automatically
- communicate MCP-backed graph capabilities as active when they are only theoretical
- replace normal local exploration for small repos or bounded tasks
- claim that a graph is required when the repository is still simple enough for direct file reading

## Atlas posture

Atlas treats repo graphs as optional optimization infrastructure, not as part of the core factory runtime.

The current safe boundary is:

- detect whether a repo graph would likely help
- detect whether `.codegraph/` already exists
- detect whether a local `codegraph` binary appears present without executing it
- describe risks, blockers and manual steps

Atlas must not:

- create `.codegraph/`
- start a CodeGraph MCP server
- run `npx @colbymchenry/codegraph`
- install SQLite-backed tooling
- add watchers, daemons or background sync

## What makes repo-graph readiness more likely

Graph-first exploration is more justified when one or more of the following are true:

- the repo is medium or large
- there are many source files or multiple languages
- the task is a refactor, architectural trace, impact analysis or route analysis
- the project has multiple modules, packages or app surfaces
- framework routes or cross-module call chains matter to the task

## What keeps it blocked or low-value

Graph-first exploration is not justified when:

- the repo is small
- the task is a small fix, documentation update or bounded local edit
- the graph would add maintenance or install surface without clear token savings
- privacy, security or approval constraints forbid external runtimes or local databases in the current phase

## Watchlist boundaries

The following stay in watchlist posture unless separately approved:

- MCP server activation
- file watchers and auto-sync
- global installs
- local database initialization
- route or impact analysis communicated as active when the graph is not actually initialized

## Relationship to existing Atlas layers

- `model_cost_control_readiness` may use this posture as a hint that a deep task is graph-shaped, but it must not trigger runtime changes.
- `priority_engine` may use repo-graph posture to prioritize “understand structure first” over brute-force exploration.
- `skill_registry_index_first_readiness` solves skill discovery, not repository structure.
- `codex_runtime_compatibility_check` explains current Codex runtime limits; repo-graph readiness must not imply runtime support beyond that evidence.
- `mcp_readiness_check` stays separate; repo-graph readiness is not permission to activate any MCP.

## Human approval and escalation

Require explicit human approval before any future step that would:

- install CodeGraph
- initialize `.codegraph/`
- add a local SQLite graph database
- enable an MCP server
- enable a watcher, hook or background sync process

Require `decision-council` before any future step that would:

- change Atlas runtime behavior around repo exploration
- make graph use the default path
- add hidden routing or auto-selection logic that depends on external graph infrastructure

## Success criterion

Atlas may call repo-graph readiness `ready` only as a recommendation to consider manual initialization later.
It must never present repo-graph tooling as active unless separately verified and approved.
