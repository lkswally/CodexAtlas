# CodexAtlas

**A governance and evidence toolkit for safer, more inspectable Codex-assisted software work.**

[![Atlas CI](https://github.com/lkswally/CodexAtlas/actions/workflows/atlas-ci.yml/badge.svg)](https://github.com/lkswally/CodexAtlas/actions/workflows/atlas-ci.yml)

CodexAtlas turns recurring engineering controls—scope checks, risk classification, bounded execution, evidence capture, and repository verification—into versioned Python tools and explicit contracts. It is a local project factory and control plane for Codex workflows, not an autonomous software-development runtime.

## Overview

LLM-assisted engineering often leaves critical behavior implicit: the model decides what to inspect, which risks matter, when evidence is sufficient, and whether an external integration is actually available. CodexAtlas makes those boundaries inspectable.

Today it provides:

- deterministic governance, repository audit, bootstrap, and certification tools;
- advisory task, risk, skill, and model-class routing;
- bounded execution adapters for selected local operations;
- evidence contracts and quality reports;
- explicit approval boundaries for state-changing or high-risk work;
- versioned policies, skills, workflow specifications, and regression tests.

CodexAtlas deliberately does **not** claim automatic model switching, a dynamic multi-agent runtime, autonomous learning, universal command interception, or live MCP connectivity.

## Why CodexAtlas

The project explores a practical agentic-systems question:

> How much of an AI-assisted engineering workflow can be made deterministic, testable, and reviewable without hiding control inside a larger autonomous runtime?

The design separates four concerns:

1. **Policy** — what is allowed, blocked, advisory, or approval-gated.
2. **Routing** — which skill, model class, or verification path is recommended.
3. **Execution** — which bounded tool or host adapter may perform work.
4. **Evidence** — what supports a result and what remains unverified.

## Architecture

~~~mermaid
flowchart TD
    U[User or Codex host] --> I[Task intake]
    I --> G[Governance and safety checks]
    G --> O[Deterministic orchestrator]
    O --> R[Skill and model-class recommendations]
    R --> B{Execution boundary}
    B -->|bounded local command| T[Audit / bootstrap / certification tools]
    B -->|host-controlled| C[Codex execution adapter]
    T --> E[Evidence and verification]
    C --> E
    E --> Q[Quality report and result]

    M[Model routing policy] -. advisory .-> R
    P[MCP profiles] -. configured / approval-gated .-> B
    H[Human approval] -. selected risk .-> B
~~~

Solid arrows represent implemented control flow. Dashed arrows represent advisory policy or host-dependent integration.

Primary executable surfaces include:

- tools/atlas_governance_check.py
- tools/atlas_verify.py
- tools/atlas_dispatcher.py
- tools/atlas_orchestrator.py
- tools/atlas_project_bootstrap.py
- tools/atlas_codex_executor.py

## How a task flows through CodexAtlas

1. **Intake** identifies the requested operation and target repository.
2. **Governance** checks canonical structure, project boundaries, and policy constraints.
3. **Risk classification** identifies destructive commands, external side effects, and approval requirements.
4. **Routing** recommends a skill, model class, and verification posture.
5. **Execution** remains bounded: deterministic tools run directly; Codex execution remains host-controlled.
6. **Evidence** records commands, exit status, artifacts, or structured findings.
7. **Verification** produces a report that distinguishes supported results from blockers and unknowns.

Not every workflow specification is an executable state machine. Several documents describe operating procedures that a host or engineer must apply.

## Governance & Safety

CodexAtlas includes deterministic checks for canonical structure, project boundaries, dangerous-command patterns, approval-sensitive operations, skill contracts, audit requirements, and evidence bundles.

The Dangerous Command Policy is a classifier used by CodexAtlas entrypoints. It is not a global shell hook and does not intercept every command executed outside those entrypoints.

Human approval remains necessary for production deployment, destructive filesystem changes, sensitive external writes, and other policy-classified high-risk work. The host applies the final approval and sandbox boundary.

## Orchestration

tools/atlas_orchestrator.py performs deterministic intake, risk assessment, and recommendation. It can invoke bounded skill handlers and prepare execution plans.

tools/intelligent_orchestrator.py is a **dry-run/advisory simulator**. It does not launch agents, switch models, call MCP servers, or mutate repositories.

The repository contains role specifications under agents/. These are contracts and reusable role descriptions, not independently verified executable agents.

tools/atlas_codex_executor.py provides an adapter for codex exec. Its behavior depends on the installed Codex CLI, host sandbox, and approval capabilities. Adapter readiness is not proof that a delegated task executed end to end.

## Skills & Workflows

The current repository contains:

- **10 governed skill directories**
- **11 workflow specifications**
- **55 policy files**
- **12 role specification files**
- **4 GitHub Actions workflow files**

These categories are intentionally separate. Skills define bounded capabilities; workflows describe procedures; policies constrain decisions; role specifications describe operating roles; evaluators are Python tools; execution adapters connect selected operations to a host.

Canonical skills: `project-bootstrap`, `repo-audit`, `decision-council`, `market-research-benchmark`, `product-branding-review`, `visual-direction-checkpoint`, `anti-generic-ui-audit`, `design-system-review`, `business-idea-evaluator`, and `conversion-copywriter`.

Workflow specifications: `atlas_project_pipeline`, `create_project`, `audit_project`, `audit_repo`, `certify_project`, `certify_output`, `change_proposal_workflow`, `decision_council_review`, `design_intelligence_pipeline`, `market_research_benchmark`, and `orchestrator_routing`.

The dispatcher exposes bounded commands including `audit-repo`, `certify-project`, and `surface-audit`.

A workflow document or role specification is not automatically an active runtime component.

## Evidence & Verification

Evidence is a first-class design concern in CodexAtlas. Implemented paths can capture commands and exit codes, output excerpts, file metadata and hashes, structured blockers, test results, and browser artifacts when an opt-in Playwright environment is provisioned.

A PASS means the checks invoked for that path succeeded. It does **not** establish correctness outside the tested scope, live availability of an external service, semantic correctness of every artifact, general autonomy, or successful browser execution when Browser Smoke was skipped.

The tracked visual-fidelity PNG files are lightweight test fixtures, not runtime screenshots. Real browser evidence requires the separate opt-in smoke workflow or an equivalent provisioned local run.

## Model Routing

| Layer | Current behavior |
|---|---|
| Task classification | Deterministic and implemented |
| Model-class recommendation | Implemented in advisory mode |
| Provider resolution | Not implemented for model providers |
| Host application | Controlled by the Codex host/operator |
| Runtime model switching | Not implemented |
| Fallback | Recommendation only; no automatic switch |

Decision Benchmark V1 contains 45 versioned cases. Its tests pass against the current routing rules. This is evidence for that bounded dataset, not a claim of general routing accuracy.

## MCP & Tool Integration

CodexAtlas includes an MCP manager, permission profiles, readiness checks, and a local read-only documentation-search adapter.

Current boundaries:

- the internal docs_search adapter is implemented locally;
- external MCP connectivity is not required for core governance;
- the audited host did not have the documentation MCP configured;
- configured profiles do not imply a successful handshake;
- selected MCP operations require explicit approval;
- a simulated fallback must not be read as live external execution.

## Failure Handling

The Failure Registry can record, validate, read, and query known failures. This supports recurrence analysis, but it is not autonomous learning.

CodexAtlas provides bounded failure classification, blocker and warning states, regression tests, component-specific retries where implemented, and documented rollback expectations. It does not provide a general self-healing loop, automatic rollback, or persistent behavioral adaptation.

## Observability

Selected components emit structured JSON/JSONL events for governance, routing, MCP evaluation, and decision feedback. These records support local diagnosis and reports.

Observability is component-scoped. Runtime logs may contain local paths or project metadata and should be treated as local operational data rather than portfolio content.

## Current Verified Status

Verified locally on Windows with Python 3.14.5 and pytest 9.0.3 for this branch on 2026-09-23. The CI baseline uses Python 3.13 and `requirements-dev.txt`:

| Area | Status | Evidence |
|---|---|---|
| Full Python suite | **PASS** | 830 passed, 1 skipped |
| Skipped test | **Expected opt-in** | Real-browser smoke requires provisioned Chromium |
| Governance | **LIVE / verified** | Current governance command and tests |
| Repository audit | **LIVE / verified** | atlas_verify.py and audit path |
| Project bootstrap | **LIVE / bounded** | Temporary-project execution in tests |
| Certification | **LIVE / bounded** | Read-only certification tests |
| Evidence Pipeline | **PARTIAL** | Non-browser paths verified; real browser not revalidated locally |
| Failure Registry | **LIVE / isolated** | Registry operations verified; no autonomous learning claim |
| Decision Benchmark V1 | **PASS in scope** | 45-case deterministic dataset |
| Intelligent Orchestrator | **DRY_RUN** | Advisory simulator only |
| Model routing | **ADVISORY** | Recommendation implemented; no runtime switching |
| External MCP | **PARTIAL / host-dependent** | Manager and contracts exist; live external server not verified |
| Baseline main CI | **PASS at `ca535ac`** | GitHub Actions run `31176337424`; focused suites |
| Autonomous model switching | **NOT IMPLEMENTED** | Host/operator remains responsible |

The only repository tag is v3.0.0-rc1, which points to an earlier commit than current main. No GitHub Release exists for that tag. Current main should not be described as a published RC1 release.

## Autonomy Boundaries

CodexAtlas **decides deterministically**:

- repository and policy validation results;
- known dangerous-command classifications;
- routing recommendations;
- readiness and verification findings.

CodexAtlas **recommends** skills, model classes, verification depth, and next steps.

CodexAtlas **executes** local audit, bootstrap, certification, reporting, and validation tools. The Codex execution adapter can invoke `codex exec` when explicitly called, but this audit did not reproduce an end-to-end delegated-agent run.

The **host or operator controls** the active model and provider, approval prompts, sandbox permissions, external MCP availability, production side effects, deployment, and publication.

CodexAtlas deliberately does not automate production deployment, dependency installation, provider selection, model switching, Git history rewriting, or unrestricted cross-repository mutation.

## Testing & CI

Requirements:

- Python 3.13 (the CI baseline; other versions are not claimed as supported)
- Git
- Codex CLI only for host-execution paths
- Chromium/Playwright only for the opt-in real-browser smoke test

Create an isolated environment and run the suite:

~~~powershell
git clone https://github.com/lkswally/CodexAtlas.git
cd CodexAtlas

python -m venv .venv
.venv\Scripts\python -m pip install --upgrade pip
.venv\Scripts\python -m pip install -r requirements-dev.txt
.venv\Scripts\python -m pytest tests/
~~~

Core verification:

~~~powershell
.venv\Scripts\python tools\atlas_verify.py
.venv\Scripts\python tools\atlas_governance_check.py
.venv\Scripts\python tools\atlas_dispatcher.py audit-repo
.venv\Scripts\python tools\mcp_readiness_check.py
~~~

Atlas CI runs on pushes and pull requests to main. It executes governance, readiness, focused governance tests, critical architecture tests, and git diff --check. The full global suite and browser smoke are separate manual workflows.

## Repository Structure

~~~text
agents/       role specifications
commands/     command contracts and registries
config/       routing, policy, benchmark, and readiness data
docs/         architecture studies and bounded technical reports
memory/       local-first state formats and operational records
policies/     human-readable governance constraints
skills/       governed capability packages
templates/    bootstrap templates
tests/        deterministic regression and integration tests
tools/        executable audit, routing, evidence, and governance tools
validators/   schema and contract validation assets
workflows/    procedure and transition specifications
~~~

## Getting Started

For a first read-only inspection:

~~~powershell
python tools\atlas_verify.py
python tools\atlas_governance_check.py
python tools\atlas_dispatcher.py audit-repo
~~~

To inspect a consumer repository without modifying it:

~~~powershell
python tools\atlas_governance_check.py --project <project_root>
python tools\atlas_dispatcher.py --project <project_root> audit-repo
python tools\atlas_dispatcher.py --project <project_root> certify-project
~~~

Project bootstrap changes the filesystem. Review its contract and provide an explicit output directory before invoking it.

## Roadmap

Near-term work is intentionally conservative:

- remove remaining named-consumer coupling from reusable core paths;
- separate local runtime records from publishable repository fixtures;
- improve reproducible real-browser evidence;
- keep external integrations opt-in and capability-checked;
- expand benchmarks only when new failure modes are observed.

## Limitations

- Some reusable core paths still contain legacy coupling to a named downstream project. This requires a separate architecture change.
- External MCP availability is host-specific and was not live in the audited environment.
- Browser E2E is opt-in and was skipped in the reproduced local suite.
- Model routing is advisory; runtime switching is not implemented.
- The execution adapter does not establish a verified multi-agent runtime.
- Failure recording does not equal autonomous learning.
- The repository has **no license file**. Reuse rights remain undefined until the owner selects a license.
- Historical Git commits may retain local paths and downstream-project names after current-tree cleanup.

## License

**License decision required.** No license has been selected.

Common options:

- **MIT** — short, permissive, minimal conditions.
- **Apache-2.0** — permissive with an explicit patent grant.
- **Proprietary / all rights reserved** — public source visibility without reuse permission.

The owner should choose based on the intended reuse model. CodexAtlas does not assign a license implicitly.
