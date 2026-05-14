from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple


DEFAULT_ROOT = Path(__file__).resolve().parents[1]
RULES_PATH = Path("config/design_quality_enforcement_rules.json")
UI_PROJECT_TYPES = {"frontend_app", "fullstack", "internal_tool"}
TRIGGER_STATUSES = {"warning", "fail", "blocked", "high", "detected", "present", "true", "yes"}

TEXT_PATTERNS = {
    "border_weight_excessive": (
        "thick black border",
        "thick black borders",
        "heavy border",
        "heavy borders",
        "border-heavy",
        "bordes negros gruesos",
        "borde negro grueso",
    ),
    "shadow_style_heavy": (
        "heavy shadow",
        "hard shadow",
        "harsh shadow",
        "sombras duras",
        "sombra dura",
    ),
    "card_repetition": (
        "repeated cards",
        "repetitive cards",
        "too many cards",
        "cards repeated",
        "cards repetidas",
        "exceso de cards",
    ),
    "weak_visual_hierarchy": (
        "weak hierarchy",
        "poor hierarchy",
        "little hierarchy",
        "falta de jerarquia",
        "poca jerarquia",
    ),
    "weak_button_hierarchy": (
        "buttons too heavy",
        "weak button hierarchy",
        "botones demasiado pesados",
        "botones sin jerarquia",
    ),
    "poor_spacing": (
        "poor spacing",
        "cramped",
        "no breathing room",
        "falta de aire",
        "low air density",
    ),
    "weak_color_system": (
        "poor palette",
        "weak color system",
        "palette without system",
        "paleta pobre",
        "paleta sin sistema",
    ),
    "typography_without_intent": (
        "typography without intent",
        "poor typography",
        "default typography",
        "tipografia sin intencion",
        "tipografia pobre",
    ),
    "wireframe_look": (
        "wireframe",
        "readme-like",
        "readme style",
        "form-like",
        "formulario crudo",
        "diseño tipo readme",
        "diseño tipo formulario crudo",
    ),
    "amateur_internal_tool_look": (
        "amateur",
        "internal tool look",
        "technical/amateur",
        "look tecnico",
        "look amateur",
        "tosco",
        "amateur internal tool",
    ),
    "excessive_horizontal_spread": (
        "too wide",
        "horizontal spread",
        "excessive horizontal spread",
        "demasiado ancho",
        "exceso horizontal",
    ),
    "unclear_state_feedback": (
        "unclear state feedback",
        "state feedback weak",
        "estado mal representado",
        "estado poco claro",
    ),
    "generic_dashboard_pattern": (
        "generic dashboard",
        "dashboard template",
        "generic saas template",
        "saas template",
        "dashboard generico",
        "template saas",
    ),
    "brutalism_misapplied": (
        "bad brutalism",
        "misapplied brutalism",
        "brutalism misapplied",
        "brutalismo mal aplicado",
    ),
}


def load_design_quality_rules(root: Path = DEFAULT_ROOT) -> Dict[str, Any]:
    return json.loads((root / RULES_PATH).read_text(encoding="utf-8-sig"))


def _normalize(value: str) -> str:
    return re.sub(r"\s+", " ", str(value or "").strip().lower())


def _dedupe_preserve_order(values: List[str]) -> List[str]:
    seen: set[str] = set()
    deduped: List[str] = []
    for value in values:
        normalized = _normalize(value)
        if not normalized or normalized in seen:
            continue
        seen.add(normalized)
        deduped.append(str(value).strip())
    return deduped


def _index_checks(checks: List[Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:
    indexed: Dict[str, Dict[str, Any]] = {}
    for item in checks:
        if not isinstance(item, dict):
            continue
        check_id = str(item.get("id", "")).strip()
        if check_id:
            indexed[check_id] = item
    return indexed


def _signal_triggered(signals: Dict[str, Any], key: str) -> Tuple[bool, List[str]]:
    raw = signals.get(key)
    if raw is None:
        return False, []
    if isinstance(raw, bool):
        return raw, [f"signal:{key}={str(raw).lower()}"] if raw else []
    if isinstance(raw, str):
        normalized = _normalize(raw)
        triggered = normalized in TRIGGER_STATUSES
        return triggered, [f"signal:{key}={normalized}"] if triggered else []
    if isinstance(raw, dict):
        status = _normalize(raw.get("status", ""))
        evidence = [str(item).strip() for item in raw.get("evidence", []) if str(item).strip()]
        triggered = status in TRIGGER_STATUSES or bool(raw.get("present"))
        return triggered, evidence[:4] or ([f"signal:{key}={status}"] if triggered else [])
    return False, []


def _design_check_triggered(indexed_checks: Dict[str, Dict[str, Any]], check_id: str) -> Tuple[bool, List[str]]:
    check = indexed_checks.get(check_id)
    if not isinstance(check, dict):
        return False, []
    status = _normalize(check.get("status", ""))
    if status not in {"warning", "fail"}:
        return False, []
    evidence = [str(item).strip() for item in check.get("evidence", []) if str(item).strip()]
    recommendation = str(check.get("recommendation", "")).strip()
    details = evidence[:4]
    if recommendation:
        details.append(recommendation)
    return True, details[:4]


def _text_triggered(text: str, key: str) -> Tuple[bool, List[str]]:
    normalized = _normalize(text)
    if not normalized:
        return False, []
    matches = [pattern for pattern in TEXT_PATTERNS.get(key, ()) if pattern in normalized]
    return bool(matches), matches[:4]


def _severity_penalty(severity: str) -> int:
    return {"high": 14, "medium": 8, "low": 4}.get(_normalize(severity), 6)


def _build_item(check_id: str, rule: Dict[str, Any], evidence: List[str]) -> Dict[str, Any]:
    return {
        "check": check_id,
        "severity": str(rule.get("severity", "medium")).strip() or "medium",
        "evidence": evidence[:4],
        "recommended_fix": str(rule.get("recommended_fix", "")).strip(),
        "why_it_matters": str(rule.get("why_it_matters", "")).strip(),
    }


def audit_design_quality(payload: Dict[str, Any], *, root: Path = DEFAULT_ROOT) -> Dict[str, Any]:
    rules = load_design_quality_rules(root)
    project_type = str(payload.get("project_type", "")).strip()
    if project_type not in UI_PROJECT_TYPES:
        return {
            "status": "skipped",
            "ready_for_handoff": False,
            "blockers": [],
            "warnings": [],
            "visual_quality_score": 0,
            "detected_risks": [],
            "recommended_fixes": [],
            "required_redesign_level": "none",
            "why": "This project does not currently look like a UI-facing surface that needs design-quality enforcement.",
            "advisory_only": bool(rules.get("advisory_only", True)),
        }

    check_rules = rules.get("checks", {})
    design_checks = _index_checks(list(payload.get("design_checks", [])))
    visual_signals = payload.get("visual_signals")
    visual_signals = visual_signals if isinstance(visual_signals, dict) else {}
    source_text = str(payload.get("source_text", "") or "")
    brand_review = payload.get("brand_profile_review") or {}
    ui_pre_return_review = payload.get("ui_pre_return_review") or {}

    brand_generic = list(brand_review.get("anti_generic_risks", [])) if isinstance(brand_review, dict) else []
    brand_accessibility = list(brand_review.get("accessibility_risks", [])) if isinstance(brand_review, dict) else []
    pre_return_risks = list(ui_pre_return_review.get("anti_generic_risks", [])) if isinstance(ui_pre_return_review, dict) else []

    derived_signals: Dict[str, Tuple[bool, List[str]]] = {}

    def infer(check_id: str) -> Tuple[bool, List[str]]:
        explicit, explicit_evidence = _signal_triggered(visual_signals, check_id)
        if explicit:
            return True, explicit_evidence

        text_hit, text_evidence = _text_triggered(source_text, check_id)
        if text_hit:
            return True, [f"text:{item}" for item in text_evidence]

        if check_id == "card_repetition":
            return _design_check_triggered(design_checks, "section_rhythm")
        if check_id == "weak_visual_hierarchy":
            evidence: List[str] = []
            triggered = False
            for design_id in ("hero_structure", "spacing_layout_coherence", "content_density"):
                hit, hit_evidence = _design_check_triggered(design_checks, design_id)
                if hit:
                    triggered = True
                    evidence.extend(hit_evidence[:2])
            return triggered, evidence[:4]
        if check_id == "weak_button_hierarchy":
            return _design_check_triggered(design_checks, "cta_clarity")
        if check_id == "poor_spacing":
            return _design_check_triggered(design_checks, "spacing_layout_coherence")
        if check_id == "weak_color_system":
            anti_generic_hit, anti_generic_evidence = _design_check_triggered(design_checks, "anti_generic_default")
            if anti_generic_hit:
                return True, anti_generic_evidence
            if "generic_color_strategy" in brand_generic or "missing_contrast_notes" in brand_accessibility:
                return True, (brand_generic + brand_accessibility)[:4]
            return False, []
        if check_id == "typography_without_intent":
            return _design_check_triggered(design_checks, "typography_coherence")
        if check_id == "wireframe_look":
            landing_balance, landing_evidence = _design_check_triggered(design_checks, "landing_vs_documentation_balance")
            density, density_evidence = _design_check_triggered(design_checks, "content_density")
            if landing_balance and density:
                return True, (landing_evidence + density_evidence)[:4]
            return False, []
        if check_id == "excessive_horizontal_spread":
            density, density_evidence = _design_check_triggered(design_checks, "content_density")
            return density, density_evidence[:4]
        if check_id == "unclear_state_feedback":
            if "ui_pre_return_accessibility_weak" in list(ui_pre_return_review.get("warnings", [])):
                return True, list(ui_pre_return_review.get("accessibility_risks", []))[:4]
            return False, []
        if check_id == "generic_dashboard_pattern":
            anti_generic_hit, anti_generic_evidence = _design_check_triggered(design_checks, "anti_generic_default")
            if anti_generic_hit:
                return True, anti_generic_evidence
            if "anti_generic_default" in pre_return_risks:
                return True, ["ui_pre_return:anti_generic_default"]
            return False, []
        if check_id == "amateur_internal_tool_look":
            base_risks = []
            for dependent in ("weak_visual_hierarchy", "poor_spacing", "weak_color_system", "typography_without_intent"):
                hit, hit_evidence = derived_signals.get(dependent, (False, []))
                if hit:
                    base_risks.extend([f"{dependent}:{item}" for item in hit_evidence[:1]] or [dependent])
            if len(base_risks) >= 3:
                return True, base_risks[:4]
            return False, []
        return False, []

    blockers: List[Dict[str, Any]] = []
    warnings: List[Dict[str, Any]] = []
    detected_risks: List[str] = []
    recommended_fixes: List[str] = []
    score = 100

    ordered_checks = [
        "border_weight_excessive",
        "shadow_style_heavy",
        "card_repetition",
        "weak_visual_hierarchy",
        "weak_button_hierarchy",
        "poor_spacing",
        "weak_color_system",
        "typography_without_intent",
        "wireframe_look",
        "amateur_internal_tool_look",
        "excessive_horizontal_spread",
        "unclear_state_feedback",
        "generic_dashboard_pattern",
        "brutalism_misapplied",
    ]

    for check_id in ordered_checks:
        triggered, evidence = infer(check_id)
        derived_signals[check_id] = (triggered, evidence)
        if not triggered:
            continue
        rule = check_rules.get(check_id, {})
        item = _build_item(check_id, rule, evidence)
        detected_risks.append(check_id)
        recommended_fix = item.get("recommended_fix")
        if recommended_fix:
            recommended_fixes.append(recommended_fix)
        score -= _severity_penalty(str(rule.get("severity", "medium")))
        if bool(rule.get("blocks_ready_if_present", False)):
            blockers.append(item)
        else:
            warnings.append(item)

    score = max(0, min(100, score))
    detected_risks = _dedupe_preserve_order(detected_risks)
    recommended_fixes = _dedupe_preserve_order(recommended_fixes)

    blocker_ids = {item["check"] for item in blockers}
    warning_ids = {item["check"] for item in warnings}
    if not blockers and not warnings:
        status = "pass"
        redesign_level = "none"
    elif blockers:
        status = "not_ready"
        if "brutalism_misapplied" in blocker_ids or {"wireframe_look", "amateur_internal_tool_look"} <= blocker_ids or len(blockers) >= 4:
            redesign_level = "full_redesign"
        elif blocker_ids & {
            "border_weight_excessive",
            "shadow_style_heavy",
            "weak_color_system",
            "typography_without_intent",
            "amateur_internal_tool_look",
        }:
            redesign_level = "visual_system_refactor"
        elif blocker_ids & {
            "weak_visual_hierarchy",
            "weak_button_hierarchy",
            "poor_spacing",
            "excessive_horizontal_spread",
        }:
            redesign_level = "layout_refactor"
        else:
            redesign_level = "minor_polish"
    else:
        status = "needs_attention"
        if warning_ids & {"card_repetition", "excessive_horizontal_spread", "generic_dashboard_pattern"}:
            redesign_level = "layout_refactor"
        else:
            redesign_level = "minor_polish"

    why_parts: List[str] = []
    if blockers:
        why_parts.append(
            "Visual blockers remain: " + ", ".join(item["check"] for item in blockers[:4]) + "."
        )
    if warnings:
        why_parts.append(
            "Advisory visual warnings remain: " + ", ".join(item["check"] for item in warnings[:4]) + "."
        )
    if not why_parts:
        why_parts.append("No strong visual-quality blockers were detected from the available design signals.")

    return {
        "status": status,
        "ready_for_handoff": status == "pass",
        "blockers": blockers,
        "warnings": warnings,
        "visual_quality_score": score,
        "detected_risks": detected_risks,
        "recommended_fixes": recommended_fixes[:8],
        "required_redesign_level": redesign_level,
        "why": " ".join(why_parts),
        "advisory_only": bool(rules.get("advisory_only", True)),
    }


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(add_help=True)
    parser.add_argument("--payload-json", required=True)
    args = parser.parse_args(argv)
    payload = json.loads(args.payload_json)
    result = audit_design_quality(payload, root=DEFAULT_ROOT)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
