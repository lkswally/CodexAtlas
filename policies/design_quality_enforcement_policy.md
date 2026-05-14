# Design Quality Enforcement Policy

## Purpose

`design_quality_enforcement` is an advisory/read-only Atlas layer that evaluates whether a UI-facing surface is visually strong enough for a serious handoff claim.

It exists to catch cases where a project is functionally coherent but still looks visually weak, generic, amateur, wireframe-like, or too close to an internal tool draft.

## When it applies

Use this policy for UI-facing work such as:

- landing pages
- dashboards
- internal tools with meaningful presentation expectations
- product interfaces that will be reviewed as designed surfaces, not only as functional flows

## When it does not apply

Do not use this policy as a blocking standard for:

- backend-only services
- CLI tools
- infrastructure repos
- documentation-only projects
- early exploratory spikes with no UI handoff claim

## What it reviews

The layer looks for explicit or inferred signs of weak visual quality, including:

- excessive black or heavy border weight
- repeated hard shadows
- wireframe or raw-form look
- excessive card repetition
- weak hierarchy and poor spacing
- weak button hierarchy
- weak or generic color system
- typography without clear intent
- excessive horizontal spread
- unclear success, degraded or error state feedback
- generic dashboard or internal-tool visual defaults
- brutalism used as a low-fidelity excuse instead of an intentional system
- lack of visual personality or brand alignment

## Functional OK vs visually not ready

A surface may be functionally OK and still be visually not ready.

That happens when the interface:

- communicates the flow but not the brand
- solves tasks but looks crude or amateur
- uses repeated panels, buttons and shadows without hierarchy
- resembles a README, raw form, dashboard template or internal admin shell
- lacks clear visual system choices for spacing, type, color and interaction emphasis

In those cases Atlas should recommend redesign or refactor before treating the UI as handoff-ready.

## Enforcement expectations

This layer should:

- request redesign when visual blockers are present
- request simplification when the interface is overloaded or horizontally spread
- request a stronger `brand_profile_schema` when personality, palette or typography are under-specified
- recommend `component_inspiration_readiness` only when local-first direction is already clear and external inspiration is still needed
- recommend screenshot or manual review later when visual proof is needed beyond metadata and text signals

## Relationship to existing Atlas layers

- `visual_intent_contract` explains what the UI should feel like
- `brand_profile_schema` explains how that identity should materialize
- `ui_pre_return_audit` checks whether the UI is ready for a stronger return claim
- `design_intelligence_audit` aggregates the static visual evidence
- `quality_gate_report` surfaces the final posture and should downgrade `ready` to `needs_improvement` when this layer finds blockers

## Human approval boundary

Ask for human clarification when:

- the design is intentionally minimalist, brutalist or technical and the intent is not explicit
- the brand profile is too weak to distinguish taste from deliberate direction
- the surface may require real screenshot review to resolve ambiguity

Escalate to `decision-council` when:

- repeated redesign pressure conflicts with project constraints
- the team wants to imitate an external visual reference too closely
- the right tradeoff between clarity, originality and execution scope is disputed

## Limits

- advisory only
- read-only
- no browser automation
- no screenshot capture
- no UI generation
- no project mutation
- no MCP activation

This layer is a stronger visual gate than the previous advisory checks, but it still does not replace real visual QA or human design review.
