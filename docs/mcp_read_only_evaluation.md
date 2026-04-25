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
- The recommendation is advisory only until a governed approval exists.
- Atlas now supports an internal `docs_search` adapter in read-only mode as the safe execution path for this stage.
- The adapter now ranks deduplicated official references, exposes structured summaries, key points, confidence and a possible-staleness signal.
- The curated docs catalog now lives in `config/docs_search_catalog.json` instead of inside the adapter code.
- Each catalog entry now carries explicit freshness metadata (`last_verified`, `freshness_window_days`) plus lifecycle status (`active`, `watchlist`, `deprecated`).
- Governance now validates catalog structure, duplicate protection and freshness metadata before Atlas can claim the adapter surface is healthy.
- The integration is logged through existing observability paths.
- No automatic connector activation happens inside Atlas.

## Catalog freshness policy

- `active`: eligible for ranking as a normal result.
- `watchlist`: still searchable, but ranked below equally relevant active entries.
- `deprecated`: kept only for auditability and excluded from active ranking.
- `possible_outdated_results` becomes `true` when a returned entry is older than its own `freshness_window_days`.
- Atlas does not scrape the web automatically; freshness depends on deliberate catalog maintenance.
- `tools/docs_catalog_report.py` now provides a read-only health report over the curated catalog, including counts by status, expired entries, near-expiry entries, top topics and maintenance recommendations.

## Runtime inspection result on this machine

Current evidence:

- Official OpenAI docs confirm that Codex can connect to the Docs MCP through `codex mcp add ...` or `~/.codex/config.toml`.
- The local `~/.codex/config.toml` currently has no `mcp_servers.openaiDeveloperDocs` entry.
- The local `codex.exe` binary is present, but direct CLI invocation from this environment currently fails with `Access is denied`.

Decision:

- Do **not** claim a real MCP runtime integration yet.
- Use the internal read-only adapter as the controlled execution path.
- Keep simulated execution as fallback if the adapter fails.

## Rollback

1. Set `experimental_enabled` to `false` for `docs_search` in `config/mcp_profiles.json`.
2. Keep `atlas_decision` as `watchlist` or `defer`.
3. Re-run `tools/atlas_governance_check.py`.
4. Atlas will fall back to local docs plus explicit manual browsing.
