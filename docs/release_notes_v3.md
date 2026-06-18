# Codex-Atlas V3 Release Notes

Release: Codex-Atlas V3 RC1

Recommended tag: `v3.0.0-rc1`

## Architecture

V3 establishes Codex-Atlas as a governed, evidence-first, local baseline for
creating, auditing, and certifying derived projects. The architecture is
root-first and file-backed, with explicit governance and no autonomous runtime.

Primary flow:

```text
Objective -> Planner -> Executor -> Evidence Pipeline -> Verifier -> Health Report -> Failure Registry
```

## Evidence

Evidence Pipeline V1 is RC1-ready for local use:

- Evidence runner.
- Evidence contract validator.
- Evidence session builder.
- Evidence bundle summary.
- Evidence quality gate adapter.
- Evidence quality report and CLI.
- Opt-in Evidence Quality Report workflow.

## Health Report

Atlas health report V1 is RC1-ready:

- JSON and Markdown render paths.
- Local core health checks.
- Workflow observations cache.
- Freshness policy with default `168` hour max age.
- Controlled WARN/UNKNOWN behavior for missing, invalid, or stale observations.

## Failure Registry

Failure Registry V1 is RC1-ready:

- Strict record fields.
- Validation and persistence.
- Advisory similarity lookup.
- Basic secret-pattern rejection for sensitive text fields.

## Browser Smoke

Evidence Browser Smoke is available as a manual opt-in workflow. It is useful
release evidence, but it is not a default blocking gate in V3.

## CI

CI posture:

- Atlas CI runs on push and pull request to `main`.
- Atlas Global Test is manual.
- Evidence Quality Report is manual and opt-in.
- Evidence Browser Smoke is manual and opt-in.
- Workflows use `windows-2025` and current GitHub Actions major versions.

## Tests

Final V3 evidence:

- Suite global: `601 passed, 1 skipped`.
- Health report tests: `23 passed`.
- Critical tests: `65 passed`.
- Evidence tests: `69 passed`.
- Governance: PASS.
- `atlas_verify`: PASS.
- `compileall`: PASS.
- `git diff --check`: PASS.
- Atlas CI: PASS.

## Immediate Roadmap

V3 is frozen. Only P0/P1 fixes are accepted.

V4 objectives are listed in `ROADMAP.md`, but V4 is not designed or started in
this release.
