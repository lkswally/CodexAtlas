# Workflow: audit_project

## Purpose

Audit an Atlas workspace or a derived project without mutating runtime behavior.

## Inputs

- workspace root
- canonical registry
- governance rules
- available evidence

## Steps

1. Validate governance and structure
2. Identify canonical vs adapter boundaries
3. Detect drift, missing docs and risky assumptions
4. Summarize evidence and residual risk
5. Recommend the smallest safe next action

## Output

- diagnosis
- evidence trail
- recommendations

## Status

Documented workflow with minimal executable support through the `repo-audit` skill and `audit-repo` dispatcher.

## Related skill

- `repo-audit`
