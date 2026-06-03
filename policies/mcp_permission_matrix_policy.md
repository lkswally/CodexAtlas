# Policy: mcp_permission_matrix_readiness

## Goal

Define a governed, advisory-only permission posture for MCP platform access before Atlas ever uses a new MCP for real work.

This layer exists to answer:

- what platform is being considered
- what capability level is being requested
- whether that level is allowed, blocked or only safe in a narrower mode
- what human approvals, dry-runs and rollback guarantees are required first

## What This Layer Can Do

- classify a requested MCP platform and capability into a permission posture
- recommend the safest capability to start with, usually `read_only`
- block `production_write` and `execute` by default
- raise risk when credentials, sensitive data or side effects are involved
- require rollback and dry-run evidence before any production-like path is considered
- keep Atlas in advisory mode even when a platform looks technically available

## What This Layer Must Not Do

- do not install or configure MCP servers
- do not mutate `~/.codex/config.toml`
- do not use credentials
- do not execute external actions
- do not activate workflows, send emails, deploy, delete or write to production
- do not relax platform-specific safety boundaries without explicit human approval

## Capability Levels

- `read_only`: inspect, list, analyze or draft findings without mutation
- `draft_only`: prepare drafts, plans or payloads for human review
- `sandbox_write`: write only inside a governed sandbox after explicit approval
- `production_write`: mutate production-like state; blocked by default
- `execute`: trigger real effects; blocked by default

## Safety Boundaries

- `production_write` stays blocked by default across platforms.
- `execute` stays blocked by default across platforms.
- `sandbox_write` requires explicit human approval.
- Real emails, workflow activation, deploys, database writes and deletes always require explicit approval.
- If credentials or sensitive data appear, risk must increase.
- If rollback is missing, write or execute paths stay blocked.
- If dry-run evidence is missing, production-like paths stay blocked.

## Platform Examples

- GitHub: start with `read_only`, then maybe `draft_only`
- n8n: start with exported workflow JSON or read-only inspection, not live mutation
- Gmail: draft-only is safer; real sends remain blocked
- Chrome DevTools: manual opt-in read-only style, with privacy and telemetry warnings
- Filesystem: writes outside the governed workspace must stay blocked

## Relationship To Existing Atlas Layers

- `mcp_readiness_check` tells Atlas whether MCP CLI/config appears functional.
- `chrome_devtools_mcp_readiness` remains a platform-specific browser-truth posture.
- `n8n_automation_readiness` remains the workflow safety posture for n8n automation design.
- `quality_gate_report` may expose this posture as a generic safety baseline, but it must not use that as permission to activate anything.

## Initial Stance

- advisory only
- human approval required for risky paths
- production writes blocked
- execute blocked
- prefer read-only or draft-only first
