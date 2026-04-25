import os
from pathlib import Path

os.environ["ATLAS_DISABLE_EVENT_LOGS"] = "1"

from tools.design_intelligence_audit import (
    anti_generic_ui_audit,
    design_system_review,
    visual_direction_checkpoint,
)


WEB_ROOT = Path(r"C:\Proyectos\CodexAtlas-Web")


def test_visual_direction_checkpoint_requires_missing_inputs_when_brief_is_vague():
    result = visual_direction_checkpoint("Create a site and make it look good.")
    assert result["status"] == "needs_input"
    assert "audience_missing_or_implicit" in result["warnings"]
    assert "mood_or_vibe_missing" in result["warnings"]


def test_visual_direction_checkpoint_detects_explicit_direction():
    result = visual_direction_checkpoint(
        "Create an internal tool landing page for developers with a premium editorial vibe and balanced originality."
    )
    assert result["status"] == "ready"
    assert result["checkpoint"]["audience"] is not None
    assert result["checkpoint"]["mood_or_vibe"] is not None


def test_anti_generic_ui_audit_returns_structured_output_for_codexatlas_web():
    result = anti_generic_ui_audit(WEB_ROOT)
    assert result["status"] in {"pass", "needs_attention"}
    assert isinstance(result["warnings"], list)
    assert isinstance(result["evidence"], list)
    assert result["next_action"]
    assert result["prioritized_problems"]
    assert any(check["id"] == "cta_clarity" for check in result["checks"])


def test_design_system_review_returns_design_findings():
    result = design_system_review(WEB_ROOT)
    assert result["status"] in {"pass", "needs_attention"}
    assert result["design_system_findings"]
    assert any(item["id"] == "typography_coherence" for item in result["design_system_findings"])
