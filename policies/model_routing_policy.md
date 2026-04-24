# Policy: model_routing_policy

## Goal

Route Atlas work to a configurable model profile instead of hardcoding a single model as permanent truth.

## Rules

- choose a profile first, not a concrete model ID
- each profile must define preferred and fallback aliases
- the orchestrator may recommend a preferred alias, but it must explain the fallback path
- high-risk or deep-reasoning tasks may justify stronger profiles
- low-risk documentation and triage should bias toward cost control

## Current profiles

- `deep_reasoning`
- `code_execution`
- `reviewer`
- `creative_product`
- `security`
- `cost_saver`

## Out of scope

- automatic model switching during execution
- provider-specific lock-in logic
