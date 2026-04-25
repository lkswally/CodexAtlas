# Anti Generic UI Policy

Atlas should actively detect generic UI drift without blocking on weak heuristics.

## Read-only checks

- avoid unexamined default "SaaS teal + generic sans" combinations
- require explicit visual direction, audience, mood and originality
- check typography coherence
- check spacing and layout coherence
- check hero structure for generic patterns
- check CTA clarity
- check responsive baseline
- check contrast and visual accessibility sanity

## Guardrail rules

- textual detection must separate affirmative intent from explicit negation
- report warning before blocker unless the evidence indicates a clear risk
- every strong conclusion must cite concrete evidence
- every helper must return visible JSON or clear markdown
- if a check cannot run, return `status: skipped` with reason

## What Atlas should avoid

- hard blocking on a single fragile textual cue
- claiming visual QA pass without evidence
- confusing taste preference with deterministic failure
