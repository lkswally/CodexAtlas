# Skill: decision-council

## Purpose

Structure difficult Atlas decisions with explicit roles, dissent and chairman synthesis before any high-risk change is executed.

## When to use

- when an architectural decision could affect Atlas boundaries or long-term maintenance
- when Atlas is evaluating external tools, MCPs or source-layer escalation
- when a proposed new skill feels ambiguous or overlaps existing capability
- when recommendations conflict and a single-path answer would hide tradeoffs
- when a high-risk change could affect derived projects before human approval

## When NOT to use

- when the task is a simple doc edit or low-risk clarification
- when local evidence already resolves the decision without meaningful disagreement
- when the request is already an explicit implementation step

## Required inputs

- decision topic
- current constraints
- relevant local evidence if available

## Expected outputs

- decision framing report
- agreement level and dissenting views
- role-specific challenge prompts
- recommended next action

## Recommended agent

- `reality_checker`

## Recommended workflow

- `decision_council_review`

## Recommended model

- `deep_reasoning`

## Risks

- turning a simple decision into unnecessary process
- hiding uncertainty behind a fake consensus
- confusing review structure with implementation approval

## Validations

- the report states whether a full council is actually needed
- risks are tied to explicit triggers or local evidence
- dissenting views remain visible
- the next action stays advisory and non-destructive

## Examples

- "Run a decision council for this architecture choice before touching Atlas."
- "Use the decision council pattern to evaluate whether this external tool belongs in the factory."
- "Frame a high-risk skill creation decision with explicit dissent and chairman synthesis."

## Relationship with the orchestrator

The orchestrator may execute this skill in read-only mode to prepare a structured decision report, but the resulting recommendation is still advisory and must not trigger automatic execution.
