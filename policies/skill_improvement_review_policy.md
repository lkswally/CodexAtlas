# Skill Improvement Review Policy

Atlas should review its skill catalog deliberately, not mutate it in the background.

## Purpose

This policy defines how Atlas reviews existing skills and external skill ideas so the catalog can improve without turning into hidden automation, duplication or ungoverned sprawl.

## When to run

Run `skill_improvement_review` when:

- Atlas adds or considers a new reusable skill
- the catalog starts to feel overlapping or noisy
- a reference repo suggests new skill candidates
- a skill repeatedly lacks tests, docs or clear boundaries
- Atlas needs a manual hygiene pass before expanding the skill surface

## What it reviews

- current Atlas skills and their metadata surface
- lifecycle posture against `skill_lifecycle_policy`
- test and documentation coverage signals
- overlap or duplication risk between existing skills
- stale or weak skills that need improvement, merge, deprecation or archival review
- external skill candidates only when Atlas already has local evidence or the candidate is passed explicitly as payload

## What it cannot do

- it must not install skills automatically
- it must not modify, merge, archive or rewrite skills automatically
- it must not search the web or external repos automatically
- it must not promote a skill beyond recommendation-only output
- it must not bypass human approval or decision-council for risky catalog changes

## Relationship with lifecycle policy

- `skill_lifecycle_policy.md` remains the canonical lifecycle source of truth
- `skill_improvement_review` uses that policy to recommend whether a skill should stay `stable`, move toward `experimental`, become `deprecated`, be `archived`, or remain `rejected`
- lifecycle review is advisory unless a human explicitly approves the next change

## Catalog hygiene rules

- prefer improving or clarifying an existing skill before adding a near-duplicate
- treat missing tests, missing docs and unclear boundaries as improvement signals
- treat duplicated scope and overlapping triggers as merge or deprecation signals
- treat high external dependency proposals as blocked or watchlist candidates until explicit approval exists

## External candidate posture

External skill ideas may be reviewed only when:

- Atlas already has a local reference or assessment for the candidate, or
- the candidate is passed explicitly as structured payload

External candidates should stay:

- `candidate_review` when the idea looks reusable and low-risk
- `blocked` when evidence is incomplete or the proposal depends on unsafe runtime expansion
- `decision_council_required` when the value is meaningful but the risk is high or the overlap is ambiguous

## Human approval

Human approval is required when:

- Atlas would add a new skill to the catalog
- an existing skill would be merged, deprecated or archived
- a candidate would widen the external dependency surface
- the recommendation materially changes how Atlas routes work

## Decision council

Use `decision-council` before acting when:

- two skills overlap heavily and both have plausible value
- a candidate touches MCP, runtime automation, installs, sync or self-improving behavior
- the recommendation could reshape the Atlas skill surface in a hard-to-reverse way

## Anti-sprawl posture

- catalog growth is slower than catalog review on purpose
- external inspiration is allowed, but Atlas should reject automation-heavy or Claude-only skill patterns
- Atlas should prefer `keep`, `improve` or `merge` over unbounded new-skill creation

## Initial enforcement level

- `skill_improvement_review` is advisory and read-only in this stage
- the output may inform governance and quality-gate reporting
- it does not block the project by itself
