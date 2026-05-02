import os
from pathlib import Path

os.environ["ATLAS_DISABLE_EVENT_LOGS"] = "1"

from tools.project_intent_analyzer import analyze_project_intent


WEB_ROOT = Path(r"C:\Proyectos\CodexAtlas-Web")


def test_project_intent_analyzer_flags_missing_definition_for_vague_brief():
    result = analyze_project_intent(brief="Build something useful for Atlas.")
    assert result["status"] == "needs_input"
    assert result["clarity_score"] <= 7
    assert result["missing_definition"]
    assert result["project_type"] in {"unknown", "internal_tool", "frontend_app"}


def test_project_intent_analyzer_returns_structured_intent_for_codexatlas_web():
    result = analyze_project_intent(project=WEB_ROOT)
    assert result["status"] in {"ready", "needs_input"}
    assert result["project_type"] == "internal_tool"
    assert result["objective"]
    assert result["risk_level"] in {"low", "medium", "high"}
    assert result["complexity"] in {"low", "medium", "high"}
    assert isinstance(result["missing_definition"], list)
    assert result["reasoning"]
