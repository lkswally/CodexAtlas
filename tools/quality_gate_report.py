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
try:
    from tools.skill_improvement_review import review_skill_catalog
except ModuleNotFoundError:
    from skill_improvement_review import review_skill_catalog
try:
    from tools.creative_pipeline_readiness import check_creative_pipeline_readiness
except ModuleNotFoundError:
    from creative_pipeline_readiness import check_creative_pipeline_readiness
try:
    from tools.component_inspiration_readiness import check_component_inspiration_readiness
except ModuleNotFoundError:
    from component_inspiration_readiness import check_component_inspiration_readiness
try:
    from tools.playwright_visual_qa_readiness import check_playwright_visual_qa_readiness
except ModuleNotFoundError:
    from playwright_visual_qa_readiness import check_playwright_visual_qa_readiness
try:
    from tools.design_quality_enforcement import audit_design_quality
except ModuleNotFoundError:
    from design_quality_enforcement import audit_design_quality
try:
    from tools.intent_clarifier_contract import assess_intent_clarifier_contract
except ModuleNotFoundError:
    from intent_clarifier_contract import assess_intent_clarifier_contract
try:
    from tools.brand_json_v2_readiness import assess_brand_json_v2_readiness
except ModuleNotFoundError:
    from brand_json_v2_readiness import assess_brand_json_v2_readiness
try:
    from tools.frontend_auto_audit_rules import audit_frontend_auto_readiness
except ModuleNotFoundError:
    from frontend_auto_audit_rules import audit_frontend_auto_readiness
try:
    from tools.model_cost_control_readiness import assess_model_cost_control
except ModuleNotFoundError:
    from model_cost_control_readiness import assess_model_cost_control
try:
    from tools.atlas_error_learning_review import review_atlas_error_learning
except ModuleNotFoundError:
    from atlas_error_learning_review import review_atlas_error_learning
try:
    from tools.codex_runtime_compatibility_check import check_codex_runtime_compatibility
except ModuleNotFoundError:
    from codex_runtime_compatibility_check import check_codex_runtime_compatibility
try:
    from tools.atlas_memory_readiness import check_atlas_memory_readiness
except ModuleNotFoundError:
    from atlas_memory_readiness import check_atlas_memory_readiness
try:
    from tools.evidence_collector_readiness import review_evidence_collector_readiness
except ModuleNotFoundError:
    from evidence_collector_readiness import review_evidence_collector_readiness
try:
    from tools.change_proposal_readiness import assess_change_proposal_readiness
except ModuleNotFoundError:
    from change_proposal_readiness import assess_change_proposal_readiness


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


LOW_RISK_INFORMATIONAL_PREFIXES = (
    "avoid ",
    "review ",
    "document ",
    "list ",
    "check ",
    "summarize ",
)


def _is_low_risk_informational_action(action: str) -> bool:
    normalized_action = str(action or "").strip().lower()
    return any(normalized_action.startswith(prefix) for prefix in LOW_RISK_INFORMATIONAL_PREFIXES)


def _step_intent_hint(source: str, action: str) -> Optional[str]:
    if _is_low_risk_informational_action(action):
        return "documentation"

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
        step_risk = risk_level
        step_complexity = complexity
        if _is_low_risk_informational_action(action):
            step_risk = "low"
            step_complexity = "low"
        try:
            route = recommend_model_profile(
                root=root,
                task=action,
                intent=_step_intent_hint(source, action),
                current_phase=str(current_phase or "").strip() or None,
                risk_level=step_risk,
                complexity=step_complexity,
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
                "active_runtime_model": route.get("active_runtime_model", "manual_or_unknown"),
                "model_switch_mode": route.get("model_switch_mode", "manual_required"),
                "recommended_model_is_advisory": bool(route.get("recommended_model_is_advisory", True)),
                "user_action_required": route.get(
                    "user_action_required",
                    "Select the recommended model manually in Codex Desktop before running this task.",
                ),
                "can_auto_switch": False,
                "auto_switch_method": "not_available",
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
                "lifecycle_recommendation": "hold_as_candidate",
                "recommended_state": "candidate",
                "promotion_blockers": ["no_repeatable_skill_gap_detected"],
                "duplication_risk": "low",
                "external_dependency_risk": "low",
                "requires_human_approval": False,
                "requires_decision_council": False,
                "why": "No reusable gap is visible, so Atlas should keep this as a candidate idea instead of promoting it.",
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


def _run_skill_improvement_review(root: Path) -> Dict[str, Any]:
    try:
        report = review_skill_catalog(root=root)
    except Exception as exc:
        return _build_failed_report("skill_improvement_review", f"skill_improvement_review_failed:{exc}")
    return _build_ok_report("skill_improvement_review", report)


def _run_creative_pipeline_readiness(root: Path) -> Dict[str, Any]:
    try:
        report = check_creative_pipeline_readiness(root=root)
    except Exception as exc:
        return _build_failed_report("creative_pipeline_readiness", f"creative_pipeline_readiness_failed:{exc}")
    return _build_ok_report("creative_pipeline_readiness", report)


def _run_component_inspiration_readiness(root: Path) -> Dict[str, Any]:
    try:
        report = check_component_inspiration_readiness(root=root)
    except Exception as exc:
        return _build_failed_report("component_inspiration_readiness", f"component_inspiration_readiness_failed:{exc}")
    return _build_ok_report("component_inspiration_readiness", report)


def _run_playwright_visual_qa_readiness(root: Path) -> Dict[str, Any]:
    try:
        report = check_playwright_visual_qa_readiness(root=root)
    except Exception as exc:
        return _build_failed_report("playwright_visual_qa_readiness", f"playwright_visual_qa_readiness_failed:{exc}")
    return _build_ok_report("playwright_visual_qa_readiness", report)


def _run_intent_clarifier_contract(
    *,
    root: Path,
    project: Path,
    intent_report: Optional[Dict[str, Any]],
) -> Dict[str, Any]:
    try:
        report = assess_intent_clarifier_contract(
            project=project,
            payload={
                "project_type": (intent_report or {}).get("project_type"),
                "primary_goal": (intent_report or {}).get("objective"),
                "target_audience": (((intent_report or {}).get("visual_intent_contract") or {}).get("contract") or {}).get("audience"),
                "style_direction": (((intent_report or {}).get("visual_intent_contract") or {}).get("contract") or {}).get("mood_or_vibe"),
                "originality_level": (((intent_report or {}).get("visual_intent_contract") or {}).get("contract") or {}).get("originality_level"),
            },
            root=root,
        )
    except Exception as exc:
        return _build_failed_report("intent_clarifier_contract", f"intent_clarifier_contract_failed:{exc}")
    return _build_ok_report("intent_clarifier_contract", report)


def _run_brand_json_v2_readiness(
    *,
    root: Path,
    project: Path,
    project_type: Optional[str],
    visual_intent_contract: Optional[Dict[str, Any]],
    brand_profile_review: Optional[Dict[str, Any]],
) -> Dict[str, Any]:
    try:
        report = assess_brand_json_v2_readiness(
            project_type=project_type,
            visual_intent_contract=(visual_intent_contract or {}).get("contract") if isinstance(visual_intent_contract, dict) else None,
            profile_review=brand_profile_review,
            project_name=project.name,
            root=root,
        )
    except Exception as exc:
        return _build_failed_report("brand_json_v2_readiness", f"brand_json_v2_readiness_failed:{exc}")
    return _build_ok_report("brand_json_v2_readiness", report)


def _run_frontend_auto_audit_rules(
    *,
    root: Path,
    payload: Dict[str, Any],
) -> Dict[str, Any]:
    try:
        report = audit_frontend_auto_readiness(payload, root=root)
    except Exception as exc:
        return _build_failed_report("frontend_auto_audit_rules", f"frontend_auto_audit_rules_failed:{exc}")
    return _build_ok_report("frontend_auto_audit_rules", report)


def _run_atlas_error_learning_review(
    *,
    root: Path,
    payload: Dict[str, Any],
) -> Dict[str, Any]:
    try:
        report = review_atlas_error_learning(payload, root=root)
    except Exception as exc:
        return _build_failed_report("atlas_error_learning_review", f"atlas_error_learning_review_failed:{exc}")
    return _build_ok_report("atlas_error_learning_review", report)


def _run_codex_runtime_compatibility(root: Path) -> Dict[str, Any]:
    try:
        report = check_codex_runtime_compatibility(root=root)
    except Exception as exc:
        return _build_failed_report("codex_runtime_compatibility_check", f"codex_runtime_compatibility_check_failed:{exc}")
    return _build_ok_report("codex_runtime_compatibility_check", report)


def _run_atlas_memory_readiness(root: Path) -> Dict[str, Any]:
    try:
        report = check_atlas_memory_readiness(root=root)
    except Exception as exc:
        return _build_failed_report("atlas_memory_readiness", f"atlas_memory_readiness_failed:{exc}")
    return _build_ok_report("atlas_memory_readiness", report)


def _run_evidence_collector_readiness(
    *,
    root: Path,
    payload: Dict[str, Any],
) -> Dict[str, Any]:
    try:
        report = review_evidence_collector_readiness(payload, root=root)
    except Exception as exc:
        return _build_failed_report("evidence_collector_readiness", f"evidence_collector_readiness_failed:{exc}")
    return _build_ok_report("evidence_collector_readiness", report)


def _run_change_proposal_readiness(
    *,
    root: Path,
    payload: Dict[str, Any],
) -> Dict[str, Any]:
    try:
        report = assess_change_proposal_readiness(payload, root=root)
    except Exception as exc:
        return _build_failed_report("change_proposal_readiness", f"change_proposal_readiness_failed:{exc}")
    return _build_ok_report("change_proposal_readiness", report)


def _run_model_cost_control(
    *,
    root: Path,
    intent_report: Optional[Dict[str, Any]],
    current_phase: Optional[str],
    top_priorities: List[Dict[str, Any]],
) -> Dict[str, Any]:
    objective = str((intent_report or {}).get("objective", "")).strip()
    priority_messages = [str(item.get("message", "")).strip() for item in top_priorities if str(item.get("message", "")).strip()]
    task = objective or ". ".join(priority_messages[:2]) or "Atlas quality gate follow-up."
    try:
        report = assess_model_cost_control(
            root=root,
            task=task,
            risk_level=str((intent_report or {}).get("risk_level", "medium")).strip() or "medium",
            complexity=str((intent_report or {}).get("complexity", "medium")).strip() or "medium",
            current_phase=str(current_phase or "").strip() or None,
        )
    except Exception as exc:
        return _build_failed_report("model_cost_control_readiness", f"model_cost_control_readiness_failed:{exc}")
    return _build_ok_report("model_cost_control_readiness", report)


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
    design_quality_review = design_report.get("design_quality_review") or {}

    if not audit_report.get("ok", False):
        return "not_ready"
    if not certify_report.get("ok", False):
        return "not_ready"
    if certify_report.get("result", {}).get("blockers"):
        return "not_ready"
    if design_report.get("public_readiness") == "not_ready":
        return "not_ready"
    if isinstance(design_quality_review, dict) and design_quality_review.get("status") == "not_ready":
        return "needs_improvement"
    if audit_report.get("result", {}).get("status") != "ok":
        return "needs_improvement"
    if surface_report.get("result", {}).get("warnings"):
        return "needs_improvement"
    if design_report.get("public_readiness") == "needs_improvement":
        return "needs_improvement"
    if isinstance(design_quality_review, dict) and design_quality_review.get("status") == "needs_attention":
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


def _derive_external_tool_posture(
    *,
    source_reports: Dict[str, Dict[str, Any]],
    blockers: List[Dict[str, Any]],
    warnings: List[Dict[str, Any]],
) -> Dict[str, Any]:
    if any(source_reports[name].get("status") == "failed" for name in CORE_REPORTS):
        return {
            "source_sufficiency": "local_only",
            "recommended_source_layer": "local_repo",
            "why": "Atlas should resolve local report failures before considering any external source.",
            "external_tools_allowed": False,
            "mcp_allowed": False,
        }

    if blockers or warnings:
        return {
            "source_sufficiency": "adapter_enough",
            "recommended_source_layer": "curated_internal_adapters",
            "why": "Current blockers or warnings are already explained by local audits and internal adapters, so no external source is needed.",
            "external_tools_allowed": False,
            "mcp_allowed": False,
        }

    return {
        "source_sufficiency": "local_only",
        "recommended_source_layer": "local_repo",
        "why": "The current readiness decision is fully supported by local repo evidence without needing any external tool.",
        "external_tools_allowed": False,
        "mcp_allowed": False,
    }


def _build_visual_intent_warning(intent_report: Optional[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
    if not isinstance(intent_report, dict):
        return None
    contract = intent_report.get("visual_intent_contract")
    if not isinstance(contract, dict):
        return None
    if not bool(contract.get("requires_contract")):
        return None
    if str(contract.get("status", "")).strip() == "ready":
        return None
    missing = list(contract.get("missing_fields", []))
    weak = list(contract.get("weak_fields", []))
    warning_code = "visual_intent_contract_missing" if missing else "visual_intent_contract_weak"
    message = "Create or clarify the visual intent contract before treating design direction as settled."
    if missing:
        message = f"{message} Missing: {', '.join(missing[:5])}."
    elif weak:
        message = f"{message} Weak: {', '.join(weak[:5])}."
    return {
        "source": "visual_intent_contract",
        "check": warning_code,
        "severity": "medium",
        "message": message,
        "evidence": list(contract.get("missing_fields", []))[:5] + list(contract.get("weak_fields", []))[:5],
    }


def _build_intent_clarifier_warnings(review: Optional[Dict[str, Any]]) -> List[Dict[str, Any]]:
    if not isinstance(review, dict) or not bool(review.get("requires_contract")):
        return []
    if str(review.get("status", "")).strip() == "ready":
        return []
    missing = list(review.get("missing_questions", []))
    weak = list(review.get("weak_answers", []))
    return [
        {
            "source": "intent_clarifier_contract",
            "check": "intent_clarifier_missing" if missing else "intent_clarifier_weak",
            "severity": "high",
            "message": "The upstream intent clarifier is still too weak for a strong UI-readiness claim.",
            "evidence": (missing[:4] + weak[:4]) or list(review.get("approval_triggers", []))[:4],
        }
    ]


def _build_brand_profile_warnings(design_report: Optional[Dict[str, Any]]) -> List[Dict[str, Any]]:
    if not isinstance(design_report, dict):
        return []
    review = design_report.get("brand_profile_review")
    if not isinstance(review, dict) or not bool(review.get("requires_profile")):
        return []

    warnings: List[Dict[str, Any]] = []
    missing = list(review.get("missing_fields", []))
    weak = list(review.get("weak_fields", []))
    invalid = list(review.get("invalid_fields", []))
    generic = list(review.get("anti_generic_risks", []))
    derivative = list(review.get("derivative_risks", []))

    if not bool(review.get("explicit_profile_present")) or missing:
        warnings.append(
            {
                "source": "brand_profile_schema",
                "check": "brand_profile_missing",
                "severity": "medium",
                "message": "Create an explicit brand profile before treating the identity as settled.",
                "evidence": [f"profile_source={review.get('profile_source', 'unknown')}"] + missing[:4],
            }
        )
    if weak or invalid:
        warnings.append(
            {
                "source": "brand_profile_schema",
                "check": "brand_profile_weak",
                "severity": "medium",
                "message": "Clarify the weakest brand-profile fields before stronger branding claims.",
                "evidence": weak[:3] + invalid[:3],
            }
        )
    if generic:
        warnings.append(
            {
                "source": "brand_profile_schema",
                "check": "brand_profile_generic_risk",
                "severity": "medium",
                "message": "The current brand profile still leans toward generic defaults instead of explicit differentiation.",
                "evidence": generic[:4],
            }
        )
    if derivative:
        warnings.append(
            {
                "source": "brand_profile_schema",
                "check": "brand_profile_derivative_risk",
                "severity": "high",
                "message": "The current brand profile needs clearer differentiation from its inspiration references.",
                "evidence": derivative[:4],
            }
        )
    return warnings


def _build_brand_json_v2_warnings(review: Optional[Dict[str, Any]]) -> List[Dict[str, Any]]:
    if not isinstance(review, dict) or not bool(review.get("requires_brand_json_v2", True)):
        return []
    if str(review.get("status", "")).strip() == "ready":
        return []
    warnings: List[Dict[str, Any]] = []
    if not bool(review.get("explicit_profile_present")) or review.get("missing_sections"):
        warnings.append(
            {
                "source": "brand_json_v2_readiness",
                "check": "brand_json_v2_missing",
                "severity": "high",
                "message": "The project still lacks an explicit brand artifact strong enough to act like brand.json v2.",
                "evidence": list(review.get("missing_sections", []))[:4] or [f"profile_source={review.get('profile_source', 'unknown')}"],
            }
        )
    if review.get("weak_sections"):
        warnings.append(
            {
                "source": "brand_json_v2_readiness",
                "check": "brand_json_v2_weak",
                "severity": "medium",
                "message": "The current brand artifact is present but still weak in core sections.",
                "evidence": list(review.get("weak_sections", []))[:4],
            }
        )
    if review.get("derivative_risks"):
        warnings.append(
            {
                "source": "brand_json_v2_readiness",
                "check": "brand_json_v2_derivative_risk",
                "severity": "high",
                "message": "The current brand artifact still needs clearer differentiation from inspiration references.",
                "evidence": list(review.get("derivative_risks", []))[:4],
            }
        )
    return warnings


def _build_ui_pre_return_warnings(design_report: Optional[Dict[str, Any]]) -> List[Dict[str, Any]]:
    if not isinstance(design_report, dict):
        return []
    review = design_report.get("ui_pre_return_review")
    if not isinstance(review, dict):
        return [
            {
                "source": "ui_pre_return_audit",
                "check": "ui_pre_return_audit_missing",
                "severity": "medium",
                "message": "UI pre-return audit output is missing, so final UI readiness has not been cross-checked yet.",
                "evidence": ["ui_pre_return_review_missing"],
            }
        ]

    warnings: List[Dict[str, Any]] = []
    warning_set = set(review.get("warnings", []))

    if "ui_pre_return_missing_evidence" in warning_set:
        warnings.append(
            {
                "source": "ui_pre_return_audit",
                "check": "ui_pre_return_missing_evidence",
                "severity": "high",
                "message": "The UI still lacks explicit evidence expectations before Atlas should treat it as passable.",
                "evidence": list(review.get("missing_evidence", []))[:4],
            }
        )
    if "ui_pre_return_generic_risk" in warning_set:
        warnings.append(
            {
                "source": "ui_pre_return_audit",
                "check": "ui_pre_return_generic_risk",
                "severity": "medium",
                "message": "The current UI still shows generic/template risk before final return.",
                "evidence": list(review.get("anti_generic_risks", []))[:4],
            }
        )
    if "ui_pre_return_brand_mismatch" in warning_set:
        warnings.append(
            {
                "source": "ui_pre_return_audit",
                "check": "ui_pre_return_brand_mismatch",
                "severity": "medium",
                "message": "The current UI still has open brand-alignment mismatches before final return.",
                "evidence": list(review.get("brand_alignment_risks", []))[:4],
            }
        )
    if review.get("status") == "not_ready" or "ui_pre_return_not_ready" in warning_set:
        warnings.append(
            {
                "source": "ui_pre_return_audit",
                "check": "ui_pre_return_not_ready",
                "severity": "high",
                "message": "The advisory pre-return review still sees unresolved blockers for a strong UI-ready claim.",
                "evidence": [item.get("id", "unknown_blocker") for item in review.get("blockers", [])[:4]],
            }
        )
    return warnings


def _build_design_quality_warnings(design_report: Optional[Dict[str, Any]]) -> List[Dict[str, Any]]:
    if not isinstance(design_report, dict):
        return []
    review = design_report.get("design_quality_review")
    if not isinstance(review, dict):
        return []

    warnings: List[Dict[str, Any]] = []
    detected = set(review.get("detected_risks", []))

    if review.get("status") == "not_ready":
        warnings.append(
            {
                "source": "design_quality_enforcement",
                "check": "design_quality_not_ready",
                "severity": "high",
                "message": "The design may be functionally coherent, but Atlas still considers its visual quality too weak for a ready claim.",
                "evidence": list(review.get("detected_risks", []))[:4],
            }
        )
    if detected & {"weak_color_system", "typography_without_intent"}:
        warnings.append(
            {
                "source": "design_quality_enforcement",
                "check": "visual_system_weak",
                "severity": "high",
                "message": "The current surface still lacks a strong enough visual system for confident handoff.",
                "evidence": sorted(detected & {"weak_color_system", "typography_without_intent", "border_weight_excessive", "shadow_style_heavy"})[:4],
            }
        )
    if detected & {"weak_visual_hierarchy", "poor_spacing", "excessive_horizontal_spread"}:
        warnings.append(
            {
                "source": "design_quality_enforcement",
                "check": "hierarchy_weak",
                "severity": "high",
                "message": "The current surface still needs stronger hierarchy and spacing before Atlas should treat it as visually ready.",
                "evidence": sorted(detected & {"weak_visual_hierarchy", "poor_spacing", "excessive_horizontal_spread"})[:4],
            }
        )
    if detected & {"amateur_internal_tool_look", "wireframe_look", "generic_dashboard_pattern"}:
        warnings.append(
            {
                "source": "design_quality_enforcement",
                "check": "amateur_ui_risk",
                "severity": "high",
                "message": "The current UI still risks reading as an amateur or templated internal tool.",
                "evidence": sorted(detected & {"amateur_internal_tool_look", "wireframe_look", "generic_dashboard_pattern"})[:4],
            }
        )
    if "brutalism_misapplied" in detected:
        warnings.append(
            {
                "source": "design_quality_enforcement",
                "check": "brutalism_misapplied",
                "severity": "high",
                "message": "The current brutalist moves still read as under-refined rather than intentional.",
                "evidence": ["brutalism_misapplied"],
            }
        )
    if detected & {"border_weight_excessive", "shadow_style_heavy"}:
        warnings.append(
            {
                "source": "design_quality_enforcement",
                "check": "excessive_visual_weight",
                "severity": "high",
                "message": "Heavy borders or shadows are still dominating the interface and dragging perceived quality down.",
                "evidence": sorted(detected & {"border_weight_excessive", "shadow_style_heavy"})[:4],
            }
        )
    return warnings


def _build_frontend_auto_audit_warnings(review: Optional[Dict[str, Any]]) -> List[Dict[str, Any]]:
    if not isinstance(review, dict):
        return [
            {
                "source": "frontend_auto_audit_rules",
                "check": "frontend_auto_audit_missing",
                "severity": "high",
                "message": "Frontend auto-audit posture is missing, so Atlas has not checked whether its local handoff guardrails are complete.",
                "evidence": ["frontend_auto_audit_missing"],
            }
        ]
    warnings: List[Dict[str, Any]] = []
    if review.get("status") == "needs_improvement":
        warnings.append(
            {
                "source": "frontend_auto_audit_rules",
                "check": "frontend_auto_audit_not_ready",
                "severity": "high",
                "message": "Local frontend guardrails are still incomplete for a strong handoff claim.",
                "evidence": list(review.get("missing_guardrails", []))[:4],
            }
        )
    if review.get("evidence_gaps"):
        warnings.append(
            {
                "source": "frontend_auto_audit_rules",
                "check": "frontend_auto_audit_missing_evidence",
                "severity": "high",
                "message": "The local frontend auto-audit still lacks explicit evidence expectations.",
                "evidence": list(review.get("evidence_gaps", []))[:4],
            }
        )
    return warnings


def _build_error_learning_warnings(review: Optional[Dict[str, Any]]) -> List[Dict[str, Any]]:
    if not isinstance(review, dict):
        return []
    warnings: List[Dict[str, Any]] = []
    for item in list(review.get("blockers", [])) + list(review.get("warnings", [])):
        if not isinstance(item, dict):
            continue
        warnings.append(
            {
                "source": "atlas_error_learning_review",
                "check": item.get("check", "error_learning_warning"),
                "severity": item.get("severity", "medium"),
                "message": item.get("message", "Atlas learned-risk warning detected."),
                "evidence": list(item.get("evidence", []))[:4],
            }
        )
    return warnings


def _build_evidence_collector_warnings(review: Optional[Dict[str, Any]]) -> List[Dict[str, Any]]:
    review = review or {}
    warnings: List[Dict[str, Any]] = []
    readiness_state = str(review.get("readiness_state", "")).strip()
    task_type = str(review.get("task_type", "")).strip() or "unknown"
    missing_evidence = list(review.get("missing_evidence", []))
    blocking_gaps = list(review.get("blocking_gaps", []))
    advisory_gaps = list(review.get("advisory_gaps", []))

    if readiness_state == "evidence_missing":
        warnings.append(
            {
                "source": "evidence_collector_readiness",
                "check": "evidence_collector_missing",
                "severity": "medium",
                "message": "Atlas still lacks the minimum evidence baseline for this task type.",
                "evidence": [task_type, *missing_evidence[:3]],
            }
        )
    elif readiness_state == "evidence_partial":
        warnings.append(
            {
                "source": "evidence_collector_readiness",
                "check": "evidence_collector_partial",
                "severity": "medium" if not blocking_gaps else "high",
                "message": "Atlas has some evidence, but not enough for a strong PASS claim yet.",
                "evidence": [task_type, *(blocking_gaps[:2] or advisory_gaps[:2])],
            }
        )

    if task_type == "frontend_ui_landing" and (
        "screenshot_desktop" in missing_evidence or "screenshot_mobile" in missing_evidence
    ):
        warnings.append(
            {
                "source": "evidence_collector_readiness",
                "check": "evidence_collector_frontend_visual_gap",
                "severity": "medium",
                "message": "Frontend evidence still lacks desktop/mobile screenshot proof, so Atlas should avoid a strong visual PASS.",
                "evidence": [item for item in ("screenshot_desktop", "screenshot_mobile") if item in missing_evidence],
            }
        )

    if task_type == "high_risk_decision" and blocking_gaps:
        warnings.append(
            {
                "source": "evidence_collector_readiness",
                "check": "evidence_collector_high_risk_gap",
                "severity": "high",
                "message": "A high-risk decision is missing proof that should exist before Atlas treats it as strong-ready.",
                "evidence": blocking_gaps[:3],
            }
        )

    return warnings


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

    design_report = source_reports["design_intelligence_audit"].get("report") or {}
    visual_intent_from_intent = (
        (source_reports["project_intent_analyzer"]["report"] or {}).get("visual_intent_contract")
        if source_reports["project_intent_analyzer"]["status"] == "ok"
        else None
    )
    visual_intent_from_design = design_report.get("visual_intent_contract_review")
    brand_profile_review = design_report.get("brand_profile_review")
    ui_pre_return_review = design_report.get("ui_pre_return_review")
    design_quality_review = design_report.get("design_quality_review")
    if not isinstance(design_quality_review, dict):
        design_quality_review = audit_design_quality(
            {
                "project_type": str((visual_intent_from_design or {}).get("contract", {}).get("project_type", "frontend_app")).strip() or "frontend_app",
                "design_checks": design_report.get("checks", []),
                "visual_intent_contract_review": visual_intent_from_design,
                "brand_profile_review": brand_profile_review,
                "ui_pre_return_review": ui_pre_return_review,
            },
            root=root,
        )

    source_reports["intent_clarifier_contract"] = _run_intent_clarifier_contract(
        root=root,
        project=project,
        intent_report=source_reports["project_intent_analyzer"]["report"] if source_reports["project_intent_analyzer"]["status"] == "ok" else {},
    )
    source_reports["brand_json_v2_readiness"] = _run_brand_json_v2_readiness(
        root=root,
        project=project,
        project_type=((source_reports["project_intent_analyzer"]["report"] or {}).get("project_type") if source_reports["project_intent_analyzer"]["status"] == "ok" else None),
        visual_intent_contract=visual_intent_from_design or visual_intent_from_intent,
        brand_profile_review=brand_profile_review,
    )
    source_reports["frontend_auto_audit_rules"] = _run_frontend_auto_audit_rules(
        root=root,
        payload={
            "project_type": ((source_reports["project_intent_analyzer"]["report"] or {}).get("project_type") if source_reports["project_intent_analyzer"]["status"] == "ok" else None) or "unknown",
            "intent_clarifier_contract": source_reports["intent_clarifier_contract"]["report"] or {},
            "visual_intent_contract_review": visual_intent_from_design or visual_intent_from_intent or {},
            "brand_json_v2_readiness": source_reports["brand_json_v2_readiness"]["report"] or {},
            "brand_profile_review": brand_profile_review or {},
            "ui_pre_return_review": ui_pre_return_review or {},
            "design_quality_review": design_quality_review or {},
            "design_checks": design_report.get("checks", []),
        },
    )
    source_reports["playwright_visual_qa_readiness"] = _run_playwright_visual_qa_readiness(root)
    source_reports["codex_runtime_compatibility_check"] = _run_codex_runtime_compatibility(root)
    source_reports["atlas_memory_readiness"] = _run_atlas_memory_readiness(root)
    source_reports["atlas_error_learning_review"] = _run_atlas_error_learning_review(
        root=root,
        payload={
            "project_type": ((source_reports["project_intent_analyzer"]["report"] or {}).get("project_type") if source_reports["project_intent_analyzer"]["status"] == "ok" else None) or "unknown",
            "design_report": design_report,
            "design_checks": design_report.get("checks", []),
            "ui_pre_return_review": ui_pre_return_review or {},
            "frontend_auto_audit_review": source_reports["frontend_auto_audit_rules"]["report"] or {},
            "visual_qa_readiness_posture": source_reports["playwright_visual_qa_readiness"]["report"] or {},
            "requires_visual_evidence": bool((ui_pre_return_review or {}).get("missing_evidence")),
            "manual_visual_review_recorded": False,
            "certify_report": source_reports["certify-project"].get("report") or {},
            "integration_surfaces": [
                {
                    "name": "creative_pipeline_readiness",
                    "claim_active": False,
                    "declared_state": "readiness",
                    "actual_state": "readiness",
                    "tests_present": True,
                },
                {
                    "name": "component_inspiration_readiness",
                    "claim_active": False,
                    "declared_state": "watchlist",
                    "actual_state": "watchlist",
                    "tests_present": True,
                },
                {
                    "name": "playwright_visual_qa_readiness",
                    "claim_active": False,
                    "declared_state": "watchlist",
                    "actual_state": "watchlist" if not bool((source_reports["playwright_visual_qa_readiness"]["report"] or {}).get("safe_to_run")) else "readiness",
                    "tests_present": True,
                },
            ],
        },
    )
    source_reports["evidence_collector_readiness"] = _run_evidence_collector_readiness(
        root=root,
        payload={
            "project_type": ((source_reports["project_intent_analyzer"]["report"] or {}).get("project_type") if source_reports["project_intent_analyzer"]["status"] == "ok" else None) or "unknown",
            "provided_evidence": [
                *(
                    ["responsive_check"]
                    if any(
                        str((item or {}).get("id", "")).strip() == "responsive_baseline"
                        for item in design_report.get("checks", [])
                        if isinstance(item, dict)
                    )
                    else []
                ),
                *(
                    ["font_loading_check"]
                    if any(
                        str((item or {}).get("id", "")).strip() == "typography_coherence"
                        for item in design_report.get("checks", [])
                        if isinstance(item, dict)
                    )
                    else []
                ),
                *(
                    ["link_cta_check"]
                    if any(
                        str((item or {}).get("id", "")).strip() in {"cta_clarity", "cta_integrity"}
                        for item in design_report.get("checks", [])
                        if isinstance(item, dict)
                    )
                    else []
                ),
                *(
                    ["accessibility_basics", "tap_target_check"]
                    if isinstance(ui_pre_return_review, dict) and ui_pre_return_review
                    else []
                ),
            ],
        },
    )
    inferred_complexity = (
        str((source_reports["project_intent_analyzer"]["report"] or {}).get("complexity", "low")).strip().lower()
        if source_reports["project_intent_analyzer"]["status"] == "ok"
        else "low"
    )
    project_type_for_change_proposal = (
        ((source_reports["project_intent_analyzer"]["report"] or {}).get("project_type") if source_reports["project_intent_analyzer"]["status"] == "ok" else None)
        or "unknown"
    )
    source_reports["change_proposal_readiness"] = _run_change_proposal_readiness(
        root=root,
        payload={
            "project_type": project_type_for_change_proposal,
            "change_size": {
                "high": "large",
                "medium": "medium",
                "low": "small",
            }.get(inferred_complexity, "small"),
            "risk_level": (
                ((source_reports["project_intent_analyzer"]["report"] or {}).get("risk_level") if source_reports["project_intent_analyzer"]["status"] == "ok" else None)
                or "low"
            ),
            "complexity": inferred_complexity,
            "is_architecture_change": inferred_complexity in {"medium", "high"}
            and project_type_for_change_proposal in {"fullstack", "ai_agent_system"},
            "is_governance_change": False,
            "is_contract_change": bool(source_reports["intent_clarifier_contract"].get("report")),
        },
    )

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

    visual_intent_warning = _build_visual_intent_warning(
        source_reports["project_intent_analyzer"]["report"] if source_reports["project_intent_analyzer"]["status"] == "ok" else None
    )
    if visual_intent_warning:
        _unique_priority_append(warnings, visual_intent_warning, seen)
    for item in _build_intent_clarifier_warnings(source_reports["intent_clarifier_contract"].get("report")):
        _unique_priority_append(candidate_priorities, item, candidate_seen)
        _unique_priority_append(warnings, item, seen)
    for item in _build_brand_profile_warnings(source_reports["design_intelligence_audit"].get("report")):
        _unique_priority_append(candidate_priorities, item, candidate_seen)
        _unique_priority_append(warnings, item, seen)
    for item in _build_brand_json_v2_warnings(source_reports["brand_json_v2_readiness"].get("report")):
        _unique_priority_append(candidate_priorities, item, candidate_seen)
        _unique_priority_append(warnings, item, seen)
    for item in _build_ui_pre_return_warnings(source_reports["design_intelligence_audit"].get("report")):
        _unique_priority_append(candidate_priorities, item, candidate_seen)
        _unique_priority_append(warnings, item, seen)
    for item in _build_design_quality_warnings(source_reports["design_intelligence_audit"].get("report")):
        _unique_priority_append(candidate_priorities, item, candidate_seen)
        _unique_priority_append(warnings, item, seen)
    for item in _build_frontend_auto_audit_warnings(source_reports["frontend_auto_audit_rules"].get("report")):
        _unique_priority_append(candidate_priorities, item, candidate_seen)
        _unique_priority_append(warnings, item, seen)
    for item in _build_error_learning_warnings(source_reports["atlas_error_learning_review"].get("report")):
        _unique_priority_append(candidate_priorities, item, candidate_seen)
        _unique_priority_append(warnings, item, seen)
    for item in _build_evidence_collector_warnings(source_reports["evidence_collector_readiness"].get("report")):
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
    intent_clarifier_review = source_reports["intent_clarifier_contract"].get("report") or {}
    brand_json_v2_review = source_reports["brand_json_v2_readiness"].get("report") or {}
    frontend_auto_audit_review = source_reports["frontend_auto_audit_rules"].get("report") or {}
    evidence_collector_review = source_reports["evidence_collector_readiness"].get("report") or {}
    if overall_status == "ready":
        if str(intent_clarifier_review.get("status", "")).strip() not in {"", "ready", "skipped"}:
            overall_status = "needs_improvement"
        if str(brand_json_v2_review.get("status", "")).strip() not in {"", "ready", "skipped"}:
            overall_status = "needs_improvement"
        if str(frontend_auto_audit_review.get("status", "")).strip() == "needs_improvement":
            overall_status = "needs_improvement"
        if str((source_reports["atlas_error_learning_review"].get("report") or {}).get("status", "")).strip() == "needs_improvement":
            overall_status = "needs_improvement"
        if not bool(evidence_collector_review.get("can_claim_ready", False)) and str(evidence_collector_review.get("readiness_state", "")).strip() in {"evidence_missing", "evidence_partial"}:
            overall_status = "needs_improvement"
    confidence_level = _derive_confidence_level(source_reports)
    if confidence_level == "high" and overall_status == "needs_improvement":
        confidence_level = "medium"
    evidence_summary = _build_evidence_summary(source_reports, blockers, warnings)
    summary_for_human = _build_summary_for_human(overall_status, confidence_level, blockers, top_priorities)
    recommended_next_action = _build_recommended_next_action(overall_status, blockers, top_priorities)
    landing_score = design_report.get("landing_score")
    public_readiness = design_report.get("public_readiness", "needs_improvement")
    external_tool_posture = _derive_external_tool_posture(
        source_reports=source_reports,
        blockers=blockers,
        warnings=warnings,
    )
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
    source_reports["skill_improvement_review"] = _run_skill_improvement_review(root)
    source_reports["creative_pipeline_readiness"] = _run_creative_pipeline_readiness(root)
    source_reports["component_inspiration_readiness"] = _run_component_inspiration_readiness(root)
    source_reports["feedback_analyzer"] = feedback_report
    source_reports["model_router"] = _run_model_route(
        root,
        project,
        phase_report=phase_data,
        intent_report=source_reports["project_intent_analyzer"]["report"] if source_reports["project_intent_analyzer"]["status"] == "ok" else {},
    )
    source_reports["model_cost_control_readiness"] = _run_model_cost_control(
        root=root,
        intent_report=source_reports["project_intent_analyzer"]["report"] if source_reports["project_intent_analyzer"]["status"] == "ok" else {},
        current_phase=current_phase,
        top_priorities=top_priorities,
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
        "visual_intent_posture": {
            "contract_status": (visual_intent_from_intent or {}).get("status"),
            "design_review_status": (visual_intent_from_design or {}).get("status"),
            "required_fields": (visual_intent_from_intent or {}).get("required_fields", []),
            "missing_fields": sorted(
                {
                    *list((visual_intent_from_intent or {}).get("missing_fields", [])),
                    *list((visual_intent_from_design or {}).get("missing_fields", [])),
                }
            ),
            "fields": (visual_intent_from_intent or {}).get("contract"),
            "next_action": (visual_intent_from_intent or {}).get("next_action")
            or (visual_intent_from_design or {}).get("next_action"),
            "advisory_only": True,
        },
        "intent_clarifier_posture": {
            "status": (source_reports["intent_clarifier_contract"]["report"] or {}).get("status"),
            "requires_contract": bool((source_reports["intent_clarifier_contract"]["report"] or {}).get("requires_contract")),
            "required_questions": (source_reports["intent_clarifier_contract"]["report"] or {}).get("required_questions", []),
            "answered_questions": (source_reports["intent_clarifier_contract"]["report"] or {}).get("answered_questions", []),
            "missing_questions": (source_reports["intent_clarifier_contract"]["report"] or {}).get("missing_questions", []),
            "weak_answers": (source_reports["intent_clarifier_contract"]["report"] or {}).get("weak_answers", []),
            "must_block_strong_ready": bool((source_reports["intent_clarifier_contract"]["report"] or {}).get("must_block_strong_ready")),
            "requires_human_clarification": bool((source_reports["intent_clarifier_contract"]["report"] or {}).get("requires_human_clarification")),
            "next_action": (source_reports["intent_clarifier_contract"]["report"] or {}).get("next_action"),
            "why": (source_reports["intent_clarifier_contract"]["report"] or {}).get("why"),
            "advisory_only": bool((source_reports["intent_clarifier_contract"]["report"] or {}).get("advisory_only", True)),
        },
        "brand_json_v2_posture": {
            "status": (source_reports["brand_json_v2_readiness"]["report"] or {}).get("status"),
            "requires_brand_json_v2": bool((source_reports["brand_json_v2_readiness"]["report"] or {}).get("requires_brand_json_v2", True)),
            "explicit_profile_present": bool((source_reports["brand_json_v2_readiness"]["report"] or {}).get("explicit_profile_present")),
            "missing_sections": (source_reports["brand_json_v2_readiness"]["report"] or {}).get("missing_sections", []),
            "weak_sections": (source_reports["brand_json_v2_readiness"]["report"] or {}).get("weak_sections", []),
            "anti_generic_risks": (source_reports["brand_json_v2_readiness"]["report"] or {}).get("anti_generic_risks", []),
            "derivative_risks": (source_reports["brand_json_v2_readiness"]["report"] or {}).get("derivative_risks", []),
            "accessibility_risks": (source_reports["brand_json_v2_readiness"]["report"] or {}).get("accessibility_risks", []),
            "export_candidate": bool((source_reports["brand_json_v2_readiness"]["report"] or {}).get("export_candidate")),
            "evidence_expectations": (source_reports["brand_json_v2_readiness"]["report"] or {}).get("evidence_expectations", []),
            "next_action": (source_reports["brand_json_v2_readiness"]["report"] or {}).get("next_action"),
            "why": (source_reports["brand_json_v2_readiness"]["report"] or {}).get("why"),
            "advisory_only": bool((source_reports["brand_json_v2_readiness"]["report"] or {}).get("advisory_only", True)),
        },
        "brand_profile_posture": {
            "profile_status": (brand_profile_review or {}).get("status"),
            "profile_source": (brand_profile_review or {}).get("profile_source"),
            "explicit_profile_present": bool((brand_profile_review or {}).get("explicit_profile_present")),
            "required_fields": (brand_profile_review or {}).get("required_fields", []),
            "missing_fields": (brand_profile_review or {}).get("missing_fields", []),
            "weak_fields": (brand_profile_review or {}).get("weak_fields", []),
            "invalid_fields": (brand_profile_review or {}).get("invalid_fields", []),
            "anti_generic_risks": (brand_profile_review or {}).get("anti_generic_risks", []),
            "derivative_risks": (brand_profile_review or {}).get("derivative_risks", []),
            "accessibility_risks": (brand_profile_review or {}).get("accessibility_risks", []),
            "fields": (brand_profile_review or {}).get("profile"),
            "next_action": (brand_profile_review or {}).get("next_action"),
            "advisory_only": True,
        },
        "ui_pre_return_posture": {
            "status": (ui_pre_return_review or {}).get("status"),
            "pass_ready": bool((ui_pre_return_review or {}).get("pass_ready")),
            "blockers": (ui_pre_return_review or {}).get("blockers", []),
            "warnings": (ui_pre_return_review or {}).get("warnings", []),
            "missing_evidence": (ui_pre_return_review or {}).get("missing_evidence", []),
            "anti_generic_risks": (ui_pre_return_review or {}).get("anti_generic_risks", []),
            "brand_alignment_risks": (ui_pre_return_review or {}).get("brand_alignment_risks", []),
            "accessibility_risks": (ui_pre_return_review or {}).get("accessibility_risks", []),
            "responsive_risks": (ui_pre_return_review or {}).get("responsive_risks", []),
            "recommended_fixes": (ui_pre_return_review or {}).get("recommended_fixes", []),
            "requires_human_clarification": bool((ui_pre_return_review or {}).get("requires_human_clarification")),
            "requires_decision_council": bool((ui_pre_return_review or {}).get("requires_decision_council")),
            "why": (ui_pre_return_review or {}).get("why"),
            "advisory_only": True,
        },
        "frontend_auto_audit_posture": {
            "status": (source_reports["frontend_auto_audit_rules"]["report"] or {}).get("status"),
            "can_support_pre_return": bool((source_reports["frontend_auto_audit_rules"]["report"] or {}).get("can_support_pre_return")),
            "blockers": (source_reports["frontend_auto_audit_rules"]["report"] or {}).get("blockers", []),
            "warnings": (source_reports["frontend_auto_audit_rules"]["report"] or {}).get("warnings", []),
            "ready_guardrails": (source_reports["frontend_auto_audit_rules"]["report"] or {}).get("ready_guardrails", []),
            "missing_guardrails": (source_reports["frontend_auto_audit_rules"]["report"] or {}).get("missing_guardrails", []),
            "evidence_gaps": (source_reports["frontend_auto_audit_rules"]["report"] or {}).get("evidence_gaps", []),
            "watchlist_dependencies": (source_reports["frontend_auto_audit_rules"]["report"] or {}).get("watchlist_dependencies", []),
            "recommended_next_action": (source_reports["frontend_auto_audit_rules"]["report"] or {}).get("recommended_next_action"),
            "why": (source_reports["frontend_auto_audit_rules"]["report"] or {}).get("why"),
            "advisory_only": bool((source_reports["frontend_auto_audit_rules"]["report"] or {}).get("advisory_only", True)),
        },
        "design_quality_posture": {
            "status": (design_quality_review or {}).get("status"),
            "ready_for_handoff": bool((design_quality_review or {}).get("ready_for_handoff")),
            "blockers": (design_quality_review or {}).get("blockers", []),
            "warnings": (design_quality_review or {}).get("warnings", []),
            "visual_quality_score": (design_quality_review or {}).get("visual_quality_score"),
            "detected_risks": (design_quality_review or {}).get("detected_risks", []),
            "recommended_fixes": (design_quality_review or {}).get("recommended_fixes", []),
            "required_redesign_level": (design_quality_review or {}).get("required_redesign_level"),
            "why": (design_quality_review or {}).get("why"),
            "advisory_only": bool((design_quality_review or {}).get("advisory_only", True)),
        },
        "model_cost_control_posture": {
            "status": (source_reports["model_cost_control_readiness"]["report"] or {}).get("status"),
            "recommended_model_tier": (source_reports["model_cost_control_readiness"]["report"] or {}).get("recommended_model_tier"),
            "cost_saver_strategy": (source_reports["model_cost_control_readiness"]["report"] or {}).get("cost_saver_strategy"),
            "context_reduction_strategy": (source_reports["model_cost_control_readiness"]["report"] or {}).get("context_reduction_strategy"),
            "split_task_recommended": bool((source_reports["model_cost_control_readiness"]["report"] or {}).get("split_task_recommended")),
            "requires_user_confirmation": bool((source_reports["model_cost_control_readiness"]["report"] or {}).get("requires_user_confirmation")),
            "risks": (source_reports["model_cost_control_readiness"]["report"] or {}).get("risks", []),
            "manual_action_required": (source_reports["model_cost_control_readiness"]["report"] or {}).get("manual_action_required"),
            "why": (source_reports["model_cost_control_readiness"]["report"] or {}).get("why"),
            "advisory_only": bool((source_reports["model_cost_control_readiness"]["report"] or {}).get("advisory_only", True)),
        },
        "error_learning_posture": {
            "status": (source_reports["atlas_error_learning_review"]["report"] or {}).get("status"),
            "blockers": (source_reports["atlas_error_learning_review"]["report"] or {}).get("blockers", []),
            "warnings": (source_reports["atlas_error_learning_review"]["report"] or {}).get("warnings", []),
            "triggered_signals": (source_reports["atlas_error_learning_review"]["report"] or {}).get("triggered_signals", []),
            "warning_codes": (source_reports["atlas_error_learning_review"]["report"] or {}).get("warning_codes", []),
            "requires_human_clarification": bool((source_reports["atlas_error_learning_review"]["report"] or {}).get("requires_human_clarification")),
            "requires_decision_council": bool((source_reports["atlas_error_learning_review"]["report"] or {}).get("requires_decision_council")),
            "recommended_next_action": (source_reports["atlas_error_learning_review"]["report"] or {}).get("recommended_next_action"),
            "why": (source_reports["atlas_error_learning_review"]["report"] or {}).get("why"),
            "advisory_only": bool((source_reports["atlas_error_learning_review"]["report"] or {}).get("advisory_only", True)),
        },
        "model_routing": source_reports["model_router"]["report"] if source_reports["model_router"]["status"] == "ok" else None,
        "external_tool_posture": external_tool_posture,
        "prompt_guidance": source_reports["prompt_builder"]["report"] if source_reports["prompt_builder"]["status"] == "ok" else None,
        "skill_creation_signal": source_reports["skill_evaluator"]["report"] if source_reports["skill_evaluator"]["status"] == "ok" else None,
        "skill_lifecycle_posture": {
            "recommended_state": (source_reports["skill_evaluator"]["report"] or {}).get("recommended_state"),
            "lifecycle_recommendation": (source_reports["skill_evaluator"]["report"] or {}).get("lifecycle_recommendation"),
            "promotion_blockers": (source_reports["skill_evaluator"]["report"] or {}).get("promotion_blockers", []),
            "requires_human_approval": (source_reports["skill_evaluator"]["report"] or {}).get("requires_human_approval"),
            "requires_decision_council": (source_reports["skill_evaluator"]["report"] or {}).get("requires_decision_council"),
        },
        "skill_improvement_posture": {
            "status": (source_reports["skill_improvement_review"]["report"] or {}).get("status"),
            "reviewed_skills": (source_reports["skill_improvement_review"]["report"] or {}).get("reviewed_skills", []),
            "weak_skills": (source_reports["skill_improvement_review"]["report"] or {}).get("weak_skills", []),
            "duplicate_risks": (source_reports["skill_improvement_review"]["report"] or {}).get("duplicate_risks", []),
            "lifecycle_recommendations": (source_reports["skill_improvement_review"]["report"] or {}).get("lifecycle_recommendations", []),
            "candidate_opportunities": (source_reports["skill_improvement_review"]["report"] or {}).get("candidate_opportunities", []),
            "blocked_candidates": (source_reports["skill_improvement_review"]["report"] or {}).get("blocked_candidates", []),
            "requires_human_approval": bool((source_reports["skill_improvement_review"]["report"] or {}).get("requires_human_approval")),
            "requires_decision_council": bool((source_reports["skill_improvement_review"]["report"] or {}).get("requires_decision_council")),
            "recommended_next_actions": (source_reports["skill_improvement_review"]["report"] or {}).get("recommended_next_actions", []),
            "why": (source_reports["skill_improvement_review"]["report"] or {}).get("why"),
            "advisory_only": bool((source_reports["skill_improvement_review"]["report"] or {}).get("advisory_only", True)),
        },
        "creative_pipeline_posture": {
            "status": (source_reports["creative_pipeline_readiness"]["report"] or {}).get("status"),
            "available_services": (source_reports["creative_pipeline_readiness"]["report"] or {}).get("available_services", []),
            "missing_services": (source_reports["creative_pipeline_readiness"]["report"] or {}).get("missing_services", []),
            "safe_to_use_profiles": (source_reports["creative_pipeline_readiness"]["report"] or {}).get("safe_to_use_profiles", []),
            "watchlist_profiles": (source_reports["creative_pipeline_readiness"]["report"] or {}).get("watchlist_profiles", []),
            "blocked_profiles": (source_reports["creative_pipeline_readiness"]["report"] or {}).get("blocked_profiles", []),
            "required_manual_steps": (source_reports["creative_pipeline_readiness"]["report"] or {}).get("required_manual_steps", []),
            "risks": (source_reports["creative_pipeline_readiness"]["report"] or {}).get("risks", []),
            "requires_human_approval": bool((source_reports["creative_pipeline_readiness"]["report"] or {}).get("requires_human_approval")),
            "requires_decision_council": bool((source_reports["creative_pipeline_readiness"]["report"] or {}).get("requires_decision_council")),
            "recommended_next_action": (source_reports["creative_pipeline_readiness"]["report"] or {}).get("recommended_next_action"),
            "why": (source_reports["creative_pipeline_readiness"]["report"] or {}).get("why"),
            "advisory_only": bool((source_reports["creative_pipeline_readiness"]["report"] or {}).get("advisory_only", True)),
        },
        "component_inspiration_posture": {
            "status": (source_reports["component_inspiration_readiness"]["report"] or {}).get("status"),
            "available_services": (source_reports["component_inspiration_readiness"]["report"] or {}).get("available_services", []),
            "missing_services": (source_reports["component_inspiration_readiness"]["report"] or {}).get("missing_services", []),
            "safe_to_use_profiles": (source_reports["component_inspiration_readiness"]["report"] or {}).get("safe_to_use_profiles", []),
            "watchlist_profiles": (source_reports["component_inspiration_readiness"]["report"] or {}).get("watchlist_profiles", []),
            "blocked_profiles": (source_reports["component_inspiration_readiness"]["report"] or {}).get("blocked_profiles", []),
            "required_manual_steps": (source_reports["component_inspiration_readiness"]["report"] or {}).get("required_manual_steps", []),
            "risks": (source_reports["component_inspiration_readiness"]["report"] or {}).get("risks", []),
            "requires_human_approval": bool((source_reports["component_inspiration_readiness"]["report"] or {}).get("requires_human_approval")),
            "requires_decision_council": bool((source_reports["component_inspiration_readiness"]["report"] or {}).get("requires_decision_council")),
            "recommended_next_action": (source_reports["component_inspiration_readiness"]["report"] or {}).get("recommended_next_action"),
            "why": (source_reports["component_inspiration_readiness"]["report"] or {}).get("why"),
            "advisory_only": bool((source_reports["component_inspiration_readiness"]["report"] or {}).get("advisory_only", True)),
        },
        "visual_qa_readiness_posture": {
            "status": (source_reports["playwright_visual_qa_readiness"]["report"] or {}).get("status"),
            "playwright_available": bool((source_reports["playwright_visual_qa_readiness"]["report"] or {}).get("playwright_available")),
            "browsers_available": bool((source_reports["playwright_visual_qa_readiness"]["report"] or {}).get("browsers_available")),
            "safe_to_run": bool((source_reports["playwright_visual_qa_readiness"]["report"] or {}).get("safe_to_run")),
            "blocked_profiles": (source_reports["playwright_visual_qa_readiness"]["report"] or {}).get("blocked_profiles", []),
            "watchlist_profiles": (source_reports["playwright_visual_qa_readiness"]["report"] or {}).get("watchlist_profiles", []),
            "required_manual_steps": (source_reports["playwright_visual_qa_readiness"]["report"] or {}).get("required_manual_steps", []),
            "recommended_next_action": (source_reports["playwright_visual_qa_readiness"]["report"] or {}).get("recommended_next_action"),
            "risks": (source_reports["playwright_visual_qa_readiness"]["report"] or {}).get("risks", []),
            "requires_human_approval": bool((source_reports["playwright_visual_qa_readiness"]["report"] or {}).get("requires_human_approval")),
            "requires_decision_council": bool((source_reports["playwright_visual_qa_readiness"]["report"] or {}).get("requires_decision_council")),
            "why": (source_reports["playwright_visual_qa_readiness"]["report"] or {}).get("why"),
            "advisory_only": bool((source_reports["playwright_visual_qa_readiness"]["report"] or {}).get("advisory_only", True)),
        },
        "codex_runtime_posture": {
            "status": (source_reports["codex_runtime_compatibility_check"]["report"] or {}).get("status"),
            "codex_cli_available": bool((source_reports["codex_runtime_compatibility_check"]["report"] or {}).get("codex_cli_available")),
            "codex_version": (source_reports["codex_runtime_compatibility_check"]["report"] or {}).get("codex_version"),
            "mcp_cli_functional": bool((source_reports["codex_runtime_compatibility_check"]["report"] or {}).get("mcp_cli_functional")),
            "configured_mcp_servers": (source_reports["codex_runtime_compatibility_check"]["report"] or {}).get("configured_mcp_servers", []),
            "runtime_model_visible": bool((source_reports["codex_runtime_compatibility_check"]["report"] or {}).get("runtime_model_visible")),
            "safe_to_use_with_atlas": bool((source_reports["codex_runtime_compatibility_check"]["report"] or {}).get("safe_to_use_with_atlas")),
            "limitations": (source_reports["codex_runtime_compatibility_check"]["report"] or {}).get("limitations", []),
            "manual_steps": (source_reports["codex_runtime_compatibility_check"]["report"] or {}).get("manual_steps", []),
            "why": (source_reports["codex_runtime_compatibility_check"]["report"] or {}).get("why"),
            "advisory_only": bool((source_reports["codex_runtime_compatibility_check"]["report"] or {}).get("advisory_only", True)),
        },
        "atlas_memory_posture": {
            "status": (source_reports["atlas_memory_readiness"]["report"] or {}).get("status"),
            "available_sources": (source_reports["atlas_memory_readiness"]["report"] or {}).get("available_sources", []),
            "missing_sources": (source_reports["atlas_memory_readiness"]["report"] or {}).get("missing_sources", []),
            "safe_to_use_profiles": (source_reports["atlas_memory_readiness"]["report"] or {}).get("safe_to_use_profiles", []),
            "watchlist_profiles": (source_reports["atlas_memory_readiness"]["report"] or {}).get("watchlist_profiles", []),
            "blocked_profiles": (source_reports["atlas_memory_readiness"]["report"] or {}).get("blocked_profiles", []),
            "required_manual_steps": (source_reports["atlas_memory_readiness"]["report"] or {}).get("required_manual_steps", []),
            "risks": (source_reports["atlas_memory_readiness"]["report"] or {}).get("risks", []),
            "requires_human_approval": bool((source_reports["atlas_memory_readiness"]["report"] or {}).get("requires_human_approval")),
            "requires_decision_council": bool((source_reports["atlas_memory_readiness"]["report"] or {}).get("requires_decision_council")),
            "recommended_next_action": (source_reports["atlas_memory_readiness"]["report"] or {}).get("recommended_next_action"),
            "why": (source_reports["atlas_memory_readiness"]["report"] or {}).get("why"),
            "advisory_only": bool((source_reports["atlas_memory_readiness"]["report"] or {}).get("advisory_only", True)),
        },
        "evidence_collector_posture": {
            "status": (source_reports["evidence_collector_readiness"]["report"] or {}).get("status"),
            "readiness_state": (source_reports["evidence_collector_readiness"]["report"] or {}).get("readiness_state"),
            "task_type": (source_reports["evidence_collector_readiness"]["report"] or {}).get("task_type"),
            "required_evidence": (source_reports["evidence_collector_readiness"]["report"] or {}).get("required_evidence", []),
            "provided_evidence": (source_reports["evidence_collector_readiness"]["report"] or {}).get("provided_evidence", []),
            "missing_evidence": (source_reports["evidence_collector_readiness"]["report"] or {}).get("missing_evidence", []),
            "blocking_gaps": (source_reports["evidence_collector_readiness"]["report"] or {}).get("blocking_gaps", []),
            "advisory_gaps": (source_reports["evidence_collector_readiness"]["report"] or {}).get("advisory_gaps", []),
            "can_claim_ready": bool((source_reports["evidence_collector_readiness"]["report"] or {}).get("can_claim_ready")),
            "can_claim_pass_with_caution": bool((source_reports["evidence_collector_readiness"]["report"] or {}).get("can_claim_pass_with_caution")),
            "manual_next_steps": (source_reports["evidence_collector_readiness"]["report"] or {}).get("manual_next_steps", []),
            "why": (source_reports["evidence_collector_readiness"]["report"] or {}).get("why"),
            "advisory_only": bool((source_reports["evidence_collector_readiness"]["report"] or {}).get("advisory_only", True)),
        },
        "change_proposal_posture": {
            "required": bool((source_reports["change_proposal_readiness"]["report"] or {}).get("required")),
            "status": (source_reports["change_proposal_readiness"]["report"] or {}).get("status"),
            "missing_artifacts": (source_reports["change_proposal_readiness"]["report"] or {}).get("missing_artifacts", []),
            "why": (source_reports["change_proposal_readiness"]["report"] or {}).get("why"),
            "advisory_only": bool((source_reports["change_proposal_readiness"]["report"] or {}).get("advisory_only", True)),
        },
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
