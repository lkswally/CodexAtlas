import os

os.environ["ATLAS_DISABLE_EVENT_LOGS"] = "1"

from tools.priority_engine import build_execution_plan


def test_priority_engine_prefers_phase_guidance_when_phase_is_invalid():
    result = build_execution_plan(
        phase_guidance={
            "current_phase": "bootstrap",
            "recommended_next_steps": ["run audit-repo", "review generated structure"],
            "top_phase_risks": ["editing files before audit"],
        },
        phase_validity="invalid",
        top_priorities=[
            {
                "source": "design_intelligence_audit",
                "check": "cta_integrity",
                "severity": "high",
                "message": "Fix CTA hierarchy",
            }
        ],
        quick_wins=["Tighten hero copy", "Tighten hero copy"],
        intent_analysis={"missing_definition": []},
        skill_creation_signal={"should_create": False},
        overall_status="needs_improvement",
        feedback_analysis=None,
    )
    assert result["execution_plan"][0]["source"] == "phase"
    assert result["primary_action"] == "run audit-repo"


def test_priority_engine_reduces_noise_and_limits_output():
    result = build_execution_plan(
        phase_guidance={
            "current_phase": "audit",
            "recommended_next_steps": ["fix warnings", "validate design and structure"],
            "top_phase_risks": ["ignoring warnings"],
        },
        phase_validity="valid",
        top_priorities=[
            {"source": "design_intelligence_audit", "check": "content_density", "severity": "medium", "message": "Trim dense sections"},
            {"source": "design_intelligence_audit", "check": "content_density", "severity": "medium", "message": "Trim dense sections"},
            {"source": "surface-audit", "check": "readme_missing_command_mentions", "severity": "medium", "message": "Document key commands"},
        ],
        quick_wins=["Trim dense sections", "Refine CTA copy", "Refine CTA copy"],
        intent_analysis={"missing_definition": []},
        skill_creation_signal={"should_create": False},
        overall_status="needs_improvement",
        feedback_analysis=None,
    )
    assert len(result["execution_plan"]) <= 3
    assert len(result["quick_wins"]) <= 2
    assert len({item["action"] for item in result["execution_plan"]}) == len(result["execution_plan"])


def test_priority_engine_can_surface_intent_gap_before_other_actions():
    result = build_execution_plan(
        phase_guidance={
            "current_phase": "planning",
            "recommended_next_steps": ["finalize project brief", "choose project type"],
            "top_phase_risks": ["missing constraints"],
        },
        phase_validity="valid",
        top_priorities=[],
        quick_wins=[],
        intent_analysis={"missing_definition": ["scope_or_constraints_missing"]},
        skill_creation_signal={"should_create": False},
        overall_status="needs_improvement",
        feedback_analysis=None,
    )
    assert result["execution_plan"][0]["source"] in {"phase", "intent"}
    assert result["why_now"]


def test_priority_engine_adjusts_priority_using_feedback_history():
    result = build_execution_plan(
        phase_guidance={
            "current_phase": "audit",
            "recommended_next_steps": ["fix warnings", "validate design and structure"],
            "top_phase_risks": ["ignoring warnings"],
        },
        phase_validity="valid",
        top_priorities=[
            {"source": "design_intelligence_audit", "check": "content_density", "severity": "medium", "message": "Trim dense sections"},
            {"source": "design_intelligence_audit", "check": "cta_integrity", "severity": "medium", "message": "Strengthen CTA copy"},
        ],
        quick_wins=[],
        intent_analysis={"missing_definition": []},
        skill_creation_signal={"should_create": False},
        overall_status="needs_improvement",
        feedback_analysis={
            "action_feedback": [
                {"action": "Trim dense sections", "frequency": 2, "acceptance_rate": 0.0, "ignore_rate": 1.0, "last_decision": "ignored"},
                {"action": "Strengthen CTA copy", "frequency": 2, "acceptance_rate": 1.0, "ignore_rate": 0.0, "last_decision": "accepted"},
            ]
        },
    )
    actions = [item["action"] for item in result["execution_plan"]]
    assert "Strengthen CTA copy" in actions
    assert "Trim dense sections" not in actions
    assert any(item["feedback_weight"] == "up" for item in result["feedback_adjusted_priorities"])


def test_priority_engine_prefers_local_actions_over_external_tool_suggestions():
    result = build_execution_plan(
        phase_guidance={
            "current_phase": "planning",
            "recommended_next_steps": ["finalize project brief", "review local policies"],
            "top_phase_risks": ["missing constraints"],
        },
        phase_validity="valid",
        top_priorities=[
            {
                "source": "surface-audit",
                "check": "external_docs",
                "severity": "medium",
                "message": "Use GitHub CLI to inspect an external repository",
            }
        ],
        quick_wins=[],
        intent_analysis={"missing_definition": []},
        skill_creation_signal={"should_create": False},
        overall_status="needs_improvement",
        feedback_analysis=None,
    )
    actions = [item["action"] for item in result["execution_plan"]]
    assert "finalize project brief" in actions
    assert "Use GitHub CLI to inspect an external repository" not in actions
