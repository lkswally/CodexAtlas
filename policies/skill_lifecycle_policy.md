# Skill Lifecycle Policy

Atlas should grow its skill catalog deliberately, not by accumulation.

## Purpose

This policy defines how Atlas evaluates, promotes, limits and retires skills so the factory stays reusable, auditable and understandable.

## Valid states

- `candidate`: idea exists, but Atlas should not treat it as part of the stable capability surface yet
- `experimental`: the skill looks useful enough to evaluate in a governed way, but still needs stronger proof
- `stable`: the skill is reusable, documented, tested and safe enough to be part of the canonical Atlas surface
- `deprecated`: the skill still exists for compatibility or auditability, but Atlas should avoid recommending it by default
- `archived`: the skill is intentionally retired from the active surface and kept only for historical traceability
- `rejected`: the skill should not enter the catalog in its current form

## Transition rules

- `candidate -> experimental` only when reuse is strong, duplication risk is low, and the proposal can be tested and documented without hidden automation
- `experimental -> stable` only when the skill has passing tests, clear documentation, governance compatibility and repeatable value across projects
- `stable -> deprecated` when the skill is superseded, overlaps too much with a better capability, or no longer fits Atlas boundaries
- `deprecated -> archived` when compatibility concerns are gone and the skill should stay only as history
- `candidate -> rejected` when the skill duplicates an existing capability, solves a one-off problem or adds disproportionate external/runtime complexity

## Rejection criteria

- the candidate duplicates an existing Atlas skill or only renames it
- the candidate solves a one-project concern instead of a reusable factory concern
- the candidate depends on hidden automation, auto-install, auto-sync or Claude-only runtime behavior
- the candidate introduces high risk with weak evidence of repeated value
- the candidate requires external services, credentials or MCP/runtime expansion without a strong Atlas-core justification

## Duplication criteria

- same problem as an existing skill with only wording differences
- same trigger conditions and expected outputs as an existing skill
- same capability split across two skills without a boundary that users can explain
- “plus”, “pro”, “advanced” or similar naming used to create overlap instead of a real new scope

## Risk criteria

- low: read-only guidance, review or reporting with no hidden runtime assumptions
- medium: reusable capability with broader scope, stronger governance impact or moderate external coupling
- high: runtime expansion, MCP dependence, installation flow, sync logic, hidden automation or difficult rollback

## External dependency criteria

- low risk: no external dependency or only optional reference material
- medium risk: external docs, optional adapters or advisory-only service awareness
- high risk: new MCP activation, browser/runtime automation, provider-specific install flow, mandatory credentials or external sync

## Human approval

Human approval is required when:

- a skill is proposed for `experimental` or `stable`
- a skill would widen Atlas write scope, runtime surface or external dependency footprint
- a skill introduces new operational expectations for users

## Decision council

Use `decision-council` before promoting or accepting a skill when:

- duplication risk is high but the perceived value is also high
- external dependency risk is high
- the candidate touches MCP, runtime automation, installs, sync or multi-service routing
- the skill would materially change the shape of the Atlas surface

## Watchlist posture

Keep a skill in watchlist-like evaluation, without adding it to the catalog, when:

- the idea is promising but still blocked by external dependency risk
- the capability belongs more to a future adapter or derived project than to Atlas core
- the evidence is not strong enough yet to justify promotion out of `candidate`

## Operating rules

- Atlas may recommend a lifecycle state, but it must not auto-install or auto-promote a skill
- lifecycle decisions must stay explainable through policy, tests and visible evidence
- external inspiration is allowed, but Claude-only runtime patterns must not become Atlas requirements
