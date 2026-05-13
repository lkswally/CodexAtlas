import json
import os
from pathlib import Path
from unittest.mock import patch

os.environ["ATLAS_DISABLE_EVENT_LOGS"] = "1"

from tools.component_inspiration_readiness import check_component_inspiration_readiness


ROOT = Path(r"C:\Proyectos\Codex-Atlas")


def _creative_report(*, available_services=None, missing_services=None):
    return {
        "status": "ok",
        "available_services": available_services or [],
        "missing_services": missing_services or [],
        "safe_to_use_profiles": [],
        "watchlist_profiles": [],
        "blocked_profiles": [],
        "required_manual_steps": [],
        "risks": [],
        "requires_human_approval": True,
        "requires_decision_council": False,
        "recommended_next_action": "stay cautious",
        "why": "test fixture",
        "advisory_only": True,
    }


def _service(
    service: str,
    *,
    available: bool,
    env_vars_present=None,
    missing_env_vars=None,
):
    return {
        "service": service,
        "display_name": service,
        "available": available,
        "env_vars_present": env_vars_present or [],
        "missing_env_vars": missing_env_vars or [],
        "related_mcp_servers": [service],
        "configured_related_mcp_servers": [service] if available and service == "context7" else [],
        "availability_reason": "fixture",
    }


def test_component_inspiration_readiness_without_21st_key():
    report = _creative_report(
        missing_services=[
            _service("twentyfirst_magic", available=False, missing_env_vars=["TWENTYFIRST_API_KEY"]),
            _service("context7", available=False),
        ]
    )
    with patch("tools.component_inspiration_readiness.check_creative_pipeline_readiness", return_value=report):
        result = check_component_inspiration_readiness(root=ROOT)

    assert result["status"] == "needs_attention"
    assert any(item["service"] == "twentyfirst_magic" for item in result["missing_services"])
    blocked = next(
        item for item in result["blocked_profiles"] if item["profile"] == "ui_component_inspiration"
    )
    assert "TWENTYFIRST_API_KEY" in blocked["missing_env_vars"]


def test_component_inspiration_readiness_with_21st_key_present():
    report = _creative_report(
        available_services=[_service("twentyfirst_magic", available=True, env_vars_present=["TWENTYFIRST_API_KEY"])],
        missing_services=[_service("context7", available=False)],
    )
    with patch("tools.component_inspiration_readiness.check_creative_pipeline_readiness", return_value=report):
        result = check_component_inspiration_readiness(root=ROOT)

    assert any(item["service"] == "twentyfirst_magic" for item in result["available_services"])
    assert any(item["profile"] == "ui_component_inspiration" for item in result["safe_to_use_profiles"])


def test_component_inspiration_readiness_marks_context7_as_missing_when_not_configured():
    report = _creative_report(
        available_services=[_service("twentyfirst_magic", available=True, env_vars_present=["TWENTYFIRST_API_KEY"])],
        missing_services=[_service("context7", available=False)],
    )
    with patch("tools.component_inspiration_readiness.check_creative_pipeline_readiness", return_value=report):
        result = check_component_inspiration_readiness(root=ROOT)

    assert any(item["service"] == "context7" for item in result["missing_services"])
    assert any("Context7" in step for step in result["required_manual_steps"])


def test_component_inspiration_readiness_exposes_safe_profiles():
    report = _creative_report(
        available_services=[
            _service("twentyfirst_magic", available=True, env_vars_present=["TWENTYFIRST_API_KEY"]),
            _service("context7", available=True),
        ]
    )
    with patch("tools.component_inspiration_readiness.check_creative_pipeline_readiness", return_value=report):
        result = check_component_inspiration_readiness(root=ROOT)

    safe_profiles = {item["profile"] for item in result["safe_to_use_profiles"]}
    assert "design_system_reference" in safe_profiles
    assert "empty_error_loading_states" in safe_profiles


def test_component_inspiration_readiness_keeps_generation_profile_in_watchlist():
    report = _creative_report(
        available_services=[_service("twentyfirst_magic", available=True, env_vars_present=["TWENTYFIRST_API_KEY"])]
    )
    with patch("tools.component_inspiration_readiness.check_creative_pipeline_readiness", return_value=report):
        result = check_component_inspiration_readiness(root=ROOT)

    watchlist = next(
        item for item in result["watchlist_profiles"] if item["profile"] == "component_generation_watchlist"
    )
    assert watchlist["risk_level"] == "high"
    assert result["requires_decision_council"] is True


def test_component_inspiration_readiness_blocks_profiles_when_services_are_missing():
    report = _creative_report(
        missing_services=[
            _service("twentyfirst_magic", available=False, missing_env_vars=["TWENTYFIRST_API_KEY"]),
            _service("context7", available=False),
        ]
    )
    with patch("tools.component_inspiration_readiness.check_creative_pipeline_readiness", return_value=report):
        result = check_component_inspiration_readiness(root=ROOT)

    blocked_profiles = {item["profile"] for item in result["blocked_profiles"]}
    assert "landing_section_patterns" in blocked_profiles
    assert "dashboard_patterns" in blocked_profiles


def test_component_inspiration_readiness_does_not_print_secret_values():
    secret_value = "super-secret-should-not-appear"
    report = _creative_report(
        available_services=[
            _service("twentyfirst_magic", available=True, env_vars_present=["TWENTYFIRST_API_KEY"])
        ]
    )
    with patch.dict(os.environ, {"TWENTYFIRST_API_KEY": secret_value}, clear=True):
        with patch(
            "tools.component_inspiration_readiness.check_creative_pipeline_readiness",
            return_value=report,
        ):
            result = check_component_inspiration_readiness(root=ROOT)

    rendered = json.dumps(result)
    assert secret_value not in rendered
    assert "TWENTYFIRST_API_KEY" in rendered
