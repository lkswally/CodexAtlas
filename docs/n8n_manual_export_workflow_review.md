# Safe n8n Manual Export Review

This workflow keeps Atlas in advisory mode while you review n8n automations from exported JSON.

## Goal

Use Atlas to inspect, classify and de-risk a workflow before any real connection, webhook, credential or production side effect is touched.

Atlas does not:
- connect to n8n
- call the n8n API
- execute workflows
- trigger webhooks
- send emails
- write to Sheets or databases

## 1. Export a workflow from n8n

From the n8n editor:
1. Open the workflow you want to review.
2. Use the workflow export option in the n8n UI.
3. Save the file locally as JSON.

Recommended local location:
- `C:\Proyectos\Codex-Atlas\_sandbox\`

Recommended filename:
- `workflow-name.n8n.local.json`

That naming keeps the export ignored by Git.

## 2. Remove or redact sensitive data before analysis

Before running Atlas, clean the export manually.

Delete or redact:
- credential IDs or names
- bearer tokens
- API keys
- OAuth references
- webhook URLs
- email addresses if they are real user data
- phone numbers
- personal data
- prompt inputs containing customer-sensitive information

If a field is needed for structure only, replace it with obvious fake values such as:
- `test@example.com`
- `https://example.invalid/webhook`
- `FAKE_TOKEN_REMOVED`

## 3. Add a safe test payload

Atlas expects a safe example input when the workflow processes external events or form submissions.

Create a small companion file such as:
- `C:\Proyectos\Codex-Atlas\_sandbox\workflow-name-test-payload.json`

Keep it fake and minimal. It should show:
- what triggers the workflow
- what the input looks like
- what fields are expected

If you want Atlas to see it explicitly, pass a small review input JSON to the readiness tool, for example:

```json
{
  "trigger": "manual webhook test",
  "input_payload": {
    "candidate_name": "Fake User",
    "email": "test@example.com"
  },
  "expected_output": "Generate a structured internal report only.",
  "human_approval_required": true,
  "dry_run_available": false,
  "rollback_documented": false
}
```

## 4. Run Atlas review

Direct readiness review:

```powershell
python tools\n8n_automation_readiness.py --project C:\Proyectos\Codex-Atlas --input C:\Proyectos\Codex-Atlas\_sandbox\workflow-review-input.json
```

If the export is stored in `_sandbox` and named like an n8n workflow export, Atlas can also pick it up from the project scan surface while staying fully local and advisory.

## 5. How to interpret `n8n_automation_posture`

Key fields:
- `automation_ready`: whether the workflow is structurally safe enough for further human review
- `risk_level`: `low`, `medium`, or `high`
- `side_effects`: real-world actions Atlas detected
- `credentials_required`: what kinds of credentials would be needed later
- `human_approval_required`: should remain true for anything real
- `dry_run_available`: whether a simulation path exists
- `test_payload_required`: true means you still need a safe sample input
- `blocked_reasons`: why Atlas thinks the workflow must not move forward yet
- `recommended_next_steps`: what to prepare before any live use

Practical reading:
- `low`: mostly documentary or design-stage workflow
- `medium`: needs safer inputs, better logging, better retries, or clearer dry-run planning
- `high`: side effects, public exposure, sensitive data, or missing controls make it unsafe to advance

## 6. What Atlas blocks

Atlas should block or strongly warn when it sees:
- real email sending
- writes to Google Sheets or databases without a safe path
- public webhooks without auth
- scraping without limits or ToS review
- LLM nodes with sensitive data
- side effects with no rollback plan
- missing test payload for externally triggered flows
- production-facing automation without human approval

## 7. When to require human approval

Human approval is required when the workflow:
- can send anything externally
- can write or mutate data
- can hit third-party APIs
- can expose or receive public webhook traffic
- can touch production tools or customer data
- can use credentials that are not fake

## 8. When not to advance

Do not move beyond review if:
- the export still contains secrets
- the workflow still references live webhook URLs
- the input payload is not documented
- there is no rollback path
- the workflow has real side effects and no dry-run strategy
- the workflow handles personal or sensitive data without redaction
- the workflow is intended for production and nobody approved live execution

## 9. Safe review discipline

Use Atlas for:
- blueprint review
- export JSON review
- payload validation
- node/risk classification
- checklist generation

Do not use Atlas alone for:
- production activation
- credential management
- webhook publication
- workflow mutation in n8n
- real automation execution
