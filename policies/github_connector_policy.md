# Policy: github_connector_readiness

## Goal

Define a governed, advisory-only readiness posture for the first GitHub platform connection before Atlas ever uses a real GitHub MCP, token or write action.

This layer exists to answer:

- what GitHub capability is being requested
- whether that capability is safe in `read_only`, `draft_only`, `sandbox_write` or must stay blocked
- what human approval boundary applies
- what the next safe non-destructive step should be

## What This Layer Can Do

- classify GitHub connector requests into safe capability levels
- keep repository inspection and metadata reads in `read_only`
- allow draft PR preparation only as governed `draft_only`
- route the permission decision through the generic MCP permission matrix
- surface blocked capabilities before any token, connector or write path exists
- distinguish theoretical readiness from a real read-only runtime probe
- allow a governed `gh` CLI read-only probe without enabling any write path

## What This Layer Must Not Do

- do not install a GitHub MCP server
- do not modify global Codex config
- do not use tokens or read secrets
- do not create PRs, issues or comments for real
- do not merge, dispatch workflows, delete refs or force-push
- do not modify repositories from this readiness layer
- do not attempt any write probe to "test" permissions

## Initial Capability Stance

- `repo_status`, `commits`, `pull_requests`, `actions_read`, `issues_read`: allowed in `read_only`
- `pr_draft`: allowed as `draft_only` with human review
- `branch_write`: sandbox-only conceptually, but keep blocked until explicit approval and rollback planning exist
- `merge`: blocked
- `workflow_dispatch`: blocked
- `secrets_access`: blocked
- `delete`: blocked
- `force_push`: blocked

## Safety Boundaries

- Start in `read_only` by default.
- Treat draft PR creation as a review-gated step, not an autonomous write.
- Block merges, workflow dispatch, secrets access, deletes and force-pushes by default.
- If rollback or dry-run evidence is missing, keep any write-like capability blocked.
- If a request implies tokens, secrets or sensitive repository data, raise risk and keep Atlas advisory-only.
- Runtime probing must stay read-only: repo metadata, commits, PR metadata, Actions metadata and issue metadata only.
- `write_attempted` must remain `false`.

## Relationship To Existing Atlas Layers

- `mcp_permission_matrix_readiness` remains the generic policy engine for capability levels.
- `github_connector_readiness` is the GitHub-specific adapter on top of that matrix.
- The runtime probe is a sub-layer of `github_connector_readiness`, not a separate write-capable connector.
- `mcp_readiness_check` only reports whether MCP CLI/config appears functional; it does not grant permission.
- `quality_gate_report` may expose GitHub connector posture as advisory evidence, not as execution permission.

## Initial Stance

- advisory only
- recommend `read_only`
- human approval required for draft or branch-like actions
- merge, workflow execution, secrets and destructive actions blocked by default
