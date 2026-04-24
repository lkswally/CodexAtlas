# MCP Read-only Evaluation

## Goal

Evaluate which MCP should be connected first in Atlas without turning the system into a risky connector hub.

## Comparative assessment

| Candidate | Fit with Atlas | Current value | Main risk | Current decision |
|---|---|---|---|---|
| `docs_search` | High | Strong support for research, current docs and version-sensitive decisions | low risk, but must stay approval-gated | `experimental_read_only` |
| `github` | Medium | Useful in principle for repo, issue and PR inspection | connector surface in this environment is not yet the read-only repo surface Atlas actually needs | `watchlist` |
| `filesystem` (restricted) | Low to medium | Cross-workspace inspection can help occasionally | prompt injection and broader file-surface exposure for work Atlas can usually do locally | `defer` |
| `engram` | Medium conceptually, low operationally today | persistent memory could help later | external memory drift, lock-in and duplicate source-of-truth risk against Atlas file-backed memory | `defer` |

## Recommended first MCP

`docs_search`

### Why it wins first

- It is read-only by nature.
- It supports a real Atlas problem: evaluating unstable documentation, APIs and versions before changing the mother config.
- It does not require writing to external systems.
- It does not force secrets or tokens into the repo.
- Atlas already has a conservative routing model that can suggest it without auto-activating it.

## Why GitHub is not first right now

- GitHub remains strategically interesting, but the currently exposed app surface in this environment is too narrow for Atlas' intended read-only repo inspection workflow.
- Atlas should wait until the connector surface supports repository, branch, issue and PR reads in a way that maps cleanly to governance and certification use cases.

## Permission model

- default deny
- read-only only
- human approval required before any activation
- no secret material stored in the repo
- no automatic writes to external services

## Experimental scope

The current experimental integration is deliberately narrow:

- Atlas may recommend `docs_search` in the orchestrator.
- The recommendation is advisory only.
- The integration is logged through existing observability paths.
- No automatic connector activation happens inside Atlas.

## Rollback

1. Set `experimental_enabled` to `false` for `docs_search` in `config/mcp_profiles.json`.
2. Keep `atlas_decision` as `watchlist` or `defer`.
3. Re-run `tools/atlas_governance_check.py`.
4. Atlas will fall back to local docs plus explicit manual browsing.
