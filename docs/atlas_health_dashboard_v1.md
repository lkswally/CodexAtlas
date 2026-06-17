# Atlas Health Dashboard V1

Estado: dashboard minimo, local y no bloqueante. No es una web app ni un runtime autonomo.

## Proposito

Atlas Health Dashboard V1 resume el estado operativo de Codex-Atlas antes de avanzar hacia Autonomous Engineering Runtime. Su salida principal es un JSON estable que puede renderizarse como Markdown para revision humana.

## Alcance

Evalua:

- Workflows conocidos: Atlas CI, Atlas Global Test, Evidence Quality Report y Evidence Browser Smoke.
- Herramientas core: Evidence Pipeline, Model Routing, Failure Registry y Governance.
- Riesgos conocidos: workflows sin observacion, integraciones advisory-only, browser smoke manual y runner warnings.

## Limites

- No crea web app.
- No ejecuta runtime autonomo.
- No modifica Evidence Pipeline, workflows, governance, Model Routing ni Failure Registry.
- No depende de APIs externas obligatorias.
- Si no se inyectan observaciones de workflows, esos estados quedan en `UNKNOWN`.
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

## Interpretacion

Un resultado `WARN` por workflows sin observacion no implica que CI este fallando. Significa que el dashboard local no recibio una observacion confiable para ese workflow.

Browser smoke permanece manual/opt-in. Ese riesgo se reporta para visibilidad operativa, pero V1 no lo convierte en bloqueo automatico.

## Proximo paso futuro

1. Definir una fuente local y cacheable para ultimas observaciones de CI.
2. Agregar una interfaz de lectura cuando exista una politica aprobada para dashboard operativo.
3. Mantener Autonomous Engineering Runtime fuera de alcance hasta que el dashboard tenga inputs confiables.
