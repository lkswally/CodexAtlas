import os

os.environ["ATLAS_DISABLE_EVENT_LOGS"] = "1"

from tests._support_paths import WEB_ROOT
from tools.project_intent_analyzer import analyze_project_intent


def test_project_intent_analyzer_flags_missing_definition_for_vague_brief():
    result = analyze_project_intent(brief="Build something useful for Atlas.")
    assert result["status"] == "needs_input"
    assert result["clarity_score"] <= 7
    assert result["missing_definition"]
    assert result["project_type"] in {"unknown", "internal_tool", "frontend_app"}
    assert result["visual_intent_contract"]["status"] == "needs_input"
    assert "audience" in result["visual_intent_contract"]["missing_fields"]


def test_project_intent_analyzer_returns_structured_intent_for_codexatlas_web():
    result = analyze_project_intent(project=WEB_ROOT)
    assert result["status"] in {"ready", "needs_input"}
    assert result["project_type"] in {"internal_tool", "frontend_app"}
    assert result["objective"]
    assert result["risk_level"] in {"low", "medium", "high"}
    assert result["complexity"] in {"low", "medium", "high"}
    assert isinstance(result["missing_definition"], list)
    assert isinstance(result["visual_intent_contract"], dict)
    assert "required_fields" in result["visual_intent_contract"]
    assert "contract" in result["visual_intent_contract"]
    assert result["reasoning"]
