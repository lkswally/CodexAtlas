# ATLAS Core Metadata

Legacy compatibility mirror: este directorio vive en `C:\Proyectos\Codex-Atlas` solo para preservar compatibilidad.
No es la fuente primaria de Atlas.

Incluye:
- `atomic_command_registry.json`: mirror legacy del contracto principal en `commands/`
- `mcp_connector_policy.md`: mirror legacy del archivo principal en `policies/`
- `context_refresh_protocol.md`: mirror legacy del archivo principal en `memory/`

Derivados (ej: REYESOFT):
- pueden tener un adapter registry (instancia) y punteros a estas policies
- no deben copiar el core tooling en forma divergente

El resto de la factory Codex-native vive en la raiz canonica de Atlas:
- `adapters/`
- `agents/`
- `commands/`
- `workflows/`
- `policies/`
- `memory/`
- `docs/`
- `tools/`
