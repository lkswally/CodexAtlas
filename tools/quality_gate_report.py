from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

try:
    from tools.design_intelligence_audit import anti_generic_ui_audit
except ModuleNotFoundError:
    from design_intelligence_audit import anti_generic_ui_audit


DEFAULT_ROOT = Path(__file__).resolve().parents[1]
SEVERITY_RANK = {"blocker": 4, "high": 3, "medium": 2, "low": 1}


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _build_failed_report(source: str, reason: str) -> Dict[str, Any]:
    return {
        "status": "failed",
        "reason": reason,
        "report": None,
    }


def _build_ok_report(source: str, report: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "status": "ok",
        "reason": None,
        "report": report,
    }


def _dispatch_output(command_id: str, root: Path, project: Optional[Path] = None) -> Dict[str, Any]:
    try:
        from tools.atlas_dispatcher import dispatch
    except ModuleNotFoundError:
        from atlas_dispatcher import dispatch
    return dispatch(command_id, root=root, project=project).output


def _run_dispatch_report(command_id: str, root: Path, project: Optional[Path] = None) -> Dict[str, Any]:
    try:
        output = _dispatch_output(command_id, root=root, project=project)
    except Exception as exc:
        return _build_failed_report(command_id, f"dispatch_failed:{exc}")
    return _build_ok_report(command_id, output)


def _run_design_report(project: Path) -> Dict[str, Any]:
    try:
        report = anti_generic_ui_audit(project)
    except Exception as exc:
        return _build_failed_report("design_intelligence_audit", f"design_audit_failed:{exc}")
    return _build_ok_report("design_intelligence_audit", report)


def _extract_certify_blockers(certify_report: Dict[str, Any]) -> List[Dict[str, Any]]:
    report = certify_report.get("report") or {}
    result = report.get("result", {})
    blockers: List[Dict[str, Any]] = []
    for blocker in result.get("blockers", []):
        if not isinstance(blocker, dict):
            continue
        blockers.append(
            {
                "source": "certify-project",
                "check": blocker.get("code", "certify_blocker"),
                "severity": blocker.get("severity", "blocker"),
                "message": blocker.get("message", "Certification blocker detected."),
                "evidence": [blocker.get("path")] if blocker.get("path") else [],
            }
        )
    return blockers


def _extract_surface_warnings(surface_report: Dict[str, Any]) -> List[Dict[str, Any]]:
    report = surface_report.get("report") or {}
    result = report.get("result", {})
    warnings: List[Dict[str, Any]] = []
    for warning in result.get("warnings", []):
        if not isinstance(warning, dict):
            continue
        warnings.append(
            {
                "source": "surface-audit",
                "check": warning.get("code", "surface_warning"),
                "severity": warning.get("severity", "medium"),
                "message": warning.get("message", "Surface-audit warning detected."),
                "evidence": list(warning.get("details", []))[:3],
            }
        )
    return warnings


def _extract_design_warning_items(design_report: Dict[str, Any]) -> List[Dict[str, Any]]:
    report = design_report.get("report") or {}
    items: List[Dict[str, Any]] = []
    for source in report.get("recommendation_sources", []):
        if not isinstance(source, dict):
            continue
        if source.get("status") not in {"warning", "fail"}:
            continue
        items.append(
            {
                "source": "design_intelligence_audit",
                "check": source.get("originating_check", "design_warning"),
                "severity": source.get("severity", "medium"),
                "message": source.get("recommendation", "Review the design warning."),
                "evidence": list(source.get("evidence", []))[:3],
            }
        )
    return items


def _extract_failed_source_items(source_reports: Dict[str, Dict[str, Any]]) -> List[Dict[str, Any]]:
    items: List[Dict[str, Any]] = []
    for source_name, source_report in source_reports.items():
        if source_report.get("status") == "failed":
            items.append(
                {
                    "source": source_name,
                    "check": "subreport_failed",
                    "severity": "blocker",
                    "message": f"{source_name} could not complete.",
                    "evidence": [source_report.get("reason", "unknown_failure")],
                }
            )
    return items


def _unique_priority_append(items: List[Dict[str, Any]], candidate: Dict[str, Any], seen: set[Tuple[str, str]]) -> None:
    key = (str(candidate.get("source", "")), str(candidate.get("message", "")))
    if key in seen:
        return
    seen.add(key)
    items.append(candidate)


def _derive_overall_status(source_reports: Dict[str, Dict[str, Any]]) -> str:
    if any(item.get("status") == "failed" for item in source_reports.values()):
        return "not_ready"

    audit_report = source_reports["audit-repo"]["report"]
    certify_report = source_reports["certify-project"]["report"]
    design_report = source_reports["design_intelligence_audit"]["report"]
    surface_report = source_reports["surface-audit"]["report"]

    if not audit_report.get("ok", False):
        return "not_ready"
    if not certify_report.get("ok", False):
        return "not_ready"
    if certify_report.get("result", {}).get("blockers"):
        return "not_ready"
    if audit_report.get("result", {}).get("status") != "ok":
        return "needs_improvement"
    if surface_report.get("result", {}).get("warnings"):
        return "needs_improvement"
    if design_report.get("status") in {"needs_attention", "skipped"}:
        return "needs_improvement"
    return "ready"


def _derive_confidence_level(source_reports: Dict[str, Dict[str, Any]]) -> str:
    if any(item.get("status") == "failed" for item in source_reports.values()):
        return "low"

    certify_report = source_reports["certify-project"]["report"]
    design_report = source_reports["design_intelligence_audit"]["report"]
    surface_report = source_reports["surface-audit"]["report"]
    audit_report = source_reports["audit-repo"]["report"]

    if audit_report.get("result", {}).get("status") != "ok":
        return "medium"
    if surface_report.get("result", {}).get("warnings"):
        return "medium"
    if certify_report.get("result", {}).get("warnings"):
        return "medium"
    if any(check.get("status") == "skipped" for check in design_report.get("checks", []) if isinstance(check, dict)):
        return "medium"
    if design_report.get("warnings"):
        return "medium"
    return "high"


def _build_evidence_summary(source_reports: Dict[str, Dict[str, Any]], blockers: List[Dict[str, Any]], warnings: List[Dict[str, Any]]) -> Dict[str, Any]:
    design_report = source_reports["design_intelligence_audit"].get("report") or {}
    certify_report = source_reports["certify-project"].get("report") or {}
    surface_report = source_reports["surface-audit"].get("report") or {}
    audit_report = source_reports["audit-repo"].get("report") or {}
    return {
        "subreports_ok": sum(1 for report in source_reports.values() if report.get("status") == "ok"),
        "subreports_failed": sum(1 for report in source_reports.values() if report.get("status") == "failed"),
        "audit_status": audit_report.get("result", {}).get("status"),
        "certify_score": certify_report.get("result", {}).get("summary", {}).get("score"),
        "design_score": design_report.get("score"),
        "surface_warnings": len(surface_report.get("result", {}).get("warnings", [])),
        "blocker_count": len(blockers),
        "warning_count": len(warnings),
    }


def _build_summary_for_human(overall_status: str, confidence_level: str, blockers: List[Dict[str, Any]], top_priorities: List[Dict[str, Any]]) -> str:
    if overall_status == "ready":
        return f"Atlas quality gate is ready with {confidence_level} confidence. No blockers or open warnings were detected."
    if overall_status == "not_ready":
        return f"Atlas quality gate is not ready with {confidence_level} confidence. Resolve {len(blockers)} blocker(s) before handoff."
    first_focus = top_priorities[0]["message"] if top_priorities else "Review the aggregated warnings."
    return f"Atlas quality gate needs improvement with {confidence_level} confidence. First focus: {first_focus}"


def _build_recommended_next_action(overall_status: str, blockers: List[Dict[str, Any]], top_priorities: List[Dict[str, Any]]) -> str:
    if overall_status == "ready":
        return "Proceed to human review or handoff with the current project state."
    if overall_status == "not_ready" and blockers:
        return blockers[0]["message"]
    if top_priorities:
        return top_priorities[0]["message"]
    return "Review the aggregated report and decide the next safe action."


def build_quality_gate_report(root: Path, project: Path) -> Dict[str, Any]:
    root = root.resolve()
    project = project.resolve()

    source_reports = {
        "audit-repo": _run_dispatch_report("audit-repo", root=root, project=project),
        "certify-project": _run_dispatch_report("certify-project", root=root, project=project),
        "design_intelligence_audit": _run_design_report(project),
        "surface-audit": _run_dispatch_report("surface-audit", root=root, project=None),
    }

    blockers = _extract_certify_blockers(source_reports["certify-project"])
    warnings: List[Dict[str, Any]] = []
    seen: set[Tuple[str, str]] = set()

    for item in _extract_failed_source_items(source_reports):
        _unique_priority_append(blockers, item, seen)

    candidate_priorities: List[Dict[str, Any]] = []
    candidate_seen: set[Tuple[str, str]] = set()
    for item in blockers:
        _unique_priority_append(candidate_priorities, item, candidate_seen)
    for item in _extract_design_warning_items(source_reports["design_intelligence_audit"]):
        _unique_priority_append(candidate_priorities, item, candidate_seen)
        _unique_priority_append(warnings, item, seen)
    for item in _extract_surface_warnings(source_reports["surface-audit"]):
        _unique_priority_append(candidate_priorities, item, candidate_seen)
        _unique_priority_append(warnings, item, seen)

    certify_report = source_reports["certify-project"].get("report") or {}
    for warning in certify_report.get("result", {}).get("warnings", []):
        if not isinstance(warning, dict):
            continue
        item = {
            "source": "certify-project",
            "check": warning.get("code", "certify_warning"),
            "severity": warning.get("severity", "medium"),
            "message": warning.get("message", "Certification warning detected."),
            "evidence": [warning.get("path")] if warning.get("path") else [],
        }
        _unique_priority_append(candidate_priorities, item, candidate_seen)
        _unique_priority_append(warnings, item, seen)

    candidate_priorities.sort(key=lambda item: SEVERITY_RANK.get(str(item.get("severity", "low")), 0), reverse=True)
    top_priorities = candidate_priorities[:3]

    quick_wins: List[str] = []
    seen_quick_wins: set[str] = set()
    design_report = source_reports["design_intelligence_audit"].get("report") or {}
    for message in design_report.get("quick_wins", []):
        message_s = str(message).strip()
        if message_s and message_s not in seen_quick_wins:
            seen_quick_wins.add(message_s)
            quick_wins.append(message_s)
        if len(quick_wins) >= 3:
            break
    if len(quick_wins) < 3:
        for item in top_priorities:
            message_s = str(item.get("message", "")).strip()
            if message_s and message_s not in seen_quick_wins:
                seen_quick_wins.add(message_s)
                quick_wins.append(message_s)
            if len(quick_wins) >= 3:
                break

    overall_status = _derive_overall_status(source_reports)
    confidence_level = _derive_confidence_level(source_reports)
    evidence_summary = _build_evidence_summary(source_reports, blockers, warnings)
    summary_for_human = _build_summary_for_human(overall_status, confidence_level, blockers, top_priorities)
    recommended_next_action = _build_recommended_next_action(overall_status, blockers, top_priorities)

    return {
        "status": "ok",
        "project_path": str(project),
        "overall_status": overall_status,
        "confidence_level": confidence_level,
        "blockers": blockers,
        "warnings": warnings,
        "top_priorities": top_priorities,
        "quick_wins": quick_wins,
        "evidence_summary": evidence_summary,
        "source_reports": source_reports,
        "summary_for_human": summary_for_human,
        "recommended_next_action": recommended_next_action,
        "root": str(root),
        "timestamp": _utc_now_iso(),
    }


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(add_help=True)
    parser.add_argument("--root", default=None, help="Atlas root to use. Defaults to this repository root.")
    parser.add_argument("--project", required=True, help="Derived project path to evaluate.")
    args = parser.parse_args(argv)

    root = Path(args.root).resolve() if args.root else DEFAULT_ROOT
    project = Path(args.project).resolve()
    report = build_quality_gate_report(root, project)
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
