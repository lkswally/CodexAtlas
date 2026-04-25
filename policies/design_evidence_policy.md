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
- warning is preferred over false PASS when a check is incomplete
- skipped checks must never silently count as success
