# Policy: external_tool_policy

## Goal

Define when Atlas should rely on local context, internal adapters, official documentation, or external tools without activating new runtime behavior by default.

Atlas must stay:

- explicit
- read-only by default
- auditable
- resistant to context bloat
- resistant to capability duplication

## Decision layers

- `knowledge`
  - documentation lookup, version checks, API references, reference repositories
- `control`
  - repo inspection, issue or PR review, command surface checks, readiness checks
- `execution`
  - code mutation, browser automation, environment control, deployment-capable tooling
- `context`
  - long-lived memory, external workspace memory, cross-session context helpers

## Source priority

When Atlas needs more information, prefer this order:

1. local repo surface
2. internal config, policies, memory and tests
3. curated internal adapters
4. official web documentation or validated upstream repositories
5. external tools or MCPs only if the first four are insufficient

## Default stance

- default deny for external tools
- default read-only for any approved external source
- prefer local evidence over remote evidence
- prefer adapters or CLI over MCP when they solve the same problem with less runtime risk
- do not activate external tooling just because it exists

## When Atlas must NOT use external tools

Do not use external tools when any of these are true:

- the local repo already contains enough evidence
- an internal adapter already covers the need
- the task is solvable with a local file read, audit or policy lookup
- the tool would duplicate an existing Atlas capability
- the tool requires credentials, OAuth, browser persistence or long-running processes for a low-value task
- the tool would require changing global Codex configuration
- real MCP support is not verified in the current environment
- the task is still ambiguous and the human intent is not clear

## CLI vs MCP rule

When both are possible, Atlas should prefer:

1. local read-only built-in commands
2. internal adapters
3. trusted local CLI in read-only mode
4. official web docs
5. MCP only after explicit readiness, approval and a proven gap

Use CLI instead of MCP when:

- the task is repo inspection or metadata review
- the task is issue, PR or branch reading
- the task is a simple docs or API lookup
- the MCP would introduce more context or permissions than the task needs

Use MCP only in future conditions like:

- the value is clearly higher than adapter or CLI alternatives
- the task needs structured remote context that cannot be recovered safely another way
- the MCP path is read-only or explicitly approval-gated
- readiness checks confirm that activation is safe

## Context bloat control

Atlas should avoid context bloat by rule, not by instinct.

- use at most one external source class at a time unless evidence quality requires a second one
- summarize external findings into evidence, never paste large raw dumps
- stop adding sources when the new source does not materially change confidence
- avoid loading community sources before checking official docs or local evidence
- do not keep external-tool suggestions alive across tasks unless the current task still needs them

## Auditability criteria

Any external-source decision should be explainable with:

- why local evidence was not enough
- why the chosen source is lower risk than alternatives
- what the source contributed
- whether the source is read-only
- whether the source requires approval
- what fallback exists if the tool is unavailable

## Risk criteria

Atlas should score external-tool usage mentally against:

- context cost
- runtime risk
- false-positive risk
- hang risk
- credential or config risk
- overlap with existing Atlas capabilities

If those risks are high and the value is only moderate, Atlas should not escalate beyond local tools and adapters.

## Current Atlas interpretation

### Preferred now

- local repo analysis
- policy and config reads
- `docs_search_adapter`
- `repo_improvement_scout`
- official docs lookup when local evidence is insufficient
- local read-only CLI alternatives such as `gh` if they are ever approved and available

### Explicitly blocked now

- real MCP activation
- global Codex config mutation
- hidden runtime switching
- browser automation by default
- persistent external memory systems

## Concrete examples

### Example: OpenAI or Codex product guidance

- first choice: local policy or adapter evidence
- second choice: official OpenAI docs
- do not activate OpenAI Docs MCP while Codex CLI readiness remains unverified

### Example: external repo improvement analysis

- first choice: local clone under `_reference/`
- second choice: official upstream repository pages
- do not add GitHub MCP just to inspect patterns already available through the local reference

### Example: GitHub repository inspection

- first choice: local clone or exported files
- second choice: read-only GitHub CLI if available and approved
- GitHub MCP stays unnecessary unless structured remote operations become a repeated Atlas need

### Example: frontend or browser QA

- first choice: read-only design and landing audits already inside Atlas
- Playwright MCP stays watchlist because it adds browser runtime and hang risk

### Example: memory systems

- first choice: Atlas memory files and decision feedback
- external persistent memory systems stay out until Atlas has a proven cross-project gap that current logs cannot cover

## Proposed integration points

This policy should guide, not automate, these outputs:

- `quality_gate_report`
  - optionally show `external_tool_posture`
  - note which source class was sufficient for the current decision
- `priority_engine`
  - prefer local or adapter-backed actions before external-source actions
- `prompt_builder`
  - state the allowed source order when a task may require external research

## Future readiness rule

If Atlas ever adds executable routing from this policy, it must remain:

- opt-in
- read-only first
- approval-gated for MCP or config changes
- evidence-based
- reversible
