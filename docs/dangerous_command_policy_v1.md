# Dangerous Command Policy V1

## Que es

Dangerous Command Policy V1 es una libreria pura de clasificacion. Evalua el riesgo aparente de un comando antes de que otro sistema lo recomiende o ejecute:

```python
from tools.dangerous_command_policy import classify_command

result = classify_command("git status -sb")
```

La funcion no ejecuta el comando. Devuelve el comando original, estado, categoria, razon, regla coincidente, necesidad de aprobacion humana y confianza.

## Que no es

- No es un hook, agente, middleware, CLI ni runtime.
- No bloquea ni modifica comportamiento.
- No instala configuracion global ni inspecciona procesos.
- No usa un LLM, red ni APIs externas.
- No sustituye sandboxing, permisos, Governance, Evidence o revision humana.

V1 es `advisory-only`: ningun consumidor automatico esta conectado.

## Por que existe

El benchmark entre Atlas y Claude-Vibecoding identifico una denylist operativa como adaptacion util si permanecia local, explicita y testeable. Esta policy aporta clasificacion sin adoptar hooks globales ni auto-ejecucion.

## Estados

| Estado | Interpretacion | Aprobacion humana |
|---|---|---|
| `SAFE` | Operacion conocida y acotada de lectura o verificacion | No |
| `WARN` | Puede cambiar estado, instalar codigo o publicar cambios | Si |
| `DENY` | Riesgo destructivo, de secretos, historial, shell o datos | Si |
| `UNKNOWN` | No coincide con una regla; nunca se asume `SAFE` | Si |

Las reglas se evaluan por severidad: `DENY`, `WARN`, `SAFE`. Un prefijo inocuo no puede ocultar una operacion peligrosa compuesta.

## Categorias

| Categoria | Alcance |
|---|---|
| `destructive_filesystem` | Borrado recursivo, formato, wipe y escritura cruda |
| `credential_exposure` | Dotenv y literales con forma de token o credencial |
| `network_exfiltration` | Contenido remoto enviado directamente a un shell |
| `privilege_escalation` | Borrado privilegiado y permisos peligrosos |
| `package_script_execution` | Instaladores capaces de ejecutar scripts de terceros |
| `git_history_rewrite` | Force push, hard reset y perdida de recuperacion |
| `production_deploy` | Publicacion o aplicacion de cambios alojados |
| `database_destructive` | Eliminacion de bases, schemas o filas sin alcance |
| `shell_obfuscation` | Evaluacion dinamica o ejecucion codificada |

La configuracion incluye categorias auxiliares para operaciones read-only y cambios locales advertidos.

## Configuracion declarativa

`config/dangerous_command_patterns.json` contiene solo datos. Cada regla declara `id`, `status`, `category`, `pattern`, `reason` y `confidence`.

Para extender categorias, se agrega una descripcion a `categories` y reglas que la referencien. Para agregar patrones, se agregan entradas a `rules`; el matcher Python no cambia. La policy valida IDs unicos, estados, categorias, confianza y regex.

Cada regla nueva debe incluir tests positivos y de falsos positivos. Las reglas `SAFE` deben estar ancladas y excluir composicion o redireccion de shell cuando corresponda.

## Limites

La clasificacion opera sobre texto, no sobre el AST de cada shell. Alias, variables, quoting complejo, scripts indirectos y sintaxis no catalogada pueden quedar `UNKNOWN`. Las regex son transparentes y conservadoras; no prueban seguridad absoluta en todo contexto.

Los consumidores futuros deberan redactar comandos antes de cualquier logging para no persistir secretos detectados.

## Integracion futura

Una fase posterior podria consultar `classify_command` antes de una propuesta de Runtime y convertir `WARN`, `DENY` o `UNKNOWN` en checkpoint humano. Requeriria contrato, redaccion, Evidence, tests de bypass y una decision explicita de enforcement.

V1 permanece desacoplada de Dispatcher, Planner, Verifier, hooks, CLI, Runtime y MCP.
