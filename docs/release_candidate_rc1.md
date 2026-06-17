# Codex-Atlas V3 RC1 Report

Fecha: 2026-06-17

## 1. Executive summary

Decision: GO.

Codex-Atlas V3 RC1 is stable enough to freeze as an internal baseline. No P0 or P1 release blockers were found during the final audit. The repo can be cloned, read, tested, and audited from committed files without relying on this conversation.

This is a WARN/GO release candidate: the core is healthy, but several surfaces remain intentionally manual or advisory-only.

## 2. Current system map

- Governance and verification: `tools/atlas_governance_check.py`, `tools/atlas_verify.py`, `commands/atomic_command_registry.json`.
- Evidence Pipeline: `tools/evidence_runner.py`, `tools/evidence_contract_validator.py`, `tools/evidence_session.py`, `tools/evidence_bundle_summary.py`, `tools/evidence_quality_report.py`, CLI wrappers, tests, and opt-in workflows.
- Health Dashboard: `tools/atlas_health_dashboard.py`, `config/workflow_observations.json`, `docs/atlas_health_dashboard_v1.md`.
- Failure Registry: `tools/failure_registry.py`, `docs/failure_registry_v1.md`.
- Model Routing: `tools/model_routing_policy.py`, `tools/model_router.py`, `tools/model_router_core.py`, `config/model_routing_rules.json`.
- Agent Loop: `docs/agent_loop_v1_design.md`, `docs/agent_loop_manual_checklist.md`, with runtime intentionally out of scope.
- Advisory readiness surfaces: n8n, Chrome MCP, GitHub connector, scheduled automations, department registry, visual QA, and related policy/config modules.

## 3. What is production-ready/internal-ready

- Local governance checks are blocking and pass.
- `atlas_verify` composes governance, audit, surface audit, and operational parity checks.
- Evidence Bundle/Report contracts are tested and deterministic.
- Failure Registry V1 validates exact fields, rejects obvious secret-like patterns, persists records, and provides advisory similarity lookup.
- Model Routing V1 is stable as advisory policy and explicitly does not auto-switch runtime models.
- Atlas Health Dashboard V1 produces JSON and Markdown, handles missing/invalid observations, and applies freshness policy before allowing PASS.
- CI uses current runner/action posture: `windows-2025`, `actions/checkout@v6`, `actions/setup-python@v6`, and artifact upload v7 where applicable.

## 4. What remains advisory-only

| Surface | RC1 state | Notes |
|---|---|---|
| Engram | DEPRECATE_LATER | Explicitly deferred/blocked; local file-backed memory remains source of truth. |
| n8n | ADVISORY_ONLY | Blueprint/generator/readiness only; no live credentials or execution. |
| Chrome MCP | ADVISORY_ONLY | Manual opt-in posture with privacy warnings. |
| GitHub connector | ADVISORY_ONLY | Readiness/draft planning only; destructive actions remain blocked/manual. |
| Scheduled automations | ADVISORY_ONLY | Manual reminder/readiness posture; no autonomous runtime. |
| Model Routing | ADVISORY_ONLY | Stable recommendation layer; no automatic model switching. |
| Evidence workflows | PARTIAL | CI workflows work, but Evidence Quality Report and Browser Smoke are opt-in/manual. |

## 5. What is intentionally manual

- Workflow observations cache updates are manual.
- Evidence Browser Smoke is manual/opt-in.
- Evidence Quality Report workflow is manual/opt-in and non-blocking when no bundle exists.
- Model selection remains manual in Codex Desktop.
- n8n credentials and live automation activation are manual and approval-bound.
- Runtime memory remains file-backed, not Engram-backed.

## 6. What is not included in this release

- Autonomous Engineering Runtime.
- Web dashboard.
- Paperclip integration.
- Live GitHub API dependency for dashboard status.
- Live n8n execution or credential binding.
- Engram runtime memory.
- Automatic model switching.
- Blocking browser smoke in Atlas CI.

## 7. Test and CI evidence

Local RC1 checks:

- Dashboard tests: `23 passed`.
- Evidence tests: `69 passed`.
- Critical tests: `65 passed`.
- Suite global: `601 passed, 1 skipped`.
- Governance: PASS.
- `atlas_verify`: PASS.
- `compileall`: PASS.
- `git diff --check`: PASS.
- `git status -sb`: clean before report creation.

## 8. Workflow evidence

| Workflow | Latest observed state | Run |
|---|---|---|
| Atlas CI | SUCCESS | `27726354258` |
| Atlas Global Test | SUCCESS | `27414397174` |
| Evidence Quality Report | SUCCESS | `27390064634` |
| Evidence Browser Smoke | SUCCESS | `27724893071` |

Workflow caveat: Atlas Global Test and Evidence Quality Report are manual workflows. Their latest successful runs are valid evidence, but they are not continuous push gates.

## 9. Dashboard state

Default dashboard state: PASS.

Workflow observations cache:

- Atlas CI: PASS, fresh, run `27725625470`.
- Atlas Global Test: PASS, fresh, run `27414397174`.
- Evidence Quality Report: PASS, fresh, run `27390064634`, artifact `7581555415`.
- Evidence Browser Smoke: PASS, fresh, run `27724893071`, artifact `7709863742`.

Freshness policy prevents expired PASS observations from keeping the dashboard in PASS. Missing or invalid observations produce controlled WARN/UNKNOWN behavior.

## 10. Known risks

- Workflow observations cache is manual and needs an owner/frequency.
- Browser smoke remains manual/opt-in.
- Evidence Quality Report remains manual/opt-in.
- External integrations are mostly advisory-only.
- README/AGENTS and historical architecture docs still contain some Engram/Pixel Bridge ambiguity, although current policy and memory state clearly defer Engram.
- The suite is healthy but broad; future growth may require test grouping discipline to avoid slow RC checks.

## 11. P0/P1/P2/P3/P4 backlog

P0:

- None found.

P1:

- None found.

P2:

- Define owner and update cadence for `config/workflow_observations.json`.
- Decide whether Atlas Global Test should become scheduled or remain manual before a non-RC baseline.
- Decide whether Evidence Browser Smoke should stay opt-in or become a blocking release gate.

P3:

- Clarify Engram/Pixel Bridge language in README-facing docs so deferred status is unambiguous everywhere.
- Add a short release checklist entry point that points to RC report, dashboard docs, evidence docs, and governance commands.
- Periodically review advisory-only configs for surfaces that should be deprecated later.

P4:

- Consider small documentation de-duplication pass across architecture audit, capability radar, and operational parity docs.
- Consider grouping long-running or real-browser tests more visibly for contributors.

## 12. Go / No-Go decision

GO.

Reason: No P0 or P1 issues were found. All required local checks passed. Latest observed CI evidence is successful. Remaining work is P2/P3/P4 and is documented as backlog rather than patched into RC1.

## 13. If GO

Recommended tag name:

- `v3.0.0-rc1`

Recommended branch strategy:

- Keep `main` as the protected baseline branch.
- Create tag `v3.0.0-rc1` from the RC1 report commit after Atlas CI passes.
- Use short-lived branches for any RC1 fixes.
- Only accept P0/P1 fixes into RC1 after tag candidate; P2/P3/P4 move to post-RC backlog unless explicitly promoted.

Freeze rules:

- No new features.
- No new workflows, registries, policies, integrations, or runtime surfaces.
- No dependency additions.
- Documentation-only fixes allowed if they clarify RC evidence or remove misleading release claims.
- Code changes allowed only for confirmed P0/P1 defects.
- Re-run dashboard, critical tests, suite global, governance, atlas_verify, compileall, diff check, and Atlas CI after any RC1 change.

## 14. If NO-GO

Not applicable. No exact P0/P1 blockers were found.
