import os
from unittest.mock import patch

os.environ["ATLAS_DISABLE_EVENT_LOGS"] = "1"

from tools.mcp_readiness_check import check_mcp_readiness


def test_mcp_readiness_check_keeps_adapter_when_cli_is_blocked():
    with patch(
        "tools.mcp_readiness_check.inspect_docs_search_runtime_support",
        return_value={
            "real_mcp_supported": False,
            "codex_cli_invocable": False,
            "cli_error": "[WinError 5] Access is denied",
            "config_path": "C:/Users/test/.codex/config.toml",
        },
    ):
        result = check_mcp_readiness()

    assert result["status"] == "ok"
    assert result["codex_cli_available"] is False
    assert result["real_mcp_safe_to_configure"] is False
    assert result["fallback"] == "docs_search_adapter"
    assert "do not modify" in result["recommended_action"].lower()
