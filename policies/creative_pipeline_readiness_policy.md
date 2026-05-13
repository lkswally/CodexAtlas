# Policy: creative_pipeline_readiness

## Goal

Define how Atlas should evaluate creative-pipeline readiness for branding, image, logo, video and component-inspiration work without turning Atlas into an automatic media runtime.

## Scope

This policy is advisory and read-only.

It may:
- report which creative services look locally available
- explain which profiles are safe to consider later
- surface legal, derivative and approval risks
- recommend explicit manual next steps

It must not:
- generate images, logos or videos
- call external providers to produce assets
- store or print secrets
- modify global Codex config
- activate MCPs automatically
- replace human review for brand-sensitive work

## When to use

Use `creative_pipeline_readiness` when:
- a derived project needs future logo, image or video capability planning
- Atlas needs to evaluate whether visual-brand review could benefit from external providers later
- component inspiration or visual QA is being considered as a future capability
- the team needs a safe readiness report before approving any visual-media integration

## When not to use

Do not use it when:
- the current need can be answered by local design audits alone
- the request is to generate assets immediately
- the project lacks a `visual_intent_contract` or `brand_profile_schema` for public-facing creative work
- the goal is only broad aesthetic exploration without a project outcome

## Relationship to existing Atlas layers

- `visual_intent_contract` defines audience, promise, originality and anti-patterns first.
- `brand_profile_schema` turns that intent into explicit identity, palette, typography and differentiation signals.
- `ui_pre_return_audit` remains the final readiness cross-check for UI claims.
- `market_research_benchmark` helps decide whether an external creative pattern is worth adapting at all.
- `external_tool_policy` remains the parent rule for any external tool, CLI or MCP escalation.
- `mcp_readiness_check` remains the canonical readiness source for real MCP configuration; this policy only consumes that signal.

## Core distinction

Atlas must distinguish clearly between:
- inspiration: collecting patterns, references or component ideas
- generation: asking a provider to create assets
- review: assessing whether brand or visual direction looks coherent
- copying: replicating an existing brand, logo, layout or motion language too closely

Inspiration and review may become safe earlier.
Generation stays approval-bound.
Copying is never acceptable.

## Legal and brand risks

Creative readiness must warn about:
- derivative logo directions that resemble known brands too closely
- prompts that name existing brands as the main source rather than as constrained references
- unclear ownership or storage plan for generated assets
- missing accessibility rationale for color, contrast or typography in visual-brand work
- visual inspiration workflows that could be mistaken for copy-paste implementation

If those risks are present, the correct output is `watchlist` or `blocked`, not optimistic readiness.

## Human approval boundary

Human approval is required before:
- enabling any logo, image or video generation profile
- activating `21st Magic`, `Context7` or future visual MCPs
- using provider-backed visual-brand review for a derived project
- moving from readiness to actual asset generation
- storing any generated asset outside the approved derived project path

## Decision-council trigger

Recommend `decision-council` when:
- a requested creative profile has high legal, derivative or brand risk
- the same need could be solved by local design review without external media tooling
- the tool posture conflicts with project governance or external-tool policy
- a future MCP or browser-driven visual QA path would expand Atlas runtime surface significantly

## Evidence expectations

Before stronger PASS claims, Atlas should be able to point to:
- whether the required env vars are locally present
- whether related MCP servers are configured
- whether the target project already has visual intent and brand profile evidence
- what manual approval step is still required
- which profiles remain blocked or watchlist and why

## Initial posture

- advisory only
- readiness only
- default deny for real generation
- default watchlist for browser-driven visual QA
- no secret storage in repo
- no implicit upgrade from readiness to execution

## Reference fit

This adapts the useful discipline from `claude-vibecoding`: visual direction first, explicit brand thinking, and strong caution around creative tooling.

Atlas intentionally does not copy:
- Claude-only runtime assumptions
- automatic visual pipelines
- hidden credential flows
- browser automation as a default prerequisite
