# Atlas Error Learning Policy

## Purpose

`atlas_error_learning_review` captures concrete delivery mistakes Atlas has already seen in real audits so they are not treated as optional hindsight. It is a local, advisory-only review layer that converts those lessons into executable checks.

## What it reviews

- UI handoff mistakes that should block a "ready" claim
- landing-page mistakes that make a surface feel like documentation instead of a product entrypoint
- integration-readiness mistakes where Atlas talks as if something is active when it is only advisory or partially configured

## What it cannot do

- modify derived projects automatically
- open browsers or collect screenshots by itself
- activate MCPs, APIs or external runtimes
- override human approval boundaries
- replace deeper visual QA, manual review or final certification

## UI lessons Atlas must remember

Do not accept a UI as ready when strong evidence shows any of these:

- the hero overflows or collapses the viewport
- the mobile header consumes too much viewport height
- declared fonts do not actually load
- primary CTAs are broken, placeholders or nonfunctional
- tap targets are smaller than 44px
- buttons are nested inside `summary`
- `focus-visible` is missing
- basic SEO or security headers are missing
- there is no visual evidence plan or no evidence trail at all

## Landing lessons Atlas must remember

Do not accept a landing as ready when:

- it reads like a README or documentation shell
- copy is obviously repetitive
- the page does not explain how to start
- the primary CTA is unclear or absent
- onboarding is not practical
- baseline SEO is missing

## Integration lessons Atlas must remember

Do not accept an integration as ready when:

- Atlas describes an advisory layer as if it were active
- the integration depends on external tools that are not configured
- Atlas does not differentiate `ready`, `readiness` and `watchlist`
- the integration has no tests

## Human approval boundary

Ask for human clarification when:

- the available evidence is too weak to tell whether a lesson truly applies
- the issue would require visual judgment beyond local metadata and heuristics
- an external integration could be interpreted as active but the runtime surface is ambiguous

Escalate to `decision-council` when:

- a readiness label materially changes delivery or runtime risk
- Atlas would otherwise present a risky external dependency as usable
- a disputed visual or integration call changes whether a project is considered publishable

## Relationship to other Atlas layers

- `design_intelligence_audit` produces many of the UI and landing signals
- `ui_pre_return_audit` and `frontend_auto_audit_rules` provide readiness evidence for UI surfaces
- `quality_gate_report` exposes `error_learning_posture` and can downgrade a UI-facing project from `ready` to `needs_improvement`
- `mcp_readiness_check`, `creative_pipeline_readiness`, `component_inspiration_readiness` and `playwright_visual_qa_readiness` provide integration/readiness signals

## Limits

- advisory only
- read-only only
- local evidence first
- no auto-remediation
- no screenshot automation
- no runtime activation
