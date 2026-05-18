from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple


DEFAULT_ROOT = Path(__file__).resolve().parents[1]
RULES_PATH = Path("config/brand_profile_schema_rules.json")
GENERIC_COLOR_TERMS = ("teal", "cyan", "saas", "default")
EXPLICIT_BRAND_PROFILE_CANDIDATES = (
    Path("docs/brand_profile.md"),
    Path("docs/brand.md"),
    Path(".atlas/brand_profile.json"),
    Path(".atlas/brand.json"),
    Path("brand_profile.md"),
    Path("brand.json"),
)


def _normalize(text: str) -> str:
    return re.sub(r"\s+", " ", (text or "").lower()).strip()


def _strip_html(text: str) -> str:
    text = re.sub(r"<[^>]+>", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def _read_text_if_exists(path: Path) -> str:
    if not path.exists():
        return ""
    return path.read_text(encoding="utf-8-sig")


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


def _merge_nested_dicts(base: Dict[str, Any], overrides: Dict[str, Any]) -> Dict[str, Any]:
    merged = dict(base)
    for key, value in overrides.items():
        if isinstance(value, dict) and isinstance(merged.get(key), dict):
            merged[key] = _merge_nested_dicts(merged[key], value)
        elif value is not None:
            merged[key] = value
    return merged


def _split_markdown_sections(text: str) -> Tuple[Optional[str], Dict[str, str]]:
    title: Optional[str] = None
    sections: Dict[str, List[str]] = {}
    current_key = "_root"
    sections[current_key] = []
    for raw_line in text.splitlines():
        line = raw_line.rstrip("\n")
        stripped = line.strip()
        if not stripped:
            sections.setdefault(current_key, []).append("")
            continue
        title_match = re.match(r"^#\s+(.+)$", stripped)
        if title_match and title is None:
            title = title_match.group(1).strip()
            continue
        heading_match = re.match(r"^##+\s+(.+)$", stripped)
        if heading_match:
            current_key = _normalize(heading_match.group(1))
            sections.setdefault(current_key, [])
            continue
        sections.setdefault(current_key, []).append(line)
    return title, {key: "\n".join(lines).strip() for key, lines in sections.items()}


def _parse_bulleted_section(section_text: str) -> Tuple[Dict[str, Any], List[str]]:
    key_values: Dict[str, Any] = {}
    loose_items: List[str] = []
    current_key: Optional[str] = None
    for raw_line in section_text.splitlines():
        line = raw_line.rstrip()
        stripped = line.strip()
        if not stripped:
            continue
        top_level = re.match(r"^-\s+([^:]+):\s*(.*)$", stripped)
        if top_level:
            key = top_level.group(1).strip().lower()
            value = top_level.group(2).strip()
            current_key = key
            if value:
                key_values[key] = value
                current_key = None
            else:
                key_values[key] = []
            continue
        nested = re.match(r"^\s*-\s+(.+)$", stripped)
        if nested and current_key:
            existing = key_values.get(current_key)
            if not isinstance(existing, list):
                existing = [] if existing in {None, ""} else [str(existing)]
            existing.append(nested.group(1).strip())
            key_values[current_key] = existing
            continue
        plain_item = re.match(r"^-\s+(.+)$", stripped)
        if plain_item:
            loose_items.append(plain_item.group(1).strip())
            current_key = None
    return key_values, loose_items


def _coerce_mood_vector(raw_values: Dict[str, Any], rules: Dict[str, Any]) -> Dict[str, int]:
    vector: Dict[str, int] = {}
    for dimension in rules.get("mood_vector_dimensions", []):
        raw = raw_values.get(dimension.lower())
        if raw is None:
            continue
        match = re.search(r"-?\d+", str(raw))
        if match:
            vector[str(dimension)] = int(match.group(0))
    return vector


def _infer_explicit_visual_density(text: str) -> Optional[str]:
    normalized_text = _normalize(text)
    for candidate in ("low", "medium", "high"):
        if re.search(rf"\b{candidate}\b", normalized_text):
            return candidate
    return None


def _infer_explicit_originality(text: str) -> Optional[str]:
    normalized_text = _normalize(text)
    for candidate in ("experimental", "distinctive", "balanced", "conservative"):
        if re.search(rf"\b{candidate}\b", normalized_text):
            return candidate
    return None


def _extract_explicit_brand_profile_from_markdown(
    text: str,
    *,
    project_type: Optional[str],
    rules: Dict[str, Any],
) -> Dict[str, Any]:
    title, sections = _split_markdown_sections(text)
    identity_map, _ = _parse_bulleted_section(sections.get("identity summary", ""))
    color_map, _ = _parse_bulleted_section(sections.get("color strategy", ""))
    typography_map, _ = _parse_bulleted_section(sections.get("typography strategy", ""))
    density_map, density_items = _parse_bulleted_section(sections.get("density", ""))
    _, personality_traits = _parse_bulleted_section(sections.get("visual personality", ""))
    mood_map, _ = _parse_bulleted_section(sections.get("mood vector", ""))
    _, layout_principles = _parse_bulleted_section(sections.get("layout principles", ""))
    _, motion_principles = _parse_bulleted_section(sections.get("motion principles", ""))
    _, anti_patterns = _parse_bulleted_section(sections.get("anti-patterns to avoid", ""))
    _, inspiration_references = _parse_bulleted_section(sections.get("inspiration references", ""))
    _, evidence_expectations = _parse_bulleted_section(sections.get("evidence expectations", ""))
    _, accessibility_items = _parse_bulleted_section(sections.get("accessibility notes", ""))
    _, copy_tone = _parse_bulleted_section(sections.get("copy tone", ""))
    _, cta_rules = _parse_bulleted_section(sections.get("cta rules", ""))

    brand_name = str(identity_map.get("brand_name") or "").strip()
    if not brand_name and title:
        normalized_title = title.replace("brand profile", "").replace("Brand Profile", "").strip(" -")
        brand_name = normalized_title.strip()

    explicit_project_type = str(identity_map.get("project_type") or "").strip() or project_type
    if not explicit_project_type:
        normalized_identity = _normalize(
            f"{identity_map.get('product_surface', '')} {identity_map.get('promise', '')} {sections.get('identity summary', '')}"
        )
        if any(term in normalized_identity for term in ("landing", "onboarding", "site", "website", "frontend")):
            explicit_project_type = "frontend_app"

    visual_density = (
        str(density_map.get("target density") or density_map.get("density") or "").strip()
        or _infer_explicit_visual_density(" ".join(density_items))
        or _infer_explicit_visual_density(sections.get("density", ""))
    )
    originality_level = _infer_explicit_originality(
        "\n".join(
            [
                sections.get("visual personality", ""),
                sections.get("identity summary", ""),
                sections.get("differentiation notes", ""),
            ]
        )
    )

    profile: Dict[str, Any] = {
        "brand_name": brand_name or None,
        "audience": str(identity_map.get("audience") or "").strip() or None,
        "project_type": explicit_project_type or None,
        "personality_traits": personality_traits,
        "mood_vector": _coerce_mood_vector(mood_map, rules),
        "color_strategy": {
            "primary": str(color_map.get("primary") or "").strip() or None,
            "secondary": str(color_map.get("secondary") or "").strip() or None,
            "accent": str(color_map.get("accent") or "").strip() or None,
            "background": str(color_map.get("background") or "").strip() or None,
            "contrast_notes": str(color_map.get("contrast_notes") or "").strip() or None,
            "forbidden_color_patterns": color_map.get("forbidden_color_patterns", []),
        },
        "typography_strategy": {
            "heading_style": str(typography_map.get("heading_style") or "").strip() or None,
            "body_style": str(typography_map.get("body_style") or "").strip() or None,
            "contrast_rationale": str(typography_map.get("contrast_rationale") or "").strip() or None,
            "forbidden_font_patterns": typography_map.get("forbidden_font_patterns", []),
        },
        "layout_principles": layout_principles,
        "motion_principles": motion_principles,
        "visual_density": visual_density or None,
        "originality_level": originality_level or None,
        "anti_patterns_to_avoid": anti_patterns,
        "inspiration_references": inspiration_references,
        "differentiation_notes": sections.get("differentiation notes", "").strip() or None,
        "accessibility_notes": (
            "; ".join(accessibility_items)
            if accessibility_items
            else sections.get("accessibility notes", "").strip() or None
        ),
        "evidence_expectations": evidence_expectations,
    }
    if copy_tone:
        profile["copy_tone"] = copy_tone
    if cta_rules:
        profile["cta_rules"] = cta_rules
    return profile


def _collect_explicit_signal_coverage(profile: Dict[str, Any]) -> List[str]:
    coverage: List[str] = []
    if len(profile.get("personality_traits") or []) >= 2:
        coverage.append("visual_personality")
    if isinstance(profile.get("mood_vector"), dict) and len(profile.get("mood_vector") or {}) >= 2:
        coverage.append("mood_vector")
    color_strategy = profile.get("color_strategy") or {}
    if isinstance(color_strategy, dict) and (
        color_strategy.get("primary") or color_strategy.get("accent") or color_strategy.get("background")
    ):
        coverage.append("color_strategy")
    typography_strategy = profile.get("typography_strategy") or {}
    if isinstance(typography_strategy, dict) and (
        typography_strategy.get("heading_style") or typography_strategy.get("body_style")
    ):
        coverage.append("typography_intent")
    if str(profile.get("visual_density") or "").strip():
        coverage.append("density")
    if len(profile.get("motion_principles") or []) >= 1:
        coverage.append("motion")
    if len(profile.get("anti_patterns_to_avoid") or []) >= 1:
        coverage.append("anti_patterns")
    return coverage


def _load_explicit_brand_profile_artifact(
    *,
    project: Optional[Path],
    project_type: Optional[str],
    visual_intent_contract: Optional[Dict[str, Any]] = None,
    surface: Optional[Dict[str, str]] = None,
    metadata: Optional[Dict[str, Any]] = None,
    project_name: Optional[str] = None,
    objective: Optional[str] = None,
    root: Path = DEFAULT_ROOT,
) -> Optional[Dict[str, Any]]:
    if project is None:
        return None

    rules = load_brand_profile_schema_rules(root)
    baseline_profile = infer_brand_profile(
        project_type=project_type,
        visual_intent_contract=visual_intent_contract,
        surface=surface,
        metadata=metadata,
        project_name=project_name,
        objective=objective,
        root=root,
    )
    for relative_path in EXPLICIT_BRAND_PROFILE_CANDIDATES:
        artifact_path = project / relative_path
        if not artifact_path.exists() or not artifact_path.is_file():
            continue

        raw_text = _read_text_if_exists(artifact_path)
        parsed_profile: Dict[str, Any] = {}
        if artifact_path.suffix.lower() == ".json":
            if raw_text.strip():
                try:
                    json_payload = json.loads(raw_text)
                except json.JSONDecodeError:
                    json_payload = {}
                if isinstance(json_payload, dict):
                    parsed_profile = json_payload
        else:
            parsed_profile = _extract_explicit_brand_profile_from_markdown(
                raw_text,
                project_type=project_type,
                rules=rules,
            )

        merged_profile = _merge_nested_dicts(baseline_profile, parsed_profile)
        explicit_signal_coverage = _collect_explicit_signal_coverage(parsed_profile)
        return {
            "profile": merged_profile,
            "explicit_profile_present": len(explicit_signal_coverage) >= 7,
            "explicit_artifact_present": True,
            "profile_source": "explicit" if len(explicit_signal_coverage) >= 7 else "explicit_artifact_weak",
            "explicit_artifact_path": relative_path.as_posix(),
            "explicit_artifact_type": artifact_path.suffix.lower().lstrip(".") or "unknown",
            "explicit_signal_coverage": explicit_signal_coverage,
            "artifact_raw_text": raw_text,
        }
    return None


def load_brand_profile_schema_rules(root: Path = DEFAULT_ROOT) -> Dict[str, Any]:
    return json.loads((root / RULES_PATH).read_text(encoding="utf-8-sig"))


def requires_brand_profile(
    *,
    project_type: Optional[str],
    visual_intent_contract: Optional[Dict[str, Any]] = None,
    source_text: str = "",
    surface_paths: Optional[List[str]] = None,
    root: Path = DEFAULT_ROOT,
) -> bool:
    rules = load_brand_profile_schema_rules(root)
    project_type_value = str(project_type or "").strip()
    if project_type_value in set(rules.get("backend_exempt_project_types", [])):
        return False
    if project_type_value in set(rules.get("required_for_project_types", [])):
        return True
    if isinstance(visual_intent_contract, dict) and bool(visual_intent_contract.get("requires_contract")):
        return True
    normalized_text = _normalize(source_text)
    ui_signals = tuple(rules.get("ui_surface_signals", []))
    if any(signal in normalized_text for signal in ui_signals):
        return True
    if surface_paths and any(Path(path).name.lower() == "index.html" for path in surface_paths):
        return True
    return False


def _infer_mood_vector(
    visual_intent_contract: Dict[str, Any],
    rules: Dict[str, Any],
    normalized_text: str,
) -> Dict[str, int]:
    vibe = _normalize(str(visual_intent_contract.get("mood_or_vibe") or ""))
    originality = _normalize(str(visual_intent_contract.get("originality_level") or ""))
    values: Dict[str, int] = {}
    for dimension in rules.get("mood_vector_dimensions", []):
        values[str(dimension)] = 4
    if "editorial" in vibe:
        values["editorial"] = 8
        values["premium"] = 6
    if "warm" in vibe:
        values["warm"] = 8
    if "bold" in vibe:
        values["bold"] = 8
    if "playful" in vibe:
        values["playful"] = 8
    if "minimal" in vibe:
        values["minimalist"] = 8
    if any(term in normalized_text for term in ("technical", "system", "governance", "factory", "architecture")):
        values["technical"] = 8
        values["futuristic"] = max(values["futuristic"], 6)
    if originality == "distinctive":
        values["bold"] = max(values["bold"], 7)
        values["futuristic"] = max(values["futuristic"], 6)
    elif originality == "experimental":
        values["bold"] = max(values["bold"], 8)
        values["futuristic"] = max(values["futuristic"], 8)
    elif originality == "conservative":
        values["minimalist"] = max(values["minimalist"], 6)
    return values


def infer_brand_profile(
    *,
    project_type: Optional[str],
    visual_intent_contract: Optional[Dict[str, Any]] = None,
    surface: Optional[Dict[str, str]] = None,
    metadata: Optional[Dict[str, Any]] = None,
    project_name: Optional[str] = None,
    objective: Optional[str] = None,
    root: Path = DEFAULT_ROOT,
) -> Dict[str, Any]:
    rules = load_brand_profile_schema_rules(root)
    contract = visual_intent_contract or {}
    surface = surface or {}
    css_text = surface.get("styles.css", "")
    fonts = _extract_css_font_families(css_text)
    css_vars = _extract_css_vars(css_text)
    normalized_text = _normalize(
        "\n".join(
            [
                str(project_name or ""),
                str(objective or ""),
                json.dumps(contract, ensure_ascii=False),
                "\n".join(surface.values()),
            ]
        )
    )

    brand_name = str(project_name or (metadata or {}).get("project_name") or (metadata or {}).get("system_name") or "").strip() or None
    mood_or_vibe = str(contract.get("mood_or_vibe") or "").strip()
    originality_level = str(contract.get("originality_level") or "").strip() or None
    visual_density = str(contract.get("visual_density") or "").strip() or None
    anti_patterns = list(contract.get("anti_patterns_to_avoid") or [])
    evidence_expectations = list(contract.get("evidence_expectations") or [])
    audience = str(contract.get("audience") or "").strip() or None
    problem_or_promise = str(contract.get("problem_or_promise") or objective or "").strip() or None
    heading_style = fonts[0] if fonts else None
    body_style = fonts[1] if len(fonts) > 1 else fonts[0] if fonts else None

    personality_traits = _dedupe_preserve_order(
        [
            mood_or_vibe,
            "technical" if any(term in normalized_text for term in ("system", "technical", "factory", "governance")) else "",
            "distinctive" if originality_level in {"distinctive", "experimental"} else "",
        ]
    )

    return {
        "brand_name": brand_name,
        "audience": audience,
        "project_type": project_type or contract.get("project_type"),
        "personality_traits": personality_traits,
        "mood_vector": _infer_mood_vector(contract, rules, normalized_text),
        "color_strategy": {
            "primary": css_vars.get("--accent") or contract.get("color_strategy"),
            "secondary": css_vars.get("--accent-soft") or css_vars.get("--surface"),
            "accent": css_vars.get("--accent-strong") or css_vars.get("--accent"),
            "background": css_vars.get("--bg"),
            "contrast_notes": f"Anchor contrast around {css_vars.get('--ink')} on {css_vars.get('--bg')}." if css_vars.get("--bg") and css_vars.get("--ink") else None,
            "forbidden_color_patterns": ["default teal without rationale"] if anti_patterns else [],
        },
        "typography_strategy": {
            "heading_style": heading_style or contract.get("typography_intent"),
            "body_style": body_style,
            "contrast_rationale": "Differentiate headline posture from body readability." if heading_style and body_style and heading_style.lower() != body_style.lower() else None,
            "forbidden_font_patterns": ["inter body default", "generic sans everywhere"] if anti_patterns else [],
        },
        "layout_principles": _dedupe_preserve_order(
            [
                f"{visual_density} density" if visual_density else "",
                "hero-first narrative" if contract.get("hero_direction") else "",
                "clear CTA progression" if contract.get("primary_cta_intent") else "",
            ]
        ),
        "motion_principles": _dedupe_preserve_order(
            [
                f"{contract.get('motion_intensity')} motion" if contract.get("motion_intensity") else "",
                "motion supports hierarchy, not decoration" if contract.get("motion_intensity") else "",
            ]
        ),
        "visual_density": visual_density,
        "originality_level": originality_level,
        "anti_patterns_to_avoid": anti_patterns,
        "inspiration_references": [],
        "differentiation_notes": (
            f"Translate {problem_or_promise} into a system-first identity instead of a generic SaaS template."
            if problem_or_promise and originality_level in {"distinctive", "experimental"}
            else None
        ),
        "accessibility_notes": "Preserve readable contrast and scanning clarity before claiming design PASS." if evidence_expectations else None,
        "evidence_expectations": evidence_expectations,
    }


def validate_brand_profile(
    profile: Dict[str, Any],
    *,
    project_type: Optional[str],
    visual_intent_contract: Optional[Dict[str, Any]] = None,
    source_text: str = "",
    surface_paths: Optional[List[str]] = None,
    explicit_profile_present: bool = True,
    root: Path = DEFAULT_ROOT,
) -> Dict[str, Any]:
    rules = load_brand_profile_schema_rules(root)
    requires_profile = requires_brand_profile(
        project_type=project_type,
        visual_intent_contract=visual_intent_contract,
        source_text=source_text,
        surface_paths=surface_paths,
        root=root,
    )
    if not requires_profile:
        return {
            "status": "skipped",
            "missing_fields": [],
            "weak_fields": [],
            "invalid_fields": [],
            "anti_generic_risks": [],
            "derivative_risks": [],
            "accessibility_risks": [],
            "requires_human_clarification": False,
            "recommended_questions": [],
            "evidence_expectations": list(rules.get("minimum_evidence_expectations", [])),
            "why": "This project does not currently look like a UI or landing surface that requires a brand profile schema.",
            "requires_profile": False,
            "profile": profile,
            "profile_source": "not_required",
            "explicit_profile_present": explicit_profile_present,
            "required_fields": list(rules.get("required_fields", [])),
            "advisory_only": bool(rules.get("advisory_only", True)),
            "next_action": "No brand profile is required for the current project type.",
        }

    required_fields = list(rules.get("required_fields", []))
    missing_fields: List[str] = []
    weak_fields: List[str] = []
    invalid_fields: List[str] = []
    anti_generic_risks: List[str] = []
    derivative_risks: List[str] = []
    accessibility_risks: List[str] = []
    recommended_questions: List[str] = []

    for field_name in required_fields:
        value = profile.get(field_name)
        if value is None or (isinstance(value, str) and not value.strip()) or (isinstance(value, list) and not value) or (isinstance(value, dict) and not value):
            missing_fields.append(field_name)

    min_rules = rules.get("minimum_quality_rules", {})
    if isinstance(profile.get("personality_traits"), list) and len(profile.get("personality_traits", [])) < int(min_rules.get("personality_traits_min_items", 2)):
        weak_fields.append("personality_traits")
    if isinstance(profile.get("layout_principles"), list) and len(profile.get("layout_principles", [])) < int(min_rules.get("layout_principles_min_items", 2)):
        weak_fields.append("layout_principles")
    if isinstance(profile.get("motion_principles"), list) and len(profile.get("motion_principles", [])) < int(min_rules.get("motion_principles_min_items", 1)):
        weak_fields.append("motion_principles")
    if isinstance(profile.get("anti_patterns_to_avoid"), list) and len(profile.get("anti_patterns_to_avoid", [])) < int(min_rules.get("anti_patterns_min_items", 2)):
        weak_fields.append("anti_patterns_to_avoid")
    if isinstance(profile.get("evidence_expectations"), list) and len(profile.get("evidence_expectations", [])) < int(min_rules.get("evidence_expectations_min_items", 1)):
        weak_fields.append("evidence_expectations")

    allowed_originality = set(rules.get("allowed_originality_levels", []))
    if profile.get("originality_level") and str(profile["originality_level"]).strip() not in allowed_originality:
        invalid_fields.append("originality_level")

    allowed_density = set(rules.get("allowed_visual_density", []))
    if profile.get("visual_density") and str(profile["visual_density"]).strip() not in allowed_density:
        invalid_fields.append("visual_density")

    mood_vector = profile.get("mood_vector")
    mood_dimensions = list(rules.get("mood_vector_dimensions", []))
    vector_range = rules.get("mood_vector_range", {})
    min_value = int(vector_range.get("min", 0))
    max_value = int(vector_range.get("max", 10))
    if not isinstance(mood_vector, dict):
        missing_fields.append("mood_vector")
    else:
        missing_dimensions = [dimension for dimension in mood_dimensions if dimension not in mood_vector]
        if missing_dimensions:
            invalid_fields.extend([f"mood_vector.{dimension}" for dimension in missing_dimensions])
        for dimension in mood_dimensions:
            value = mood_vector.get(dimension)
            if not isinstance(value, (int, float)) or value < min_value or value > max_value:
                invalid_fields.append(f"mood_vector.{dimension}")

    color_strategy = profile.get("color_strategy")
    if not isinstance(color_strategy, dict):
        missing_fields.append("color_strategy")
    else:
        for field_name in rules.get("required_color_strategy_fields", []):
            value = color_strategy.get(field_name)
            if value is None or (isinstance(value, str) and not value.strip()) or (isinstance(value, list) and not value):
                missing_fields.append(f"color_strategy.{field_name}")

        normalized_primary = _normalize(str(color_strategy.get("primary") or ""))
        normalized_accent = _normalize(str(color_strategy.get("accent") or ""))
        if any(term in normalized_primary or term in normalized_accent for term in GENERIC_COLOR_TERMS):
            anti_generic_risks.append("generic_color_strategy")

    typography_strategy = profile.get("typography_strategy")
    forbidden_fonts = tuple(str(item).strip().lower() for item in rules.get("forbidden_font_patterns", []))
    if not isinstance(typography_strategy, dict):
        missing_fields.append("typography_strategy")
    else:
        for field_name in rules.get("required_typography_strategy_fields", []):
            value = typography_strategy.get(field_name)
            if value is None or (isinstance(value, str) and not value.strip()) or (isinstance(value, list) and not value):
                missing_fields.append(f"typography_strategy.{field_name}")
        heading_style = _normalize(str(typography_strategy.get("heading_style") or ""))
        body_style = _normalize(str(typography_strategy.get("body_style") or ""))
        if any(font in heading_style or font in body_style for font in forbidden_fonts):
            anti_generic_risks.append("forbidden_font_pattern_detected")
        if heading_style and body_style and heading_style == body_style:
            anti_generic_risks.append("low_typographic_contrast")

    differentiation_notes = str(profile.get("differentiation_notes") or "").strip()
    differentiation_min_words = int(min_rules.get("differentiation_notes_min_words", 6))
    if differentiation_notes and len(differentiation_notes.split()) < differentiation_min_words:
        weak_fields.append("differentiation_notes")
    if not differentiation_notes:
        anti_generic_risks.append("missing_differentiation_notes")

    inspiration_references = profile.get("inspiration_references")
    reference_signals = tuple(str(item).strip().lower() for item in rules.get("derivative_reference_signals", []))
    if isinstance(inspiration_references, list):
        normalized_refs = [_normalize(str(item)) for item in inspiration_references if str(item).strip()]
        if normalized_refs and not differentiation_notes:
            derivative_risks.append("undifferentiated_inspiration_reference")
        if any(any(signal in ref for signal in reference_signals) for ref in normalized_refs) and len(differentiation_notes.split()) < differentiation_min_words:
            derivative_risks.append("brand_reference_without_clear_differentiation")
    elif inspiration_references is not None:
        invalid_fields.append("inspiration_references")

    accessibility_notes = str(profile.get("accessibility_notes") or "").strip()
    if not accessibility_notes:
        accessibility_risks.append("missing_accessibility_notes")
    if isinstance(color_strategy, dict) and not str(color_strategy.get("contrast_notes") or "").strip():
        accessibility_risks.append("missing_contrast_notes")

    if not profile.get("originality_level"):
        anti_generic_risks.append("missing_originality_level")
    if not profile.get("anti_patterns_to_avoid"):
        anti_generic_risks.append("missing_anti_patterns")

    question_map = {
        "brand_name": "What is the explicit brand or product name this profile should represent?",
        "audience": "Who is the audience this identity must feel right for?",
        "personality_traits": "What two or three personality traits should the identity consistently signal?",
        "mood_vector": "How should the mood vector score across premium, playful, technical, editorial, minimalist, bold, warm and futuristic?",
        "color_strategy": "What palette strategy should guide primary, secondary, accent and background choices?",
        "typography_strategy": "How should heading and body typography differ, and why?",
        "layout_principles": "What layout principles should make the UI feel recognizable instead of generic?",
        "motion_principles": "How should motion support hierarchy without becoming decorative noise?",
        "visual_density": "Should the visual density be low, medium or high?",
        "originality_level": "Should the identity be conservative, balanced, distinctive or experimental?",
        "anti_patterns_to_avoid": "What brand anti-patterns must Atlas explicitly avoid?",
        "inspiration_references": "Which inspiration references are acceptable, if any?",
        "differentiation_notes": "How will this identity stay distinct from its inspiration references?",
        "accessibility_notes": "What accessibility or contrast constraints should shape the visual system?",
        "evidence_expectations": "What evidence is required before Atlas can call the brand direction passable?",
    }
    for field_name in missing_fields + weak_fields + [field.split(".", 1)[0] for field in invalid_fields]:
        top_level = field_name.split(".", 1)[0]
        question = question_map.get(top_level)
        if question and question not in recommended_questions:
            recommended_questions.append(question)

    status = "ready"
    if missing_fields or weak_fields or invalid_fields or anti_generic_risks or derivative_risks or accessibility_risks or not explicit_profile_present:
        status = "needs_input"

    why_parts: List[str] = []
    if not explicit_profile_present:
        why_parts.append("The current brand profile is inferred from surrounding signals, not explicitly declared yet.")
    if missing_fields:
        why_parts.append(f"Missing fields: {', '.join(_dedupe_preserve_order(missing_fields))}.")
    if weak_fields:
        why_parts.append(f"Weak fields: {', '.join(_dedupe_preserve_order(weak_fields))}.")
    if invalid_fields:
        why_parts.append(f"Invalid fields: {', '.join(_dedupe_preserve_order(invalid_fields))}.")
    if anti_generic_risks:
        why_parts.append(f"Anti-generic risks: {', '.join(_dedupe_preserve_order(anti_generic_risks))}.")
    if derivative_risks:
        why_parts.append(f"Derivative risks: {', '.join(_dedupe_preserve_order(derivative_risks))}.")
    if accessibility_risks:
        why_parts.append(f"Accessibility risks: {', '.join(_dedupe_preserve_order(accessibility_risks))}.")
    if not why_parts:
        why_parts.append("The brand profile is explicit enough to support advisory branding review.")

    next_action = "Document the brand profile explicitly before treating the identity as settled." if not explicit_profile_present else "Clarify the weak brand fields before stronger brand readiness claims."
    if status == "ready":
        next_action = "Use this brand profile as the branding baseline and keep PASS claims tied to evidence."

    return {
        "status": status,
        "missing_fields": _dedupe_preserve_order(missing_fields),
        "weak_fields": _dedupe_preserve_order(weak_fields),
        "invalid_fields": _dedupe_preserve_order(invalid_fields),
        "anti_generic_risks": _dedupe_preserve_order(anti_generic_risks),
        "derivative_risks": _dedupe_preserve_order(derivative_risks),
        "accessibility_risks": _dedupe_preserve_order(accessibility_risks),
        "requires_human_clarification": bool(
            missing_fields or weak_fields or invalid_fields or derivative_risks or accessibility_risks or not explicit_profile_present
        ),
        "recommended_questions": recommended_questions[:8],
        "evidence_expectations": profile.get("evidence_expectations") or list(rules.get("minimum_evidence_expectations", [])),
        "why": " ".join(why_parts),
        "requires_profile": True,
        "profile": profile,
        "profile_source": "explicit" if explicit_profile_present else "inferred_from_context",
        "explicit_profile_present": explicit_profile_present,
        "required_fields": required_fields,
        "advisory_only": bool(rules.get("advisory_only", True)),
        "next_action": next_action,
    }


def build_brand_profile_assessment(
    *,
    project_type: Optional[str],
    visual_intent_contract: Optional[Dict[str, Any]] = None,
    profile: Optional[Dict[str, Any]] = None,
    project: Optional[Path] = None,
    surface: Optional[Dict[str, str]] = None,
    metadata: Optional[Dict[str, Any]] = None,
    project_name: Optional[str] = None,
    objective: Optional[str] = None,
    root: Path = DEFAULT_ROOT,
) -> Dict[str, Any]:
    explicit_artifact = None
    if profile is None:
        explicit_artifact = _load_explicit_brand_profile_artifact(
            project=project,
            project_type=project_type,
            visual_intent_contract=visual_intent_contract,
            surface=surface,
            metadata=metadata,
            project_name=project_name,
            objective=objective,
            root=root,
        )

    resolved_profile = profile or (explicit_artifact or {}).get("profile") or infer_brand_profile(
        project_type=project_type,
        visual_intent_contract=visual_intent_contract,
        surface=surface,
        metadata=metadata,
        project_name=project_name,
        objective=objective,
        root=root,
    )
    review = validate_brand_profile(
        resolved_profile,
        project_type=project_type,
        visual_intent_contract=visual_intent_contract,
        source_text="\n".join(
            [
                json.dumps(resolved_profile, ensure_ascii=False),
                str((explicit_artifact or {}).get("artifact_raw_text") or ""),
            ]
        ),
        surface_paths=list((surface or {}).keys()),
        explicit_profile_present=bool(profile is not None or (explicit_artifact or {}).get("explicit_profile_present")),
        root=root,
    )
    if explicit_artifact:
        review["explicit_artifact_present"] = bool(explicit_artifact.get("explicit_artifact_present"))
        review["explicit_artifact_path"] = explicit_artifact.get("explicit_artifact_path")
        review["explicit_artifact_type"] = explicit_artifact.get("explicit_artifact_type")
        review["explicit_signal_coverage"] = explicit_artifact.get("explicit_signal_coverage", [])
        review["profile_source"] = str(explicit_artifact.get("profile_source") or review.get("profile_source"))
    return review


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(add_help=True)
    parser.add_argument("--project-type", default=None)
    parser.add_argument("--visual-intent-json", default=None)
    parser.add_argument("--brand-profile-json", default=None)
    args = parser.parse_args(argv)

    visual_intent_contract = json.loads(args.visual_intent_json) if args.visual_intent_json else None
    explicit_profile = json.loads(args.brand_profile_json) if args.brand_profile_json else None
    result = build_brand_profile_assessment(
        project_type=args.project_type,
        visual_intent_contract=visual_intent_contract,
        profile=explicit_profile,
        root=DEFAULT_ROOT,
    )
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
