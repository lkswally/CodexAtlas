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


def test_prompt_builder_defaults_to_planning_for_new_brief():
    result = build_prompt(
        root=ATLAS_ROOT,
        brief="Create an internal tool site for Atlas onboarding with no deploy and a clear setup flow.",
    )
    assert result["status"] == "ok"
    assert result["current_phase"] == "planning"
    assert result["recommended_command"] == "project-bootstrap"
    assert "project-bootstrap" in result["prompt"]


def test_dispatcher_exposes_prompt_builder_and_project_intent_commands():
    prompt_result = dispatch("prompt-builder", root=ATLAS_ROOT, project=WEB_ROOT)
    intent_result = dispatch("project-intent-report", root=ATLAS_ROOT, project=WEB_ROOT)
    assert prompt_result.ok is True
    assert intent_result.ok is True
    assert prompt_result.output["result"]["status"] == "ok"
    assert intent_result.output["result"]["project_type"] == "internal_tool"
