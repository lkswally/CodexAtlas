# Frontend Auto Audit Rules Policy

## Purpose

`frontend_auto_audit_rules` is Atlas's safe, local-first substitute for the stronger automatic pre-return checks found in the Vibecoding pipeline.

It does not run browsers, screenshots, or LLM-as-judge flows yet. It checks whether Atlas has enough local evidence and guardrails to support a trustworthy frontend handoff decision.

## What it reviews

The rules review whether Atlas has:

- an intent clarifier contract
- a visual intent contract
- a governed brand artifact posture
- a pre-return UI audit result
- a design-quality result
- responsive baseline evidence
- explicit evidence expectations before PASS

## What it does not do yet

This layer does not:

- take screenshots
- run Playwright
- judge visual fidelity from real rendered output
- replace human review

Those capabilities remain readiness or watchlist layers until separately approved.

## Blocking philosophy

For UI-facing work, Atlas should not call a project strongly ready when:

- the intent clarifier is still weak
- the brand artifact is still only inferred
- the pre-return UI audit is not ready
- design quality is not ready
- evidence expectations are still undefined

## Human approval boundary

Atlas should recommend human clarification or review when:

- local auto-audit says the project is not ready
- screenshot-based evidence is still missing
- design quality and brand direction disagree
- the project is public-facing and Atlas is otherwise close to a ready claim

## Relationship to existing Atlas layers

- `intent_clarifier_contract` protects upstream direction quality
- `visual_intent_contract` protects visual direction quality
- `brand_json_v2_readiness` protects identity structure quality
- `ui_pre_return_audit` protects pre-handoff design readiness
- `design_quality_enforcement` protects visual quality and refinement
- `quality_gate_report` is where the aggregate handoff posture becomes visible

## Advisory-only scope

This first version is advisory and read-only.

It can lower Atlas readiness from `ready` to `needs_improvement` for UI work, but it does so from local checks and explicit evidence gaps only.
