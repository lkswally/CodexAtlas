# Skill: anti-generic-ui-audit

## Purpose

Audit a UI surface for generic patterns, weak direction and evidence gaps without modifying the project.

## When to use

- when a page or UI feels generic and needs a disciplined review
- when Atlas should adapt the reference repo’s anti-generic and visual QA ideas in a safe way
- when a derived project needs design evidence before declaring quality

## When NOT to use

- when the task is to implement the redesign immediately
- when the main issue is backend behavior
- when runtime browser automation is required and not available

## Required inputs

- project path

## Expected outputs

- visual diagnosis
- prioritized problems
- quick wins
- layout and copy recommendations
- evidence-backed score and next action

## Recommended agent

- `evidence_collector`

## Recommended workflow

- `design_intelligence_pipeline`

## Recommended model

- `reviewer`

## Risks

- over-blocking based on weak heuristics
- confusing advisory warnings with deterministic failures
- calling PASS without concrete evidence

## Validations

- output includes status, warnings, evidence and next action
- findings cite real files or observable project signals
- generic-pattern detection stays warning-first unless risk is clear
- the audit remains read-only

## Examples

- "Audit this landing page for anti-generic UI issues."
- "Run a visual QA pass on the derived project without changing files."

## Relationship with the orchestrator

The orchestrator should recommend this skill when the task asks for design audit, visual QA, anti-generic review, hero quality, typography review or evidence-backed UI feedback.
