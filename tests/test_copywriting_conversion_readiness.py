import os
import shutil
from pathlib import Path
from uuid import uuid4

os.environ["ATLAS_DISABLE_EVENT_LOGS"] = "1"

from tests._support_paths import ATLAS_ROOT
from tools.copywriting_conversion_readiness import assess_copywriting_conversion_readiness


def _make_temp_project() -> Path:
    base = ATLAS_ROOT / "tests" / "_tmp_copywriting_conversion_cases"
    base.mkdir(parents=True, exist_ok=True)
    project = base / f"case_{uuid4().hex}"
    project.mkdir(parents=True, exist_ok=False)
    return project


def test_copywriting_conversion_needs_improvement_without_clear_audience():
    project = _make_temp_project()
    try:
        (project / "index.html").write_text(
            "<html><body><h1>Structured AI work without chaos</h1><p>Atlas keeps AI work controlled.</p><a>Start setup</a></body></html>",
            encoding="utf-8",
        )
        result = assess_copywriting_conversion_readiness(
            {
                "project_type": "frontend_app",
                "problem": "AI work gets chaotic without a system.",
                "value_proposition": "Atlas adds structure and governance.",
                "cta_labels": ["Start setup"],
            },
            root=ATLAS_ROOT,
            project=project,
        )
    finally:
        shutil.rmtree(project, ignore_errors=True)

    assert result["copy_readiness_state"] == "needs_improvement"
    assert "target_audience" in result["missing_inputs"]


def test_copywriting_conversion_needs_improvement_when_problem_is_missing_from_hero():
    project = _make_temp_project()
    try:
        result = assess_copywriting_conversion_readiness(
            {
                "project_type": "frontend_app",
                "target_audience": "Technical builders and PMs.",
                "hero_text": "A governed factory layer for Codex.",
                "value_proposition": "Atlas adds structure and quality gates.",
                "cta_labels": ["Create first project"],
            },
            root=ATLAS_ROOT,
            project=project,
        )
    finally:
        shutil.rmtree(project, ignore_errors=True)

    assert result["copy_readiness_state"] == "needs_improvement"
    assert result["hero_message"]["problem_visible"] is False


def test_copywriting_conversion_reduces_conversion_score_for_confusing_cta():
    project = _make_temp_project()
    try:
        result = assess_copywriting_conversion_readiness(
            {
                "project_type": "frontend_app",
                "target_audience": "Product teams using Codex.",
                "problem": "They lose time coordinating AI work manually.",
                "value_proposition": "Atlas gives them structure and visible gates.",
                "hero_text": "Structured AI work without chaos.",
                "cta_labels": ["Learn more"],
            },
            root=ATLAS_ROOT,
            project=project,
        )
    finally:
        shutil.rmtree(project, ignore_errors=True)

    assert result["conversion_score"] < 70
    assert any("CTA" in warning or "cta" in warning.lower() for warning in result["warnings"])


def test_copywriting_conversion_blocks_guaranteed_profitability_claims():
    project = _make_temp_project()
    try:
        result = assess_copywriting_conversion_readiness(
            {
                "project_type": "frontend_app",
                "page_text": "Usá Atlas y obtené rentabilidad garantizada para tu startup.",
                "cta_labels": ["Start setup"],
            },
            root=ATLAS_ROOT,
            project=project,
        )
    finally:
        shutil.rmtree(project, ignore_errors=True)

    assert result["copy_readiness_state"] == "blocked"
    assert "rentabilidad garantizada" in " ".join(result["must_not_claim"]).lower()


def test_copywriting_conversion_flags_generic_ai_filler():
    project = _make_temp_project()
    try:
        result = assess_copywriting_conversion_readiness(
            {
                "project_type": "frontend_app",
                "page_text": "Transformá tu negocio con IA y revolucioná tu operación.",
                "cta_labels": ["Start setup"],
            },
            root=ATLAS_ROOT,
            project=project,
        )
    finally:
        shutil.rmtree(project, ignore_errors=True)

    assert any("generic AI-style filler" in warning for warning in result["warnings"])


def test_copywriting_conversion_warns_when_form_lacks_next_step_clarity():
    project = _make_temp_project()
    try:
        result = assess_copywriting_conversion_readiness(
            {
                "project_type": "frontend_app",
                "target_audience": "Founders validating product ideas.",
                "problem": "They need a clearer decision process before building.",
                "value_proposition": "Atlas structures hypotheses, risks and next steps.",
                "hero_text": "Validate product ideas with governed AI workflows.",
                "cta_labels": ["Send idea"],
                "form_microcopy": "Email Idea Submit",
            },
            root=ATLAS_ROOT,
            project=project,
        )
    finally:
        shutil.rmtree(project, ignore_errors=True)

    assert any("what happens after submission" in warning.lower() for warning in result["warnings"])


def test_copywriting_conversion_marks_ready_when_core_message_is_clear():
    project = _make_temp_project()
    try:
        result = assess_copywriting_conversion_readiness(
            {
                "project_type": "frontend_app",
                "target_audience": "Technical builders and PMs using Codex.",
                "problem": "Teams lose control when AI work runs without roles, scope or visible checks.",
                "value_proposition": "Codex Atlas adds structure, governance and quality gates before files change.",
                "hero_text": "Build structured AI projects without chaos.",
                "cta_labels": ["Start setup", "Create first project"],
                "next_step": "After you start setup, Atlas runs the first audit and shows the next safe step.",
                "data_handling": "We only use your contact details to follow up on the request.",
                "proof_points": "Atlas keeps decisions visible and does not promise guaranteed outcomes.",
            },
            root=ATLAS_ROOT,
            project=project,
        )
    finally:
        shutil.rmtree(project, ignore_errors=True)

    assert result["copy_readiness_state"] == "ready"
    assert result["hero_message"]["cta_clear"] is True
    assert result["clarity_score"] >= 75
