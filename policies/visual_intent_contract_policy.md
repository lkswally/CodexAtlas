# Visual Intent Contract Policy

Atlas should not treat visual quality as a taste-only discussion.

Before Atlas claims that a landing, public page or design direction is coherent enough, it should be able to describe a minimum visual intent contract in a structured and reviewable way.

## When the contract is required

- required for landing pages, public sites, frontend apps and UI-heavy fullstack work
- recommended for internal tools when the task includes a visible interface, dashboard, page, hero or CTA
- optional for backend-only or non-visual CLI/service work

## Required contract fields

- audience
- project_type
- problem / promise
- mood / vibe
- originality level
- hero direction
- primary CTA intent
- visual density
- motion intensity
- typography intent
- color strategy
- anti-patterns to avoid
- evidence expectations before PASS

## Policy goals

- reduce generic README/PDF-like outputs
- reduce default SaaS-template drift
- keep brand and UX guidance explicit before implementation
- keep PASS claims tied to evidence, not to confidence language

## Atlas behavior

- the contract is advisory and read-only in this stage
- missing contract fields should produce guidance, not hidden automation
- the contract should inform `project_intent_analyzer`, `visual-direction-checkpoint`, `brand_agent`, `design_intelligence_audit` and `quality_gate_report`
- lack of contract clarity may justify `needs_input`, but should not silently fabricate direction

## Quality criteria

- the problem or promise should describe what the page must communicate, not just that it should "look good"
- originality must be explicit: `conservative`, `balanced`, `distinctive` or `experimental`
- hero direction should communicate posture or structure, not a placeholder heading only
- CTA intent should describe the expected user action
- typography and color strategy should help avoid default template outputs
- evidence expectations should say what must be validated before Atlas treats the design as passable

## Minimum evidence before PASS

- explicit visual direction or mood language
- explicit hero promise and primary CTA intent
- stated anti-patterns
- traceable audit, validation or certification expectations before PASS claims

## Warning signals

- no explicit audience
- no clear problem or promise
- no mood or vibe
- no originality target
- hero speaks like documentation instead of a product promise
- CTA exists but has no clear user intent
- no stated anti-patterns to avoid
- readiness or design PASS is claimed without evidence expectations

## Anti-patterns

- README/PDF-like landing structure
- default SaaS teal plus generic sans with no rationale
- repeated identical cards with no visual rhythm
- hero text that explains too much but persuades nothing
- "just make it look good" or "you decide everything" with no contract

## Relation to claude-vibecoding

This policy adapts the reference repo's Intent Clarifier, Visual Direction Checkpoint, anti-generic guardrails and proof-before-pass discipline into a Codex-native read-only contract. It does not import `.claude`, Claude hooks, Engram or Playwright runtime assumptions.

## Escalation

Escalate to explicit human review when:

- the design direction is high-stakes or public-facing and the contract is still weak
- branding decisions would lock visual identity without agreement
- multiple contract fields are missing but implementation is still requested
