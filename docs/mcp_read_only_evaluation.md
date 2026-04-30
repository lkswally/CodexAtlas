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

## Official OpenAI Developer Docs MCP check (2026-04-30)

OpenAI's Docs MCP guide says the official Codex setup path is:

- `codex mcp add openaiDeveloperDocs --url https://developers.openai.com/mcp`
- `codex mcp list`
- or a direct entry in `~/.codex/config.toml`:

```toml
[mcp_servers.openaiDeveloperDocs]
url = "https://developers.openai.com/mcp"
```

Source:

- [Docs MCP | OpenAI Developers](https://developers.openai.com/learn/docs-mcp)

Local findings on this machine:

- `codex.exe` resolves to the installed Windows Store package under `C:\Program Files\WindowsApps\OpenAI.Codex_26.406.3494.0_x64__2p2nqsd0c76g0\app\resources\codex.exe`
- `codex --version` fails with `Access is denied`
- `codex mcp --help` fails with `Access is denied`
- `codex mcp list` fails with `Access is denied`
- direct execution of the full binary path also fails with `Access is denied`
- `C:\Users\Lucas\.codex\config.toml` exists, but it has no `mcp_servers.openaiDeveloperDocs` entry
- `C:\Proyectos\Codex-Atlas\.codex\config.toml` does not exist today

Interpretation:

- the official MCP server is real and the official configuration path is valid
- this machine does **not** currently offer a working Codex CLI path for MCP setup or verification
- the failure is not limited to the workspace sandbox, because the same denial occurs when the binary is invoked directly and with elevated execution
- the most likely blocker is the current Windows Store packaging / execution surface for `codex.exe`, not Atlas policy

Atlas decision for now:

- do **not** write `~/.codex/config.toml` automatically
- do **not** create a project-scoped `.codex/config.toml` without explicit evidence that this Codex build will honor it for MCP
- keep `docs_search_adapter` as the active read-only path
- keep lifecycle logging and approval gating in place

If Codex CLI becomes operational later, the next safe test is:

```powershell
codex mcp add openaiDeveloperDocs --url https://developers.openai.com/mcp
codex mcp list
```

Only after those commands work should Atlas consider moving `docs_search` from adapter-backed execution to a verified real MCP path.

## Rollback

1. Set `experimental_enabled` to `false` for `docs_search` in `config/mcp_profiles.json`.
2. Keep `atlas_decision` as `watchlist` or `defer`.
3. Re-run `tools/atlas_governance_check.py`.
4. Atlas will fall back to local docs plus explicit manual browsing.
