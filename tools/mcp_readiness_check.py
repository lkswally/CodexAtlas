from __future__ import annotations

import argparse
import json
import re
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional

try:
    from tools.atlas_mcp_manager import inspect_docs_search_runtime_support
except ModuleNotFoundError:
    from atlas_mcp_manager import inspect_docs_search_runtime_support


DEFAULT_ROOT = Path(__file__).resolve().parents[1]
GLOBAL_CODEX_CONFIG = Path.home() / ".codex" / "config.toml"


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _read_text_if_exists(path: Path) -> str:
    if not path.exists():
        return ""
    try:
        return path.read_text(encoding="utf-8")
    except Exception:
        return ""


def _extract_configured_mcp_servers(config_text: str) -> List[str]:
    servers: List[str] = []
    for match in re.finditer(r"^\s*\[mcp_servers\.([^\]\s]+)\]\s*$", config_text, re.MULTILINE):
        server = match.group(1).strip().strip('"')
        if server and server not in servers:
            servers.append(server)
    return servers


def _probe_codex_mcp_list() -> Dict[str, object]:
    try:
        completed = subprocess.run(
            ["codex", "mcp", "list"],
            capture_output=True,
            text=True,
            timeout=10,
            check=False,
        )
    except Exception as exc:
        return {
            "functional": False,
            "error": str(exc),
            "stdout_preview": "",
            "stderr_preview": "",
        }

    stdout = (completed.stdout or "").strip()
    stderr = (completed.stderr or "").strip()
    return {
        "functional": completed.returncode == 0,
        "error": None if completed.returncode == 0 else (stderr or stdout or f"exit_code:{completed.returncode}"),
        "stdout_preview": stdout[:300],
        "stderr_preview": stderr[:300],
    }


def _derive_readiness_state(
    *,
    cli_available: bool,
    mcp_cli_functional: bool,
    configured_servers: List[str],
    docs_configured: bool,
    real_mcp_safe: bool,
) -> str:
    if real_mcp_safe:
        return "real_mcp_configured_and_cli_verified"
    if not cli_available:
        return "codex_cli_unavailable"
    if not mcp_cli_functional:
        return "codex_mcp_cli_unavailable"
    if not configured_servers:
        return "cli_ready_no_servers_configured"
    if not docs_configured:
        return "servers_configured_but_openai_docs_missing"
    return "configured_but_not_functionally_verified"


def _recommended_action_for_state(state: str, cli_error: object, mcp_list_error: object) -> str:
    if state == "real_mcp_configured_and_cli_verified":
        return "A real MCP entry appears configured and Codex MCP CLI is callable. Still require explicit user approval before changing any MCP config."
    if state == "codex_cli_unavailable":
        if cli_error and "access is denied" in str(cli_error).lower():
            return "Keep `docs_search_adapter` as fallback and do not modify `~/.codex/config.toml` until Codex CLI stops returning Access is denied."
        return "Keep MCP real activation blocked until Codex CLI can be invoked successfully."
    if state == "codex_mcp_cli_unavailable":
        return f"Keep MCP real activation blocked because `codex mcp list` is not functional: {mcp_list_error}"
    if state == "cli_ready_no_servers_configured":
        return "Codex MCP CLI is callable, but no MCP servers are configured. Do not add servers without explicit approval and secret-safe setup."
    if state == "servers_configured_but_openai_docs_missing":
        return "Some MCP servers are configured, but OpenAI Developer Docs MCP is not configured. Verify each server manually before claiming it is functional."
    return "MCP configuration exists, but functional use is not verified. Keep adapters as fallback and require explicit approval before activation."


def check_mcp_readiness(*, root: Optional[Path] = None) -> Dict[str, object]:
    runtime = inspect_docs_search_runtime_support()
    cli_available = bool(runtime.get("codex_cli_invocable"))
    cli_error = runtime.get("cli_error")
    real_mcp_safe = bool(runtime.get("real_mcp_supported"))
    config_path = Path(str(runtime.get("config_path") or GLOBAL_CODEX_CONFIG))
    config_text = _read_text_if_exists(config_path)
    configured_servers = _extract_configured_mcp_servers(config_text)
    docs_configured = "openaiDeveloperDocs" in configured_servers or bool(runtime.get("configured_in_global_codex"))
    mcp_list = _probe_codex_mcp_list()
    mcp_cli_functional = bool(mcp_list.get("functional"))

    readiness_state = _derive_readiness_state(
        cli_available=cli_available,
        mcp_cli_functional=mcp_cli_functional,
        configured_servers=configured_servers,
        docs_configured=docs_configured,
        real_mcp_safe=real_mcp_safe,
    )
    recommended_action = _recommended_action_for_state(
        readiness_state,
        cli_error,
        mcp_list.get("error"),
    )

    return {
        "status": "ok",
        "codex_cli_available": cli_available,
        "codex_cli_error": cli_error,
        "codex_mcp_cli_functional": mcp_cli_functional,
        "codex_mcp_list_error": mcp_list.get("error"),
        "configured_mcp_servers": configured_servers,
        "configured_mcp_server_count": len(configured_servers),
        "openai_docs_mcp_configured": docs_configured,
        "openai_docs_mcp_functional": bool(real_mcp_safe and docs_configured and mcp_cli_functional),
        "real_mcp_safe_to_configure": real_mcp_safe,
        "readiness_state": readiness_state,
        "recommended_action": recommended_action,
        "fallback": "docs_search_adapter",
        "config_path": str(config_path),
        "mcp_list_stdout_preview": mcp_list.get("stdout_preview"),
        "mcp_list_stderr_preview": mcp_list.get("stderr_preview"),
        "manual_next_steps": [
            "Do not paste API keys in chat.",
            "Do not commit API keys or MCP secrets to Atlas.",
            "Add MCP servers only after explicit approval.",
            "Use environment variables or the Codex-approved secret mechanism for any future key.",
            "Verify with `codex mcp list` after manual configuration.",
        ],
        "timestamp": _utc_now_iso(),
    }


def main(argv: Optional[list[str]] = None) -> int:
    parser = argparse.ArgumentParser(add_help=True)
    parser.add_argument("--root", default=None, help="Atlas root to use.")
    parser.parse_args(argv)
    result = check_mcp_readiness(root=DEFAULT_ROOT)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
