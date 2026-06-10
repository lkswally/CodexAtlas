# Model Routing Policy V1

Estado: advisory-only, sin runtime.

Model Routing Policy V1 define clases de modelo recomendadas segun tarea, riesgo, costo y criticidad. No ejecuta cambios automaticos, no llama APIs y no habilita auto-switch.

## Objetivo

Evitar dos fallos opuestos:

- evidencia tecnica sin control de costo
- optimizacion de costo sin evidencia suficiente

La policy ayuda al Atlas Planner a elegir una clase de modelo antes de ejecutar trabajo, pero no decide aprobacion ni resultado final.

## Clases

- `cheap_fast`: documentacion, resumen y formato de bajo riesgo.
- `balanced`: cambios pequenos de codigo, generacion de tests y analisis tecnico acotado.
- `premium_reasoning`: decisiones de arquitectura, seguridad, visual QA y outcome evaluation.
- `human_required`: operaciones de produccion o side effects externos.
- `blocked`: secretos, credenciales o riesgo explicitamente bloqueado.

## Reglas base

- `documentation`, `summarization`, `formatting` -> `cheap_fast`.
- `code_small_change`, `test_generation` -> `balanced`.
- `architecture_decision`, `security_review`, `outcome_evaluation` -> `premium_reasoning`.
- `production_operation`, `external_side_effect` -> `human_required`.
- `secrets_or_credentials` -> `blocked`.

## Overrides de riesgo

- `high` nunca puede seleccionar `cheap_fast`.
- `blocked` siempre selecciona `blocked`.
- Las clases `human_required` y `blocked` no se degradan por costo.

## Output requerido

```json
{
  "task_type": "",
  "risk_level": "",
  "selected_model_class": "",
  "reason": "",
  "requires_human_approval": false,
  "auto_switch_allowed": false
}
```

`auto_switch_allowed` siempre debe ser `false` en V1.

## Relacion con Agent Loop

La decision se toma despues de Objective Intake y Planning:

Atlas Planner -> Model Routing Policy -> Codex Executor.

El router recomienda clase de modelo para ejecutar trabajo. No aprueba resultados, no reemplaza Evidence Quality Report y no puede declarar PASS.

## Fuera de scope

- Auto Model Switching.
- Llamadas a APIs.
- Seleccion de proveedor concreto.
- Cambios automaticos de runtime.
- Aprobacion de quality gates.
- Operaciones de produccion.
- Manejo de secretos.
