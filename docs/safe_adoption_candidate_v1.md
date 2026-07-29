# Safe Adoption Candidate V1

Fecha: 2026-07-29.

Estado: diseno solamente. No implementa tools, tests funcionales, workflows,
runtime, hooks, MCP, agentes, policies ni dependencias.

Fuente de verdad:

- `docs/atlas_vs_claude_vibecoding_delta_benchmark_v4.md`.
- Claude-Vibecoding comparado desde `2f75af6efa9bd7692e39f695c468528eeadfa5e6`
  hasta `9288a09552529ffede2af59390adc35d404bb751`.
- Atlas baseline: commit `54a3fab`, Atlas CI run `30480394494` SUCCESS.

## 1. Executive Summary

Resultado: `IMPLEMENT_NEXT`.

Candidato seleccionado: `Diagnostic mode checklist`.

Razon corta: es el candidato ADAPT con mejor relacion valor/riesgo porque mejora
estabilidad, seguridad y DX sin requerir runtime, hooks globales, configuracion
global, agentes nuevos, MCP, autoejecucion ni cambios al Evidence Pipeline.

No se selecciona el candidato mas llamativo. `Evidence-aware composition variety`
ataca un gap visual real, pero su complejidad y duplicacion parcial con
`ui_pre_return_audit`, `frontend_visual_execution_guard`, `design_quality_enforcement`
y `visual_fidelity_judge` lo hacen menos seguro para la primera adopcion.

No se selecciona `Context splitting` aunque tiene impacto fuerte en tokens,
porque puede crear drift documental si se implementa antes de tener una regla
simple de modo diagnostico que separe analisis de ejecucion.

## 2. Candidatos Extraidos Del Reporte V4

### ADAPT

| Candidato | Fuente V4 | Lectura inicial |
|---|---|---|
| Context splitting with on-demand references | `CLAUDE.md`, `agents/orquestador.md`, `agents/*-reference.md` | Valioso para tokens/contexto, pero con riesgo de segunda fuente de verdad |
| Evidence-aware composition variety and fluid spacing audit | `agents/ui-designer.md`, `agents/ux-architect.md`, `hooks/pre-return-audit.sh` | Gap visual real, pero toca superficie ya poblada de checks visuales |
| VISUAL_IMPACT checkpoint semantics | `agents/agent-protocol.md`, `agents/orquestador-vdc-reference.md` | Util para no confundir PASS tecnico con aprobacion visual |
| Simplicity-first reporting doctrine | `CLAUDE.md`, `agents/simplicity-first-reference.md` | Bajo riesgo y ahorro de tokens, pero menor impacto de estabilidad |
| Diagnostic mode checklist | `agents/modo-diagnostico-reference.md` | Mejora read-only audits y evita implementacion accidental durante analisis |

### WATCH

| Candidato | Fuente V4 | Razon para no seleccionar ahora |
|---|---|---|
| `.codegraph/` ignore principle | `.gitignore` | Atlas ya tiene higiene de temporales; sin Codegraph runtime |
| Engram save protocol | `agents/engram-save-reference.md` | Engram sigue externo/advisory; riesgo de memoria externa |
| Visual Direction Checkpoint details | `agents/orquestador-vdc-reference.md` | Parcialmente ADAPT como semantica, pero no como runtime |
| Phase 4/5 certification/publication detail | `agents/orquestador-fase45-reference.md` | Deploy/git automation fuera de scope |
| Domain references: auth, React, Linux, Redis, GSAP, scroll, creative coding | `agents/*-reference.md` | Utiles solo para generacion de apps o visual work futuro |
| Healthcheck aggregator | hooks/reporting Claude | Atlas ya tiene `atlas_verify`; observar antes de duplicar |
| Engram cloud lifecycle | Engram refs | Riesgo de side effects y secretos |

### ADOPT

No se encontro candidato `ADOPT` literal en el reporte V4. El reporte V4
recomienda adaptar patrones, no copiar runtime Claude.

## 3. Ranking Deterministico

Escala: 1 bajo, 5 alto.

Formula:

```text
benefit_score =
stability_value
+ security_value
+ maintainability_value
+ dx_value
+ token_saving_value

risk_score =
implementation_risk
+ compatibility_risk
+ complexity
+ side_effect_risk
+ regression_risk

adoption_score =
benefit_score - risk_score
```

| Candidato | Gap real en Atlas | Valor | Riesgo | Complejidad | Token impact | Duplicacion | Testeabilidad | Rollback | Resultado |
|---|---|---:|---:|---:|---:|---:|---:|---:|---|
| Diagnostic mode checklist | Auditorias manuales existen, pero falta un contrato corto que bloquee drift hacia implementacion durante analisis | 20 | 7 | 2 | 2 | 2 | 5 | 5 | SELECTED, score 13 |
| Simplicity-first reporting doctrine | Reportes Atlas pueden crecer y consumir contexto | 16 | 5 | 1 | 5 | 3 | 3 | 5 | WATCH, score 11 |
| Context splitting with on-demand references | Mucha superficie documental compite por contexto | 18 | 11 | 3 | 5 | 2 | 4 | 4 | WATCH, score 7 |
| VISUAL_IMPACT checkpoint semantics | PASS tecnico puede confundirse con aprobacion visual | 15 | 10 | 2 | 2 | 3 | 4 | 4 | WATCH, score 5 |
| Evidence-aware composition variety and fluid spacing audit | Salidas visuales repetitivas y containers rigidos fueron gap real | 13 | 12 | 3 | 2 | 3 | 4 | 4 | WATCH, score 1 |

Detalle de scoring:

| Candidato | stability_value | security_value | maintainability_value | dx_value | token_saving_value | benefit_score | implementation_risk | compatibility_risk | complexity | side_effect_risk | regression_risk | risk_score | adoption_score |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| Diagnostic mode checklist | 5 | 5 | 4 | 4 | 2 | 20 | 2 | 1 | 2 | 1 | 1 | 7 | 13 |
| Simplicity-first reporting doctrine | 2 | 1 | 4 | 4 | 5 | 16 | 1 | 1 | 1 | 1 | 1 | 5 | 11 |
| Context splitting with on-demand references | 3 | 2 | 4 | 4 | 5 | 18 | 2 | 2 | 3 | 2 | 2 | 11 | 7 |
| VISUAL_IMPACT checkpoint semantics | 4 | 2 | 3 | 4 | 2 | 15 | 2 | 2 | 2 | 2 | 2 | 10 | 5 |
| Evidence-aware composition variety and fluid spacing audit | 2 | 2 | 3 | 4 | 2 | 13 | 2 | 2 | 3 | 2 | 3 | 12 | 1 |

## 4. Mandatory Gate

| Gate | Diagnostic mode checklist |
|---|---|
| Resuelve un gap demostrado | PASS: Atlas tiene auditorias y checklists, pero no un contrato compacto para "solo diagnostico" |
| No duplica capacidad existente | PASS_WITH_WARNINGS: duplica parcialmente repo-audit/Agent Loop, pero los ordena como modo operativo |
| Puede implementarse aisladamente | PASS |
| No requiere runtime | PASS |
| No requiere hooks globales | PASS |
| No requiere configuracion global | PASS |
| No requiere autoejecucion | PASS |
| No introduce side effects invisibles | PASS |
| No debilita Evidence | PASS |
| No debilita Governance | PASS |
| No debilita Dangerous Command Policy | PASS |
| No aumenta agentes innecesariamente | PASS |
| No obliga a modelos premium para tareas simples | PASS |
| Tiene contrato verificable | PASS |
| Tiene tests claros | PASS |
| Tiene rollback claro | PASS |

Gate final: `SELECTED`.

## 5. Duplicaciones Revisadas

| Candidato | Superficie Atlas relacionada | Clasificacion | Decision |
|---|---|---|---|
| Diagnostic mode checklist | `docs/agent_loop_manual_checklist.md`, `skills/repo-audit/skill.md`, `docs/architecture_audit_v1.md`, governance/verify checks | COMPLEMENTARIO | Seleccionar como contrato manual compacto |
| Simplicity-first reporting doctrine | Final answer rules, report docs, architecture audits | DUPLICADO_PARCIAL | No seleccionar primero; puede incorporarse como estilo posterior |
| Context splitting with on-demand references | `docs/README.md`, `docs/architecture_audit_v1.md`, many policies/configs, skill docs | COMPLEMENTARIO | Riesgo de drift si se divide sin estrategia documental |
| VISUAL_IMPACT checkpoint semantics | `skills/visual-direction-checkpoint`, `docs/claude_vibecoding_design_intelligence.md`, Evidence Quality Report docs | DUPLICADO_PARCIAL | Mejor despues de reforzar diagnostico manual |
| Evidence-aware composition variety and fluid spacing audit | `tools/ui_pre_return_audit.py`, `frontend_visual_execution_guard.py`, `design_quality_enforcement.py`, `visual_fidelity_judge.py`, visual tests | DUPLICADO_PARCIAL | No seleccionar; requiere cuidado para no crear otro readiness |

Duplicaciones concretas encontradas:

- `docs/agent_loop_manual_checklist.md` ya define fases, evidencia y estados,
  pero es un loop completo, no un modo de auditoria read-only.
- `skills/repo-audit/skill.md` define una skill para auditoria de repos, pero no
  tiene un contrato universal de "no implementar todavia".
- `docs/architecture_audit_v1.md` registra auditorias reales, pero no provee un
  checklist reusable de intake/outputs/failures para diagnosticos futuros.
- `skills/visual-direction-checkpoint/` y `tools/frontend_visual_execution_guard.py`
  ya cubren parte de visual checkpoints; agregar `VISUAL_IMPACT` ahora podria
  duplicar semanticas.
- `tools/ui_pre_return_audit.py` ya es el lugar natural para fluid spacing; por
  eso no conviene crear otro audit visual.

## 6. Gap Real

Gap demostrado: Atlas ya ejecuta auditorias complejas y tiene Evidence,
Governance, Model Routing y Failure Registry, pero las solicitudes de analisis
pueden mezclarse con fases de implementacion si no hay un contrato operativo
manual, corto y verificable que diga:

- que la tarea es diagnostica;
- que no se modifican runtime/tools/workflows;
- que los hallazgos deben citar evidencia;
- que la salida no declara PASS sin revision/checks;
- que los fallos se registran como candidates, no como auto-learning.

Este gap se observa indirectamente en el propio flujo V4: el usuario tuvo que
repetir muchas veces "No implementar todavia", "No crear runtime", "No avanzar".
Un modo diagnostico manual reduce ese costo de coordinacion.

## 7. Adaptation Design

```json
{
  "candidate": "Diagnostic mode checklist",
  "source_reference": "Claude-Vibecoding agents/modo-diagnostico-reference.md as summarized in docs/atlas_vs_claude_vibecoding_delta_benchmark_v4.md",
  "atlas_gap": "Atlas has repo-audit and Agent Loop docs, but no compact reusable diagnostic-mode contract that prevents analysis tasks from drifting into implementation.",
  "adaptation_scope": "Create a documentation-only Atlas diagnostic mode contract that defines read-only intake, evidence expectations, allowed outputs, prohibited actions, result states, and escalation criteria.",
  "non_goals": [
    "No runtime mode",
    "No new agent",
    "No hook",
    "No MCP integration",
    "No workflow change",
    "No quality gate integration",
    "No auto-learning",
    "No automatic file writes beyond the approved documentation change in the implementation phase"
  ],
  "inputs": [
    "user objective",
    "scope constraints",
    "allowed files",
    "forbidden files",
    "current repo evidence",
    "checks requested or applicable"
  ],
  "outputs": [
    "diagnostic classification",
    "evidence inventory",
    "findings with paths or command evidence",
    "risk register",
    "recommendation",
    "explicit non-implementation statement",
    "next-phase proposal if safe"
  ],
  "contract": {
    "mode": "diagnostic_only",
    "runtime_integration": false,
    "allowed_actions": [
      "read files",
      "run read-only inventory commands",
      "run tests/checks when requested or required",
      "create or update the approved diagnostic report only"
    ],
    "forbidden_actions": [
      "create runtime tools",
      "modify quality gates",
      "modify workflows",
      "modify policies",
      "install dependencies",
      "run external side-effectful integrations",
      "push without requested validation"
    ],
    "status_values": [
      "PASS",
      "WARN",
      "FAIL",
      "BLOCKED"
    ],
    "pass_rule": "PASS requires real review evidence plus requested checks when applicable.",
    "evidence_rule": "Every finding must cite a real path, command result, or explicit unknown.",
    "side_effect_rule": "No hidden side effects; generated logs must be excluded unless explicitly requested."
  },
  "failure_modes": [
    "The mode becomes another long doc nobody uses",
    "The checklist duplicates Agent Loop instead of simplifying diagnostic tasks",
    "Operators treat diagnostic recommendations as implementation approval",
    "Findings are asserted without path or command evidence"
  ],
  "security_boundaries": [
    "No secrets in reports",
    "No .env reads",
    "No token dumps",
    "No external network unless explicitly requested for current facts",
    "No global config writes",
    "No destructive commands"
  ],
  "side_effects": [],
  "dependencies": [],
  "token_impact": "Positive but modest: a compact diagnostic contract should reduce repeated scope reminders and final-report sprawl.",
  "context_impact": "Positive: it creates a short routing surface for read-only analysis instead of requiring the full Agent Loop doc.",
  "model_routing_impact": "Neutral to positive: diagnostic tasks can remain advisory and use existing Model Routing Policy classes; no auto-switch.",
  "agent_routing_impact": "Neutral: no new agents; it clarifies when existing reviewer/reality_checker posture applies.",
  "evidence_required": [
    "source paths reviewed",
    "commands executed",
    "checks results",
    "explicit unknowns",
    "scope adherence statement"
  ],
  "tests_required": [
    "docs contain required sections",
    "docs state runtime_integration=false",
    "docs prohibit hooks/global config/MCP/runtime",
    "docs define PASS/WARN/FAIL/BLOCKED",
    "docs require evidence for PASS",
    "docs link to Agent Loop and repo-audit without replacing them"
  ],
  "rollback_plan": "Single commit revert removes the diagnostic-mode documentation and any optional README link. No data migration or runtime cleanup required.",
  "migration_required": false,
  "runtime_integration": false
}
```

## 8. Architecture Impact Review

| Domain | Impact | Rationale |
|---|---|---|
| Governance | POSITIVE | Reinforces read-only and evidence-before-PASS posture without changing governance code |
| Evidence | POSITIVE | Requires evidence citations for diagnostic claims |
| Dangerous Command Policy | NEUTRAL | Does not change command classification; references existing safety boundaries |
| Intelligent Orchestrator | POSITIVE | Gives a clearer manual mode before planning/execution |
| Decision Benchmark | NEUTRAL | No runtime routing change |
| Architecture State Model | NEUTRAL | No state schema change |
| MCP | NEUTRAL | Explicitly prohibits MCP runtime/write integration |
| Skills | POSITIVE | Complements `repo-audit` without creating a new skill yet |
| Agents/Roles | NEUTRAL | No new agent or role |
| Failure Registry | POSITIVE | Clarifies failures as candidate records, not auto-learning |
| Dashboard | NEUTRAL | No dashboard fields or artifacts |
| CI | NEUTRAL | No workflow change required |
| Developer Experience | POSITIVE | Reduces repeated "no implementation" instructions |
| token/context efficiency | POSITIVE | Shorter reusable diagnostic contract can replace repeated long constraints |

No `NEGATIVE` impact accepted. No `UNKNOWN` remains; all uncertain future
effects are listed as risks and excluded from V1 runtime scope.

## 9. Test Plan For Future Implementation

### Unit Tests

- Happy path: diagnostic contract document contains required mode, status values,
  evidence rule and non-goals.
- Invalid input: a future parser or docs validator rejects missing `mode`.
- Missing input: validator reports missing required sections without crashing.
- Deterministic output: repeated validation of the same doc returns same result.
- No side effects: validation reads docs only and writes nothing.
- Error contract: missing section returns structured FAIL, not uncaught exception.

### Contract Tests

- Input format: documentation contains Objective, Allowed Actions, Forbidden
  Actions, Evidence, Status, Output, Rollback.
- Output format: any future diagnostic report includes status, evidence,
  findings, risks and recommendation.
- Compatibility: references Agent Loop and repo-audit as upstream/downstream
  docs, without redefining their full contracts.
- Evidence required: PASS section explicitly requires real review evidence.
- Failure propagation: BLOCKED/FAIL examples remain explicit and non-PASS.

### Regression Tests

- Existing suite does not degrade.
- Decision Benchmark does not change.
- Dangerous Command Policy does not change.
- Context minimization does not degrade by creating an oversized doc.
- Model Routing does not change class outputs.

### Safety Tests

- No autoexecution.
- No config global.
- No unexpected filesystem write.
- No MCP write.
- No secrets exposed.
- No implicit network access.
- No hooks created.

## 10. Rollback Plan

Files that would be created in the next implementation phase:

- `docs/atlas_diagnostic_mode_v1.md`.

Optional file that could be modified:

- `docs/README.md` with one link only, if the docs index requires it.

Files that must not be modified:

- `tools/*`.
- `tests/*`, except optional docs-only validator if explicitly approved later.
- `.github/workflows/*`.
- `quality_gate_report.py`.
- `visual_fidelity_judge.py`.
- `tools/dangerous_command_policy.py`.
- MCP configs.
- registries.
- policies.
- agent runtime docs unless separately approved.

Disable path:

- Stop referencing `docs/atlas_diagnostic_mode_v1.md`.
- Remove optional docs index link if present.

Revert:

- `git revert <implementation_commit>`.

Persistent data:

- None expected. The design has no runtime, artifacts, registries, memory writes
  or external services.

Verification after rollback:

- `git status -sb`.
- `git diff --check`.
- `py tools/atlas_governance_check.py`.
- `py tools/atlas_verify.py`.
- `py -m compileall -q tools`.
- Optional focused docs test if one was introduced in the future.

Rollback should be possible through a single revert commit.

## 11. Acceptance Criteria

The next implementation phase can be accepted only if:

- It creates documentation only, unless explicit approval expands scope.
- It does not create runtime behavior.
- It does not create hooks.
- It does not create MCP integration.
- It does not modify workflows.
- It does not modify quality gates.
- It defines PASS/WARN/FAIL/BLOCKED.
- It states that PASS requires evidence.
- It names allowed and forbidden actions.
- It links to existing Agent Loop/repo-audit surfaces instead of duplicating them.
- Governance, atlas_verify, compileall and git diff checks pass.

## 12. Recommendation

Recommendation: `IMPLEMENT_NEXT`.

Implementation should be a small documentation phase only:

1. Create `docs/atlas_diagnostic_mode_v1.md`.
2. Optionally add one docs index link.
3. Run governance, atlas_verify, compileall and diff checks.
4. Do not create runtime, tests, workflows, policies, agents, hooks or MCP.

Rejected for this immediate next phase:

- `Evidence-aware composition variety and fluid spacing audit`.
- `VISUAL_IMPACT checkpoint semantics`.
- `Context splitting with on-demand references`.
- `Simplicity-first reporting doctrine`.

They remain valid future candidates, but this selection optimizes first for
stability, security, compatibility and maintainability.
