# Breadcrumbs

## 2026-04-23 19:03 (America/Buenos_Aires)
- Change: created the minimum Codex-native Atlas factory structure
- Reason: strengthen Level 1 bootstrap without copying Claude-oriented setup
- Files: AGENTS.md, ATLAS_STATUS.md, ATLAS_NEXT_STEPS.md, agents/, workflows/, policies/, commands/, validators/, memory/, docs/
- Impact: faster continuity across sessions and clearer parent-vs-derived boundaries
- Residual risk: most of the new surface is documentary and still depends on disciplined maintenance
- Rollback: delete the new directories and restore the previous governance validator expectations

## 2026-04-23 19:35 (America/Buenos_Aires)
- Change: promoted root-level commands, policies and memory to the primary mother configuration
- Reason: align Atlas with a Codex-native structure and stop treating the seed under `00_SISTEMA/_meta/atlas/` as the main home
- Files: commands/, policies/, memory/, tools/, adapters/reyesoft/, 00_SISTEMA/_meta/atlas/
- Impact: Atlas is now root-first while still preserving a reversible legacy layer
- Residual risk: root-first and legacy files must stay synchronized
- Rollback: switch tooling back to legacy-first path resolution
