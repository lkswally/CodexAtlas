# Intelligent Orchestrator V1

## Estado

V1 es un simulador advisory, deterministico y sin runtime. No ejecuta comandos, agentes, modelos, MCPs, workflows ni writes. No esta conectado a Dispatcher, Planner, Evidence Pipeline o Model Routing runtime.

## Proposito

La fase coordina contratos que Atlas ya tiene sin crear un loop autonomo:

1. recibe una tarea;
2. clasifica intent, riesgo, complejidad, impacto, tools, evidence y costo;
3. consulta un Decision Gate;
4. recomienda clase de modelo;
5. recomienda de uno a tres roles;
6. entrega contexto minimo;
7. valida Return Envelopes;
8. consolida resultados provistos por el caller.

Todo resultado es una simulacion. `runtime_execution` siempre es `false`.

## Architecture State Model

`tools/architecture_state_model.py` construye un estado explicito para:

- Governance
- Evidence
- MCP
- Skills
- Agents/Roles
- Workflows
- Security
- Tests
- Docs
- Dashboard
- Model Routing
- Failure Registry
- Release

Cada dominio expone:

```json
{
  "status": "PASS|WARN|FAIL|UNKNOWN",
  "evidence": [],
  "freshness": {},
  "risks": [],
  "dependencies": [],
  "confidence": 0.0,
  "next_actions": []
}
```

Reglas conservadoras:

- un dominio ausente queda `UNKNOWN`;
- `PASS` sin evidence se rechaza a `UNKNOWN`;
- `PASS` con `freshness.is_stale=true` baja a `WARN`;
- cualquier `FAIL` hace overall `FAIL`;
- mezcla de PASS y UNKNOWN hace overall `WARN`;
- no consulta dashboard, GitHub, red ni filesystem por si mismo.

El modelo recibe observaciones de un caller. No inventa ni recolecta evidencia.

## Intake Y Decision Gate

El intake usa keywords transparentes y longitud acotada. No usa LLM. Clasifica:

- task type;
- risk level;
- complexity;
- impact;
- tool needs;
- whether multiple roles add value;
- evidence requirement;
- expected cost.

Si el prompt es vacio o demasiado vago, el simulador emite una sola pregunta y no asigna roles. No existe una segunda ronda automatica.

El Decision Gate bloquea antes de asignar roles cuando:

- Dangerous Command Policy devuelve `DENY`;
- Governance o Security estan `FAIL` en Architecture State;
- la tarea carece de contexto critico.

Comandos `WARN` o `UNKNOWN` requieren aprobacion humana. UNKNOWN nunca se trata como SAFE.

## Model Routing

V1 recomienda clases, no proveedores ni modelos hardcodeados:

| Condicion | Clase |
|---|---|
| simple y low-risk | `cheap_fast` |
| moderada | `balanced` |
| arquitectura compleja o high-risk | `premium_reasoning` |
| codigo complejo | `code_specialist` |
| verificacion | `verifier` |
| resumen puro | `summarizer` |

Cada resultado registra clase, razon, cost sensitivity y risk level. Esta recomendacion no cambia el modelo activo y no modifica Model Routing V1 existente.

## Agent Routing

Roles permitidos:

- Planner
- Executor
- Verifier
- Evidence Reporter
- Security Reviewer
- MCP Specialist
- Documentation Specialist
- Release Reviewer
- Failure Recorder
- Orchestrator

Una tarea simple recibe un rol. Una tarea compleja o de alto riesgo puede recibir hasta tres. Los roles no conversan entre si y no se lanzan procesos.

Cada assignment contiene solo objetivo, hasta cuatro relevant files, estados de hasta cuatro dominios relacionados, restricciones y campos esperados del Return Envelope. El caller decide cuales archivos son relevantes; el simulador no escanea todo el repo.

## Return Envelope

Contrato exacto:

```json
{
  "agent": "",
  "status": "PASS|WARN|FAIL|BLOCKED",
  "summary": "",
  "evidence": [],
  "changes": [],
  "risks": [],
  "recommendation": "",
  "needs_followup": false
}
```

PASS requiere evidence. La consolidacion usa el peor estado, deduplica evidence/changes/risks y marca follow-up ante cualquier resultado no PASS.

La salida incluye un verification_plan fijo para revisar evidence, riesgos, tests/checks, cambios y consistencia documental. failure_registry_review_required se activa ante blockers o un resultado consolidado FAIL/BLOCKED; no escribe el registry.

## Uso

```python
from tools.architecture_state_model import build_architecture_state
from tools.intelligent_orchestrator import simulate_orchestration

state = build_architecture_state(
    {
        "governance": {
            "status": "PASS",
            "evidence": ["atlas_governance_check:ok"],
            "confidence": 1.0
        }
    }
)

plan = simulate_orchestration(
    "Review a bounded documentation change",
    relevant_files=["README.md"],
    architecture_state=state
)
```

El ejemplo conserva los otros dominios en UNKNOWN; por eso el overall state no se eleva artificialmente a PASS.

## Loop Prevention

- una sola ronda de decision;
- una sola pregunta de clarificacion;
- maximo tres roles;
- roles sin conversacion automatica;
- no retries;
- no tool execution;
- no recursive delegation;
- no self-modification.

## Limites

- La clasificacion por keywords es explicita pero no comprende semantica compleja.
- No estima tokens ni costo monetario real.
- No elige un modelo concreto.
- No prueba que un agent assignment haya sido ejecutado.
- No escribe Failure Registry.
- No consume MCPs.
- No convierte advisory en enforcement.
- No declara una integracion WORKING.

## Siguiente Gate

Antes de integrar con runtime se necesita evidencia de uso manual repetido, un consumidor concreto, audit trail, redaccion de secretos, approval boundaries y pruebas end-to-end que demuestren que la coordinacion reduce trabajo sin ocultar decisiones.
