# Codex-native Operational Parity

This document captures the safe adaptation of useful operational patterns from
`Emaleo0522/claude-vibecoding` into Codex-Atlas.

Atlas does not copy the Claude runtime. Parity means comparable operational
discipline, not identical architecture.

## Scope

Adapt:
- explicit handoff structure
- evidence-first closure
- delegation stop rules
- context resume discipline
- manual quality hook bundle

Do not adapt:
- `.claude/`
- `CLAUDE.md`
- automatic hooks
- mandatory Engram
- deployer
- Pixel Bridge
- installers
- Claude-only runtime behavior
- opaque automation

## Atlas Handoff Envelope

Every Atlas command or human handoff should make these fields explicit:

- `status`: ready, needs_improvement, blocked, skipped or error
- `task`: what was attempted
- `changed_or_reviewed_files`: files touched or inspected
- `validation`: commands run, evidence collected and result
- `blockers`: issues that prevent safe closure
- `warnings`: risks that need attention but do not block by themselves
- `rollback`: how to undo the change when applicable
- `next_action`: the smallest useful follow-up

The dispatcher already exposes an `envelope` for implemented commands. This
document makes the contract explicit for Codex-native work.

## Evidence Index

Evidence is not a feeling. Before declaring a task ready, collect a compact
index of what proves the state:

- git branch and working-tree status
- changed files or declared file changes
- validation commands and outcomes
- blockers and warnings
- relevant docs or policies consulted
- runtime/readiness limits

The evidence index must be read-only. It may summarize local files and command
results, but it must not activate MCPs, install dependencies, run deploys or
mutate derived projects.

## Delegation Stop Rules

Stop local execution and split, review or ask for approval when:

- the next step would expand scope beyond the user's current block
- implementation depends on a risky architecture decision
- a command would mutate runtime, credentials, deploy state or external config
- the task needs evidence that is not locally available
- two quality signals conflict
- the change would add a new reusable skill, MCP, hook or provider
- the branch already contains unrelated work that would make review unclear

Delegation is useful only when the subtask is concrete, bounded and does not
hide responsibility.

## Context Resume Protocol

When resuming work, read from explicit local evidence before acting:

1. Check `git status`.
2. Read the latest relevant branch/commit context.
3. Review `memory/context_refresh_protocol.md` and `memory/breadcrumbs.md`.
4. Re-run the smallest relevant verification command.
5. State what is known, what is dirty and what remains uncertain.

Do not reconstruct context from vibes, hidden memory or external runtime state.

## Manual Quality Hook Bundle

Atlas does not use automatic hooks at this stage. The Codex-native equivalent is
a manual bundle of checks that a human or Codex can run before handoff:

```powershell
python tools\atlas_verify.py
python tools\atlas_governance_check.py
python tools\atlas_dispatcher.py audit-repo
python tools\mcp_readiness_check.py
python tools\atlas_dispatcher.py operational-parity-report
```

For derived projects, add:

```powershell
python tools\atlas_dispatcher.py --project <project_root> quality-gate-report
```

## Readiness States

- `ready`: artifacts exist and no forbidden runtime was detected
- `needs_improvement`: parity artifacts exist partially or evidence is thin
- `blocked`: a Claude-only runtime artifact or unsafe automation was detected

Readiness is advisory. It does not grant permission to activate MCPs, install
dependencies, deploy or write outside the requested scope.
