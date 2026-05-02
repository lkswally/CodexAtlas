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
try:
    from tools.project_intent_analyzer import analyze_project_intent
except ModuleNotFoundError:
    from project_intent_analyzer import analyze_project_intent
try:
    from tools.prompt_builder import build_prompt
except ModuleNotFoundError:
    from prompt_builder import build_prompt
try:
    from tools.model_router import recommend_model_profile
except ModuleNotFoundError:
    from model_router import recommend_model_profile
try:
    from tools.skill_evaluator import evaluate_skill_candidate
except ModuleNotFoundError:
    from skill_evaluator import evaluate_skill_candidate
try:
    from tools.priority_engine import build_execution_plan
except ModuleNotFoundError:
    from priority_engine import build_execution_plan
try:
    from tools.decision_feedback import find_relevant_feedback
except ModuleNotFoundError:
    from decision_feedback import find_relevant_feedback
try:
    from tools.feedback_analyzer import analyze_feedback
except ModuleNotFoundError:
    from feedback_analyzer import analyze_feedback
try:
    from tools.error_pattern_analyzer import analyze_error_patterns
except ModuleNotFoundError:
    from error_pattern_analyzer import analyze_error_patterns


DEFAULT_ROOT = Path(__file__).resolve().parents[1]
SEVERITY_RANK = {"blocker": 4, "high": 3, "medium": 2, "low": 1}
CORE_REPORTS = {
    "project-phase-report",
    "audit-repo",
    "certify-project",
    "design_intelligence_audit",
    "surface-audit",
}


def _collect_feedback_candidates(
    top_priorities: List[Dict[str, Any]],
    quick_wins: List[str],
    execution_plan: List[Dict[str, Any]],
    primary_action: Optional[str],
) -> Tuple[List[str], List[str]]:
    recommendation_ids: List[str] = []
    actions: List[str] = []
    seen_ids: set[str] = set()
    seen_actions: set[str] = set()

    for item in top_priorities:
        check = str(item.get("check", "")).strip()
        if check and check not in seen_ids:
            seen_ids.add(check)
            recommendation_ids.append(check)

    for action in [primary_action, *quick_wins]:
        action_text = str(action or "").strip()
        if action_text and action_text not in seen_actions:
            seen_actions.add(action_text)
            actions.append(action_text)

    for step in execution_plan:
        action_text = str(step.get("action", "")).strip()
        if action_text and action_text not in seen_actions:
            seen_actions.add(action_text)
            actions.append(action_text)

    return recommendation_ids, actions


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
    if not bool(output.get("ok", False)):
        reason = str(output.get("error", "dispatch_failed"))
        if output.get("phase_report"):
            reason = f"{reason}:current_phase={output['phase_report'].get('current_phase')}"
        return _build_failed_report(command_id, reason)
    return _build_ok_report(command_id, output)


def _run_design_report(project: Path) -> Dict[str, Any]:
    try:
        report = anti_generic_ui_audit(project)
    except Exception as exc:
        return _build_failed_report("design_intelligence_audit", f"design_audit_failed:{exc}")
    return _build_ok_report("design_intelligence_audit", report)


def _run_intent_report(project: Path) -> Dict[str, Any]:
    try:
        report = analyze_project_intent(project=project)
    except Exception as exc:
        return _build_failed_report("project_intent_analyzer", f"intent_analysis_failed:{exc}")
    return _build_ok_report("project_intent_analyzer", report)


def _run_model_route(
    root: Path,
    project: Path,
    *,
    phase_report: Dict[str, Any],
    intent_report: Dict[str, Any],
) -> Dict[str, Any]:
    try:
        report = recommend_model_profile(
            root=root,
            task=f"quality gate follow-up for {project.name}",
            intent="code_review",
            current_phase=str(phase_report.get("current_phase", "")).strip() or None,
            risk_level=str(intent_report.get("risk_level", "low")).strip(),
            complexity=str(intent_report.get("complexity", "low")).strip(),
            project_type=str(intent_report.get("project_type", "unknown")).strip(),
        )
    except Exception as exc:
        return _build_failed_report("model_router", f"model_router_failed:{exc}")
    return _build_ok_report("model_router", report)


def _step_intent_hint(source: str) -> Optional[str]:
    normalized = str(source or "").strip().lower()
    if normalized in {"phase", "intent", "skill"}:
        return "planning"
    if normalized in {"design_audit", "quick_win"}:
        return "branding_ux"
    if normalized in {"audit-repo", "certify-project", "surface-audit", "priority"}:
        return "code_review"
    return None


def _enrich_execution_plan_with_models(
    *,
    root: Path,
    execution_plan: List[Dict[str, Any]],
    current_phase: Optional[str],
    intent_report: Optional[Dict[str, Any]],
) -> List[Dict[str, Any]]:
    enriched: List[Dict[str, Any]] = []
    risk_level = str((intent_report or {}).get("risk_level", "medium")).strip() or "medium"
    complexity = str((intent_report or {}).get("complexity", "medium")).strip() or "medium"
    project_type = str((intent_report or {}).get("project_type", "unknown")).strip() or "unknown"

    for step in execution_plan:
        step_copy = dict(step)
        action = str(step.get("action", "")).strip()
        source = str(step.get("source", "")).strip()
        try:
            route = recommend_model_profile(
                root=root,
                task=action,
                intent=_step_intent_hint(source),
                current_phase=str(current_phase or "").strip() or None,
                risk_level=risk_level,
                complexity=complexity,
                project_type=project_type,
            )
        except Exception as exc:
            step_copy.update(
                {
                    "recommended_model": None,
                    "fallback_model": None,
                    "cheaper_alternative_model": None,
                    "requires_user_confirmation": True,
                    "why_model": f"model_router_failed:{exc}",
                }
            )
            enriched.append(step_copy)
            continue

        step_copy.update(
            {
                "recommended_model": route.get("recommended_model"),
                "fallback_model": route.get("fallback_model"),
                "cheaper_alternative_model": route.get("cost_saver_model")
                or route.get("cheaper_alternative_model"),
                "requires_user_confirmation": bool(route.get("requires_user_confirmation")),
                "why_model": route.get("why"),
            }
        )
        enriched.append(step_copy)
    return enriched


def _run_prompt_report(
    root: Path,
    project: Path,
    *,
    phase_report: Optional[Dict[str, Any]] = None,
    intent_report: Optional[Dict[str, Any]] = None,
    model_route: Optional[Dict[str, Any]] = None,
    priority_bundle: Optional[Dict[str, Any]] = None,
    feedback_analysis: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    try:
        report = build_prompt(
            root=root,
            project=project,
            phase_report=phase_report,
            intent_report=intent_report,
            model_route=model_route,
            priority_bundle=priority_bundle,
            feedback_analysis=feedback_analysis,
        )
    except Exception as exc:
        return _build_failed_report("prompt_builder", f"prompt_builder_failed:{exc}")
    return _build_ok_report("prompt_builder", report)


def _run_skill_signal(
    root: Path,
    project: Path,
    current_phase: str,
    top_priorities: List[Dict[str, Any]],
    intent_report: Dict[str, Any],
) -> Dict[str, Any]:
    if not top_priorities:
        return _build_ok_report(
            "skill_evaluator",
            {
                "status": "ok",
                "candidate_name": "atlas-follow-up-guidance",
                "project_path": str(project),
                "project_type": ((intent_report.get("report") or {}).get("project_type")) if isinstance(intent_report, dict) else "unknown",
                "need_score": 15,
                "reuse_potential": "low",
                "complexity": "low",
                "should_create": False,
                "overlapping_skills": [],
                "reasoning": [
                    "The current project does not expose open priorities that justify a new reusable Atlas skill.",
                    "Keep using the existing phase, audit and prompt layers until a repeatable cross-project gap appears.",
                ],
                "evidence": ["no_top_priorities"],
                "timestamp": _utc_now_iso(),
            },
        )
    candidate = "atlas-follow-up-guidance"
    priority_labels = [str(item.get("check", "")).strip() or str(item.get("message", "")).strip() for item in top_priorities]
    project_type = (
        ((intent_report.get("report") or {}).get("project_type"))
        if isinstance(intent_report, dict)
        else None
    ) or "unknown"
    problem_statement = (
        f"Project is in phase {current_phase}. "
        f"Project type: {project_type}. "
        f"Current priorities: {', '.join(priority_labels[:3]) or 'none'}. "
        "Evaluate whether Atlas needs a new reusable skill or should reuse existing guidance."
    )
    try:
        report = evaluate_skill_candidate(
            root=root,
            candidate_name=candidate,
            problem_statement=problem_statement,
            project=project,
        )
    except Exception as exc:
        return _build_failed_report("skill_evaluator", f"skill_evaluator_failed:{exc}")
    return _build_ok_report("skill_evaluator", report)


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
        if source_name not in CORE_REPORTS:
            continue
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
    if any(source_reports[name].get("status") == "failed" for name in CORE_REPORTS):
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
    if design_report.get("public_readiness") == "not_ready":
        return "not_ready"
    if audit_report.get("result", {}).get("status") != "ok":
        return "needs_improvement"
    if surface_report.get("result", {}).get("warnings"):
        return "needs_improvement"
    if design_report.get("public_readiness") == "needs_improvement":
        return "needs_improvement"
    if design_report.get("status") in {"needs_attention", "skipped"}:
        return "needs_improvement"
    return "ready"


def _derive_confidence_level(source_reports: Dict[str, Dict[str, Any]]) -> str:
    if any(source_reports[name].get("status") == "failed" for name in CORE_REPORTS):
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
        "core_subreports_failed": sum(1 for name, report in source_reports.items() if name in CORE_REPORTS and report.get("status") == "failed"),
        "audit_status": audit_report.get("result", {}).get("status"),
        "certify_score": certify_report.get("result", {}).get("summary", {}).get("score"),
        "design_score": design_report.get("score"),
        "landing_score": design_report.get("landing_score"),
        "public_readiness": design_report.get("public_readiness"),
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
    phase_report = _run_dispatch_report("project-phase-report", root=root, project=project)
    intent_report = _run_intent_report(project)
    feedback_report = _build_ok_report("feedback_analyzer", analyze_feedback(root=root, project_path=project))

    source_reports = {
        "project-phase-report": phase_report,
        "audit-repo": _run_dispatch_report("audit-repo", root=root, project=project),
        "certify-project": _run_dispatch_report("certify-project", root=root, project=project),
        "design_intelligence_audit": _run_design_report(project),
        "surface-audit": _run_dispatch_report("surface-audit", root=root, project=None),
        "project_intent_analyzer": intent_report,
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
    landing_score = design_report.get("landing_score")
    public_readiness = design_report.get("public_readiness", "needs_improvement")
    phase_result = phase_report.get("report") or {}
    if "result" in phase_result and isinstance(phase_result["result"], dict):
        phase_data = phase_result["result"]
    else:
        phase_data = phase_result
    current_phase = phase_data.get("current_phase")
    phase_alignment = {
        "current_phase": current_phase,
        "minimum_expected_phase": "audit",
        "is_aligned": current_phase in {"audit", "certified"},
        "blocked_actions": phase_data.get("blocked_actions", []),
    }
    phase_validity = "valid" if phase_alignment["is_aligned"] else "invalid"
    phase_guidance = {
        "current_phase": current_phase,
        "phase_validity": phase_validity,
        "recommended_next_steps": phase_data.get("recommended_next_steps", []),
        "top_phase_risks": phase_data.get("common_mistakes", [])[:3],
    }
    source_reports["skill_evaluator"] = _run_skill_signal(root, project, str(current_phase or ""), top_priorities, source_reports["project_intent_analyzer"])
    source_reports["feedback_analyzer"] = feedback_report
    source_reports["model_router"] = _run_model_route(
        root,
        project,
        phase_report=phase_data,
        intent_report=source_reports["project_intent_analyzer"]["report"] if source_reports["project_intent_analyzer"]["status"] == "ok" else {},
    )
    priority_bundle = build_execution_plan(
        phase_guidance=phase_guidance,
        phase_validity=phase_validity,
        top_priorities=top_priorities,
        quick_wins=quick_wins,
        intent_analysis=source_reports["project_intent_analyzer"]["report"] if source_reports["project_intent_analyzer"]["status"] == "ok" else None,
        skill_creation_signal=source_reports["skill_evaluator"]["report"] if source_reports["skill_evaluator"]["status"] == "ok" else None,
        overall_status=overall_status,
        feedback_analysis=source_reports["feedback_analyzer"]["report"] if source_reports["feedback_analyzer"]["status"] == "ok" else None,
    )
    source_reports["prompt_builder"] = _run_prompt_report(
        root,
        project,
        phase_report=phase_data,
        intent_report=source_reports["project_intent_analyzer"]["report"] if source_reports["project_intent_analyzer"]["status"] == "ok" else None,
        model_route=source_reports["model_router"]["report"] if source_reports["model_router"]["status"] == "ok" else None,
        priority_bundle=priority_bundle,
        feedback_analysis=source_reports["feedback_analyzer"]["report"] if source_reports["feedback_analyzer"]["status"] == "ok" else None,
    )
    enriched_execution_plan = _enrich_execution_plan_with_models(
        root=root,
        execution_plan=priority_bundle["execution_plan"],
        current_phase=current_phase,
        intent_report=source_reports["project_intent_analyzer"]["report"] if source_reports["project_intent_analyzer"]["status"] == "ok" else None,
    )
    source_reports["error_pattern_analyzer"] = _build_ok_report(
        "error_pattern_analyzer",
        analyze_error_patterns(root=root, project=project),
    )
    feedback_recommendation_ids, feedback_actions = _collect_feedback_candidates(
        top_priorities=top_priorities,
        quick_wins=priority_bundle["quick_wins"],
        execution_plan=priority_bundle["execution_plan"],
        primary_action=priority_bundle["primary_action"],
    )
    decision_feedback = find_relevant_feedback(
        root=root,
        project_path=project,
        recommendation_ids=feedback_recommendation_ids,
        actions=feedback_actions,
        limit=5,
    )

    return {
        "status": "ok",
        "project_path": str(project),
        "overall_status": overall_status,
        "confidence_level": confidence_level,
        "landing_score": landing_score,
        "public_readiness": public_readiness,
        "phase_alignment": phase_alignment,
        "phase_validity": phase_validity,
        "phase_guidance": phase_guidance,
        "intent_analysis": source_reports["project_intent_analyzer"]["report"] if source_reports["project_intent_analyzer"]["status"] == "ok" else None,
        "model_routing": source_reports["model_router"]["report"] if source_reports["model_router"]["status"] == "ok" else None,
        "prompt_guidance": source_reports["prompt_builder"]["report"] if source_reports["prompt_builder"]["status"] == "ok" else None,
        "skill_creation_signal": source_reports["skill_evaluator"]["report"] if source_reports["skill_evaluator"]["status"] == "ok" else None,
        "system_learning": source_reports["error_pattern_analyzer"]["report"] if source_reports["error_pattern_analyzer"]["status"] == "ok" else None,
        "blockers": blockers,
        "warnings": warnings,
        "top_priorities": top_priorities,
        "quick_wins": priority_bundle["quick_wins"],
        "execution_plan": enriched_execution_plan,
        "feedback_adjusted_priorities": priority_bundle["feedback_adjusted_priorities"],
        "detected_patterns": (source_reports["feedback_analyzer"]["report"] or {}).get("detected_patterns", []) if source_reports["feedback_analyzer"]["status"] == "ok" else [],
        "primary_action": priority_bundle["primary_action"],
        "why_now": priority_bundle["why_now"],
        "decision_feedback": decision_feedback,
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
