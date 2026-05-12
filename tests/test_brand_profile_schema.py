import os

os.environ["ATLAS_DISABLE_EVENT_LOGS"] = "1"

from tools.brand_profile_schema import build_brand_profile_assessment, validate_brand_profile


def _valid_brand_profile():
    return {
        "brand_name": "CodexAtlas",
        "audience": "for developers",
        "project_type": "frontend_app",
        "personality_traits": ["technical", "distinctive"],
        "mood_vector": {
            "premium": 6,
            "playful": 2,
            "technical": 9,
            "editorial": 7,
            "minimalist": 6,
            "bold": 7,
            "warm": 4,
            "futuristic": 7,
        },
        "color_strategy": {
            "primary": "deep graphite",
            "secondary": "muted mineral",
            "accent": "copper orange",
            "background": "warm ivory",
            "contrast_notes": "Use strong text contrast over warm backgrounds.",
            "forbidden_color_patterns": ["default teal with no rationale", "washed grayscale with no accent"],
        },
        "typography_strategy": {
            "heading_style": "editorial serif",
            "body_style": "disciplined grotesk sans",
            "contrast_rationale": "The serif handles posture while the sans keeps operational copy readable.",
            "forbidden_font_patterns": ["inter everywhere", "generic sans only"],
        },
        "layout_principles": ["hero-first narrative", "modular proof blocks"],
        "motion_principles": ["low motion", "motion supports hierarchy"],
        "visual_density": "medium",
        "originality_level": "distinctive",
        "anti_patterns_to_avoid": ["README/PDF-like layout", "default SaaS teal"],
        "inspiration_references": ["industrial editorial systems"],
        "differentiation_notes": "Borrow structural clarity, not recognizable brand signatures or copied layout rhythms.",
        "accessibility_notes": "Keep contrast and scanning clarity above visual novelty.",
        "evidence_expectations": ["audit", "before pass"],
    }


def test_brand_profile_schema_accepts_complete_profile():
    result = validate_brand_profile(
        _valid_brand_profile(),
        project_type="frontend_app",
        visual_intent_contract={"requires_contract": True},
        source_text="landing page for developers",
    )
    assert result["status"] == "ready"
    assert result["missing_fields"] == []
    assert result["invalid_fields"] == []


def test_brand_profile_schema_flags_missing_brand_name():
    profile = _valid_brand_profile()
    profile["brand_name"] = ""
    result = validate_brand_profile(
        profile,
        project_type="frontend_app",
        visual_intent_contract={"requires_contract": True},
        source_text="landing page",
    )
    assert result["status"] == "needs_input"
    assert "brand_name" in result["missing_fields"]


def test_brand_profile_schema_flags_missing_mood_vector():
    profile = _valid_brand_profile()
    profile["mood_vector"] = {}
    result = validate_brand_profile(
        profile,
        project_type="frontend_app",
        visual_intent_contract={"requires_contract": True},
        source_text="landing page",
    )
    assert "mood_vector" in result["missing_fields"]


def test_brand_profile_schema_rejects_out_of_range_mood_vector():
    profile = _valid_brand_profile()
    profile["mood_vector"]["premium"] = 11
    result = validate_brand_profile(
        profile,
        project_type="frontend_app",
        visual_intent_contract={"requires_contract": True},
        source_text="landing page",
    )
    assert "mood_vector.premium" in result["invalid_fields"]


def test_brand_profile_schema_detects_generic_color_strategy():
    profile = _valid_brand_profile()
    profile["color_strategy"]["primary"] = "teal"
    result = validate_brand_profile(
        profile,
        project_type="frontend_app",
        visual_intent_contract={"requires_contract": True},
        source_text="landing page",
    )
    assert "generic_color_strategy" in result["anti_generic_risks"]


def test_brand_profile_schema_detects_generic_typography_strategy():
    profile = _valid_brand_profile()
    profile["typography_strategy"]["heading_style"] = "Inter"
    profile["typography_strategy"]["body_style"] = "Inter"
    result = validate_brand_profile(
        profile,
        project_type="frontend_app",
        visual_intent_contract={"requires_contract": True},
        source_text="landing page",
    )
    assert "forbidden_font_pattern_detected" in result["anti_generic_risks"]
    assert "low_typographic_contrast" in result["anti_generic_risks"]


def test_brand_profile_schema_allows_documented_forbidden_font_patterns_without_false_positive():
    profile = _valid_brand_profile()
    profile["typography_strategy"]["forbidden_font_patterns"] = ["Inter everywhere"]
    result = validate_brand_profile(
        profile,
        project_type="frontend_app",
        visual_intent_contract={"requires_contract": True},
        source_text="landing page",
    )
    assert "forbidden_font_pattern_detected" not in result["anti_generic_risks"]


def test_brand_profile_schema_detects_derivative_risk():
    profile = _valid_brand_profile()
    profile["inspiration_references"] = ["Linear", "Stripe"]
    profile["differentiation_notes"] = ""
    result = validate_brand_profile(
        profile,
        project_type="frontend_app",
        visual_intent_contract={"requires_contract": True},
        source_text="landing page",
    )
    assert result["derivative_risks"]


def test_backend_project_does_not_require_brand_profile():
    result = build_brand_profile_assessment(
        project_type="backend_service",
        visual_intent_contract={"project_type": "backend_service"},
    )
    assert result["status"] == "skipped"
    assert result["requires_profile"] is False


def test_landing_project_requires_brand_profile():
    result = build_brand_profile_assessment(
        project_type="frontend_app",
        visual_intent_contract={
            "project_type": "frontend_app",
            "requires_contract": True,
            "audience": "for developers",
            "problem_or_promise": "Create structured AI projects without chaos.",
            "mood_or_vibe": "editorial",
            "originality_level": "distinctive",
            "hero_direction": "system-first hero",
            "primary_cta_intent": "start setup",
            "visual_density": "medium",
            "motion_intensity": "low",
            "typography_intent": "editorial serif plus grotesk sans",
            "color_strategy": "warm neutrals with a bold accent",
            "anti_patterns_to_avoid": ["avoid generic", "avoid saas"],
            "evidence_expectations": ["audit"],
        },
    )
    assert result["requires_profile"] is True
    assert result["status"] == "needs_input"
    assert result["explicit_profile_present"] is False
