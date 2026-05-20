import os

os.environ["ATLAS_DISABLE_EVENT_LOGS"] = "1"

from tests._support_paths import ATLAS_ROOT, WEB_ROOT
from tools.business_idea_simulation_readiness import assess_business_idea_simulation_readiness
from tools.quality_gate_report import build_quality_gate_report


def test_business_idea_simulation_requires_customer_definition():
    result = assess_business_idea_simulation_readiness(
        {
            "problem": "Small teams lose time coordinating Codex work without clear governance.",
            "value_proposition": "Give them a governed factory layer for AI coding workflows.",
        },
        root=ATLAS_ROOT,
    )

    assert result["readiness_state"] == "insufficient_data"
    assert "customer" in result["missing_inputs"]
    assert result["signal"] == "weak"


def test_business_idea_simulation_can_be_scenario_ready_with_basic_business_inputs():
    result = assess_business_idea_simulation_readiness(
        {
            "problem": "Technical PMs and builders waste time coordinating AI coding work manually.",
            "customer": "Technical PMs, builders and small product teams using Codex.",
            "value_proposition": "Codex Atlas adds structure, audits and reusable workflows on top of Codex.",
            "pricing": "Team subscription around USD 49-99 per seat or workspace.",
            "costs": "Primary costs are model usage, support and setup time.",
        },
        root=ATLAS_ROOT,
    )

    assert result["readiness_state"] == "scenario_ready"
    assert result["signal"] in {"incomplete", "promising"}
    assert result["must_not_claim_prediction"] is True


def test_business_idea_simulation_blocks_guaranteed_prediction_requests():
    result = assess_business_idea_simulation_readiness(
        {
            "problem": "We need to know if this startup will be profitable for sure.",
            "customer": "Startup founders.",
            "guaranteed_prediction_requested": True,
        },
        root=ATLAS_ROOT,
    )

    assert result["readiness_state"] == "blocked"
    assert result["must_not_claim_prediction"] is True
    assert result["signal"] == "weak"


def test_business_idea_simulation_keeps_profitability_confidence_low_without_costs_or_conversion():
    result = assess_business_idea_simulation_readiness(
        {
            "problem": "AI ops teams need lighter governance around coding agents.",
            "customer": "AI-enabled product teams.",
            "value_proposition": "A managed governance layer for agentic workflows.",
            "pricing": "Monthly subscription.",
            "channels": "Inbound content and community.",
        },
        root=ATLAS_ROOT,
    )

    assert result["profitability_confidence"] == "low"
    assert result["can_estimate_profitability"] is False
    assert "costs" in result["profitability_missing_inputs"]


def test_quality_gate_report_exposes_business_idea_simulation_posture():
    result = build_quality_gate_report(ATLAS_ROOT, WEB_ROOT)

    assert isinstance(result["business_idea_simulation_posture"], dict)
    assert result["business_idea_simulation_posture"]["must_not_claim_prediction"] is True
    assert result["business_idea_simulation_posture"]["advisory_only"] is True
    assert "readiness_state" in result["business_idea_simulation_posture"]
    assert "recommended_next_step" in result["business_idea_simulation_posture"]
