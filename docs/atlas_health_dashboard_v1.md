# Atlas Health Dashboard V1

Estado: dashboard minimo, local y no bloqueante. No es una web app ni un runtime autonomo.

## Proposito

Atlas Health Dashboard V1 resume el estado operativo de Codex-Atlas antes de avanzar hacia Autonomous Engineering Runtime. Su salida principal es un JSON estable que puede renderizarse como Markdown para revision humana.

## Alcance

Evalua:

- Workflows conocidos: Atlas CI, Atlas Global Test, Evidence Quality Report y Evidence Browser Smoke.
- Herramientas core: Evidence Pipeline, Model Routing, Failure Registry y Governance.
- Riesgos conocidos: workflows sin observacion, integraciones advisory-only, browser smoke manual y runner warnings.
- Cache local opcional: `config/workflow_observations.json`.

## Limites

- No crea web app.
- No ejecuta runtime autonomo.
- No modifica Evidence Pipeline, workflows, governance, Model Routing ni Failure Registry.
- No depende de APIs externas obligatorias.
- Si no se inyectan observaciones de workflows, esos estados quedan en `UNKNOWN`.
- Si el cache de observaciones falta, esos estados quedan en `UNKNOWN`.
- Si el cache existe pero es invalido, el dashboard queda en `WARN` controlado.
- No instala dependencias.

## Contrato JSON

```json
{
  "dashboard_name": "atlas_health_dashboard",
  "version": "v1",
  "overall_status": "",
  "generated_at": "",
  "sections": {
    "ci": {},
    "evidence": {},
    "browser_smoke": {},
    "model_routing": {},
    "failure_registry": {},
    "integrations": {}
  },
  "risks": [],
  "next_actions": []
}
```

## Estados

- `PASS`: no hay fallos ni estados desconocidos en las secciones evaluadas.
- `WARN`: hay `WARN` o `UNKNOWN`, pero no hay fallo critico.
- `FAIL`: una seccion critica reporta `FAIL`.
- `UNKNOWN`: se usa dentro de secciones cuando no hay observacion disponible.

## Uso

```python
from tools.atlas_health_dashboard import build_health_dashboard, render_health_markdown

report = build_health_dashboard()
markdown = render_health_markdown(report)
```

`build_health_dashboard` puede recibir `workflow_statuses` y `core_statuses` para usar observaciones ya obtenidas por otro proceso. V1 no llama `gh` ni APIs externas por si mismo.

Por defecto tambien intenta leer `config/workflow_observations.json`. El archivo es local, manual y no contiene tokens ni URLs con credenciales. Una observacion ausente no se convierte en `PASS`: queda como `UNKNOWN`.

## Workflow Observations Cache

Formato:

```json
{
  "observations_version": "v1",
  "updated_at": "",
  "workflows": {
    "atlas_ci": {
      "status": "PASS",
      "run_id": "",
      "observed_at": "",
      "notes": ""
    },
    "atlas_global_test": {
      "status": "PASS",
      "run_id": "",
      "observed_at": "",
      "notes": ""
    },
    "evidence_quality_report": {
      "status": "PASS",
      "run_id": "",
      "artifact_id": "",
      "observed_at": "",
      "notes": ""
    },
    "evidence_browser_smoke": {
      "status": "PASS",
      "run_id": "",
      "artifact_id": "",
      "observed_at": "",
      "notes": ""
    }
  }
}
```

Campos:

- `status`: admite `PASS`, `WARN`, `FAIL` o `UNKNOWN`.
- `run_id`: referencia textual a la corrida observada.
- `artifact_id`: opcional, solo cuando hay artifact relevante.
- `observed_at`: momento de la observacion.
- `notes`: nota corta sin secretos.

Politica:

- El cache no llama GitHub, no usa `gh` y no consulta APIs externas.
- Una observacion invalida marca `WARN`, no rompe la ejecucion.
- Una observacion faltante conserva `UNKNOWN`.
- `overall_status` no debe ser `PASS` si hay workflows criticos `UNKNOWN`, salvo que una politica futura lo documente explicitamente.
- Core local se evalua de forma independiente del cache de workflows.

## Interpretacion

Un resultado `WARN` por workflows sin observacion no implica que CI este fallando. Significa que el dashboard local no recibio una observacion confiable para ese workflow.

Un resultado `PASS` con cache significa que las secciones core locales estan sanas y que los workflows conocidos tienen observaciones cacheadas en `PASS`. No equivale a una consulta en vivo de GitHub Actions.

Browser smoke permanece manual/opt-in. Ese riesgo se reporta para visibilidad operativa, pero V1 no lo convierte en bloqueo automatico.

## Proximo paso futuro

1. Definir una politica de frescura para `workflow_observations.json`.
2. Agregar una interfaz de lectura cuando exista una politica aprobada para dashboard operativo.
3. Mantener Autonomous Engineering Runtime fuera de alcance hasta que el dashboard tenga inputs confiables.
