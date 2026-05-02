import os
from pathlib import Path

os.environ["ATLAS_DISABLE_EVENT_LOGS"] = "1"

from tools.atlas_dispatcher import dispatch
from tools.prompt_builder import build_prompt


ATLAS_ROOT = Path(r"C:\Proyectos\Codex-Atlas")
WEB_ROOT = Path(r"C:\Proyectos\CodexAtlas-Web")


def test_prompt_builder_uses_phase_and_intent_for_existing_project():
    result = build_prompt(root=ATLAS_ROOT, project=WEB_ROOT)
    assert result["status"] == "ok"
    assert result["current_phase"] == "certified"
    assert result["prompt_kind"] == "next_iteration"
    assert "no tocar REYESOFT" in result["prompt"]
    assert "Fase actual: `certified`." in result["prompt"]
    assert isinstance(result["model_profile_recommendation"], dict)
    assert result["why_this_prompt"]
    assert isinstance(result["risks"], list)
    assert isinstance(result["validation_after_prompt"], list)


def test_prompt_builder_defaults_to_planning_for_new_brief():
    result = build_prompt(
        root=ATLAS_ROOT,
        brief="Create an internal tool site for Atlas onboarding with no deploy and a clear setup flow.",
    )
    assert result["status"] == "ok"
    assert result["current_phase"] == "planning"
    assert result["recommended_command"] == "project-bootstrap"
    assert "project-bootstrap" in result["prompt"]
    assert "Orden de fuentes si hace falta research" in result["prompt"]
    assert "primero revisar repo local" in result["prompt"]
    assert "no usar MCP real sin confirmación" in result["prompt"]
    assert result["model_profile_recommendation"]["recommended_model_profile"] in {"cost_saver", "deep_reasoning", "code_execution"}


def test_prompt_builder_surfaces_feedback_patterns_when_present():
    result = build_prompt(
        root=ATLAS_ROOT,
        project=WEB_ROOT,
        feedback_analysis={
            "detected_patterns": [
                {
                    "pattern": "Action `Trim dense sections` is repeatedly ignored.",
                    "recommendation": "Stop surfacing this action unless a new blocker reintroduces it.",
                }
            ]
        },
    )
    assert result["status"] == "ok"
    assert "Patrones de feedback a tener en cuenta" in result["prompt"]
    assert "Trim dense sections" in result["prompt"]


def test_prompt_builder_adds_research_guidance_when_definition_is_missing():
    result = build_prompt(
        root=ATLAS_ROOT,
        project=WEB_ROOT,
        intent_report={
            "project_type": "internal_tool",
            "objective": "Investigate external documentation posture.",
            "risk_level": "medium",
            "complexity": "medium",
            "missing_definition": ["reference_scope"],
            "evidence": [],
        },
    )
    assert result["status"] == "ok"
    assert "Orden de fuentes si hace falta research" in result["prompt"]
    assert "luego adapters curados" in result["prompt"]


def test_dispatcher_exposes_prompt_builder_and_project_intent_commands():
    prompt_result = dispatch("prompt-builder", root=ATLAS_ROOT, project=WEB_ROOT)
    intent_result = dispatch("project-intent-report", root=ATLAS_ROOT, project=WEB_ROOT)
    assert prompt_result.ok is True
    assert intent_result.ok is True
    assert prompt_result.output["result"]["status"] == "ok"
    assert intent_result.output["result"]["project_type"] == "internal_tool"
