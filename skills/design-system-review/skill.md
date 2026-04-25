# Skill: design-system-review

## Purpose

Review typography, spacing, hierarchy and structural consistency in a project surface without changing code.

## When to use

- when a derived project has UI but no clear design-system discipline
- when Atlas needs a lighter Codex-native equivalent of the reference repo’s UI-designer review
- when typography, spacing or layout coherence needs a structured assessment

## When NOT to use

- when the task is a repo audit unrelated to UI quality
- when the request is to implement a full redesign immediately
- when the project has no inspectable UI files

## Required inputs

- project_path

## Expected outputs

- design-system review
- typography and spacing findings
- consistency risks
- recommendations for next review or implementation step

## Recommended agent

- `ui_designer`

## Recommended workflow

- `design_intelligence_pipeline`

## Recommended model

- `creative_product`

## Risks

- overfitting aesthetic opinion without repository evidence
- assuming a design system exists when the repo only has a simple page
- mixing strategic branding feedback with structural UI review

## Validations

- typography and spacing findings cite evidence
- the review distinguishes pass, warning and skipped states
- recommendations remain advisory
- the review stays read-only

## Examples

- "Review the design system quality of this static site."
- "Check typography, spacing and hierarchy before redesigning."

## Relationship with the orchestrator

The orchestrator should recommend this skill when the task asks for design-system review, typography review, spacing review, UI consistency or structural design QA.
