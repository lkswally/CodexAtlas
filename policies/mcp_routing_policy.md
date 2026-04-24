# Policy: mcp_routing_policy

## Goal

Keep MCP suggestions controlled, explicit and denied by default.

## Rules

- default deny: no MCP is suggested unless the task clearly benefits from one
- suggestions are advisory only and never imply automatic connection
- prefer read-only modes
- require human approval before any real MCP activation
- do not suggest MCPs when the task is solvable with built-in repo context
- only one experimental read-only MCP may be enabled at a time in Atlas metadata

## Current MCP profile catalog

- `docs_search`
- `filesystem`
- `engram`
- `github`
- `web_search`
- `database_schema`
- `docs`
- `analytics`

## Current experimental decision

- `docs_search` is the only experimental read-only MCP enabled right now
- it remains advisory and approval-gated
- all other MCP profiles stay disabled for experimental activation
