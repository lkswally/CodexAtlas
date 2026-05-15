# Model Cost Control Policy

## Purpose

`model_cost_control_readiness` is an Atlas advisory layer that evaluates whether a task should stay on a mini, medium, or strong model tier, and whether Atlas should reduce context before recommending a more expensive path.

This policy exists to improve cost-awareness without changing the active Codex Desktop model automatically.

## What it can do

- recommend a model tier, not a specific runtime change
- suggest context reduction before escalation
- suggest splitting a task into smaller steps
- signal when a stronger model is justified
- signal when a cheaper pass is enough
- request human confirmation before a costly or ambiguous recommendation

## What it cannot do

- auto-switch the active model
- mutate Codex configuration
- call external APIs
- install providers, adapters, or local runtimes
- enable Ruflo, hooks, daemons, or background workers

## Decision priorities

Atlas should prefer:

1. narrower scope before a stronger model
2. summarization before context bloat
3. staged execution before one giant prompt
4. manual confirmation before expensive or ambiguous escalations

## Typical strong-tier cases

- architecture or boundary decisions
- high-risk security or certification work
- multi-file delicate changes
- complex audits with contradictory evidence
- tasks that need deep reasoning and cannot be narrowed first

## Typical medium-tier cases

- focused implementation
- standard repo audits
- controlled design or documentation work
- bounded planning after the scope is already clear

## Typical mini-tier cases

- lightweight documentation
- triage and summarization
- low-risk informational follow-ups
- short classification or routing checks

## Cost-saving expectations

Before Atlas recommends a strong tier, it should ask whether the task can be improved by:

- trimming background context
- summarizing prior evidence
- splitting planning from execution
- separating audit from implementation

## Human approval boundary

Require user confirmation when:

- Atlas wants a strong tier but the task is still ambiguous
- the context looks large enough to waste tokens
- the task mixes planning, research, and execution in one step
- cost priority versus quality priority is unclear

Escalate to `decision-council` when:

- model choice changes the risk profile materially
- the user wants local or external fallback providers with nontrivial surface area
- cost pressure pushes Atlas toward a weaker model on a high-risk task

## Relationship to other Atlas layers

- `model_router_core` recommends the model profile and actual named model
- `model_cost_control_readiness` explains whether that recommendation is cost-disciplined
- `quality_gate_report` should expose the posture without blocking runtime
- `prompt_builder` should surface the guidance as manual/advisory instructions

## Limits

- advisory only
- readiness only
- no provider activation
- no auto-routing across external runtimes
- no changes to `can_auto_switch: false`
- no changes to `model_switch_mode: manual_required`
