from pathlib import Path
from unittest.mock import patch

from tests._support_paths import ATLAS_ROOT
from tools.codex_runtime_compatibility_check import check_codex_runtime_compatibility


ROOT = ATLAS_ROOT


def test_codex_runtime_compatibility_reports_safe_runtime():
    with patch(
        "tools.codex_runtime_compatibility_check._probe_codex_version",
        return_value={"available": True, "version": "codex-cli 0.130.0-alpha.5", "error": None},
    ):
        with patch(
            "tools.codex_runtime_compatibility_check.check_mcp_readiness",
            return_value={
                "codex_mcp_cli_functional": True,
                "configured_mcp_servers": ["openaiDeveloperDocs"],
                "openai_docs_mcp_functional": True,
            },
        ):
            with patch(
                "tools.codex_runtime_compatibility_check.inspect_model_switch_support",
                return_value={"current_global_model": "gpt-5.5", "current_project_model": None},
            ):
                result = check_codex_runtime_compatibility(root=ROOT)
    assert result["status"] == "ok"
    assert result["safe_to_use_with_atlas"] is True
    assert result["codex_cli_available"] is True


def test_codex_runtime_compatibility_flags_missing_runtime_capabilities():
    with patch(
        "tools.codex_runtime_compatibility_check._probe_codex_version",
        return_value={"available": False, "version": None, "error": "codex missing"},
    ):
        with patch(
            "tools.codex_runtime_compatibility_check.check_mcp_readiness",
            return_value={
                "codex_mcp_cli_functional": False,
                "configured_mcp_servers": [],
                "openai_docs_mcp_functional": False,
            },
        ):
            with patch(
                "tools.codex_runtime_compatibility_check.inspect_model_switch_support",
                return_value={"current_global_model": None, "current_project_model": None},
            ):
                result = check_codex_runtime_compatibility(root=ROOT)
    assert result["status"] == "needs_attention"
    assert result["safe_to_use_with_atlas"] is False
    assert "codex_cli_not_callable" in result["limitations"]
