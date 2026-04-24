# Codex Atlas (Canonical)

`C:\Proyectos\Codex-Atlas` es la fuente de verdad canonica de ATLAS:
- sistema padre
- factory reusable
- configuracion madre de Codex para proyectos derivados
- governance, workflows, policies, validators y tooling minimo

REYESOFT es un proyecto derivado y mantiene su runtime propio.
ATLAS no debe vivir escondido dentro de REYESOFT ni depender de artefactos Claude-only.

## Estructura primaria en raiz

La configuracion madre vive en la raiz del repo/carpeta:
- `AGENTS.md`
- `commands/`
- `policies/`
- `memory/`
- `agents/`
- `workflows/`
- `docs/`
- `tools/`
- `adapters/`

## Operacion sobre derivados

Atlas opera proyectos derivados desde afuera.
Ejemplo:

```powershell
python C:\Proyectos\Codex-Atlas\tools\atlas_governance_check.py --project C:\Proyectos\REYESOFT
python C:\Proyectos\Codex-Atlas\tools\atlas_dispatcher.py --project C:\Proyectos\REYESOFT audit-repo
```

Los derivados no necesitan shims de Atlas si exponen una metadata minima en `.atlas-project.json`.

## Legacy compat

`00_SISTEMA/_meta/atlas/` se conserva solo como mirror legacy de compatibilidad.
No es la fuente principal de Atlas.

## Restricciones vigentes

Atlas no incluye:
- `.claude`
- `CLAUDE.md` como fuente principal
- hooks automaticos
- MCP real
- Engram
- Pixel Bridge
- deploy automatico
- dependencias externas nuevas

## Referencias rapidas

- [AGENTS.md](/C:/Proyectos/Codex-Atlas/AGENTS.md)
- [ATLAS_STATUS.md](/C:/Proyectos/Codex-Atlas/ATLAS_STATUS.md)
- [ATLAS_NEXT_STEPS.md](/C:/Proyectos/Codex-Atlas/ATLAS_NEXT_STEPS.md)
- [docs/architecture.md](/C:/Proyectos/Codex-Atlas/docs/architecture.md)
- [docs/claude_to_codex_mapping.md](/C:/Proyectos/Codex-Atlas/docs/claude_to_codex_mapping.md)
