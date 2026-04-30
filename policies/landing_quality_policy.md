# Landing Quality Policy

## Purpose

This policy adapts the `claude-vibecoding` patterns behind:
- Visual Direction Checkpoint
- Anti-Generic Guardrails
- evidence-collector
- reality-checker
- certification readiness before handoff

For Atlas, the policy stays read-only and deterministic. It does not use hooks, MCPs or browser automation.

## What A Public Landing Must Prove

Before Atlas calls a landing publicly ready, the page should show evidence for:
- what the system is
- who it is for
- what problem it solves
- what the visitor should do next

If that evidence is weak, implicit or contradictory, the landing should stay in `needs_improvement`.

## Quality Gates

Atlas design intelligence should check:
- `above_the_fold_clarity`
- `cta_integrity`
- `landing_vs_documentation_balance`
- `content_density`
- `section_rhythm`
- `public_readiness`

These checks complement the existing visual direction, typography, contrast and anti-generic checks.

## Guardrails

- Do not treat a documentation-heavy page as ready just because the HTML and CSS are valid.
- Do not emit corrective recommendations from checks already in `pass`.
- Do not emit recommendations without explicit evidence.
- If a check cannot be verified from the available static surface, return `skipped` with a reason.
- Prefer warnings over blockers unless the landing is missing a next step entirely or the CTA path is clearly broken.

## README-Like Risk Signals

Atlas should warn when a landing leans too far toward static documentation, for example:
- long text blocks with little pacing
- too many lists or inline command blocks
- onboarding sections dominating the page
- weak or missing visual proof

This is not a ban on documentation. It is a signal that the page may read like a README or PDF instead of a guided public landing.

## Public Readiness

`public_readiness` should mean:
- `ready`: clear value proposition, working CTA path, no major landing warnings
- `needs_improvement`: usable, but still too dense, too generic or too documentary
- `not_ready`: the page lacks a viable next step or has a broken public conversion path
