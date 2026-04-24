# Policy: cost_control_policy

## Goal

Keep Atlas useful without over-spending model capacity or suggesting unnecessary integrations.

## Rules

- default to the smallest sufficient model profile
- escalate to `deep_reasoning` or `security` only when the task justifies it
- do not suggest MCPs unless they materially improve correctness or evidence
- keep routing explanations short and auditable
- prefer read-only planning before mutation

## Practical effect

- simple documentation can use `cost_saver`
- implementation uses `code_execution`
- security-sensitive or destructive intent escalates approval and routing rigor
