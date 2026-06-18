# Engram Sandbox Test V1

## Summary

Codex-Atlas V4.1 tested Engram with an explicit sandbox data directory and no
global MCP configuration changes. The standalone CLI path can save and recover a
test memory when `ENGRAM_DATA_DIR` points at `.atlas_test_tmp/engram_sandbox`.

Final classification: `WORKING_STANDALONE`.

This does not mean Engram is working as an Atlas MCP. It means the local Engram
binary and standalone store operations are safe enough to consider a later,
separate MCP stdio test.

## Constraints Honored

- No real Engram memory was intentionally touched.
- `ENGRAM_DATA_DIR` was set to the sandbox path for version, help, doctor,
  save and search commands.
- No sensitive data was written.
- No Codex, Claude or global MCP config was modified.
- No external service was written.
- No CI, workflow or Evidence Pipeline file was changed.

## Sandbox

- Path: `.atlas_test_tmp/engram_sandbox`
- Absolute path during test: `D:\Proyectos\Codex-Atlas\.atlas_test_tmp\engram_sandbox`
- Git state: ignored by the existing `.atlas_test_tmp/` rule in `.gitignore`
- File observed after write/read: `.atlas_test_tmp/engram_sandbox/engram.db`

## Commands Run

```powershell
$env:ENGRAM_DATA_DIR=(Resolve-Path '.atlas_test_tmp\engram_sandbox').Path
engram --version
```

Result:

```text
engram 1.16.3
```

```powershell
$env:ENGRAM_DATA_DIR=(Resolve-Path '.atlas_test_tmp\engram_sandbox').Path
engram doctor --json
```

Result summary:

```text
status: ok
total: 4
ok: 4
warnings: 0
blocked: 0
errors: 0
sessions_evaluated: 0
pending_mutations_evaluated: 0
```

```powershell
$env:ENGRAM_DATA_DIR=(Resolve-Path '.atlas_test_tmp\engram_sandbox').Path
engram save "codex-atlas-v4-engram-sandbox-test" "Sandbox-only test memory for Codex-Atlas V4.1 Engram validation. No secrets." --type note --project codex-atlas-v4-sandbox --scope local
```

Result:

```text
Memory saved: #1 "codex-atlas-v4-engram-sandbox-test" (note)
```

```powershell
$env:ENGRAM_DATA_DIR=(Resolve-Path '.atlas_test_tmp\engram_sandbox').Path
engram search "codex-atlas-v4-engram-sandbox-test" --project codex-atlas-v4-sandbox --limit 5
```

Result summary:

```text
Found 1 memories:
[1] #1 (note) - codex-atlas-v4-engram-sandbox-test
project: codex-atlas-v4-sandbox
```

## Result

| Check | Result |
|---|---|
| Version command | PASS |
| Help command | PASS |
| Doctor in sandbox | PASS |
| Save test memory in sandbox | PASS |
| Search test memory in sandbox | PASS |
| Real memory intentionally touched | No |
| Global MCP config modified | No |
| Atlas MCP integration active | No |

## Classification

`WORKING_STANDALONE`

Engram can run standalone CLI operations with a sandboxed data directory. The
next gate is not feature work; it is a controlled MCP stdio proof using the same
sandbox isolation and without changing global configuration.
