# Workflow: atlas_project_pipeline

## Purpose

Provide a documented phase-based path for Atlas work without introducing automatic orchestration.

## Phases

1. Intent Clarifier
2. Planning
3. Architecture and boundary review
4. Branding and visual direction
5. Development plus QA loop
6. Certification
7. Delivery and handoff

## Phase outputs

- Intent Clarifier: task intent, audience, constraints and ambiguity check
- Planning: scope, risks, validation plan and recommended workflow
- Architecture and boundary review: reusable versus project-local split, interfaces and no-go zones
- Branding and visual direction: anti-generic guidance, audience fit and differentiation notes
- Development plus QA loop: implementation deltas and validation evidence
- Certification: blockers, warnings, score and recommendations
- Delivery and handoff: next actions, open risks and ownership boundaries

## Rules

- each phase must leave explicit outputs
- implementation starts only after scope and constraints are clear
- risky changes require human approval
- outputs must distinguish facts from assumptions
- no phase may silently smuggle Atlas core into a derived project
- no handoff should claim success without evidence
- delivery means handoff, not automatic deployment

## Related policies

- `anti_generic_output_policy`
- `evidence_required_policy`
- `project_boundary_check_policy`
- `template_quality_check_policy`

## Related skills

- `project-bootstrap`
- `repo-audit`
- `product-branding-review`

## Status

Documentary and suggestive. Atlas can route into this pipeline, but it does not execute phases automatically.
