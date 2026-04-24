# Policy: mcp_routing_policy

## Goal

Keep MCP suggestions controlled, explicit and denied by default.

## Rules

- default deny: no MCP is suggested unless the task clearly benefits from one
- suggestions are advisory only and never imply automatic connection
- prefer read-only modes
- require human approval before any real MCP activation
- do not suggest MCPs when the task is solvable with built-in repo context

## Current MCP profile catalog

- `filesystem`
- `github`
- `web_search`
- `database_schema`
- `docs`
- `analytics`
