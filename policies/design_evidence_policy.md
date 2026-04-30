# Design Evidence Policy

Atlas should not declare a design or visual review as pass without observable evidence.

## Required output fields

- `status`
- `warnings`
- `evidence`
- `next_action`

## Evidence expectations

- cite actual files, selectors, colors, typography or layout structures when possible
- distinguish between deterministic evidence and advisory interpretation
- if a runtime or screenshot check did not happen, say so explicitly

## PASS rules

- PASS requires enough evidence for the claims being made
- PASS checks must not emit corrective recommendations
- warning is preferred over false PASS when a check is incomplete
- skipped checks must never silently count as success
- skipped checks must expose a reason when the audit could not verify them
- public landing checks must not claim readiness if CTA targets are placeholders, broken or unverifiable

## Recommendation coherence

- `next_action` must derive only from warning or fail checks with concrete evidence
- `quick_wins` must derive from concrete evidence, not generic advice
- audits should expose recommendation provenance so humans can trace each recommendation back to the originating check and evidence
- landing-readiness recommendations must stay tied to verifiable checks such as `above_the_fold_clarity`, `cta_integrity`, `landing_vs_documentation_balance`, `content_density` and `section_rhythm`

## Landing readiness discipline

- a public landing should prove what the system is, who it is for, what problem it solves and what the next action is
- documentation density is a warning signal when it overwhelms narrative, proof and conversion
- Atlas should prefer `needs_improvement` over a false `ready` state when the page reads like a README or PDF export
