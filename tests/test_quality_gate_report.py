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
    assert result["overall_status"] == "needs_improvement"
    assert result["confidence_level"] in {"medium", "high"}
    assert isinstance(result["blocking_issues"], list)
    assert isinstance(result["top_priorities"], list)
    assert len(result["top_priorities"]) <= 3
    assert result["summary_for_human"]
    assert result["component_results"]["audit_repo"]["ok"] is True
    assert result["component_results"]["certify_project"]["ok"] is True
    assert result["component_results"]["surface_audit"]["ok"] is True


def test_quality_gate_report_uses_existing_outputs_to_mark_not_ready():
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
            "audit-repo": fake_audit,
            "certify-project": fake_certify,
            "surface-audit": fake_surface,
        }
        return _Res(mapping[command_id])

    with patch("tools.quality_gate_report.dispatch", side_effect=fake_dispatch):
        with patch("tools.quality_gate_report.anti_generic_ui_audit", return_value=fake_design):
            result = build_quality_gate_report(ATLAS_ROOT, WEB_ROOT)

    assert result["overall_status"] == "not_ready"
    assert result["confidence_level"] == "high"
    assert result["blocking_issues"]
    assert result["top_priorities"][0]["source"] == "certify-project"
    assert "not ready" in result["summary_for_human"].lower()


def test_quality_gate_report_priorities_come_from_existing_design_recommendation_sources():
    fake_audit = {"ok": True, "result": {"status": "ok", "findings": []}}
    fake_certify = {"ok": True, "result": {"status": "ok", "blockers": [], "warnings": []}}
    fake_surface = {"ok": True, "result": {"status": "ok", "warnings": [], "recommendations": []}}
    fake_design = {
        "status": "needs_attention",
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
            "audit-repo": fake_audit,
            "certify-project": fake_certify,
            "surface-audit": fake_surface,
        }
        return _Res(mapping[command_id])

    with patch("tools.quality_gate_report.dispatch", side_effect=fake_dispatch):
        with patch("tools.quality_gate_report.anti_generic_ui_audit", return_value=fake_design):
            result = build_quality_gate_report(ATLAS_ROOT, WEB_ROOT)

    assert result["overall_status"] == "needs_improvement"
    assert result["top_priorities"][0]["check"] == "typography_coherence"
    assert result["quick_wins"][0] == "Replace the generic body sans with a more intentional family."
