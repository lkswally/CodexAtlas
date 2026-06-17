from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional


DASHBOARD_NAME = "atlas_health_dashboard"
DASHBOARD_VERSION = "v1"
VALID_STATUSES = {"PASS", "WARN", "FAIL", "UNKNOWN"}
DEFAULT_ROOT = Path(__file__).resolve().parents[1]

REQUIRED_TOP_LEVEL_FIELDS = (
    "dashboard_name",
    "version",
    "overall_status",
    "generated_at",
    "sections",
    "risks",
    "next_actions",
)
REQUIRED_SECTION_FIELDS = (
    "ci",
    "evidence",
    "browser_smoke",
    "model_routing",
    "failure_registry",
    "integrations",
)
KNOWN_WORKFLOWS = (
    "Atlas CI",
    "Atlas Global Test",
    "Evidence Quality Report",
    "Evidence Browser Smoke",
)


class AtlasHealthDashboardValidationError(ValueError):
    pass


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _normalize_status(value: Any) -> str:
    status = str(value or "UNKNOWN").upper()
    return status if status in VALID_STATUSES else "UNKNOWN"


def _component(name: str, status: Any, summary: str, **extra: Any) -> Dict[str, Any]:
    item = {
        "name": name,
        "status": _normalize_status(status),
        "summary": summary,
    }
    item.update(extra)
    return item


def _rollup_status(items: List[Dict[str, Any]]) -> str:
    statuses = {_normalize_status(item.get("status")) for item in items}
    if "FAIL" in statuses:
        return "FAIL"
    if "WARN" in statuses:
        return "WARN"
    if "UNKNOWN" in statuses:
        return "UNKNOWN"
    return "PASS"


def _overall_status(sections: Dict[str, Any]) -> str:
    statuses: List[str] = []
    for section in sections.values():
        if isinstance(section, dict):
            statuses.append(_normalize_status(section.get("status")))
    if "FAIL" in statuses:
        return "FAIL"
    if "WARN" in statuses or "UNKNOWN" in statuses:
        return "WARN"
    return "PASS"


def _file_presence_status(root: Path, paths: List[str]) -> str:
    return "PASS" if all((root / path).exists() for path in paths) else "FAIL"


def _build_default_core_statuses(root: Path) -> Dict[str, str]:
    statuses = {
        "evidence_pipeline": _file_presence_status(
            root,
            [
                "tools/evidence_runner.py",
                "tools/evidence_quality_report.py",
                "tools/evidence_contract_validator.py",
            ],
        ),
        "model_routing": _file_presence_status(
            root,
            [
                "tools/model_routing_policy.py",
                "tools/model_router.py",
                "config/model_routing_rules.json",
            ],
        ),
        "failure_registry": _file_presence_status(
            root,
            [
                "tools/failure_registry.py",
                "docs/failure_registry_v1.md",
                "tests/test_failure_registry.py",
            ],
        ),
        "governance": _file_presence_status(
            root,
            [
                "tools/atlas_governance_check.py",
                "tests/test_atlas_verify.py",
                "commands/atomic_command_registry.json",
            ],
        ),
    }
    return statuses


def _workflow_components(workflow_statuses: Optional[Dict[str, Any]]) -> List[Dict[str, Any]]:
    provided = workflow_statuses or {}
    components: List[Dict[str, Any]] = []
    for workflow_name in KNOWN_WORKFLOWS:
        status = _normalize_status(provided.get(workflow_name, "UNKNOWN"))
        if status == "UNKNOWN":
            summary = "Workflow status is not observed by the local dashboard input."
        else:
            summary = f"Last observed workflow status is {status}."
        components.append(
            _component(
                workflow_name,
                status,
                summary,
                observation_source="provided" if workflow_name in provided else "not_observed",
            )
        )
    return components


def build_health_dashboard(
    *,
    root: Optional[Path] = None,
    workflow_statuses: Optional[Dict[str, Any]] = None,
    core_statuses: Optional[Dict[str, Any]] = None,
    runner_warnings: Optional[List[str]] = None,
    generated_at: Optional[str] = None,
) -> Dict[str, Any]:
    repo_root = (root or DEFAULT_ROOT).resolve()
    core = {key: _normalize_status(value) for key, value in (core_statuses or _build_default_core_statuses(repo_root)).items()}
    workflows = _workflow_components(workflow_statuses)
    ci_status = _rollup_status(workflows)

    evidence_components = [
        _component(
            "Evidence Pipeline",
            core.get("evidence_pipeline", "UNKNOWN"),
            "Local evidence tooling contract is present and readable.",
            mode="local_read_only",
        ),
        next(item for item in workflows if item["name"] == "Evidence Quality Report"),
    ]

    browser_workflow = next(item for item in workflows if item["name"] == "Evidence Browser Smoke")
    sections = {
        "ci": {
            "status": ci_status,
            "workflows": workflows,
        },
        "evidence": {
            "status": _rollup_status(evidence_components),
            "components": evidence_components,
        },
        "browser_smoke": {
            "status": browser_workflow["status"],
            "mode": "manual_opt_in",
            "workflow": browser_workflow,
        },
        "model_routing": {
            "status": core.get("model_routing", "UNKNOWN"),
            "mode": "advisory_only",
            "summary": "Model Routing V1 recommends routes but does not auto-switch models.",
        },
        "failure_registry": {
            "status": core.get("failure_registry", "UNKNOWN"),
            "mode": "advisory_only",
            "summary": "Failure Registry V1 stores and compares validated records without automatic remediation.",
        },
        "integrations": {
            "status": core.get("governance", "UNKNOWN"),
            "governance": _component(
                "Governance",
                core.get("governance", "UNKNOWN"),
                "Governance surface is represented as a local read-only health signal.",
            ),
            "external_integrations": {
                "status": "WARN",
                "mode": "advisory_only",
                "summary": "External integrations are not required for dashboard generation.",
            },
        },
    }

    risks = [
        {
            "id": "workflows_without_observation",
            "status": "WARN" if any(item["status"] == "UNKNOWN" for item in workflows) else "PASS",
            "summary": "Workflow health depends on supplied observations; missing observations remain UNKNOWN.",
        },
        {
            "id": "integrations_advisory_only",
            "status": "WARN",
            "summary": "External integrations remain advisory-only and do not prove runtime readiness.",
        },
        {
            "id": "browser_smoke_manual",
            "status": "WARN",
            "summary": "Evidence Browser Smoke remains manual/opt-in and is not a blocking runtime signal.",
        },
        {
            "id": "runner_warnings",
            "status": "WARN" if runner_warnings else "PASS",
            "summary": "Runner warnings require review when supplied.",
            "items": list(runner_warnings or []),
        },
    ]

    next_actions = [
        "Feed latest workflow observations into the dashboard before release decisions.",
        "Keep browser smoke manual until a separate blocking policy is approved.",
        "Define operational dashboard inputs before Autonomous Engineering Runtime work.",
    ]

    report = {
        "dashboard_name": DASHBOARD_NAME,
        "version": DASHBOARD_VERSION,
        "overall_status": _overall_status(sections),
        "generated_at": generated_at or _utc_now_iso(),
        "sections": sections,
        "risks": risks,
        "next_actions": next_actions,
    }
    validate_health_dashboard(report)
    return report


def validate_health_dashboard(report: Any) -> Dict[str, Any]:
    findings: List[str] = []
    if not isinstance(report, dict):
        raise AtlasHealthDashboardValidationError("Atlas Health Dashboard report must be a JSON object.")

    for field in REQUIRED_TOP_LEVEL_FIELDS:
        if field not in report:
            findings.append(f"missing_field:{field}")

    if report.get("dashboard_name") != DASHBOARD_NAME:
        findings.append("invalid_dashboard_name")
    if report.get("version") != DASHBOARD_VERSION:
        findings.append("invalid_version")
    if _normalize_status(report.get("overall_status")) != report.get("overall_status"):
        findings.append("invalid_overall_status")
    if not isinstance(report.get("generated_at"), str) or not report.get("generated_at", "").strip():
        findings.append("invalid_generated_at")

    sections = report.get("sections")
    if not isinstance(sections, dict):
        findings.append("sections_not_object")
    else:
        for section in REQUIRED_SECTION_FIELDS:
            if section not in sections:
                findings.append(f"missing_section:{section}")
            elif not isinstance(sections[section], dict):
                findings.append(f"section_not_object:{section}")
            elif _normalize_status(sections[section].get("status")) != sections[section].get("status"):
                findings.append(f"invalid_section_status:{section}")

    if not isinstance(report.get("risks"), list):
        findings.append("risks_not_list")
    if not isinstance(report.get("next_actions"), list):
        findings.append("next_actions_not_list")

    if findings:
        raise AtlasHealthDashboardValidationError(
            "Atlas Health Dashboard validation failed: " + ", ".join(findings)
        )
    return {"status": "PASS", "valid": True, "findings": []}


def render_health_markdown(report: Dict[str, Any]) -> str:
    validate_health_dashboard(report)
    sections = report["sections"]
    lines = [
        "# Atlas Health Dashboard",
        "",
        f"- Dashboard: {report['dashboard_name']} {report['version']}",
        f"- Overall status: {report['overall_status']}",
        f"- Generated at: {report['generated_at']}",
        "",
        "## CI",
    ]
    for workflow in sections["ci"].get("workflows", []):
        lines.append(f"- {workflow['name']}: {workflow['status']}")

    lines.extend(
        [
            "",
            "## Evidence",
        ]
    )
    for component in sections["evidence"].get("components", []):
        lines.append(f"- {component['name']}: {component['status']}")

    lines.extend(
        [
            "",
            "## Browser Smoke",
            f"- Evidence Browser Smoke: {sections['browser_smoke']['status']}",
            f"- Mode: {sections['browser_smoke']['mode']}",
            "",
            "## Model Routing",
            f"- Status: {sections['model_routing']['status']}",
            f"- Mode: {sections['model_routing']['mode']}",
            "",
            "## Failure Registry",
            f"- Status: {sections['failure_registry']['status']}",
            f"- Mode: {sections['failure_registry']['mode']}",
            "",
            "## Integrations",
            f"- Status: {sections['integrations']['status']}",
            f"- External integrations: {sections['integrations']['external_integrations']['mode']}",
            "",
            "## Risks",
        ]
    )
    for risk in report["risks"]:
        lines.append(f"- {risk['id']}: {risk['status']} - {risk['summary']}")

    lines.extend(["", "## Next Actions"])
    lines.extend(f"- {item}" for item in report["next_actions"])
    return "\n".join(lines)
