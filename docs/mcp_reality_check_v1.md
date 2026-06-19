# Codex-Atlas V4.0 MCP Reality Check V1

## Executive Summary

This report audits the MCP and connector reality of the current Codex-Atlas
environment after the V3 RC1 baseline. It does not enable, install, repair or
reconfigure any MCP. The goal is to separate real working surfaces from local
policy profiles, advisory readiness checks and missing integrations.

The current environment has working read-only GitHub CLI access, a locally
available Playwright runtime with browser binaries, and a healthy Engram CLI
store according to `engram doctor --json`. However, Atlas should not treat
Engram, GitHub, Playwright, Notion, Context7, 21st Magic, Vercel, Google Drive,
Slack, Telegram, Supabase or Postgres as active Atlas MCP integrations yet.

The only MCP server found in the local Codex config is `node_repl`. Atlas
readiness still reports Codex MCP CLI verification as unavailable in this
environment with `[WinError 5] Acceso denegado`. Repository MCP profiles remain
default-deny, approval-bound and mostly advisory.

## Inventory Method

- Searched repository MCP references in `.claude/`, `.codex/`, `config/`,
  `docs/` and MCP-like filenames.
- Read local Codex config from the user profile with secret values avoided.
- Checked Claude Desktop config presence.
- Checked relevant CLI presence without installing packages.
- Ran only read-only local readiness tools.
- Ran only read-only connector probes.
- Did not write test memories, pages, messages, deployments or database queries.

## Configuration Findings

- Repository MCP-related config files found:
  - `config/mcp_profiles.json`
  - `config/mcp_permission_matrix_rules.json`
  - `config/chrome_devtools_mcp_rules.json`
  - `config/component_inspiration_profiles.json`
  - `config/creative_pipeline_profiles.json`
- Documentation and status references found in:
  - `README.md`
  - `ARCHITECTURE.md`
  - `ROADMAP.md`
  - `ATLAS_STATUS.md`
  - `ATLAS_NEXT_STEPS.md`
  - `docs/mcp_read_only_evaluation.md`
  - `docs/architecture_audit_v1.md`
- Local Codex user config contains `mcp_servers.node_repl`.
- No project-scoped `.claude` or `.codex` MCP config was found in the repo.
- Claude Desktop config was not found at the expected AppData path.
- No relevant secret-bearing environment variable names were visible for
  Engram, Notion, Context7, 21st Magic, Vercel, Google Drive, Slack, Telegram,
  Supabase or Postgres.
- MCP Protocol after V4.3: `VALIDATED` for the minimal stdio diagnostic cycle
  `initialize -> notifications/initialized -> tools/list -> shutdown`.

## MCP Status Table

| MCP | Config encontrado | Prueba ejecutada | Estado | Evidencia | Riesgo | Recomendacion |
|---|---|---|---|---|---|---|
| Engram | `config/mcp_profiles.json` has `engram` as `external_mcp`, `atlas_decision: defer`, `experimental_enabled: false`; local Codex config does not list Engram MCP. | V4.0: `engram --version`, `engram --help`, `engram doctor --json`. V4.1: sandboxed `ENGRAM_DATA_DIR`, `engram save`, `engram search`. V4.2: official repo study and local `engram mcp --tools=agent --project codex-atlas-v4-mcp-sandbox` process harness. | PARTIAL_MCP_AVAILABLE | Standalone CLI remains `WORKING_STANDALONE`; MCP process startup/shutdown in sandbox passed with no stderr/stdout and no errors. Handshake/tool calls were not attempted because no Engram-specific raw handshake recipe was found in official docs. Codex setup remains unexecuted. | False confidence: MCP process lifecycle success is not MCP tool readiness. Official `engram setup codex` mutates global Codex config and prompt files. | Keep global MCP disabled. Next gate is a standard MCP initialize handshake in sandbox, still without global config changes. |
| Playwright | `config/creative_pipeline_profiles.json` and `config/playwright_visual_qa_profiles.json` track Playwright visual QA as watchlist/advisory. Browser smoke workflow exists and remains manual/opt-in. | `tools/playwright_visual_qa_readiness.py`; prior browser smoke evidence from V3. | PARTIAL | Readiness returned `playwright_available: true`, `browsers_available: true`, `safe_to_run: true`, but also `advisory_only: true`, `requires_human_approval: true`, `requires_decision_council: true`. Prior manual smoke run `27724893071` passed with artifact `7709863742`. | Browser automation can hang, drift by environment or be mistaken for design proof. | Keep manual/opt-in. Allow into V4 runtime only as an approval-bound evidence step, not autonomous default. |
| GitHub | `config/mcp_profiles.json` has GitHub on watchlist; `github_connector_readiness.py` exists; GitHub CLI is installed and authenticated. | `gh auth status`; `gh run list --limit 1`; `tools/github_connector_readiness.py`. | PARTIAL | `gh` is logged in; last run listed: `27765466069`, `success`. Readiness says theoretical read-only governance is ready, but `advisory_only: true` and runtime probe was not requested. | CLI works, but Atlas GitHub connector/MCP is still governance/advisory, and write operations remain blocked. | Use GitHub CLI for explicit read-only checks. Do not call this an active Atlas MCP until a read-only connector probe is implemented and documented. |
| Notion | No repo MCP server config found. Notion skills may exist in the host Codex plugin environment, but Atlas has no Notion MCP profile activated. | Config/env presence only; no page reads or writes. | MISSING | No Notion env var names visible; no Notion entry in MCP profiles. | Confusing host app/plugin availability with Atlas runtime capability. | Leave out of V4 runtime until a read-only profile, secret policy and probe exist. |
| Context7 | Mentioned in `component_inspiration_profiles.json` and `creative_pipeline_profiles.json`; no active MCP server config found. | Config/env presence only. | ADVISORY_ONLY | Profiles list Context7 as future documentation/design grounding; expected env vars are empty, but no server is configured. | Treating design inspiration metadata as a live connector. | Keep advisory. Add a read-only probe only if V4 runtime needs external doc grounding beyond local docs. |
| Magic / 21st | `config/mcp_profiles.json` has `21st_magic` watchlist disabled; component and creative profiles require `TWENTYFIRST_API_KEY`. | Config/env presence only; no component generation. | DEPRECATE_LATER | `experimental_enabled: false`; `ATLAS_NEXT_STEPS.md` says keep `21st_magic` disabled until an exposed key is revoked and a fresh key is stored outside repo. No `TWENTYFIRST_API_KEY` env var name was visible. | Secret exposure history and derivative/generated UI risk. | Keep disabled. Deprecate from active V4 scope unless a fresh key, read-only mode and derivative-risk policy are approved. |
| Filesystem | `config/mcp_profiles.json` has `filesystem` as `external_mcp`, `atlas_decision: defer`; current Codex workspace filesystem access works. | Verified allowed workspace access by repository reads and report creation path; no external path access tested. | PARTIAL | Built-in workspace file access is functional under sandbox rules, but no external filesystem MCP server is configured. | External path access could bypass repo-local safety expectations. | Keep normal repo filesystem as the default. Do not add external filesystem MCP without path allowlists and approval. |
| Vercel | `mcp_permission_matrix_rules.json` includes Vercel platform defaults; no Vercel MCP config found. | `Get-Command vercel -ErrorAction SilentlyContinue`. | MISSING | Vercel CLI was not found; no deploy or account probe was run. | Accidental deploy if later connected without strict dry-run rules. | Leave out of V4 runtime. Add read-only deployment metadata checks only after explicit approval. |
| Google Drive | Permission matrix includes `google_drive`; no MCP server config found. | Config/env presence only; no private document read. | MISSING | No visible Google Drive env var names; no active config. | Privacy exposure if document reads are introduced casually. | Keep missing/advisory. Require read-only scope and explicit document boundaries before use. |
| Slack | No repository MCP config found. | Config/env presence only; no messages sent. | MISSING | No visible Slack env var names; no readiness tool found. | Message send side effects and workspace privacy. | Do not include in V4 runtime until a read-only channel metadata probe and send block are defined. |
| Telegram | No repository MCP config found. | Config/env presence only; no messages sent. | MISSING | No visible Telegram env var names; no readiness tool found. | Message send side effects and token risk. | Do not include in V4 runtime. |
| Supabase / Postgres | `mcp_profiles.json` has generic `database_schema` watchlist; permission matrix has `database`; Engram help references Postgres DSN for Engram cloud only. | Config/env presence only; no queries. | ADVISORY_ONLY | No visible Supabase/Postgres env var names; no active DB MCP config. | Database reads may expose business data; writes/migrations are high risk. | Keep schema inspection advisory-only until a redacted schema artifact or read-only DSN policy exists. |
| node_repl | Local user Codex config contains `mcp_servers.node_repl`. This is not an Atlas V4 target MCP. | `tools/mcp_readiness_check.py`. | CONFIGURED_NOT_TESTED | Readiness saw `node_repl` and parser also reported `node_repl.env`; Codex MCP list failed with `[WinError 5] Acceso denegado`. | Treating a host runtime helper as an Atlas connector. | Exclude from Atlas runtime planning unless separately documented. |

## Engram Reality Check

Engram is the highest-priority ambiguity because it is present as a binary and
has real local state, but Atlas policy still defers it.

Observed facts:

- `engram --version` returned `engram 1.16.3`.
- `engram --help` exposes `mcp [--tools=PROFILE] [--project NAME]` with stdio
  transport and profiles `agent`, `admin` and `all`.
- `engram doctor --json` returned `status: ok` in the V4.0 real-store
  read-only check.
- V4.1 reran `engram doctor --json` with `ENGRAM_DATA_DIR` set to
  `.atlas_test_tmp/engram_sandbox`; it reported 4 total checks, 4 ok, 0
  warnings, 0 blocked and 0 errors.
- V4.1 saved memory `codex-atlas-v4-engram-sandbox-test` with project
  `codex-atlas-v4-sandbox` and recovered it through `engram search`.
- The sandbox created `.atlas_test_tmp/engram_sandbox/engram.db`, which is
  ignored by git through the existing `.atlas_test_tmp/` rule.
- V4.2 studied the official Engram repository and confirmed the official Codex
  setup path writes `[mcp_servers.engram]`, `engram-instructions.md`, and
  `engram-compact-prompt.md`; the setup command was not executed.
- V4.2 started `engram mcp --tools=agent --project
  codex-atlas-v4-mcp-sandbox` with `ENGRAM_DATA_DIR` under
  `.atlas_test_tmp/engram_mcp_harness`; startup and shutdown passed.
- No Engram MCP server is configured in local Codex config.
- `config/mcp_profiles.json` keeps Engram deferred and disabled.

Classification after V4.2: `PARTIAL_MCP_AVAILABLE`.

Reason: Engram is locally installed and operational as a CLI/store, the V4.1
sandbox proved a safe save/search roundtrip without touching real memory, and
the V4.2 harness proved the official MCP process can start and stop under a
sandbox data dir. It is not Atlas MCP-ready yet, because no Codex/Claude config
was changed and no MCP initialize/tool-call handshake was executed.

## What To Fix First

1. Define an MCP proof protocol that separates binary presence, server config,
   authentication, read-only probe and write-safe sandbox tests.
2. For Engram, design the next MCP-only stdio test using a temporary
   `ENGRAM_DATA_DIR`; require explicit approval before any config change.
3. Update `mcp_readiness_check.py` later to avoid counting nested env tables
   such as `node_repl.env` as independent MCP servers.
4. Decide whether GitHub should remain CLI-only or gain an Atlas read-only
   connector probe.
5. Keep Playwright browser automation manual until V4 runtime has a specific
   evidence gate and timeout policy.

## What To Deprecate

- `21st_magic` should remain disabled and can be treated as `DEPRECATE_LATER`
  for V4 unless the old key exposure risk is resolved and a fresh external
  policy is approved.
- Any connector profile that only duplicates local Atlas checks should stay out
  of the V4 runtime.

## What To Leave Advisory

- Context7 for future documentation/design grounding.
- Supabase/Postgres schema inspection until a safe read-only schema source
  exists.
- GitHub connector readiness until runtime read probes are explicit.
- Playwright visual QA until manual approval and browser evidence policy are
  part of runtime design.

## What Can Enter V4 Runtime

Eligible candidates, in order:

1. GitHub read-only observation through existing CLI, because `gh` is already
   authenticated and read-only run listing works.
2. Playwright as an opt-in evidence step, because local readiness is true and
   prior smoke evidence exists.
3. Engram only as standalone memory until an MCP stdio test proves the same
   isolation without modifying global config.

Not eligible yet:

- Notion, Vercel, Google Drive, Slack, Telegram, Supabase/Postgres, Context7 and
  21st Magic.

## Decision

Result: `WARN`.

There are no P0/P1 findings in this audit because no active Atlas MCP is failing
inside the V3 baseline. The V4 risk is posture drift: several integrations are
documented or visible as profiles, but only a small subset has real local
evidence. V4.3 validates the base MCP protocol cycle, but no target MCP should
be declared fully integrated as an Atlas runtime connector yet.
