import os
from pathlib import Path
from unittest.mock import patch

os.environ["ATLAS_DISABLE_EVENT_LOGS"] = "1"

from tools.quality_gate_report import build_quality_gate_report


ATLAS_ROOT = Path(r"C:\Proyectos\Codex-Atlas")
WEB_ROOT = Path(r"C:\Proyectos\CodexAtlas-Web")


def test_quality_gate_report_returns_real_structured_summary_for_codexatlas_web():
    result = build_quality_gate_report(ATLAS_ROOT, WEB_ROOT)
    assert result["status"] == "ok"
    assert result["project_path"] == str(WEB_ROOT)
    assert result["overall_status"] == "ready"
    assert result["confidence_level"] in {"medium", "high"}
    assert result["public_readiness"] == "ready"
    assert isinstance(result["landing_score"], int)
    assert result["phase_validity"] in {"valid", "invalid"}
    assert isinstance(result["phase_alignment"], dict)
    assert isinstance(result["blockers"], list)
    assert isinstance(result["warnings"], list)
    assert isinstance(result["top_priorities"], list)
    assert len(result["top_priorities"]) <= 3
    assert result["summary_for_human"]
    assert result["source_reports"]["project-phase-report"]["status"] == "ok"
    assert result["source_reports"]["audit-repo"]["status"] == "ok"
    assert result["source_reports"]["certify-project"]["status"] == "ok"
    assert result["source_reports"]["surface-audit"]["status"] == "ok"
    assert result["source_reports"]["project_intent_analyzer"]["status"] == "ok"
    assert result["source_reports"]["prompt_builder"]["status"] == "ok"
    assert result["source_reports"]["skill_evaluator"]["status"] == "ok"
    assert result["source_reports"]["feedback_analyzer"]["status"] == "ok"
    assert result["source_reports"]["model_router"]["status"] == "ok"
    assert result["source_reports"]["error_pattern_analyzer"]["status"] == "ok"
    assert isinstance(result["intent_analysis"], dict)
    assert isinstance(result["model_routing"], dict)
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
    assert isinstance(result["system_learning"], dict)
    assert isinstance(result["execution_plan"], list)
    assert len(result["execution_plan"]) <= 3
    if result["execution_plan"]:
        first_step = result["execution_plan"][0]
        assert "recommended_model" in first_step
        assert "fallback_model" in first_step
        assert "cheaper_alternative_model" in first_step
        assert "requires_user_confirmation" in first_step
        assert first_step["why_model"]
        avoid_steps = [step for step in result["execution_plan"] if str(step.get("action", "")).lower().startswith("avoid ")]
        if avoid_steps:
            assert avoid_steps[0]["recommended_model"] in {"GPT-5.4-Mini", "GPT-5.1-Codex-Mini"}
    assert len(result["quick_wins"]) <= 2
    assert isinstance(result["feedback_adjusted_priorities"], list)
    assert isinstance(result["detected_patterns"], list)
    assert result["primary_action"] is not None
    assert result["why_now"]
    assert isinstance(result["decision_feedback"], dict)
    assert result["decision_feedback"]["status"] in {"ok", "failed"}
    assert result["recommended_next_action"]


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
