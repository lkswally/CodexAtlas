# Context Refresh Protocol v0

## Objetivo

Reducir drift entre:

- estado real del proyecto
- decisiones recientes
- documentacion operativa
- memoria de trabajo

## Cuando correr un refresh

Hacer refresh solo si hubo alguno de estos cambios:

- nueva capacidad reusable
- cambio relevante de arquitectura
- alta/baja de una politica
- decision de gobernanza
- cambio de fuente canonica

No hacer refresh por microcambios irrelevantes.

## Breadcrumb minimo

Cada refresh debe dejar:

- fecha
- decision o cambio
- motivo
- archivos tocados
- impacto esperado
- riesgo residual
- rollback simple

## Formato sugerido

```md
## YYYY-MM-DD HH:MM (TZ)
- Cambio:
- Motivo:
- Archivos:
- Impacto:
- Riesgo residual:
- Rollback:
```

## Ubicacion sugerida

Mientras no exista un subsistema Atlas mas grande, los breadcrumbs y resumentes pueden vivir en:

- `memory/breadcrumbs.md`
- `memory/session_summaries.md`

El mirror legacy puede conservar una copia compatible en `00_SISTEMA/_meta/atlas/`.

## Regla de sobriedad

No usar el refresh para reescribir toda la documentacion.
Actualizar solo lo necesario para mantener continuidad operativa.
