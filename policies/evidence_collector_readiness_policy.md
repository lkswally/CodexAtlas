# Evidence Collector Readiness Policy

## Purpose

`evidence_collector_readiness` defines the minimum evidence Atlas should expect before making a strong PASS or ready claim.

This layer is advisory and read-only.
It does not collect screenshots automatically, does not run browsers, does not execute external tools, and does not modify derived projects.

## Why this exists

Atlas already has intent, brand, design-quality, pre-return and error-learning guardrails.
The remaining gap is not only "what looks weak", but "what proof exists".

Atlas should not communicate a strong PASS when the evidence trail is still thin, missing or ambiguous.

## Task-type evidence expectations

### Frontend / UI / Landing

Expected evidence:

- desktop screenshot
- mobile screenshot
- responsive check
- tap target check
- font loading check
- link or CTA check
- SEO basics
- accessibility basics
- build or test result
- known false positives

Without this evidence, Atlas may still report `pass with caution`, but not a strong PASS.

### Backend / API

Expected evidence:

- tests
- endpoint contract
- error handling proof
- migration or schema check when applicable
- relevant logs
- explicit no-secrets posture

### Research / benchmark

Expected evidence:

- sources
- query or consultation date
- selection criteria
- limitations
- explicit distinction between inference and data

### High-risk decision

Expected evidence:

- decision-council output
- alternatives compared
- tradeoffs
- risks
- human approval

### Skill / governance change

Expected evidence:

- policy
- config
- behavior or execution contract
- tests
- governance check
- lifecycle state

## Approval and escalation

Ask for human clarification when:

- the task type is unclear
- the evidence list is incomplete but the claim language is strong
- local heuristics can only infer, not verify, a critical proof point

Escalate to `decision-council` when:

- a high-risk decision lacks explicit alternatives and tradeoffs
- the evidence boundary changes whether Atlas may call something ready
- a proposal would blur the line between readiness and activation

## Relationship to other Atlas layers

- `ui_pre_return_audit` checks pre-handoff UI quality signals.
- `design_quality_enforcement` blocks visually weak UI.
- `atlas_error_learning_review` captures repeated mistakes Atlas has already seen.
- `playwright_visual_qa_readiness` stays in readiness posture for future screenshot collection.
- `quality_gate_report` may use this layer to downgrade strong-ready claims when evidence is still incomplete.

## Limits

- no automatic screenshot collection
- no browser automation
- no external APIs
- no mutation of derived projects
- no replacement for real certification or human review

## Readiness rule

Atlas may only call a task strongly ready when:

- required evidence is explicit
- blocking evidence gaps are empty
- the remaining gaps are advisory only

Otherwise Atlas should stay at `evidence_partial`, `evidence_missing` or `pass with caution`.
