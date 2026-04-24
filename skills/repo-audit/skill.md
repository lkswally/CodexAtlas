# Skill: repo-audit

## Purpose

Audit a repository or derived project for structure, drift, governance gaps and architectural clarity before proposing bigger changes.

## When to use

- when evaluating a repo before refactoring
- when checking Atlas vs derived-project boundaries
- when validating whether docs match the real workspace

## When NOT to use

- when the request is pure implementation with a clear scoped change
- when a single file explanation is enough
- when the user needs a branding review instead of an architectural audit

## Required inputs

- workspace root
- current constraints
- known boundary assumptions
- target of the audit if the repo is a derived project

## Expected outputs

- diagnosis
- findings
- risk summary
- recommended next actions

## Recommended agent

- `reality_checker`
- `reviewer` for higher-risk follow-up review

## Recommended workflow

- `audit_project`

## Recommended model

- `deep_reasoning`

## Risks

- mistaking documentation for reality
- drifting into implementation too soon
- over-claiming certainty without evidence

## Validations

- findings cite real paths or commands
- unknowns remain explicit
- no destructive action is taken
- governance and registry stay consistent

## Examples

- "Audit this repo before we separate core and adapters."
- "Review a derived project for Atlas contamination and governance drift."

## Relationship with the orchestrator

The orchestrator should recommend this skill when the request contains audit, review, drift, workspace inspection, boundary checking or repo analysis signals.
