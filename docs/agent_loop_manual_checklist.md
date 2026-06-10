# Agent Loop V2 Manual Checklist

Estado: checklist manual, sin runtime.

Este documento convierte el diseno Agent Loop V1 en una secuencia operativa manual. No crea agentes, automatizaciones, MCPs ni runtime de model routing.

Regla obligatoria: PASS nunca puede existir sin evidencia.

## Roles

- Atlas Planner: define objetivo, scope, plan, riesgos y clase de modelo recomendada.
- Codex Executor: ejecuta cambios dentro del scope autorizado.
- CodexAtlas Verifier: valida evidencia, tests, diff y limites.
- Evidence Reporter: genera o resume Evidence Quality Report.
- Failure Recorder: documenta fallos, bloqueos y aprendizaje candidato.

## 1. Objective Intake

Inputs:

- objetivo del usuario
- contexto del repo
- archivos permitidos y prohibidos
- restricciones de seguridad, costo y criticidad
- definicion de evidencia esperada

Outputs:

- objetivo normalizado
- non-scope explicito
- riesgos iniciales
- criterio minimo de evidencia

Criterios:

- PASS: objetivo claro, scope claro y evidencia esperada definida.
- WARN: objetivo claro con supuestos menores.
- FAIL: objetivo contradictorio o pide acciones prohibidas.
- BLOCKED: falta informacion indispensable.

## 2. Planning

Inputs:

- objective intake
- restricciones de archivos
- riesgos
- Model Routing Policy V1

Outputs:

- plan paso a paso
- checks requeridos
- clase de modelo recomendada
- condiciones de stop

Criterios:

- PASS: plan acotado y verificable.
- WARN: plan viable con riesgos residuales.
- FAIL: plan viola restricciones.
- BLOCKED: faltan permisos, runtime o decision humana.

## 3. Execution

Inputs:

- plan aprobado
- archivos permitidos
- comandos permitidos
- clase de modelo recomendada

Outputs:

- cambios realizados
- comandos ejecutados
- resultados intermedios
- desviaciones reportadas

Criterios:

- PASS: ejecucion completa dentro del scope.
- WARN: ejecucion completa con advertencias no bloqueantes.
- FAIL: ejecucion rompe contrato, tests o scope.
- BLOCKED: dependencia externa impide continuar.

## 4. Evidence Generation

Inputs:

- resultado ejecutado
- superficie verificable
- Evidence Runner o evidencia equivalente

Outputs:

- Evidence Contract V1
- Evidence Bundle V1
- screenshots, viewport reports, console errors y network errors cuando aplique

Criterios:

- PASS: evidencia generada y persistida.
- WARN: evidencia parcial pero util.
- FAIL: evidencia invalida.
- BLOCKED: no hay entorno para generar evidencia.

## 5. Verification

Inputs:

- diff
- tests/checks
- Evidence Bundle V1
- scope y non-scope

Outputs:

- decision tecnica
- hallazgos
- checks faltantes
- riesgos residuales

Criterios:

- PASS: tests/checks pasan y hay evidencia suficiente.
- WARN: tests pasan pero hay advertencias o evidencia incompleta.
- FAIL: tests fallan, evidencia invalida o scope violado.
- BLOCKED: verificacion no puede ejecutarse.

## 6. Evidence Quality Report

Inputs:

- Evidence Bundle V1 persistido
- Evidence Quality Report CLI

Outputs:

- Evidence Quality Report V1
- resultado PASS/WARN/FAIL
- recommendation tecnica

Criterios:

- PASS: reporte tecnico PASS.
- WARN: reporte tecnico WARN.
- FAIL: reporte tecnico FAIL.
- BLOCKED: reporte no pudo ejecutarse por runtime o archivo faltante indispensable.

Nota: PASS tecnico no aprueba visualmente el producto.

## 7. Final Report

Inputs:

- decision del verifier
- Evidence Quality Report
- tests/checks
- diff final

Outputs:

- resumen final
- archivos tocados
- evidencia generada
- resultado PASS/WARN/FAIL/BLOCKED
- riesgos residuales
- proximo paso recomendado

Criterios:

- PASS: resultado completado con evidencia real.
- WARN: resultado util con limitaciones explicitas.
- FAIL: resultado no cumple.
- BLOCKED: no se pudo completar por condicion externa.

## 8. Failure/Learning Note

Inputs:

- WARN, FAIL o BLOCKED
- errores de tests
- evidencia faltante
- desviaciones de scope
- decisiones humanas pendientes

Outputs:

- nota de fallo/aprendizaje
- causa probable
- accion recomendada
- candidato futuro para Failure Registry

Criterios:

- PASS: no aplica o nota creada cuando correspondia.
- WARN: aprendizaje incompleto pero util.
- FAIL: no se registro una falla relevante.
- BLOCKED: no se puede clasificar sin mas informacion.

## Conexion futura

Mapa previsto:

Atlas Planner
↓
Model Routing Policy
↓
Codex Executor
↓
Evidence Pipeline
↓
CodexAtlas Verifier
↓
Evidence Quality Report
↓
Failure Recorder

La decision de modelo se toma entre Planning y Execution. La toma Atlas Planner usando Model Routing Policy V1 como recomendacion advisory-only.

La evidencia se genera despues de Execution, usando Evidence Pipeline cuando exista una superficie verificable.

Los fallos se registran al final del ciclo, despues de Verification y Evidence Quality Report. En V2 solo se redacta una nota manual; no se escribe en registries.

El router no debe decidir aprobacion porque no ve el resultado final. Solo recomienda clase de modelo antes de ejecutar. La aprobacion depende de evidencia, tests, scope y verificacion.

## Prohibiciones V2

- No crear runtime.
- No crear agentes.
- No crear automatizaciones.
- No activar Paperclip.
- No activar n8n.
- No agregar MCP.
- No auto-mutarse.
- No hacer auto-switch de modelo.
- No declarar PASS sin evidencia.
- No escribir Failure Registry.
