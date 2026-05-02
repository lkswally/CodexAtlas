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
    assert isinstance(result["intent_analysis"], dict)
    assert isinstance(result["prompt_guidance"], dict)
    assert isinstance(result["skill_creation_signal"], dict)
    assert isinstance(result["execution_plan"], list)
    assert len(result["execution_plan"]) <= 3
    assert len(result["quick_wins"]) <= 2
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
    assert result["top_priorities"][0]["check"] == "typography_coherence"
    assert result["quick_wins"][0] == "Replace the generic body sans with a more intentional family."
    assert result["execution_plan"]
    assert result["primary_action"]


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
