# Market Research Benchmark

This workflow lets Atlas compare its current capability surface against explicit references without turning research into scraping or hidden automation.

## Goal

Benchmark Atlas against `_reference/claude-vibecoding` and curated radar repos so roadmap decisions stay evidence-based, bounded and Codex-native.

## When to use

1. when Atlas needs to know whether a benchmark pattern is already covered
2. when a roadmap step depends on external reference fit, not just intuition
3. when a skill or policy idea needs comparison against a known reference repo
4. when Atlas should review radar repos without installing or copying them

## Flow

1. **Frame the benchmark**
   - define the topic
   - keep the scope explicit
   - prefer local Atlas evidence first
2. **Review current Atlas coverage**
   - identify which capabilities are already adapted, partial or missing
3. **Review the primary reference**
   - use `_reference/claude-vibecoding` when present locally
   - do not widen scope beyond explicit evidence
4. **Review radar references**
   - treat documented repos as advisory input only
   - avoid automatic installs, sync or runtime activation
5. **Classify each reference**
   - `adapt_now`
   - `design_later`
   - `watchlist`
   - `discard`
6. **Record the next safe move**
   - recommend one or two focused follow-ups
   - escalate to `decision-council` if a recommendation widens runtime or governance surface

## Constraints

- read-only
- no web scraping
- no cloning
- no installs
- no MCP activation
- no derived-project mutation

## Expected output

```json
{
  "reviewed_references": [],
  "prioritized_opportunities": [],
  "blocked_references": [],
  "recommended_next_actions": []
}
```
