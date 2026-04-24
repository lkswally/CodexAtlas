# Policy: project_derivative_policy

## Goal

Protect the boundary between Atlas as a parent factory and any derived project such as REYESOFT.

## Rules

- Atlas owns reusable structures, contracts, workflows and validation rules
- derived projects own runtime, business logic, product copy and operational configuration
- project-specific adapters must live under `adapters/` or in the derived repo, not inside Atlas core folders
- do not pull derived-project constraints into Atlas unless they generalize cleanly
- if a compatibility layer is needed, label it as legacy or adapter explicitly

## Current application

- `adapters/reyesoft/` documents the REYESOFT relationship
- `00_SISTEMA/_meta/atlas/` is a legacy compatibility mirror, not the primary Atlas home
