import os
from pathlib import Path
from unittest.mock import patch

os.environ["ATLAS_DISABLE_EVENT_LOGS"] = "1"

from tests._support_paths import ATLAS_ROOT
from tools.creative_pipeline_readiness import check_creative_pipeline_readiness


ROOT = ATLAS_ROOT


def _fake_mcp_readiness(servers=None):
    return {
        "status": "ok",
        "configured_mcp_servers": servers or ["openaiDeveloperDocs"],
        "readiness_state": "real_mcp_configured_and_cli_verified",
    }


def test_creative_pipeline_readiness_with_all_services_absent():
    with patch.dict(os.environ, {}, clear=True):
        with patch("tools.creative_pipeline_readiness.check_mcp_readiness", return_value=_fake_mcp_readiness()):
            result = check_creative_pipeline_readiness(root=ROOT)

    assert result["status"] == "needs_attention"
    assert result["available_services"] == []
    assert any(item["profile"] == "brand_visual_review" for item in result["blocked_profiles"])
    assert any(item["profile"] == "video_generation" for item in result["watchlist_profiles"])


def test_creative_pipeline_readiness_detects_gemini_presence():
    with patch.dict(os.environ, {"GEMINI_API_KEY": "present"}, clear=True):
        with patch("tools.creative_pipeline_readiness.check_mcp_readiness", return_value=_fake_mcp_readiness()):
            result = check_creative_pipeline_readiness(root=ROOT)

    assert any(item["service"] == "gemini" for item in result["available_services"])
    assert any(item["profile"] == "brand_visual_review" for item in result["safe_to_use_profiles"])


def test_creative_pipeline_readiness_detects_huggingface_presence():
    with patch.dict(os.environ, {"HF_TOKEN": "present"}, clear=True):
        with patch("tools.creative_pipeline_readiness.check_mcp_readiness", return_value=_fake_mcp_readiness()):
            result = check_creative_pipeline_readiness(root=ROOT)

    assert any(item["service"] == "huggingface" for item in result["available_services"])
    assert any(item["profile"] == "brand_visual_review" for item in result["safe_to_use_profiles"])


def test_creative_pipeline_readiness_detects_replicate_presence():
    with patch.dict(os.environ, {"REPLICATE_API_TOKEN": "present"}, clear=True):
        with patch("tools.creative_pipeline_readiness.check_mcp_readiness", return_value=_fake_mcp_readiness()):
            result = check_creative_pipeline_readiness(root=ROOT)

    assert any(item["service"] == "replicate" for item in result["available_services"])
    assert any(item["profile"] == "image_generation" for item in result["safe_to_use_profiles"])


def test_creative_pipeline_readiness_keeps_21st_missing_without_key():
    with patch.dict(os.environ, {}, clear=True):
        with patch("tools.creative_pipeline_readiness.check_mcp_readiness", return_value=_fake_mcp_readiness()):
            result = check_creative_pipeline_readiness(root=ROOT)

    twentyfirst = next(item for item in result["missing_services"] if item["service"] == "twentyfirst_magic")
    assert "TWENTYFIRST_API_KEY" in twentyfirst["missing_env_vars"]


def test_creative_pipeline_readiness_blocks_profile_without_required_key():
    with patch.dict(os.environ, {}, clear=True):
        with patch("tools.creative_pipeline_readiness.check_mcp_readiness", return_value=_fake_mcp_readiness()):
            result = check_creative_pipeline_readiness(root=ROOT)

    blocked = next(item for item in result["blocked_profiles"] if item["profile"] == "logo_generation")
    assert "GEMINI_API_KEY" in blocked["missing_env_vars"] or "REPLICATE_API_TOKEN" in blocked["missing_env_vars"]


def test_creative_pipeline_readiness_marks_high_risk_profile_as_watchlist():
    with patch.dict(os.environ, {"REPLICATE_API_TOKEN": "present"}, clear=True):
        with patch("tools.creative_pipeline_readiness.check_mcp_readiness", return_value=_fake_mcp_readiness()):
            result = check_creative_pipeline_readiness(root=ROOT)

    watchlist = next(item for item in result["watchlist_profiles"] if item["profile"] == "video_generation")
    assert watchlist["risk_level"] == "high"
    assert result["requires_decision_council"] is True
