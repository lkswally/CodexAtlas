# Diagnostic Mode Usage

Fecha: 2026-07-29.

Estado: capacidad deterministica minima, advisory-only. No crea runtime, agentes,
hooks, workflows automaticos, MCP, sandbox del sistema operativo ni auto-fix.

## 1. Que Es

Diagnostic Mode es un contrato read-only para tareas de auditoria, diagnostico,
inspeccion, benchmarking, reality check, health check y analisis arquitectonico.

Su regla central:

```text
Diagnostic Mode observa, verifica, registra evidencia y recomienda.
Diagnostic Mode no corrige.
```

La configuracion data-only vive en `config/diagnostic_mode_checklist.json`.
El evaluador deterministico vive en `tools/diagnostic_mode.py`.

## 2. Que Problema Resuelve

Atlas ya tiene Evidence, Governance, Failure Registry, Model Routing y Agent
Loop manual. El gap era operativo: una tarea de auditoria podia derivar hacia
implementacion si el usuario no repetia explicitamente "no implementar".

Diagnostic Mode convierte esa frontera en contrato testeable:

- acciones read-only pueden ser `ALLOW`;
- acciones mutantes son `BLOCK`;
- acciones ambiguas quedan `UNKNOWN`, y el consumidor debe bloquearlas;
- PASS requiere evidencia.

## 3. Cuando Usarlo

Usarlo cuando la tarea sea:

- diagnostico;
- auditoria;
- inspeccion;
- benchmark;
- reality check;
- health check;
- analisis de arquitectura;
- revision de consistencia;
- investigacion previa a una fase de implementacion.

No usarlo cuando el usuario ya aprobo una fase de implementacion con archivos y
checks concretos.

## 4. Que Permite

Diagnostic Mode permite acciones inequivocamente read-only:

- leer archivos;
- listar archivos;
- inspeccionar `git status`;
- inspeccionar `git diff`;
- ejecutar tests read-only;
- ejecutar `compileall`;
- ejecutar governance checks;
- ejecutar `atlas_verify`;
- consultar MCP `tools/list`;
- consultar MCP read-only allowlisted con metadata explicita;
- analizar logs;
- generar hallazgos en memoria;
- preparar reporte sin persistirlo todavia.

## 5. Que Bloquea

Diagnostic Mode bloquea:

- modificar, crear, borrar o mover archivos;
- instalar o actualizar dependencias;
- `git commit`;
- `git push`;
- `git reset`;
- `git clean`;
- deploy;
- cambios de secrets;
- cambios de config;
- cambios de workflow;
- MCP write;
- memory write;
- database write;
- auto-fix;
- runtime integration.

Tambien bloquea por ambiguedad operativa: comandos no clasificados, MCP sin
metadata de side effects, red sin naturaleza read-only comprobada y herramientas
externas sin contrato read-only.

## 6. Interaccion Con Orchestrator

Integracion permitida: advisory-only.

Cuando una tarea esta marcada como diagnostic, el Orchestrator puede incluir
Diagnostic Mode como precondition en el plan. No debe ejecutar acciones por el
checklist. Debe usarlo para decidir si una accion propuesta pertenece al scope
read-only.

Dentro de Diagnostic Mode no existe escalation a ejecucion. Para corregir,
implementar, commitear o pushear, la tarea debe salir explicitamente de
Diagnostic Mode y abrir una fase separada aprobada.

## 7. Interaccion Con Dangerous Command Policy

Diagnostic Mode y Dangerous Command Policy no responden la misma pregunta.

- Diagnostic Mode: "esta accion esta permitida dentro de una auditoria read-only?"
- Dangerous Command Policy: "que tan peligroso es este comando?"

Si una accion falla cualquiera de las dos, prevalece la decision mas restrictiva.
Por ejemplo, `git commit` puede ser `WARN` en Dangerous Command Policy, pero es
`BLOCK` dentro de Diagnostic Mode porque produce una mutacion.

## 8. Como Salir De Diagnostic Mode

Salida correcta:

```text
Fase 1:
Auditar repo en Diagnostic Mode.

Resultado:
Hallazgos y recomendaciones.

Fase 2:
Solicitar aprobacion explicita para implementar una recomendacion.
```

Salida incorrecta:

```text
Auditar y corregir automaticamente.
```

Una fase de implementacion posterior debe declarar objetivo, archivos permitidos,
archivos prohibidos, checks, criterio de PASS y rollback.

## 9. Return Envelope

Una auditoria diagnostica debe usar esta forma:

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

Reglas:

- `changes` siempre debe ser `[]`.
- `PASS` requiere evidencia.
- `BLOCKED` debe mencionar la accion prohibida.
- No se declaran correcciones realizadas.

## 10. Limites Conocidos

Diagnostic Mode no es sandbox real, permiso de sistema operativo, interceptor
global de shell, hook global, runtime autonomo, agente, auto-remediation,
auto-commit, auto-push, auto-deploy, telemetria ni persistencia.

El evaluador no ejecuta acciones. Solo clasifica etiquetas de accion y contratos
estructurados. Los comandos concretos deben seguir pasando por Dangerous Command
Policy cuando corresponda.

## 11. Ejemplos

Permitido:

```python
evaluate_diagnostic_action("git status")
```

Resultado esperado: `ALLOW`.

Bloqueado:

```python
evaluate_diagnostic_action("git push")
```

Resultado esperado: `BLOCK`.

Ambiguo:

```python
evaluate_diagnostic_action("run external maintenance tool")
```

Resultado esperado: `UNKNOWN`. Un consumidor debe tratarlo como bloqueo.

MCP read-only:

```python
evaluate_diagnostic_action("mcp_tools_list", metadata={"read_only": True})
```

Resultado esperado: `ALLOW`.

MCP sin metadata:

```python
evaluate_diagnostic_action("mcp_tools_list")
```

Resultado esperado: `UNKNOWN`, porque Diagnostic Mode falla cerrado ante side
effects no comprobados.
