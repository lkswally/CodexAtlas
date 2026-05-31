from __future__ import annotations

import argparse
import json
import re
from html import unescape
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional


DEFAULT_ROOT = Path(__file__).resolve().parents[1]
RULES_PATH = Path("config/copywriting_conversion_rules.json")


def load_copywriting_conversion_rules(root: Path = DEFAULT_ROOT) -> Dict[str, Any]:
    return json.loads((root / RULES_PATH).read_text(encoding="utf-8-sig"))


def _normalize(value: Any) -> str:
    return " ".join(str(value or "").strip().lower().split())


def _has_value(value: Any) -> bool:
    if value is None:
        return False
    if isinstance(value, str):
        return bool(value.strip())
    if isinstance(value, (list, tuple, set, dict)):
        return bool(value)
    return True


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
    text = _stringify(value)
    if not text:
        return []
    return [part.strip() for part in re.split(r"[,|\n]+", text) if part.strip()]


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
    if "backend_real_available" in payload:
        extracted["backend_real_available"] = bool(payload.get("backend_real_available"))
    return extracted


def _candidate_files(project: Path, rules: Dict[str, Any]) -> List[Path]:
    ordered: List[Path] = []
    seen: set[Path] = set()
    for relative in rules.get("project_scan_files", []):
        candidate = project / str(relative)
        if candidate.exists() and candidate.is_file() and candidate not in seen:
            seen.add(candidate)
            ordered.append(candidate)
    for pattern in ("*.html", "*.md", "app/*.tsx", "app/*.jsx", "pages/*.tsx", "pages/*.jsx"):
        for candidate in sorted(project.glob(pattern)):
            if candidate.is_file() and candidate not in seen:
                seen.add(candidate)
                ordered.append(candidate)
    return ordered[:12]


def _read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        return path.read_text(encoding="latin-1")


def _strip_html(raw_text: str) -> str:
    text = re.sub(r"<script\b[^>]*>.*?</script>", " ", raw_text, flags=re.IGNORECASE | re.DOTALL)
    text = re.sub(r"<style\b[^>]*>.*?</style>", " ", text, flags=re.IGNORECASE | re.DOTALL)
    text = re.sub(r"<[^>]+>", " ", text)
    return re.sub(r"\s+", " ", unescape(text)).strip()


def _extract_html_matches(raw_text: str, pattern: str) -> List[str]:
    matches = re.findall(pattern, raw_text, flags=re.IGNORECASE | re.DOTALL)
    cleaned: List[str] = []
    for match in matches:
        text = _strip_html(match)
        if text:
            cleaned.append(text)
    return cleaned


def _scan_project_copy_surface(project: Path, rules: Dict[str, Any]) -> Dict[str, Any]:
    files = _candidate_files(project, rules)
    page_parts: List[str] = []
    hero_lines: List[str] = []
    cta_labels: List[str] = []
    form_parts: List[str] = []
    source_files: List[str] = []

    for path in files:
        raw_text = _read_text(path)
        source_files.append(str(path.relative_to(project)).replace("\\", "/"))
        if path.suffix.lower() == ".html":
            page_parts.append(_strip_html(raw_text))
            hero_lines.extend(_extract_html_matches(raw_text, r"<h1[^>]*>(.*?)</h1>"))
            hero_lines.extend(_extract_html_matches(raw_text, r"<h2[^>]*>(.*?)</h2>")[:1])
            cta_labels.extend(_extract_html_matches(raw_text, r"<a[^>]*>(.*?)</a>"))
            cta_labels.extend(_extract_html_matches(raw_text, r"<button[^>]*>(.*?)</button>"))
            form_parts.extend(_extract_html_matches(raw_text, r"<form\b[^>]*>(.*?)</form>"))
        else:
            text = re.sub(r"\s+", " ", raw_text).strip()
            if text:
                page_parts.append(text)
            if not hero_lines:
                heading = re.search(r"^\s*#\s+(.+)$", raw_text, flags=re.MULTILINE)
                if heading:
                    hero_lines.append(heading.group(1).strip())

    cleaned_ctas: List[str] = []
    for label in cta_labels:
        label = re.sub(r"\s+", " ", label).strip()
        if label and len(label) <= 90 and label not in cleaned_ctas:
            cleaned_ctas.append(label)

    return {
        "page_text": " ".join(part for part in page_parts if part)[:20000],
        "hero_text": " ".join(hero_lines[:3]).strip(),
        "cta_labels": cleaned_ctas[:8],
        "form_microcopy": " ".join(form_parts).strip()[:4000],
        "form_present": bool(form_parts),
        "source_files": source_files,
    }


def _project_is_copy_surface(project_type: str, project: Path, scanned: Dict[str, Any], rules: Dict[str, Any]) -> bool:
    normalized_type = _normalize(project_type)
    if normalized_type in {_normalize(item) for item in rules.get("applicable_project_types", [])}:
        return True
    return bool(scanned.get("hero_text") or scanned.get("cta_labels") or (project / "index.html").exists())


def _contains_any(surface: str, phrases: Iterable[str]) -> List[str]:
    normalized_surface = _normalize(surface)
    return [str(phrase).strip() for phrase in phrases if str(phrase).strip() and _normalize(phrase) in normalized_surface]


def _audience_visible(surface: str, audience: str, rules: Dict[str, Any]) -> bool:
    if audience:
        return True
    normalized_surface = _normalize(surface)
    audience_terms = [re.escape(str(item).strip()) for item in rules.get("audience_keywords", []) if str(item).strip()]
    if audience_terms:
        pattern = rf"\b(for|para)\b[^.:\n]{{0,80}}\b({'|'.join(audience_terms)})\b"
        if re.search(pattern, normalized_surface):
            return True
    return any(_normalize(item) in normalized_surface for item in rules.get("audience_keywords", []))


def _problem_visible(surface: str, problem: str, rules: Dict[str, Any]) -> bool:
    if problem:
        return True
    normalized_surface = _normalize(surface)
    return any(_normalize(item) in normalized_surface for item in rules.get("problem_keywords", []))


def _value_visible(surface: str, value_proposition: str, rules: Dict[str, Any]) -> bool:
    if value_proposition:
        return True
    normalized_surface = _normalize(surface)
    return any(_normalize(item) in normalized_surface for item in rules.get("value_keywords", []))


def _cta_clear(cta_labels: List[str], rules: Dict[str, Any]) -> bool:
    if not cta_labels:
        return False
    strong = {_normalize(item) for item in rules.get("strong_cta_terms", [])}
    for label in cta_labels:
        normalized = _normalize(label)
        if any(term and term in normalized for term in strong):
            return True
    return False


def _cta_confusing(cta_labels: List[str], rules: Dict[str, Any]) -> bool:
    if not cta_labels:
        return True
    strong = {_normalize(item) for item in rules.get("strong_cta_terms", [])}
    weak = {_normalize(item) for item in rules.get("weak_cta_terms", [])}
    if any(any(term and term in _normalize(label) for term in strong) for label in cta_labels):
        return False
    return any(any(term and term in _normalize(label) for term in weak) for label in cta_labels)


def _clamp(score: int) -> int:
    return max(0, min(100, score))


def assess_copywriting_conversion_readiness(
    payload: Dict[str, Any],
    *,
    root: Path = DEFAULT_ROOT,
    project: Optional[Path] = None,
) -> Dict[str, Any]:
    root = root.resolve()
    project = (project or root).resolve()
    rules = load_copywriting_conversion_rules(root)
    extracted = _extract_inputs(payload, rules)
    scanned = _scan_project_copy_surface(project, rules) if project.exists() else {}

    target_audience = _stringify(extracted.get("target_audience"))
    problem = _stringify(extracted.get("problem"))
    value_proposition = _stringify(extracted.get("value_proposition"))
    hero_text = _stringify(extracted.get("hero_text") or scanned.get("hero_text"))
    page_text = _stringify(extracted.get("page_text") or scanned.get("page_text"))
    cta_labels = _listify(extracted.get("cta_labels") or scanned.get("cta_labels"))
    next_step = _stringify(extracted.get("next_step"))
    form_microcopy = _stringify(extracted.get("form_microcopy") or scanned.get("form_microcopy"))
    data_handling = _stringify(extracted.get("data_handling"))
    proof_points = _stringify(extracted.get("proof_points"))
    brand_tone = _stringify(extracted.get("brand_tone"))
    backend_real_available = bool(extracted.get("backend_real_available", False))
    form_present = bool(scanned.get("form_present")) or bool(form_microcopy)
    form_surface = " ".join(part for part in [next_step, form_microcopy, data_handling] if part)

    surface = " ".join(
        part
        for part in [
            hero_text,
            page_text,
            target_audience,
            problem,
            value_proposition,
            next_step,
            form_microcopy,
            data_handling,
            proof_points,
            brand_tone,
            " ".join(cta_labels),
        ]
        if part
    )

    if not _project_is_copy_surface(_stringify(extracted.get("project_type")), project, scanned, rules):
        return {
            "status": "ok",
            "copy_readiness_state": "not_applicable",
            "clarity_score": 0,
            "conversion_score": 0,
            "trust_score": 0,
            "tone_consistency_score": 0,
            "hero_message": {
                "clear_for_target_audience": False,
                "problem_visible": False,
                "value_proposition_visible": False,
                "cta_clear": False
            },
            "warnings": [],
            "risks": [],
            "missing_inputs": [],
            "recommended_changes": [],
            "must_not_claim": [],
            "recommended_next_step": "Copywriting conversion readiness is only relevant for frontend or landing-like surfaces.",
            "source_files": scanned.get("source_files", []),
            "why": "Atlas did not detect a frontend or landing surface that needs copy evaluation.",
            "advisory_only": True,
        }

    blocked_claims = _contains_any(surface, rules.get("blocked_claim_terms", []))
    instant_claims = _contains_any(surface, rules.get("instant_diagnosis_terms", []))
    generic_phrases = _contains_any(surface, rules.get("generic_ai_phrases", []))
    aggressive_phrases = _contains_any(surface, rules.get("aggressive_sales_phrases", []))

    audience_visible = _audience_visible(surface, target_audience, rules)
    problem_visible = _problem_visible(surface, problem, rules)
    value_visible = _value_visible(surface, value_proposition, rules)
    cta_is_clear = _cta_clear(cta_labels, rules)
    cta_is_confusing = _cta_confusing(cta_labels, rules)
    next_step_clear = bool(next_step) or bool(_contains_any(form_surface, rules.get("form_follow_up_terms", [])))
    consent_clear = (not form_present) or bool(data_handling) or bool(_contains_any(form_surface, rules.get("consent_terms", [])))
    trust_boundary_present = bool(proof_points) or bool(_contains_any(surface, rules.get("trust_terms", [])))

    hero_clear = bool(hero_text) and len(hero_text.split()) <= 24 and (audience_visible or value_visible) and cta_is_clear
    cta_promises_too_much = bool(blocked_claims) or (bool(instant_claims) and not backend_real_available)
    cta_alignment_clear = cta_is_clear and not cta_promises_too_much

    clarity_score = _clamp(
        (25 if audience_visible else 0)
        + (25 if problem_visible else 0)
        + (25 if value_visible else 0)
        + (25 if hero_clear else 0)
    )
    conversion_score = _clamp(
        (30 if cta_is_clear else 0)
        + (25 if next_step_clear else 0)
        + (25 if cta_alignment_clear else 0)
        + (20 if (not form_present or consent_clear) else 0)
    )
    trust_score = _clamp(
        100
        - (55 if blocked_claims else 0)
        - (35 if instant_claims and not backend_real_available else 0)
        - (20 if generic_phrases else 0)
        - (15 if aggressive_phrases else 0)
        - (15 if form_present and not consent_clear else 0)
        - (10 if not trust_boundary_present else 0)
    )
    tone_consistency_score = _clamp(
        100
        - (35 if generic_phrases else 0)
        - (25 if aggressive_phrases else 0)
        - (20 if cta_is_confusing else 0)
        - (10 if not hero_text else 0)
    )

    warnings: List[str] = []
    risks: List[Dict[str, str]] = []
    missing_inputs: List[str] = []
    recommended_changes: List[str] = []
    must_not_claim: List[str] = []

    if not audience_visible:
        missing_inputs.append("target_audience")
        warnings.append("The copy does not clearly say who the page is for.")
        recommended_changes.append("Name the target audience explicitly in the hero or the first supporting paragraph.")
    if not problem_visible:
        missing_inputs.append("problem")
        warnings.append("The problem is not visible fast enough in the current copy.")
        recommended_changes.append("State the pain or friction the product resolves within the first screen.")
    if not value_visible:
        missing_inputs.append("value_proposition")
        warnings.append("The value proposition is still too implicit.")
        recommended_changes.append("Add a direct sentence that explains what the product does and why it matters.")
    if cta_is_confusing:
        warnings.append("The CTA is vague or too generic for a conversion-oriented page.")
        recommended_changes.append("Replace vague CTA labels with a concrete next action tied to the real workflow.")
    if form_present and not next_step_clear:
        warnings.append("The form does not explain clearly what happens after submission.")
        recommended_changes.append("Explain the next step after form submission in one short sentence near the form CTA.")
    if form_present and not consent_clear:
        warnings.append("The page collects user data without clear privacy or consent language.")
        recommended_changes.append("Add concise privacy or consent microcopy near the form action.")
    if generic_phrases:
        warnings.append("The copy still contains generic AI-style filler instead of specific value.")
        recommended_changes.append("Replace generic AI phrasing with concrete, product-specific language.")
        risks.append(
            {
                "severity": "medium",
                "type": "generic_copy",
                "message": f"Generic phrases detected: {', '.join(generic_phrases[:3])}."
            }
        )
    if aggressive_phrases:
        warnings.append("The tone leans too hard into sales pressure and weakens trust.")
        recommended_changes.append("Use direct, professional language instead of urgency-based pressure.")
        risks.append(
            {
                "severity": "medium",
                "type": "aggressive_tone",
                "message": f"Aggressive phrases detected: {', '.join(aggressive_phrases[:3])}."
            }
        )
    if blocked_claims:
        must_not_claim.extend(blocked_claims)
        warnings.append("The copy includes commercial claims Atlas must block.")
        recommended_changes.append("Remove guaranteed-outcome claims and replace them with realistic, bounded language.")
        risks.append(
            {
                "severity": "high",
                "type": "unsupported_claim",
                "message": f"Blocked commercial claim detected: {', '.join(blocked_claims[:3])}."
            }
        )
    if instant_claims and not backend_real_available:
        must_not_claim.extend(instant_claims)
        warnings.append("The page implies instant diagnosis or instant output without real backend support.")
        recommended_changes.append("Avoid promising instant diagnosis until a real backend supports that claim.")
        risks.append(
            {
                "severity": "high",
                "type": "capability_mismatch",
                "message": f"Instant-diagnosis language detected without backend support: {', '.join(instant_claims[:3])}."
            }
        )
    if not trust_boundary_present:
        warnings.append("The copy lacks a trust boundary or scope clarification.")
        recommended_changes.append("Add one short sentence that clarifies limits, review steps or human involvement.")

    thresholds = rules.get("ready_thresholds", {})
    blocked = bool(blocked_claims) or (bool(instant_claims) and not backend_real_available)
    if blocked:
        copy_readiness_state = "blocked"
    elif (
        clarity_score >= int(thresholds.get("clarity_score", 75))
        and conversion_score >= int(thresholds.get("conversion_score", 70))
        and trust_score >= int(thresholds.get("trust_score", 75))
        and tone_consistency_score >= int(thresholds.get("tone_consistency_score", 70))
        and not warnings
    ):
        copy_readiness_state = "ready"
    else:
        copy_readiness_state = "needs_improvement"

    recommended_next_step = (
        "Remove blocked or unsupported claims before treating this page as externally ready."
        if blocked
        else "Tighten the hero, CTA and objection-handling copy before calling the surface conversion-ready."
        if warnings
        else "The copy is coherent enough to proceed to human review."
    )

    return {
        "status": "ok",
        "copy_readiness_state": copy_readiness_state,
        "clarity_score": clarity_score,
        "conversion_score": conversion_score,
        "trust_score": trust_score,
        "tone_consistency_score": tone_consistency_score,
        "hero_message": {
            "clear_for_target_audience": audience_visible and hero_clear,
            "problem_visible": problem_visible,
            "value_proposition_visible": value_visible,
            "cta_clear": cta_is_clear
        },
        "warnings": warnings,
        "risks": risks,
        "missing_inputs": missing_inputs,
        "recommended_changes": list(dict.fromkeys(recommended_changes)),
        "must_not_claim": list(dict.fromkeys(must_not_claim)),
        "recommended_next_step": recommended_next_step,
        "source_files": scanned.get("source_files", []),
        "why": (
            "Atlas found copy risks that still weaken clarity, trust or conversion."
            if warnings or blocked
            else "The current copy looks structurally clear, realistic and aligned with the next action."
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
    result = assess_copywriting_conversion_readiness(payload, root=DEFAULT_ROOT, project=project)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
