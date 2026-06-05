# Policy: post_execution_learning_review

## Purpose

`post_execution_learning_review` gives Atlas an explicit, advisory-only way to
inspect what a finished block taught the factory without turning that learning
into automatic self-modification.

The layer should help Atlas notice repeated mistakes, missing tests, risky
patterns and connector/readiness gaps while preserving a human approval boundary.

## What it can do

- analyze a closed block summary, changed files, validations and blockers
- propose candidate learnings for documentation, policies, tests or readiness
- surface repeated patterns that should not remain trapped inside chat history
- recommend whether the learning should be treated as accepted, deferred or
  rejected pending human review

## What it cannot do

- modify skills automatically
- create tests automatically
- create policies automatically
- create readiness layers automatically
- rewrite prompts or mutate Atlas behavior in the background
- activate MCPs, providers, automations or gateways

## Required posture

- `auto_mutation_allowed` must remain `false`
- the output is advisory and reviewable
- dangerous or self-modifying proposals stay blocked
- new policy or test work should be proposed as a separate follow-up block

## State guidance

- `no_learning_needed`: the block closed cleanly with no durable lesson
- `learning_candidate`: a repeated pattern or human decision suggests a reusable lesson
- `policy_candidate`: risky behavior reveals a governance gap
- `test_candidate`: a bug was fixed without sufficient test coverage
- `readiness_candidate`: a new external/runtime surface should be framed as readiness first
- `blocked_auto_mutation`: the proposal drifts into self-modifying behavior
- `needs_human_review`: the lesson is plausible but ambiguous

## Human approval

Human approval is required when the output proposes:

- a new policy
- a new readiness layer
- a new reusable test expectation
- any change to Atlas routing, mutation boundaries or runtime surface

## Relationship to existing Atlas layers

- `decision_feedback` records decisions, but does not synthesize them into block-level learning
- `atlas_error_learning_review` focuses on known UI and integration delivery mistakes
- `skill_improvement_review` governs catalog hygiene, not post-block learning across the factory
- `quality_gate_report` may expose this posture, but must not auto-act on it

## Success criterion

Atlas should become better at noticing repeated mistakes and missing guardrails
without pretending it may rewrite itself automatically.
