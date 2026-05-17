# Skill Registry Index-First Policy

## Purpose

`skill_registry_index_first_readiness` evaluates whether Atlas can safely use an index-first skill registry pattern without replacing the current skill system or importing external runtime behavior.

The goal is simple:

- keep `skill.md` or `SKILL.md` as the instructional source of truth
- keep `skill.json` and `behavior.json` as governed machine-readable metadata
- expose a lightweight registry entry so the orchestrator can pass paths instead of bloated summaries

## What This Layer Does

- verifies that each skill directory has the minimum governed files
- checks that skill paths are resolvable
- checks that descriptions are strong enough for index-first discovery
- checks for duplicate names and malformed frontmatter
- produces a minimal registry index suitable for Atlas-native routing and future path-first loading

## What This Layer Does Not Do

- it does not replace the current orchestrator
- it does not auto-load full `skill.md` bodies into runtime prompts
- it does not modify skills automatically
- it does not install or sync external skills
- it does not change global Codex behavior

## Required Local Contract

Each Atlas skill should expose:

- `skill.md` or `SKILL.md`
- `skill.json`
- `behavior.json`

Optional frontmatter in the markdown file is allowed, but not required.

If frontmatter is present:

- it must be parseable
- it may provide `name`, `description` and `scope`
- multiline `description: >` is valid and should remain supported

## Description Expectations

An index-first registry only works if descriptions are strong enough to route by metadata first.

A description is acceptable when it:

- clearly states the capability
- distinguishes the skill from generic audit or review language
- stays human-readable and path-stable

## Safety Boundary

Atlas should treat this layer as advisory and readiness-only until a future change explicitly updates orchestrator behavior.

That means:

- registry generation may be evaluated
- path-first loading may be assessed
- runtime adoption still requires explicit human approval and separate implementation review

## Decision Rule

- `ready`: Atlas can safely generate a minimal registry index from the current skill surface.
- `partial`: Atlas is close, but some descriptions or metadata still weaken the registry.
- `blocked`: broken paths, duplicates or invalid frontmatter make index-first usage unsafe for now.
