# Market Research Benchmark Policy

Atlas may benchmark itself against explicit references, but that benchmark must stay governed, local-first and read-only.

## Purpose

This policy defines how Atlas compares its current capability surface against reference repos, curated skill catalogs or documented external patterns without turning research into hidden scraping, auto-installation or automatic catalog mutation.

## When to run

Run `market_research_benchmark` when:

- Atlas needs a structured comparison against `claude-vibecoding`
- a roadmap decision depends on whether a gap is already covered or still missing
- a radar repo suggests a reusable pattern that might fit Atlas
- the skill catalog needs external inspiration, but Atlas should avoid copying runtime-heavy or Claude-only behavior
- a proposed improvement feels useful, but its fit, risk or governance posture is still unclear

## What it reviews

- the current Atlas capability surface from local files
- the local reference clone under `_reference/claude-vibecoding` when present
- documented radar repos only when they are explicitly listed in the governed benchmark rules or passed as payload
- fit, risk, benefit and next-step posture for each reference pattern

## What it cannot do

- it must not scrape the web automatically
- it must not clone repositories automatically
- it must not install skills, plugins or tooling
- it must not modify Atlas or derived projects
- it must not activate MCPs, browser automation or external runtimes
- it must not treat a benchmark recommendation as implementation approval

## Source posture

- local Atlas evidence is the first source of truth
- `_reference/claude-vibecoding` is the primary external benchmark when present locally
- radar repos remain documented-only unless Atlas has local evidence or the user passes explicit payload
- lack of local evidence should reduce confidence instead of being filled with assumptions

## Relationship with existing Atlas layers

- `repo_improvement_scout` remains the focused read-only comparison helper for `_reference/claude-vibecoding`
- `skill_lifecycle_policy` governs how any resulting skill idea should be promoted or rejected
- `skill_improvement_review` governs catalog hygiene after a benchmark suggests candidate work
- `decision-council` should be used before acting on high-risk recommendations or runtime-expanding patterns

## Anti-sprawl posture

- prefer adapting one high-fit, low-risk pattern over importing broad external systems
- reject runtime-heavy, sync-heavy or self-modifying systems by default
- treat install tooling, sync tooling and benchmark evolution frameworks as inspiration unless Atlas has a specific repeated need

## Human approval

Human approval is required when:

- a benchmark would lead to adding a new skill, workflow or policy
- the recommendation widens external dependency surface
- the recommendation implies MCP activation, browser automation, automatic sync or auto-improvement
- the benchmark result would reshape Atlas governance or routing materially

## Decision council

Use `decision-council` before acting when:

- two or more references suggest conflicting patterns
- a reference repo mixes useful discipline with risky runtime assumptions
- a recommendation would add automation-heavy behavior to Atlas
- the benchmark result would affect multiple Atlas layers at once

## Initial enforcement level

- advisory and read-only only
- benchmark output may appear in reporting, but must not trigger implementation by itself
- no benchmark result replaces direct local evidence
