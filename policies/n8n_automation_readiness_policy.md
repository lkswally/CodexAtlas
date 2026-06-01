# n8n Automation Readiness Policy

## Purpose

`n8n_automation_readiness` exists to help Atlas review n8n workflows, blueprints and exported JSON safely before anything touches a real system.

The goal is not to run automation. The goal is to decide whether a workflow should stay in:

- documentation
- blueprint design
- test payload review
- human approval

## Core rules

- advisory only
- no n8n connection
- no webhook execution
- no real workflow runs
- no writes to Gmail, Sheets, databases or production systems
- no credential activation
- no workflow mutation without separate human approval

## What the layer should evaluate

- trigger shape
- expected input payload
- expected output
- node types
- credentials required
- sensitive data exposure
- side effects
- idempotency
- retries
- logging
- error handling
- human approval
- dry-run posture
- rollback posture
- test payload readiness

## What the layer should flag as high risk

- real email delivery
- writes to Sheets or databases
- public webhooks without auth
- scraping or crawler flows without limits or review
- LLM nodes with sensitive data
- production-active workflows without explicit approval
- side effects without rollback guidance

## Safety boundary

Atlas may:

- review exported JSON
- review workflow blueprints
- propose safer node structure
- propose test payloads
- generate checklists

Atlas must not:

- execute workflows
- call live webhooks
- send emails
- write rows
- mutate production automation
- consume credentials

## Output posture

The layer should return:

- automation readiness
- risk level
- side effects
- credentials required
- human approval requirement
- dry-run availability
- test payload requirement
- blocked reasons
- recommended next steps
