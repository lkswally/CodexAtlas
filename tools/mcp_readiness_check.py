from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Optional

try:
    from tools.atlas_mcp_manager import inspect_docs_search_runtime_support
except ModuleNotFoundError:
    from atlas_mcp_manager import inspect_docs_search_runtime_support


DEFAULT_ROOT = Path(__file__).resolve().parents[1]


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def check_mcp_readiness(*, root: Optional[Path] = None) -> Dict[str, object]:
    runtime = inspect_docs_search_runtime_support()
    cli_available = bool(runtime.get("codex_cli_invocable"))
    cli_error = runtime.get("cli_error")
    real_mcp_safe = bool(runtime.get("real_mcp_supported"))

    if real_mcp_safe:
        recommended_action = "Codex CLI looks available and the official Docs MCP appears configured. Re-verify with explicit `codex mcp list` before touching Atlas policy."
    elif cli_error and "access is denied" in str(cli_error).lower():
        recommended_action = "Keep `docs_search_adapter` as fallback and do not modify `~/.codex/config.toml` until Codex CLI stops returning Access is denied."
    else:
        recommended_action = "Keep MCP real activation blocked and continue using `docs_search_adapter` until the Codex CLI path is verifiable."

    return {
        "status": "ok",
        "codex_cli_available": cli_available,
        "codex_cli_error": cli_error,
        "real_mcp_safe_to_configure": real_mcp_safe,
        "recommended_action": recommended_action,
        "fallback": "docs_search_adapter",
        "config_path": runtime.get("config_path"),
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
