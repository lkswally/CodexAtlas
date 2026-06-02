# Policy: department_registry

## Goal

Define a governed, advisory-first registry of Atlas operating departments so Atlas can organize existing capabilities by area without creating free-floating agents, hidden automation or duplicated skill surfaces.

## What This Layer Can Do

- map existing Atlas capabilities into explicit operational departments
- explain when each department should activate
- define required inputs, expected outputs and handoff boundaries
- recommend departments for a project or task in manual, governed mode
- keep watchlist departments visible without pretending they are active runtime teams

## What This Layer Must Not Do

- do not create autonomous multi-agent loops
- do not duplicate existing skills or readiness layers
- do not activate MCPs, providers or workflows automatically
- do not turn departments into hidden runtime routing logic
- do not let any department bypass quality, evidence or human approval boundaries

## Required Departments

Atlas should keep explicit registry coverage for:

- Product
- Web/UX
- Automation/n8n
- Engineering
- Growth/Marketing
- Research
- QA/Governance

Operations/Finance may exist only in watchlist posture unless Atlas later adds explicit approved scope for it.

## Activation Model

- department activation is advisory only
- activation mode is manual and governed
- recommended departments may guide a handoff or a next-step plan
- recommendation does not imply execution permission

## Department Contract

Every department entry must define:

- purpose
- activate_when
- required_inputs
- expected_outputs
- capabilities used
- must_not_do
- required_checks
- handoff_to
- project_type_fit
- signal_triggers

## Human Approval Boundary

This layer must not remove existing approval boundaries.

If an underlying capability is approval-bound, the department that uses it remains approval-bound.

Examples:

- Automation/n8n does not make workflow execution allowed.
- Web/UX does not make browser automation or MCP activation allowed.
- Operations/Finance watchlist does not allow provider connection or auto-fallback.

## Relationship To Existing Atlas Layers

- `quality_gate_report` may expose a department posture summary.
- `atlas_governance_check` remains the source of truth for registry file presence and structural validity.
- readiness layers remain the real capability contracts; the registry only organizes them.
- departments are a governance surface, not a second orchestrator.

## Initial Stance

- advisory only
- no automatic activation
- no new autonomous agents
- no duplication of skill logic
- no product-specific runtime behavior
