# Codex-Atlas

`<atlas_root>` es la fuente de verdad canónica de ATLAS: una configuración madre de Codex para crear, gobernar, auditar y certificar proyectos derivados sin mezclar el core reusable con runtimes de producto.

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
- `tools/operational_parity_readiness.py`: reporte read-only de paridad operativa Codex-native frente a patrones útiles de `claude-vibecoding`

`00_SISTEMA/_meta/atlas/` se conserva solo como mirror legacy de compatibilidad. No es la fuente principal.

## Features actuales

- gobernanza root-first validada
- dispatcher ejecutable con `audit-repo` y `certify-project`
- orquestador sugerente con skills, perfiles de modelo y MCPs controlados
- skills estructuradas con `skill.md`, `skill.json`, `behavior.json` y contratos externos cuando aplica
- `project-bootstrap` con preflight real, templates por perfil y salida mínima segura
- `repo-audit` y `certify-project` en modo read-only
- `decision-council` como capa read-only para decisiones dificiles con dissent explicito y chairman synthesis manual
- `market-research-benchmark` como benchmark read-only contra `_reference/claude-vibecoding` y repos radar documentados
- observabilidad append-only para routing, governance, MCPs y proyectos derivados
- adapter interno `docs_search` con ranking, deduplicación, summary, confidence y política de frescura
- reporte read-only del catálogo curado de documentación oficial
- paridad operativa Codex-native con handoff envelope, evidence index, stop rules, resume protocol y quality hook bundle manual

## Skills disponibles

- `project-bootstrap`
- `repo-audit`
- `decision-council`
- `market-research-benchmark`
- `product-branding-review`
- `visual-direction-checkpoint`
- `anti-generic-ui-audit`
- `design-system-review`
- `business-idea-evaluator`
- `conversion-copywriter`

## Workflows disponibles

- `atlas_project_pipeline`
- `create_project`
- `audit_project`
- `audit_repo`
- `certify_project`
- `certify_output`
- `change_proposal_workflow`
- `decision_council_review`
- `design_intelligence_pipeline`
- `market_research_benchmark`
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

Auditar Atlas desde la raíz del repo:

```powershell
python tools/atlas_governance_check.py
python tools/atlas_dispatcher.py audit-repo
python tools/atlas_dispatcher.py surface-audit
python tools/atlas_dispatcher.py operational-parity-report
```

Auditar un derivado:

```powershell
python tools/atlas_governance_check.py --project <project_root>
python tools/atlas_dispatcher.py --project <project_root> audit-repo
```

Certificar un derivado:

```powershell
python tools/atlas_dispatcher.py --project <project_root> certify-project
```

Los derivados no necesitan shims de Atlas si exponen `.atlas-project.json`.

## Estado actual

**Codex-Atlas V3 RC1**

Atlas V3 esta congelado como release candidate baseline. Es apto para uso
interno real como sistema gobernado, local y evidence-first para crear,
auditar y certificar proyectos derivados. No es un runtime autonomo.

Estado de release:
- RC1: GO
- P0/P1: ninguno conocido
- Suite global: `601 passed, 1 skipped`
- Atlas CI: PASS
- Health report: PASS con workflow observations cache y freshness policy
- Evidence Pipeline: PASS
- Failure Registry: PASS
- Model Routing: PASS en modo advisory

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

## Roadmap inmediato

V3 esta congelado. Solo acepta P0/P1.

Ver `ROADMAP.md` para objetivos preliminares de V4. V4 no esta disponible en
este release.

## Desarrollo y tests

Prerequisito mínimo para correr la suite local:

```powershell
pip install -r requirements-dev.txt
pytest tests/
```

Los tests resuelven la raíz del repo desde el checkout actual y aceptan override por `ATLAS_ROOT` si hiciera falta.

## Referencias rápidas

- [ARCHITECTURE.md](ARCHITECTURE.md)
- [ROADMAP.md](ROADMAP.md)
- [CONTRIBUTING.md](CONTRIBUTING.md)
- [AGENTS.md](AGENTS.md)
- [ATLAS_STATUS.md](ATLAS_STATUS.md)
- [ATLAS_NEXT_STEPS.md](ATLAS_NEXT_STEPS.md)
- [docs/architecture.md](docs/architecture.md)
- [docs/release_candidate_rc1.md](docs/release_candidate_rc1.md)
- [docs/release_notes_v3.md](docs/release_notes_v3.md)
- [docs/codex_system_prompt.md](docs/codex_system_prompt.md)
- [docs/mcp_read_only_evaluation.md](docs/mcp_read_only_evaluation.md)
