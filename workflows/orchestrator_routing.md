# Workflow: orchestrator_routing

## Purpose

Provide a safe suggestion layer that decides how Atlas should approach a task without executing it automatically.

## Inputs

- task text
- model profile catalog
- MCP profile catalog
- routing policies

## Steps

1. classify task intent
2. estimate risk
3. choose the recommended agent
4. choose the recommended workflow
5. choose the recommended model profile
6. suggest MCPs only if clearly justified
7. decide whether human approval is required

## Output

- routing JSON
- rationale for model profile
- rationale for MCP suggestions
- next safe action

## Safety rules

- suggestion only
- read-only by default
- default deny for MCPs
- destructive or deployment intent always escalates approval
