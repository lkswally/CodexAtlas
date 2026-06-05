from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Set


DEFAULT_ROOT = Path(__file__).resolve().parents[1]
RULES_PATH = Path("config/frontend_visual_execution_guard_rules.json")


def load_frontend_visual_execution_guard_rules(root: Path = DEFAULT_ROOT) -> Dict[str, Any]:
    return json.loads((root / RULES_PATH).read_text(encoding="utf-8-sig"))


def _normalize(value: Any) -> str:
    return re.sub(r"\s+", " ", str(value or "").strip().lower())


def _string_list(values: Any) -> List[str]:
    if not isinstance(values, list):
        return []
    result: List[str] = []
    for value in values:
        text = str(value or "").strip()
        if text:
            result.append(text)
    return result


def _dedupe(values: Iterable[str]) -> List[str]:
    seen: Set[str] = set()
    result: List[str] = []
    for value in values:
        text = str(value or "").strip()
        key = _normalize(text)
        if text and key not in seen:
            seen.add(key)
            result.append(text)
    return result


def _extract_contract(payload: Dict[str, Any]) -> Dict[str, Any]:
    direct = payload.get("visual_intent_contract")
    if isinstance(direct, dict):
        return direct.get("contract") if isinstance(direct.get("contract"), dict) else direct
    review = payload.get("visual_intent_contract_review")
    if isinstance(review, dict):
        contract = review.get("contract")
        if isinstance(contract, dict):
            return contract
        nested = review.get("fields")
        if isinstance(nested, dict):
            return nested
    return {}


def _has_visual_brief(payload: Dict[str, Any], rules: Dict[str, Any]) -> bool:
    contract = _extract_contract(payload)
    if not contract:
        return bool(payload.get("visual_brief_present"))
    required = [str(item).strip() for item in rules.get("visual_brief_required_fields", []) if str(item).strip()]
    present_count = sum(1 for field in required if str(contract.get(field, "")).strip())
    return present_count >= max(3, min(len(required), 5))


def _collect_evidence(payload: Dict[str, Any]) -> List[str]:
    evidence: List[str] = []
    evidence.extend(_string_list(payload.get("provided_evidence")))
    collector = payload.get("evidence_collector_posture")
    if isinstance(collector, dict):
        evidence.extend(_string_list(collector.get("provided_evidence")))
    visual_fidelity = payload.get("visual_fidelity_posture")
    if isinstance(visual_fidelity, dict):
        if visual_fidelity.get("screenshot_evidence_present"):
            evidence.append("browser_qa")
        if visual_fidelity.get("report_detected"):
            evidence.append("visual_fidelity_report")
        for viewport in _string_list(visual_fidelity.get("provided_viewports")):
            evidence.append(f"screenshot_{viewport}")
    if payload.get("browser_qa_present") or payload.get("browser_qa"):
        evidence.append("browser_qa")
    if payload.get("screenshot_evidence_present"):
        evidence.append("browser_qa")
    return _dedupe(evidence)


def _has_any_evidence(evidence: List[str], accepted: Iterable[str]) -> bool:
    normalized = {_normalize(item) for item in evidence}
    return any(_normalize(item) in normalized for item in accepted)


def _has_responsive_checkpoints(payload: Dict[str, Any], rules: Dict[str, Any], evidence: List[str]) -> bool:
    checkpoints = payload.get("responsive_checkpoints")
    if isinstance(checkpoints, list) and len([item for item in checkpoints if str(item).strip()]) >= 2:
        return True
    if payload.get("mobile_first_plan_present"):
        return True
    return _has_any_evidence(evidence, rules.get("responsive_evidence", []))


def _has_design_references(payload: Dict[str, Any], rules: Dict[str, Any], evidence: List[str]) -> bool:
    if payload.get("design_reference_justification") or payload.get("references_not_needed_reason"):
        return True
    references = payload.get("design_references")
    if isinstance(references, list) and any(str(item).strip() for item in references):
        return True
    return _has_any_evidence(evidence, rules.get("design_reference_evidence", []))


def _motion_detected(payload: Dict[str, Any], rules: Dict[str, Any]) -> bool:
    if payload.get("motion_requirements_detected") or payload.get("motion_requirements"):
        return True
    ui_posture = payload.get("ui_ux_design_system_posture")
    if isinstance(ui_posture, dict):
        if payload.get("treat_ui_motion_signals_as_requirements") and _string_list(ui_posture.get("motion_signals")):
            return True
        if payload.get("treat_recommended_motion_as_requirement") and str(ui_posture.get("recommended_motion", "")).strip():
            return True
    text = " ".join(
        str(part or "")
        for part in (
            payload.get("source_text"),
            payload.get("objective"),
            payload.get("notes"),
            payload.get("motion_notes"),
        )
    )
    normalized = _normalize(text)
    return any(_normalize(term) in normalized for term in rules.get("motion_terms", []))


def _motion_validated(payload: Dict[str, Any], rules: Dict[str, Any], evidence: List[str]) -> bool:
    if payload.get("motion_validated"):
        return True
    motion = payload.get("motion_validation")
    if isinstance(motion, dict):
        required_flags = ("asset_verified", "event_verified", "progress_verified", "fallback_verified")
        if all(bool(motion.get(flag)) for flag in required_flags):
            return True
    return _has_any_evidence(evidence, rules.get("motion_validation_evidence", []))


def _generic_template_risk(payload: Dict[str, Any], rules: Dict[str, Any]) -> str:
    explicit = _normalize(payload.get("generic_template_risk"))
    if explicit in {"low", "medium", "high"}:
        return explicit
    design_quality = payload.get("design_quality_review")
    risks: List[str] = []
    if isinstance(design_quality, dict):
        risks.extend(_string_list(design_quality.get("detected_risks")))
        risks.extend(str(item.get("check", "")) for item in design_quality.get("warnings", []) if isinstance(item, dict))
        risks.extend(str(item.get("check", "")) for item in design_quality.get("blockers", []) if isinstance(item, dict))
    ui_pre_return = payload.get("ui_pre_return_review")
    if isinstance(ui_pre_return, dict):
        risks.extend(_string_list(ui_pre_return.get("anti_generic_risks")))
    source_text = _normalize(" ".join([str(payload.get("source_text", "")), " ".join(risks)]))
    hits = [term for term in rules.get("generic_template_signals", []) if _normalize(term) in source_text]
    if len(hits) >= 2:
        return "high"
    if hits:
        return "medium"
    return "low"


def _visual_system_consistent(payload: Dict[str, Any], rules: Dict[str, Any]) -> bool:
    if payload.get("visual_system_consistent"):
        return True
    design_quality = payload.get("design_quality_review")
    if isinstance(design_quality, dict):
        if design_quality.get("ready_for_handoff"):
            return True
        status = _normalize(design_quality.get("status"))
        if status in {"ready", "ok"} and not design_quality.get("blockers"):
            return True
    checks = payload.get("visual_system_checks")
    if isinstance(checks, list):
        available = {_normalize(item) for item in checks}
        expected = {_normalize(item) for item in rules.get("visual_system_checks", [])}
        if expected and len(available & expected) >= 4:
            return True
    return False


def assess_frontend_visual_execution_guard(
    payload: Dict[str, Any],
    *,
    root: Path = DEFAULT_ROOT,
) -> Dict[str, Any]:
    rules = load_frontend_visual_execution_guard_rules(root)
    project_type = _normalize(payload.get("project_type"))
    frontend_types = {_normalize(item) for item in rules.get("frontend_project_types", [])}
    ui_changes_detected = bool(payload.get("ui_changes_detected", True))
    is_frontend = project_type in frontend_types or bool(payload.get("is_frontend"))

    if not is_frontend or not ui_changes_detected:
        return {
            "state": "ready",
            "applicable": False,
            "visual_brief_present": False,
            "mobile_first_plan_present": False,
            "design_references_present": False,
            "browser_qa_present": False,
            "responsive_checkpoints_present": False,
            "motion_requirements_detected": False,
            "motion_validated": False,
            "generic_template_risk": "low",
            "visual_system_consistent": False,
            "limitations_declared": bool(payload.get("limitations_declared")),
            "blocked_reasons": [],
            "required_next_steps": [],
            "why": "Frontend visual execution guard is not applicable for this project type or there are no UI changes.",
            "advisory_only": bool(rules.get("advisory_only", True)),
        }

    evidence = _collect_evidence(payload)
    visual_brief_present = _has_visual_brief(payload, rules)
    mobile_first_plan_present = _has_responsive_checkpoints(payload, rules, evidence)
    design_references_present = _has_design_references(payload, rules, evidence)
    browser_qa_present = _has_any_evidence(evidence, rules.get("browser_qa_evidence", []))
    responsive_checkpoints_present = mobile_first_plan_present
    motion_requirements_detected = _motion_detected(payload, rules)
    motion_validated = _motion_validated(payload, rules, evidence)
    generic_template_risk = _generic_template_risk(payload, rules)
    visual_system_consistent = _visual_system_consistent(payload, rules)
    limitations_declared = bool(payload.get("limitations_declared") or payload.get("browser_qa_blocked_reason"))
    claims_visual_ready = bool(payload.get("claims_visual_ready") or payload.get("claims_visual_ok"))

    blocked_reasons: List[str] = []
    required_next_steps: List[str] = []
    next_steps = rules.get("required_next_steps", {})

    if not visual_brief_present:
        blocked_reasons.append("missing_visual_brief")
        required_next_steps.append(str(next_steps.get("visual_brief")))
    if not mobile_first_plan_present:
        blocked_reasons.append("missing_mobile_first_checkpoints")
        required_next_steps.append(str(next_steps.get("mobile_first")))
    if not design_references_present and generic_template_risk in {"medium", "high"}:
        blocked_reasons.append("missing_design_references_or_justification")
        required_next_steps.append(str(next_steps.get("references")))
    if not browser_qa_present:
        blocked_reasons.append("missing_browser_or_screenshot_qa")
        required_next_steps.append(str(next_steps.get("browser_qa")))
    if motion_requirements_detected and not motion_validated:
        blocked_reasons.append("motion_or_scroll_or_video_unverified")
        required_next_steps.append(str(next_steps.get("motion")))
    if generic_template_risk == "high" and (not visual_brief_present or not design_references_present):
        blocked_reasons.append("generic_template_risk_without_brief_or_references")
        required_next_steps.append(str(next_steps.get("generic")))
    if not visual_system_consistent:
        blocked_reasons.append("visual_system_consistency_not_proven")

    if motion_requirements_detected and not motion_validated:
        state = "blocked_motion_unverified"
    elif generic_template_risk == "high" and (not visual_brief_present or not design_references_present):
        state = "blocked_generic_template_risk"
    elif claims_visual_ready and not browser_qa_present and not limitations_declared:
        state = "blocked_missing_visual_evidence"
    elif blocked_reasons:
        state = "needs_visual_review"
    else:
        state = "ready"

    if state == "ready":
        why = "Frontend visual execution has brief, references or justification, responsive checkpoints, browser evidence and visual-system consistency."
    elif state == "blocked_motion_unverified":
        why = "Motion, scroll or video behavior was requested, but Atlas has no validation evidence for the asset, event, progress calculation and fallback."
    elif state == "blocked_generic_template_risk":
        why = "The surface has high generic-template risk without enough visual intent or reference evidence to justify the direction."
    elif state == "blocked_missing_visual_evidence":
        why = "The handoff claims visual readiness, but browser or screenshot QA evidence is missing."
    else:
        why = "Build evidence is not enough for a visual-ready claim; Atlas needs browser, responsive and visual-system proof before closing frontend work."

    return {
        "state": state,
        "applicable": True,
        "visual_brief_present": visual_brief_present,
        "mobile_first_plan_present": mobile_first_plan_present,
        "design_references_present": design_references_present,
        "browser_qa_present": browser_qa_present,
        "responsive_checkpoints_present": responsive_checkpoints_present,
        "motion_requirements_detected": motion_requirements_detected,
        "motion_validated": motion_validated,
        "generic_template_risk": generic_template_risk,
        "visual_system_consistent": visual_system_consistent,
        "limitations_declared": limitations_declared,
        "blocked_reasons": _dedupe(blocked_reasons),
        "required_next_steps": _dedupe(step for step in required_next_steps if step),
        "evidence": evidence,
        "why": why,
        "advisory_only": bool(rules.get("advisory_only", True)),
    }


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(add_help=True)
    parser.add_argument("--payload", default="{}")
    args = parser.parse_args(argv)
    payload = json.loads(args.payload)
    result = assess_frontend_visual_execution_guard(payload, root=DEFAULT_ROOT)
    print(json.dumps({"frontend_visual_execution_posture": result}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
