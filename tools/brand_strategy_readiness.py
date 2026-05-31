from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Dict, List, Optional

try:
    from tools.brand_profile_schema import build_brand_profile_assessment
except ModuleNotFoundError:
    from brand_profile_schema import build_brand_profile_assessment


DEFAULT_ROOT = Path(__file__).resolve().parents[1]
RULES_PATH = Path("config/brand_strategy_rules.json")


def load_brand_strategy_rules(root: Path = DEFAULT_ROOT) -> Dict[str, Any]:
    return json.loads((root / RULES_PATH).read_text(encoding="utf-8-sig"))


def _normalize(value: Any) -> str:
    return " ".join(str(value or "").strip().lower().split())


def _stringify(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, str):
        return value.strip()
    if isinstance(value, (list, tuple, set)):
        return ", ".join(str(item).strip() for item in value if str(item).strip())
    if isinstance(value, dict):
        return ", ".join(f"{key}: {value[key]}" for key in value if str(value[key]).strip())
    return str(value).strip()


def _listify(value: Any) -> List[str]:
    if isinstance(value, list):
        return [str(item).strip() for item in value if str(item).strip()]
    if isinstance(value, tuple):
        return [str(item).strip() for item in value if str(item).strip()]
    text = _stringify(value)
    if not text:
        return []
    return [part.strip() for part in text.replace("|", ",").split(",") if part.strip()]


def _has_value(value: Any) -> bool:
    if value is None:
        return False
    if isinstance(value, str):
        return bool(value.strip())
    if isinstance(value, (list, tuple, set, dict)):
        return bool(value)
    return True


def _clamp(score: int) -> int:
    return max(0, min(100, score))


def _extract_inputs(payload: Dict[str, Any], rules: Dict[str, Any]) -> Dict[str, Any]:
    aliases = rules.get("input_aliases", {})
    extracted: Dict[str, Any] = {}
    for canonical in aliases:
        candidates = [canonical, *list(aliases.get(canonical, []))]
        for name in candidates:
            value = payload.get(name)
            if _has_value(value):
                extracted[canonical] = value
                break
    if _has_value(payload.get("project_type")):
        extracted["project_type"] = payload.get("project_type")
    if _has_value(payload.get("project_name")):
        extracted["project_name"] = payload.get("project_name")
    if _has_value(payload.get("objective")):
        extracted["objective"] = payload.get("objective")
    return extracted


def _resolve_visual_intent_contract(payload: Dict[str, Any]) -> Dict[str, Any]:
    review = payload.get("visual_intent_contract_review") or payload.get("visual_intent_contract") or {}
    if isinstance(review, dict) and isinstance(review.get("contract"), dict):
        return review.get("contract") or {}
    return review if isinstance(review, dict) else {}


def _resolve_brand_profile(payload: Dict[str, Any]) -> Dict[str, Any]:
    review = payload.get("brand_profile_review") or {}
    if isinstance(review, dict) and isinstance(review.get("profile"), dict):
        return review.get("profile") or {}
    profile = payload.get("brand_profile") or {}
    return profile if isinstance(profile, dict) else {}


def _contains_any(surface: str, signals: List[str]) -> List[str]:
    normalized_surface = _normalize(surface)
    matches: List[str] = []
    for signal in signals:
        cleaned = str(signal).strip()
        if cleaned and _normalize(cleaned) in normalized_surface:
            matches.append(cleaned)
    return matches


def _is_applicable(project_type: str, assessment: Dict[str, Any], rules: Dict[str, Any]) -> bool:
    normalized_type = _normalize(project_type)
    if normalized_type in {_normalize(item) for item in rules.get("applicable_project_types", [])}:
        return True
    return bool(assessment.get("requires_profile"))


def assess_brand_strategy_readiness(
    payload: Dict[str, Any],
    *,
    root: Path = DEFAULT_ROOT,
    project: Optional[Path] = None,
) -> Dict[str, Any]:
    root = root.resolve()
    project = (project or root).resolve()
    rules = load_brand_strategy_rules(root)
    extracted = _extract_inputs(payload, rules)

    project_type = _stringify(extracted.get("project_type")) or "unknown"
    visual_contract = _resolve_visual_intent_contract(payload)
    explicit_profile = _resolve_brand_profile(payload)
    copy_review = payload.get("copywriting_conversion_posture") or payload.get("copywriting_review") or {}
    brand_review = payload.get("brand_profile_review") or {}
    design_review = payload.get("design_quality_review") or {}
    design_warnings = _listify((design_review or {}).get("warnings", [])) + _listify(payload.get("design_warnings"))

    assessment = build_brand_profile_assessment(
        project_type=project_type,
        visual_intent_contract=visual_contract,
        profile=explicit_profile if explicit_profile else None,
        project=project,
        project_name=_stringify(extracted.get("project_name")) or project.name,
        objective=_stringify(extracted.get("objective")),
        root=root,
    )
    profile = (assessment.get("profile") or {}) if isinstance(assessment, dict) else {}

    if not _is_applicable(project_type, assessment, rules):
        return {
            "status": "ok",
            "brand_readiness_state": "not_applicable",
            "positioning_score": 0,
            "differentiation_score": 0,
            "trust_score": 0,
            "visual_consistency_score": 0,
            "tone_consistency_score": 0,
            "audience_fit_score": 0,
            "generic_brand_risk": "low",
            "warnings": [],
            "risks": [],
            "missing_inputs": [],
            "recommended_changes": [],
            "why": "Brand strategy readiness is only relevant for frontend or other branded user-facing surfaces.",
            "advisory_only": bool(rules.get("advisory_only", True)),
        }

    audience = _stringify(extracted.get("target_audience")) or _stringify(profile.get("audience"))
    category = _stringify(extracted.get("category")) or _stringify(profile.get("project_type")) or project_type
    positioning = (
        _stringify(extracted.get("positioning"))
        or _stringify(visual_contract.get("problem_or_promise"))
        or _stringify(payload.get("product_promise"))
        or _stringify(extracted.get("objective"))
    )
    differentiation_notes = _stringify(extracted.get("differentiation_notes")) or _stringify(profile.get("differentiation_notes"))
    verbal_tone = _listify(extracted.get("verbal_tone")) or _listify(profile.get("copy_tone")) or _listify(payload.get("voice_attributes"))
    visual_tone = _stringify(extracted.get("visual_tone")) or _stringify(visual_contract.get("mood_or_vibe"))
    cta_intent = _listify(extracted.get("cta_intent")) or _listify(profile.get("cta_rules")) or _listify(visual_contract.get("primary_cta_intent"))
    proof_points = _stringify(extracted.get("proof_points")) or _stringify(payload.get("proof_points"))
    page_text = _stringify(extracted.get("page_text"))

    personality_traits = _listify(profile.get("personality_traits"))
    color_strategy = profile.get("color_strategy") if isinstance(profile.get("color_strategy"), dict) else {}
    typography_strategy = profile.get("typography_strategy") if isinstance(profile.get("typography_strategy"), dict) else {}
    accessibility_notes = _stringify(profile.get("accessibility_notes"))
    evidence_expectations = _listify(profile.get("evidence_expectations"))
    anti_generic_risks = _listify(assessment.get("anti_generic_risks"))
    derivative_risks = _listify(assessment.get("derivative_risks"))
    accessibility_risks = _listify(assessment.get("accessibility_risks"))
    weak_fields = _listify(assessment.get("weak_fields"))
    missing_fields = _listify(assessment.get("missing_fields"))
    brand_profile_status = _stringify(assessment.get("status"))

    copy_state = _stringify((copy_review or {}).get("copy_readiness_state"))
    copy_trust_score = (copy_review or {}).get("trust_score")
    copy_tone_score = (copy_review or {}).get("tone_consistency_score")
    hero_message = (copy_review or {}).get("hero_message") if isinstance(copy_review, dict) else {}
    if not isinstance(hero_message, dict):
        hero_message = {}
    copy_warnings = _listify((copy_review or {}).get("warnings", []))
    must_not_claim = _listify((copy_review or {}).get("must_not_claim", []))

    brand_surface = " ".join(
        part
        for part in [
            audience,
            category,
            positioning,
            differentiation_notes,
            visual_tone,
            " ".join(verbal_tone),
            " ".join(cta_intent),
            proof_points,
            page_text,
            " ".join(personality_traits),
            " ".join(copy_warnings),
            " ".join(design_warnings),
        ]
        if part
    )

    generic_category_terms = {_normalize(item) for item in rules.get("generic_category_terms", [])}
    category_clear = bool(category) and _normalize(category) not in generic_category_terms
    audience_clear = bool(audience)
    positioning_clear = bool(positioning)
    differentiation_clear = bool(differentiation_notes) and len(differentiation_notes.split()) >= 6
    color_roles_present = all(_stringify(color_strategy.get(field_name)) for field_name in rules.get("required_color_roles", []))
    generic_palette_terms = _contains_any(
        " ".join(_stringify(color_strategy.get(field_name)) for field_name in ("primary", "secondary", "accent", "background", "contrast_notes")),
        list(rules.get("generic_palette_terms", [])),
    )
    typography_hierarchy = (
        bool(_stringify(typography_strategy.get("heading_style")))
        and bool(_stringify(typography_strategy.get("body_style")))
        and _normalize(typography_strategy.get("heading_style")) != _normalize(typography_strategy.get("body_style"))
        and bool(_stringify(typography_strategy.get("contrast_rationale")))
    )
    template_signals = _contains_any(brand_surface, list(rules.get("template_risk_signals", [])))
    generic_brand_phrases = _contains_any(brand_surface, list(rules.get("generic_brand_phrases", [])))
    inconsistent_tone_signals = _contains_any(brand_surface, list(rules.get("inconsistent_tone_signals", [])))
    claims_without_evidence = _contains_any(brand_surface, list(rules.get("claims_without_evidence_terms", [])))
    audience_mismatch = _contains_any(brand_surface, list(rules.get("audience_mismatch_signals", [])))
    cta_clear = bool(hero_message.get("cta_clear"))
    trust_boundary_present = bool(proof_points) or bool(evidence_expectations) or not bool(claims_without_evidence)
    visual_trust_low = bool(accessibility_risks) or not accessibility_notes or not color_roles_present
    generic_template_brand = bool(template_signals or generic_brand_phrases or generic_palette_terms or anti_generic_risks or derivative_risks)
    verbal_tone_inconsistent = bool(inconsistent_tone_signals) or (isinstance(copy_tone_score, int) and copy_tone_score < 60)

    positioning_score = _clamp(
        100
        - (25 if not audience_clear else 0)
        - (20 if not category_clear else 0)
        - (25 if not positioning_clear else 0)
        - (20 if not differentiation_clear else 0)
        - (10 if not hero_message.get("problem_visible", True) else 0)
    )
    differentiation_score = _clamp(
        100
        - (30 if generic_template_brand else 0)
        - (25 if not differentiation_clear else 0)
        - (15 if "missing_differentiation_notes" in anti_generic_risks else 0)
        - (15 if not personality_traits else 0)
        - (15 if not _stringify(profile.get("originality_level")) else 0)
    )
    trust_score = _clamp(
        int(copy_trust_score) if isinstance(copy_trust_score, int) else 85
        - (35 if must_not_claim or copy_state == "blocked" else 0)
        - (20 if claims_without_evidence else 0)
        - (10 if not trust_boundary_present else 0)
        - (10 if visual_trust_low else 0)
        - (10 if not cta_clear else 0)
    )
    visual_consistency_score = _clamp(
        100
        - (25 if not color_roles_present else 0)
        - (20 if generic_palette_terms else 0)
        - (20 if not typography_hierarchy else 0)
        - (15 if "low_typographic_contrast" in anti_generic_risks else 0)
        - (10 if "layout_principles" in missing_fields or "layout_principles" in weak_fields else 0)
        - (10 if "motion_principles" in missing_fields or "motion_principles" in weak_fields else 0)
    )
    tone_consistency_score = _clamp(
        int(copy_tone_score) if isinstance(copy_tone_score, int) else 85
        - (20 if not verbal_tone else 0)
        - (20 if verbal_tone_inconsistent else 0)
        - (10 if not visual_tone else 0)
        - (10 if not personality_traits else 0)
    )
    audience_fit_score = _clamp(
        100
        - (30 if not audience_clear else 0)
        - (20 if not category_clear else 0)
        - (20 if audience_mismatch else 0)
        - (15 if not cta_clear else 0)
        - (15 if not positioning_clear else 0)
    )

    warnings: List[str] = []
    risks: List[Dict[str, str]] = []
    missing_inputs: List[str] = []
    recommended_changes: List[str] = []

    if not audience_clear:
        missing_inputs.append("target_audience")
        warnings.append("The brand still lacks a clearly named target audience.")
        recommended_changes.append("Name the ideal customer explicitly so tone, CTA and visual choices can align with a real buyer.")
    if not category_clear:
        missing_inputs.append("category")
        warnings.append("The brand category is still too generic to position the product clearly.")
        recommended_changes.append("Describe the product category in a more specific way than a generic app or website label.")
    if not positioning_clear:
        missing_inputs.append("positioning")
        warnings.append("The brand positioning is still too implicit.")
        recommended_changes.append("Write a short positioning statement that explains what this is and why it matters.")
    if not differentiation_clear:
        warnings.append("The brand still lacks a differentiated angle that would make it memorable.")
        recommended_changes.append("Add differentiation notes that explain why this product should not feel like a generic competitor.")
    if not color_roles_present:
        warnings.append("The palette is missing clear color roles, which weakens brand consistency.")
        recommended_changes.append("Define primary, secondary, accent and background roles, plus contrast rationale.")
    if generic_palette_terms:
        warnings.append("The palette still reads as generic or default instead of intentional.")
        recommended_changes.append("Refine the palette with a more product-specific accent strategy and clearer contrast logic.")
        risks.append({"severity": "medium", "type": "generic_palette", "message": f"Generic palette signals detected: {', '.join(generic_palette_terms[:3])}."})
    if generic_brand_phrases:
        warnings.append("The brand language still sounds generic instead of product-specific.")
        recommended_changes.append("Replace generic brand phrases with sharper positioning and more distinctive product language.")
    if not typography_hierarchy:
        warnings.append("Typography still lacks hierarchy or rationale between heading and body roles.")
        recommended_changes.append("Define distinct heading and body typography roles with a contrast rationale.")
    if verbal_tone_inconsistent:
        warnings.append("The verbal tone is inconsistent with the current brand direction.")
        recommended_changes.append("Tighten the copy tone so it matches the intended audience, product seriousness and CTA.")
    if claims_without_evidence:
        warnings.append("The brand language makes trust claims without enough evidence or boundaries.")
        recommended_changes.append("Replace unsupported brand claims with bounded language or explicit proof points.")
        risks.append({"severity": "high" if must_not_claim else "medium", "type": "unsupported_brand_claim", "message": f"Claims without evidence detected: {', '.join(claims_without_evidence[:3])}."})
    if generic_template_brand:
        warnings.append("The brand direction still feels generic or too close to a template.")
        recommended_changes.append("Increase differentiation through clearer positioning, stronger anti-generic choices and more specific brand rationale.")
    if visual_trust_low:
        warnings.append("Visual trust is weaker than it should be for this type of product.")
        recommended_changes.append("Strengthen accessibility notes, contrast rationale and confidence signals before calling the brand ready.")
    if audience_mismatch:
        warnings.append("The brand tone or styling does not fully match the target client.")
        recommended_changes.append("Adjust the personality and tone so the presentation feels credible for the intended buyer.")
    if not cta_clear:
        warnings.append("The CTA posture does not feel fully coherent with the brand promise.")
        recommended_changes.append("Clarify the next action so it matches the promise and level of trust the brand is trying to build.")

    if anti_generic_risks:
        risks.append({"severity": "medium", "type": "anti_generic", "message": f"Brand profile anti-generic risks: {', '.join(anti_generic_risks[:3])}."})
    if derivative_risks:
        risks.append({"severity": "medium", "type": "derivative_brand", "message": f"Derivative brand risks: {', '.join(derivative_risks[:3])}."})
    if must_not_claim or copy_state == "blocked":
        brand_readiness_state = "blocked"
    else:
        thresholds = rules.get("ready_thresholds", {})
        passes_thresholds = (
            positioning_score >= int(thresholds.get("positioning_score", 70))
            and differentiation_score >= int(thresholds.get("differentiation_score", 70))
            and trust_score >= int(thresholds.get("trust_score", 75))
            and visual_consistency_score >= int(thresholds.get("visual_consistency_score", 70))
            and tone_consistency_score >= int(thresholds.get("tone_consistency_score", 70))
            and audience_fit_score >= int(thresholds.get("audience_fit_score", 70))
        )
        brand_readiness_state = "ready" if passes_thresholds and not warnings else "needs_improvement"

    if generic_template_brand or differentiation_score < 55:
        generic_brand_risk = "high"
    elif warnings:
        generic_brand_risk = "medium"
    else:
        generic_brand_risk = "low"

    return {
        "status": "ok",
        "brand_readiness_state": brand_readiness_state,
        "positioning_score": positioning_score,
        "differentiation_score": differentiation_score,
        "trust_score": trust_score,
        "visual_consistency_score": visual_consistency_score,
        "tone_consistency_score": tone_consistency_score,
        "audience_fit_score": audience_fit_score,
        "generic_brand_risk": generic_brand_risk,
        "warnings": list(dict.fromkeys(warnings)),
        "risks": risks,
        "missing_inputs": list(dict.fromkeys(missing_inputs)),
        "recommended_changes": list(dict.fromkeys(recommended_changes)),
        "why": (
            "Atlas found brand strategy gaps that still weaken positioning, trust or distinctiveness."
            if warnings or brand_readiness_state == "blocked"
            else "The brand direction looks coherent enough to proceed to human review."
        ),
        "advisory_only": bool(rules.get("advisory_only", True)),
    }


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(add_help=True)
    parser.add_argument("--project", default=None)
    parser.add_argument("--payload-json", default="{}")
    args = parser.parse_args(argv)

    project = Path(args.project).resolve() if args.project else DEFAULT_ROOT
    payload = json.loads(args.payload_json)
    result = assess_brand_strategy_readiness(payload, root=DEFAULT_ROOT, project=project)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
