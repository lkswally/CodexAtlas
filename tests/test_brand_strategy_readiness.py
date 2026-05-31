import os
import shutil
from pathlib import Path
from uuid import uuid4

os.environ["ATLAS_DISABLE_EVENT_LOGS"] = "1"

from tests._support_paths import ATLAS_ROOT
from tools.brand_strategy_readiness import assess_brand_strategy_readiness


def _make_temp_project() -> Path:
    base = ATLAS_ROOT / "tests" / "_tmp_brand_strategy_cases"
    base.mkdir(parents=True, exist_ok=True)
    project = base / f"case_{uuid4().hex}"
    project.mkdir(parents=True, exist_ok=False)
    return project


def test_brand_strategy_needs_improvement_without_clear_audience():
    project = _make_temp_project()
    try:
        result = assess_brand_strategy_readiness(
            {
                "project_type": "frontend_app",
                "category": "ai workflow operating system",
                "positioning": "A governed layer for structured AI delivery.",
                "brand_profile": {
                    "brand_name": "Atlas",
                    "project_type": "frontend_app",
                    "personality_traits": ["technical", "structured"],
                    "mood_vector": {"premium": 5, "playful": 2, "technical": 8, "editorial": 5, "minimalist": 6, "bold": 6, "warm": 3, "futuristic": 7},
                    "color_strategy": {"primary": "graphite", "secondary": "slate", "accent": "amber", "background": "ink", "contrast_notes": "High contrast dark system."},
                    "typography_strategy": {"heading_style": "Space Grotesk", "body_style": "IBM Plex Sans", "contrast_rationale": "Headings feel technical, body stays readable."},
                    "layout_principles": ["hero-first narrative", "clear cta progression"],
                    "motion_principles": ["low motion"],
                    "visual_density": "balanced",
                    "originality_level": "distinctive",
                    "anti_patterns_to_avoid": ["generic saas gradients", "default teal"],
                    "inspiration_references": [],
                    "differentiation_notes": "Governance-first positioning for AI work.",
                    "accessibility_notes": "Keep strong contrast and readable spacing.",
                    "evidence_expectations": ["show governance boundaries"]
                },
            },
            root=ATLAS_ROOT,
            project=project,
        )
    finally:
        shutil.rmtree(project, ignore_errors=True)

    assert result["brand_readiness_state"] == "needs_improvement"
    assert "target_audience" in result["missing_inputs"]


def test_brand_strategy_warns_when_color_roles_are_missing():
    project = _make_temp_project()
    try:
        result = assess_brand_strategy_readiness(
            {
                "project_type": "frontend_app",
                "target_audience": "Technical product teams.",
                "category": "ai governance workspace",
                "positioning": "Structured AI delivery with visible phase gates.",
                "brand_profile": {
                    "brand_name": "Atlas",
                    "audience": "Technical product teams.",
                    "project_type": "frontend_app",
                    "personality_traits": ["technical", "confident"],
                    "mood_vector": {"premium": 6, "playful": 1, "technical": 8, "editorial": 4, "minimalist": 6, "bold": 5, "warm": 2, "futuristic": 7},
                    "color_strategy": {"primary": "graphite"},
                    "typography_strategy": {"heading_style": "Space Grotesk", "body_style": "IBM Plex Sans", "contrast_rationale": "Distinct heading and body roles."},
                    "layout_principles": ["hero-first narrative", "clear cta progression"],
                    "motion_principles": ["low motion"],
                    "visual_density": "balanced",
                    "originality_level": "distinctive",
                    "anti_patterns_to_avoid": ["generic saas gradients", "default teal"],
                    "inspiration_references": [],
                    "differentiation_notes": "Governance-first positioning for AI work.",
                    "accessibility_notes": "Keep strong contrast and readable spacing.",
                    "evidence_expectations": ["show governance boundaries"]
                },
            },
            root=ATLAS_ROOT,
            project=project,
        )
    finally:
        shutil.rmtree(project, ignore_errors=True)

    assert any("color roles" in warning.lower() for warning in result["warnings"])


def test_brand_strategy_marks_generic_template_risk_high():
    project = _make_temp_project()
    try:
        result = assess_brand_strategy_readiness(
            {
                "project_type": "frontend_app",
                "target_audience": "Founders evaluating AI tools.",
                "category": "ai operating system",
                "positioning": "A platform for structured product decisions.",
                "design_quality_review": {"warnings": ["template-like hero", "generic layout rhythm"]},
                "brand_profile": {
                    "brand_name": "Atlas",
                    "audience": "Founders evaluating AI tools.",
                    "project_type": "frontend_app",
                    "personality_traits": ["technical", "modern"],
                    "mood_vector": {"premium": 5, "playful": 2, "technical": 8, "editorial": 4, "minimalist": 6, "bold": 5, "warm": 2, "futuristic": 7},
                    "color_strategy": {"primary": "teal", "secondary": "teal", "accent": "blue gradient", "background": "white", "contrast_notes": "Basic contrast."},
                    "typography_strategy": {"heading_style": "Inter", "body_style": "Inter", "contrast_rationale": ""},
                    "layout_principles": ["hero-first narrative"],
                    "motion_principles": ["low motion"],
                    "visual_density": "balanced",
                    "originality_level": "conservative",
                    "anti_patterns_to_avoid": ["generic templates"],
                    "inspiration_references": [],
                    "differentiation_notes": "",
                    "accessibility_notes": "",
                    "evidence_expectations": ["show governance boundaries"]
                },
            },
            root=ATLAS_ROOT,
            project=project,
        )
    finally:
        shutil.rmtree(project, ignore_errors=True)

    assert result["generic_brand_risk"] == "high"


def test_brand_strategy_warns_when_verbal_tone_is_inconsistent():
    project = _make_temp_project()
    try:
        result = assess_brand_strategy_readiness(
            {
                "project_type": "frontend_app",
                "target_audience": "Security-conscious product teams.",
                "category": "governed ai workspace",
                "positioning": "Structured AI delivery with visible controls.",
                "copywriting_conversion_posture": {
                    "copy_readiness_state": "needs_improvement",
                    "trust_score": 72,
                    "tone_consistency_score": 40,
                    "hero_message": {"cta_clear": True, "problem_visible": True},
                    "warnings": ["generic AI-style filler instead of specific value"],
                    "must_not_claim": []
                },
                "brand_profile": {
                    "brand_name": "Atlas",
                    "audience": "Security-conscious product teams.",
                    "project_type": "frontend_app",
                    "personality_traits": ["technical", "reliable"],
                    "mood_vector": {"premium": 6, "playful": 1, "technical": 9, "editorial": 4, "minimalist": 6, "bold": 4, "warm": 2, "futuristic": 6},
                    "color_strategy": {"primary": "graphite", "secondary": "slate", "accent": "amber", "background": "ink", "contrast_notes": "High contrast dark system."},
                    "typography_strategy": {"heading_style": "Space Grotesk", "body_style": "IBM Plex Sans", "contrast_rationale": "Technical heading posture, readable body copy."},
                    "layout_principles": ["hero-first narrative", "clear cta progression"],
                    "motion_principles": ["low motion"],
                    "visual_density": "balanced",
                    "originality_level": "distinctive",
                    "anti_patterns_to_avoid": ["generic saas gradients", "default teal"],
                    "inspiration_references": [],
                    "differentiation_notes": "Governance-first positioning for AI work.",
                    "accessibility_notes": "Keep strong contrast and readable spacing.",
                    "evidence_expectations": ["show governance boundaries"],
                    "copy_tone": ["calm", "precise"]
                },
            },
            root=ATLAS_ROOT,
            project=project,
        )
    finally:
        shutil.rmtree(project, ignore_errors=True)

    assert any("verbal tone" in warning.lower() for warning in result["warnings"])


def test_brand_strategy_marks_ready_when_brand_direction_is_coherent():
    project = _make_temp_project()
    try:
        result = assess_brand_strategy_readiness(
            {
                "project_type": "frontend_app",
                "target_audience": "Technical builders and PMs using Codex.",
                "category": "ai governance operating system",
                "positioning": "A factory layer that structures AI delivery with visible rules and review gates.",
                "differentiation_notes": "Atlas positions AI work as a governed delivery system instead of a loose prompt playground.",
                "brand_profile": {
                    "brand_name": "Codex Atlas",
                    "audience": "Technical builders and PMs using Codex.",
                    "project_type": "frontend_app",
                    "personality_traits": ["technical", "structured", "credible"],
                    "mood_vector": {"premium": 6, "playful": 1, "technical": 9, "editorial": 6, "minimalist": 6, "bold": 6, "warm": 2, "futuristic": 7},
                    "color_strategy": {"primary": "graphite", "secondary": "slate", "accent": "amber", "background": "ink", "contrast_notes": "Anchor contrast around warm amber on deep graphite."},
                    "typography_strategy": {"heading_style": "Space Grotesk", "body_style": "IBM Plex Sans", "contrast_rationale": "Headlines feel architectural while body copy stays operational."},
                    "layout_principles": ["hero-first narrative", "clear cta progression"],
                    "motion_principles": ["low motion", "motion supports hierarchy"],
                    "visual_density": "balanced",
                    "originality_level": "distinctive",
                    "anti_patterns_to_avoid": ["generic saas gradients", "default teal"],
                    "inspiration_references": [],
                    "differentiation_notes": "Atlas positions AI work as a governed delivery system instead of a loose prompt playground.",
                    "accessibility_notes": "Keep high contrast, stable spacing and clear scanning hierarchy.",
                    "evidence_expectations": ["show governance boundaries", "clarify human review"],
                    "copy_tone": ["calm", "direct", "technical"],
                    "cta_rules": ["Start setup", "Create first project"]
                },
                "copywriting_conversion_posture": {
                    "copy_readiness_state": "ready",
                    "trust_score": 90,
                    "tone_consistency_score": 88,
                    "hero_message": {"cta_clear": True, "problem_visible": True},
                    "warnings": [],
                    "must_not_claim": []
                },
            },
            root=ATLAS_ROOT,
            project=project,
        )
    finally:
        shutil.rmtree(project, ignore_errors=True)

    assert result["brand_readiness_state"] == "ready"
    assert result["generic_brand_risk"] == "low"
    assert result["positioning_score"] >= 70
