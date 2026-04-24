# Policy: safe_execution_policy

## Goal

Keep Atlas execution controlled, inspectable and reversible.

## Rules

- prefer read-only inspection before mutation
- prefer stdlib and local files before external dependencies
- do not execute destructive actions by default
- document impact, risk and rollback for write operations
- block hidden automation and implicit side effects

## Out of scope in this stage

- MCP execution
- automatic hooks
- auto-deploy
- auto-healing
