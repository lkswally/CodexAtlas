from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Dict, List, Optional

try:
    from tools.design_quality_enforcement import audit_design_quality
except ModuleNotFoundError:
    from design_quality_enforcement import audit_design_quality

DEFAULT_ROOT = Path(__file__).resolve().parents[1]
RULES_PATH = Path("config/ui_pre_return_audit_rules.json")
UI_PROJECT_TYPES = {"frontend_app", "fullstack", "internal_tool"}


def load_ui_pre_return_rules(root: Path = DEFAULT_ROOT) -> Dict[str, Any]:
    return json.loads((root / RULES_PATH).read_text(encoding="utf-8-sig"))


def _dedupe_preserve_order(values: List[str]) -> List[str]:
    seen: set[str] = set()
    deduped: List[str] = []
    for value in values:
        normalized = value.strip().lower()
        if not normalized or normalized in seen:
            continue
        seen.add(normalized)
        deduped.append(value.strip())
    return deduped


def _index_checks(checks: List[Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:
    by_id: Dict[str, Dict[str, Any]] = {}
    for item in checks:
        if not isinstance(item, dict):
            continue
        check_id = str(item.get("id", "")).strip()
        if check_id:
            by_id[check_id] = item
    return by_id


def _check_result(
    check_id: str,
    status: str,
    severity: str,
    evidence: List[str],
    warning_code: Optional[str] = None,
    blocker: Optional[str] = None,
) -> Dict[str, Any]:
    result = {
        "id": check_id,
        "status": status,
        "severity": severity,
        "evidence": evidence[:4],
    }
    if warning_code:
        result["warning_code"] = warning_code
    if blocker:
        result["blocker"] = blocker
    return result


def audit_ui_pre_return(payload: Dict[str, Any], *, root: Path = DEFAULT_ROOT) -> Dict[str, Any]:
    rules = load_ui_pre_return_rules(root)
    project_type = str(payload.get("project_type", "")).strip()
    requires_ui_audit = project_type in UI_PROJECT_TYPES
    if not requires_ui_audit:
        return {
            "status": "skipped",
            "pass_ready": False,
            "checks": [],
            "blockers": [],
            "warnings": [],
            "missing_evidence": [],
            "anti_generic_risks": [],
            "brand_alignment_risks": [],
            "accessibility_risks": [],
            "responsive_risks": [],
            "recommended_fixes": [],
            "requires_human_clarification": False,
            "requires_decision_council": False,
            "why": "This project does not currently look like a UI-facing surface that needs a pre-return UI audit.",
            "advisory_only": bool(rules.get("advisory_only", True)),
        }

    visual_review = payload.get("visual_intent_contract_review") or {}
    brand_review = payload.get("brand_profile_review") or {}
    design_checks = _index_checks(list(payload.get("design_checks", [])))
    public_readiness = str(payload.get("public_readiness", "needs_improvement")).strip() or "needs_improvement"
    landing_score = int(payload.get("landing_score", 0) or 0)

    checks: List[Dict[str, Any]] = []
    warnings: List[Dict[str, Any]] = []
    blockers: List[Dict[str, Any]] = []
    missing_evidence: List[str] = []
    anti_generic_risks: List[str] = []
    brand_alignment_risks: List[str] = []
    accessibility_risks: List[str] = []
    responsive_risks: List[str] = []
    recommended_fixes: List[str] = []

    severity = rules.get("severity", {})

    visual_present = isinstance(visual_review, dict) and bool(visual_review)
    visual_required = bool(visual_review.get("requires_contract", True)) if visual_present else True
    if not visual_present or not visual_required:
        result = _check_result(
            "visual_intent_contract_present",
            "fail",
            str(severity.get("visual_intent_contract_present", "high")),
            ["visual intent review missing"],
            warning_code="ui_pre_return_missing_visual_intent",
            blocker="Visual intent contract review is missing for a UI-facing project.",
        )
        checks.append(result)
        blockers.append(result)
    else:
        status = "pass" if str(visual_review.get("status", "")).strip() == "ready" else "warning"
        result = _check_result(
            "visual_intent_contract_present",
            status,
            str(severity.get("visual_intent_contract_present", "high")),
            [f"visual_intent_status={visual_review.get('status', 'unknown')}"],
            warning_code=None if status == "pass" else "ui_pre_return_missing_visual_intent",
        )
        checks.append(result)
        if status != "pass":
            warnings.append(result)

    missing_visual_fields = list(visual_review.get("missing_fields", [])) if isinstance(visual_review, dict) else []
    weak_visual_fields = list(visual_review.get("weak_fields", [])) if isinstance(visual_review, dict) else []
    visual_status = "pass" if not missing_visual_fields and not weak_visual_fields and str(visual_review.get("status", "")).strip() == "ready" else "warning"
    visual_sufficient = _check_result(
        "visual_intent_contract_sufficient",
        visual_status,
        str(severity.get("visual_intent_contract_sufficient", "medium")),
        [*missing_visual_fields[:3], *weak_visual_fields[:3]] or [f"visual_intent_status={visual_review.get('status', 'unknown')}"],
        warning_code=None if visual_status == "pass" else "ui_pre_return_missing_visual_intent",
    )
    checks.append(visual_sufficient)
    if visual_status != "pass":
        warnings.append(visual_sufficient)
        recommended_fixes.append("Clarify the visual intent contract before final UI handoff.")

    brand_present = isinstance(brand_review, dict) and bool(brand_review)
    explicit_brand = bool(brand_review.get("explicit_profile_present")) if brand_present else False
    brand_present_status = "pass" if brand_present and explicit_brand else "warning"
    brand_present_check = _check_result(
        "brand_profile_present",
        brand_present_status,
        str(severity.get("brand_profile_present", "medium")),
        [f"profile_source={brand_review.get('profile_source', 'missing')}"] if brand_present else ["brand profile review missing"],
        warning_code=None if brand_present_status == "pass" else "ui_pre_return_missing_brand_profile",
    )
    checks.append(brand_present_check)
    if brand_present_status != "pass":
        warnings.append(brand_present_check)
        brand_alignment_risks.append("brand_profile_missing_or_inferred")
        recommended_fixes.append("Document an explicit brand profile before stronger identity claims.")

    brand_missing = list(brand_review.get("missing_fields", [])) if isinstance(brand_review, dict) else []
    brand_weak = list(brand_review.get("weak_fields", [])) if isinstance(brand_review, dict) else []
    brand_invalid = list(brand_review.get("invalid_fields", [])) if isinstance(brand_review, dict) else []
    brand_derivative = list(brand_review.get("derivative_risks", [])) if isinstance(brand_review, dict) else []
    brand_generic = list(brand_review.get("anti_generic_risks", [])) if isinstance(brand_review, dict) else []
    brand_accessibility = list(brand_review.get("accessibility_risks", [])) if isinstance(brand_review, dict) else []
    brand_sufficient_status = "pass" if not any([brand_missing, brand_weak, brand_invalid, brand_derivative, brand_generic, brand_accessibility]) and str(brand_review.get("status", "")).strip() == "ready" else "warning"
    brand_sufficient_check = _check_result(
        "brand_profile_sufficient",
        brand_sufficient_status,
        str(severity.get("brand_profile_sufficient", "medium")),
        [*brand_missing[:2], *brand_weak[:2], *brand_invalid[:2], *brand_derivative[:2], *brand_generic[:2]],
        warning_code=None if brand_sufficient_status == "pass" else "ui_pre_return_brand_mismatch",
    )
    checks.append(brand_sufficient_check)
    if brand_sufficient_status != "pass":
        warnings.append(brand_sufficient_check)
        brand_alignment_risks.extend(brand_missing + brand_weak + brand_invalid + brand_derivative)
        anti_generic_risks.extend(brand_generic)
        accessibility_risks.extend(brand_accessibility)
        recommended_fixes.append("Tighten the brand profile so palette, typography and differentiation are explicit.")

    def add_from_design(
        check_id: str,
        warning_code: str,
        *,
        output_check_id: Optional[str] = None,
        target_list: Optional[List[str]] = None,
        blocker_on_fail: bool = False,
    ) -> None:
        resolved_id = output_check_id or check_id
        design_check = design_checks.get(check_id)
        if not design_check:
            result = _check_result(
                resolved_id,
                "skipped",
                str(severity.get(resolved_id, "medium")),
                ["design check not available"],
                warning_code=warning_code,
            )
            checks.append(result)
            warnings.append(result)
            missing_evidence.append(resolved_id)
            if target_list is not None:
                target_list.append(f"{resolved_id}_unknown")
            return
        status = str(design_check.get("status", "warning")).strip()
        result = _check_result(
            resolved_id,
            status,
            str(severity.get(resolved_id, design_check.get("severity", "medium"))),
            list(design_check.get("evidence", [])),
            warning_code=None if status == "pass" else warning_code,
            blocker=str(design_check.get("recommendation")) if blocker_on_fail and status == "fail" else None,
        )
        checks.append(result)
        if status in {"warning", "fail", "skipped"}:
            warnings.append(result)
            if target_list is not None:
                target_list.append(resolved_id if status != "skipped" else f"{resolved_id}_unknown")
            if blocker_on_fail and status == "fail":
                blockers.append(result)
            recommendation = str(design_check.get("recommendation", "")).strip()
            if recommendation:
                recommended_fixes.append(recommendation)

    add_from_design("cta_clarity", "ui_pre_return_cta_weak", blocker_on_fail=True)
    add_from_design("above_the_fold_clarity", "ui_pre_return_cta_weak", blocker_on_fail=True)
    add_from_design("typography_coherence", "ui_pre_return_generic_risk", target_list=anti_generic_risks)
    add_from_design(
        "responsive_baseline",
        "ui_pre_return_responsive_unknown",
        output_check_id="responsive_expectations",
        target_list=responsive_risks,
    )
    add_from_design(
        "contrast_accessibility",
        "ui_pre_return_accessibility_weak",
        output_check_id="accessibility_basics",
        target_list=accessibility_risks,
    )

    hero_structure = design_checks.get("hero_structure")
    spacing_layout = design_checks.get("spacing_layout_coherence")
    content_density = design_checks.get("content_density")
    hierarchy_warning = False
    hierarchy_evidence: List[str] = []
    for signal in (hero_structure, spacing_layout, content_density):
        if isinstance(signal, dict):
            hierarchy_evidence.extend(list(signal.get("evidence", []))[:2])
            if str(signal.get("status", "")).strip() in {"warning", "fail"}:
                hierarchy_warning = True
    layout_hierarchy = _check_result(
        "layout_hierarchy",
        "warning" if hierarchy_warning else "pass",
        str(severity.get("layout_hierarchy", "medium")),
        hierarchy_evidence[:4] or ["layout hierarchy signals available"],
        warning_code="ui_pre_return_hierarchy_weak" if hierarchy_warning else None,
    )
    checks.append(layout_hierarchy)
    if hierarchy_warning:
        warnings.append(layout_hierarchy)
        anti_generic_risks.append("layout_hierarchy_weak")
        recommended_fixes.append("Strengthen hierarchy and pacing before treating the UI as final-return ready.")

    contract_fields = visual_review.get("contract") if isinstance(visual_review, dict) else {}
    profile_fields = brand_review.get("profile") if isinstance(brand_review, dict) else {}
    density_contract = str((contract_fields or {}).get("visual_density", "")).strip()
    density_profile = str((profile_fields or {}).get("visual_density", "")).strip()
    density_mismatch = bool(density_contract and density_profile and density_contract != density_profile)
    density_unknown = not density_contract or not density_profile
    density_status = "warning" if density_mismatch or density_unknown else "pass"
    density_check = _check_result(
        "visual_density_alignment",
        density_status,
        str(severity.get("visual_density_alignment", "medium")),
        [f"contract_density={density_contract or 'missing'}", f"profile_density={density_profile or 'missing'}"],
        warning_code="ui_pre_return_brand_mismatch" if density_status != "pass" else None,
    )
    checks.append(density_check)
    if density_status != "pass":
        warnings.append(density_check)
        brand_alignment_risks.append("visual_density_mismatch_or_unknown")

    motion_contract = str((contract_fields or {}).get("motion_intensity", "")).strip()
    motion_principles = list((profile_fields or {}).get("motion_principles", [])) if isinstance(profile_fields, dict) else []
    motion_unknown = not motion_contract or not motion_principles
    motion_status = "warning" if motion_unknown else "pass"
    motion_check = _check_result(
        "motion_alignment",
        motion_status,
        str(severity.get("motion_alignment", "low")),
        [f"contract_motion={motion_contract or 'missing'}", f"motion_principles={motion_principles[:2] or ['missing']}"],
        warning_code="ui_pre_return_brand_mismatch" if motion_status != "pass" else None,
    )
    checks.append(motion_check)
    if motion_status != "pass":
        warnings.append(motion_check)
        brand_alignment_risks.append("motion_alignment_unknown")

    anti_generic_sources = []
    for check_id in ("anti_generic_default", "landing_vs_documentation_balance", "section_rhythm"):
        design_check = design_checks.get(check_id)
        if isinstance(design_check, dict) and str(design_check.get("status", "")).strip() in {"warning", "fail"}:
            anti_generic_sources.append(check_id)
    anti_generic_sources.extend(brand_generic)
    anti_generic_check = _check_result(
        "anti_generic_patterns",
        "warning" if anti_generic_sources else "pass",
        str(severity.get("anti_generic_patterns", "medium")),
        anti_generic_sources[:4] or ["no major anti-generic signal"],
        warning_code="ui_pre_return_generic_risk" if anti_generic_sources else None,
    )
    checks.append(anti_generic_check)
    if anti_generic_sources:
        warnings.append(anti_generic_check)
        anti_generic_risks.extend(anti_generic_sources)

    color_generic = "generic_color_strategy" in brand_generic
    color_unknown = "missing_contrast_notes" in brand_accessibility or not (profile_fields or {}).get("color_strategy")
    color_status = "warning" if color_generic or color_unknown else "pass"
    color_check = _check_result(
        "color_strategy_coherence",
        color_status,
        str(severity.get("color_strategy_coherence", "medium")),
        [f"generic_color={str(color_generic).lower()}", f"color_strategy_present={str(bool((profile_fields or {}).get('color_strategy'))).lower()}"],
        warning_code="ui_pre_return_generic_risk" if color_status != "pass" else None,
    )
    checks.append(color_check)
    if color_status != "pass":
        warnings.append(color_check)
        anti_generic_risks.append("color_strategy_coherence_weak")

    evidence_expectations = list((contract_fields or {}).get("evidence_expectations", [])) or list((profile_fields or {}).get("evidence_expectations", []))
    evidence_missing = not evidence_expectations
    evidence_check = _check_result(
        "evidence_expectations",
        "warning" if evidence_missing else "pass",
        str(severity.get("evidence_expectations", "high")),
        evidence_expectations[:3] or ["evidence expectations missing"],
        warning_code="ui_pre_return_missing_evidence" if evidence_missing else None,
    )
    checks.append(evidence_check)
    if evidence_missing:
        warnings.append(evidence_check)
        missing_evidence.append("evidence_expectations")
        recommended_fixes.append("State what evidence Atlas needs before calling the UI passable.")

    unsupported_ready_claim = public_readiness == "ready" and (
        blockers or any(item["status"] in {"warning", "fail"} for item in checks if item["id"] in {
            "visual_intent_contract_present",
            "visual_intent_contract_sufficient",
            "brand_profile_present",
            "brand_profile_sufficient",
            "cta_clarity",
            "above_the_fold_clarity",
            "responsive_baseline",
            "contrast_accessibility",
            "evidence_expectations",
        })
    )
    evidence_claim_check = _check_result(
        "final_claim_supported_by_evidence",
        "fail" if unsupported_ready_claim else "pass",
        str(severity.get("final_claim_supported_by_evidence", "high")),
        [f"public_readiness={public_readiness}", f"landing_score={landing_score}"],
        warning_code="ui_pre_return_not_ready" if unsupported_ready_claim else None,
        blocker="The current UI still has unresolved readiness warnings, so the final 'ready' claim is not supported by evidence." if unsupported_ready_claim else None,
    )
    checks.append(evidence_claim_check)
    if unsupported_ready_claim:
        warnings.append(evidence_claim_check)
        blockers.append(evidence_claim_check)

    warning_codes = _dedupe_preserve_order([str(item.get("warning_code", "")).strip() for item in warnings if str(item.get("warning_code", "")).strip()])
    recommended_fixes = _dedupe_preserve_order(recommended_fixes)
    anti_generic_risks = _dedupe_preserve_order(anti_generic_risks)
    brand_alignment_risks = _dedupe_preserve_order(brand_alignment_risks)
    accessibility_risks = _dedupe_preserve_order(accessibility_risks)
    responsive_risks = _dedupe_preserve_order(responsive_risks)
    missing_evidence = _dedupe_preserve_order(missing_evidence)

    requires_decision_council = bool(
        brand_derivative
        or len(blockers) >= 2
        or ("visual_density_mismatch_or_unknown" in brand_alignment_risks and anti_generic_risks)
    )
    requires_human_clarification = bool(
        missing_visual_fields
        or weak_visual_fields
        or brand_missing
        or brand_weak
        or brand_invalid
        or missing_evidence
        or blockers
    )

    design_quality_review = audit_design_quality(
        {
            "project_type": project_type,
            "design_checks": list(payload.get("design_checks", [])),
            "visual_intent_contract_review": visual_review,
            "brand_profile_review": brand_review,
            "ui_pre_return_review": {
                "warnings": warning_codes,
                "anti_generic_risks": anti_generic_risks,
                "accessibility_risks": accessibility_risks,
            },
            "visual_signals": payload.get("visual_signals", {}),
            "source_text": payload.get("source_text", ""),
        },
        root=root,
    )
    if isinstance(design_quality_review, dict) and design_quality_review.get("status") == "not_ready":
        blockers.append(
            {
                "id": "design_quality_enforcement",
                "severity": "high",
                "evidence": list(design_quality_review.get("detected_risks", []))[:4],
                "blocker": str(design_quality_review.get("why", "")).strip()
                or "Visual quality enforcement still sees a redesign-level blocker.",
            }
        )
        warning_codes = _dedupe_preserve_order([*warning_codes, "ui_pre_return_not_ready"])
    if isinstance(design_quality_review, dict) and design_quality_review.get("status") in {"needs_attention", "not_ready"}:
        recommended_fixes.extend(list(design_quality_review.get("recommended_fixes", []))[:4])
        requires_human_clarification = True
    recommended_fixes = _dedupe_preserve_order(recommended_fixes)

    pass_ready = not blockers and not warning_codes
    status = "pass" if pass_ready else "needs_attention"
    if blockers:
        status = "not_ready"

    why_parts: List[str] = []
    if blockers:
        why_parts.append(f"Blockers remain before a stronger final-return claim: {', '.join(item['id'] for item in blockers[:3])}.")
    if warning_codes:
        why_parts.append(f"Open advisory warnings remain: {', '.join(warning_codes[:5])}.")
    if missing_evidence:
        why_parts.append(f"Missing evidence: {', '.join(missing_evidence[:4])}.")
    if not why_parts:
        why_parts.append("The current UI has enough intent, brand and evidence signals for an advisory pre-return pass.")

    return {
        "status": status,
        "pass_ready": pass_ready,
        "checks": checks,
        "blockers": blockers,
        "warnings": warning_codes,
        "missing_evidence": missing_evidence,
        "anti_generic_risks": anti_generic_risks,
        "brand_alignment_risks": brand_alignment_risks,
        "accessibility_risks": accessibility_risks,
        "responsive_risks": responsive_risks,
        "recommended_fixes": recommended_fixes[:6],
        "requires_human_clarification": requires_human_clarification,
        "requires_decision_council": requires_decision_council,
        "design_quality_review": design_quality_review,
        "why": " ".join(why_parts),
        "advisory_only": bool(rules.get("advisory_only", True)),
    }


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(add_help=True)
    parser.add_argument("--payload-json", required=True)
    args = parser.parse_args(argv)
    payload = json.loads(args.payload_json)
    result = audit_ui_pre_return(payload, root=DEFAULT_ROOT)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
