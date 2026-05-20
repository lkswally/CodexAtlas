# Business Idea Simulation Readiness Policy

## Purpose

This layer lets Atlas evaluate business ideas, product hypotheses and startup concepts in advisory mode before people spend time or money.

It does not predict outcomes. It does not guarantee profitability. It does not replace customer discovery, market data or legal review.

## What This Layer Can Do

- clarify the idea in terms of problem, customer and value proposition
- surface weak hypotheses and missing assumptions
- compare optimistic, base and pessimistic scenarios
- explain what data is still missing before talking seriously about profitability
- propose validation experiments that can be run manually first

## What This Layer Must Not Do

- do not claim the idea will be profitable
- do not assign exact probabilities of success
- do not present simulation language as evidence
- do not call external providers, APIs, Docker runtimes or research services
- do not write or modify derived projects automatically

## Readiness States

- `insufficient_data`: the idea is too vague to evaluate beyond basic questions
- `scenario_ready`: the idea has enough structure for hypotheses, scenarios and cautious profitability framing
- `research_required`: the idea is understandable, but missing critical market, pricing, cost or acquisition evidence
- `blocked`: the request asks Atlas to guarantee a prediction or crosses advisory boundaries

## Required Evaluation Dimensions

Atlas should inspect, when available:

- problem clarity
- target customer
- value proposition
- substitutes or competitors
- pricing hypothesis
- delivery or operating costs
- acquisition path
- retention assumptions
- legal, technical and commercial risks
- missing data that blocks stronger conclusions

## Profitability Guardrail

Atlas may only say whether profitability framing is possible at low, medium or high confidence.

Atlas must not say:

- “this will be profitable”
- “this startup will succeed”
- “there is an X% chance of success”

If pricing, costs, acquisition or retention inputs are weak or missing, profitability confidence must stay low.

## Human Approval Boundary

Human approval is required before:

- treating any scenario as a decision basis for investment
- presenting results as market evidence
- using external data collection, scraping or provider-backed simulations

## Validation

Before calling this layer ready:

- policy, config, tool and tests must exist
- the skill must stay read-only
- governance must validate the new files
- quality gate integration must expose the posture without changing unrelated project status rules
