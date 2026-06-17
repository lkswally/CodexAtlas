from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional


DASHBOARD_NAME = "atlas_health_dashboard"
DASHBOARD_VERSION = "v1"
VALID_STATUSES = {"PASS", "WARN", "FAIL", "UNKNOWN"}
DEFAULT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_WORKFLOW_OBSERVATIONS_PATH = DEFAULT_ROOT / "config" / "workflow_observations.json"

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
WORKFLOW_OBSERVATION_KEYS = {
    "Atlas CI": "atlas_ci",
    "Atlas Global Test": "atlas_global_test",
    "Evidence Quality Report": "evidence_quality_report",
    "Evidence Browser Smoke": "evidence_browser_smoke",
}
WORKFLOW_OBSERVATION_OPTIONAL_FIELDS = ("run_id", "artifact_id", "observed_at", "notes")


class AtlasHealthDashboardValidationError(ValueError):
    pass


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _normalize_status(value: Any) -> str:
    status = str(value or "UNKNOWN").upper()
    return status if status in VALID_STATUSES else "UNKNOWN"


def _is_valid_status(value: Any) -> bool:
    return isinstance(value, str) and value.upper() in VALID_STATUSES


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


def _section_status(statuses: List[str]) -> str:
    normalized = {_normalize_status(status) for status in statuses}
    if "FAIL" in normalized:
        return "FAIL"
    if "WARN" in normalized:
        return "WARN"
    if "UNKNOWN" in normalized:
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


def load_workflow_observations(path: Path) -> Dict[str, Any]:
    observations_path = Path(path)
    try:
        payload = json.loads(observations_path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        return {
            "status": "UNKNOWN",
            "valid": True,
            "observations": {},
            "findings": [],
            "source": str(observations_path),
        }
    except (OSError, json.JSONDecodeError) as exc:
        return {
            "status": "WARN",
            "valid": False,
            "observations": {},
            "findings": [f"invalid_observations_file:{exc}"],
            "source": str(observations_path),
        }

    findings: List[str] = []
    observations: Dict[str, Dict[str, Any]] = {}
    if not isinstance(payload, dict):
        findings.append("observations_not_object")
    elif payload.get("observations_version") != "v1":
        findings.append("invalid_observations_version")

    workflows = payload.get("workflows") if isinstance(payload, dict) else None
    if not isinstance(workflows, dict):
        findings.append("workflows_not_object")
        workflows = {}

    for workflow_name, key in WORKFLOW_OBSERVATION_KEYS.items():
        item = workflows.get(key)
        if item is None:
            continue
        if not isinstance(item, dict):
            findings.append(f"workflow_observation_not_object:{key}")
            continue
        status = item.get("status")
        if not _is_valid_status(status):
            findings.append(f"invalid_workflow_status:{key}")
            observations[key] = {
                "name": workflow_name,
                "status": "WARN",
                "summary": "Workflow observation has an invalid status.",
                "observation_source": "cache_invalid",
            }
            continue
        observation = {
            "name": workflow_name,
            "status": _normalize_status(status),
            "summary": f"Cached workflow observation status is {_normalize_status(status)}.",
            "observation_source": "cache",
        }
        for field in WORKFLOW_OBSERVATION_OPTIONAL_FIELDS:
            value = item.get(field)
            if isinstance(value, str) and value.strip():
                observation[field] = value
            elif value not in (None, ""):
                findings.append(f"invalid_workflow_field:{key}:{field}")
        observations[key] = observation

    return {
        "status": "WARN" if findings else "PASS",
        "valid": not findings,
        "observations": observations,
        "findings": findings,
        "source": str(observations_path),
        "updated_at": payload.get("updated_at", "") if isinstance(payload, dict) else "",
    }


def _workflow_components(
    workflow_statuses: Optional[Dict[str, Any]],
    workflow_observations: Optional[Dict[str, Any]],
) -> List[Dict[str, Any]]:
    provided = workflow_statuses
    cached = workflow_observations or {}
    components: List[Dict[str, Any]] = []
    for workflow_name in KNOWN_WORKFLOWS:
        key = WORKFLOW_OBSERVATION_KEYS[workflow_name]
        if provided is not None and workflow_name in provided:
            status = _normalize_status(provided[workflow_name])
            source = "provided"
            extra: Dict[str, Any] = {}
        elif key in cached:
            item = cached[key]
            status = _normalize_status(item.get("status"))
            source = str(item.get("observation_source", "cache"))
            extra = {
                field: item[field]
                for field in WORKFLOW_OBSERVATION_OPTIONAL_FIELDS
                if isinstance(item.get(field), str) and item[field].strip()
            }
        else:
            status = "UNKNOWN"
            source = "not_observed"
            extra = {}
        if status == "UNKNOWN":
            summary = "Workflow status is not observed by the local dashboard input."
        elif source == "cache_invalid":
            summary = "Workflow observation is invalid and requires review."
        elif source == "cache":
            summary = f"Cached workflow observation status is {status}."
        else:
            summary = f"Last observed workflow status is {status}."
        components.append(_component(workflow_name, status, summary, observation_source=source, **extra))
    return components


def build_health_dashboard(
    *,
    root: Optional[Path] = None,
    workflow_statuses: Optional[Dict[str, Any]] = None,
    workflow_observations_path: Optional[Path] = None,
    core_statuses: Optional[Dict[str, Any]] = None,
    runner_warnings: Optional[List[str]] = None,
    generated_at: Optional[str] = None,
) -> Dict[str, Any]:
    repo_root = (root or DEFAULT_ROOT).resolve()
    core = {key: _normalize_status(value) for key, value in (core_statuses or _build_default_core_statuses(repo_root)).items()}
    observations_path = workflow_observations_path or repo_root / "config" / "workflow_observations.json"
    observations_result = load_workflow_observations(observations_path)
    workflows = _workflow_components(workflow_statuses, observations_result["observations"])
    ci_status = _section_status([_rollup_status(workflows), observations_result["status"]])

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
            "observations_cache": {
                "status": observations_result["status"],
                "valid": observations_result["valid"],
                "source": observations_result["source"],
                "updated_at": observations_result.get("updated_at", ""),
                "findings": observations_result["findings"],
            },
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
            "id": "workflow_observations_cache",
            "status": observations_result["status"],
            "summary": "Local workflow observations cache is optional and must remain valid evidence.",
            "findings": observations_result["findings"],
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
        "Keep workflow observations local, token-free, and evidence-based.",
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
        details = []
        for field in ("run_id", "artifact_id", "notes"):
            if workflow.get(field):
                details.append(f"{field}: {workflow[field]}")
        suffix = f" ({'; '.join(details)})" if details else ""
        lines.append(f"- {workflow['name']}: {workflow['status']}{suffix}")

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
