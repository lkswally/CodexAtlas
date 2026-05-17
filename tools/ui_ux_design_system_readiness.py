from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Dict, List, Optional


DEFAULT_ROOT = Path(__file__).resolve().parents[1]
RULES_PATH = Path("config/ui_ux_design_system_rules.json")


def _read_json(path: Path) -> Dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def load_ui_ux_design_system_rules(root: Path = DEFAULT_ROOT) -> Dict[str, Any]:
    return _read_json(root / RULES_PATH)


def _normalize_text(value: Any) -> str:
    return str(value or "").strip()


def _normalize_stack(value: Any) -> str:
    raw = _normalize_text(value).lower().replace("_", "-")
    aliases = {
        "next.js": "nextjs",
        "next": "nextjs",
        "react+vite": "react-vite",
        "vite+react": "react-vite",
        "html+tailwind": "html-tailwind",
    }
    return aliases.get(raw, raw)


def _extract_contract_value(contract: Dict[str, Any], key: str) -> str:
    if not isinstance(contract, dict):
        return ""
    return _normalize_text(contract.get(key))


def _match_profile(rules: Dict[str, Any], product_text: str) -> Dict[str, Any]:
    normalized = product_text.lower()
    best_profile: Optional[Dict[str, Any]] = None
    best_score = -1
    for profile in rules.get("product_profiles", []):
        if not isinstance(profile, dict):
            continue
        terms = [str(term).strip().lower() for term in profile.get("match_terms", []) if str(term).strip()]
        score = sum(1 for term in terms if term and term in normalized)
        if score > best_score:
            best_score = score
            best_profile = profile
    return dict(best_profile or {})


def _audience_modifiers(rules: Dict[str, Any], audience: str) -> Dict[str, Any]:
    normalized = audience.lower()
    matches: List[Dict[str, Any]] = []
    for key, modifier in (rules.get("audience_modifiers") or {}).items():
        if key in normalized and isinstance(modifier, dict):
            matches.append(modifier)
    anti_patterns: List[str] = []
    style_shift: List[str] = []
    for modifier in matches:
        shift = _normalize_text(modifier.get("style_shift"))
        if shift:
            style_shift.append(shift)
        for item in modifier.get("anti_patterns", []):
            value = _normalize_text(item)
            if value and value not in anti_patterns:
                anti_patterns.append(value)
    return {
        "style_shift": "; ".join(style_shift),
        "anti_patterns": anti_patterns,
    }


def _frontend_motion_posture(
    *,
    rules: Dict[str, Any],
    project_type: str,
    stack: str,
    motion_signals: List[str],
) -> str:
    motion_rules = rules.get("motion_library_posture") or {}
    react_eligible = {str(item).strip().lower() for item in motion_rules.get("react_eligible_stacks", [])}
    css_first = {str(item).strip().lower() for item in motion_rules.get("css_first_stacks", [])}
    frontend_project_types = {str(item).strip().lower() for item in rules.get("frontend_project_types", [])}

    if project_type.lower() not in frontend_project_types:
        return "not_required"
    if stack in react_eligible and motion_signals:
        return "recommended_for_react"
    if stack in css_first and not motion_signals:
        return "css_sufficient"
    if stack and stack not in react_eligible and motion_signals:
        return "watchlist"
    if not stack and motion_signals:
        return "watchlist"
    if stack in css_first:
        return "css_sufficient"
    return "not_required"


def _stack_recommendation(
    *,
    stack: str,
    profile_recommendation: str,
    motion_posture: str,
) -> str:
    if motion_posture == "recommended_for_react":
        return "Current React-compatible stack can justify a motion library, but only in the derived project and only with explicit approval."
    if motion_posture == "css_sufficient":
        return "Keep motion CSS-first in the derived project; a JS animation library is not justified yet."
    if motion_posture == "watchlist":
        return "Motion needs look richer than basic CSS, but the current stack signal is not strong enough to recommend a React motion library safely."
    if stack:
        return f"Current stack `{stack}` looks sufficient for the current UI direction. {profile_recommendation}"
    return profile_recommendation


def assess_ui_ux_design_system_readiness(
    *,
    payload: Dict[str, Any],
    root: Path = DEFAULT_ROOT,
) -> Dict[str, Any]:
    rules = load_ui_ux_design_system_rules(root)
    visual_contract = payload.get("visual_intent_contract") or {}
    brand_profile = payload.get("brand_profile") or {}

    project_type = _normalize_text(payload.get("project_type")) or _extract_contract_value(visual_contract, "project_type")
    audience = _normalize_text(payload.get("audience")) or _extract_contract_value(visual_contract, "audience") or _normalize_text(brand_profile.get("audience"))
    product_type = (
        _normalize_text(payload.get("product_type"))
        or _normalize_text(payload.get("domain_context"))
        or _normalize_text(payload.get("objective"))
        or project_type
    )
    stack = _normalize_stack(payload.get("stack"))

    missing_inputs: List[str] = []
    for required in rules.get("required_inputs", []):
        if required == "project_type" and not project_type:
            missing_inputs.append("project_type")
        if required == "audience" and not audience:
            missing_inputs.append("audience")

    profile = _match_profile(rules, product_type)
    modifiers = _audience_modifiers(rules, audience)
    motion_signals = [
        name
        for name, enabled in {
            "hero_animated_complex": bool(payload.get("needs_complex_hero_motion")),
            "microinteractions_required": bool(payload.get("needs_microinteractions")),
            "accordion_or_transition_heavy": bool(payload.get("needs_transition_heavy_ui")),
            "scroll_reveal_required": bool(payload.get("needs_scroll_reveal")),
        }.items()
        if enabled
    ]

    motion_posture = _frontend_motion_posture(
        rules=rules,
        project_type=project_type,
        stack=stack,
        motion_signals=motion_signals,
    )

    anti_patterns = []
    for item in profile.get("anti_patterns", []):
        value = _normalize_text(item)
        if value and value not in anti_patterns:
            anti_patterns.append(value)
    for item in modifiers.get("anti_patterns", []):
        if item not in anti_patterns:
            anti_patterns.append(item)

    style = _normalize_text(profile.get("recommended_style"))
    style_shift = _normalize_text(modifiers.get("style_shift"))
    if style_shift:
        style = f"{style}; {style_shift}" if style else style_shift

    status = "ok" if not missing_inputs else "needs_input"
    why = (
        "Atlas can suggest a stronger visual system safely when product type, audience and stack signals are explicit enough to recommend pattern, style, palette, typography and motion without installing anything."
        if not missing_inputs
        else "Atlas should not pretend a design system is explicit when project type or audience are still missing."
    )

    return {
        "status": status,
        "recommended_pattern": _normalize_text(profile.get("recommended_pattern")),
        "recommended_style": style,
        "recommended_palette": _normalize_text(profile.get("recommended_palette")),
        "recommended_typography": _normalize_text(profile.get("recommended_typography")),
        "recommended_motion": _normalize_text(profile.get("recommended_motion")),
        "anti_patterns": anti_patterns,
        "pre_delivery_checklist": list(rules.get("pre_delivery_checklist", [])),
        "stack_recommendation": _stack_recommendation(
            stack=stack,
            profile_recommendation=_normalize_text(profile.get("stack_recommendation")),
            motion_posture=motion_posture,
        ),
        "accessibility_baseline": list(rules.get("accessibility_baseline", [])),
        "frontend_motion_library_posture": motion_posture,
        "motion_signals": motion_signals,
        "missing_inputs": missing_inputs,
        "advisory_only": bool(rules.get("advisory_only", True)),
        "why": why,
    }


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(add_help=True)
    parser.add_argument("--payload", default="{}", help="JSON payload to evaluate.")
    args = parser.parse_args(argv)
    payload = json.loads(args.payload)
    result = assess_ui_ux_design_system_readiness(payload=payload, root=DEFAULT_ROOT)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
