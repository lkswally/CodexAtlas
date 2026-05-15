# Codex Runtime Compatibility Policy

## Purpose

`codex_runtime_compatibility_check` verifies which Codex capabilities are actually available on the current machine so Atlas can distinguish a healthy local runtime from a merely assumed one.

## What it can verify

- whether the Codex CLI is callable
- whether a Codex version can be read locally
- whether `codex mcp list` is functional
- which MCP server names are visible in the current Codex config
- whether a runtime model is visible in local or project config
- whether Atlas should consider the runtime safe for advisory use

## What it cannot do

- change the active model
- modify local or global Codex configuration
- activate MCPs
- install runtimes, adapters or dependencies
- reveal secrets or raw credentials

## Compatibility expectations

Atlas should treat a Codex runtime as safe for normal Atlas use when:

- the Codex CLI is callable
- the MCP CLI path is functional enough to inspect configured servers
- any runtime model visibility remains advisory and manual
- known limitations are explicit

Atlas should treat the runtime as degraded when:

- the CLI is missing or broken
- MCP inspection is unavailable
- configuration visibility is partial
- Atlas would have to guess whether a runtime surface is active

## Human approval boundary

Ask for human intervention when:

- the runtime is present but key capability probes fail
- MCP configuration exists but functional readiness is unclear
- Atlas sees runtime ambiguity that could be mistaken for a working integration

Escalate to `decision-council` when:

- a runtime limitation materially changes delivery risk
- a provider or local model fallback would expand the runtime surface
- Atlas is pressured to treat a partial runtime as production-ready

## Relationship to other Atlas layers

- `mcp_readiness_check` remains the dedicated MCP-readiness layer
- `model_router_core` remains advisory/manual for actual model selection
- `quality_gate_report` exposes `codex_runtime_posture`
- this layer only reports compatibility and limitations; it never changes runtime state

## Limits

- advisory only
- read-only only
- no auto-switch
- no MCP activation
- no secret disclosure
