# Agent Loop V1 Design

Estado: diseno Atlas-native, sin runtime.

Agent Loop V1 define una forma minima de coordinar trabajo entre planificacion, ejecucion, verificacion y reporte sin crear agentes nuevos todavia. El objetivo es convertir trabajo asistido en ciclos con evidencia, no agregar una capa autonoma opaca.

## Problema que resuelve

Codex-Atlas ya tiene una cadena evidence-driven:

Runner -> Validator -> Bundle -> Persist/Read -> Summary -> CLI -> Adapter -> Report -> Report CLI.

El problema pendiente no es falta de mas policies ni mas readiness. El problema es coordinar el ciclo completo de trabajo para que cada cambio tenga:

- objetivo explicito
- plan verificable
- ejecucion acotada
- evidencia generada
- verificacion real
- reporte legible
- registro de fallos cuando no se puede declarar PASS

Agent Loop V1 resuelve la coordinacion del ciclo. No resuelve todavia autonomia total, aprendizaje automatico ni evaluacion visual profunda.

## Roles minimos

### Atlas Planner

Responsabilidad: convertir un objetivo en plan acotado, riesgos, no-scope y criterios de evidencia.

Inputs:

- objetivo del usuario
- restricciones del repo
- fases previas completadas
- archivos permitidos y prohibidos
- criterios de PASS/WARN/FAIL/BLOCKED

Outputs:

- plan de ejecucion
- lista de checks requeridos
- limites explicitos de scope
- criterios para detenerse

### Codex Executor

Responsabilidad: ejecutar el plan dentro del scope autorizado.

Inputs:

- plan del Atlas Planner
- archivos permitidos
- comandos autorizados
- criterios de verificacion

Outputs:

- cambios realizados
- comandos ejecutados
- resultados de tests
- evidencia tecnica producida
- diff listo para revision

### CodexAtlas Verifier

Responsabilidad: verificar que el resultado cumple el scope y que no se declaran estados sin evidencia.

Inputs:

- diff
- resultados de tests/checks
- Evidence Bundle o Evidence Quality Report cuando aplique
- reglas de no-scope

Outputs:

- decision PASS/WARN/FAIL/BLOCKED
- hallazgos tecnicos
- desviaciones de scope
- checks faltantes

### Evidence Reporter

Responsabilidad: convertir evidencia tecnica en reporte legible y transportable.

Inputs:

- Evidence Bundle V1
- Evidence Summary V1
- Evidence Quality Gate Adapter output
- resultados de tests/checks

Outputs:

- Evidence Quality Report V1
- resumen humano
- recommendation tecnica
- estado non-blocking cuando el modo sea opt-in

### Failure Recorder

Responsabilidad: registrar fallos utiles para aprendizaje futuro sin convertirlos todavia en registry runtime.

Inputs:

- estado FAIL/WARN/BLOCKED
- causa principal
- evidencia faltante
- comandos fallidos
- restricciones que impidieron avanzar

Outputs:

- failure record propuesto
- clasificacion de causa
- accion recomendada
- candidato futuro para Failure Registry

## Flujo

1. Objective intake: se captura objetivo, restricciones, no-scope y estado esperado.
2. Plan: Atlas Planner define pasos, checks y criterios de salida.
3. Execution: Codex Executor realiza cambios o acciones dentro del scope.
4. Evidence generation: se genera evidencia tecnica cuando el trabajo tiene superficie verificable.
5. Verification: CodexAtlas Verifier revisa tests, diff, scope y evidencia.
6. Report: Evidence Reporter emite reporte tecnico, preferentemente con Evidence Quality Report cuando exista bundle.
7. Failure/learning record: Failure Recorder propone registro si el resultado es WARN, FAIL o BLOCKED.

Para tareas documentales o de arquitectura sin UI ejecutable, la evidencia minima puede ser revision real, diff, tests aplicables y checks de repositorio. Evidence Quality Report aplica cuando existe un Evidence Bundle V1; no debe fingirse un bundle para trabajos que no generan evidencia visual o de navegador.

## Que no debe hacer

Agent Loop V1 no debe:

- auto-mutarse
- ejecutar produccion
- activar n8n
- instalar Paperclip
- agregar MCPs
- crear agentes runtime nuevos
- pushear sin tests cuando los tests aplican
- declarar PASS sin evidencia real
- convertir WARN en PASS
- convertir FAIL en WARN
- modificar quality gates existentes
- escribir en registries sin fase explicita

## Estados

`PASS`: el objetivo se cumplio, los tests/checks aplicables corrieron y la evidencia requerida existe.

`WARN`: el objetivo principal se cumplio parcialmente o hay evidencia tecnica con advertencias, pero no hay razon suficiente para declarar FAIL.

`FAIL`: la verificacion demuestra que el resultado no cumple el contrato, el scope o los checks requeridos.

`BLOCKED`: falta una dependencia externa, permiso, runtime o informacion indispensable para continuar.

## Conexion con Evidence Quality Report

Agent Loop V1 debe tratar Evidence Quality Report como senal tecnica opt-in y non-blocking.

Uso previsto:

1. Codex Executor genera o recibe un Evidence Bundle V1.
2. Evidence Reporter ejecuta `tools/evidence_quality_report_cli.py`.
3. CodexAtlas Verifier usa `result`, `gate`, `warnings` y `failures` como evidencia tecnica.
4. El loop conserva que `blocking` es `false` hasta una fase futura.

Un reporte `PASS` no aprueba visualmente el producto. Solo confirma que la evidencia tecnica minima esta sana segun las reglas actuales.

Si no hay bundle porque la tarea no tiene superficie verificable por navegador, el Verifier debe registrar `Evidence Quality Report: no aplica` y sostener la decision con la evidencia real disponible. Si habia obligacion explicita de generar bundle y no se pudo, el estado debe ser WARN, FAIL o BLOCKED segun la causa.

## Conexion futura con Failure Registry

Failure Recorder no debe escribir todavia en registries. En V1 solo propone un record estructurado para futura captura.

Campos candidatos:

- objective_id
- status
- failure_type
- root_cause
- missing_evidence
- failed_commands
- affected_files
- recommended_next_action
- evidence_report_path

La integracion real con Failure Registry debe esperar a que existan patrones repetidos y criterios claros de deduplicacion.

## Comparacion breve con Paperclip

Ventajas potenciales de Paperclip:

- puede aportar patrones de AI workers
- puede ayudar a coordinar tareas repetibles
- puede servir como referencia para loops semi-automaticos

Riesgos:

- aumentar complejidad antes de estabilizar evidencia
- duplicar roles que Atlas puede modelar de forma mas simple
- crear dependencia externa prematura
- empujar autonomia antes de tener failure learning confiable

Por que no integrarlo todavia:

- Agent Loop V1 todavia necesita demostrar valor como flujo manual
- Evidence Quality Report sigue en modo opt-in y non-blocking
- no existe Failure Registry operativo
- no hay criterios maduros para delegar decisiones a workers externos
- el riesgo de sobreingenieria es mayor que el beneficio inmediato

## Roadmap incremental

### V1 diseno

Documento de roles, flujo, estados y limites. Sin runtime.

### V2 loop manual

Checklist manual por tarea:

- objetivo
- plan
- ejecucion
- evidencia
- verificacion
- reporte
- failure record propuesto

### V3 loop semi-automatico

Runner local que orquesta comandos existentes en modo opt-in:

- no bloqueante
- sin nuevos agentes
- sin produccion
- sin n8n
- sin mutation automatica

### V4 integracion opcional con Paperclip

Evaluar Paperclip solo si:

- el loop manual demostro valor
- el reporte evidence-driven es estable
- hay failure records repetidos
- Paperclip reduce trabajo real sin ocultar evidencia
- la integracion puede apagarse sin romper Atlas
