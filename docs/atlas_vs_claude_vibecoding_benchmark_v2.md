# Atlas vs Claude-Vibecoding Benchmark V2

Fecha: 2026-06-19

## 1. Executive Summary

Decision: mantener Codex-Atlas como base, conservar las adaptaciones ya verificadas y no implementar una nueva feature en esta fase.

El benchmark externo fue actualizado en sandbox desde `10fae5b` hasta `2f75af6` (`feat(observability): healthcheck unificado + drift-check + MCP registry`). Se auditaron estructura, agentes, hooks, MCPs, routing, prompts, memoria, seguridad, permisos, approvals, DX, testing, workflows, reporting, self-audit y checkpoints. No se copiaron archivos ni se ejecutaron installers, hooks globales, MCPs, Engram, deploys o herramientas con side effects.

Los tres nuevos componentes del benchmark tienen tests puros y esos tests pasan: healthcheck `10/10`, drift-check `8/8`, MCP registry `9/9`. La calidad local de esos helpers es real. Sin embargo, su semantica no puede importarse sin cambios:

- el healthcheck puede declarar `READY` con drift detectado y Engram ausente;
- un fallo de lectura del registry se convierte en WARN fail-open;
- el registry usa `LIVE` para MCPs cuya disponibilidad real depende de la sesion;
- drift-check compara un repo contra `~/.claude`, superficie global que Atlas no instala ni debe gobernar;
- Verification Levels permite saltar verificacion para `config`, incompatible con Evidence-first si se adopta literalmente.

El Intelligent Execution Gate rechazo una implementacion nueva. Return Envelope, command danger patterns, checkpoints, MCP compatibility y self-audit ya existen en Atlas con distintos grados de madurez. Agregar otra capa ahora sumaria duplicacion o estados ambiguos. El resultado correcto es documentar decisiones y mantener las candidatas restantes en WATCH/NEEDS_RESEARCH.

## 2. Repos Comparados

| Repo | Commit | Ubicacion | Uso |
|---|---|---|---|
| Codex-Atlas | `82a71f1` al iniciar | `D:\\Proyectos\\Codex-Atlas` | base gobernada |
| claude-vibecoding | `2f75af6` | `D:\\Proyectos\\_benchmark_sandbox\\claude-vibecoding` | referencia read-only |

El sandbox externo permanece separado. Ningun archivo externo fue copiado a Atlas.

## 3. Tabla de Paridad

| Area | Atlas | Claude-Vibecoding | Ganador | Motivo | Riesgo |
|---|---|---|---|---|---|
| Governance | checks canonicos, atlas_verify, policies testeadas | doctrina central + audit-system | Atlas | gates de repo y CI verificables | bajo |
| Evidence | contracts, bundle, report, browser artifact, freshness | Return Envelope y auto-audits de agentes | Atlas | evidencia transportable y estados controlados | bajo |
| Release engineering | RC1, tag, CI, global/manual workflows, reports | installer/update log; sin baseline equivalente Atlas | Atlas | trazabilidad de release mas fuerte | bajo |
| Runtime UX | herramientas explicitas, mostly manual/advisory | 25 agentes, hooks y pipelines integrados en Claude | Claude-Vibecoding | experiencia mas automatizada | alto por acoplamiento global |
| Return Envelope | contrato Codex-native + envelope del dispatcher | formato compartido obligatorio entre agentes | empate contextual | Atlas lo tiene operativo; benchmark lo aplica mas uniformemente | medio |
| Verification Levels | verificacion estructurada, sin taxonomia unica | `typo/layout/config/none` | Claude-Vibecoding | taxonomia simple y ergonomica | alto si `config/none` salta evidencia necesaria |
| Checkpoints | human approval, visual direction, stop rules | checkpoint humano y visual impact muy visibles | Claude-Vibecoding | mejor lenguaje operativo | medio por dependencia de prompts |
| Dangerous commands | policy pura, data-driven, 100 tests, advisory | hooks reactivos de bloqueo | Atlas | determinismo y desacoplamiento | regex no es parser completo |
| Secret guard | gitignore, registry validation, scans/tests, command policy | config-protection + quality gate + reality checker | Claude-Vibecoding en cobertura UX | defensa en varias fases | hooks globales y falsos positivos |
| MCP protocol | generic stdio diagnostic + policy-gated mem_doctor | MCPs asumidos por Claude runtime | Atlas | prueba protocolar y estados honestos | Atlas aun no tiene runtime productivo |
| MCP inventory | profiles, permission matrix, reality reports | nuevo JSON registry + summary CLI | Claude-Vibecoding en DX | resumen mas directo | `LIVE` puede no significar conectado |
| Health | dashboard con freshness + atlas_verify | healthcheck unificado manual | empate contextual | Atlas mas riguroso; benchmark mas rapido de leer | agregador externo es fail-open |
| Drift | governance/surface checks y git evidence | SHA256 repo vs `~/.claude` | Claude-Vibecoding para su instalacion | detecta desync de contenido instalado | no aplica al modelo repo-local Atlas |
| Model routing | policy advisory y tests | `model:` por agente + orquestador | Atlas | menor magia y sin auto-switch | menos automatico |
| Memory | file-backed; Engram sandbox/MCP parcial | Engram obligatorio + cloud/sync | Atlas en seguridad | no hay side effects ocultos | menos continuidad automatica |
| Testing | 722 tests, critical suite, CI | tests Node puros + audit funcional de hooks | Atlas | mayor cobertura de repo | suite mas amplia de mantener |
| CI | GitHub Actions observado | no es el centro del runtime | Atlas | evidencia remota reproducible | browser/global siguen manuales |
| Onboarding/DX | README y comandos, sobrio | installers y quickstart muy guiados | Claude-Vibecoding | menor friccion inicial | instala global y modifica entorno |
| Error handling | WARN/UNKNOWN/FAIL, Failure Registry | fallbacks y fail-open auxiliares | Atlas | estados mas conservadores | menos fluido en runtime interactivo |
| Reporting | dashboard, RC, MCP reality, architecture audit | session/cost/health summaries | empate contextual | Atlas mejor release; benchmark mejor sesion | telemetria externa/sensible |

## 4. Que Hace Mejor Atlas

1. Separa config, disponibilidad, prueba protocolar e integracion runtime.
2. No convierte una declaracion o binario presente en estado WORKING.
3. Tiene Evidence Pipeline, freshness, Failure Registry, governance y CI observada.
4. Mantiene integraciones externas advisory/disabled hasta tener prueba y policy.
5. Dangerous Command Policy es una libreria pura y testeada, no un hook global.
6. MCP diagnostics usa sandbox, allowlist y un unico `tools/call` read-only.
7. Conserva V3 RC1 como baseline y evita que V4 reescriba evidencia historica.
8. Prefiere WARN/UNKNOWN a PASS sin evidencia.

## 5. Que Hace Mejor Claude-Vibecoding

1. Onboarding y comando unico de health mas visibles.
2. Return Envelope aplicado de forma uniforme a muchos agentes.
3. Checkpoints humanos explicados con ejemplos operativos claros.
4. Secret checks distribuidos en pre-tool, quality gate y reality checker.
5. Drift SHA256 util para su modelo de repo fuente + instalacion global.
6. Registry MCP consultable y testeado como inventario declarativo.
7. Session summaries, cost reports y health de hooks mejoran DX interactiva.
8. Los nuevos helpers separan funciones puras del glue de I/O y tienen tests sin dependencias.

## 6. Que No Conviene Copiar

| Patron | Decision | Motivo |
|---|---|---|
| 25 agentes y pipeline completo | REJECT | superficie y prompt drift sin necesidad Atlas |
| hooks globales bajo `~/.claude` | REJECT | side effects globales y acoplamiento Claude-only |
| installer que modifica git/GitHub/Vercel | REJECT | rompe explicitud y approvals Atlas |
| Engram obligatorio/cloud sync | REJECT | memoria externa y writes ocultos |
| auto-deploy/auto-push | REJECT | viola Evidence/Verifier y approval |
| Pixel Bridge/runtime visual | REJECT | fuera del hardening del core |
| healthcheck READY con drift | REJECT | drift no puede quedar solo como WARN para claims fuertes |
| registry MCP `LIVE` declarativo | REJECT | availability por sesion debe probarse |
| registry ilegible fail-open READY | REJECT | Atlas debe producir UNKNOWN/WARN y negar claim fuerte |
| Verification `config` = saltar todo | REJECT literal | config tambien necesita schema/tests/diff checks |
| drift contra config global | REJECT | Atlas no instala una copia runtime global |

## 7. Decision Gate

El gate se aplico a las siete prioridades sugeridas.

| Idea | Mejora real | Solape Atlas | Riesgo | Alternativa simple | Decision | Implementar ahora |
|---|---|---|---|---|---|---|
| Return Envelope estandar | si | ya existe en dispatcher y operational parity | duplicar contratos | endurecer tests cuando aparezca un consumidor real | ADAPT, ya realizado | no |
| Verification Levels | potencial | verificacion ya estructurada | taxonomia externa permite omitir checks | disenar niveles Atlas evidence-aware primero | NEEDS_RESEARCH | no |
| Checkpoint Library | potencial | human approval + visual checkpoint + stop rules | otra policy sin consumidor | mejorar docs existentes en fase DX | WATCH | no |
| Secret Guard advisory | si | Dangerous Policy, Failure Registry, gitignore y scans | duplicacion y falsa cobertura | ampliar tests del clasificador existente | ADAPT, parcial existente | no |
| Catalog Drift Check | potencial | governance y surface audit ya detectan drift estructural | otra fuente de verdad | agregar checks concretos solo al hallar drift repetido | WATCH | no |
| DX command map | si | README y manual quality bundle ya listan comandos | duplicacion documental | indexar docs en futura pasada P2 | WATCH | no |
| MCP compatibility matrix | si | docs MCP protocol/reality + permission matrix | registry manual stale | usar reports con evidencia/freshness | ADAPT, ya realizado | no |

### Preguntas obligatorias del gate

1. **Mejora estabilidad o suma complejidad:** ninguna feature nueva demostro una ganancia neta inmediata.
2. **Compatibilidad Atlas:** solo los principios son compatibles; los hooks/global runtime no.
3. **Riesgo V3:** nuevas capas de envelope/readiness podrian alterar contratos que ya pasan RC1.
4. **Alternativa simple:** conservar tools actuales y documentar gaps concretos.
5. **Advisory-first:** Atlas ya usa ese patron en routing, dangerous commands y MCP.
6. **Tests claros:** posibles, pero falta un consumidor que justifique nueva API.
7. **Rollback:** docs-only es rollback trivial; una nueva capa contractual no lo seria.
8. **Aprobacion humana:** cualquier enforcement, hook, MCP productivo o cambio de runtime la requiere.

Resultado: `NO_IMPLEMENTATION_JUSTIFIED`.

## 8. Decision Records

### Return Envelope

```json
{
  "idea": "Standard Return Envelope",
  "source": "claude-vibecoding",
  "decision": "ADAPT",
  "why": "Improves handoff clarity and is already implemented by Atlas dispatcher and operational parity docs.",
  "risk": "A second schema would create drift.",
  "atlas_fit": "Existing Codex-native envelope with status, files, verification, blockers and notes.",
  "implementation_scope": "No new implementation; keep the current contract and extend only with a proven consumer.",
  "requires_human_approval": false,
  "tests_required": ["dispatcher envelope contract", "operational parity readiness"],
  "rollback_plan": "No change in V2."
}
```

### Secret Guard Pattern

```json
{
  "idea": "Advisory secret guard",
  "source": "claude-vibecoding",
  "decision": "ADAPT",
  "why": "Secret detection improves safety, but Atlas already covers command literals, failure records, ignored dotenv files and audit scans.",
  "risk": "A new scanner could duplicate patterns, retain secret values or create false confidence.",
  "atlas_fit": "Extend existing deterministic policies and tests instead of adding hooks.",
  "implementation_scope": "Future false-negative tests against current classifiers; no hook or enforcement.",
  "requires_human_approval": true,
  "tests_required": ["redaction tests", "false-positive fixtures", "false-negative fixtures", "no-secret-persistence test"],
  "rollback_plan": "Remove only added declarative patterns and tests if precision regresses."
}
```

### MCP Compatibility Inventory

```json
{
  "idea": "Machine-readable MCP compatibility inventory",
  "source": "claude-vibecoding",
  "decision": "ADAPT",
  "why": "A terse inventory improves DX, while Atlas already has profiles, permission matrix and evidence reports.",
  "risk": "Manual LIVE labels become stale and overdeclare connectivity.",
  "atlas_fit": "Any future inventory must derive effective state from evidence plus freshness, not a hand-written LIVE field.",
  "implementation_scope": "No new registry now; research a read-only projection from existing configs and observations.",
  "requires_human_approval": true,
  "tests_required": ["missing observation remains UNKNOWN", "stale evidence cannot remain WORKING", "config-only never becomes connected"],
  "rollback_plan": "Keep current MCP reality reports and permission matrix as sources of truth."
}
```

## 9. Patrones Nuevos del Commit 2f75af6

### Unified Healthcheck

Decision: `WATCH`.

La UX de un comando es buena, pero Atlas ya tiene `atlas_verify` y Health Dashboard. El agregador externo considera drift y Engram ausente como WARN y sigue READY. Atlas no debe adoptar ese verdict. Una futura mejora DX podria presentar ambos reportes sin cambiar sus estados ni crear un tercer health authority.

### SHA256 Drift Check

Decision: `REJECT` directo, `WATCH` como principio.

Es correcto para un sistema que instala agentes/hooks desde repo hacia `~/.claude`. Atlas es repo-local y prohibe global hooks/config. Governance, surface audit y Git ya cubren su drift relevante. Solo se justificaria un hash check para artifacts derivados con una relacion fuente-copia real y documentada.

### MCP Registry

Decision: `NEEDS_RESEARCH`.

El schema y sus tests son simples y utiles. El problema es epistemico: `LIVE` no debe ser una propiedad manual si la conexion depende de la sesion. Atlas necesita separar `configured`, `binary_present`, `protocol_validated`, `connected_now`, `policy_allowed` y `freshness`. Los MCP reality reports actuales son mas honestos, aunque menos tersos.

## 10. Que Se Implemento

No se implemento codigo, config, policy, hook, MCP, agente, runtime ni workflow.

Se creo este benchmark V2 con:

- referencia actualizada al commit externo `2f75af6`;
- prueba real de sus tres suites nuevas (`27 PASS` total);
- tabla de paridad;
- Decision Gate;
- decision records para adaptaciones existentes/futuras;
- rechazo explicito de semanticas incompatibles.

Esta no-implementacion es deliberada: evita duplicar Return Envelope, Health, MCP reality y Governance.

## 11. Que Se Rechazo

- copiar helpers JS o sus tests;
- crear un segundo healthcheck;
- crear un registry MCP manual con `LIVE`;
- comparar Atlas contra `~/.claude`;
- activar hooks o installers;
- introducir Verification Levels browser-first;
- integrar Engram, Context7 o Playwright al runtime;
- agregar agentes o loops automaticos.

## 12. Que Quedo Para Investigar

| Tema | Estado | Condicion para avanzar |
|---|---|---|
| Verification Levels Atlas-native | NEEDS_RESEARCH | semantica evidence-aware y consumidor concreto |
| MCP inventory projection | NEEDS_RESEARCH | derivar estado de evidencia/freshness, no labels manuales |
| Unified health UX | WATCH | demostrar que reduce operacion sin nueva autoridad de estado |
| Catalog/content drift | WATCH | hallar un drift repetido que governance no detecte |
| Checkpoint taxonomy | WATCH | integrar en contrato existente sin nueva policy |
| Secret false-negative expansion | WATCH | corpus de bypasses y redaccion segura |

## 13. Riesgos

1. Convertir DX tersa en falso PASS.
2. Duplicar fuentes de verdad para health, MCP y envelopes.
3. Confundir tests de schema con prueba de conectividad.
4. Importar fail-open donde Atlas requiere UNKNOWN/WARN controlado.
5. Hacer de Engram un requisito por imitacion arquitectonica.
6. Agregar taxonomias sin consumidores y aumentar maintenance.
7. Permitir que prompts/hook conventions sustituyan Evidence/Verifier.

## 14. Proximas Fases Seguras

1. Mantener Atlas como base y `v3.0.0-rc1` intacto.
2. No implementar nada de este benchmark sin un issue/propuesta con consumidor real.
3. Si MCP inventory se prioriza, definir primero un contrato derivado de evidence + freshness.
4. Si Verification Levels se prioriza, prohibir que `config` o `none` signifiquen automaticamente “sin checks”.
5. Si se mejora DX de health, presentar `atlas_verify` + dashboard sin fusionar ni suavizar estados.
6. Repetir critical/global/governance/CI para cualquier futura adaptacion.

## 15. Recomendacion Final

No fusionar arquitecturas y no implementar una nueva capa en esta fase.

Claude-Vibecoding sigue siendo una referencia valiosa para UX operativa, protocolos de agentes y herramientas manuales. Atlas sigue siendo la base mas adecuada para estabilidad, evidencia, release engineering y seguridad progresiva.

La mejora mas importante de este benchmark no es codigo: es rechazar estados `READY`/`LIVE` que no alcanzan el umbral de evidencia Atlas.
