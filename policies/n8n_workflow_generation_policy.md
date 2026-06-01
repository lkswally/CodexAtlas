# n8n Workflow Generation Policy

## Purpose

This layer allows Atlas to design and render offline n8n workflow blueprints and importable JSON skeletons without touching a live n8n instance.

## Allowed

- generate workflow blueprints
- generate importable JSON skeletons
- propose nodes, data contracts and test payloads
- mark side effects and human approval boundaries
- require manual credential binding
- pass every generated result through `n8n_automation_readiness`

## Forbidden

- connect to n8n
- call the n8n API
- install n8n MCP
- execute workflows
- activate workflows
- use real credentials
- create or edit workflows in a live environment
- embed production webhook URLs, bearer tokens or API keys

## Safety Rules

- generated workflows must default to `active: false`
- generated JSON must not contain real credentials
- side-effect nodes must be marked clearly
- test payloads are mandatory
- human approval is mandatory for email, Sheets, database writes or public webhooks
- generated output is advisory until a human reviews the readiness posture

## Approval Boundary

Atlas may help draft the workflow, but a human must approve:

- credential binding
- webhook exposure
- email sending
- database or spreadsheet writes
- production activation

## Output Discipline

Every generated workflow should include:

- workflow name
- trigger
- proposed nodes
- data contract
- test payload
- side effects
- credential placeholders
- readiness posture
- checklist before import

## Reversibility

Generated JSON is a local skeleton only. It must stay importable, inactive and manually reviewable.
