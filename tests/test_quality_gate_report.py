import os
from pathlib import Path
from unittest.mock import patch

os.environ["ATLAS_DISABLE_EVENT_LOGS"] = "1"

from tests._support_paths import ATLAS_ROOT, WEB_ROOT
from tools.quality_gate_report import build_quality_gate_report, verify_file_change_declaration


def test_file_change_declaration_verification_ready_when_sets_match():
    result = verify_file_change_declaration(
        declared_files=["./tools/example.py", "tests\\test_example.py"],
        actual_files=["tools/example.py", "tests/test_example.py"],
    )
    assert result["status"] == "ready"
    assert result["missing_from_declaration"] == []
    assert result["declared_but_not_changed"] == []
    assert result["advisory_only"] is True


def test_file_change_declaration_verification_flags_missing_declaration():
    result = verify_file_change_declaration(declared_files=[], actual_files=["tools/example.py"])
    assert result["status"] == "missing_declaration"
    assert result["missing_from_declaration"] == ["tools/example.py"]
    assert result["declared_but_not_changed"] == []


def test_file_change_declaration_verification_flags_mismatch_both_ways():
    result = verify_file_change_declaration(
        declared_files=["tools/declared.py", "tests/shared.py"],
        actual_files=["tools/actual.py", "tests/shared.py"],
    )
    assert result["status"] == "mismatch"
    assert result["missing_from_declaration"] == ["tools/actual.py"]
    assert result["declared_but_not_changed"] == ["tools/declared.py"]


def test_file_change_declaration_verification_not_applicable_without_changes():
    result = verify_file_change_declaration(declared_files=[], actual_files=[])
    assert result["status"] == "not_applicable"
    assert result["declared_files"] == []
    assert result["actual_files"] == []



def test_quality_gate_report_returns_real_structured_summary_for_codexatlas_web():
    result = build_quality_gate_report(ATLAS_ROOT, WEB_ROOT)
    assert result["status"] == "ok"
    assert result["project_path"] == str(WEB_ROOT)
    assert result["overall_status"] in {"ready", "needs_improvement", "not_ready"}
    assert result["confidence_level"] in {"low", "medium", "high"}
    assert result["public_readiness"] in {"ready", "needs_improvement", "not_ready"}
    assert isinstance(result["landing_score"], int)
    assert result["phase_validity"] in {"valid", "invalid"}
    assert isinstance(result["phase_alignment"], dict)
    assert isinstance(result["blockers"], list)
    assert isinstance(result["warnings"], list)
    assert isinstance(result["top_priorities"], list)
    assert len(result["top_priorities"]) <= 3
    assert result["summary_for_human"]
    assert result["source_reports"]["project-phase-report"]["status"] == "ok"
    assert result["source_reports"]["audit-repo"]["status"] in {"ok", "failed"}
    assert result["source_reports"]["certify-project"]["status"] in {"ok", "failed"}
    assert result["source_reports"]["surface-audit"]["status"] in {"ok", "failed"}
    assert result["source_reports"]["project_intent_analyzer"]["status"] == "ok"
    assert result["source_reports"]["prompt_builder"]["status"] == "ok"
    assert result["source_reports"]["skill_evaluator"]["status"] == "ok"
    assert result["source_reports"]["skill_improvement_review"]["status"] == "ok"
    assert result["source_reports"]["feedback_analyzer"]["status"] == "ok"
    assert result["source_reports"]["model_router"]["status"] == "ok"
    assert result["source_reports"]["error_pattern_analyzer"]["status"] == "ok"
    assert result["source_reports"]["chrome_devtools_mcp_readiness"]["status"] == "ok"
    assert result["source_reports"]["copywriting_conversion_readiness"]["status"] == "ok"
    assert isinstance(result["intent_analysis"], dict)
    assert isinstance(result["design_quality_posture"], dict)
    assert isinstance(result["model_cost_control_posture"], dict)
    assert isinstance(result["business_idea_simulation_posture"], dict)
    assert isinstance(result["copywriting_conversion_posture"], dict)
    assert isinstance(result["visual_intent_posture"], dict)
    assert result["visual_intent_posture"]["advisory_only"] is True
    assert isinstance(result["brand_profile_posture"], dict)
    assert result["brand_profile_posture"]["advisory_only"] is True
    assert isinstance(result["ui_pre_return_posture"], dict)
    assert result["ui_pre_return_posture"]["advisory_only"] is True
    assert isinstance(result["model_routing"], dict)
    assert result["model_routing"]["active_runtime_model"] == "manual_or_unknown"
    assert result["model_routing"]["model_switch_mode"] == "manual_required"
    assert result["model_routing"]["recommended_model_is_advisory"] is True
    assert (
        result["model_routing"]["user_action_required"]
        == "Select the recommended model manually in Codex Desktop before running this task."
    )
    assert result["model_routing"]["can_auto_switch"] is False
    assert result["model_routing"]["auto_switch_method"] == "not_available"
    assert isinstance(result["external_tool_posture"], dict)
    assert result["external_tool_posture"]["source_sufficiency"] in {
        "local_only",
        "adapter_enough",
        "external_recommended",
        "external_required",
    }
    assert result["external_tool_posture"]["external_tools_allowed"] is False
    assert result["external_tool_posture"]["mcp_allowed"] is False
    assert isinstance(result["prompt_guidance"], dict)
    assert isinstance(result["skill_creation_signal"], dict)
    assert isinstance(result["skill_lifecycle_posture"], dict)
    assert isinstance(result["skill_improvement_posture"], dict)
    assert result["skill_improvement_posture"]["advisory_only"] is True
    assert isinstance(result["creative_pipeline_posture"], dict)
    assert result["creative_pipeline_posture"]["advisory_only"] is True
    assert isinstance(result["component_inspiration_posture"], dict)
    assert result["component_inspiration_posture"]["advisory_only"] is True
    assert isinstance(result["visual_qa_readiness_posture"], dict)
    assert result["visual_qa_readiness_posture"]["advisory_only"] is True
    assert isinstance(result["visual_fidelity_posture"], dict)
    assert result["visual_fidelity_posture"]["advisory_only"] is True
    assert isinstance(result["chrome_devtools_mcp_posture"], dict)
    assert result["chrome_devtools_mcp_posture"]["auto_activate"] is False
    assert result["chrome_devtools_mcp_posture"]["telemetry_risk"] in {"low", "medium", "high"}
    assert isinstance(result["error_learning_posture"], dict)
    assert result["error_learning_posture"]["advisory_only"] is True
    assert isinstance(result["codex_runtime_posture"], dict)
    assert result["codex_runtime_posture"]["advisory_only"] is True
    assert isinstance(result["atlas_memory_posture"], dict)
    assert result["atlas_memory_posture"]["advisory_only"] is True
    assert isinstance(result["evidence_collector_posture"], dict)
    assert result["evidence_collector_posture"]["advisory_only"] is True
    assert isinstance(result["change_proposal_posture"], dict)
    assert result["change_proposal_posture"]["advisory_only"] is True
    assert isinstance(result["file_change_declaration_posture"], dict)
    assert result["file_change_declaration_posture"]["advisory_only"] is True
    assert result["source_reports"]["file_change_declaration_verification"]["status"] == "ok"
    assert isinstance(result["skill_registry_index_first_posture"], dict)
    assert result["skill_registry_index_first_posture"]["advisory_only"] is True
    assert isinstance(result["ui_ux_design_system_posture"], dict)
    assert result["ui_ux_design_system_posture"]["advisory_only"] is True
    assert isinstance(result["component_library_posture"], dict)
    assert isinstance(result["repo_graph_posture"], dict)
    assert result["repo_graph_posture"]["advisory_only"] is True
    assert result["business_idea_simulation_posture"]["advisory_only"] is True
    assert result["copywriting_conversion_posture"]["advisory_only"] is True
    assert isinstance(result["system_learning"], dict)
    assert isinstance(result["execution_plan"], list)
    assert len(result["execution_plan"]) <= 3
    if result["execution_plan"]:
        first_step = result["execution_plan"][0]
        assert "conflict_rule" in first_step
        assert "recommended_model" in first_step
        assert "fallback_model" in first_step
        assert "cheaper_alternative_model" in first_step
        assert first_step["active_runtime_model"] == "manual_or_unknown"
        assert first_step["model_switch_mode"] == "manual_required"
        assert first_step["recommended_model_is_advisory"] is True
        assert (
            first_step["user_action_required"]
            == "Select the recommended model manually in Codex Desktop before running this task."
        )
        assert first_step["can_auto_switch"] is False
        assert first_step["auto_switch_method"] == "not_available"
        assert "requires_user_confirmation" in first_step
        assert first_step["why_model"]
        avoid_steps = [step for step in result["execution_plan"] if str(step.get("action", "")).lower().startswith("avoid ")]
        if avoid_steps:
            assert isinstance(avoid_steps[0]["recommended_model"], str)
            assert avoid_steps[0]["recommended_model"]
    assert len(result["quick_wins"]) <= 2
    assert isinstance(result["feedback_adjusted_priorities"], list)
    assert isinstance(result["detected_patterns"], list)
    assert result["primary_action"] is not None
    assert result["why_now"]
    assert isinstance(result["decision_feedback"], dict)
    assert result["decision_feedback"]["status"] in {"ok", "failed"}
    assert result["recommended_next_action"]
    assert "recommended_state" in result["skill_lifecycle_posture"]
    assert "lifecycle_recommendation" in result["skill_lifecycle_posture"]
    assert "promotion_blockers" in result["skill_lifecycle_posture"]
    assert "reviewed_skills" in result["skill_improvement_posture"]
    assert "recommended_next_actions" in result["skill_improvement_posture"]
    assert "available_services" in result["creative_pipeline_posture"]
    assert "watchlist_profiles" in result["creative_pipeline_posture"]
    assert "available_services" in result["component_inspiration_posture"]
    assert "blocked_profiles" in result["component_inspiration_posture"]
    assert "playwright_available" in result["visual_qa_readiness_posture"]
    assert "blocked_profiles" in result["visual_qa_readiness_posture"]
    assert "fidelity_state" in result["visual_fidelity_posture"]
    assert "can_support_visual_pass" in result["visual_fidelity_posture"]
    assert "recommended_flags" in result["chrome_devtools_mcp_posture"]
    assert "--no-usage-statistics" in result["chrome_devtools_mcp_posture"]["recommended_flags"]
    assert "triggered_signals" in result["error_learning_posture"]
    assert "recommended_model_tier" in result["model_cost_control_posture"]
    assert "fallback_posture" in result["model_cost_control_posture"]
    assert "must_not_claim_prediction" in result["business_idea_simulation_posture"]
    assert "recommended_next_step" in result["business_idea_simulation_posture"]
    assert result["copywriting_conversion_posture"]["copy_readiness_state"] in {
        "ready",
        "needs_improvement",
        "blocked",
        "not_applicable",
    }
    assert isinstance(result["copywriting_conversion_posture"]["clarity_score"], int)
    assert isinstance(result["copywriting_conversion_posture"]["conversion_score"], int)
    assert isinstance(result["copywriting_conversion_posture"]["trust_score"], int)
    assert isinstance(result["copywriting_conversion_posture"]["tone_consistency_score"], int)
    assert isinstance(result["copywriting_conversion_posture"]["warnings"], list)
    assert isinstance(result["copywriting_conversion_posture"]["recommended_changes"], list)
    assert isinstance(result["copywriting_conversion_posture"]["hero_message"], dict)
    assert "configured_mcp_servers" in result["codex_runtime_posture"]
    assert "available_sources" in result["atlas_memory_posture"]
    assert "missing_evidence" in result["evidence_collector_posture"]
    assert "missing_artifacts" in result["change_proposal_posture"]
    assert "skills_indexed" in result["skill_registry_index_first_posture"]
    assert "recommended_pattern" in result["ui_ux_design_system_posture"]
    assert "frontend_motion_library_posture" in result["ui_ux_design_system_posture"]
    assert "component_library_posture" in result["ui_ux_design_system_posture"]
    assert "tailgrids_fit" in result["component_library_posture"]
    assert "recommended_use" in result["component_library_posture"]
    assert "repo_graph_recommended" in result["repo_graph_posture"]
    assert "codegraph_detected" in result["repo_graph_posture"]
    assert "required_fields" in result["visual_intent_posture"]
    assert "missing_fields" in result["visual_intent_posture"]
    assert "required_fields" in result["brand_profile_posture"]
    assert "missing_fields" in result["brand_profile_posture"]


def test_quality_gate_report_exposes_creative_pipeline_posture():
    result = build_quality_gate_report(ATLAS_ROOT, WEB_ROOT)
    assert isinstance(result["creative_pipeline_posture"], dict)
    assert result["creative_pipeline_posture"]["advisory_only"] is True
    assert "available_services" in result["creative_pipeline_posture"]
    assert "blocked_profiles" in result["creative_pipeline_posture"]


def test_quality_gate_report_detects_explicit_brand_profile_from_derived_project_artifact():
    result = build_quality_gate_report(ATLAS_ROOT, WEB_ROOT)
    assert result["brand_profile_posture"]["explicit_profile_present"] is True
    assert result["brand_profile_posture"]["profile_source"] == "explicit"
    assert result["brand_profile_posture"]["profile_status"] in {"ready", "needs_input"}


def test_quality_gate_report_exposes_component_inspiration_posture():
    result = build_quality_gate_report(ATLAS_ROOT, WEB_ROOT)
    assert isinstance(result["component_inspiration_posture"], dict)
    assert result["component_inspiration_posture"]["advisory_only"] is True
    assert "available_services" in result["component_inspiration_posture"]
    assert "blocked_profiles" in result["component_inspiration_posture"]


def test_quality_gate_report_exposes_visual_qa_readiness_posture():
    result = build_quality_gate_report(ATLAS_ROOT, WEB_ROOT)
    assert isinstance(result["visual_qa_readiness_posture"], dict)
    assert result["visual_qa_readiness_posture"]["advisory_only"] is True
    assert "playwright_available" in result["visual_qa_readiness_posture"]
    assert "blocked_profiles" in result["visual_qa_readiness_posture"]


def test_quality_gate_report_exposes_visual_fidelity_posture():
    result = build_quality_gate_report(ATLAS_ROOT, WEB_ROOT)
    assert isinstance(result["visual_fidelity_posture"], dict)
    assert result["visual_fidelity_posture"]["advisory_only"] is True
    assert "fidelity_state" in result["visual_fidelity_posture"]
    assert "must_not_claim_visual_pass_without_evidence" in result["visual_fidelity_posture"]


def test_quality_gate_report_exposes_chrome_devtools_mcp_posture():
    result = build_quality_gate_report(ATLAS_ROOT, WEB_ROOT)
    assert isinstance(result["chrome_devtools_mcp_posture"], dict)
    assert result["chrome_devtools_mcp_posture"]["auto_activate"] is False
    assert result["chrome_devtools_mcp_posture"]["activation_mode"] == "manual_opt_in"
    assert result["chrome_devtools_mcp_posture"]["telemetry_risk"] in {"low", "medium", "high"}
    assert result["chrome_devtools_mcp_posture"]["browser_profile_risk"] in {"low", "medium", "high"}
    assert "--no-usage-statistics" in result["chrome_devtools_mcp_posture"]["recommended_flags"]


def test_quality_gate_report_exposes_copywriting_conversion_posture():
    result = build_quality_gate_report(ATLAS_ROOT, WEB_ROOT)
    assert isinstance(result["copywriting_conversion_posture"], dict)
    assert result["copywriting_conversion_posture"]["advisory_only"] is True
    assert result["copywriting_conversion_posture"]["copy_readiness_state"] in {
        "ready",
        "needs_improvement",
        "blocked",
        "not_applicable",
    }
    assert isinstance(result["copywriting_conversion_posture"]["clarity_score"], int)
    assert isinstance(result["copywriting_conversion_posture"]["conversion_score"], int)
    assert isinstance(result["copywriting_conversion_posture"]["trust_score"], int)
    assert isinstance(result["copywriting_conversion_posture"]["tone_consistency_score"], int)
    assert isinstance(result["copywriting_conversion_posture"]["warnings"], list)
    assert isinstance(result["copywriting_conversion_posture"]["recommended_changes"], list)


def test_quality_gate_report_exposes_error_learning_and_codex_runtime_postures():
    result = build_quality_gate_report(ATLAS_ROOT, WEB_ROOT)
    assert isinstance(result["error_learning_posture"], dict)
    assert result["error_learning_posture"]["advisory_only"] is True
    assert "triggered_signals" in result["error_learning_posture"]
    assert isinstance(result["codex_runtime_posture"], dict)
    assert result["codex_runtime_posture"]["advisory_only"] is True
    assert "configured_mcp_servers" in result["codex_runtime_posture"]
    assert isinstance(result["atlas_memory_posture"], dict)
    assert result["atlas_memory_posture"]["advisory_only"] is True
    assert "available_sources" in result["atlas_memory_posture"]
    assert isinstance(result["evidence_collector_posture"], dict)
    assert result["evidence_collector_posture"]["advisory_only"] is True
    assert "missing_evidence" in result["evidence_collector_posture"]
    assert isinstance(result["change_proposal_posture"], dict)
    assert result["change_proposal_posture"]["advisory_only"] is True
    assert "missing_artifacts" in result["change_proposal_posture"]
    assert isinstance(result["skill_registry_index_first_posture"], dict)
    assert result["skill_registry_index_first_posture"]["advisory_only"] is True
    assert "skills_indexed" in result["skill_registry_index_first_posture"]
    assert isinstance(result["ui_ux_design_system_posture"], dict)
    assert result["ui_ux_design_system_posture"]["advisory_only"] is True
    assert "recommended_pattern" in result["ui_ux_design_system_posture"]
    assert isinstance(result["component_library_posture"], dict)
    assert "tailgrids_fit" in result["component_library_posture"]
    assert isinstance(result["repo_graph_posture"], dict)
    assert result["repo_graph_posture"]["advisory_only"] is True
    assert "repo_graph_recommended" in result["repo_graph_posture"]


def test_quality_gate_report_uses_existing_outputs_to_mark_not_ready():
    phase_report = {
        "ok": True,
        "result": {
            "status": "ok",
            "current_phase": "audit",
            "confidence": "high",
            "blocked_actions": [],
            "next_valid_phases": ["certified"],
            "recommended_actions": ["Run certify-project once audit findings are resolved."],
        },
    }
    fake_audit = {"ok": True, "result": {"status": "ok", "findings": []}}
    fake_certify = {
        "ok": True,
        "result": {
            "status": "partial",
            "blockers": [
                {
                    "severity": "blocker",
                    "code": "missing_required_file",
                    "message": "Missing README.md.",
                    "path": "C:/fake/README.md",
                }
            ],
            "warnings": [],
        },
    }
    fake_surface = {"ok": True, "result": {"status": "ok", "warnings": [], "recommendations": []}}
    fake_design = {
        "status": "pass",
        "public_readiness": "ready",
        "landing_score": 96,
        "warnings": [],
        "quick_wins": [],
        "checks": [],
        "recommendation_sources": [],
        "ui_pre_return_review": {"status": "pass", "pass_ready": True, "warnings": [], "blockers": []},
    }

    def fake_dispatch(command_id, root=None, project=None):
        class _Res:
            def __init__(self, output):
                self.output = output

        mapping = {
            "project-phase-report": phase_report,
            "audit-repo": fake_audit,
            "certify-project": fake_certify,
            "surface-audit": fake_surface,
        }
        return _Res(mapping[command_id])

    with patch("tools.quality_gate_report._dispatch_output", side_effect=lambda command_id, root=None, project=None: fake_dispatch(command_id, root=root, project=project).output):
        with patch("tools.quality_gate_report.anti_generic_ui_audit", return_value=fake_design):
            with patch("tools.quality_gate_report.assess_intent_clarifier_contract", return_value={"status": "ready", "requires_contract": True, "required_questions": [], "answered_questions": [], "missing_questions": [], "weak_answers": [], "must_block_strong_ready": False, "requires_human_clarification": False, "next_action": "Proceed.", "why": "Ready.", "advisory_only": True}):
                with patch("tools.quality_gate_report.assess_brand_json_v2_readiness", return_value={"status": "ready", "requires_brand_json_v2": True, "explicit_profile_present": True, "missing_sections": [], "weak_sections": [], "anti_generic_risks": [], "derivative_risks": [], "accessibility_risks": [], "export_candidate": True, "evidence_expectations": ["palette rationale"], "next_action": "Proceed.", "why": "Ready.", "advisory_only": True}):
                    with patch("tools.quality_gate_report.audit_frontend_auto_readiness", return_value={"status": "ready", "can_support_pre_return": True, "blockers": [], "warnings": [], "ready_guardrails": [], "missing_guardrails": [], "evidence_gaps": [], "watchlist_dependencies": [], "recommended_next_action": "Proceed.", "why": "Ready.", "advisory_only": True}):
                        with patch("tools.quality_gate_report.assess_copywriting_conversion_readiness", return_value={"status": "ok", "copy_readiness_state": "ready", "clarity_score": 90, "conversion_score": 90, "trust_score": 90, "tone_consistency_score": 90, "hero_message": {"clear_for_target_audience": True, "problem_visible": True, "value_proposition_visible": True, "cta_clear": True}, "warnings": [], "risks": [], "missing_inputs": [], "recommended_changes": [], "must_not_claim": [], "why": "Ready.", "advisory_only": True}):
                            result = build_quality_gate_report(ATLAS_ROOT, WEB_ROOT)

    assert result["overall_status"] == "not_ready"
    assert result["confidence_level"] == "high"
    assert result["blockers"]
    assert result["top_priorities"][0]["source"] == "certify-project"
    assert "not ready" in result["summary_for_human"].lower()


def test_quality_gate_report_priorities_come_from_existing_design_recommendation_sources():
    phase_report = {
        "ok": True,
        "result": {
            "status": "ok",
            "current_phase": "audit",
            "confidence": "high",
            "blocked_actions": [],
            "next_valid_phases": ["certified"],
            "recommended_actions": ["Run certify-project once audit findings are resolved."],
        },
    }
    fake_audit = {"ok": True, "result": {"status": "ok", "findings": []}}
    fake_certify = {"ok": True, "result": {"status": "ok", "blockers": [], "warnings": []}}
    fake_surface = {"ok": True, "result": {"status": "ok", "warnings": [], "recommendations": []}}
    fake_design = {
        "status": "needs_attention",
        "public_readiness": "needs_improvement",
        "landing_score": 82,
        "warnings": ["typography_coherence:warning"],
        "quick_wins": ["Replace the generic body sans with a more intentional family."],
        "checks": [],
        "recommendation_sources": [
            {
                "recommendation": "Replace the generic body sans with a more intentional family.",
                "originating_check": "typography_coherence",
                "evidence": ["body_font=Segoe UI"],
                "severity": "medium",
                "status": "warning",
            }
        ],
    }

    def fake_dispatch(command_id, root=None, project=None):
        class _Res:
            def __init__(self, output):
                self.output = output

        mapping = {
            "project-phase-report": phase_report,
            "audit-repo": fake_audit,
            "certify-project": fake_certify,
            "surface-audit": fake_surface,
        }
        return _Res(mapping[command_id])

    with patch("tools.quality_gate_report._dispatch_output", side_effect=lambda command_id, root=None, project=None: fake_dispatch(command_id, root=root, project=project).output):
        with patch("tools.quality_gate_report.anti_generic_ui_audit", return_value=fake_design):
            with patch("tools.quality_gate_report.assess_intent_clarifier_contract", return_value={"status": "ready", "requires_contract": True, "required_questions": [], "answered_questions": [], "missing_questions": [], "weak_answers": [], "must_block_strong_ready": False, "requires_human_clarification": False, "next_action": "Proceed.", "why": "Ready.", "advisory_only": True}):
                with patch("tools.quality_gate_report.assess_brand_json_v2_readiness", return_value={"status": "ready", "requires_brand_json_v2": True, "explicit_profile_present": True, "missing_sections": [], "weak_sections": [], "anti_generic_risks": [], "derivative_risks": [], "accessibility_risks": [], "export_candidate": True, "evidence_expectations": ["palette rationale"], "next_action": "Proceed.", "why": "Ready.", "advisory_only": True}):
                    with patch("tools.quality_gate_report.audit_frontend_auto_readiness", return_value={"status": "ready", "can_support_pre_return": True, "blockers": [], "warnings": [], "ready_guardrails": [], "missing_guardrails": [], "evidence_gaps": [], "watchlist_dependencies": [], "recommended_next_action": "Proceed.", "why": "Ready.", "advisory_only": True}):
                        with patch("tools.quality_gate_report.assess_copywriting_conversion_readiness", return_value={"status": "ok", "copy_readiness_state": "ready", "clarity_score": 90, "conversion_score": 90, "trust_score": 90, "tone_consistency_score": 90, "hero_message": {"clear_for_target_audience": True, "problem_visible": True, "value_proposition_visible": True, "cta_clear": True}, "warnings": [], "risks": [], "missing_inputs": [], "recommended_changes": [], "must_not_claim": [], "why": "Ready.", "advisory_only": True}):
                            result = build_quality_gate_report(ATLAS_ROOT, WEB_ROOT)

    assert result["overall_status"] == "needs_improvement"
    assert result["public_readiness"] == "needs_improvement"
    assert result["external_tool_posture"]["source_sufficiency"] == "adapter_enough"
    assert result["external_tool_posture"]["recommended_source_layer"] == "curated_internal_adapters"
    assert result["top_priorities"][0]["check"] == "typography_coherence"
    assert result["quick_wins"][0] == "Replace the generic body sans with a more intentional family."
    assert result["execution_plan"]
    assert result["primary_action"]


def test_quality_gate_report_enriches_execution_plan_with_per_action_model_recommendations():
    phase_report = {
        "ok": True,
        "result": {
            "status": "ok",
            "current_phase": "audit",
            "confidence": "high",
            "blocked_actions": [],
            "next_valid_phases": ["certified"],
            "recommended_actions": ["Run certify-project once audit findings are resolved."],
        },
    }
    fake_audit = {"ok": True, "result": {"status": "ok", "findings": []}}
    fake_certify = {"ok": True, "result": {"status": "ok", "blockers": [], "warnings": []}}
    fake_surface = {"ok": True, "result": {"status": "ok", "warnings": [], "recommendations": []}}
    fake_design = {
        "status": "needs_attention",
        "public_readiness": "needs_improvement",
        "landing_score": 82,
        "warnings": ["content_density:warning"],
        "quick_wins": ["Trim dense sections"],
        "checks": [],
        "recommendation_sources": [
            {
                "recommendation": "Trim dense sections",
                "originating_check": "content_density",
                "evidence": ["long_sections=3"],
                "severity": "medium",
                "status": "warning",
            }
        ],
        "ui_pre_return_review": {"status": "pass", "pass_ready": True, "warnings": [], "blockers": []},
    }

    def fake_dispatch(command_id, root=None, project=None):
        class _Res:
            def __init__(self, output):
                self.output = output

        mapping = {
            "project-phase-report": phase_report,
            "audit-repo": fake_audit,
            "certify-project": fake_certify,
            "surface-audit": fake_surface,
        }
        return _Res(mapping[command_id])

    routed_models = [
        {
            "status": "ok",
            "recommended_model": "GPT-5.4",
            "fallback_model": "GPT-5.2",
            "cost_saver_model": "GPT-5.4-Mini",
            "requires_user_confirmation": True,
            "why": "Model route for general gate context.",
        },
        {
            "status": "ok",
            "recommended_model": "GPT-5.4",
            "fallback_model": "GPT-5.2",
            "cost_saver_model": "GPT-5.4-Mini",
            "requires_user_confirmation": True,
            "why": "Model route for phase action.",
        },
        {
            "status": "ok",
            "recommended_model": "GPT-5.4-Mini",
            "fallback_model": "GPT-5.1-Codex-Mini",
            "cost_saver_model": "GPT-5.1-Codex-Mini",
            "requires_user_confirmation": True,
            "why": "Model route for quick win.",
        },
        {
            "status": "ok",
            "recommended_model": "GPT-5.2",
            "fallback_model": "GPT-5.4",
            "cost_saver_model": "GPT-5.4-Mini",
            "requires_user_confirmation": True,
            "why": "Model route for audit-oriented warning.",
        },
    ]

    with patch("tools.quality_gate_report._dispatch_output", side_effect=lambda command_id, root=None, project=None: fake_dispatch(command_id, root=root, project=project).output):
        with patch("tools.quality_gate_report.anti_generic_ui_audit", return_value=fake_design):
            with patch("tools.quality_gate_report.recommend_model_profile", side_effect=routed_models):
                result = build_quality_gate_report(ATLAS_ROOT, WEB_ROOT)

    assert result["execution_plan"]
    first_step = result["execution_plan"][0]
    assert first_step["recommended_model"]
    assert first_step["fallback_model"]
    assert first_step["cheaper_alternative_model"]
    assert first_step["active_runtime_model"] == "manual_or_unknown"
    assert first_step["model_switch_mode"] == "manual_required"
    assert first_step["recommended_model_is_advisory"] is True
    assert first_step["can_auto_switch"] is False
    assert first_step["auto_switch_method"] == "not_available"
    assert isinstance(first_step["requires_user_confirmation"], bool)
    assert first_step["why_model"]


def test_quality_gate_report_surfaces_relevant_decision_feedback():
    phase_report = {
        "ok": True,
        "result": {
            "status": "ok",
            "current_phase": "audit",
            "confidence": "high",
            "blocked_actions": [],
            "next_valid_phases": ["certified"],
            "recommended_actions": ["Run certify-project once audit findings are resolved."],
        },
    }
    fake_audit = {"ok": True, "result": {"status": "ok", "findings": []}}
    fake_certify = {"ok": True, "result": {"status": "ok", "blockers": [], "warnings": []}}
    fake_surface = {"ok": True, "result": {"status": "ok", "warnings": [], "recommendations": []}}
    fake_design = {
        "status": "needs_attention",
        "public_readiness": "needs_improvement",
        "landing_score": 88,
        "warnings": ["typography_coherence:warning"],
        "quick_wins": ["Replace the generic body sans with a more intentional family."],
        "checks": [],
        "recommendation_sources": [
            {
                "recommendation": "Replace the generic body sans with a more intentional family.",
                "originating_check": "typography_coherence",
                "evidence": ["body_font=Segoe UI"],
                "severity": "medium",
                "status": "warning",
            }
        ],
        "ui_pre_return_review": {"status": "pass", "pass_ready": True, "warnings": [], "blockers": []},
    }
    fake_feedback = {
        "status": "ok",
        "reason": None,
        "has_relevant_feedback": True,
        "relevant_feedback": [
            {
                "project_path": str(WEB_ROOT),
                "recommendation_id": "typography_coherence",
                "action": "Replace the generic body sans with a more intentional family.",
                "decision": "deferred",
                "reason": "Bundled into the next design pass.",
                "timestamp": "2026-05-01T00:00:00+00:00",
                "source": "quality_gate_report",
            }
        ],
        "matched_recommendation_ids": ["typography_coherence"],
        "matched_actions": ["Replace the generic body sans with a more intentional family."],
        "log_path": "C:/fake/decision_feedback.jsonl",
    }

    def fake_dispatch(command_id, root=None, project=None):
        class _Res:
            def __init__(self, output):
                self.output = output

        mapping = {
            "project-phase-report": phase_report,
            "audit-repo": fake_audit,
            "certify-project": fake_certify,
            "surface-audit": fake_surface,
        }
        return _Res(mapping[command_id])

    with patch("tools.quality_gate_report._dispatch_output", side_effect=lambda command_id, root=None, project=None: fake_dispatch(command_id, root=root, project=project).output):
        with patch("tools.quality_gate_report.anti_generic_ui_audit", return_value=fake_design):
            with patch("tools.quality_gate_report.find_relevant_feedback", return_value=fake_feedback):
                result = build_quality_gate_report(ATLAS_ROOT, WEB_ROOT)

    assert result["decision_feedback"]["has_relevant_feedback"] is True
    assert result["decision_feedback"]["relevant_feedback"][0]["decision"] == "deferred"


def test_quality_gate_report_exposes_feedback_patterns_and_adjusted_priorities():
    phase_report = {
        "ok": True,
        "result": {
            "status": "ok",
            "current_phase": "audit",
            "confidence": "high",
            "blocked_actions": [],
            "next_valid_phases": ["certified"],
            "recommended_actions": ["Run certify-project once audit findings are resolved."],
        },
    }
    fake_audit = {"ok": True, "result": {"status": "ok", "findings": []}}
    fake_certify = {"ok": True, "result": {"status": "ok", "blockers": [], "warnings": []}}
    fake_surface = {"ok": True, "result": {"status": "ok", "warnings": [], "recommendations": []}}
    fake_design = {
        "status": "needs_attention",
        "public_readiness": "needs_improvement",
        "landing_score": 82,
        "warnings": ["content_density:warning"],
        "quick_wins": ["Trim dense sections"],
        "checks": [],
        "recommendation_sources": [
            {
                "recommendation": "Trim dense sections",
                "originating_check": "content_density",
                "evidence": ["long_sections=3"],
                "severity": "medium",
                "status": "warning",
            }
        ],
        "ui_pre_return_review": {"status": "pass", "pass_ready": True, "warnings": [], "blockers": []},
    }
    fake_feedback_analysis = {
        "status": "ok",
        "reason": None,
        "project_path": str(WEB_ROOT),
        "analyzed_entries": 2,
        "action_feedback": [
            {"action": "Trim dense sections", "frequency": 2, "acceptance_rate": 0.0, "ignore_rate": 1.0, "last_decision": "ignored"}
        ],
        "detected_patterns": [
            {
                "pattern": "Action `Trim dense sections` is repeatedly ignored.",
                "impact": "Lower its priority or drop it when stronger signals exist.",
                "recommendation": "Stop surfacing this action as a top recommendation unless a new blocker reintroduces it.",
            }
        ],
        "log_path": "C:/fake/decision_feedback.jsonl",
    }

    def fake_dispatch(command_id, root=None, project=None):
        class _Res:
            def __init__(self, output):
                self.output = output

        mapping = {
            "project-phase-report": phase_report,
            "audit-repo": fake_audit,
            "certify-project": fake_certify,
            "surface-audit": fake_surface,
        }
        return _Res(mapping[command_id])

    with patch("tools.quality_gate_report._dispatch_output", side_effect=lambda command_id, root=None, project=None: fake_dispatch(command_id, root=root, project=project).output):
        with patch("tools.quality_gate_report.anti_generic_ui_audit", return_value=fake_design):
            with patch("tools.quality_gate_report.analyze_feedback", return_value=fake_feedback_analysis):
                result = build_quality_gate_report(ATLAS_ROOT, WEB_ROOT)

    assert result["detected_patterns"]
    assert result["feedback_adjusted_priorities"]
    assert result["feedback_adjusted_priorities"][0]["feedback_weight"] in {"neutral", "down", "up"}


def test_quality_gate_report_warns_when_ui_project_lacks_visual_intent_contract():
    phase_report = {
        "ok": True,
        "result": {
            "status": "ok",
            "current_phase": "audit",
            "confidence": "high",
            "blocked_actions": [],
            "next_valid_phases": ["certified"],
            "recommended_actions": ["Run certify-project once audit findings are resolved."],
        },
    }
    fake_audit = {"ok": True, "result": {"status": "ok", "findings": []}}
    fake_certify = {"ok": True, "result": {"status": "ok", "blockers": [], "warnings": []}}
    fake_surface = {"ok": True, "result": {"status": "ok", "warnings": [], "recommendations": []}}
    fake_design = {
        "status": "pass",
        "public_readiness": "ready",
        "landing_score": 95,
        "warnings": [],
        "quick_wins": [],
        "checks": [],
        "recommendation_sources": [],
        "ui_pre_return_review": {"status": "pass", "pass_ready": True, "warnings": [], "blockers": []},
    }
    fake_intent = {
        "status": "needs_input",
        "project_type": "frontend_app",
        "objective": "Create an Atlas landing page.",
        "risk_level": "medium",
        "complexity": "medium",
        "visual_intent_contract": {
            "status": "needs_input",
            "requires_contract": True,
            "missing_fields": ["audience", "originality_level"],
            "weak_fields": [],
            "required_fields": ["audience", "project_type"],
            "contract": {"project_type": "frontend_app"},
            "next_action": "Fill the contract before stronger design claims.",
            "advisory_only": True,
        },
    }

    def fake_dispatch(command_id, root=None, project=None):
        class _Res:
            def __init__(self, output):
                self.output = output

        mapping = {
            "project-phase-report": phase_report,
            "audit-repo": fake_audit,
            "certify-project": fake_certify,
            "surface-audit": fake_surface,
        }
        return _Res(mapping[command_id])

    with patch("tools.quality_gate_report._dispatch_output", side_effect=lambda command_id, root=None, project=None: fake_dispatch(command_id, root=root, project=project).output):
        with patch("tools.quality_gate_report.anti_generic_ui_audit", return_value=fake_design):
            with patch("tools.quality_gate_report.analyze_project_intent", return_value=fake_intent):
                result = build_quality_gate_report(ATLAS_ROOT, WEB_ROOT)

    assert result["overall_status"] == "needs_improvement"
    assert any(item["check"] == "visual_intent_contract_missing" for item in result["warnings"])


def test_quality_gate_report_warns_when_brand_profile_is_missing():
    phase_report = {
        "ok": True,
        "result": {
            "status": "ok",
            "current_phase": "audit",
            "confidence": "high",
            "blocked_actions": [],
            "next_valid_phases": ["certified"],
            "recommended_actions": ["Run certify-project once audit findings are resolved."],
        },
    }
    fake_audit = {"ok": True, "result": {"status": "ok", "findings": []}}
    fake_certify = {"ok": True, "result": {"status": "ok", "blockers": [], "warnings": []}}
    fake_surface = {"ok": True, "result": {"status": "ok", "warnings": [], "recommendations": []}}
    fake_design = {
        "status": "pass",
        "public_readiness": "ready",
        "landing_score": 95,
        "warnings": [],
        "quick_wins": [],
        "checks": [],
        "recommendation_sources": [],
        "brand_profile_review": {
            "status": "needs_input",
            "requires_profile": True,
            "explicit_profile_present": False,
            "profile_source": "inferred_from_context",
            "missing_fields": ["brand_name", "inspiration_references"],
            "weak_fields": [],
            "invalid_fields": [],
            "anti_generic_risks": ["missing_differentiation_notes"],
            "derivative_risks": [],
            "accessibility_risks": [],
            "required_fields": ["brand_name", "audience"],
            "profile": {"audience": "for developers"},
            "next_action": "Document the brand profile explicitly before stronger brand readiness claims.",
            "advisory_only": True,
        },
        "ui_pre_return_review": {"status": "pass", "pass_ready": True, "warnings": [], "blockers": []},
    }
    fake_intent = {
        "status": "ready",
        "project_type": "frontend_app",
        "objective": "Create an Atlas landing page.",
        "risk_level": "medium",
        "complexity": "medium",
        "visual_intent_contract": {
            "status": "ready",
            "requires_contract": True,
            "missing_fields": [],
            "weak_fields": [],
            "required_fields": ["audience", "project_type"],
            "contract": {"project_type": "frontend_app", "audience": "for developers"},
            "next_action": "Proceed.",
            "advisory_only": True,
        },
    }

    def fake_dispatch(command_id, root=None, project=None):
        class _Res:
            def __init__(self, output):
                self.output = output

        mapping = {
            "project-phase-report": phase_report,
            "audit-repo": fake_audit,
            "certify-project": fake_certify,
            "surface-audit": fake_surface,
        }
        return _Res(mapping[command_id])

    with patch("tools.quality_gate_report._dispatch_output", side_effect=lambda command_id, root=None, project=None: fake_dispatch(command_id, root=root, project=project).output):
        with patch("tools.quality_gate_report.anti_generic_ui_audit", return_value=fake_design):
            with patch("tools.quality_gate_report.analyze_project_intent", return_value=fake_intent):
                result = build_quality_gate_report(ATLAS_ROOT, WEB_ROOT)

    warning_codes = {item["check"] for item in result["warnings"]}
    assert "brand_profile_missing" in warning_codes
    assert "brand_profile_generic_risk" in warning_codes


def test_quality_gate_report_exposes_ui_pre_return_posture_and_warnings():
    phase_report = {
        "ok": True,
        "result": {
            "status": "ok",
            "current_phase": "audit",
            "confidence": "high",
            "blocked_actions": [],
            "next_valid_phases": ["certified"],
            "recommended_actions": ["Run certify-project once audit findings are resolved."],
        },
    }
    fake_audit = {"ok": True, "result": {"status": "ok", "findings": []}}
    fake_certify = {"ok": True, "result": {"status": "ok", "blockers": [], "warnings": []}}
    fake_surface = {"ok": True, "result": {"status": "ok", "warnings": [], "recommendations": []}}
    fake_design = {
        "status": "needs_attention",
        "public_readiness": "needs_improvement",
        "landing_score": 84,
        "warnings": [],
        "quick_wins": ["Strengthen hierarchy before final return."],
        "checks": [],
        "recommendation_sources": [],
        "ui_pre_return_review": {
            "status": "not_ready",
            "pass_ready": False,
            "warnings": ["ui_pre_return_missing_evidence", "ui_pre_return_generic_risk", "ui_pre_return_not_ready"],
            "blockers": [{"id": "cta_clarity"}],
            "missing_evidence": ["evidence_expectations"],
            "anti_generic_risks": ["anti_generic_default"],
            "brand_alignment_risks": [],
            "accessibility_risks": [],
            "responsive_risks": [],
            "recommended_fixes": ["Clarify the CTA and evidence trail before handoff."],
            "requires_human_clarification": True,
            "requires_decision_council": False,
            "why": "CTA and evidence still need a final pre-return pass.",
        },
    }

    def fake_dispatch(command_id, root=None, project=None):
        class _Res:
            def __init__(self, output):
                self.output = output

        mapping = {
            "project-phase-report": phase_report,
            "audit-repo": fake_audit,
            "certify-project": fake_certify,
            "surface-audit": fake_surface,
        }
        return _Res(mapping[command_id])

    with patch("tools.quality_gate_report._dispatch_output", side_effect=lambda command_id, root=None, project=None: fake_dispatch(command_id, root=root, project=project).output):
        with patch("tools.quality_gate_report.anti_generic_ui_audit", return_value=fake_design):
            with patch("tools.quality_gate_report.assess_intent_clarifier_contract", return_value={"status": "ready", "requires_contract": True, "required_questions": [], "answered_questions": [], "missing_questions": [], "weak_answers": [], "must_block_strong_ready": False, "requires_human_clarification": False, "next_action": "Proceed.", "why": "Ready.", "advisory_only": True}):
                with patch("tools.quality_gate_report.assess_brand_json_v2_readiness", return_value={"status": "ready", "requires_brand_json_v2": True, "explicit_profile_present": True, "missing_sections": [], "weak_sections": [], "anti_generic_risks": [], "derivative_risks": [], "accessibility_risks": [], "export_candidate": True, "evidence_expectations": ["palette rationale"], "next_action": "Proceed.", "why": "Ready.", "advisory_only": True}):
                    with patch("tools.quality_gate_report.audit_frontend_auto_readiness", return_value={"status": "ready", "can_support_pre_return": True, "blockers": [], "warnings": [], "ready_guardrails": [], "missing_guardrails": [], "evidence_gaps": [], "watchlist_dependencies": [], "recommended_next_action": "Proceed.", "why": "Ready.", "advisory_only": True}):
                        result = build_quality_gate_report(ATLAS_ROOT, WEB_ROOT)

    warning_codes = {item["check"] for item in result["warnings"]}
    assert result["ui_pre_return_posture"]["status"] == "not_ready"
    assert "ui_pre_return_missing_evidence" in warning_codes
    assert "ui_pre_return_generic_risk" in warning_codes
    assert "ui_pre_return_not_ready" in warning_codes


def test_quality_gate_report_downgrades_ready_when_design_quality_is_not_ready():
    phase_report = {
        "ok": True,
        "result": {
            "status": "ok",
            "current_phase": "audit",
            "confidence": "high",
            "blocked_actions": [],
            "next_valid_phases": ["certified"],
            "recommended_actions": ["Run certify-project once audit findings are resolved."],
        },
    }
    fake_audit = {"ok": True, "result": {"status": "ok", "findings": []}}
    fake_certify = {"ok": True, "result": {"status": "ok", "blockers": [], "warnings": []}}
    fake_surface = {"ok": True, "result": {"status": "ok", "warnings": [], "recommendations": []}}
    fake_design = {
        "status": "pass",
        "public_readiness": "ready",
        "landing_score": 95,
        "warnings": [],
        "quick_wins": [],
        "checks": [],
        "recommendation_sources": [],
        "ui_pre_return_review": {"status": "pass", "pass_ready": True, "warnings": [], "blockers": []},
        "design_quality_review": {
            "status": "not_ready",
            "ready_for_handoff": False,
            "blockers": [{"check": "border_weight_excessive", "severity": "high", "evidence": ["heavy border"]}],
            "warnings": [],
            "visual_quality_score": 62,
            "detected_risks": ["border_weight_excessive", "amateur_internal_tool_look"],
            "recommended_fixes": ["Reduce border weight before handoff."],
            "required_redesign_level": "visual_system_refactor",
            "why": "Visual blockers remain.",
            "advisory_only": True,
        },
    }

    def fake_dispatch(command_id, root=None, project=None):
        class _Res:
            def __init__(self, output):
                self.output = output

        mapping = {
            "project-phase-report": phase_report,
            "audit-repo": fake_audit,
            "certify-project": fake_certify,
            "surface-audit": fake_surface,
        }
        return _Res(mapping[command_id])

    with patch("tools.quality_gate_report._dispatch_output", side_effect=lambda command_id, root=None, project=None: fake_dispatch(command_id, root=root, project=project).output):
        with patch("tools.quality_gate_report.anti_generic_ui_audit", return_value=fake_design):
            with patch("tools.quality_gate_report.assess_intent_clarifier_contract", return_value={"status": "ready", "requires_contract": True, "required_questions": [], "answered_questions": [], "missing_questions": [], "weak_answers": [], "must_block_strong_ready": False, "requires_human_clarification": False, "next_action": "Proceed.", "why": "Ready.", "advisory_only": True}):
                with patch("tools.quality_gate_report.assess_brand_json_v2_readiness", return_value={"status": "ready", "requires_brand_json_v2": True, "explicit_profile_present": True, "missing_sections": [], "weak_sections": [], "anti_generic_risks": [], "derivative_risks": [], "accessibility_risks": [], "export_candidate": True, "evidence_expectations": ["palette rationale"], "next_action": "Proceed.", "why": "Ready.", "advisory_only": True}):
                    with patch("tools.quality_gate_report.audit_frontend_auto_readiness", return_value={"status": "ready", "can_support_pre_return": True, "blockers": [], "warnings": [], "ready_guardrails": [], "missing_guardrails": [], "evidence_gaps": [], "watchlist_dependencies": [], "recommended_next_action": "Proceed.", "why": "Ready.", "advisory_only": True}):
                        result = build_quality_gate_report(ATLAS_ROOT, WEB_ROOT)

    warning_codes = {item["check"] for item in result["warnings"]}
    assert result["overall_status"] == "needs_improvement"
    assert result["design_quality_posture"]["status"] == "not_ready"
    assert "design_quality_not_ready" in warning_codes
    assert "amateur_ui_risk" in warning_codes
    assert "excessive_visual_weight" in warning_codes


def test_quality_gate_report_exposes_intent_clarifier_posture_and_downgrades_ready():
    phase_report = {
        "ok": True,
        "result": {
            "status": "ok",
            "current_phase": "audit",
            "confidence": "high",
            "blocked_actions": [],
            "next_valid_phases": ["certified"],
            "recommended_actions": ["Run certify-project once audit findings are resolved."],
        },
    }
    fake_audit = {"ok": True, "result": {"status": "ok", "findings": []}}
    fake_certify = {"ok": True, "result": {"status": "ok", "blockers": [], "warnings": []}}
    fake_surface = {"ok": True, "result": {"status": "ok", "warnings": [], "recommendations": []}}
    fake_design = {
        "status": "pass",
        "public_readiness": "ready",
        "landing_score": 96,
        "warnings": [],
        "quick_wins": [],
        "checks": [],
        "recommendation_sources": [],
        "visual_intent_contract_review": {"status": "ready", "contract": {"project_type": "frontend_app", "audience": "for developers"}},
        "brand_profile_review": {"status": "ready", "explicit_profile_present": True, "profile": {}},
        "ui_pre_return_review": {"status": "pass", "pass_ready": True, "warnings": [], "blockers": [], "missing_evidence": []},
        "design_quality_review": {"status": "ready", "ready_for_handoff": True, "detected_risks": [], "warnings": [], "blockers": []},
    }
    fake_intent = {
        "status": "ready",
        "project_type": "frontend_app",
        "objective": "Create an Atlas landing page.",
        "risk_level": "medium",
        "complexity": "medium",
        "visual_intent_contract": {"status": "ready", "contract": {"project_type": "frontend_app", "audience": "for developers"}},
    }

    def fake_dispatch(command_id, root=None, project=None):
        class _Res:
            def __init__(self, output):
                self.output = output

        mapping = {
            "project-phase-report": phase_report,
            "audit-repo": fake_audit,
            "certify-project": fake_certify,
            "surface-audit": fake_surface,
        }
        return _Res(mapping[command_id])

    fake_clarifier = {
        "status": "needs_input",
        "requires_contract": True,
        "required_questions": ["project_type", "target_audience", "style_direction"],
        "answered_questions": ["project_type"],
        "missing_questions": ["target_audience", "style_direction"],
        "weak_answers": [],
        "must_block_strong_ready": True,
        "requires_human_clarification": True,
        "next_action": "Fill missing intent answers.",
        "why": "Not enough explicit intent yet.",
        "advisory_only": True,
    }
    fake_brand_json = {
        "status": "ready",
        "requires_brand_json_v2": True,
        "explicit_profile_present": True,
        "missing_sections": [],
        "weak_sections": [],
        "anti_generic_risks": [],
        "derivative_risks": [],
        "accessibility_risks": [],
        "export_candidate": True,
        "evidence_expectations": ["palette rationale"],
        "next_action": "Proceed.",
        "why": "Ready.",
        "advisory_only": True,
    }
    fake_frontend_auto = {
        "status": "ready",
        "can_support_pre_return": True,
        "blockers": [],
        "warnings": [],
        "ready_guardrails": ["intent_clarifier_ready"],
        "missing_guardrails": [],
        "evidence_gaps": [],
        "watchlist_dependencies": [],
        "recommended_next_action": "Proceed.",
        "why": "Ready.",
        "advisory_only": True,
    }

    with patch("tools.quality_gate_report._dispatch_output", side_effect=lambda command_id, root=None, project=None: fake_dispatch(command_id, root=root, project=project).output):
        with patch("tools.quality_gate_report.anti_generic_ui_audit", return_value=fake_design):
            with patch("tools.quality_gate_report.analyze_project_intent", return_value=fake_intent):
                with patch("tools.quality_gate_report.assess_intent_clarifier_contract", return_value=fake_clarifier):
                    with patch("tools.quality_gate_report.assess_brand_json_v2_readiness", return_value=fake_brand_json):
                        with patch("tools.quality_gate_report.audit_frontend_auto_readiness", return_value=fake_frontend_auto):
                            result = build_quality_gate_report(ATLAS_ROOT, WEB_ROOT)

    assert result["overall_status"] == "needs_improvement"
    assert result["intent_clarifier_posture"]["status"] == "needs_input"
    assert any(item["check"] == "intent_clarifier_missing" for item in result["warnings"])


def test_quality_gate_report_exposes_brand_json_v2_and_frontend_auto_audit_postures():
    phase_report = {
        "ok": True,
        "result": {
            "status": "ok",
            "current_phase": "audit",
            "confidence": "high",
            "blocked_actions": [],
            "next_valid_phases": ["certified"],
            "recommended_actions": ["Run certify-project once audit findings are resolved."],
        },
    }
    fake_audit = {"ok": True, "result": {"status": "ok", "findings": []}}
    fake_certify = {"ok": True, "result": {"status": "ok", "blockers": [], "warnings": []}}
    fake_surface = {"ok": True, "result": {"status": "ok", "warnings": [], "recommendations": []}}
    fake_design = {
        "status": "pass",
        "public_readiness": "ready",
        "landing_score": 92,
        "warnings": [],
        "quick_wins": [],
        "checks": [{"id": "responsive_baseline", "status": "pass", "evidence": ["viewport_meta=true"]}],
        "recommendation_sources": [],
        "visual_intent_contract_review": {"status": "ready", "contract": {"project_type": "frontend_app", "audience": "for developers", "evidence_expectations": ["proof"]}},
        "brand_profile_review": {"status": "ready", "explicit_profile_present": True, "profile": {}},
        "ui_pre_return_review": {"status": "pass", "pass_ready": True, "warnings": [], "blockers": [], "missing_evidence": []},
        "design_quality_review": {"status": "ready", "ready_for_handoff": True, "detected_risks": [], "warnings": [], "blockers": []},
    }
    fake_intent = {
        "status": "ready",
        "project_type": "frontend_app",
        "objective": "Create an Atlas landing page.",
        "risk_level": "medium",
        "complexity": "medium",
        "visual_intent_contract": {"status": "ready", "contract": {"project_type": "frontend_app", "audience": "for developers"}},
    }

    def fake_dispatch(command_id, root=None, project=None):
        class _Res:
            def __init__(self, output):
                self.output = output

        mapping = {
            "project-phase-report": phase_report,
            "audit-repo": fake_audit,
            "certify-project": fake_certify,
            "surface-audit": fake_surface,
        }
        return _Res(mapping[command_id])

    fake_clarifier = {
        "status": "ready",
        "requires_contract": True,
        "required_questions": ["project_type"],
        "answered_questions": ["project_type"],
        "missing_questions": [],
        "weak_answers": [],
        "must_block_strong_ready": False,
        "requires_human_clarification": False,
        "next_action": "Proceed.",
        "why": "Ready.",
        "advisory_only": True,
    }
    fake_brand_json = {
        "status": "needs_input",
        "requires_brand_json_v2": True,
        "explicit_profile_present": False,
        "missing_sections": ["mood_vector"],
        "weak_sections": [],
        "anti_generic_risks": [],
        "derivative_risks": [],
        "accessibility_risks": [],
        "export_candidate": False,
        "evidence_expectations": ["palette rationale"],
        "next_action": "Document the profile explicitly.",
        "why": "Still inferred.",
        "advisory_only": True,
    }
    fake_frontend_auto = {
        "status": "needs_improvement",
        "can_support_pre_return": False,
        "blockers": [{"check": "frontend_auto_audit_missing_brand_json_v2", "severity": "high", "message": "Need explicit brand artifact.", "evidence": ["mood_vector"]}],
        "warnings": [],
        "ready_guardrails": ["intent_clarifier_ready"],
        "missing_guardrails": ["brand_json_v2_ready"],
        "evidence_gaps": [],
        "watchlist_dependencies": ["visual_fidelity_judge"],
        "recommended_next_action": "Resolve missing brand artifact.",
        "why": "Brand artifact still weak.",
        "advisory_only": True,
    }

    with patch("tools.quality_gate_report._dispatch_output", side_effect=lambda command_id, root=None, project=None: fake_dispatch(command_id, root=root, project=project).output):
        with patch("tools.quality_gate_report.anti_generic_ui_audit", return_value=fake_design):
            with patch("tools.quality_gate_report.analyze_project_intent", return_value=fake_intent):
                with patch("tools.quality_gate_report.assess_intent_clarifier_contract", return_value=fake_clarifier):
                    with patch("tools.quality_gate_report.assess_brand_json_v2_readiness", return_value=fake_brand_json):
                        with patch("tools.quality_gate_report.audit_frontend_auto_readiness", return_value=fake_frontend_auto):
                            result = build_quality_gate_report(ATLAS_ROOT, WEB_ROOT)

    warning_codes = {item["check"] for item in result["warnings"]}
    assert result["brand_json_v2_posture"]["status"] == "needs_input"
    assert result["frontend_auto_audit_posture"]["status"] == "needs_improvement"
    assert "brand_json_v2_missing" in warning_codes
    assert "frontend_auto_audit_not_ready" in warning_codes


def test_quality_gate_report_downgrades_ready_when_visual_fidelity_detects_drift():
    phase_report = {
        "ok": True,
        "result": {
            "status": "ok",
            "current_phase": "audit",
            "confidence": "high",
            "blocked_actions": [],
            "next_valid_phases": ["certified"],
            "recommended_actions": ["Run certify-project once audit findings are resolved."],
        },
    }
    fake_audit = {"ok": True, "result": {"status": "ok", "findings": []}}
    fake_certify = {"ok": True, "result": {"status": "ok", "blockers": [], "warnings": []}}
    fake_surface = {"ok": True, "result": {"status": "ok", "warnings": [], "recommendations": []}}
    fake_design = {
        "status": "pass",
        "public_readiness": "ready",
        "landing_score": 94,
        "warnings": [],
        "quick_wins": [],
        "checks": [{"id": "responsive_baseline", "status": "pass", "evidence": ["viewport_meta=true"]}],
        "recommendation_sources": [],
        "visual_intent_contract_review": {"status": "ready", "contract": {"project_type": "frontend_app", "audience": "for developers", "evidence_expectations": ["proof"]}},
        "brand_profile_review": {"status": "ready", "explicit_profile_present": True, "profile": {}},
        "ui_pre_return_review": {"status": "pass", "pass_ready": True, "warnings": [], "blockers": [], "missing_evidence": []},
        "design_quality_review": {"status": "ready", "ready_for_handoff": True, "detected_risks": [], "warnings": [], "blockers": []},
    }
    fake_intent = {
        "status": "ready",
        "project_type": "frontend_app",
        "objective": "Create an Atlas landing page.",
        "risk_level": "medium",
        "complexity": "medium",
        "visual_intent_contract": {"status": "ready", "contract": {"project_type": "frontend_app", "audience": "for developers"}},
    }

    def fake_dispatch(command_id, root=None, project=None):
        class _Res:
            def __init__(self, output):
                self.output = output

        mapping = {
            "project-phase-report": phase_report,
            "audit-repo": fake_audit,
            "certify-project": fake_certify,
            "surface-audit": fake_surface,
        }
        return _Res(mapping[command_id])

    fake_visual_fidelity = {
        "status": "needs_attention",
        "fidelity_state": "drift_detected",
        "report_detected": True,
        "report_path": "docs/visual_fidelity_report.json",
        "screenshot_evidence_present": True,
        "required_viewports": ["desktop", "mobile"],
        "provided_viewports": ["desktop", "mobile"],
        "missing_viewports": [],
        "compared_layers": ["visual_intent_contract", "brand_profile"],
        "missing_compared_layers": [],
        "matched_signals": ["Palette intent is still visible."],
        "drift_signals": ["CTA hierarchy is visually buried."],
        "confidence": "medium",
        "can_support_visual_pass": False,
        "must_not_claim_visual_pass_without_evidence": True,
        "manual_next_steps": ["Resolve the reported drift before claiming a strong PASS."],
        "why": "Drift detected.",
        "advisory_only": True,
    }

    with patch("tools.quality_gate_report._dispatch_output", side_effect=lambda command_id, root=None, project=None: fake_dispatch(command_id, root=root, project=project).output):
        with patch("tools.quality_gate_report.anti_generic_ui_audit", return_value=fake_design):
            with patch("tools.quality_gate_report.analyze_project_intent", return_value=fake_intent):
                with patch("tools.quality_gate_report.assess_visual_fidelity_judge", return_value=fake_visual_fidelity):
                    result = build_quality_gate_report(ATLAS_ROOT, WEB_ROOT)

    assert result["overall_status"] == "needs_improvement"
    assert result["visual_fidelity_posture"]["fidelity_state"] == "drift_detected"
    assert any(item["check"] == "visual_fidelity_drift_detected" for item in result["warnings"])
