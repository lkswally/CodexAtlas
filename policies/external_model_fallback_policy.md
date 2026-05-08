# Policy: external_model_fallback_policy

## Goal

Define how Atlas should evaluate external model fallbacks, including NVIDIA Build models, without confusing them with Codex Desktop model routing.

Codex Desktop routing remains manual and advisory. External fallback models are a separate, opt-in research path for moments when the user wants another provider because Claude or another tool is unavailable.

## Current stance

- Atlas does not auto-route to external providers.
- Atlas does not store API keys.
- Atlas does not call NVIDIA Build or any other model endpoint by default.
- Atlas may document candidates and provide a manual benchmark plan.
- Any future adapter must be read-only first and explicitly approved.

## Source priority

1. Codex Desktop model router for work inside Codex.
2. Local Atlas policies and validation tools.
3. Manual external model benchmark when the user asks for fallback strategy.
4. Experimental adapter only after benchmark evidence proves value.

## When to consider an external fallback

Consider a fallback only when:

- the active tool/model is unavailable, rate-limited or too expensive
- the task is separable from Atlas core execution
- the user explicitly wants provider comparison or fallback planning
- the candidate model has a documented endpoint or deployment path
- the work can be validated with local Atlas checks after completion

Do not consider a fallback when:

- the task is normal Codex repo work
- Codex Desktop already has a suitable model selected manually
- the external provider requires unapproved credentials or config mutation
- the model would perform write actions without Atlas validation
- the benefit is only novelty or hype

## Benchmark-before-integration rule

No external fallback becomes an Atlas profile or adapter until it passes a manual benchmark against at least these tasks:

- planning: produce a scoped, constraint-aware project plan
- coding: make a small, testable stdlib-only change
- audit: identify real findings without inventing blockers
- design/branding: critique a landing with evidence and no generic advice
- safety: refuse unsupported assumptions and ask for missing data

Benchmark outputs must include:

- model name
- date tested
- prompt
- result summary
- correctness notes
- false positives
- context handling
- latency or usability notes
- recommended Atlas posture

## Integration levels

| Level | Meaning | Approved now |
| --- | --- | --- |
| Documentation only | Atlas records model candidates and benchmark criteria | Yes |
| Manual benchmark | User runs prompts outside Atlas and records results | Yes |
| Fallback profile | Atlas can recommend the external model as a manual option | Not yet |
| Experimental adapter | Atlas calls an endpoint in read-only mode | Not yet |
| Runtime routing | Atlas chooses and calls models automatically | No |

## Relation to model_router

`model_router` handles Codex Desktop recommendations only.

External fallback recommendations must not alter:

- `config/model_routing_rules.json`
- Codex Desktop selection
- `~/.codex/config.toml`
- `.codex/config.toml`

If a future external fallback is approved, it should live in a separate config surface so Codex model routing stays truthful.

## NVIDIA Build posture

NVIDIA Build/NIM candidates are useful as a manual fallback radar because some catalog entries expose free development endpoints. They are not safe to use automatically because they still require account/API key handling, terms review, model-by-model stability checks and benchmark evidence.

Recommended current posture:

- document candidates
- benchmark manually
- do not integrate runtime
- do not store keys
- do not make Atlas depend on NVIDIA availability

