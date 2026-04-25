# Codex-Atlas

`C:\Proyectos\Codex-Atlas` es la fuente de verdad canónica de ATLAS: una configuración madre de Codex para crear, gobernar, auditar y certificar proyectos derivados sin mezclar el core reusable con runtimes de producto.

REYESOFT es un derivado separado. Atlas opera sobre derivados desde afuera y no debe volver a vivir dentro de ellos.

## Objetivo

Codex-Atlas existe para:
- bootstrappear proyectos derivados con límites claros
- gobernar skills, workflows, policies y contratos
- auditar y certificar derivados en modo read-only
- mantener observabilidad mínima y continuidad entre sesiones
- adaptar patrones útiles del ecosistema sin copiar Claude-only runtime

## Arquitectura

La superficie canónica vive en raíz:
- `AGENTS.md`
- `commands/`
- `config/`
- `agents/`
- `skills/`
- `workflows/`
- `policies/`
- `templates/`
- `memory/`
- `docs/`
- `tools/`
- `adapters/`
- `tests/`

Capas principales:
- `tools/atlas_orchestrator.py`: routing sugerente, skills, modelos y MCPs controlados
- `tools/atlas_dispatcher.py`: comandos ejecutables read-only o de escritura limitada y gobernada
- `tools/atlas_governance_check.py`: validación canónica de estructura, contratos y límites
- `tools/atlas_mcp_manager.py`: lifecycle controlado de MCPs experimentales
- `tools/docs_search_adapter.py`: adapter interno read-only sobre catálogo curado
- `tools/docs_catalog_report.py`: reporte read-only de salud y frescura del catálogo

`00_SISTEMA/_meta/atlas/` se conserva solo como mirror legacy de compatibilidad. No es la fuente principal.

## Features actuales

- gobernanza root-first validada
- dispatcher ejecutable con `audit-repo` y `certify-project`
- orquestador sugerente con skills, perfiles de modelo y MCPs controlados
- skills estructuradas con `skill.md`, `skill.json`, `behavior.json` y contratos externos cuando aplica
- `project-bootstrap` con preflight real, templates por perfil y salida mínima segura
- `repo-audit` y `certify-project` en modo read-only
- observabilidad append-only para routing, governance, MCPs y proyectos derivados
- adapter interno `docs_search` con ranking, deduplicación, summary, confidence y política de frescura
- reporte read-only del catálogo curado de documentación oficial

## Skills disponibles

- `project-bootstrap`
- `repo-audit`
- `product-branding-review`

## Workflows disponibles

- `atlas_project_pipeline`
- `create_project`
- `audit_project`
- `audit_repo`
- `certify_project`
- `certify_output`
- `orchestrator_routing`

## Cómo crear un proyecto derivado

Atlas no crea runtime completo. Crea una base derivada segura y certificable.

Inputs mínimos recomendados:
- `project_goal`
- `scope_and_non_scope`
- `target_runtime_or_stack`
- `constraints_and_approval_boundaries`
- `output_dir`
- opcional: `project_name`, `project_type`, `adapter_notes`, `initial_docs_scope`

Perfiles soportados:
- `backend_service`
- `frontend_app`
- `fullstack`
- `internal_tool`
- `ai_agent_system`

Flujo sugerido:
1. Pedir routing/orquestación sobre la idea del proyecto.
2. Ejecutar `project-bootstrap` con `output_dir` explícito.
3. Auditar el derivado con `audit-repo`.
4. Certificar el derivado con `certify-project`.

## Cómo auditar o certificar un proyecto

Auditar Atlas:

```powershell
python C:\Proyectos\Codex-Atlas\tools\atlas_governance_check.py
python C:\Proyectos\Codex-Atlas\tools\atlas_dispatcher.py audit-repo
```

Auditar un derivado:

```powershell
python C:\Proyectos\Codex-Atlas\tools\atlas_governance_check.py --project C:\Ruta\Al\Proyecto
python C:\Proyectos\Codex-Atlas\tools\atlas_dispatcher.py --project C:\Ruta\Al\Proyecto audit-repo
```

Certificar un derivado:

```powershell
python C:\Proyectos\Codex-Atlas\tools\atlas_dispatcher.py --project C:\Ruta\Al\Proyecto certify-project
```

Los derivados no necesitan shims de Atlas si exponen `.atlas-project.json`.

## Estado actual

**Listo con cautela**

Atlas está listo para una primera prueba real de bootstrap sobre un proyecto nuevo, siempre que el objetivo sea generar una base derivada segura y no un runtime completo en un solo paso.

## Límites actuales

Atlas no incluye ni habilita por defecto:
- `.claude`
- `CLAUDE.md` como fuente principal
- hooks automáticos
- MCP real
- Engram
- Pixel Bridge
- deploy automático
- instalación automática de dependencias
- escritura fuera de `output_dir` en bootstrap

Además:
- `docs_search` sigue siendo adapter interno, no conector MCP real
- la creación de proyecto produce scaffold y metadata, no lógica de negocio lista
- siguen existiendo algunos residuos legacy bloqueados por el filesystem en `tests/`

## Roadmap inmediato

- cerrar el baseline actual y usar Atlas para el primer proyecto real controlado
- mantener fresco `config/docs_search_catalog.json`
- seguir fortaleciendo quality gates read-only antes de sumar más autonomía
- retirar residuos legacy cuando el filesystem lo permita
- evaluar un segundo MCP solo si el modelo de gobernanza actual se sostiene

## Referencias rápidas

- [AGENTS.md](/C:/Proyectos/Codex-Atlas/AGENTS.md)
- [ATLAS_STATUS.md](/C:/Proyectos/Codex-Atlas/ATLAS_STATUS.md)
- [ATLAS_NEXT_STEPS.md](/C:/Proyectos/Codex-Atlas/ATLAS_NEXT_STEPS.md)
- [docs/architecture.md](/C:/Proyectos/Codex-Atlas/docs/architecture.md)
- [docs/codex_system_prompt.md](/C:/Proyectos/Codex-Atlas/docs/codex_system_prompt.md)
- [docs/mcp_read_only_evaluation.md](/C:/Proyectos/Codex-Atlas/docs/mcp_read_only_evaluation.md)
