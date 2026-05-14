# Policy: playwright_visual_qa_readiness

## Goal

Define how Atlas should evaluate readiness for future screenshot or browser-based visual QA without turning Playwright into an implicit runtime dependency.

## Scope

This policy is advisory and readiness-only.

It may:
- report whether Playwright appears locally available
- report whether browser binaries seem present
- explain which visual-QA profiles remain blocked or watchlisted
- recommend manual next steps before any future visual QA run

It must not:
- install Playwright
- install browsers
- open a browser
- capture screenshots
- activate MCPs
- touch derived projects

## When to use

Use `playwright_visual_qa_readiness` when:
- a derived project may later need stronger visual proof than static design audits
- the team wants to understand whether the environment is technically ready for screenshot-based QA
- there is uncertainty about whether browser-driven QA is even safe to attempt later

## When not to use

Do not use it when:
- the task is backend, CLI or otherwise non-visual
- local design direction is still underspecified
- `visual_intent_contract`, `brand_profile_schema` or `ui_pre_return_audit` are still missing for a public-facing UI
- the request is to run automation immediately

## Evidence potential

If Playwright later becomes approved and runnable, it may help produce:
- screenshot evidence
- responsive layout comparisons
- regression snapshots
- UI-state verification for loading, empty and error surfaces

This layer only reports readiness for that future step.

## Risks

This layer must warn about:
- false positives caused by environment differences, fonts or rendering drift
- false negatives caused by flaky layout timing or missing browser state
- hung or orphaned browser processes
- over-trusting screenshots as a replacement for intent, brand or accessibility review
- declaring a UI ready only because a browser tool exists

## Human approval boundary

Human approval is required before:
- installing Playwright
- installing browser binaries
- running any browser automation
- collecting screenshots from a real derived project

## Decision-council trigger

Recommend `decision-council` when:
- screenshot QA is being treated as mandatory for Atlas core
- the team wants to widen Atlas runtime surface around browser automation
- there is disagreement about whether visual QA is worth the operational risk

## Relationship to Atlas design chain

- `visual_intent_contract` should exist before stronger visual claims are tested.
- `brand_profile_schema` should exist before screenshot-based brand alignment claims are trusted.
- `ui_pre_return_audit` remains the local readiness gate before any stronger “UI ready” statement.
- `component_inspiration_readiness` and `creative_pipeline_readiness` stay separate: inspiration and generation readiness are not proof of visual QA readiness.
- `quality_gate_report` may surface this readiness posture, but it does not make Playwright mandatory.

## Initial stance

- advisory only
- readiness only
- no browser automation
- no screenshot capture
- no MCP activation
- no derived-project mutation
