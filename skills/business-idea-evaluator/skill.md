# Skill: business-idea-evaluator

## Purpose

Evaluate a business idea, startup concept or product hypothesis in Atlas-native advisory mode.

This skill is for structured thinking, not prediction. It should surface hypotheses, scenarios, risks, missing data and validation experiments before anyone treats an idea as investable.

## When to use

- when someone shares a business idea and wants structured evaluation
- when the goal is to test assumptions before building
- when pricing, costs, channels or retention are still uncertain
- when Atlas should separate evidence from opinion

## When NOT to use

- when the user wants guaranteed profitability or exact success probabilities
- when the task requires real market scraping, provider-backed simulation or Docker runtimes
- when the request is purely to implement product code

## Required inputs

- the idea in plain language
- target customer if known
- problem being solved if known
- pricing, costs, channels or retention assumptions if available

## Expected outputs

- signal: promising, incomplete or weak
- readiness state for idea evaluation
- missing inputs and key risks
- optimistic, base and pessimistic scenarios
- validation experiments and recommended next step

## Recommended agent

- `planner` for structured evaluation
- `researcher` only when external research is explicitly requested and separately approved

## Recommended workflow

- `atlas_project_pipeline`

## Recommended model

- `deep_reasoning`

## Risks

- confusing simulation language with evidence
- overconfidence on pricing or market size
- hiding missing data behind polished strategy language

## Validations

- never claim a guaranteed prediction
- state missing data explicitly
- keep profitability confidence low when unit economics are weak
- propose experiments before recommending heavy build-out

## Examples

- "Evaluate this startup idea with hypotheses, risks and experiments."
- "Help me think through whether this SaaS idea looks promising or incomplete."
- "Analyze this business concept without pretending to predict the future."

## Relationship with the orchestrator

The orchestrator should recommend this skill when the task is idea evaluation, startup hypothesis review, pricing-risk review or pre-MVP validation planning.
