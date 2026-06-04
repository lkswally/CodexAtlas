# Policy: scheduled_automation_readiness

## Purpose

`scheduled_automation_readiness` lets Atlas evaluate whether a future scheduled task
looks safe enough to remain a manual reminder, a dry-run candidate or a sandbox-only
idea without creating cron jobs, workers, gateways or runtime automation.

This layer is advisory and read-only.

## What it can do

- classify a requested schedule as reminder, dry-run candidate, sandbox candidate,
  manual-review-only or blocked
- surface whether the task would require external services, credentials, approvals,
  dry-run support or rollback
- detect recursion, auto-mutation and unsafe production targets before any scheduler
  exists
- inform `quality_gate_report` about scheduling risk posture

## What it cannot do

- create cron jobs
- start background workers
- use Windows Task Scheduler
- use GitHub Actions as a scheduler
- connect to n8n, Telegram, Discord, Slack or WhatsApp
- execute scheduled jobs
- rewrite code or prompts automatically

## Safe scheduling posture

Atlas should bias toward the smallest safe state:

- `manual_reminder_ready`: non-destructive reminders or checklist nudges
- `dry_run_ready`: read-only or preview-first scheduled ideas with explicit dry-run
- `sandbox_ready`: sandbox-only write candidates with approval, dry-run and rollback
- `manual_review_only`: external, credentialed or ambiguous automation ideas that
  still need human review
- `blocked`: recursive, self-mutating, execution-heavy or production write tasks
- `watchlist`: worthwhile future idea, but the runtime surface is intentionally absent

## Required guardrails

- sending emails automatically requires explicit human approval
- writing to Sheets or databases requires sandbox, dry-run and rollback
- workflow execution or activation stays blocked by default
- modifying code automatically on a schedule stays blocked
- recursive or self-mutating tasks stay blocked
- production targets without sandbox stay blocked

## Relationship to existing Atlas layers

- `n8n_automation_readiness` remains the workflow safety layer for workflow shapes
- `n8n_api_connector_readiness` remains the API posture for any future n8n connection
- `mcp_permission_matrix_readiness` remains the permission model for external tool
  surfaces
- `github_connector_readiness` remains the GitHub-specific posture; scheduling GitHub
  reads does not make writes allowed

## Human approval

Human approval is required when a scheduled task would:

- send emails or messages
- write or delete data
- use secrets or credentials
- target production surfaces
- trigger workflows, deploys or external mutation

## Success criterion

Atlas may call a scheduling idea `ready` only when it still remains advisory,
bounded and reviewable without pretending a real scheduler already exists.
