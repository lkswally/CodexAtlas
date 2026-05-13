# Policy: component_inspiration_readiness

## Goal

Define how Atlas should evaluate controlled readiness for component inspiration, UI pattern lookup and design-system reference work without turning Atlas into an external component runtime.

## Scope

This policy is advisory and read-only.

It may:
- report whether 21st Magic or Context7 appear locally usable later
- explain which inspiration profiles are safe to consider
- surface derivative, brand and dependency risks
- recommend fallback paths when no external inspiration source is ready

It must not:
- generate components automatically
- fetch or inject external UI into a derived project
- activate MCPs or external tooling automatically
- replace local design evidence with external pattern browsing
- store or print secrets

## When to use

Use `component_inspiration_readiness` when:
- a derived project may later benefit from component inspiration
- the team wants to compare local design direction against external pattern sources
- there is a need to evaluate landing sections, dashboard modules, form flows or state patterns before approving external inspiration tooling

## When not to use

Do not use it when:
- the project already has enough local design direction and audit evidence
- the request is to implement components immediately
- the task is mostly backend, CLI or non-visual
- the project lacks a `visual_intent_contract` or `brand_profile_schema` for public-facing UI work

## Relationship to existing Atlas layers

- `visual_intent_contract` should define the audience, promise and originality posture before external inspiration is considered.
- `brand_profile_schema` should define differentiation, palette, typography and anti-patterns before external inspiration is considered.
- `creative_pipeline_readiness` is the parent readiness layer for visual-media providers and related visual services.
- `ui_pre_return_audit` remains the final local readiness cross-check for UI claims.
- `external_tool_policy` remains the parent policy for any external source escalation.

## Inspiration vs copy

Atlas must distinguish clearly between:
- inspiration: studying structure, hierarchy or interaction patterns
- reference: observing a system or section type to understand tradeoffs
- derivation: getting too close to a specific layout, motion language or branded component surface
- copying: reusing a recognizable visual system with minimal transformation

Inspiration may be acceptable with clear differentiation notes.
Copying is never acceptable.

## Risks

This layer must warn about:
- over-reliance on one external source for design decisions
- replacing brand direction with pattern shopping
- drifting toward generic SaaS sections because the reference source is stronger than the project brief
- derivative layouts, dashboard blocks or form flows that closely mirror a known product
- declaring a UI ready just because a pattern source exists

## Human approval boundary

Human approval is required before:
- enabling or configuring 21st Magic for real use
- enabling or configuring Context7 for real use
- using any external inspiration source as a project decision input for public-facing UI work
- turning inspiration into implementation tasks

## Decision-council trigger

Recommend `decision-council` when:
- a team wants to depend heavily on external component inspiration
- there is disagreement between local brand direction and external pattern pressure
- the same UI problem can be solved locally without external services
- a future MCP activation would materially expand Atlas runtime surface

## Fallback posture

If 21st Magic or Context7 are not ready, Atlas should fall back to:
- local `visual_intent_contract`
- local `brand_profile_schema`
- local `market_research_benchmark`
- local design-intelligence audits
- local manual evidence and explicit differentiation notes

The absence of an external inspiration source must never block UI readiness by itself.

## Initial stance

- advisory only
- readiness only
- local-first
- no automatic MCP activation
- no component generation
- no external dependency required for PASS
