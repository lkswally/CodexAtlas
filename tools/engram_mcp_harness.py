"""Local Engram MCP process harness for Atlas V4 studies.

This harness intentionally does not implement an MCP client. It only starts the
official `engram mcp` subprocess with a sandboxed ENGRAM_DATA_DIR, observes that
the process stays alive through a short startup window, then shuts it down and
reports the lifecycle result.
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Mapping, Optional


DEFAULT_SANDBOX = Path(".atlas_test_tmp") / "engram_mcp_harness"
DEFAULT_REPORT = DEFAULT_SANDBOX / "engram_mcp_harness_report.json"


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _redact_env(env: Mapping[str, str]) -> Dict[str, str]:
    safe: Dict[str, str] = {}
    for key in ("ENGRAM_DATA_DIR", "ENGRAM_PROJECT"):
        if key in env:
            safe[key] = env[key]
    return safe


def _truncate(value: str, limit: int = 4000) -> str:
    if len(value) <= limit:
        return value
    return value[:limit] + "\n...[truncated]"


def build_engram_mcp_command(
    *,
    engram_command: str = "engram",
    tools_profile: str = "agent",
    project: Optional[str] = None,
) -> List[str]:
    command = [engram_command, "mcp", f"--tools={tools_profile}"]
    if project:
        command.extend(["--project", project])
    return command


def run_engram_mcp_harness(
    *,
    sandbox_dir: Path | str = DEFAULT_SANDBOX,
    report_path: Path | str | None = DEFAULT_REPORT,
    engram_command: str = "engram",
    tools_profile: str = "agent",
    project: str = "codex-atlas-v4-mcp-sandbox",
    startup_seconds: float = 2.0,
    shutdown_timeout_seconds: float = 5.0,
    popen_factory: Any = subprocess.Popen,
) -> Dict[str, Any]:
    sandbox = Path(sandbox_dir)
    sandbox.mkdir(parents=True, exist_ok=True)
    resolved_sandbox = sandbox.resolve()

    command = build_engram_mcp_command(
        engram_command=engram_command,
        tools_profile=tools_profile,
        project=project,
    )
    env = os.environ.copy()
    env["ENGRAM_DATA_DIR"] = str(resolved_sandbox)
    env["ENGRAM_PROJECT"] = project

    report: Dict[str, Any] = {
        "harness_name": "engram_mcp_harness",
        "version": "v1",
        "generated_at": _utc_now(),
        "command": command,
        "env": _redact_env(env),
        "sandbox_dir": str(resolved_sandbox),
        "startup": {
            "status": "UNKNOWN",
            "wait_seconds": startup_seconds,
            "exit_code_during_startup": None,
        },
        "shutdown": {
            "status": "UNKNOWN",
            "timeout_seconds": shutdown_timeout_seconds,
            "exit_code": None,
        },
        "stdout": "",
        "stderr": "",
        "errors": [],
        "classification": "UNKNOWN",
        "handshake_attempted": False,
        "handshake_status": "NOT_ATTEMPTED",
    }

    process = None
    try:
        process = popen_factory(
            command,
            cwd=str(Path.cwd()),
            env=env,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        time.sleep(max(0.0, startup_seconds))
        startup_exit = process.poll()
        report["startup"]["exit_code_during_startup"] = startup_exit
        if startup_exit is None:
            report["startup"]["status"] = "PASS"
        else:
            report["startup"]["status"] = "FAIL"
            report["errors"].append(f"process_exited_during_startup:{startup_exit}")
    except FileNotFoundError as exc:
        report["startup"]["status"] = "FAIL"
        report["shutdown"]["status"] = "NOT_STARTED"
        report["errors"].append(f"command_not_found:{exc}")
        report["classification"] = "BROKEN_SANDBOX"
        _write_report(report, report_path)
        return report
    except Exception as exc:  # pragma: no cover - defensive reporting path
        report["startup"]["status"] = "FAIL"
        report["shutdown"]["status"] = "UNKNOWN"
        report["errors"].append(f"startup_exception:{type(exc).__name__}:{exc}")
        report["classification"] = "BROKEN_SANDBOX"
        _write_report(report, report_path)
        return report

    stdout = ""
    stderr = ""
    if process is not None:
        if process.poll() is None:
            try:
                process.terminate()
                stdout, stderr = process.communicate(timeout=shutdown_timeout_seconds)
                report["shutdown"]["status"] = "PASS"
            except subprocess.TimeoutExpired:
                process.kill()
                stdout, stderr = process.communicate(timeout=shutdown_timeout_seconds)
                report["shutdown"]["status"] = "TIMEOUT_KILLED"
                report["errors"].append("shutdown_timeout")
        else:
            stdout, stderr = process.communicate(timeout=shutdown_timeout_seconds)
            report["shutdown"]["status"] = "ALREADY_EXITED"

        report["shutdown"]["exit_code"] = process.returncode
        report["stdout"] = _truncate(stdout or "")
        report["stderr"] = _truncate(stderr or "")

    if report["startup"]["status"] == "PASS":
        report["classification"] = "PARTIAL_MCP_AVAILABLE"
    else:
        report["classification"] = "BROKEN_SANDBOX"

    _write_report(report, report_path)
    return report


def _write_report(report: Mapping[str, Any], report_path: Path | str | None) -> None:
    if report_path is None:
        return
    output = Path(report_path)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def validate_engram_mcp_harness_report(report: Mapping[str, Any]) -> Dict[str, Any]:
    required = (
        "harness_name",
        "version",
        "generated_at",
        "command",
        "env",
        "sandbox_dir",
        "startup",
        "shutdown",
        "classification",
        "handshake_attempted",
        "handshake_status",
    )
    findings = [f"missing:{key}" for key in required if key not in report]
    valid = not findings
    return {"status": "PASS" if valid else "FAIL", "valid": valid, "findings": findings}


def main(argv: Optional[Iterable[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Run the Engram MCP sandbox process harness.")
    parser.add_argument("--sandbox-dir", default=str(DEFAULT_SANDBOX))
    parser.add_argument("--report", default=str(DEFAULT_REPORT))
    parser.add_argument("--engram-command", default="engram")
    parser.add_argument("--tools-profile", default="agent")
    parser.add_argument("--project", default="codex-atlas-v4-mcp-sandbox")
    parser.add_argument("--startup-seconds", type=float, default=2.0)
    parser.add_argument("--shutdown-timeout-seconds", type=float, default=5.0)
    args = parser.parse_args(list(argv) if argv is not None else None)

    report = run_engram_mcp_harness(
        sandbox_dir=args.sandbox_dir,
        report_path=args.report,
        engram_command=args.engram_command,
        tools_profile=args.tools_profile,
        project=args.project,
        startup_seconds=args.startup_seconds,
        shutdown_timeout_seconds=args.shutdown_timeout_seconds,
    )
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0 if report["classification"] == "PARTIAL_MCP_AVAILABLE" else 1


if __name__ == "__main__":
    raise SystemExit(main())
