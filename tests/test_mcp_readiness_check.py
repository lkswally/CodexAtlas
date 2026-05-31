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
        with patch("tools.mcp_readiness_check._probe_codex_mcp_list", return_value={"functional": False, "error": "Access is denied", "stdout_preview": "", "stderr_preview": ""}):
            result = check_mcp_readiness()

    assert result["status"] == "ok"
    assert result["codex_cli_available"] is False
    assert result["codex_mcp_cli_functional"] is False
    assert result["real_mcp_safe_to_configure"] is False
    assert result["readiness_state"] == "codex_cli_unavailable"
    assert result["fallback"] == "docs_search_adapter"
    assert result["chrome_devtools_mcp_configured"] is False
    assert result["chrome_devtools_mcp_servers"] == []
    assert "do not modify" in result["recommended_action"].lower()


def test_mcp_readiness_distinguishes_cli_ready_from_configured_mcp():
    with patch(
        "tools.mcp_readiness_check.inspect_docs_search_runtime_support",
        return_value={
            "real_mcp_supported": False,
            "codex_cli_invocable": True,
            "cli_error": None,
            "config_path": "C:/Users/test/.codex/config.toml",
            "configured_in_global_codex": False,
        },
    ):
        with patch("tools.mcp_readiness_check._read_text_if_exists", return_value=""):
            with patch("tools.mcp_readiness_check._probe_codex_mcp_list", return_value={"functional": True, "error": None, "stdout_preview": "No MCP servers configured yet.", "stderr_preview": ""}):
                result = check_mcp_readiness()

    assert result["codex_cli_available"] is True
    assert result["codex_mcp_cli_functional"] is True
    assert result["configured_mcp_servers"] == []
    assert result["configured_mcp_server_count"] == 0
    assert result["chrome_devtools_mcp_configured"] is False
    assert result["openai_docs_mcp_configured"] is False
    assert result["openai_docs_mcp_functional"] is False
    assert result["real_mcp_safe_to_configure"] is False
    assert result["readiness_state"] == "cli_ready_no_servers_configured"
    assert "no MCP servers are configured" in result["recommended_action"]


def test_mcp_readiness_lists_configured_servers_without_claiming_functional_use():
    config_text = """
[mcp_servers.openaiDeveloperDocs]
url = "https://developers.openai.com/mcp"

[mcp_servers."21st_magic"]
command = "npx"

[mcp_servers.chrome-devtools-mcp]
command = "npx"
"""
    with patch(
        "tools.mcp_readiness_check.inspect_docs_search_runtime_support",
        return_value={
            "real_mcp_supported": False,
            "codex_cli_invocable": True,
            "cli_error": None,
            "config_path": "C:/Users/test/.codex/config.toml",
            "configured_in_global_codex": True,
        },
    ):
        with patch("tools.mcp_readiness_check._read_text_if_exists", return_value=config_text):
            with patch("tools.mcp_readiness_check._probe_codex_mcp_list", return_value={"functional": True, "error": None, "stdout_preview": "openaiDeveloperDocs\n21st_magic", "stderr_preview": ""}):
                result = check_mcp_readiness()

    assert result["configured_mcp_servers"] == ["openaiDeveloperDocs", "21st_magic", "chrome-devtools-mcp"]
    assert result["chrome_devtools_mcp_configured"] is True
    assert result["chrome_devtools_mcp_servers"] == ["chrome-devtools-mcp"]
    assert result["openai_docs_mcp_configured"] is True
    assert result["openai_docs_mcp_functional"] is False
    assert result["readiness_state"] == "configured_but_not_functionally_verified"
