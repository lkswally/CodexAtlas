# Policy: evidence_required_policy

## Goal

Prevent Atlas from claiming completion, readiness or quality without concrete evidence.

## Rules

- Do not say a project, skill or workflow is complete without validation proportional to the risk.
- Distinguish facts, assumptions and recommendations explicitly.
- When a command is read-only, its output must still show what was checked and what was not checked.
- If validation could not run, say so and explain the residual risk.
- Prefer named findings, blockers, warnings and recommendations over vague status language.

## Evidence expectations

- Documentation changes: cite the updated files and the intended contract.
- Executable tooling changes: run the relevant checks or tests.
- Derived-project claims: use `audit-repo` or `certify-project` from Atlas, not statements based on assumption.
- Boundary claims: cite the exact paths that were checked.

## Anti-patterns

- "Looks fine" without validation
- "Done" when only docs changed but the executable contract was not checked
- "Healthy" without naming the checks performed
