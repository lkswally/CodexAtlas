import os

os.environ["ATLAS_DISABLE_EVENT_LOGS"] = "1"

from tools.visual_intent_contract import infer_visual_intent_contract, validate_visual_intent_contract


def test_visual_intent_contract_accepts_complete_landing_contract():
    contract = {
        "audience": "for developers",
        "project_type": "frontend_app",
        "problem_or_promise": "Help teams create structured AI projects without chaos.",
        "mood_or_vibe": "editorial",
        "originality_level": "distinctive",
        "hero_direction": "system-first hero",
        "primary_cta_intent": "start setup",
        "visual_density": "medium",
        "motion_intensity": "low",
        "typography_intent": "serif plus disciplined sans",
        "color_strategy": "warm neutrals",
        "anti_patterns_to_avoid": ["avoid generic", "avoid saas"],
        "evidence_expectations": ["audit", "before pass"],
    }
    result = validate_visual_intent_contract(contract, project_type="frontend_app", source_text="landing page for developers")
    assert result["status"] == "ready"
    assert result["requires_contract"] is True
    assert result["missing_fields"] == []


def test_visual_intent_contract_flags_missing_audience():
    contract = {
        "project_type": "frontend_app",
        "problem_or_promise": "Help teams create structured AI projects without chaos.",
        "mood_or_vibe": "editorial",
        "originality_level": "balanced",
        "hero_direction": "system-first hero",
        "primary_cta_intent": "start setup",
        "visual_density": "medium",
        "motion_intensity": "low",
        "typography_intent": "serif",
        "color_strategy": "warm neutrals",
        "anti_patterns_to_avoid": ["avoid generic"],
        "evidence_expectations": ["audit"],
    }
    result = validate_visual_intent_contract(contract, project_type="frontend_app", source_text="landing page")
    assert result["status"] == "needs_input"
    assert "audience" in result["missing_fields"]


def test_visual_intent_contract_flags_missing_originality():
    contract = {
        "audience": "for developers",
        "project_type": "frontend_app",
        "problem_or_promise": "Help teams create structured AI projects without chaos.",
        "mood_or_vibe": "editorial",
        "hero_direction": "system-first hero",
        "primary_cta_intent": "start setup",
        "visual_density": "medium",
        "motion_intensity": "low",
        "typography_intent": "serif",
        "color_strategy": "warm neutrals",
        "anti_patterns_to_avoid": ["avoid generic"],
        "evidence_expectations": ["audit"],
    }
    result = validate_visual_intent_contract(contract, project_type="frontend_app", source_text="landing page")
    assert "originality_level" in result["missing_fields"]
    assert "missing_originality_level" in result["anti_generic_risks"]


def test_visual_intent_contract_rejects_invalid_originality_level():
    contract = {
        "audience": "for developers",
        "project_type": "frontend_app",
        "problem_or_promise": "Help teams create structured AI projects without chaos.",
        "mood_or_vibe": "editorial",
        "originality_level": "maximalist",
        "hero_direction": "system-first hero",
        "primary_cta_intent": "start setup",
        "visual_density": "medium",
        "motion_intensity": "low",
        "typography_intent": "serif",
        "color_strategy": "warm neutrals",
        "anti_patterns_to_avoid": ["avoid generic"],
        "evidence_expectations": ["audit"],
    }
    result = validate_visual_intent_contract(contract, project_type="frontend_app", source_text="landing page")
    assert "originality_level" in result["weak_fields"]


def test_backend_project_does_not_require_visual_intent_contract():
    contract = infer_visual_intent_contract(project_type="backend_service", brief="Build an API service for internal workflows.")
    result = validate_visual_intent_contract(contract, project_type="backend_service", source_text="api service")
    assert result["status"] == "skipped"
    assert result["requires_contract"] is False


def test_landing_project_requires_visual_intent_contract():
    contract = infer_visual_intent_contract(project_type="frontend_app", brief="Create a landing page for Atlas.")
    result = validate_visual_intent_contract(contract, project_type="frontend_app", source_text="landing page for Atlas")
    assert result["requires_contract"] is True
    assert result["status"] in {"ready", "needs_input"}
