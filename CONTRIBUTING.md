# Contributing to Codex-Atlas

Codex-Atlas V3 is an RC1 baseline and frozen. Contributions should preserve
the baseline unless a P0 or P1 issue requires a minimal fix.

## How to Contribute

1. Start from a clean checkout.
2. Read `ARCHITECTURE.md`, `ROADMAP.md`, and `docs/release_candidate_rc1.md`.
3. Keep changes scoped to the requested issue.
4. Do not add new features, workflows, registries, policies, readiness modules,
   dependencies, or runtime integrations in V3.
5. Document P2/P3/P4 ideas as backlog instead of implementing them.

## Running Tests

Install development dependencies:

```powershell
python -m pip install -r requirements-dev.txt
```

Run the full suite:

```powershell
python -m pytest -q
```

Run critical checks:

```powershell
python -m pytest tests\test_evidence_runner.py tests\test_evidence_quality_report.py tests\test_model_routing_policy.py tests\test_failure_registry.py tests\test_atlas_verify.py -q
```

Run health report checks with the focused health test module.

## Validating Evidence

Evidence Pipeline tests:

```powershell
python -m pytest tests\test_evidence_runner.py tests\test_evidence_contract_validator.py tests\test_evidence_session.py tests\test_evidence_bundle_summary.py tests\test_evidence_bundle_summary_cli.py tests\test_evidence_quality_gate_adapter.py tests\test_evidence_quality_report.py tests\test_evidence_quality_report_cli.py -q
```

Generate an Evidence Quality Report from an existing bundle:

```powershell
python -m tools.evidence_quality_report_cli tests\fixtures\evidence_bundle_valid.json
```

Real browser smoke is opt-in and requires Playwright browser provisioning. Do
not make it mandatory in V3 without a release decision.

## Opening PRs

PRs should include:

- Purpose and scope.
- Files changed.
- Tests run.
- Evidence generated, when applicable.
- Risk classification.
- Confirmation that V3 freeze rules were respected.

## Maintaining Evidence Pipeline

- Preserve the Evidence Bundle V1 contract.
- Keep CLI behavior non-surprising and test-covered.
- Do not make optional evidence workflows blocking without a release decision.
- Do not store secrets in evidence, failure records, or workflow observations.

## Avoiding Governance Breakage

Run:

```powershell
python tools\atlas_governance_check.py
python tools\atlas_verify.py
python -m compileall -q tools
git diff --check
```

Governance is the source of truth for root structure, required files, configs,
skills, workflows, and legacy mirrors.

## Mandatory Checks Before Push

- Full suite: `python -m pytest -q`
- Critical tests.
- Health report tests.
- Evidence tests when touching evidence.
- `python tools\atlas_governance_check.py`
- `python tools\atlas_verify.py`
- `python -m compileall -q tools`
- `git diff --check`
- `git status -sb`

## Workflows

- Atlas CI: push and pull request gate on `main`.
- Atlas Global Test: manual full-suite workflow.
- Evidence Quality Report: manual, opt-in, non-blocking report workflow.
- Evidence Browser Smoke: manual, opt-in, real-browser workflow.

Do not add workflows in V3 unless fixing a confirmed P0/P1 release blocker.
