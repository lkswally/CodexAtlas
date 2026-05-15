# Atlas Memory Readiness Policy

## Purpose

`atlas_memory_readiness` defines when Atlas can safely rely on local-first memory artifacts and when memory ambitions must stay in watchlist posture.

This layer is advisory and read-only.
It does not inject context automatically, does not modify prompts silently, and does not activate plugins, hooks, background workers, MCP memory servers or cross-machine sync.

## When to use it

Use this readiness layer when Atlas needs to answer:

- whether local memory artifacts are strong enough for cross-session continuity
- whether current memory is only documentary or also operationally useful
- whether a request is trying to communicate watchlist memory as if it were already active
- whether Atlas should keep relying on `decision_log`, `project_state`, `derived_projects` and append-only logs instead of adding new runtime surface

## When not to use it

Do not use this layer to:

- justify hidden prompt reinjection
- treat plugin memory as active when it is only documented
- store or infer secrets
- synchronize memory across machines automatically
- replace explicit briefing, evidence or validation

## Local-first memory posture

Atlas memory is acceptable only when it stays:

- local-first
- explicit
- reviewable
- append-only where appropriate
- separated from derived-project runtime

The current safe baseline is documentary and operational memory inside Atlas itself:

- `memory/decision_log.md`
- `memory/project_state.json`
- `memory/derived_projects.json`
- `memory/routing_log.jsonl`
- `memory/governance_events.jsonl`
- `memory/decision_feedback.jsonl`

## Readiness boundaries

### Safe now

- session summaries written explicitly by humans or Atlas tooling
- cross-session Atlas continuity from local files
- derived-project awareness through `derived_projects.json`
- reviewable feedback weighting based on local append-only logs

### Watchlist only

- plugin or MCP-backed memory
- automatic memory reinjection into prompts
- cross-machine sync
- vector memory, RAG or graph-backed memory
- hidden summarization loops

## Human approval and escalation

Require human approval when a proposal would:

- write new persistent memory outside the current local Atlas files
- sync memory to another machine or service
- attach memory behavior to a runtime, MCP or plugin
- store user/project context that could include sensitive information

Require `decision-council` when a proposal would:

- change Codex runtime behavior
- add background workers, daemons or hooks
- introduce opaque memory ranking or reinjection
- mix memory with multi-provider or plugin orchestration

## Relationship to existing Atlas layers

- `atlas_error_learning_review` captures repeated failures and should remain evidence-first, not pseudo-memory.
- `codex_runtime_compatibility_check` explains what Codex can really do here; memory must not assume more runtime support than that report proves.
- `skill_improvement_review` and `market_research_benchmark` may use memory posture as context, but they must not activate memory behavior.
- `repo_graph_readiness` remains a separate watchlist concern; graph structure is not a substitute for governed memory.

## Prohibited outcomes

Atlas must not communicate any of the following as active unless separately verified:

- automatic memory
- long-term semantic retrieval
- cross-machine memory continuity
- plugin-backed memory
- hidden context injection

## Success criterion

Atlas may call memory `ready` only for local-first reviewable continuity, never for autonomous memory runtime.
