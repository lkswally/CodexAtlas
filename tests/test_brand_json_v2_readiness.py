from tools.brand_json_v2_readiness import assess_brand_json_v2_readiness


def _explicit_profile():
    return {
        "brand_name": "Atlas",
        "audience": "for developers",
        "project_type": "frontend_app",
        "personality_traits": ["technical", "editorial"],
        "mood_vector": {
            "premium": 6,
            "playful": 2,
            "technical": 8,
            "editorial": 7,
            "minimalist": 6,
            "bold": 7,
            "warm": 4,
            "futuristic": 6
        },
        "color_strategy": {
            "primary": "#0b182b",
            "secondary": "#cad2dc",
            "accent": "#e76f51",
            "background": "#f7f4ef",
            "contrast_notes": "High contrast with warm editorial accent.",
            "forbidden_color_patterns": ["default teal without rationale"]
        },
        "typography_strategy": {
            "heading_style": "Newsreader",
            "body_style": "Satoshi",
            "contrast_rationale": "Editorial headings with crisp system body copy.",
            "forbidden_font_patterns": ["inter body default"]
        },
        "layout_principles": ["hero-first narrative", "medium density"],
        "motion_principles": ["low motion", "motion supports hierarchy"],
        "visual_density": "medium",
        "originality_level": "distinctive",
        "anti_patterns_to_avoid": ["generic saas", "pdf look"],
        "inspiration_references": ["editorial systems"],
        "differentiation_notes": "Translate Atlas into a system-first editorial identity that feels governed, technical and clearly differentiated from generic SaaS defaults.",
        "accessibility_notes": "Preserve 4.5 contrast, clear CTA emphasis, keyboard-visible focus and readable hierarchy before any stronger PASS claim.",
        "evidence_expectations": ["palette rationale", "typography rationale", "differentiation note"]
    }


def test_brand_json_v2_accepts_complete_explicit_profile():
    result = assess_brand_json_v2_readiness(
        project_type="frontend_app",
        profile=_explicit_profile(),
    )
    assert result["status"] == "ready"
    assert result["export_candidate"] is True


def test_brand_json_v2_flags_missing_mood_vector():
    profile = _explicit_profile()
    del profile["mood_vector"]
    result = assess_brand_json_v2_readiness(
        project_type="frontend_app",
        profile=profile,
    )
    assert result["status"] == "needs_input"
    assert "mood_vector" in result["missing_sections"]


def test_brand_json_v2_requires_explicit_profile_for_ready():
    review = {
        "status": "ready",
        "explicit_profile_present": False,
        "missing_fields": [],
        "weak_fields": [],
        "invalid_fields": [],
        "anti_generic_risks": [],
        "derivative_risks": [],
        "accessibility_risks": [],
        "profile": _explicit_profile(),
        "profile_source": "inferred_from_context",
    }
    result = assess_brand_json_v2_readiness(
        project_type="frontend_app",
        profile_review=review,
    )
    assert result["status"] == "needs_input"
    assert result["explicit_profile_present"] is False


def test_brand_json_v2_flags_derivative_risk():
    review = {
        "status": "needs_input",
        "explicit_profile_present": True,
        "missing_fields": [],
        "weak_fields": [],
        "invalid_fields": [],
        "anti_generic_risks": [],
        "derivative_risks": ["inspiration too close to reference"],
        "accessibility_risks": [],
        "profile": _explicit_profile(),
        "profile_source": "explicit_profile",
    }
    result = assess_brand_json_v2_readiness(
        project_type="frontend_app",
        profile_review=review,
    )
    assert result["status"] == "needs_input"
    assert result["derivative_risks"]
