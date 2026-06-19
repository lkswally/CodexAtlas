# Atlas vs Claude-Vibecoding Benchmark V1

Fecha: 2026-06-19

## Executive Summary

Decision: mantener Codex-Atlas como base y adaptar piezas puntuales de `claude-vibecoding`; no fusionar arquitecturas.

`claude-vibecoding` es un sistema Claude-first orientado a ejecucion creativa end-to-end: muchos agentes, hooks reactivos, MCPs globales, memoria Engram obligatoria y una experiencia de instalacion/onboarding muy guiada. Su fortaleza esta en DX, checkpoints humanos, hooks de seguridad/calidad y protocolos operativos para agentes.

Codex-Atlas es mas estable para un baseline gobernado: tiene tests locales, CI, evidencia formal, dashboard, failure registry, model routing advisory y MCP diagnostics con policy read-only. Su fortaleza esta en verificabilidad, trazabilidad, aislamiento de integraciones y release discipline.

El benchmark recomienda adaptar solamente patrones que fortalezcan seguridad, mantenibilidad y operacion de Atlas sin convertirlo en un runtime Claude-only ni habilitar auto-ejecucion.

Repo comparado:

- URL: `https://github.com/Emaleo0522/claude-vibecoding/tree/main`
- Commit auditado en sandbox: `10fae5b`
- Sandbox local: `D:\\Proyectos\\_benchmark_sandbox\\claude-vibecoding`
- No se copiaron archivos al repo de Atlas.

## Tabla de paridad

| Area | Codex-Atlas | claude-vibecoding | Benchmark |
|---|---|---|---|
| Arquitectura base | Repo gobernado, evidence-first, no runtime autonomo | Runtime Claude-first con agentes y hooks globales | Atlas es mas apto como baseline estable; vibecoding es mas apto como experiencia interactiva Claude |
| Agentes | Agentes documentales y workflows gobernados | 25 agentes especializados con frontmatter y protocolo compartido | ADAPT: return envelope/protocol checks, no copiar agentes |
| Agent loops | Manual Agent Loop, evidence/verifier boundaries | Pipeline 5 fases con dev-QA loop y checkpoints humanos | ADAPT: checkpoints/stop rules como policy verificable |
| MCPs | Reality check, protocol validation, read-only `tools/call` sandbox, no config global | Engram/Context7/Playwright configurados como runtime tools | WATCH: ideas utiles, pero demasiado acopladas a Claude runtime |
| Model routing | Advisory, config/tested | Frontmatter `model:` por agente | ADAPT: catalogar intentos por clase de trabajo, no auto-switch |
| Seguridad | Governance, external tool policies, secret rejection in Failure Registry, MCP read-only policy | Hooks bloquean `--no-verify`, force push, destructive rm, secrets edits, remote pipe-to-shell | ADOPT/ADAPT: patterns de denylist como checks Atlas, no hooks globales automaticos todavia |
| Filesystem boundaries | Derivados separados, bootstrap limitado a `output_dir`, no global config | Installer copia a `~/.claude`, settings globales, permisos amplios | REJECT: no adoptar instalacion global como default |
| Approvals | Human approval policies, manual release gates | Checkpoints para visual/multi-opcion/irreversible, deploy/git con confirmacion | ADAPT: formalizar triggers de checkpoint como policy/test |
| Testing | Suite local, critical tests, CI, compileall, diff check | Self-audit JS para instalacion; proyectos generados recomiendan tests/CI | Atlas mejor en repo-level CI; vibecoding mejor en runtime self-audit UX |
| CI | Atlas CI y workflows observados | No se encontro `.github` en repo raiz; CI se genera para proyectos derivados | Atlas mejor para baseline |
| Docs/DX | Release docs y comandos de verificacion; mas sobrio | README/Windows/Linux install muy guiados, quickstart fuerte | ADAPT: mejorar onboarding operativo de Atlas sin instalador global |
| Error handling | Failure Registry, controlled WARN/UNKNOWN, freshness policy | Hooks fail-open, retry/fallback docs, Engram fallback-to-disk pattern | ADAPT: graceful degradation docs; REJECT fail-open como unica defensa |
| Logging/observabilidad | governance/mcp/routing/project logs; dashboard | cost-tracker, session-summary, learning-index | ADAPT: local operation log summaries, no token-cost claims sin data |
| Memoria | File-backed + Engram deferred/proven diagnostics | Engram mandatory, cloud sync, cross-Claude mailbox | WATCH/REJECT: memory ideas interesting but high operational risk |
| Comandos de operacion | Python CLIs validated by tests | Node hook utilities and install scripts | ADAPT: small read-only health utilities only |

## Que hace mejor Atlas

1. **Release discipline y verificabilidad.** Atlas tiene RC1, tag `v3.0.0-rc1`, suite local, CI observado, dashboard, governance y `atlas_verify`.
2. **Separacion entre advisory y working.** Las integraciones externas no se declaran working sin prueba real; MCP se valido por fases.
3. **Evidence-first.** Las claims pasan por Evidence Pipeline, health dashboard, failure registry y checks reproducibles.
4. **Aislamiento de riesgos.** No escribe config global Claude/Codex, no activa MCPs globales y no convierte Engram en runtime memory sin policy.
5. **Contratos testeables.** Herramientas Python tienen tests y salidas JSON/Markdown estables.
6. **Postura de seguridad mas conservadora.** Atlas prefiere `UNKNOWN/WARN` antes que `PASS` sin evidencia.

## Que hace mejor claude-vibecoding

1. **DX de onboarding.** README, Windows guide e installer explican un camino humano de instalacion y verificacion.
2. **Hooks practicos de seguridad.** `block-no-verify`, `config-protection` y `quality-gate` codifican riesgos comunes de forma concreta.
3. **Protocolos de agente muy claros.** `agent-protocol.md` define return envelope, verification levels y visual impact.
4. **Checkpoints humanos bien nombrados.** Distingue decisiones tecnicas deducibles de decisiones visuales/interpretable/irreversibles.
5. **Observabilidad de sesion.** Tiene cost/session logs y reportes operativos locales.
6. **Fail-soft en herramientas auxiliares.** Algunos hooks son warnings no bloqueantes, utiles para no romper flujo interactivo.
7. **Self-audit de instalacion.** `audit-system.js` valida catalogo, hooks, settings y performance de hooks.

## Gaps reales de Atlas

| Gap | Impacto | Clasificacion |
|---|---|---|
| No existe un catalogo ejecutable de reglas peligrosas tipo command denylist fuera de policies documentales | Seguridad operacional mejorable | ADAPT |
| No hay equivalente directo a `Return Envelope` para resultados de agentes/workflows Atlas | Mantenibilidad y handoff mejorables | ADAPT |
| Onboarding publico podria ser mas guiado | DX mejorable | ADAPT |
| No hay reporte compacto de actividad operacional por sesion | Operacion/debug posterior mejorable | WATCH |
| Visual/UI pre-return checks existen como policies/readiness, pero no estan empaquetados como utility manual simple | DX de QA visual mejorable | ADAPT |
| MCP runtime audit logs para `tools/call` aun son diagnosticos, no policy-grade audit trail | Seguridad y trazabilidad futura | ADAPT |

## Riesgos de importar ideas

| Riesgo | Motivo | Clasificacion |
|---|---|---|
| Copiar hooks globales Claude | Tocan `~/.claude`, dependen del runtime Claude y pueden sorprender al usuario | REJECT |
| Adoptar Engram como memoria obligatoria | Atlas acaba de probar MCP read-only, pero memoria read/write sigue sin gates suficientes | REJECT |
| Copiar 25 agentes | Aumenta superficie, prompt drift y maintenance sin evidencia de necesidad en Atlas | REJECT |
| Activar Context7/Playwright/Vercel MCPs por default | Incrementa permisos y dependencia externa | REJECT |
| Usar installers que instalan Node/Vercel/gh/global git config | Rompe regla Atlas de no instalar dependencias ni tocar global sin aprobacion | REJECT |
| Fail-open como unica barrera | Sirve para UX, no para governance/release claims | REJECT/ADAPT: solo warnings auxiliares, no gates |
| Cross-Claude mailbox | Interesante pero implica memoria cloud, coordinacion externa y riesgo de auto-aplicar cambios | WATCH |
| Pixel Bridge | UI runtime grande y ajeno al core Atlas | REJECT para V4 hardening |

## Patrones recomendados para adaptar

| Patron | Decision | Adaptacion segura para Atlas |
|---|---|---|
| Command danger denylist (`--no-verify`, force push, `rm -rf`, `git reset --hard`, remote pipe-to-shell, destructive SQL) | ADAPT | Crear en fase futura un check local/manual, testeado, sin hooks globales; integrarlo a governance solo tras pruebas |
| Secret/config edit guard | ADAPT | Extender policy/readiness de secrets como scanner local testeado; no interceptar ediciones aun |
| Return Envelope | ADAPT | Definir formato Atlas para outputs de workflows/agentes: status, files, evidence, blockers, verification, risk |
| Verification levels (`typo/layout/config/none`) | ADAPT | Mapear a Evidence Pipeline/Verifier como metadata documental primero |
| Visual impact checkpoint | ADAPT | Convertir en policy de approval para cambios visuales, sin agentes nuevos |
| Self-audit catalog checks | ADAPT | Atlas ya tiene governance; se puede agregar una seccion futura para MCP/tool-policy catalog drift |
| Cost/session operation summary | WATCH | Util si se implementa como log local no invasivo y sin datos sensibles |
| Graceful degradation | ADAPT | Atlas ya usa WARN/UNKNOWN; documentar patrones por integracion |
| Design pre-return utility | ADAPT | Atlas ya tiene anti-generic/design policies; empaquetar como utility manual podria mejorar DX |
| Engram project explicitness | WATCH | Aplicable solo si Atlas avanza a memory runtime; por ahora no adoptar |

## Patrones rechazados

| Patron | Decision | Razon |
|---|---|---|
| Instalacion global en `~/.claude` como flujo Atlas | REJECT | Atlas es repo gobernado Codex-native, no paquete Claude global |
| MCPs globales por default | REJECT | Contradice MCP Reality Check y read-only policy gradual |
| Engram Cloud obligatorio | REJECT | Demasiado acoplamiento externo, secretos/infra y sync risk |
| Subagentes como feature importada | REJECT | Atlas no necesita mas agentes para robustez; necesita contracts y gates |
| Pixel Bridge | REJECT | Feature visual/IDE fuera de objetivo hardening |
| Auto-deploy / auto-push | REJECT | Atlas mantiene approval y evidence gates |
| Hooks que modifican/sincronizan memoria al Stop | REJECT | Side effects ocultos; Atlas exige explicitud |
| Installer que instala dependencias globales | REJECT | Rompe no-dependencies/no-global-config posture |

## Backlog seguro

### P0: seguridad/estabilidad

- Ningun P0 detectado en Atlas a partir del benchmark.

### P1: robustez

- ADAPT: disenar `dangerous_command_patterns` como policy + tests, basado en ideas de `block-no-verify`, pero sin hooks globales.
- ADAPT: agregar audit trail estructurado para futuros MCP `tools/call`: tool, policy, input hash/redaction, result status, side_effects_expected.
- ADAPT: formalizar `UNKNOWN/WARN` para integraciones externas con graceful degradation por defecto.

### P2: DX/mantenibilidad

- ADAPT: documentar un Atlas Return Envelope para workflows/agents sin crear agentes nuevos.
- ADAPT: crear una pagina de onboarding operativo: comandos minimos, health, governance, tests, MCP diagnostics.
- ADAPT: convertir algunos checks visuales/prompt-safety en utility manual local si ya existen policies y fixtures.
- ADAPT: catalog drift check para configs/policies/docs similar al self-audit, aprovechando governance existente.

### P3: mejoras opcionales

- WATCH: resumen local de actividad de sesion, sin tokens/secrets, append-only y opt-in.
- WATCH: decision record index para benchmark decisions en `memory/decision_log.md` o docs, no Engram obligatorio.
- WATCH: Context7 as advisory read-only docs source only after MCP policy expands.

### P4: ideas futuras

- NEEDS_RESEARCH: cross-machine coordination protocol sin memoria cloud obligatoria.
- NEEDS_RESEARCH: UI audit helper inspired by `pre-return-audit.sh`, but implemented as Atlas Python tool with tests.
- NEEDS_RESEARCH: model routing telemetry comparing advisory recommendations vs outcomes.

## Plan de adopcion seguro

1. No importar codigo ni prompts completos.
2. Abrir una propuesta pequena por patron, empezando por dangerous-command policy.
3. Para cada propuesta exigir: policy, tests, docs, no global config, no runtime auto-execution.
4. Mantener cada cambio como utility manual o governance check antes de cualquier hook/runtime integration.
5. Validar con critical tests, governance, atlas_verify, compileall, diff check y Atlas CI.
6. Promover a blocking solo si reduce riesgo sin falsos positivos altos y con fallback documentado.

## Recomendacion final

Mantener Atlas como arquitectura base.

Adaptar piezas puntuales de `claude-vibecoding` donde refuercen seguridad, DX y mantenibilidad: command denylist, return envelope, checkpoint taxonomy, self-audit ideas y algunos pre-return audit patterns.

No fusionar arquitecturas. `claude-vibecoding` es un sistema runtime Claude global; Atlas es un baseline gobernado, evidence-first y Codex-native. Importar el runtime completo debilitaria trazabilidad y aumentaria permisos antes de tener gates suficientes.

## Hallazgos clasificados

| Hallazgo | Clasificacion | Razon |
|---|---|---|
| Command danger patterns | ADAPT | Alta mejora de seguridad, testeable, no requiere runtime global |
| Secret/config edit protection | ADAPT | Buena defensa si se implementa como scanner/policy local |
| Return Envelope | ADAPT | Mejora handoffs sin agregar agentes |
| Verification levels | ADAPT | Encaja con Evidence/Verifier |
| Visual impact checkpoint | ADAPT | Mejora approval boundaries |
| Self-audit installer checks | ADAPT | Atlas governance puede absorber version repo-local |
| Cost/session report | WATCH | Util, pero debe evitar datos sensibles y claims de costo no medido |
| Engram read/write memory protocol | WATCH | Atlas aun no debe activar memory runtime |
| Cross-Claude mailbox | WATCH | Alto acoplamiento externo, potencial futuro solo con policy fuerte |
| Global Claude hooks | REJECT | Demasiado acoplado y side-effectful |
| MCPs globales default | REJECT | Contradice realidad MCP actual de Atlas |
| 25-agent pipeline | REJECT | No mejora robustez de Atlas; aumenta maintenance |
| Pixel Bridge | REJECT | Feature ajena al hardening operativo |
| Installer global | REJECT | Modifica sistema del usuario y dependencias globales |
| Automatic deploy/push | REJECT | Choca con evidence/approval gates |

## Evidencia de auditoria

- `claude-vibecoding` clonado en sandbox externo y auditado read-only.
- Se revisaron `README.en.md`, `CLAUDE.md` por busqueda, `agents/agent-protocol.md`, `agents/PIPELINE-AGENTS.md`, templates de settings/MCP, hooks de seguridad/calidad/costo y scripts de instalacion.
- Se comparo contra README/ARCHITECTURE/RC1/MCP Reality/MCP Protocol/Health Dashboard de Atlas.
- No se ejecutaron installers, hooks mutantes, MCPs externos ni herramientas del repo externo.
