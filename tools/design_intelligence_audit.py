from __future__ import annotations

import argparse
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple


ALLOWED_PROJECT_FILES = (
    "index.html",
    "styles.css",
    "README.md",
    "AGENTS.md",
    "docs/architecture.md",
)
GENERIC_SANS_FONTS = (
    "inter",
    "roboto",
    "open sans",
    "lato",
    "arial",
    "segoe ui",
    "sf pro",
    "helvetica",
)
VISUAL_DIRECTION_TERMS = (
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
    "visual direction",
    "design direction",
)
AUDIENCE_TERMS = (
    "for teams",
    "for operators",
    "for developers",
    "for designers",
    "for product teams",
    "for internal teams",
    "audience",
    "internal tool",
    "b2b",
    "b2c",
    "creatives",
)
ORIGINALITY_TERMS = (
    "originality",
    "distinctive",
    "differentiated",
    "experimental",
    "balanced",
    "conservative",
    "non-generic",
    "original",
)
MOOD_TERMS = (
    "mood",
    "vibe",
    "tone",
    "warm",
    "calm",
    "sharp",
    "bold",
    "soft",
    "premium",
    "serious",
)
CTA_TERMS = (
    "learn more",
    "get started",
    "start",
    "create",
    "audit",
    "certify",
    "open",
    "read",
    "view",
    "contact",
)
VALUE_PROPOSITION_TERMS = (
    "factory",
    "configuration",
    "bootstrap",
    "audit",
    "certify",
    "governed",
    "structured",
    "reduce",
    "chaos",
    "quality",
    "boundaries",
)
DOCUMENTATION_SECTION_TERMS = (
    "installation",
    "configure",
    "prompt",
    "example prompts",
    "common mistakes",
    "first project",
    "how atlas works",
)
LANDING_SECTION_TERMS = (
    "what is",
    "why",
    "benefits",
    "real examples",
    "contact",
    "results",
)
PLACEHOLDER_LINK_TERMS = (
    "pegar_aca",
    "tu-usuario",
    "example.com",
    "todo",
    "placeholder",
)


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _normalize(value: str) -> str:
    return re.sub(r"\s+", " ", value.lower()).strip()


def _read_text_if_exists(path: Path) -> str:
    if not path.exists():
        return ""
    return path.read_text(encoding="utf-8")


def _load_project_surface(project: Path) -> Dict[str, str]:
    return {relative_path: _read_text_if_exists(project / relative_path) for relative_path in ALLOWED_PROJECT_FILES}


def _extract_css_font_families(css_text: str) -> List[str]:
    matches = re.findall(r"font-family\s*:\s*([^;]+);", css_text, flags=re.IGNORECASE)
    families: List[str] = []
    for raw_match in matches:
        first = raw_match.split(",")[0].strip().strip("'\"")
        if first:
            families.append(first)
    return families


def _extract_css_vars(css_text: str) -> Dict[str, str]:
    return {name: value.strip() for name, value in re.findall(r"(--[a-zA-Z0-9_-]+)\s*:\s*([^;]+);", css_text)}


def _extract_heading_count(html_text: str) -> int:
    return len(re.findall(r"<h[1-3]\b", html_text, flags=re.IGNORECASE))


def _extract_cta_elements(html_text: str) -> List[str]:
    ctas: List[str] = []
    for pattern in (r"<a\b[^>]*>(.*?)</a>", r"<button\b[^>]*>(.*?)</button>"):
        for raw in re.findall(pattern, html_text, flags=re.IGNORECASE | re.DOTALL):
            text = re.sub(r"<[^>]+>", " ", raw)
            cleaned = re.sub(r"\s+", " ", text).strip()
            if cleaned:
                ctas.append(cleaned)
    return ctas


def _strip_html(text: str) -> str:
    text = re.sub(r"<[^>]+>", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def _extract_link_targets(html_text: str) -> List[Dict[str, str]]:
    targets: List[Dict[str, str]] = []
    for match in re.finditer(
        r"<a\b([^>]*)href=\"([^\"]*)\"([^>]*)>(.*?)</a>",
        html_text,
        flags=re.IGNORECASE | re.DOTALL,
    ):
        href = match.group(2).strip()
        label = _strip_html(match.group(4))
        attrs = f"{match.group(1)} {match.group(3)}"
        class_match = re.search(r'class=\"([^\"]+)\"', attrs, flags=re.IGNORECASE)
        targets.append(
            {
                "href": href,
                "label": label,
                "classes": class_match.group(1) if class_match else "",
            }
        )
    return targets


def _extract_section_blocks(html_text: str) -> List[Dict[str, Any]]:
    blocks: List[Dict[str, Any]] = []
    for match in re.finditer(r"<section\b([^>]*)>(.*?)</section>", html_text, flags=re.IGNORECASE | re.DOTALL):
        attrs = match.group(1)
        inner = match.group(2)
        heading_match = re.search(r"<h2\b[^>]*>(.*?)</h2>", inner, flags=re.IGNORECASE | re.DOTALL)
        heading = _strip_html(heading_match.group(1)) if heading_match else ""
        text = _strip_html(inner)
        blocks.append(
            {
                "heading": heading,
                "text": text,
                "word_count": len(re.findall(r"\b[\w-]+\b", text)),
                "list_items": len(re.findall(r"<li\b", inner, flags=re.IGNORECASE)),
                "code_tokens": len(re.findall(r"<code\b", inner, flags=re.IGNORECASE)),
                "has_cta": bool(re.search(r"<a\b", inner, flags=re.IGNORECASE)),
                "classes": attrs,
            }
        )
    return blocks


def _hex_to_rgb(hex_color: str) -> Tuple[float, float, float]:
    hex_value = hex_color.lstrip("#")
    return tuple(int(hex_value[index:index + 2], 16) / 255.0 for index in (0, 2, 4))


def _rgb_to_hsl(rgb: Tuple[float, float, float]) -> Tuple[float, float, float]:
    r, g, b = rgb
    max_color = max(rgb)
    min_color = min(rgb)
    lightness = (max_color + min_color) / 2
    if max_color == min_color:
        return 0.0, 0.0, lightness
    delta = max_color - min_color
    saturation = delta / (1 - abs(2 * lightness - 1))
    if max_color == r:
        hue = ((g - b) / delta) % 6
    elif max_color == g:
        hue = ((b - r) / delta) + 2
    else:
        hue = ((r - g) / delta) + 4
    return hue * 60, saturation, lightness


def _relative_luminance(hex_color: str) -> float:
    rgb = _hex_to_rgb(hex_color)
    normalized = []
    for channel in rgb:
        if channel <= 0.03928:
            normalized.append(channel / 12.92)
        else:
            normalized.append(((channel + 0.055) / 1.055) ** 2.4)
    return 0.2126 * normalized[0] + 0.7152 * normalized[1] + 0.0722 * normalized[2]


def _contrast_ratio(hex_a: str, hex_b: str) -> float:
    lum_a = _relative_luminance(hex_a)
    lum_b = _relative_luminance(hex_b)
    lighter = max(lum_a, lum_b)
    darker = min(lum_a, lum_b)
    return (lighter + 0.05) / (darker + 0.05)


def _has_any(normalized_text: str, terms: Tuple[str, ...]) -> List[str]:
    hits: List[str] = []
    for term in terms:
        pattern = r"(^|[^a-z0-9])" + re.escape(term) + r"([^a-z0-9]|$)"
        if re.search(pattern, normalized_text):
            hits.append(term)
    return hits


def _build_check(
    check_id: str,
    title: str,
    status: str,
    severity: str,
    evidence: List[str],
    recommendation: Optional[str],
    reason: Optional[str] = None,
) -> Dict[str, Any]:
    result = {
        "id": check_id,
        "title": title,
        "status": status,
        "severity": severity,
        "evidence": evidence,
    }
    if recommendation:
        result["recommendation"] = recommendation
    if reason:
        result["reason"] = reason
    return result


def _make_recommendation_source(check: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    recommendation = check.get("recommendation")
    if check["status"] == "pass" or not recommendation:
        return None
    return {
        "recommendation": recommendation,
        "originating_check": check["id"],
        "evidence": check["evidence"][:3],
        "severity": check["severity"],
        "status": check["status"],
    }


def _derive_public_readiness(checks: List[Dict[str, Any]], landing_score: int) -> Tuple[str, List[Dict[str, Any]]]:
    blockers = [
        {
            "check": check["id"],
            "title": check["title"],
            "severity": check["severity"],
            "evidence": check["evidence"][:3],
            "recommendation": check.get("recommendation"),
        }
        for check in checks
        if check["status"] == "fail"
    ]
    if blockers or landing_score < 60:
        return "not_ready", blockers
    if any(check["status"] in {"warning", "skipped"} for check in checks) or landing_score < 90:
        return "needs_improvement", blockers
    return "ready", blockers


def _build_next_action(recommendation_sources: List[Dict[str, Any]], skipped_checks: List[Dict[str, Any]]) -> str:
    actionable_sources = [source for source in recommendation_sources if source["status"] in {"warning", "fail"}]
    if actionable_sources:
        top_sources = actionable_sources[:2]
        actions = [source["recommendation"] for source in top_sources]
        return f"Prioritize these fixes, then re-run the audit: {'; '.join(actions)}"
    if skipped_checks:
        skipped_ids = ", ".join(check["id"] for check in skipped_checks[:3])
        return f"Re-run the audit after making the skipped checks verifiable: {skipped_ids}."
    return "The current static surface is coherent enough for the next iteration."


def _score_from_checks(checks: List[Dict[str, Any]]) -> int:
    score = 100
    for check in checks:
        if check["status"] == "fail":
            score -= 12
        elif check["status"] == "warning":
            score -= 6
        elif check["status"] == "skipped":
            score -= 2
    return max(score, 0)


def visual_direction_checkpoint(task: str) -> Dict[str, Any]:
    normalized = _normalize(task)
    audience_hits = _has_any(normalized, AUDIENCE_TERMS)
    mood_hits = _has_any(normalized, MOOD_TERMS + VISUAL_DIRECTION_TERMS)
    originality_hits = _has_any(normalized, ORIGINALITY_TERMS)
    warnings: List[str] = []
    if not audience_hits:
        warnings.append("audience_missing_or_implicit")
    if not mood_hits:
        warnings.append("mood_or_vibe_missing")
    if not originality_hits:
        warnings.append("originality_level_missing")
    return {
        "status": "ready" if not warnings else "needs_input",
        "warnings": warnings,
        "evidence": [
            f"audience_terms={audience_hits or ['none']}",
            f"mood_terms={mood_hits or ['none']}",
            f"originality_terms={originality_hits or ['none']}",
        ],
        "next_action": (
            "Proceed to design-system review or implementation with the current direction."
            if not warnings
            else "Confirm audience, mood/vibe and originality before UI design work."
        ),
        "checkpoint": {
            "audience": audience_hits[0] if audience_hits else None,
            "mood_or_vibe": mood_hits[0] if mood_hits else None,
            "originality_signal": originality_hits[0] if originality_hits else None,
            "questions": [
                "Who is the primary audience?",
                "What mood or vibe should the interface communicate?",
                "How conservative or experimental should the visual system be?",
                "What should the design explicitly avoid?",
            ],
        },
        "task": task,
        "timestamp": _utc_now_iso(),
    }


def _run_project_visual_analysis(project: Path) -> Dict[str, Any]:
    surface = _load_project_surface(project)
    html_text = surface.get("index.html", "")
    css_text = surface.get("styles.css", "")
    if not html_text or not css_text:
        missing = []
        if not html_text:
            missing.append("index.html")
        if not css_text:
            missing.append("styles.css")
        return {
            "status": "skipped",
            "warnings": [f"missing_project_surface:{item}" for item in missing],
            "evidence": [f"missing_files={missing}"],
            "next_action": "Provide a static HTML/CSS surface or extend the audit helper for the current stack.",
            "checks": [],
            "recommendation_sources": [],
            "score": 0,
            "project": str(project.resolve()),
            "timestamp": _utc_now_iso(),
        }

    content_text = "\n".join(
        value
        for key, value in surface.items()
        if value and key != "styles.css"
    )
    normalized_text = _normalize(content_text)
    audience_hits = _has_any(normalized_text, AUDIENCE_TERMS)
    mood_hits = _has_any(normalized_text, MOOD_TERMS + VISUAL_DIRECTION_TERMS)
    originality_hits = _has_any(normalized_text, ORIGINALITY_TERMS)
    css_vars = _extract_css_vars(css_text)
    fonts = _extract_css_font_families(css_text)
    ctas = _extract_cta_elements(html_text)
    links = _extract_link_targets(html_text)
    section_blocks = _extract_section_blocks(html_text)
    hero_match = re.search(r"<header\b[^>]*class=\"[^\"]*hero[^\"]*\"[^>]*>(.*?)</header>", html_text, flags=re.IGNORECASE | re.DOTALL)
    hero_text = hero_match.group(1) if hero_match else html_text
    hero_plain = _strip_html(hero_text)
    hero_normalized = _normalize(hero_plain)
    heading_count = _extract_heading_count(hero_text)
    heading_font = fonts[0] if fonts else None
    body_font = fonts[1] if len(fonts) > 1 else fonts[0] if fonts else None
    checks: List[Dict[str, Any]] = []

    checks.append(
        _build_check(
            "audience_explicit",
            "Audience is explicit",
            "pass" if audience_hits else "warning",
            "medium" if not audience_hits else "low",
            [f"matched audience terms: {', '.join(audience_hits[:3])}" if audience_hits else "No explicit audience wording found in README, AGENTS or index.html."],
            None if audience_hits else "State who the project is for near the hero and supporting sections.",
        )
    )
    checks.append(
        _build_check(
            "visual_direction_explicit",
            "Visual direction is explicit",
            "pass" if mood_hits else "warning",
            "medium" if not mood_hits else "low",
            [f"matched direction terms: {', '.join(mood_hits[:3])}" if mood_hits else "No explicit visual direction or mood language detected in project-facing content."],
            None if mood_hits else "Add a short visual-direction statement so the site explains its intended aesthetic clearly.",
        )
    )
    checks.append(
        _build_check(
            "originality_level",
            "Originality level is explicit",
            "pass" if originality_hits else "warning",
            "medium" if not originality_hits else "low",
            [f"matched originality terms: {', '.join(originality_hits[:3])}" if originality_hits else "No explicit originality signal found in the current project surface."],
            None if originality_hits else "Say whether the site aims for conservative, balanced or distinctive visual output.",
        )
    )

    hero_identity = "codex-atlas" in hero_normalized or ("atlas" in hero_normalized and "codex" in hero_normalized)
    hero_value_hits = _has_any(hero_normalized, VALUE_PROPOSITION_TERMS)
    hero_audience_hits = _has_any(hero_normalized, AUDIENCE_TERMS)
    above_fold_clarity_ok = hero_identity and bool(hero_value_hits) and bool(hero_audience_hits or audience_hits)
    checks.append(
        _build_check(
            "above_the_fold_clarity",
            "Above-the-fold clarity",
            "pass" if above_fold_clarity_ok else "warning",
            "high" if not above_fold_clarity_ok else "low",
            [
                f"hero_identity={str(hero_identity).lower()}",
                f"hero_value_terms={hero_value_hits or ['none']}",
                f"hero_audience_terms={hero_audience_hits or audience_hits or ['none']}",
            ],
            None if above_fold_clarity_ok else "Make the hero explain in one glance what Atlas is, who it is for and what problem it solves.",
        )
    )

    if heading_font and body_font:
        generic_body = any(font in body_font.lower() for font in GENERIC_SANS_FONTS)
        checks.append(
            _build_check(
                "typography_coherence",
                "Typography coherence",
                "pass" if heading_font.lower() != body_font.lower() and not generic_body else "warning",
                "medium" if generic_body else "low",
                [
                    f"heading_font={heading_font}",
                    f"body_font={body_font}",
                    f"generic_body_font={str(generic_body).lower()}",
                ],
                None if heading_font.lower() != body_font.lower() and not generic_body else "Keep a clear rationale for the serif/sans pairing and consider replacing the generic body sans with a more intentional family.",
            )
        )
    else:
        checks.append(
            _build_check(
                "typography_coherence",
                "Typography coherence",
                "skipped",
                "low",
                ["Could not extract enough font-family declarations from styles.css."],
                "Make typography tokens explicit if the site grows into a richer design system.",
                reason="Not enough font-family declarations were available to compare heading and body typography.",
            )
        )

    layout_status = "pass" if css_vars and "--max" in css_vars and "--line" in css_vars and re.search(r"@media\s*\(max-width:\s*760px\)", css_text) else "warning"
    checks.append(
        _build_check(
            "spacing_layout_coherence",
            "Spacing and layout coherence",
            layout_status,
            "medium" if layout_status == "warning" else "low",
            [
                f"css_tokens_detected={sorted(list(css_vars.keys()))[:6]}",
                f"responsive_breakpoint={str(bool(re.search(r'@media\s*\(max-width:\s*760px\)', css_text))).lower()}",
            ],
            None if layout_status == "pass" else "Promote layout and spacing decisions into clearer reusable tokens if the site grows.",
        )
    )

    normalized_ctas = [_normalize(label) for label in ctas]
    has_cta = any(any(term in label for term in CTA_TERMS) for label in normalized_ctas)
    has_media = bool(re.search(r"<(img|video)\b", hero_text, flags=re.IGNORECASE))
    hero_generic = heading_count == 1 and not has_media and not has_cta
    checks.append(
        _build_check(
            "hero_structure",
            "Hero structure avoids a generic placeholder pattern",
            "warning" if hero_generic else "pass",
            "medium",
            [
                f"heading_count={heading_count}",
                f"hero_has_media={str(has_media).lower()}",
                f"hero_has_cta={str(has_cta).lower()}",
            ],
            None if not hero_generic else "Introduce a clearer action, proof point or visual anchor so the hero feels more intentional.",
        )
    )
    checks.append(
        _build_check(
            "cta_clarity",
            "CTA clarity",
            "pass" if has_cta else "warning",
            "high" if not has_cta else "low",
            [f"detected_ctas={ctas[:3] if ctas else ['none']}"],
            None if has_cta else "Add one clear primary CTA that tells the visitor what to do next.",
        )
    )

    broken_ctas: List[str] = []
    placeholder_ctas: List[str] = []
    next_step_ctas = 0
    for link in links:
        href = link["href"].strip()
        label_normalized = _normalize(link["label"])
        href_normalized = _normalize(href)
        if any(term in label_normalized for term in CTA_TERMS):
            next_step_ctas += 1
        if href in {"", "#"} or href.lower().startswith("javascript:"):
            broken_ctas.append(f"{link['label']} -> {href or 'empty'}")
        elif any(term in href_normalized for term in PLACEHOLDER_LINK_TERMS):
            placeholder_ctas.append(f"{link['label']} -> {href}")
    cta_integrity_status = "pass"
    cta_integrity_recommendation: Optional[str] = None
    if next_step_ctas == 0:
        cta_integrity_status = "fail"
        cta_integrity_recommendation = "Add at least one working next-step CTA that moves the visitor from reading to action."
    elif broken_ctas or placeholder_ctas:
        cta_integrity_status = "warning"
        cta_integrity_recommendation = "Fix placeholder or broken CTA targets before calling the landing publicly ready."
    checks.append(
        _build_check(
            "cta_integrity",
            "CTA integrity",
            cta_integrity_status,
            "high" if cta_integrity_status != "pass" else "low",
            [
                f"next_step_ctas={next_step_ctas}",
                f"broken_ctas={broken_ctas or ['none']}",
                f"placeholder_ctas={placeholder_ctas or ['none']}",
            ],
            cta_integrity_recommendation,
        )
    )

    responsive_ok = bool(re.search(r"<meta[^>]+name=\"viewport\"", html_text, flags=re.IGNORECASE)) and bool(re.search(r"@media\s*\(", css_text, flags=re.IGNORECASE))
    checks.append(
        _build_check(
            "responsive_baseline",
            "Responsive baseline",
            "pass" if responsive_ok else "warning",
            "medium",
            [
                f"viewport_meta={str(bool(re.search(r'<meta[^>]+name=\"viewport\"', html_text, flags=re.IGNORECASE))).lower()}",
                f"media_queries={str(bool(re.search(r'@media\s*\(', css_text, flags=re.IGNORECASE))).lower()}",
            ],
            None if responsive_ok else "Keep at least one explicit mobile breakpoint and verify live behavior in a browser.",
        )
    )

    body_bg = css_vars.get("--bg", "#ffffff").strip()
    body_ink = css_vars.get("--ink", "#111111").strip()
    accent = css_vars.get("--accent", "#000000").strip()
    contrast_score = _contrast_ratio(body_bg, body_ink)
    accent_contrast = _contrast_ratio(css_vars.get("--accent-soft", body_bg).strip(), accent)
    checks.append(
        _build_check(
            "contrast_accessibility",
            "Contrast and visual accessibility sanity",
            "pass" if contrast_score >= 4.5 and accent_contrast >= 3.0 else "warning",
            "medium",
            [
                f"body_contrast={contrast_score:.2f}",
                f"accent_contrast={accent_contrast:.2f}",
                f"body_bg={body_bg}",
                f"accent={accent}",
            ],
            None if contrast_score >= 4.5 and accent_contrast >= 3.0 else "Increase contrast before claiming stronger accessibility quality.",
        )
    )

    accent_hue, accent_saturation, _ = _rgb_to_hsl(_hex_to_rgb(accent))
    teal_like = 160 <= accent_hue <= 205 and accent_saturation >= 0.25
    generic_body = any(font in (body_font or "").lower() for font in GENERIC_SANS_FONTS)
    checks.append(
        _build_check(
            "anti_generic_default",
            "Anti-generic default risk",
            "warning" if teal_like and generic_body else "pass",
            "medium",
            [
                f"accent_hue={accent_hue:.1f}",
                f"accent_saturation={accent_saturation:.2f}",
                f"body_font={body_font or 'none'}",
            ],
            None if not (teal_like and generic_body) else "The palette and body type lean toward a familiar generic pattern; add a clearer visual rationale or a stronger distinctive move.",
        )
    )

    documentation_sections = [
        block for block in section_blocks if any(term in _normalize(block["heading"]) for term in DOCUMENTATION_SECTION_TERMS)
    ]
    landing_sections = [
        block for block in section_blocks if any(term in _normalize(block["heading"]) for term in LANDING_SECTION_TERMS)
    ]
    total_list_items = sum(block["list_items"] for block in section_blocks)
    total_code_tokens = sum(block["code_tokens"] for block in section_blocks)
    landing_balance_warning = len(documentation_sections) > len(landing_sections) and (total_list_items >= 18 or total_code_tokens >= 8)
    checks.append(
        _build_check(
            "landing_vs_documentation_balance",
            "Landing versus documentation balance",
            "warning" if landing_balance_warning else "pass",
            "medium",
            [
                f"documentation_sections={len(documentation_sections)}",
                f"landing_sections={len(landing_sections)}",
                f"list_items={total_list_items}",
                f"code_tokens={total_code_tokens}",
            ],
            None if not landing_balance_warning else "Reduce the README-like density above the fold and keep the public page anchored in narrative, proof and conversion.",
        )
    )

    long_sections = [block for block in section_blocks if block["word_count"] >= 120]
    dense_sections = [
        block for block in section_blocks
        if block["list_items"] >= 5 or block["code_tokens"] >= 3
    ]
    content_density_warning = len(long_sections) >= 3 or len(dense_sections) >= 4
    checks.append(
        _build_check(
            "content_density",
            "Content density stays readable for a landing",
            "warning" if content_density_warning else "pass",
            "medium",
            [
                f"long_sections={len(long_sections)}",
                f"dense_sections={len(dense_sections)}",
                f"total_sections={len(section_blocks)}",
            ],
            None if not content_density_warning else "Trim or split the densest sections so the landing reads like a guided page instead of a static document dump.",
        )
    )

    repetitive_panel_sections = sum(1 for block in section_blocks if "panel" in block["classes"])
    repeated_two_up_groups = len(re.findall(r'class=\"[^\"]*grid[^\"]*two-up[^\"]*\"', html_text, flags=re.IGNORECASE))
    rhythm_warning = repetitive_panel_sections >= 8 and repeated_two_up_groups >= 3 and not has_media
    checks.append(
        _build_check(
            "section_rhythm",
            "Section rhythm and pacing",
            "warning" if rhythm_warning else "pass",
            "low" if not rhythm_warning else "medium",
            [
                f"panel_sections={repetitive_panel_sections}",
                f"two_up_groups={repeated_two_up_groups}",
                f"hero_has_media={str(has_media).lower()}",
            ],
            None if not rhythm_warning else "Introduce more visual pacing between sections so the page feels less like a stack of equally weighted documentation cards.",
        )
    )

    warnings = [f"{check['id']}:{check['status']}" for check in checks if check["status"] in {"warning", "skipped"}]
    evidence = [f"{check['id']}::{item}" for check in checks for item in check["evidence"][:2]]
    recommendation_sources = [
        source
        for source in (_make_recommendation_source(check) for check in checks)
        if source is not None
    ]
    skipped_checks = [check for check in checks if check["status"] == "skipped"]
    prioritized_problems = [
        {
            "title": check["title"],
            "id": check["id"],
            "severity": check["severity"],
            "evidence": check["evidence"],
            "recommendation": check.get("recommendation"),
        }
        for check in checks
        if check["status"] in {"warning", "fail"}
    ][:5]
    landing_score = _score_from_checks(checks)
    quick_wins = [
        source["recommendation"]
        for source in recommendation_sources
        if source["status"] in {"warning", "fail"} and source["severity"] in {"high", "medium"}
    ][:3]
    layout_recommendations = [
        source["recommendation"]
        for source in recommendation_sources
        if source["status"] in {"warning", "fail"} and source["originating_check"] in {"hero_structure", "spacing_layout_coherence", "responsive_baseline"}
    ][:3]
    copy_recommendations = [
        source["recommendation"]
        for source in recommendation_sources
        if source["status"] in {"warning", "fail"} and source["originating_check"] in {"audience_explicit", "visual_direction_explicit", "originality_level", "cta_clarity"}
    ][:3]
    public_readiness, blockers = _derive_public_readiness(checks, landing_score)
    top_priorities = [
        {
            "check": source["originating_check"],
            "severity": source["severity"],
            "message": source["recommendation"],
            "evidence": source["evidence"],
        }
        for source in recommendation_sources
        if source["status"] in {"warning", "fail"}
    ][:3]
    return {
        "status": "needs_attention" if prioritized_problems else "pass" if not skipped_checks else "skipped",
        "landing_score": landing_score,
        "public_readiness": public_readiness,
        "blockers": blockers,
        "warnings": warnings,
        "evidence": evidence[:12],
        "next_action": _build_next_action(recommendation_sources, skipped_checks),
        "score": landing_score,
        "checks": checks,
        "recommendation_sources": recommendation_sources,
        "prioritized_problems": prioritized_problems,
        "top_priorities": top_priorities,
        "quick_wins": quick_wins,
        "layout_recommendations": layout_recommendations,
        "copy_recommendations": copy_recommendations,
        "project": str(project.resolve()),
        "timestamp": _utc_now_iso(),
    }


def anti_generic_ui_audit(project: Path) -> Dict[str, Any]:
    return _run_project_visual_analysis(project.resolve())


def design_system_review(project: Path) -> Dict[str, Any]:
    analysis = _run_project_visual_analysis(project.resolve())
    if analysis["status"] == "skipped":
        return analysis
    return {
        "status": analysis["status"],
        "warnings": analysis["warnings"],
        "evidence": analysis["evidence"],
        "next_action": analysis["next_action"],
        "score": analysis["score"],
        "recommendation_sources": [
            source
            for source in analysis["recommendation_sources"]
            if source["originating_check"] in {"typography_coherence", "spacing_layout_coherence", "contrast_accessibility", "hero_structure"}
        ],
        "design_system_findings": [
            {
                "id": check["id"],
                "status": check["status"],
                "evidence": check["evidence"],
                "recommendation": check.get("recommendation"),
                "reason": check.get("reason"),
            }
            for check in analysis["checks"]
            if check["id"] in {"typography_coherence", "spacing_layout_coherence", "contrast_accessibility", "hero_structure"}
        ],
        "project": analysis["project"],
        "timestamp": analysis["timestamp"],
    }


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(add_help=True)
    parser.add_argument("--project", default=None, help="Project path for read-only visual or design-system audit.")
    parser.add_argument(
        "--mode",
        default="anti-generic-ui-audit",
        choices=("anti-generic-ui-audit", "design-system-review", "visual-direction-checkpoint"),
        help="Audit or checkpoint mode.",
    )
    parser.add_argument("task", nargs="*", help="Optional task text, mainly for visual-direction-checkpoint.")
    args = parser.parse_args(argv)

    if args.mode == "visual-direction-checkpoint":
        result = visual_direction_checkpoint(" ".join(args.task))
    elif not args.project:
        result = {
            "status": "skipped",
            "warnings": ["missing_project_path"],
            "evidence": ["A project path is required for project-surface review modes."],
            "next_action": "Provide --project for anti-generic or design-system review.",
            "recommendation_sources": [],
        }
    else:
        project = Path(args.project).resolve()
        result = anti_generic_ui_audit(project) if args.mode == "anti-generic-ui-audit" else design_system_review(project)

    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
