import json
import os
import shutil
from pathlib import Path
from uuid import uuid4
from unittest.mock import patch

os.environ["ATLAS_DISABLE_EVENT_LOGS"] = "1"

from tests._support_paths import ATLAS_ROOT
from tools.chrome_devtools_mcp_readiness import assess_chrome_devtools_mcp_readiness


def _mcp_readiness(*, configured: bool):
    return {
        "status": "ok",
        "configured_mcp_servers": ["chrome-devtools-mcp"] if configured else [],
        "chrome_devtools_mcp_configured": configured,
        "chrome_devtools_mcp_servers": ["chrome-devtools-mcp"] if configured else [],
        "readiness_state": "configured_but_not_functionally_verified" if configured else "cli_ready_no_servers_configured",
    }


def _make_temp_project() -> Path:
    base = ATLAS_ROOT / "tests" / "_tmp_chrome_devtools_cases"
    base.mkdir(parents=True, exist_ok=True)
    project = base / f"case_{uuid4().hex}"
    project.mkdir(parents=True, exist_ok=False)
    return project


def test_chrome_devtools_mcp_readiness_recommends_for_frontend_visual_drift():
    project = _make_temp_project()
    try:
        (project / "package.json").write_text(json.dumps({"dependencies": {"react": "^19.0.0"}}), encoding="utf-8")

        payload = {
            "project_type": "frontend_app",
            "objective": "Polish the landing page and resolve responsive hierarchy drift.",
            "visual_fidelity_posture": {
                "fidelity_state": "drift_detected",
                "drift_signals": ["CTA hierarchy is visually buried."],
                "screenshot_evidence_present": True,
                "missing_viewports": [],
                "missing_compared_layers": [],
                "can_support_visual_pass": False,
            },
            "design_warnings": ["Responsive layout still breaks CTA hierarchy on smaller screens."],
        }

        with patch("tools.chrome_devtools_mcp_readiness.check_mcp_readiness", return_value=_mcp_readiness(configured=False)):
            result = assess_chrome_devtools_mcp_readiness(payload, root=ATLAS_ROOT, project=project)
    finally:
        shutil.rmtree(project, ignore_errors=True)

    posture = result["chrome_devtools_mcp_posture"]
    assert result["status"] == "ok"
    assert posture["recommended"] is True
    assert posture["manual_setup_required"] is True
    assert posture["symptoms"]["visual_fidelity_drift"] is True
    assert posture["symptoms"]["screenshots_need_browser_truth"] is True


def test_chrome_devtools_mcp_readiness_skips_backend_projects():
    project = _make_temp_project()
    try:
        (project / "pyproject.toml").write_text("[project]\nname='api-service'\n", encoding="utf-8")

        with patch("tools.chrome_devtools_mcp_readiness.check_mcp_readiness", return_value=_mcp_readiness(configured=False)):
            result = assess_chrome_devtools_mcp_readiness(
                {
                    "project_type": "backend_service",
                    "objective": "Refactor API handlers.",
                },
                root=ATLAS_ROOT,
                project=project,
            )
    finally:
        shutil.rmtree(project, ignore_errors=True)

    posture = result["chrome_devtools_mcp_posture"]
    assert posture["recommended"] is False
    assert posture["current_mcp_state"] == "not_needed"


def test_chrome_devtools_mcp_readiness_always_declares_risks_and_manual_opt_in():
    project = _make_temp_project()
    try:
        (project / "index.html").write_text("<!doctype html><html></html>", encoding="utf-8")

        with patch("tools.chrome_devtools_mcp_readiness.check_mcp_readiness", return_value=_mcp_readiness(configured=True)):
            result = assess_chrome_devtools_mcp_readiness(
                {
                    "project_type": "frontend_app",
                    "objective": "Investigate console warnings and slow rendering.",
                    "design_warnings": ["Console warning appears after hydration.", "Performance feels slow."],
                },
                root=ATLAS_ROOT,
                project=project,
            )
    finally:
        shutil.rmtree(project, ignore_errors=True)

    posture = result["chrome_devtools_mcp_posture"]
    assert posture["auto_activate"] is False
    assert posture["activation_mode"] == "manual_opt_in"
    assert posture["telemetry_risk"] == "medium"
    assert posture["browser_profile_risk"] == "medium"
    assert posture["privacy_risk"] == "medium"
    assert "--no-usage-statistics" in posture["recommended_flags"]


def test_chrome_devtools_mcp_readiness_surfaces_manual_setup_when_not_configured():
    project = _make_temp_project()
    try:
        (project / "package.json").write_text(json.dumps({"dependencies": {"next": "^16.0.0"}}), encoding="utf-8")

        with patch("tools.chrome_devtools_mcp_readiness.check_mcp_readiness", return_value=_mcp_readiness(configured=False)):
            result = assess_chrome_devtools_mcp_readiness(
                {
                    "project_type": "frontend_app",
                    "objective": "Debug layout shift and network waterfall in the app shell.",
                },
                root=ATLAS_ROOT,
                project=project,
            )
    finally:
        shutil.rmtree(project, ignore_errors=True)

    posture = result["chrome_devtools_mcp_posture"]
    assert posture["recommended"] is True
    assert posture["mcp_configured"] is False
    assert posture["manual_setup_required"] is True
    assert posture["current_mcp_state"] == "manual_setup_recommended"
