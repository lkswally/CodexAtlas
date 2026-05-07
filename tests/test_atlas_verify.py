import os
from pathlib import Path
from unittest.mock import patch

os.environ["ATLAS_DISABLE_EVENT_LOGS"] = "1"

from tools.atlas_verify import build_verify_report


ATLAS_ROOT = Path(r"C:\Proyectos\Codex-Atlas")
WEB_ROOT = Path(r"C:\Proyectos\CodexAtlas-Web")


def test_atlas_verify_returns_real_read_only_summary_for_atlas_root():
    result = build_verify_report(ATLAS_ROOT)
    assert result["status"] == "ok"
    assert result["root"] == str(ATLAS_ROOT)
    assert result["project"] is None
    assert result["checks"]["governance_check"]["ok"] is True
    assert result["checks"]["audit_repo"]["ok"] is True
    assert result["checks"]["surface_audit"]["ok"] is True
    assert result["failed_checks"] == []
    assert result["next_action"]


def test_atlas_verify_marks_project_follow_up_without_duplicating_quality_gate_logic():
    class _Res:
        def __init__(self, output):
            self.output = output

    fake_outputs = {
        "audit-repo": {
            "ok": True,
            "result": {"status": "ok", "summary": {"target_root": str(WEB_ROOT)}, "findings": []},
        },
        "surface-audit": {
            "ok": True,
            "result": {"status": "ok", "summary": {"root": str(ATLAS_ROOT)}, "findings": []},
        },
        "quality-gate-report": {
            "ok": True,
            "result": {
                "status": "ok",
                "overall_status": "needs_improvement",
                "public_readiness": "needs_improvement",
                "summary_for_human": "Follow up on warnings.",
            },
        },
    }

    with patch("tools.atlas_verify.run_check", return_value={"ok": True, "findings": [], "profile": "canonical+derived_project"}):
        with patch("tools.atlas_verify.dispatch", side_effect=lambda command_id, root=None, project=None: _Res(fake_outputs[command_id])):
            result = build_verify_report(ATLAS_ROOT, project=WEB_ROOT)

    assert result["status"] == "needs_attention"
    assert result["checks"]["quality_gate_report"]["overall_status"] == "needs_improvement"
    assert result["checks"]["quality_gate_report"]["public_readiness"] == "needs_improvement"
    assert result["failed_checks"] == []
