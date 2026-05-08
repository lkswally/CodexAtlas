# Decision Council Review

This workflow adapts the useful reasoning pattern from `karpathy/llm-council` into a Codex-Atlas form that stays read-only, local and explicit.

## Goal

Use structured multi-role challenge before Atlas makes a high-risk decision about architecture, external tools, reusable skills or derived-project impact.

## When to use

Use this workflow when any of these are true:

1. the decision is architectural and could shape future projects
2. the decision involves external tools, MCPs or new source layers
3. a new skill or reusable capability is being considered
4. signals conflict across quality gates, routing or policy
5. the user is about to change Atlas or a derived project under uncertainty

## Flow

1. **Frame the decision**
   - define the topic, scope and hard constraints
   - collect only local Atlas evidence first
2. **Architect pass**
   - ask what structure, boundaries or maintenance costs the decision creates
3. **Skeptic pass**
   - ask what assumption could be wrong, what simpler option exists and why this may be premature
4. **Governance pass**
   - check project boundaries, read-only posture, approval needs and config risk
5. **Cost pass**
   - challenge context cost, maintenance burden and provider or tooling sprawl
6. **Product or UX pass**
   - ask whether the decision improves operator clarity or only internal cleverness
7. **Chairman synthesis**
   - record:
     - decision
     - agreement level
     - dissenting views
     - risks
     - evidence
     - open questions
     - recommended next action

## Atlas constraints

- read-only by default
- no external APIs
- no MCP activation
- no global Codex config mutation
- no hidden model switching
- no derived-project mutation

## Expected output shape

```json
{
  "decision": "...",
  "agreement_level": "high|medium|low|undetermined",
  "dissenting_views": ["..."],
  "risks": [{"trigger": "...", "message": "..."}],
  "evidence": ["..."],
  "open_questions": ["..."],
  "recommended_next_action": "..."
}
```

## Relationship to existing Atlas layers

- `claude-vibecoding` remains the main source for evidence discipline and reality-check behavior
- `llm-council` contributes the explicit council pattern: first views, critique, synthesis and dissent visibility
- `quality_gate_report`, `priority_engine`, `skill_evaluator` and `external_tool_policy` remain the main evidence inputs
- this workflow adds structured disagreement handling; it does not replace those systems
