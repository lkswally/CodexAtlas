# Evidence Quality Report opt-in usage

Estado: opt-in, non-blocking.

Esta guia documenta la cadena evidence-driven actual de Codex-Atlas V2. No integra el reporte con `quality_gate_report.py`, no bloquea flujos existentes y no reemplaza revisiones visuales, UX ni aprobaciones humanas.

## Problema que resuelve

Atlas tenia muchas capas de readiness, governance y advisory, pero poca verificacion basada en evidencia tecnica persistible. Esta cadena permite pasar de "parece listo" a "hay evidencia tecnica verificable en disco" para revisiones futuras.

La capacidad actual permite:

- capturar evidencia tecnica desde una URL
- validar que la evidencia cumple Evidence Contract V1
- normalizarla como Evidence Bundle V1
- persistir y leer el bundle como JSON
- resumir conteos tecnicos
- traducir el resumen a una senal de quality gate futura
- emitir un reporte opt-in no bloqueante

## Estado actual

- Opt-in: solo corre si alguien lo ejecuta explicitamente.
- Non-blocking: el reporte siempre declara `"blocking": false`.
- Aislado: no modifica quality gates, governance, registries, policies ni readiness layers.
- Tecnico: resume evidencia disponible, errores de consola/red y metadata.
- Limitado: no evalua UX, jerarquia visual, calidad visual, motion, copy, accesibilidad completa ni resultado de producto.

## Flujo conceptual

1. Evidence Runner genera Evidence Contract V1 desde una URL.
2. Contract Validator valida estructura y campos obligatorios.
3. Evidence Session construye Evidence Bundle V1.
4. Bundle persistence guarda el bundle en JSON.
5. Bundle Reader lee y valida el bundle persistido.
6. Summary Consumer produce Evidence Summary V1.
7. Quality Gate Adapter traduce el summary a una senal futura de gate.
8. Evidence Quality Report emite un reporte opt-in no bloqueante.

## Comandos de ejemplo

Prerequisito: estos comandos asumen que existe una app o URL accesible para generar evidencia y que el bundle se escribira en `.atlas_evidence/bundle.json`.

Generar Evidence Contract V1 desde una URL:

```powershell
python tools/evidence_runner.py --url http://localhost:3000 --output-dir .atlas_evidence/screenshots --contract-out .atlas_evidence/contract.json
```

Crear un Evidence Bundle V1 desde Python y persistirlo:

```powershell
python -c "import json; from pathlib import Path; from tools.evidence_session import build_evidence_bundle, write_evidence_bundle; contract=json.loads(Path('.atlas_evidence/contract.json').read_text(encoding='utf-8')); bundle=build_evidence_bundle(contract); write_evidence_bundle(bundle, Path('.atlas_evidence/bundle.json'))"
```

Emitir Summary V1 desde un bundle:

```powershell
python tools/evidence_bundle_summary_cli.py .atlas_evidence/bundle.json
```

Emitir Evidence Quality Report V1:

```powershell
python tools/evidence_quality_report_cli.py .atlas_evidence/bundle.json
```

Si el bundle no existe o es invalido, la CLI devuelve `FAIL` y exit code 1. Ese comportamiento es correcto para uso manual: obliga a mirar la causa tecnica en el JSON impreso por stdout.

## GitHub Actions opt-in

El workflow manual `.github/workflows/evidence-quality-report.yml` permite publicar el reporte desde GitHub Actions sin convertirlo en quality gate obligatorio.

Como ejecutarlo:

1. Abrir la pestana Actions en GitHub.
2. Seleccionar `Evidence Quality Report`.
3. Ejecutar `Run workflow`.
4. Opcionalmente ajustar `bundle_path`. El valor por defecto es `.atlas_evidence/bundle.json`.

Comportamiento esperado:

- Si el bundle existe, el workflow ejecuta `tools/evidence_quality_report_cli.py`.
- Si se genera reporte, lo sube como artifact `evidence-quality-report`.
- Si el bundle no existe, emite un warning claro y termina con exit code 0.
- Si el reporte devuelve `FAIL`, queda registrado como warning, pero el workflow no bloquea.
- El workflow no requiere secrets y no ejecuta navegador real.

Diferencia importante: la CLI local falla con exit code 1 ante bundle invalido o ausente, pero el workflow manual captura ese caso como observacion no bloqueante. El workflow existe para publicar evidencia cuando ya hay bundle, no para exigir que todos los runs generen evidencia visual.

### Observacion real de workflow

Run observado: `27251943469`.

Resultado:

- `workflow_dispatch` termino en PASS.
- Tests en GitHub Actions: `69 passed`.
- Sin bundle: el workflow emitio aviso claro y termino con exit code 0.
- Artifact: no se genero artifact porque no se genero reporte, correcto para corrida sin bundle.

Interpretacion:

- El workflow es operativo en modo opt-in/no bloqueante.
- La ausencia de bundle no es un fallo.
- El comportamiento observado coincide con el proposito de publicar reporte solo cuando ya existe evidencia persistida.

Warnings observados:

- GitHub Actions aviso de deprecation para acciones basadas en Node.js 20.
- `windows-latest` redirigio a `windows-2025`.

Riesgo:

- Bajo y no bloqueante. No afecta el resultado actual, pero conviene monitorearlo.

Accion futura recomendada:

- Revisar versiones de actions antes de que Node.js 20 sea removido.
- Considerar pin de runner si `windows-latest` cambia comportamiento relevante.

Estado operativo: PASS con warnings menores.

## Interpretacion de estados

`PASS` significa que el bundle es tecnicamente valido, tiene al menos un screenshot, al menos un viewport report y no contiene console errors ni network errors.

`WARN` significa que el bundle es valido, pero falta evidencia esperada o existen warnings tecnicos, por ejemplo screenshots ausentes, viewport reports ausentes, console errors o network errors.

`FAIL` significa que el bundle no pudo leerse, no es valido o fallo validacion tecnica.

## Regla explicita

Un `PASS` tecnico no significa que el producto esta aprobado visualmente.

Un `PASS` tecnico solo significa que la evidencia minima disponible esta sana segun las reglas actuales. No valida identidad visual, layout real, responsive quality, motion, UX, copy, accesibilidad completa, performance ni resultado de negocio.

## Proxima integracion prevista

La siguiente integracion razonable es ejecutar el Evidence Quality Report como modo WARN/no bloqueante junto al quality gate principal. Debe reportar evidencia sin impedir merges, releases o certificaciones hasta que haya historial suficiente y criterios de bloqueo claros.

## Limitaciones actuales

- No hay visual regression.
- No hay AI visual judge.
- No hay outcome evaluator.
- No hay aprendizaje real automatico todavia.
- No compara screenshots contra baseline.
- No valida calidad visual ni UX.
- No verifica despliegues productivos.
- No escribe resultados en governance ni memory.
