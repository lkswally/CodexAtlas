# Skill: market-research-benchmark

## Purpose

Compare Atlas against explicit reference repos so roadmap decisions stay evidence-based, bounded and free of hidden runtime assumptions.

## When to use

- when Atlas needs to benchmark itself against `claude-vibecoding`
- when a radar repo suggests a pattern that may or may not fit Atlas
- when a roadmap step depends on reference fit instead of intuition
- when Atlas needs a structured comparison before adding new capability

## When NOT to use

- when the task is a simple implementation already scoped locally
- when the user wants automatic scraping, cloning or install behavior
- when the benchmark result is being treated as implementation approval

## Required inputs

- benchmark topic
- explicit reference payload if available

## Expected outputs

- benchmark comparison report
- prioritized adaptation opportunities
- blocked references with rationale
- recommended next safe moves

## Recommended agent

- `reality_checker`

## Recommended workflow

- `market_research_benchmark`

## Recommended model

- `deep_reasoning`

## Risks

- turning documented repo blurbs into stronger evidence than they deserve
- importing install/runtime assumptions into Atlas core
- expanding scope from benchmark into implementation without approval

## Validations

- Atlas capability coverage is tied to real local files
- documented-only references are clearly marked
- high-risk runtime patterns stay watchlist or discard by default
- next actions remain advisory and bounded
