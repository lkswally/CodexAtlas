# Intent Clarifier Contract Policy

## Purpose

The intent clarifier contract makes early project direction explicit before Atlas treats UI, landing, or workflow-facing work as visually ready.

It exists to prevent vague briefs from passing through branding, layout and QA layers with only inferred intent.

## When it is required

The contract is required when:

- the project type is `frontend_app`, `fullstack`, or `internal_tool`
- the brief or project surface looks like a landing page, dashboard, product UI, workflow UI, or public-facing web surface
- Atlas is about to make stronger claims about visual direction, branding, readiness, or handoff quality

## When it may be omitted

The contract may be skipped when:

- the project is clearly backend-only, infra-only, or CLI-only
- Atlas is only doing a structural repo audit with no visual or UX claim
- the project is not presenting a user-facing surface yet

## Minimum required answers

For strong UI-facing readiness claims, Atlas should have explicit answers for:

- project type
- domain context
- target audience
- primary goal
- style direction
- originality level

The following remain recommended even in the advisory phase:

- reference direction
- success criteria
- constraints

## Weak-answer patterns

Atlas should not treat the contract as strong if the brief relies on generic answers such as:

- "make it modern"
- "make it look good"
- "professional"
- "clean SaaS"
- "nice dashboard"
- "something useful"

## Human approval boundary

Atlas should recommend human clarification when:

- project type is still unknown
- target audience is missing
- primary goal is generic or missing
- a UI-facing project lacks explicit style direction or originality level
- the task is visually public-facing but the contract is mostly inferred rather than explicit

## Relationship to existing Atlas layers

- `project_intent_analyzer` remains the broad project and risk analyzer.
- `visual_intent_contract` remains the visual-direction contract.
- `intent_clarifier_contract` sits one level earlier and checks whether enough directional input exists to trust later design guidance.
- `quality_gate_report` should surface the contract posture and downgrade a UI-ready claim when the contract is still weak.

## Advisory-only scope

This first version is advisory and read-only:

- it does not generate design output
- it does not edit project files
- it does not call external services
- it does not auto-resolve ambiguity

It exists to make missing intent explicit before Atlas moves deeper into branding, layout, and final UI quality claims.
