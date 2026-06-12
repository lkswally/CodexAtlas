# Failure Registry V1

Estado: registro minimo, manual y aislado. No existe runtime automatico de aprendizaje.

## Problema que resuelve

Failure Registry V1 convierte un fallo observado en un registro estructurado, validable y reutilizable. Conserva la causa raiz, la resolucion y una referencia a la evidencia sin depender de notas libres dispersas.

El registro sirve para que una revision futura pueda distinguir entre un fallo nuevo y uno ya entendido. No modifica por si mismo el comportamiento de Atlas.

## Que no resuelve

- No encuentra fallos similares automaticamente.
- No cambia policies, prompts, agentes ni rutas de modelo.
- No ejecuta remediaciones.
- No evalua outcomes.
- No convierte WARN, FAIL o BLOCKED en PASS.
- No reemplaza Evidence Quality Report ni los tests.

## Relacion con Agent Loop

El rol Failure Recorder usa este contrato durante `Failure/Learning Note` cuando el Agent Loop termina en WARN, FAIL o BLOCKED. El registro captura aprendizaje candidato; una persona sigue decidiendo si la causa y la resolucion son correctas.

## Relacion con Evidence Quality Report

`evidence_ref` puede apuntar a un Evidence Quality Report, run de CI, artifact u otra evidencia tecnica ya validada. Failure Registry no lee ni reinterpreta esa evidencia: solo conserva una referencia no sensible.

## Failure Record V1

```json
{
  "failure_id": "",
  "timestamp": "",
  "task_type": "",
  "status": "FAIL",
  "summary": "",
  "root_cause": "",
  "resolution": "",
  "evidence_ref": "",
  "source_commit": "",
  "tags": []
}
```

Los campos son exactos. `status` admite `FAIL`, `WARN` o `BLOCKED`. `resolution`, `evidence_ref` y `source_commit` pueden quedar vacios. `tags` contiene solo strings.

## Ejemplo de uso

```python
from pathlib import Path

from tools.failure_registry import create_failure_record, write_failure_record

record = create_failure_record(
    task_type="test_execution_analysis",
    status="FAIL",
    summary="Atlas CI rechazo una configuracion valida.",
    root_cause="El validador esperaba el esquema anterior.",
    resolution="Se agrego validacion explicita del contrato V1.",
    evidence_ref="github-actions:27251498044",
    source_commit="cfed81a",
    tags=["ci", "governance"],
)

write_failure_record(record, Path("local-failures/failure.json"))
```

La ubicacion del ejemplo es deliberadamente local. V1 no define un registry compartido ni agrega records automaticamente al repositorio.

## Limites de seguridad

- No registrar secretos, credenciales ni contenido de archivos de entorno.
- No copiar stack traces completos; pueden contener paths, parametros o datos sensibles.
- `summary`, `root_cause` y `resolution` rechazan patrones obvios: `sk-`, `ghp_`, `password=`, `token=` y `.env`.
- El filtro es una barrera minima, no un detector completo de secretos.
- Usar referencias de evidencia antes que contenido diagnostico extenso.

## Proximo paso futuro

1. Failure similarity lookup para consultar records validados sin mutar comportamiento.
2. Outcome Evaluator para comparar resultados esperados y observados usando evidencia real.

Ninguno de esos pasos forma parte de V1.
