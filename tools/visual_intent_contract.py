from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any, Dict, List, Optional


DEFAULT_ROOT = Path(__file__).resolve().parents[1]
RULES_PATH = Path("config/visual_intent_contract_rules.json")

AUDIENCE_TERMS = (
    "for developers",
    "for teams",
    "for operators",
    "for founders",
    "for internal teams",
    "for product teams",
    "for technical teams",
    "audience",
)
MOOD_TERMS = (
    "editorial",
    "minimal",
    "luxury",
    "brutalist",
    "immersive",
    "playful",
    "industrial",
    "swiss",
    "monochrome",
    "cinematic",
    "warm",
    "calm",
    "sharp",
    "bold",
    "soft",
    "premium",
    "serious",
    "mood",
    "vibe",
    "tone",
)
ORIGINALITY_TERMS = {
    "conservative": ("conservative",),
    "balanced": ("balanced",),
    "distinctive": ("distinctive", "differentiated", "non-generic"),
    "experimental": ("experimental",),
}
HERO_DIRECTION_TERMS = (
    "hero",
    "headline",
    "above the fold",
    "factory",
    "system",
    "governance",
    "architecture",
    "control",
    "anti-chaos",
)
CTA_INTENT_TERMS = (
    "start setup",
    "create first project",
    "contact",
    "get started",
    "view roadmap",
    "explore architecture",
    "audit",
    "certify",
)
VISUAL_DENSITY_TERMS = {
    "low": ("minimal", "spacious", "airy", "quiet"),
    "medium": ("balanced", "editorial", "structured"),
    "high": ("dense", "packed", "layered", "immersive"),
}
MOTION_INTENSITY_TERMS = {
    "low": ("subtle motion", "low motion", "minimal motion", "calm"),
    "medium": ("balanced motion", "measured motion", "medium motion"),
    "high": ("immersive motion", "high motion", "kinetic", "bold animation"),
}
TYPOGRAPHY_INTENT_TERMS = (
    "serif",
    "sans",
    "monospace",
    "editorial typography",
    "industrial typography",
    "expressive typography",
    "geometric",
)
COLOR_STRATEGY_TERMS = (
    "monochrome",
    "warm neutrals",
    "high contrast",
    "deep teal",
    "muted palette",
    "bold accent",
    "earth tone",
    "cool neutral",
)
ANTI_PATTERN_TERMS = (
    "avoid generic",
    "avoid saas",
    "avoid template",
    "avoid pdf",
    "avoid readme",
    "anti-pattern",
    "no teal",
    "no inter",
)
EVIDENCE_EXPECTATION_TERMS = (
    "evidence",
    "proof",
    "before pass",
    "before calling it done",
    "audit",
    "certify",
    "validation",
)
GENERIC_PROMISE_TERMS = (
    "something useful",
    "look good",
    "nice website",
    "modern site",
)


def _normalize(text: str) -> str:
    return re.sub(r"\s+", " ", (text or "").lower()).strip()


def _strip_html(text: str) -> str:
    text = re.sub(r"<[^>]+>", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def _extract_first_meaningful_sentence(text: str) -> Optional[str]:
    cleaned = _strip_html(text)
    if not cleaned:
        return None
    parts = re.split(r"(?<=[.!?])\s+", cleaned)
    for part in parts:
        candidate = part.strip()
        if len(candidate.split()) >= 5:
            return candidate
    return cleaned[:180].strip() if cleaned else None


def _extract_first_heading(text: str) -> Optional[str]:
    for pattern in (
        r"<h1\b[^>]*>(.*?)</h1>",
        r"^#\s+(.+)$",
        r"^##\s+(.+)$",
    ):
        match = re.search(pattern, text, flags=re.IGNORECASE | re.MULTILINE | re.DOTALL)
        if match:
            heading = _strip_html(match.group(1)).strip()
            if heading:
                return heading
    return None


def _keyword_hits(normalized_text: str, terms: tuple[str, ...]) -> List[str]:
    return [term for term in terms if term in normalized_text]


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


def load_visual_intent_contract_rules(root: Path = DEFAULT_ROOT) -> Dict[str, Any]:
    path = root / RULES_PATH
    return json.loads(path.read_text(encoding="utf-8-sig"))


def requires_visual_intent_contract(
    *,
    project_type: Optional[str],
    source_text: str = "",
    surface_paths: Optional[List[str]] = None,
    root: Path = DEFAULT_ROOT,
) -> bool:
    rules = load_visual_intent_contract_rules(root)
    project_type_value = str(project_type or "").strip()
    if project_type_value in set(rules.get("backend_exempt_project_types", [])):
        return False
    if project_type_value in set(rules.get("required_for_project_types", [])):
        return True
    normalized_text = _normalize(source_text)
    ui_signals = tuple(rules.get("ui_surface_signals", []))
    if any(signal in normalized_text for signal in ui_signals):
        return True
    if surface_paths and any(Path(path).name.lower() == "index.html" for path in surface_paths):
        return True
    return False


def _first_match_from_map(normalized_text: str, mapping: Dict[str, tuple[str, ...]]) -> Optional[str]:
    for key, terms in mapping.items():
        if any(term in normalized_text for term in terms):
            return key
    return None


def infer_visual_intent_contract(
    *,
    project_type: Optional[str],
    brief: Optional[str] = None,
    surface: Optional[Dict[str, str]] = None,
    metadata: Optional[Dict[str, Any]] = None,
    objective: Optional[str] = None,
) -> Dict[str, Any]:
    source_text = brief or "\n".join((surface or {}).values())
    normalized_text = _normalize(source_text)
    audience_hits = _keyword_hits(normalized_text, AUDIENCE_TERMS)
    mood_hits = _keyword_hits(normalized_text, MOOD_TERMS)
    originality_level = _first_match_from_map(normalized_text, ORIGINALITY_TERMS)
    hero_direction = None
    if surface and surface.get("index.html"):
        hero_direction = _extract_first_heading(surface.get("index.html", ""))
    if not hero_direction:
        for term in HERO_DIRECTION_TERMS:
            if term in normalized_text:
                hero_direction = term
                break
    problem_or_promise = None
    if metadata:
        goal = str(metadata.get("project_goal", "")).strip()
        if goal:
            problem_or_promise = goal[:240]
    if not problem_or_promise:
        problem_or_promise = objective[:240] if objective else _extract_first_meaningful_sentence(source_text)
    contract = {
        "audience": audience_hits[0] if audience_hits else None,
        "project_type": project_type,
        "problem_or_promise": problem_or_promise,
        "mood_or_vibe": mood_hits[0] if mood_hits else None,
        "originality_level": originality_level,
        "hero_direction": hero_direction,
        "primary_cta_intent": next((term for term in CTA_INTENT_TERMS if term in normalized_text), None),
        "visual_density": _first_match_from_map(normalized_text, VISUAL_DENSITY_TERMS),
        "motion_intensity": _first_match_from_map(normalized_text, MOTION_INTENSITY_TERMS),
        "typography_intent": next((term for term in TYPOGRAPHY_INTENT_TERMS if term in normalized_text), None),
        "color_strategy": next((term for term in COLOR_STRATEGY_TERMS if term in normalized_text), None),
        "anti_patterns_to_avoid": _dedupe_preserve_order(_keyword_hits(normalized_text, ANTI_PATTERN_TERMS)),
        "evidence_expectations": _dedupe_preserve_order(_keyword_hits(normalized_text, EVIDENCE_EXPECTATION_TERMS)),
    }
    return contract


def validate_visual_intent_contract(
    contract: Dict[str, Any],
    *,
    project_type: Optional[str],
    source_text: str = "",
    surface_paths: Optional[List[str]] = None,
    root: Path = DEFAULT_ROOT,
) -> Dict[str, Any]:
    rules = load_visual_intent_contract_rules(root)
    requires_contract = requires_visual_intent_contract(
        project_type=project_type,
        source_text=source_text,
        surface_paths=surface_paths,
        root=root,
    )
    if not requires_contract:
        return {
            "status": "skipped",
            "missing_fields": [],
            "weak_fields": [],
            "anti_generic_risks": [],
            "requires_human_clarification": False,
            "recommended_questions": [],
            "evidence_expectations": list(rules.get("minimum_evidence_expectations", [])),
            "why": "This project does not currently look like a landing/web/UI surface that requires a visual intent contract.",
            "requires_contract": False,
            "contract": contract,
            "required_fields": list(rules.get("required_fields", [])),
            "advisory_only": bool(rules.get("advisory_only", True)),
        }

    required_fields = list(rules.get("required_fields", []))
    missing_fields: List[str] = []
    weak_fields: List[str] = []
    anti_generic_risks: List[str] = []
    recommended_questions: List[str] = []

    for field_name in required_fields:
        value = contract.get(field_name)
        if value is None or (isinstance(value, str) and not value.strip()) or (isinstance(value, list) and not value):
            missing_fields.append(field_name)

    allowed_originality = set(rules.get("allowed_originality_levels", []))
    allowed_motion = set(rules.get("allowed_motion_intensity", []))
    allowed_density = set(rules.get("allowed_visual_density", []))
    if contract.get("originality_level") and contract["originality_level"] not in allowed_originality:
        weak_fields.append("originality_level")
    if contract.get("motion_intensity") and contract["motion_intensity"] not in allowed_motion:
        weak_fields.append("motion_intensity")
    if contract.get("visual_density") and contract["visual_density"] not in allowed_density:
        weak_fields.append("visual_density")

    problem_or_promise = str(contract.get("problem_or_promise") or "").strip()
    min_words = int((rules.get("weak_field_rules") or {}).get("problem_or_promise_min_words", 5))
    if problem_or_promise and len(problem_or_promise.split()) < min_words:
        weak_fields.append("problem_or_promise")
    if any(term in _normalize(problem_or_promise) for term in GENERIC_PROMISE_TERMS):
        anti_generic_risks.append("generic_problem_or_promise")

    if not contract.get("originality_level"):
        anti_generic_risks.append("missing_originality_level")
    if not contract.get("anti_patterns_to_avoid"):
        anti_generic_risks.append("missing_anti_patterns")
    if not contract.get("typography_intent"):
        anti_generic_risks.append("missing_typography_intent")
    if not contract.get("color_strategy"):
        anti_generic_risks.append("missing_color_strategy")
    if not contract.get("primary_cta_intent"):
        anti_generic_risks.append("missing_primary_cta_intent")

    question_map = {
        "audience": "Who is the primary audience for this interface?",
        "project_type": "What kind of UI surface is this: landing, app, dashboard or another interface?",
        "problem_or_promise": "What problem or promise should the page communicate first?",
        "mood_or_vibe": "What mood or vibe should the UI communicate?",
        "originality_level": "Should the design be conservative, balanced, distinctive or experimental?",
        "hero_direction": "What should the hero communicate or feel like above the fold?",
        "primary_cta_intent": "What is the one main next action the visitor should take?",
        "visual_density": "Should the page feel low, medium or high density?",
        "motion_intensity": "Should motion feel low, medium or high intensity?",
        "typography_intent": "What typography intent should guide the interface?",
        "color_strategy": "What color strategy should the interface follow?",
        "anti_patterns_to_avoid": "What visual anti-patterns should Atlas explicitly avoid?",
        "evidence_expectations": "What evidence is required before Atlas calls the design pass?",
    }
    for field_name in missing_fields + weak_fields:
        question = question_map.get(field_name)
        if question and question not in recommended_questions:
            recommended_questions.append(question)

    status = "ready"
    if missing_fields or weak_fields:
        status = "needs_input"

    why_parts: List[str] = []
    if missing_fields:
        why_parts.append(f"Missing contract fields: {', '.join(missing_fields)}.")
    if weak_fields:
        why_parts.append(f"Weak or invalid fields: {', '.join(_dedupe_preserve_order(weak_fields))}.")
    if anti_generic_risks:
        why_parts.append(f"Anti-generic risks: {', '.join(_dedupe_preserve_order(anti_generic_risks))}.")
    if not why_parts:
        why_parts.append("The visual intent contract is explicit enough to support advisory design guidance.")

    return {
        "status": status,
        "missing_fields": missing_fields,
        "weak_fields": _dedupe_preserve_order(weak_fields),
        "anti_generic_risks": _dedupe_preserve_order(anti_generic_risks),
        "requires_human_clarification": bool(missing_fields or weak_fields),
        "recommended_questions": recommended_questions[:6],
        "evidence_expectations": contract.get("evidence_expectations") or list(rules.get("minimum_evidence_expectations", [])),
        "why": " ".join(why_parts),
        "requires_contract": True,
        "contract": contract,
        "required_fields": required_fields,
        "advisory_only": bool(rules.get("advisory_only", True)),
    }


def build_visual_intent_assessment(
    *,
    project_type: Optional[str],
    brief: Optional[str] = None,
    surface: Optional[Dict[str, str]] = None,
    metadata: Optional[Dict[str, Any]] = None,
    objective: Optional[str] = None,
    root: Path = DEFAULT_ROOT,
) -> Dict[str, Any]:
    contract = infer_visual_intent_contract(
        project_type=project_type,
        brief=brief,
        surface=surface,
        metadata=metadata,
        objective=objective,
    )
    return validate_visual_intent_contract(
        contract,
        project_type=project_type,
        source_text=brief or "\n".join((surface or {}).values()),
        surface_paths=list((surface or {}).keys()),
        root=root,
    )


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(add_help=True)
    parser.add_argument("--project-type", default=None)
    parser.add_argument("--brief", default=None)
    parser.add_argument("--contract-json", default=None)
    args = parser.parse_args(argv)

    contract = json.loads(args.contract_json) if args.contract_json else infer_visual_intent_contract(
        project_type=args.project_type,
        brief=args.brief,
    )
    result = validate_visual_intent_contract(
        contract,
        project_type=args.project_type,
        source_text=args.brief or "",
        root=DEFAULT_ROOT,
    )
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
