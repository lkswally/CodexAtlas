# Karpathy Architecture Benchmark V1

Fecha: 2026-08-07.

Estado: investigacion y diseno solamente. No implementa runtime, modelos,
providers, MCP, hooks, workflows, agentes, experiments autonomos ni copia codigo
externo.

## 1. Executive Summary

Conclusion: Atlas debe adaptar dos patrones de Karpathy, pero en forma
mucho mas conservadora que los repos originales:

1. `Atlas Experiment Loop`: adaptar el ciclo baseline -> hypothesis ->
   bounded experiment -> objective metric -> KEEP/DISCARD/INCONCLUSIVE, pero
   inicialmente solo como simulacion/manual y con budgets deterministicos.
2. `Atlas Verifier Council`: adaptar blind review y chairman solamente para
   tareas high-risk, evidencia contradictoria o decisiones irreversibles. No
   usar multi-model por defecto.

La mejora mas valiosa no es autonomia. Es decision quality: saber cuando pensar
mas, cuando experimentar, cuando verificar con mas de una mirada y cuando parar.

No se recomienda copiar:

- el loop indefinido `NEVER STOP` de `autoresearch`;
- modificaciones autonomas de codigo core;
- `git reset`/branch advancing automatizado;
- OpenRouter o providers concretos;
- council en todas las preguntas;
- chairman premium por defecto;
- persistencia de conversaciones/respuestas de modelos sin redaccion.

Recomendacion final: `ADAPT`, con roadmap incremental y sin runtime en esta
fase.

## 2. Repositorios Inspeccionados

### Deep Inspection

| Repo | Commit inspeccionado | Motivo |
|---|---|---|
| `karpathy/autoresearch` | `228791fb499afffb54b46200aca536f79142f117` | Patron directo de experimentos autonomos con baseline, budget fijo y metrica objetiva |
| `karpathy/llm-council` | `92e1fccb1bdcf1bab7221aa9ed90f9dc72529131` | Patron directo de council, blind peer review y chairman synthesis |

Archivos leidos:

- `autoresearch/README.md`.
- `autoresearch/program.md`.
- `autoresearch/prepare.py`.
- `autoresearch/pyproject.toml`.
- `llm-council/README.md`.
- `llm-council/CLAUDE.md`.
- `llm-council/backend/council.py`.
- `llm-council/backend/config.py`.
- `llm-council/backend/openrouter.py`.
- `llm-council/backend/storage.py`.
- `llm-council/pyproject.toml`.

### Superficial Inspection

| Repo | Clasificacion | Razon |
|---|---|---|
| `rendergit` | INDIRECT_PATTERN_VALUE | Renderiza repos a una pagina/LLM view; relevante para context minimization y repo evidence packs |
| `reader3` | INDIRECT_PATTERN_VALUE | Lectura por capitulos para LLM; relevante como chunking/manual context discipline |
| `nanochat` | MODEL_TRAINING_ONLY with indirect metrics value | Leaderboard/time-to-capability y depth knob son utiles conceptualmente, pero el repo es training infra |
| `nanoGPT`, `llm.c`, `llama2.c`, `minGPT`, `micrograd`, `minbpe`, `makemore`, `nn-zero-to-hero`, `LLM101n` | EDUCATIONAL_ONLY / MODEL_TRAINING_ONLY | Valiosos para aprendizaje ML, no para arquitectura Atlas actual |
| `arxiv-sanity-*`, `covid-sanity`, `researchpooler`, `researchlei`, `scholaroctopus`, `paper-notes` | INDIRECT_PATTERN_VALUE | Busqueda/recomendacion academica; no se profundiza porque Atlas ya tiene benchmark/docs search surfaces |
| `hn-time-capsule`, `jobs`, `calorie`, `gitstats` | INDIRECT_PATTERN_VALUE | Aplicaciones LLM o visualizacion; no hay gap directo prioritario |
| `char-rnn`, `convnetjs`, `recurrentjs`, `reinforcejs`, `forestjs`, `svmjs`, `tsnejs`, `optim`, `tf-agent`, `pytorch-*`, `deep-vector-quantization` | EDUCATIONAL_ONLY / MODEL_TRAINING_ONLY | No aportan arquitectura segura para Atlas V4 |
| `cpython`, `transformers` forks | IRRELEVANT_TO_ATLAS | Forks no orientados a la decision architecture de Atlas |
| `ulogme`, `simple-amt`, `twoolpy`, `find-birds`, `lifejs`, `notpygamejs`, `scriptsbots`, `MatlabWrapper`, `EigenLibSVM`, `cryptos`, `randomfun`, `karpathy.github.io`, `karpathy` | IRRELEVANT_TO_ATLAS | Dominio externo o utilitario sin relacion demostrable |

## 3. Patrones Relevantes

| Patron | Repo origen | Lectura para Atlas |
|---|---|---|
| Controlled Experiment Loop | `autoresearch` | Muy valioso si se limita a experiments pequenos, metricados y reversibles |
| Fixed Budget | `autoresearch` | Directamente aplicable: max rounds, calls, files, duration, model class |
| Objective Metric | `autoresearch`, `nanochat` | Directamente aplicable: Decision Benchmark, risk precision, evidence completeness |
| Single editable surface | `autoresearch` | Adaptar como allowed_files minimo; nunca editar core sin scope explicito |
| KEEP/DISCARD discipline | `autoresearch` | Adaptar, con seguridad/evidence como condiciones duras |
| Blind peer review | `llm-council` | Adaptar solo para verifier conflicts/high risk |
| Chairman synthesis | `llm-council` | Adaptar como final verification, no como autoridad absoluta |
| Graceful degradation | `llm-council` | Util: council puede quedar INCONCLUSIVE sin fallar el sistema |
| Raw output inspectability | `llm-council` | Util: conservar evidencia/reviews para auditabilidad |
| Repo rendering/chunking | `rendergit`, `reader3` | WATCH: podria ayudar context minimization, pero no ahora |

## 4. Autoresearch Analysis

`autoresearch` declara un loop donde un agente modifica `train.py`, ejecuta
training por un tiempo fijo, mide `val_bpb`, conserva el cambio si mejora y
descarta si no mejora. La arquitectura es potente porque reduce arbitrariedad:
no se acepta "parece mejor"; se acepta menor `val_bpb`.

Elementos utiles:

- baseline antes del primer experimento;
- una metrica primaria objetiva;
- tiempo fijo para comparabilidad;
- una superficie editable;
- no modificar el harness de evaluacion;
- log tabular de resultados;
- criterio de simplicidad cuando la mejora es pequena;
- crash/OOM tratados como resultados, no como narrativa.

Riesgos para Atlas:

- el repo promueve autonomia indefinida;
- hace commits/resets como parte del loop;
- modifica codigo real;
- descarga datasets y depende de GPU;
- usa `results.tsv` no versionado;
- el agente puede intentar fixes durante crashes.

Decision: `ADAPT`, no adoptar literal.

## 5. LLM Council Analysis

`llm-council` consulta varios modelos por OpenRouter, anonimiza respuestas,
pide rankings cruzados y usa un chairman para sintetizar una respuesta final.

Elementos utiles:

- respuestas iniciales independientes;
- blind review para reducir favoritismo por modelo/proveedor;
- ranking parseable;
- aggregate ranking;
- chairman synthesis;
- mostrar raw reviews para transparencia;
- continuar si algunos modelos fallan.

Riesgos para Atlas:

- usa cuatro modelos por defecto;
- depende de OpenRouter y `.env`;
- hardcodea modelos/proveedores;
- aumenta costo y latencia;
- persiste conversaciones localmente;
- chairman recibe todo el contexto y puede convertirse en autoridad opaca;
- no esta pensado como gate de seguridad.

Decision: `ADAPT`, con activation gate fuerte.

## 6. Atlas Experiment Loop

Objetivo: permitir que Atlas compare estrategias bajo budget, metrica y rollback,
sin volverse autonomo.

Flujo propuesto:

```text
baseline
  -> hypothesis
  -> bounded scope
  -> fixed budget
  -> simulated or approved experiment
  -> objective metric
  -> compare against baseline
  -> KEEP / DISCARD / INCONCLUSIVE
```

Baseline requerido:

```json
{
  "state": {},
  "metrics": {},
  "tests": [],
  "estimated_cost": {},
  "context_used": [],
  "model_class": "",
  "evidence": []
}
```

Hypothesis contract:

```json
{
  "hypothesis": "",
  "expected_improvement": "",
  "metric": "",
  "budget": {},
  "scope": [],
  "risk": "",
  "rollback": ""
}
```

Bounded scope:

- `allowed_files`.
- `allowed_tools`.
- `allowed_commands`.
- `allowed_models`.
- `allowed_context`.
- `max_rounds`.
- `max_agents`.
- `max_tokens`.
- `max_time`.

Default:

```json
{
  "max_agents": 1,
  "max_model_calls": 3,
  "max_rounds": 1,
  "max_context_files": 4,
  "max_duration_seconds": 300,
  "max_cost_class": "balanced"
}
```

KEEP rule:

```text
metric improves
AND critical tests do not degrade
AND Decision Benchmark does not regress
AND security does not degrade
AND Evidence remains valid
```

Any degradation in security, Evidence or Decision Benchmark turns the result
into `DISCARD`, even if the local metric improves.

## 7. Atlas Verifier Council

Council activation is not a feature for everyday work. It is a high-friction
verification path for tasks where one verifier is not enough.

Activation candidates:

- security-critical;
- architecture-critical;
- release decision;
- irreversible operation;
- high uncertainty;
- verifier conflict;
- benchmark degradation;
- contradictory evidence.

Non-activation:

- README edits;
- typos;
- simple docs;
- small bounded code changes;
- trivial tests;
- routine formatting.

Architecture:

```text
Primary Agent
  -> Primary Result
  -> Risk / Confidence Gate
  -> Council needed?
     -> NO: single verifier
     -> YES: Verifier A + Verifier B
             -> blind comparison
             -> Chairman
             -> Final Verification
```

Council output:

```json
{
  "status": "AGREE|DISAGREE|INCONCLUSIVE",
  "candidate_count": 0,
  "consensus_score": 0.0,
  "critical_disagreements": [],
  "preferred_result": "",
  "evidence": [],
  "requires_human_review": false
}
```

Cost gate:

```text
expected_quality_gain > expected_additional_cost
```

Deterministic activation rules should use risk, novelty, evidence conflict and
benchmark degradation, not vibes.

## 8. Intelligence Escalation Ladder

Proposed ladder:

```text
LEVEL 0: deterministic rule
LEVEL 1: cheap_fast
LEVEL 2: balanced
LEVEL 3: premium_reasoning
LEVEL 4: premium + verifier
LEVEL 5: Verifier Council
LEVEL 6: Human Approval
```

Escalate only when:

- risk increases;
- confidence decreases;
- evidence conflicts;
- benchmark similarity is low;
- benchmark regression is observed;
- unknown action appears in Diagnostic Mode;
- Dangerous Command Policy returns WARN/DENY/UNKNOWN.

Never escalate only because a more expensive model might be better.

## 9. Confidence And Novelty Design

Decision confidence must not be fake probability. It should be derived from
deterministic signals.

Proposed output:

```json
{
  "decision": "",
  "confidence": 0.0,
  "evidence_strength": 0.0,
  "benchmark_similarity": 0.0,
  "risk": "",
  "novelty": ""
}
```

Deterministic signals:

- exact or token-overlap similarity to Decision Benchmark cases;
- number of matching routing rules;
- policy conflicts;
- Diagnostic Mode result;
- Dangerous Command Policy result;
- evidence availability;
- architecture domain status;
- prompt novelty.

Novelty classes:

- `KNOWN`: exact/near-exact benchmark match and no policy conflict.
- `SIMILAR`: overlaps with benchmark family but includes new terms/scope.
- `NOVEL`: weak benchmark overlap or new capability category.
- `UNKNOWN`: insufficient prompt/context.

Atlas should treat NOVEL/UNKNOWN prompts as less safe than prompts covered by
many benchmark cases.

## 10. Decision Experiment Registry

Future record shape:

```json
{
  "experiment_id": "",
  "hypothesis": "",
  "baseline": {},
  "candidate": {},
  "metric_before": {},
  "metric_after": {},
  "decision": "KEEP|DISCARD|INCONCLUSIVE",
  "cost": {},
  "evidence": [],
  "timestamp": ""
}
```

V1 recommendation: design only. Do not persist until the experiment loop has a
validated manual dry run and redaction rules.

## 11. Safe Adoption Matrix

| Patron | Repo origen | Gap Atlas | Beneficio | Riesgo | Token Impact | Complejidad | Decision |
|---|---|---|---|---|---|---|---|
| Controlled Experiment Loop | `autoresearch` | Atlas has calibrated decisions but no controlled improvement loop | Reduces arbitrary changes | High if autonomous | Neutral initially | Medium | ADAPT |
| Fixed Budget | `autoresearch` | Atlas needs hard limits for experiments/council | Prevents loops/cost blowups | Low | Positive | Low | ADOPT as design principle |
| Objective Metric / KEEP rule | `autoresearch`, `nanochat` | Atlas needs measurable improvement gates | Makes improvement falsifiable | Low | Neutral | Low | ADOPT as design principle |
| Single editable surface | `autoresearch` | Atlas changes can span too much surface | Better rollback and review | Low | Positive | Low | ADAPT |
| Autonomous endless loop | `autoresearch` | None | None for Atlas priorities | Extreme | Negative | High | REJECT |
| Blind peer review | `llm-council` | High-risk reviews can inherit model/agent bias | Reduces bias | Medium | Negative when overused | Medium | ADAPT |
| Chairman synthesis | `llm-council` | Conflicting verifier outputs need final consolidation | Useful for hard decisions | Medium | Negative | Medium | ADAPT |
| Multi-model default | `llm-council` | None | Marginal for routine tasks | High cost | Negative | Medium | REJECT |
| Raw review transparency | `llm-council` | Atlas needs traceability for council decisions | Auditable verification | Low | Neutral | Low | ADAPT |
| Repo rendering / LLM view | `rendergit` | Context surface is large | Could improve context packs | Medium if copied | Positive | Medium | WATCH |
| Chaptered reading | `reader3` | Long docs need chunking discipline | Helps context minimization | Low | Positive | Low | WATCH |

## 12. Anti-patterns

From `autoresearch`, do not copy:

- autonomous indefinite loops;
- self-modifying runtime;
- direct edits to Atlas core in an experiment;
- commit/reset automation;
- experiments without hypothesis;
- experiments without baseline;
- experiments without objective metric;
- non-versioned result files as source of truth;
- GPU/data/download requirements.

From `llm-council`, do not copy:

- multi-model on every question;
- four or more models by default;
- hardcoded provider/model names;
- OpenRouter integration in Atlas core;
- chairman premium always;
- full context exchange between all models;
- model identity exposure during blind review;
- persistent conversation storage without redaction.

## 13. Cost Analysis

Autoresearch cost risk:

- real training cost and GPU runtime;
- repeated experiments;
- indefinite loop;
- context cost from logs and failures.

Atlas adaptation:

- default one conceptual change;
- one round;
- max three model calls;
- max four context files;
- no runtime execution until approved;
- objective metric before any KEEP.

Council cost risk:

- N models in stage 1;
- N models in stage 2;
- chairman synthesis;
- large duplicated context.

Atlas adaptation:

- default no council;
- council only under explicit gates;
- max two verifiers plus one chairman;
- cap total models at three;
- record added tokens, latency and activation reason;
- prefer deterministic rules before LLM calls.

## 14. Security Analysis

Security posture for any future implementation:

- Diagnostic Mode must block mutating experiments during diagnostic phases.
- Dangerous Command Policy remains command danger classifier.
- Governance must remain unchanged until a separate approved integration.
- Evidence remains mandatory for PASS/KEEP.
- Secrets must not appear in council prompts or experiment records.
- MCP writes are out of scope.
- External providers are out of scope.
- Human approval is required for production, irreversible or high-risk actions.

No recommended pattern requires weakening existing security controls.

## 15. Architecture Impact

| Domain | Impact | Notes |
|---|---|---|
| Governance | POSITIVE | Adds measurable decision discipline if implemented as advisory contracts first |
| Evidence | POSITIVE | KEEP requires evidence and metric comparison |
| Dangerous Command Policy | POSITIVE | Becomes one signal in escalation/confidence |
| Diagnostic Mode | POSITIVE | Blocks mutation during diagnostic/experiment design phases |
| Decision Benchmark | POSITIVE | Becomes baseline/similarity source |
| Model Routing | POSITIVE | Gains escalation ladder and cost gate inputs |
| Agent Routing | NEUTRAL | No new agents needed initially |
| Context Minimization | POSITIVE | Fixed context budget and render/chunk ideas help |
| Failure Registry | POSITIVE | Failed experiments can become failure records later |
| Architecture State | POSITIVE | Can feed risk/confidence gate |
| MCP | NEUTRAL | No MCP runtime change recommended |
| CI | NEUTRAL | Future contracts can be tested without new workflows first |
| Dashboard | NEUTRAL | Metrics may later surface in dashboard |

No NEGATIVE impact is accepted for the recommended design-only path.

## 16. Target Architecture

```text
User Prompt
  -> Intelligent Orchestrator
  -> Decision Benchmark
  -> Novelty + Confidence Gate
  -> Intelligence Escalation Ladder
  -> Execution / Simulation Plan
  -> Optional Experiment Loop
  -> Optional Verifier Council
  -> Evidence
  -> Decision Registry
  -> Final Response
```

This extends Atlas. It does not replace current components.

## 17. Future Metrics

Decision Quality:

- routing accuracy;
- approval accuracy;
- risk precision;
- risk recall.

Intelligence Efficiency:

- average model class;
- premium escalation rate;
- council activation rate;
- unnecessary council rate.

Cost Efficiency:

- tokens/task;
- context/task;
- calls/task;
- estimated cost/task.

Experiment Quality:

- experiments attempted;
- KEEP rate;
- DISCARD rate;
- regression rate;
- inconclusive rate.

Safety:

- blocked unsafe experiments;
- side effects attempted;
- policy conflicts.

## 18. Prioritized Roadmap

P0: No implementation in this phase.

P1: Design-only `atlas_experiment_contract_v1`.

- Data-only schema for baseline, hypothesis, budget, scope, metric and decision.
- Unit tests only.
- No execution.

P1: Confidence/Novelty scoring prototype.

- Deterministic benchmark similarity against Decision Benchmark.
- No LLM calls.
- No routing enforcement.

P2: Escalation Ladder advisory.

- Map Diagnostic Mode, Dangerous Command Policy, risk, confidence and benchmark
  novelty to levels 0-6.
- No auto-switch.

P2: Manual Experiment Dry Run.

- Use one documentation/routing hypothesis.
- Compare a metric before/after.
- No autonomous loop.

P3: Verifier Council design contract.

- Output schema, activation criteria and cost gate.
- No provider integration.

P4: Optional dashboard/reporting.

- Only after manual evidence proves value.

## 19. Final Recommendation

Overall: `ADAPT`.

Recommended next implementation phase:

`atlas_experiment_contract_v1` as data-only + pure validator tests.

Do not build runtime, providers, OpenRouter integration, agent swarm, MCP writes
or autonomous experiments. Atlas should first learn to describe and reject bad
experiments before it runs any experiment.

The north star is not more autonomy. It is better stopping power:

- know when a prompt is known, similar, novel or unknown;
- know when deterministic rules are enough;
- know when a cheaper model is enough;
- know when evidence is weak;
- know when a verifier is needed;
- know when a council is worth the cost;
- know when the right answer is human approval or STOP.
