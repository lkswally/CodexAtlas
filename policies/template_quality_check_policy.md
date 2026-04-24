# Policy: template_quality_check_policy

## Goal

Keep Atlas templates renderable, governed and useful instead of becoming fragile boilerplate.

## Rules

- Every canonical template referenced by a contract must exist.
- Only approved placeholders may appear in governed templates.
- Rendered output must not leave unresolved placeholders behind.
- Templates must include the minimum content required by their contract.
- Template complexity must stay below the point where Atlas needs a full templating framework.

## Bootstrap template rules

- The approved placeholder set is intentionally small and explicit.
- README and AGENTS templates are validated per project profile.
- Template quality checks are read-only and should fail fast when drift appears.

## Watchpoint

If templates begin to need conditionals, nested partials or uncontrolled variables, Atlas should revisit the contract before adding more templating power.
