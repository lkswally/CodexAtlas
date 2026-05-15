import os
from pathlib import Path
from unittest.mock import patch

os.environ["ATLAS_DISABLE_EVENT_LOGS"] = "1"

from tests._support_paths import ATLAS_ROOT, PLAYWRIGHT_HOME_HINT
from tools.playwright_visual_qa_readiness import check_playwright_visual_qa_readiness


ROOT = ATLAS_ROOT


def _cli_probe(*, available: bool, stdout: str = "", stderr: str = "", returncode: int | None = None):
    return {
        "available": available,
        "stdout": stdout,
        "stderr": stderr,
        "returncode": 0 if available else returncode,
    }


def _browser_probe(*, available: bool, detected_browsers=None, checked_paths=None):
    return {
        "available": available,
        "detected_browsers": detected_browsers or [],
        "checked_paths": checked_paths or [str(PLAYWRIGHT_HOME_HINT)],
    }


def test_playwright_visual_qa_readiness_when_playwright_is_absent():
    with patch("tools.playwright_visual_qa_readiness._probe_playwright_cli", return_value=_cli_probe(available=False, stderr="No module named playwright")):
        with patch("tools.playwright_visual_qa_readiness._detect_browsers", return_value=_browser_probe(available=False)):
            result = check_playwright_visual_qa_readiness(root=ROOT)

    assert result["status"] == "needs_attention"
    assert result["playwright_available"] is False
    assert result["safe_to_run"] is False
    assert any(item["profile"] == "landing_visual_qa" for item in result["blocked_profiles"])


def test_playwright_visual_qa_readiness_when_playwright_is_present():
    with patch("tools.playwright_visual_qa_readiness._probe_playwright_cli", return_value=_cli_probe(available=True, stdout="Version 1.52.0")):
        with patch("tools.playwright_visual_qa_readiness._detect_browsers", return_value=_browser_probe(available=False)):
            result = check_playwright_visual_qa_readiness(root=ROOT)

    assert result["playwright_available"] is True
    assert result["browsers_available"] is False


def test_playwright_visual_qa_readiness_when_browsers_are_absent():
    with patch("tools.playwright_visual_qa_readiness._probe_playwright_cli", return_value=_cli_probe(available=True, stdout="Version 1.52.0")):
        with patch("tools.playwright_visual_qa_readiness._detect_browsers", return_value=_browser_probe(available=False)):
            result = check_playwright_visual_qa_readiness(root=ROOT)

    assert result["safe_to_run"] is False
    assert any("Install Playwright browsers manually" in step for step in result["required_manual_steps"])


def test_playwright_visual_qa_readiness_can_be_safe_to_run():
    with patch("tools.playwright_visual_qa_readiness._probe_playwright_cli", return_value=_cli_probe(available=True, stdout="Version 1.52.0")):
        with patch(
            "tools.playwright_visual_qa_readiness._detect_browsers",
            return_value=_browser_probe(available=True, detected_browsers=["chromium-1148", "firefox-1490"]),
        ):
            result = check_playwright_visual_qa_readiness(root=ROOT)

    assert result["status"] == "ok"
    assert result["safe_to_run"] is True
    assert result["blocked_profiles"] == []


def test_playwright_visual_qa_readiness_keeps_regression_profile_on_watchlist():
    with patch("tools.playwright_visual_qa_readiness._probe_playwright_cli", return_value=_cli_probe(available=True, stdout="Version 1.52.0")):
        with patch(
            "tools.playwright_visual_qa_readiness._detect_browsers",
            return_value=_browser_probe(available=True, detected_browsers=["chromium-1148"]),
        ):
            result = check_playwright_visual_qa_readiness(root=ROOT)

    watchlist = next(
        item for item in result["watchlist_profiles"] if item["profile"] == "regression_screenshot_watchlist"
    )
    assert watchlist["risk_level"] == "high"


def test_playwright_visual_qa_readiness_blocks_profiles_when_runtime_is_missing():
    with patch("tools.playwright_visual_qa_readiness._probe_playwright_cli", return_value=_cli_probe(available=False, stderr="missing")):
        with patch("tools.playwright_visual_qa_readiness._detect_browsers", return_value=_browser_probe(available=False)):
            result = check_playwright_visual_qa_readiness(root=ROOT)

    blocked = next(item for item in result["blocked_profiles"] if item["profile"] == "responsive_visual_qa")
    assert "playwright_not_available" in blocked["blockers"]
