# MCP Connector Policy v0

## Objetivo

Definir una politica minima antes de evaluar o incorporar conectores externos en ATLAS.

ATLAS no debe crecer por acumulacion oportunista de conectores. Cada conector futuro debe justificar claramente su valor para:

- gobernanza
- evaluacion
- workflows reutilizables
- control de capacidades

## Regla por defecto

Estado por defecto: **no integrar**.

Un conector solo se considera si resuelve un problema real y recurrente que no puede resolverse mejor con:

- convencion
- metadata local
- archivo versionado
- workflow manual controlado

## Criterios de evaluacion obligatorios

1. Fit de negocio
   - Que problema real resuelve.
   - Por que mejora a ATLAS como sistema padre de capacidades.

2. Tipo de acceso
   - solo lectura de metadata
   - lectura estructural
   - accion operativa

3. Riesgo
   - secretos
   - mutacion remota
   - exfiltracion
   - acoplamiento proveedor
   - superficie de prompt injection

4. Trazabilidad
   - decisiones registradas
   - owner definido
   - rollback claro

5. Aislamiento
   - no mezclar un conector con otros modulos sin frontera clara
   - no usar un conector como atajo a una arquitectura confusa

## Niveles permitidos

Nivel 0 - Prohibido por ahora
- conectores con escritura remota sin justificacion excepcional
- conectores que abren ejecucion arbitraria
- conectores sin owner o sin politica de secretos

Nivel 1 - Evaluacion documental
- analizar el conector
- evaluar metadata
- documentar decision

Sin implementacion.

Nivel 2 - Lectura controlada
- Solo si el caso es recurrente
- Si hay fit alto
- Si el acceso es de lectura
- Si hay logs y alcance acotado

Nivel 3 - Accion operativa
- No habilitar en esta etapa salvo necesidad fuerte y validacion explicita posterior

## Checklist minimo antes de aprobar

- problema real nombrado
- owner definido
- datos accedidos y alcance documentados
- riesgos listados
- rollback simple
- decision registrada en breadcrumbs o metadata

## Resultado esperado

Cada conector futuro debe terminar en una decision concreta:
- aprobar para fase posterior
- disenar sin implementar
- watchlist
- descartar
