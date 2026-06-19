# Engram Official Integration Study

## Executive Summary

Codex-Atlas V4.2 studied the official Engram repository before proposing any
integration. The current Atlas posture is:

- Standalone Engram CLI: `WORKING_STANDALONE`.
- Engram MCP process lifecycle in sandbox: `PARTIAL_MCP_AVAILABLE`.
- Engram MCP handshake/tool calls: not attempted.
- Atlas runtime integration: not implemented.

The official design is agent-first MCP over stdio, backed by local SQLite +
FTS5, with curated memory writes through `mem_*` tools. The official Codex path
is `engram setup codex`, which registers `[mcp_servers.engram]`, writes Engram
Memory Protocol instructions, writes a compaction prompt, and requires Codex
restart. Atlas should not run that setup yet because it mutates global Codex
configuration and would turn a study into user-level activation.

Recommended next gate: build a raw MCP stdio handshake only if it follows the
standard MCP initialization protocol and Engram's official `engram mcp
--tools=agent` process model. Until then, Atlas may document Engram as
standalone-proven and MCP-process-available, but not MCP-ready.

Official sources used:

- https://github.com/Gentleman-Programming/engram
- https://github.com/Gentleman-Programming/engram/blob/main/README.md
- https://github.com/Gentleman-Programming/engram/blob/main/DOCS.md
- https://github.com/Gentleman-Programming/engram/blob/main/docs/AGENT-SETUP.md
- https://github.com/Gentleman-Programming/engram/blob/main/docs/ARCHITECTURE.md
- https://github.com/Gentleman-Programming/engram/blob/main/internal/setup/setup.go
- https://github.com/Gentleman-Programming/engram/blob/main/internal/mcp/mcp.go
- https://github.com/Gentleman-Programming/engram/blob/main/cmd/engram/main.go

## Engram Architecture

Engram is a single Go binary that exposes the same memory system through CLI,
HTTP API, MCP stdio server and TUI. Its local-first storage is SQLite with FTS5.
The default local store is `~/.engram/engram.db`, and `ENGRAM_DATA_DIR` overrides
that location.

The MCP path is:

```text
Agent
  -> MCP stdio
  -> engram mcp
  -> SQLite + FTS5
```

Official MCP command shape:

```text
engram mcp --tools=agent
```

Useful startup options:

- `--tools=agent`: registers the agent profile.
- `--tools=admin`: registers admin/manual curation tools.
- `--tools=agent,admin` or individual tools are supported.
- `--project NAME`: sets process-level `MCPConfig.DefaultProject`.
- `ENGRAM_PROJECT=NAME`: environment alternative to `--project`.
- `ENGRAM_DATA_DIR=PATH`: controls the database directory.

## Memory Model

Engram stores:

- `sessions`
- `observations`
- `observations_fts`
- `user_prompts`
- `prompts_fts`
- `memory_relations`

The official model is curated memory, not raw event ingestion. Agents should
save structured summaries after significant decisions, discoveries, bugfixes,
patterns or configuration changes. The documented `mem_save` content shape is:

- `What`
- `Why`
- `Where`
- `Learned`

Search uses FTS5 through `mem_search`, with context retrieval through
`mem_context`, full observation retrieval through `mem_get_observation`, and
session closure through `mem_session_summary`.

## MCP Tools

The official agent profile includes tools such as:

- `mem_save`
- `mem_search`
- `mem_context`
- `mem_session_summary`
- `mem_session_start`
- `mem_session_end`
- `mem_get_observation`
- `mem_suggest_topic_key`
- `mem_capture_passive`
- `mem_save_prompt`
- `mem_update`
- `mem_current_project`
- `mem_judge`
- `mem_compare`
- `mem_doctor`
- `mem_review`
- `mem_pin`
- `mem_unpin`

Admin tools include destructive or curation-oriented operations such as delete,
stats, timeline and project merge. Atlas should not expose admin tools in a
runtime integration by default.

## Project Resolution

Official Engram project resolution happens at MCP tool call time. It prefers:

1. nearest `.engram/config.json` under the enclosing git root,
2. git origin remote,
3. git root directory,
4. single git child,
5. ambiguous error for multiple git children,
6. directory basename fallback.

For Atlas, the safest future integration is to pass a stable process-level
project with `--project codex-atlas` or `ENGRAM_PROJECT=codex-atlas` only after
deciding whether Atlas wants repo-level memory or per-derived-project memory.

## Official Codex Setup

The official command is:

```text
engram setup codex
```

The official docs and code show that it:

- writes or updates Codex config,
- registers `[mcp_servers.engram]`,
- sets command to the resolved Engram executable,
- uses `args = ["mcp", "--tools=agent"]`,
- writes `engram-instructions.md`,
- writes `engram-compact-prompt.md`,
- sets top-level `model_instructions_file`,
- sets top-level `experimental_compact_prompt_file`,
- requires restarting Codex.

On Windows the docs mention `%APPDATA%\codex\config.toml`; the code path uses
`APPDATA\codex\config.toml` when `APPDATA` exists. This differs from the current
local Codex Desktop config observed in V4.0 under `C:\Users\lksro\.codex`.
That discrepancy is a concrete risk: running setup could modify a config file
different from the one Atlas currently inspected.

`engram setup codex` was not executed.

## Atlas Architecture

Atlas V3/V4 currently has:

- local evidence pipeline,
- failure registry,
- model routing advisory policy,
- governance checks,
- health dashboard,
- MCP readiness/advisory profiles,
- Engram standalone sandbox proof,
- Engram MCP process harness proof.

Atlas does not yet have:

- active Engram MCP config,
- Memory Protocol injected into Codex,
- compaction recovery prompt wired through Engram,
- MCP client handshake or tool call implementation,
- runtime policy for when to save/read memory,
- contamination controls for production memory.

## Comparison

| Question | Engram official design | Atlas current state |
|---|---|---|
| Storage | SQLite + FTS5 under `ENGRAM_DATA_DIR` or default `~/.engram` | Sandbox proof used `.atlas_test_tmp`; production memory untouched |
| MCP transport | stdio subprocess via `engram mcp` | Harness starts and terminates subprocess only |
| Codex integration | `engram setup codex` mutates Codex config and prompts | Not executed; Atlas avoids global config mutation |
| Tool profile | `--tools=agent` for agents | Harness uses `--tools=agent` |
| Memory behavior | Proactive curated `mem_save`, recall via `mem_context`/`mem_search` | Not implemented in Atlas runtime |
| Project resolution | cwd/config/git or `--project`/`ENGRAM_PROJECT` | Harness uses explicit sandbox project |
| Compaction | Official compact prompt requires `mem_session_summary` | Not wired into Atlas |
| Admin tools | Separate profile | Not exposed |

## Findings

- Atlas V4.1 already matched Engram's safe storage override by using
  `ENGRAM_DATA_DIR`.
- Atlas V4.2 now matches the official process command shape:
  `engram mcp --tools=agent --project codex-atlas-v4-mcp-sandbox`.
- The MCP server can start in sandbox and remain alive for the startup window.
- The harness can terminate the MCP process and capture stdout/stderr.
- No official raw handshake snippet was found in Engram docs; therefore Atlas
  did not invent one.
- `engram setup codex` is the official convenience path, but it is global and
  mutating, so it is not appropriate during a study phase.

## Harness Result

Harness command:

```text
python tools\engram_mcp_harness.py --sandbox-dir .atlas_test_tmp\engram_mcp_harness --report .atlas_test_tmp\engram_mcp_harness\report.json --startup-seconds 2 --shutdown-timeout-seconds 5
```

Result summary:

```json
{
  "classification": "PARTIAL_MCP_AVAILABLE",
  "startup": {
    "status": "PASS",
    "exit_code_during_startup": null
  },
  "shutdown": {
    "status": "PASS",
    "exit_code": 1
  },
  "handshake_attempted": false,
  "handshake_status": "NOT_ATTEMPTED",
  "errors": []
}
```

The exit code after termination was recorded as evidence, not treated as
startup failure. There was no stdout/stderr output.

## Handshake

Handshake status: `NOT_ATTEMPTED`.

Reason: the official Engram docs explain MCP stdio setup and tools, but the
study did not find an Engram-specific raw JSON-RPC handshake recipe. A future
handshake test must use the standard MCP initialization flow deliberately and
must not send invented partial messages.

## Risks

- Running `engram setup codex` may alter global/user Codex config and prompt
  behavior.
- On this Windows machine, official setup path and observed Codex Desktop config
  path may differ.
- Engram's official Memory Protocol is mandatory/proactive; using it without an
  Atlas memory policy could save too much or save the wrong scope.
- Admin tools must not be exposed by default.
- Production memory contamination remains the main risk.
- Compaction prompt integration would alter Codex behavior globally.

## Advantages

- Official integration is simple and mature.
- SQLite + FTS5 is local-first and inspectable.
- `ENGRAM_DATA_DIR` gives Atlas a clean sandbox/prod separation.
- The agent tool profile avoids admin tools by default.
- The Memory Protocol is explicit about when to save and search.

## Disadvantages

- Official setup is not project-local by default.
- Codex setup mutates user-level files.
- Atlas needs a policy layer before enabling proactive memory writes.
- MCP readiness requires client-level handshake/tool-call proof, not just
  process lifecycle.

## Recommended Integration

Future Atlas integration should be staged:

1. Keep standalone CLI status as `WORKING_STANDALONE`.
2. Keep MCP lifecycle status as `PARTIAL_MCP_AVAILABLE`.
3. Add a separate MCP stdio handshake test using the standard MCP initialize
   flow and `ENGRAM_DATA_DIR` sandbox.
4. Add a sandbox MCP `mem_current_project`, `mem_save`, `mem_search` proof only
   after the handshake is correct.
5. Only then decide whether to use official `engram setup codex` or a manual
   Atlas-scoped config.
6. If integrating with Atlas runtime, use `--tools=agent`; do not expose admin
   tools.
7. Use `ENGRAM_DATA_DIR` sandbox for tests and a separate production data dir
   only after explicit approval.

## No Integration Recommended

Do not do these yet:

- Do not run `engram setup codex`.
- Do not modify `~/.codex/config.toml` or `%APPDATA%\codex\config.toml`.
- Do not write Codex instruction files.
- Do not wire compaction recovery into Codex.
- Do not make Atlas automatically call `mem_save`.
- Do not expose admin tools.
- Do not sync Engram Cloud.

## Future Runtime Design

```text
Codex Atlas
  -> Planner
  -> Executor
  -> Engram MCP
  -> Memory
  -> Evidence
  -> Verifier
  -> Failure Registry
  -> Dashboard
```

Read memory:

- at session start,
- before repeating prior architecture/integration work,
- when user asks to recall,
- after compaction recovery,
- before changing memory-sensitive policy.

Write memory:

- after a completed bugfix,
- after a confirmed architecture decision,
- after a non-obvious discovery,
- after a stable convention is established,
- after a session summary,
- after failure analysis that should influence future work.

Do not save:

- secrets, tokens or credentials,
- private external document contents,
- raw shell logs,
- raw tool-call firehoses,
- speculative plans not accepted by the user,
- transient CI noise,
- sensitive personal data.

Avoid contamination:

- require explicit project scope,
- use `topic_key` for evolving decisions,
- prefer curated summaries,
- keep test memory under sandbox `ENGRAM_DATA_DIR`,
- require review before production memory writes,
- keep Failure Registry as the source of failure facts and Engram as recall,
  not as a replacement registry.

## Roadmap

| Step | Status | Notes |
|---|---|---|
| Standalone CLI sandbox save/search | Done | V4.1 |
| Official repo study | Done | V4.2 |
| MCP process harness | Done | V4.2 |
| MCP stdio handshake | Not started | Must follow standard MCP initialization |
| MCP tool call sandbox proof | Not started | `mem_current_project`, `mem_save`, `mem_search` |
| Atlas memory policy | Not started | Required before runtime writes |
| Codex setup decision | Deferred | Official setup mutates global config |

## Decision

Classification: `PARTIAL_MCP_AVAILABLE`.

Engram is ready for the next sandbox-only MCP handshake study. It is not ready
for Atlas runtime integration.
