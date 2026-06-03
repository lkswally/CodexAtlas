# n8n API Connector Readiness Policy

## Purpose

`n8n_api_connector_readiness` exists to evaluate whether a future API connection to n8n would be safe before Atlas ever reads or writes workflows through HTTP.

The layer is intentionally advisory-only. It does not connect to n8n, does not read an API key, and does not execute requests.

## What This Layer Evaluates

- whether `N8N_BASE_URL` appears configured or is still missing
- whether an API key would be required
- whether the current posture is `not_configured`, `read_only_ready`, `sandbox_write_ready` or `blocked`
- whether writes are still disabled by default
- whether execute remains blocked
- whether sandbox tags are present for any future write
- whether workflow creation would stay `active:false`
- whether production webhook URLs require explicit approval

## Hard Boundaries

- no real n8n connection
- no API key reading
- no `.env.local` inspection
- no HTTP requests
- no workflow creation
- no workflow activation
- no workflow execution
- no credential or secret reads

## Safe Defaults

- `N8N_ALLOW_WRITE` must be treated as `false` by default
- `N8N_ALLOW_EXECUTE` must be treated as `false` always
- only `list_workflows` and `get_workflow` can become read-only candidates
- `create_workflow` and `update_workflow` may only become sandbox-ready with:
  - explicit human approval
  - sandbox tag present
  - `active:false`
- `activate_workflow`, `execute_workflow`, `delete_workflow` and credential reads stay blocked

## Approval Boundary

Any future write-like action requires:

- explicit human approval
- sandbox tagging
- inactive workflow posture
- manual rollback thinking

This layer does not grant permission to execute anything by itself. It only reports whether a future connector path could be considered safe enough for later review.
