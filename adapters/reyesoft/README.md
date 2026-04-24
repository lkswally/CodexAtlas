# REYESOFT Adapter

This directory documents how REYESOFT consumes Atlas without turning Atlas into REYESOFT.

## Current contract

- REYESOFT keeps its own runtime and business logic
- REYESOFT identifies itself through `.atlas-project.json`
- Atlas tools run from `C:\Proyectos\Codex-Atlas\tools\` with `--project C:\Proyectos\REYESOFT`

## Compatibility note

- Atlas canonical structure is root-first
- REYESOFT no longer keeps active Atlas core files in product paths
- Previous Atlas shims, docs and mirrors were moved to `00_SISTEMA/_legacy/atlas_deprecated_2026-04-23/`
