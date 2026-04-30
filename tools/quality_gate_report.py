from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

try:
    from tools.atlas_dispatcher import dispatch
except ModuleNotFoundError:
    from atlas_dispatcher import dispatch

try:
    from tools.design_intelligence_audit import anti_generic_ui_audit
except ModuleNotFoundError:
    from design_intelligence_audit import anti_generic_ui_audit


DEFAULT_ROOT = Path(__file__).resolve().parents[1]
SEVERITY_RANK = {"blocker": 3, "high": 2, "medium": 1, "low": 0}


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _unique_append(items: List[Dict[str, Any]], candidate: Dict[str, Any], seen: set[Tuple[str, str]]) -> None:
    key = (str(candidate.get("source", "")), str(candidate.get("message", "")))
    if key in seen:
        return
    seen.add(key)
    items.append(candidate)


def _extract_blocking_issues(certify_result: Dict[str, Any]) -> List[Dict[str, Any]]:
    issues: List[Dict[str, Any]] = []
    for blocker in certify_result.get("blockers", []):
        if not isinstance(blocker, dict):
            continue
        issues.append(
            {
                "source": "certify-project",
                "check": blocker.get("code", "certify_blocker"),
                "severity": blocker.get("severity", "blocker"),
                "message": blocker.get("message", "Certification blocker detected."),
                "evidence": [blocker.get("path")] if blocker.get("path") else [],
            }
        )
    return issues


def _extract_design_priorities(design_result: Dict[str, Any]) -> List[Dict[str, Any]]:
    priorities: List[Dict[str, Any]] = []
    for item in design_result.get("recommendation_sources", []):
        if not isinstance(item, dict):
            continue
        if item.get("status") not in {"warning", "fail"}:
            continue
        priorities.append(
            {
                "source": "design_intelligence_audit",
                "check": item.get("originating_check", "design_check"),
                "severity": item.get("severity", "medium"),
                "message": item.get("recommendation", "Review the design evidence and address the warning."),
                "evidence": list(item.get("evidence", []))[:3],
            }
        )
    return priorities


def _extract_surface_priorities(surface_result: Dict[str, Any]) -> List[Dict[str, Any]]:
    priorities: List[Dict[str, Any]] = []
    warnings = surface_result.get("warnings", [])
    recommendations = surface_result.get("recommendations", [])
    for index, warning in enumerate(warnings):
        if not isinstance(warning, dict):
            continue
        message = recommendations[index] if index < len(recommendations) else warning.get("message", "Resolve the surface-audit warning.")
        priorities.append(
            {
                "source": "surface-audit",
                "check": warning.get("code", "surface_warning"),
                "severity": warning.get("severity", "medium"),
                "message": message,
                "evidence": list(warning.get("details", []))[:3],
            }
        )
    return priorities


def _derive_overall_status(
    audit_output: Dict[str, Any],
    certify_output: Dict[str, Any],
    design_output: Dict[str, Any],
    surface_output: Dict[str, Any],
) -> str:
    if not audit_output.get("ok", False) or not certify_output.get("ok", False) or not surface_output.get("ok", False):
        return "not_ready"
    certify_result = certify_output.get("result", {})
    if certify_result.get("blockers"):
        return "not_ready"
    if audit_output.get("result", {}).get("status") != "ok":
        return "needs_improvement"
    if surface_output.get("result", {}).get("warnings"):
        return "needs_improvement"
    if design_output.get("status") in {"needs_attention", "skipped"}:
        return "needs_improvement"
    return "ready"


def _derive_confidence_level(
    audit_output: Dict[str, Any],
    certify_output: Dict[str, Any],
    design_output: Dict[str, Any],
    surface_output: Dict[str, Any],
) -> str:
    if not audit_output.get("ok", False) or not certify_output.get("ok", False) or not surface_output.get("ok", False):
        return "low"
    if any(check.get("status") == "skipped" for check in design_output.get("checks", []) if isinstance(check, dict)):
        return "medium"
    if design_output.get("warnings") or surface_output.get("result", {}).get("warnings") or certify_output.get("result", {}).get("warnings"):
        return "medium"
    return "high"


def _build_summary_for_human(
    overall_status: str,
    confidence_level: str,
    blocking_issues: List[Dict[str, Any]],
    top_priorities: List[Dict[str, Any]],
) -> str:
    if overall_status == "ready":
        return f"Atlas quality gate is ready with {confidence_level} confidence. No blocking issues were detected."
    if overall_status == "not_ready":
        return (
            f"Atlas quality gate is not ready with {confidence_level} confidence. "
            f"{len(blocking_issues)} blocking issue(s) must be resolved before proceeding."
        )
    top_focus = top_priorities[0]["message"] if top_priorities else "Review the latest warnings."
    return f"Atlas quality gate needs improvement with {confidence_level} confidence. First focus: {top_focus}"


def build_quality_gate_report(root: Path, project: Path) -> Dict[str, Any]:
    root = root.resolve()
    project = project.resolve()

    audit_output = dispatch("audit-repo", root=root, project=project).output
    certify_output = dispatch("certify-project", root=root, project=project).output
    surface_output = dispatch("surface-audit", root=root).output
    design_output = anti_generic_ui_audit(project)

    blocking_issues = _extract_blocking_issues(certify_output.get("result", {}))

    candidates: List[Dict[str, Any]] = []
    seen: set[Tuple[str, str]] = set()
    for item in blocking_issues:
        _unique_append(candidates, item, seen)
    for item in _extract_design_priorities(design_output):
        _unique_append(candidates, item, seen)
    for item in _extract_surface_priorities(surface_output.get("result", {})):
        _unique_append(candidates, item, seen)

    candidates.sort(key=lambda item: SEVERITY_RANK.get(str(item.get("severity", "low")), 0), reverse=True)
    top_priorities = candidates[:3]

    quick_wins = []
    seen_quick_wins: set[str] = set()
    for message in design_output.get("quick_wins", []):
        message_s = str(message).strip()
        if not message_s or message_s in seen_quick_wins:
            continue
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

    overall_status = _derive_overall_status(audit_output, certify_output, design_output, surface_output)
    confidence_level = _derive_confidence_level(audit_output, certify_output, design_output, surface_output)
    summary_for_human = _build_summary_for_human(overall_status, confidence_level, blocking_issues, top_priorities)

    return {
        "status": "ok",
        "overall_status": overall_status,
        "confidence_level": confidence_level,
        "blocking_issues": blocking_issues,
        "top_priorities": top_priorities,
        "quick_wins": quick_wins,
        "summary_for_human": summary_for_human,
        "component_results": {
            "audit_repo": audit_output,
            "certify_project": certify_output,
            "design_intelligence_audit": design_output,
            "surface_audit": surface_output,
        },
        "project": str(project),
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
