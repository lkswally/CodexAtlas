# Codex-Atlas V2 Architecture Audit V1

Fecha de evidencia: 2026-06-12.

Estado del informe: auditoria read-only. No implementa cambios funcionales, no elimina capas y no modifica governance, workflows, policies ni Evidence Pipeline.

## P0 workflow compatibility update (2026-06-12)

Decision applied without changing workflow behavior:

- `actions/checkout` was upgraded from v4 to v6.
- `actions/setup-python` was upgraded from v5 to v6.
- `actions/upload-artifact` was upgraded from v4 to v7 in the opt-in Evidence Quality Report workflow.
- Both workflows now pin `windows-2025` instead of following the moving `windows-latest` alias.

These action majors declare Node.js 24 runtimes natively, so `FORCE_JAVASCRIPT_ACTIONS_TO_NODE24` is not required. Atlas CI run `27390047784` and Evidence Quality Report run `27390064634` passed without Node.js 20 warnings. The manual report run preserved opt-in/non-blocking behavior and published artifact `7581555415` through `actions/upload-artifact@v7`. GitHub still emits a hosted-runner notice that `windows-2025` is redirected to `windows-2025-vs2026`; this external image transition remains a low monitoring risk.

## Test determinism update (2026-06-12)

The global suite is now fixture-first and independent from the optional sibling repository `../CodexAtlas-Web`. Dispatcher exposure tests create a temporary governed project with metadata derived from the active Atlas root instead of relying on stale, machine-specific fixture metadata. The three original failures reproduce independently on the old setup and pass after this isolation; the complete suite now reports `578 passed` on Python 3.14.5.

## 1. Executive summary

Codex-Atlas ya es un sistema real en tres areas: governance estructural, ejecucion local de tests/checks y Evidence Pipeline opt-in. No es todavia un runtime de agentes ni una plataforma de aprendizaje automatico. La mayor parte de sus integraciones externas, routing, learning y readiness son clasificadores advisory-only que producen postura y recomendaciones, no efectos operativos.

El avance mas importante de V2 es Evidence Pipeline: abre una URL con Playwright, captura desktop/mobile, recoge errores de consola/red, persiste un contrato validado, genera summary/report y publica un artifact mediante un workflow manual observado. Esta cadena tiene evidencia real. Sin embargo, su quality report solo confirma salud tecnica basica; no verifica calidad visual, motion, CTA visibility, spacing, hierarchy, deploy ni regresion.

El riesgo arquitectonico principal es la acumulacion de superficie declarativa alrededor de un nucleo operativo pequeno. El repositorio contiene 78 archivos bajo `tools`, 55 policies y 42 configs. Muchas capas son utiles como guardrails, pero `atlas_governance_check.py` (~4.800 lineas) y `quality_gate_report.py` (~2.700 lineas) concentran demasiadas responsabilidades. Governance valida con rigor que contratos y archivos existan, pero eso puede dar una sensacion de madurez superior a la capacidad real de observar outcomes.

Veredicto: **WARN arquitectonico, PASS operativo del nucleo canónico**.

- PASS: governance local, `atlas_verify`, CI principal, Evidence Report opt-in, Failure Record V1 y lookup deterministico.
- WARN: suite global no deterministica/verde, CI cubre un subset, Agent Loop sigue manual, docs presentan drift, readiness domina sobre runtime.
- No se encontro una integracion externa activa de Engram, n8n, Chrome DevTools MCP o scheduled automation.
- No hay evidencia para declarar BROKEN esas integraciones porque sus contratos dicen advisory-only; si hay claims de operatividad, esos claims deben corregirse.

## 2. Evidence collected

### Checks locales

| Check | Resultado |
|---|---|
| Tests canonicos usados para este ciclo | `138 passed` |
| Governance | `ATLAS GOVERNANCE CHECK / OK` |
| `atlas_verify` | `status: ok`, sin failed checks |
| Compile de `tools` | `python -m compileall -q tools`, exit 0 |
| `git diff --check` inicial | limpio |
| `git status -sb` inicial | `main...origin/main`, limpio |
| Suite global | Initial audit: `575 passed, 3 failed`; after determinism fix: `578 passed` |

Los tres fallos globales son:

1. `test_prompt_builder_uses_phase_and_intent_for_existing_project`: espera `planning/certified`, pero el repo hermano mutable `CodexAtlas-Web` resuelve `audit`.
2. `test_dispatcher_exposes_prompt_builder_and_project_intent_commands`: recibe `governance_check_failed_before_execution`, no el unico error alternativo aceptado por el test.
3. `test_dispatcher_exposes_skill_evaluator`: misma discrepancia de error del dispatcher.

Dos fallos de dispatcher ya fueron reproducidos sobre el commit base `74c0398`; no son una regresion de Failure Registry. El primer fallo depende de una ruta externa seleccionada por `tests/_support_paths.py` cuando existe `../CodexAtlas-Web`.

### GitHub Actions

Ultimos cinco runs de Atlas CI observados:

| Run | Commit | Resultado |
|---|---|---|
| `27388610730` | `0801e4b` | SUCCESS |
| `27388323847` | `6d5e3bb` | SUCCESS |
| `27387939075` | `74c0398` | SUCCESS |
| `27282541206` | `74e0fe6` | SUCCESS |
| `27281568355` | `08c8182` | FAILURE, luego corregido |

Evidence Quality Report tiene tres runs manuales observados; el run `27252455700` genero artifact valido desde `tests/fixtures/evidence_bundle_valid.json`.

Remediacion P0 aplicada el 2026-06-12: `actions/checkout@v6`, `actions/setup-python@v6` y `actions/upload-artifact@v7` declaran Node.js 24; ambos workflows fijan `windows-2025`. La validacion operativa posterior queda registrada en la seccion de actualizacion P0.

## 3. Current architecture map

```text
Objective / user request
  -> manual Agent Loop checklist
  -> Model Routing Policy V1 (advisory class selection)
  -> Codex/manual execution
  -> local tools and derived-project audits
  -> optional Evidence Runner
  -> Evidence Contract Validator
  -> Evidence Bundle persist/read
  -> Evidence Summary
  -> Evidence Quality Gate Adapter
  -> Evidence Quality Report + CLI + manual GitHub workflow
  -> manual verification/final report
  -> optional Failure Record V1
  -> optional token-overlap similarity lookup

Cross-cutting:
  atlas_dispatcher -> command registry -> audit/certify/report tools
  atlas_governance_check -> validates structural contracts/config/policies
  atlas_verify -> governance + repo audit + surface audit + parity report
  quality_gate_report -> aggregates many readiness/advisory reports
```

Important boundary: Evidence Quality Gate Adapter is isolated and non-blocking. It is not integrated into the main `quality_gate_report.py` or Atlas CI.

## 4. Inventory

### Tools

Core execution and governance:

`atlas.ps1`, `start_atlas_project.ps1`, `atlas_codex_executor.py`, `atlas_context_audit.py`, `atlas_dispatcher.py`, `atlas_governance_check.py`, `atlas_orchestrator.py`, `atlas_project_bootstrap.py`, `atlas_run.py`, `atlas_surface_audit.py`, `atlas_verify.py`, `quality_gate_report.py`, `quality_gate_schema.py`, `priority_engine.py`, `project_intent_analyzer.py`, `project_phase_resolver.py`, `prompt_builder.py`.

Evidence and failure learning:

`evidence_runner.py`, `evidence_contract_validator.py`, `evidence_session.py`, `evidence_bundle_summary.py`, `evidence_bundle_summary_cli.py`, `evidence_quality_gate_adapter.py`, `evidence_quality_report.py`, `evidence_quality_report_cli.py`, `failure_registry.py`, `decision_feedback.py`, `feedback_analyzer.py`, `error_pattern_analyzer.py`, `atlas_error_learning_review.py`, `post_execution_learning_review.py`.

Design/frontend quality:

`brand_json_v2_readiness.py`, `brand_profile_schema.py`, `brand_strategy_readiness.py`, `component_inspiration_readiness.py`, `copywriting_conversion_readiness.py`, `creative_pipeline_readiness.py`, `design_intelligence_audit.py`, `design_quality_enforcement.py`, `frontend_auto_audit_rules.py`, `frontend_visual_execution_guard.py`, `intent_clarifier_contract.py`, `playwright_visual_qa_readiness.py`, `ui_pre_return_audit.py`, `ui_ux_design_system_readiness.py`, `visual_fidelity_judge.py`, `visual_intent_contract.py`.

External/integration readiness:

`atlas_mcp_manager.py`, `mcp_readiness_check.py`, `mcp_permission_matrix_readiness.py`, `chrome_devtools_mcp_readiness.py`, `github_connector_readiness.py`, `n8n_api_connector_readiness.py`, `n8n_automation_readiness.py`, `n8n_workflow_blueprint_generator.py`, `n8n_workflow_json_generator.py`, `scheduled_automation_readiness.py`, `codex_runtime_compatibility_check.py`, `operational_parity_readiness.py`, `repo_graph_readiness.py`.

Routing, cost, skills and business review:

`model_router.py`, `model_router_core.py`, `model_routing_policy.py`, `model_cost_control_readiness.py`, `department_registry_readiness.py`, `skill_evaluator.py`, `skill_improvement_review.py`, `skill_registry_index_first_readiness.py`, `repo_improvement_scout.py`, `business_idea_simulation_readiness.py`, `change_proposal_readiness.py`, `decision_council_report.py`, `market_research_benchmark.py`, `docs_catalog_report.py`, `docs_search_adapter.py`.

Coverage note: `model_router_core.py` has no same-name test file but is exercised through `test_model_router.py`. No clearly unreferenced Python tool was found by name/import scan.

### Policies

55 policies exist. Groups:

- Safety/governance: `safe_execution`, `human_approval`, `project_boundary_check`, `project_derivative`, `template_quality_check`, `change_proposal`.
- Evidence/quality: `evidence_required`, `design_evidence`, `landing_quality`, `anti_generic_output`, `anti_generic_ui`, `design_quality_enforcement`, `ui_pre_return_audit`, `visual_fidelity_judge`, `frontend_visual_execution_guard`.
- Readiness/integrations: MCP connector/routing/permissions, Chrome DevTools, GitHub, n8n API/automation/generation, scheduled automation, repo graph, operational parity.
- Product/design: brand profile/strategy/JSON V2, copywriting, visual intent/direction, creative pipeline, component inspiration, UI/UX system, market research.
- Model/learning: model routing, model cost, external fallback, error learning, memory readiness, post-execution learning, skill lifecycle/improvement/index-first.

Static reference scan found two policies with zero references outside themselves:

- `policies/external_model_fallback_policy.md`
- `policies/visual_media_capability_policy.md`

These are candidates for explicit indexing or later deprecation, not immediate deletion.

### Configs

42 JSON configs exist. Every config had at least one static reference; most have exactly a tool consumer plus a test/governance reference. Key families:

- model: `model_profiles.json`, `model_routing_rules.json`, `model_cost_control_profiles.json`
- evidence/design: visual fidelity, visual intent, frontend guard, UI pre-return, design quality, creative/component/Playwright profiles
- integrations: MCP profiles/permission matrix, Chrome, GitHub, n8n API/automation/generation, scheduled automation
- learning/memory: error learning, post-execution learning, memory readiness, skill lifecycle/improvement/index-first
- orchestration: `phase_playbook.json`, department registry, external tool policy, docs catalog

`external_tool_policy.json` has only one direct static reference and deserves ownership clarification.

### Docs

Primary docs:

`README.md`, `docs/README.md`, `architecture.md`, `e2e_flows_guide.md`, `operational_parity_codex_native.md`, `capability_radar_and_fallbacks.md`, `codex_system_prompt.md`, `codex_global_factory_setup.md`, `agent_loop_v1_design.md`, `agent_loop_manual_checklist.md`, `evidence_quality_report_usage.md`, `failure_registry_v1.md`, `mcp_read_only_evaluation.md`, `n8n_manual_export_workflow_review.md`, plus reference-assessment docs for Claude/vibecoding.

Drift found:

- `agent_loop_manual_checklist.md` says V2 does not write Failure Registry, but Failure Registry V1 and lookup now exist.
- `README.md` lists Engram and Pixel Bridge while `AGENTS.md` says no Engram/Pixel Bridge and evaluation docs defer/discard them.
- `codex_global_factory_setup.md` contains personal/legacy paths such as `C:\Users\Lucas` and `C:\Proyectos\Codex-Atlas`; current repo is under `D:\Proyectos`.
- Some docs call CLIs as direct scripts; package-import CLIs such as Evidence Report are reliably executable with `python -m tools...`, not `python tools/...` from all contexts.

### Workflows

GitHub Actions:

- `.github/workflows/atlas-ci.yml`: push/PR, governance-oriented, blocking.
- `.github/workflows/evidence-quality-report.yml`: manual dispatch, non-blocking report and optional artifact.

Documented workflows:

`atlas_project_pipeline`, `audit_project`, `audit_repo`, `certify_output`, `certify_project`, `change_proposal_workflow`, `create_project`, `decision_council_review`, `design_intelligence_pipeline`, `market_research_benchmark`, `orchestrator_routing`.

The Markdown workflows are operational guidance, not executable automation.

### Tests

Test modules cover almost every named tool family. Important limitations:

- Atlas CI runs only four focused files: skill governance, quality gate report, project bootstrap and atlas run.
- It does not run Failure Registry, Model Routing Policy, Model Router or the Evidence suite.
- Evidence workflow runs its Evidence subset only on manual dispatch.
- The full local suite is green and fixture-first after the 2026-06-12 determinism fix.
- Many tests use stubs/fixtures and prove contract behavior, not external integration behavior.

### Registries

- `commands/atomic_command_registry.json`: canonical command metadata.
- `00_SISTEMA/_meta/atlas/atomic_command_registry.json`: byte-for-byte equivalent mirror at audit time; duplication carries drift risk.
- `config/department_registry_rules.json`: advisory department catalogue, not runtime department activation.
- `config/skill_registry_index_first_rules.json`: advisory skill selection rules.
- Failure Registry V1: library/record contract only; no central registry directory, index or automatic ingestion.

### Readiness layers

Explicit readiness tools include Atlas memory, brand JSON/strategy, business simulation, change proposal, Chrome DevTools MCP, component inspiration, copywriting, creative pipeline, department registry, evidence collector, GitHub connector, MCP checks/permissions, model cost, n8n API/automation, operational parity, Playwright visual QA, repo graph, scheduled automation, skill registry index-first and UI/UX design system.

Most return `advisory_only: true`. This is truthful in code, but their number increases cognitive load and aggregation complexity.

## 5. What works

1. Governance contracts are executable and currently pass locally and in CI.
2. `atlas_verify` composes governance, repo audit, surface audit and operational parity without mutation.
3. Evidence Runner captures real browser artifacts when Playwright/runtime are available.
4. Evidence Contract/Bundle/Summary/Report have deterministic schemas and focused tests.
5. Evidence Quality Report manual workflow handles missing bundles and valid bundle artifacts correctly.
6. Model Routing V1 selects classes deterministically, keeps auto-switch disabled and has a compatibility bridge for older advisory consumers.
7. Failure Record V1 validates exact fields, rejects obvious secret patterns, persists JSON and supports deterministic lexical lookup.
8. n8n offline blueprint/JSON and readiness tools provide safe local design surfaces without pretending to execute n8n.
9. GitHub CLI is available in the operating environment and workflow history can be observed.
10. Source modules compile successfully.

## 6. Partial or advisory-only

### Agent Loop

Manual checklist and role boundaries are coherent, but there is no runtime, state machine, run record or enforcement. Evidence and Failure Registry are invoked by operator discipline, not architecture.

### Model Routing

Policy selection works. Concrete model recommendation compatibility works. Actual model selection remains manual and runtime model state is unknown. This is correctly advisory-only.

### Failure Learning

Failure records and similarity lookup work as isolated library functions. There is no shared storage/index, no Agent Loop hook and no measured reuse. `post_execution_learning_review` still recommends creating more readiness/policies, which conflicts with the V2 goal of reducing readiness proliferation.

### Visual verification

Visual fidelity and frontend guard consume report fields, filenames, declared evidence and static signals. They do not inspect screenshot pixels, compare baselines, execute motion, measure layout geometry or verify CTA visibility. Evidence Runner produces screenshots but no visual evaluator consumes them.

### Memory

Local files exist and memory readiness checks their presence. This is continuity scaffolding, not automatic memory retrieval. JSONL files can grow; `governance_events.jsonl` is already materially larger than most source docs.

## 7. What is broken or inconsistent

No P0 runtime break was found in the canonical path. Confirmed inconsistencies:

1. Agent Loop docs still prohibit Failure Registry after it was implemented.
2. README/AGENTS conflict on Engram and Pixel Bridge.
3. Main CI does not run the newly added Failure Registry or Model Routing tests.
4. Direct invocation of `tools/evidence_quality_report_cli.py` fails package import; documented/module invocation works.
5. Chrome readiness probe can report browser symptoms but declare frontend not applicable when project type vocabulary does not match configured types; taxonomy requires review.
6. `atlas_verify` reports operational parity `ready` even when MCP CLI is unavailable. The label is narrower than it sounds.

Resolved on 2026-06-12: the three global-suite failures, mutable sibling `WEB_ROOT` selection, and invalid dispatcher fixture setup.

## 8. Remove or deprecate later

Do not delete during this audit. Candidates:

- Either index or deprecate the two unreferenced policies.
- Decide which atomic command registry is canonical and generate/validate the mirror instead of hand-maintaining two copies.
- Archive reference-assessment docs if they are no longer active architecture guidance.
- Consolidate overlapping readiness layers only after measuring which outputs are consumed by decisions.
- Split monolithic governance/quality reporting by stable ownership boundaries after characterization tests exist.

## 9. Integration audit

| Integration | State | Evidence | Risks | Recommendation |
|---|---|---|---|---|
| Engram | ADVISORY_ONLY | MCP profile/evaluation docs; explicitly deferred; no connector/runtime | README ambiguity, duplicate source of truth | isolate; clarify as unsupported/deferred |
| n8n | PARTIAL | offline generators and readiness tests work; API probe returns `not_configured`, all operations blocked | users may confuse generated JSON/readiness with live integration | keep offline tools; isolate live connector claims |
| Chrome DevTools MCP | ADVISORY_ONLY | readiness tool/test; MCP not configured; Codex CLI unavailable | no real browser MCP evidence, privacy/telemetry | keep readiness; do not promote until a real read-only probe succeeds |
| GitHub connector | PARTIAL | readiness logic and tests; `gh` works operationally; runtime probe not requested by default | connector output can say theoretically ready without probing | keep; separate theoretical posture from observed runtime |
| Scheduled automations | ADVISORY_ONLY | classifier returns watchlist; no scheduler/runtime | false impression of automation capability | keep only if consumed; otherwise deprecate later |
| Model Routing | ADVISORY_ONLY | deterministic policy tests and bridge; `auto_switch_allowed=false` | legacy concrete-model bridge can drift from class policy | keep; define one authoritative output boundary |
| Evidence Quality Report | WORKING | local CLI PASS, manual runs, artifact validation | non-blocking; technical PASS is not product approval | keep and deepen evidence before integrating |

## 10. Workflow audit

### Atlas CI

Strengths:

- blocking on push/PR
- executes verify, governance, MCP readiness and focused governance tests
- recent history is stable after routing fixes

Gaps:

- only a focused subset runs
- does not exercise Failure Registry, routing policy/router or Evidence Pipeline
- does not fail on full-suite regressions
- Node.js 24 action majors require an observed post-change CI run
- the pinned `windows-2025` hosted image can still drift internally

### Evidence Quality Report

Strengths:

- manual/opt-in and non-blocking by design
- tests Evidence chain before report generation
- skips missing bundle clearly
- publishes artifact only when generated

Gaps:

- does not run Evidence Runner or a browser
- validates a supplied bundle, so provenance can be synthetic
- `continue-on-error` intentionally prevents technical FAIL from failing workflow
- only three observed manual runs; no continuous history

## 11. Test/docs/config consistency audit

### Tools and tests

Nominal coverage is broad. The main issue is not absent unit tests but execution selection: CI does not run many of them. Integration tests mostly mock external surfaces.

### Config consumers

All configs have references. Low reference count should not be interpreted as dead automatically because configs are often loaded by one tool and validated by one test. `external_tool_policy.json` needs a named owner/consumer boundary.

### Policies

Most policy references come from governance/index surfaces, not runtime enforcement. Policy existence is therefore evidence of documented intent, not behavior.

### Naming

The terms `readiness`, `posture`, `guard`, `judge`, `audit`, `review` and `enforcement` overlap. In practice, many are advisory classifiers. `design_quality_enforcement` and `visual_fidelity_judge` sound stronger than their actual evidence model.

## 12. Architecture scores

| Area | Score / 100 | Rationale |
|---|---:|---|
| Evidence System | 78 | real capture/persistence/report path; no visual semantics/regression/deploy verification |
| Governance | 72 | strong structural validation and CI; monolithic and outcome-light |
| Model Routing | 65 | deterministic and safe; advisory, dual class/concrete boundary |
| Agent Loop | 42 | good manual design; no runtime or durable run state |
| Failure Learning | 58 | valid records and lookup; no actual feedback loop usage yet |
| CI/CD | 68 | stable canonical CI and manual evidence workflow; subset coverage and imminent action warning |
| Integrations | 35 | mostly theoretical/readiness; only GitHub CLI and Evidence artifact path observed |
| Docs | 61 | extensive and thoughtful; stale claims, local paths and scope contradictions |
| Test Coverage | 70 | many unit tests; full suite fails and external-path determinism is weak |
| Operational Readiness | 62 | core works; several advertised surfaces require manual discipline |

Overall architecture score: **61/100**.

## 13. Risk register

| ID | Risk | Severity | Evidence | Mitigation direction |
|---|---|---|---|---|
| R1 | Hosted runner image transition | Low/monitoring | Node.js 24 runs pass, but GitHub redirects `windows-2025` to `windows-2025-vs2026` | monitor runner release notes and observed runs |
| R2 | Full-suite determinism regression | Low/monitoring | 578 pass after fixture isolation; previously 575 pass / 3 fail | keep tests fixture-first and require full-suite validation |
| R3 | CI coverage false confidence | High | main CI runs four test files | define canonical suite manifest or broader test job |
| R4 | Readiness proliferation | Medium-high | 20+ readiness tools, 55 policies | measure consumers; consolidate by evidence/value |
| R5 | Governance monolith | Medium-high | ~4.800 lines | characterize and split validators by domain later |
| R6 | Quality report monolith | Medium-high | ~2.700 lines, many posture adapters | separate aggregation from domain checks |
| R7 | Visual PASS semantics too weak | High | screenshots counted, not inspected | add evidence-based viewport/CTA/motion checks before visual approval |
| R8 | Documentation truth drift | Medium | Agent Loop/Failure Registry and Engram conflicts | truth-source audit and status labels |
| R9 | External path coupling | Low/monitoring | test defaults no longer select sibling `CodexAtlas-Web`; explicit env override remains available | keep integration paths opt-in |
| R10 | Failure learning not consumed | Medium | isolated functions only | manual Planner/Verifier dry run before runtime integration |
| R11 | Duplicate command registry | Medium | two identical copies | generate or validate mirror ownership |
| R12 | Advisory names imply enforcement | Medium | judge/enforcement/guard labels | document evidence consumed and authority explicitly |

## 14. Prioritized improvement backlog

### P0

#### P0.1 GitHub Actions Node runtime compatibility (closed 2026-06-12)

- Problem: previous action majors used deprecated Node.js 20 before the runtime transition.
- Evidence: warning in run `27388610730`; official stable majors now declare Node.js 24.
- Impact: migration removes the time-bound Node.js 20 dependency without changing job logic.
- Risk: low; hosted runner redirection remains external and non-blocking.
- Recommendation: retain monitoring only; runs `27390047784` and `27390064634` passed.
- Files: both `.github/workflows/*.yml`.
- Effort: S.
- Human approval: yes, workflow change.

### P1

#### P1.1 Make full test suite deterministic and green (closed 2026-06-12)

- Evidence: the original three failures reproduced individually; `578 passed` after fixture isolation.
- Impact: local results no longer change merely because `../CodexAtlas-Web` exists.
- Resolution: fixture-first `WEB_ROOT` and temporary governed projects for dispatcher exposure tests.
- Files: `tests/_support_paths.py`, `tests/test_prompt_builder.py`, `tests/test_skill_evaluator.py`.
- Effort: S.
- Human approval: no runtime contract changed.

#### P1.2 Define and run a canonical CI test manifest

- Evidence: main CI excludes Evidence, routing and Failure Registry tests.
- Impact: regressions can merge while CI remains green.
- Recommendation: one documented test set that includes all critical V2 capabilities; keep browser tests separate.
- Files: `atlas-ci.yml`, test documentation/config.
- Effort: S-M.
- Human approval: yes.

#### P1.3 Prove Evidence Runner in CI/manual browser execution

- Evidence: workflow validates fixture bundle but does not launch browser.
- Impact: pipeline can PASS while capture path is broken.
- Recommendation: separate opt-in browser smoke run against deterministic local fixture; do not make visual approval claims.
- Files: future workflow/test fixture, Evidence docs.
- Effort: M.
- Human approval: yes.

### P2

#### P2.1 Readiness value/consumer matrix

- Evidence: many layers feed only `quality_gate_report`; most are advisory.
- Impact: maintenance cost and unclear authority.
- Recommendation: classify each as keep/merge/deprecate based on unique evidence and active consumers.
- Files: readiness tools/config/policies, no deletion first pass.
- Effort: M.
- Human approval: yes before deprecation.

#### P2.2 Split governance and quality aggregation boundaries

- Evidence: two modules total ~7.500 lines.
- Impact: schema migrations cause broad regressions; ownership is opaque.
- Recommendation: characterization tests, then domain validators/adapters without behavior change.
- Files: governance/quality modules and tests.
- Effort: L.
- Human approval: yes.

#### P2.3 Connect Failure Lookup to manual Agent Loop

- Evidence: lookup works but no consumer; Agent Loop doc says registry is prohibited.
- Impact: learning exists but does not alter planning behavior.
- Recommendation: documentation-only dry run first; record whether lookup changes a plan.
- Files: Agent Loop docs and Failure Registry docs.
- Effort: S.
- Human approval: no for docs; yes before runtime.

#### P2.4 Tighten Evidence semantics

- Evidence: PASS means counts/errors/build presence, not UX or visual correctness.
- Impact: technical PASS may be misread as product approval.
- Recommendation: keep report wording explicit; next checks should be deterministic CTA visibility, viewport overflow and motion event verification before image scoring.
- Files: future isolated evidence consumers/tests.
- Effort: M-L.
- Human approval: yes for any blocking behavior.

### P3

#### P3.1 Documentation truth pass

- Fix Agent Loop/Failure Registry drift, Engram/Pixel Bridge ambiguity, personal paths and CLI invocation consistency.
- Effort: S-M.
- Human approval: no.

#### P3.2 Resolve orphan policies and duplicate registry ownership

- Index or mark deprecated; do not delete until consumers are confirmed.
- Effort: S.
- Human approval: yes for deprecation/deletion.

#### P3.3 Memory/log retention policy

- Define rotation/archival for JSONL event logs and prevent workspace noise.
- Effort: M.
- Human approval: yes before deleting history.

### P4

- Outcome Evaluator only after production outcome evidence exists.
- Visual regression only after deterministic baselines and viewport policy exist.
- Failure similarity beyond lexical overlap only after real query history proves the need.
- Optional Paperclip evaluation only after manual Agent Loop has measurable value and pain.
- External model/provider integrations only after a specific workload justifies cost and risk.

## 15. Recommended next five implementation phases

1. **Critical coverage phase**: include Evidence/Failure/Model critical tests in canonical CI.
2. **Evidence execution phase**: run a deterministic browser capture smoke test and verify produced bundle/report.
3. **Architecture consolidation audit**: produce readiness consumer/value matrix, then approve only evidence-backed merges/deprecations.
4. **Hosted runner monitoring phase**: review the `windows-2025-vs2026` transition only if observed behavior changes.
5. **Test determinism monitoring phase**: retain full-suite validation and keep sibling-project integration explicitly opt-in.

## 16. Explicit no-go list

Do not implement now:

- new readiness layers
- new policies without an active consumer and demonstrated gap
- new agents or agent runtime
- Paperclip integration
- Engram integration
- automatic model switching
- automatic failure-record ingestion or self-mutation
- LLM/embedding similarity search
- visual AI judge or scoring before deterministic checks
- mandatory Evidence Quality Gate
- live n8n writes/execution
- scheduled production automation
- broad governance refactor before characterization coverage
- deletion of policies/tools solely because static reference count is low

## 17. Final verdict

Atlas is no longer only a readiness documentation system: Evidence Pipeline, CI, governance and isolated failure records are concrete capabilities. But it is not yet evidence-driven end to end. Evidence is optional, visual evidence is not semantically evaluated, failure learning is not consumed by planning, and most integrations remain advisory classifiers.

The highest ROI is not another feature. It is making the existing truth surface reliable: CI runtime continuity, deterministic full tests, critical-suite coverage and one real browser capture path. Only after those four are stable should Atlas consolidate readiness layers or introduce outcome evaluation.
