# Policy: human_approval_policy

## Goal

Define when Atlas work must pause for explicit human approval.

## Approval is required for

- destructive commands
- remote writes
- deployment steps
- secret handling changes
- changes that affect derived runtime behavior
- new external integrations

## Approval is not required for

- documentation-only updates
- read-only audits
- local validation with no side effects

## Reminder

Atlas should bias toward clarity and safe handoffs, not silent automation.
