# Codex-Atlas V3 Architecture

Codex-Atlas V3 is a governed, evidence-first Codex workspace for creating,
auditing, and certifying derived projects. V3 is intentionally not an
autonomous runtime. It is an RC1 internal baseline made of local tools,
contracts, policies, docs, tests, and opt-in workflows.

## Vision

Atlas keeps project work explicit and auditable. A task should move from an
objective to a planned action, then to implementation, evidence collection,
verification, health review, and failure learning when needed.

```text
Objective
     |
Planner
     |
Executor
     |
Evidence Pipeline
     |
Verifier
     |
Health Report
     |
Failure Registry
```

## Main Modules

| Area | Files | Role |
|---|---|---|
| Governance | `tools/atlas_governance_check.py`, `tools/atlas_verify.py`, `commands/atomic_command_registry.json` | Validates repo structure, command surfaces, policies, configs, skills, and docs. |
| Dispatcher | `tools/atlas_dispatcher.py`, `tools/atlas_run.py` | Exposes governed commands and reports. |
| Evidence Pipeline | `tools/evidence_runner.py`, `tools/evidence_contract_validator.py`, `tools/evidence_session.py`, `tools/evidence_bundle_summary.py`, `tools/evidence_quality_report.py` | Captures, validates, summarizes, and reports evidence bundles. |
| Health Report | Local health tool and `config/workflow_observations.json` | Reports local health, workflow observations, freshness, and operational risks. |
| Failure Registry | `tools/failure_registry.py` | Validates and persists failure records, with advisory similarity lookup. |
| Model Routing | `tools/model_routing_policy.py`, `tools/model_router.py`, `tools/model_router_core.py`, `config/model_routing_rules.json` | Recommends model classes in advisory mode. |
| Agent Loop | `docs/agent_loop_v1_design.md`, `docs/agent_loop_manual_checklist.md` | Defines manual planning, execution, verification, and learning boundaries. |
| Docs and Memory | `docs/`, `memory/` | Keep release evidence, decisions, summaries, and state file-backed. |

## Dependencies

- Python standard library for most tools.
- `pytest` for tests.
- Playwright only for opt-in real browser smoke tests.
- GitHub Actions only for CI workflows, not for required local health report generation.

No V3 core path requires Engram, Paperclip, n8n, Chrome MCP, live GitHub API
access, or an autonomous runtime.

## Complete Flow

1. A human or Codex session defines the objective.
2. Planner uses local docs, policies, and model routing advice.
3. Executor performs scoped changes.
4. Evidence Pipeline captures or validates evidence where applicable.
5. Verifier runs tests, governance, and `atlas_verify`.
6. Health report reviews core and workflow observation state.
7. Failure Registry records validated failures when a run ends in WARN, FAIL, or BLOCKED.
8. Release reports or project certification documents the result.

## Mandatory in V3

- Governance checks before release claims.
- Evidence contracts for evidence-based claims.
- Local tests for changed behavior.
- `git diff --check` before commit/push.
- Human review for release decisions.

## Advisory in V3

- Model Routing recommendations.
- Failure similarity lookup.
- n8n readiness and workflow generation.
- Chrome MCP readiness.
- GitHub connector readiness.
- Scheduled automation readiness.
- Visual QA readiness and quality gate synthesis.

Advisory surfaces can inform decisions, but they do not execute autonomous
actions or replace verification.

## Opt-in in V3

- Evidence Browser Smoke workflow.
- Evidence Quality Report workflow when run manually.
- Real browser Playwright smoke tests.
- Workflow observations cache refresh.

## In Scope for V3

- RC1-ready local governance and verification.
- Evidence Pipeline V1.
- Atlas health report V1 with workflow observation freshness.
- Failure Registry V1.
- Model Routing V1 advisory mode.
- Manual Agent Loop design and checklist.
- CI workflows on `windows-2025`.
- Release Candidate and final release documentation.

## Deferred to V4

- Autonomous Runtime.
- Runtime Planner and Runtime Verifier.
- Runtime Failure Learning.
- Automatic Model Routing.
- Live Workflow Observations.
- Runtime Memory.
- Multi-model orchestration.
- Optional Paperclip integration.
- Optional Engram integration.
- Runtime health interface.

V4 is not designed in this release. These are only future objective names.
