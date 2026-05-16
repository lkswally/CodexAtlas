# Change Proposal Policy

## Purpose

`change_proposal_workflow` gives Atlas a Codex-native, governed way to prepare medium or large changes before implementation starts. It adapts the useful planning discipline from spec-driven systems without importing external runtime, slash commands or toolchain coupling.

## When It Is Required

Use a change proposal when at least one of these is true:

- the change is medium or large in size
- the change has high risk
- the change spans multiple modules or architectural boundaries
- the change alters governance, lifecycle, contracts or quality-gate behavior

## When It Is Not Required

A change proposal is not required for:

- tiny fixes with clear local scope
- documentation-only edits with no governance impact
- low-risk, single-file changes that do not alter contracts or architecture

## Required Artifacts

Atlas expects these artifacts when the workflow is required:

1. `proposal`
2. `specs`
3. `design`
4. `tasks`
5. `verify`
6. `archive`

## Artifact Intent

### Proposal

Must explain:

- what will change
- why it matters
- what problem it resolves
- what is out of scope
- main risks
- expected impact

### Specs

Must capture:

- functional requirements
- non-functional requirements
- scenarios
- acceptance criteria

### Design

Must capture:

- technical approach
- affected files or modules
- tradeoffs
- discarded alternatives

### Tasks

Must capture:

- small tasks
- suggested order
- validation by task
- rollback if it applies

### Verify

Must capture:

- tests
- governance
- quality gate
- minimum evidence
- known false positives

### Archive

Must capture:

- final decision
- commit or closure reference
- learnings
- next steps

## Boundaries

- This workflow is advisory and readiness-only.
- It does not create, apply or auto-update code.
- It does not replace human approval.
- It does not activate external tools or MCPs.
- It does not mutate Codex runtime or project configuration.

## Human Approval

Require explicit human confirmation when the change:

- widens Atlas runtime surface
- changes governance rules materially
- affects model-routing or approval boundaries
- introduces new external dependencies or integration claims

## Decision-Council Trigger

Recommend `decision-council` when:

- tradeoffs are high-risk or unclear
- there are multiple viable architectural paths
- the change may create long-term governance debt

## Relationship To Existing Atlas Layers

- `intent_clarifier_contract` improves clarity of the requested change.
- `quality_gate_report` surfaces whether the artifact chain is missing, partial or ready.
- `atlas_governance_check` verifies that this workflow stays governed and machine-readable.
- `memory/decision_log.md` remains the durable closure path for final outcomes and lessons learned.
