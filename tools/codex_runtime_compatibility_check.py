from __future__ import annotations

import argparse
import json
import subprocess
from pathlib import Path
from typing import Any, Dict, List, Optional

try:
    from tools.mcp_readiness_check import check_mcp_readiness
except ModuleNotFoundError:
    from mcp_readiness_check import check_mcp_readiness
try:
    from tools.model_router_core import inspect_model_switch_support
except ModuleNotFoundError:
    from model_router_core import inspect_model_switch_support


DEFAULT_ROOT = Path(__file__).resolve().parents[1]
RULES_PATH = Path("config/codex_runtime_compatibility_rules.json")


def load_codex_runtime_compatibility_rules(root: Path = DEFAULT_ROOT) -> Dict[str, Any]:
    return json.loads((root / RULES_PATH).read_text(encoding="utf-8-sig"))


def _probe_codex_version() -> Dict[str, Any]:
    try:
        result = subprocess.run(
            ["codex", "--version"],
            capture_output=True,
            text=True,
            timeout=10,
            check=False,
        )
    except Exception as exc:
        return {
            "available": False,
            "version": None,
            "error": str(exc),
        }
    output = (result.stdout or result.stderr or "").strip()
    return {
        "available": result.returncode == 0,
        "version": output if result.returncode == 0 else None,
        "error": None if result.returncode == 0 else output or f"codex_exit_{result.returncode}",
    }


def check_codex_runtime_compatibility(root: Optional[Path] = None) -> Dict[str, Any]:
    root = (root or DEFAULT_ROOT).resolve()
    rules = load_codex_runtime_compatibility_rules(root)
    version_probe = _probe_codex_version()
    mcp_report = check_mcp_readiness(root=root)
    model_support = inspect_model_switch_support(root=root)

    configured_mcp_servers = list(mcp_report.get("configured_mcp_servers", []))
    runtime_model_visible = bool(model_support.get("current_project_model") or model_support.get("current_global_model"))
    limitations = list(rules.get("known_limitations", []))
    if not version_probe.get("available"):
        limitations.append("codex_cli_not_callable")
    if not bool(mcp_report.get("codex_mcp_cli_functional")):
        limitations.append("mcp_cli_not_functional")
    if not configured_mcp_servers:
        limitations.append("no_mcp_servers_configured")
    if not runtime_model_visible:
        limitations.append("runtime_model_not_visible")

    safe_to_use_with_atlas = bool(version_probe.get("available")) and bool(mcp_report.get("codex_mcp_cli_functional"))
    status = "ok" if safe_to_use_with_atlas else "needs_attention"

    manual_steps: List[str] = list(rules.get("manual_step_templates", []))
    if not version_probe.get("available"):
        manual_steps.insert(0, "Ensure the Codex CLI is installed and callable in the current shell before relying on Atlas runtime posture.")
    if not bool(mcp_report.get("codex_mcp_cli_functional")):
        manual_steps.insert(0, "Fix `codex mcp list` locally before treating MCP posture as reliable.")
    if configured_mcp_servers and not bool(mcp_report.get("openai_docs_mcp_functional")):
        manual_steps.insert(0, "A configured MCP exists but is not functionally verified; keep it advisory until local verification passes.")
    if not configured_mcp_servers:
        manual_steps.insert(0, "No MCP servers are configured; Atlas can still run locally, but MCP-backed claims must stay in readiness/watchlist language.")
    manual_steps = list(dict.fromkeys(manual_steps))

    why = (
        "Codex runtime compatibility is derived from local CLI probes, local MCP inspection and visible config/model metadata only."
    )
    return {
        "status": status,
        "codex_cli_available": bool(version_probe.get("available")),
        "codex_version": version_probe.get("version"),
        "mcp_cli_functional": bool(mcp_report.get("codex_mcp_cli_functional")),
        "configured_mcp_servers": configured_mcp_servers,
        "runtime_model_visible": runtime_model_visible,
        "safe_to_use_with_atlas": safe_to_use_with_atlas,
        "limitations": limitations,
        "manual_steps": manual_steps,
        "why": why,
        "advisory_only": bool(rules.get("advisory_only", True)),
    }


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(add_help=True)
    parser.add_argument("--root", default=None)
    args = parser.parse_args(argv)
    root = Path(args.root).resolve() if args.root else DEFAULT_ROOT
    result = check_codex_runtime_compatibility(root=root)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
