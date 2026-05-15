from tools.intent_clarifier_contract import assess_intent_clarifier_contract


def test_intent_clarifier_accepts_complete_ui_contract():
    result = assess_intent_clarifier_contract(
        payload={
            "project_type": "frontend_app",
            "domain_context": "developer_tools",
            "target_audience": "for developers",
            "primary_goal": "Help teams bootstrap governed Codex projects.",
            "style_direction": "editorial technical",
            "originality_level": "distinctive",
            "success_criteria": "Users understand Atlas in the first viewport.",
            "constraints": ["read-only"],
        }
    )
    assert result["status"] == "ready"
    assert result["must_block_strong_ready"] is False


def test_intent_clarifier_flags_missing_audience():
    result = assess_intent_clarifier_contract(
        payload={
            "project_type": "frontend_app",
            "domain_context": "developer_tools",
            "primary_goal": "Ship a governed Atlas landing page.",
            "style_direction": "editorial",
            "originality_level": "balanced",
        }
    )
    assert result["status"] == "needs_input"
    assert "target_audience" in result["missing_questions"]


def test_intent_clarifier_flags_generic_style_answers():
    result = assess_intent_clarifier_contract(
        payload={
            "project_type": "frontend_app",
            "domain_context": "marketing_positioning",
            "target_audience": "for product teams",
            "primary_goal": "Present Atlas to teams.",
            "style_direction": "modern clean",
            "originality_level": "balanced",
        }
    )
    assert result["status"] == "needs_input"
    assert "style_direction" in result["weak_answers"]


def test_intent_clarifier_skips_backend_only_project():
    result = assess_intent_clarifier_contract(
        payload={
            "project_type": "backend_service",
            "primary_goal": "Provide a structured API."
        }
    )
    assert result["status"] == "skipped"
    assert result["requires_contract"] is False
