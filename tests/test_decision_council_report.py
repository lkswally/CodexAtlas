import os
from pathlib import Path

os.environ["ATLAS_DISABLE_EVENT_LOGS"] = "1"

from tools.decision_council_report import build_decision_council_report


ATLAS_ROOT = Path(r"C:\Proyectos\Codex-Atlas")
WEB_ROOT = Path(r"C:\Proyectos\CodexAtlas-Web")


def test_decision_council_recommends_review_for_architecture_and_external_tool_topics():
    result = build_decision_council_report(
        topic="Should Atlas use an MCP for this architecture decision before touching derived projects?",
        root=ATLAS_ROOT,
    )

    assert result["status"] == "ok"
    assert result["council_recommended"] is True
    assert result["agreement_level"] == "undetermined"
    assert any(item["trigger"] == "architecture" for item in result["risks"])
    assert any(item["trigger"] == "external_tooling" for item in result["risks"])
    assert result["role_briefs"][-1]["role"] == "Chairman"
    assert result["recommended_next_action"]


def test_decision_council_stays_light_for_simple_documentation_topics():
    result = build_decision_council_report(
        topic="Review a README typo and summarize the current docs change.",
        root=ATLAS_ROOT,
    )

    assert result["status"] == "ok"
    assert result["council_recommended"] is False
    assert result["decision"] == "A full decision council is not required for the current topic."
    assert result["agreement_level"] == "high"
    assert result["risks"] == []


def test_decision_council_can_include_local_project_phase_and_intent_context():
    result = build_decision_council_report(
        topic="Evaluate conflicting recommendations before changing this derived project.",
        root=ATLAS_ROOT,
        project=WEB_ROOT,
    )

    assert result["status"] == "ok"
    assert result["project_path"] == str(WEB_ROOT)
    assert isinstance(result["phase_context"], dict)
    assert result["phase_context"]["current_phase"]
    assert isinstance(result["intent_context"], dict)
    assert result["intent_context"]["project_type"]
    assert any(str(item).startswith("project_phase=") for item in result["evidence"])
