# Brand Profile Schema Policy

Atlas should not treat branding as an unstructured taste exercise.

Once a project has a visual intent contract, Atlas should be able to express the resulting brand direction in a structured profile that stays reviewable, reusable and auditable.

## When the brand profile is required

- required for landing pages, public sites, frontend apps and UI-heavy fullstack work
- recommended for internal tools when the task includes a visible interface, dashboard, hero or CTA
- optional for backend-only or non-visual CLI/service work

## Relationship with the visual intent contract

- the visual intent contract defines the minimum intent
- the brand profile translates that intent into identity rules
- the brand profile should not contradict audience, originality level, hero direction or CTA intent already declared in the visual intent contract

## Required profile areas

- brand name and audience
- personality traits
- mood vector
- color strategy
- typography strategy
- layout and motion principles
- visual density and originality level
- anti-patterns to avoid
- differentiation notes
- accessibility notes
- evidence expectations before PASS

## Policy goals

- make visual identity explicit before stronger design claims
- reduce generic SaaS-template drift
- reduce derivative "fake {brand}" outcomes
- keep brand decisions tied to rationale, not to vibes alone

## Quality criteria

- the profile should explain why the identity fits the audience and promise
- the mood vector should be complete and internally coherent
- color strategy should define contrast intent, not just colors
- typography strategy should justify hierarchy and contrast
- differentiation notes should explain how inspiration stays inspiration instead of copy
- evidence expectations should say what Atlas must validate before calling the brand direction passable

## Anti-patterns

- default teal/cyan plus generic sans with no rationale
- "premium" or "minimal" as empty labels with no supporting system
- inspiration references with no differentiation notes
- copied brand signatures, recognizable layouts or logo-adjacent mimicry
- PASS claims without contrast, accessibility or evidence expectations

## Inspiration versus copying

- inspiration references may guide tokens, spacing mood, motion curves or typographic posture
- Atlas should not copy logos, signatures, proprietary imagery, exact layouts or recognizable brand combinations
- if the result reads like "fake Linear", "fake Apple" or "fake Stripe", the profile is too derivative

## Minimum evidence before PASS

- explicit rationale for palette and typography
- anti-patterns are stated
- accessibility notes are present
- evidence expectations mention audit, review or validation before PASS

## Atlas behavior

- the schema is advisory and read-only in this stage
- missing or weak brand profile data should produce warnings, not hidden automation
- the profile should inform `brand_agent`, `product-branding-review`, `design_intelligence_audit` and `quality_gate_report`
- if the profile is inferred from the visual intent contract instead of explicitly declared, Atlas should treat it as incomplete

## Relation to claude-vibecoding

This adapts the reference repo's `brand.json schema v2`, mood-vector discipline, anti-generic blocklists and anti-derivative review into a Codex-native schema. It does not import `.claude`, Claude hooks, Engram assumptions or creative runtime agents.

## Escalation

Escalate to explicit human review when:

- the project is public-facing and the brand profile is still weak
- inspiration references create derivative risk
- accessibility or contrast rationale is missing but branding decisions would be treated as final
