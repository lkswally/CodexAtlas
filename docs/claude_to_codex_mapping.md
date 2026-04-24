# Claude to Codex Mapping

This document keeps inspiration from Claude-oriented repos separate from Codex-native implementation.

## Mapping

- `CLAUDE.md` -> `AGENTS.md` plus focused docs under `docs/`
- Claude system prompt logic -> `docs/codex_system_prompt.md` plus policy and workflow docs
- `~/.claude/agents` -> project-local `agents/` documentation and Codex global agents outside the repo
- `~/.claude/hooks` -> manual validators and policies, not automatic hooks
- Claude settings files -> repo docs plus local Codex config outside the repo
- Engram MCP -> markdown and JSON memory files under `memory/`
- reactive Claude guards -> explicit policies plus manual validation
- deploy agent -> documented workflow with human approval, not automatic deploy
- certification phase -> `certify-project` plus policy-backed manual quality gates

## Atlas-native placement

- mother configuration -> root-level `commands/`, `policies/`, `memory/`, `agents/`, `workflows/`
- derived-project notes -> `adapters/`
- executable checks -> `tools/`
- legacy compatibility only -> `00_SISTEMA/_meta/atlas/`

## Rejected in Level 1

- `.claude` directories
- mandatory MCP memory backends
- Pixel Bridge
- hook automation
- install scripts tied to Claude products
