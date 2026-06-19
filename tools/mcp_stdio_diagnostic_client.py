"""Minimal generic MCP stdio diagnostic client for Atlas.

This client validates the base MCP lifecycle only:

1. launch an MCP stdio server,
2. send initialize,
3. send notifications/initialized,
4. request tools/list,
5. close stdin and shut the server down.

It intentionally does not call tools, read resources, get prompts, or integrate
with Atlas runtime components.
"""

from __future__ import annotations

import argparse
import json
import os
import queue
import subprocess
import threading
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Mapping, Optional


PROTOCOL_VERSION = "2025-06-18"
DEFAULT_SANDBOX = Path(".atlas_test_tmp") / "mcp_protocol_validation"
DEFAULT_REPORT = DEFAULT_SANDBOX / "mcp_protocol_validation_report.json"


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def build_initialize_request(request_id: int = 1) -> Dict[str, Any]:
    return {
        "jsonrpc": "2.0",
        "id": request_id,
        "method": "initialize",
        "params": {
            "protocolVersion": PROTOCOL_VERSION,
            "capabilities": {},
            "clientInfo": {
                "name": "codex-atlas-mcp-diagnostic-client",
                "title": "Codex-Atlas MCP Diagnostic Client",
                "version": "v1",
            },
        },
    }


def build_initialized_notification() -> Dict[str, Any]:
    return {"jsonrpc": "2.0", "method": "notifications/initialized"}


def build_tools_list_request(request_id: int = 2) -> Dict[str, Any]:
    return {"jsonrpc": "2.0", "id": request_id, "method": "tools/list", "params": {}}


def encode_stdio_message(message: Mapping[str, Any]) -> str:
    encoded = json.dumps(message, separators=(",", ":"), ensure_ascii=False)
    if "\n" in encoded or "\r" in encoded:
        raise ValueError("MCP stdio messages must not contain embedded newlines")
    return encoded + "\n"


def _reader(stream: Any, output: "queue.Queue[str]", stop: threading.Event) -> None:
    while not stop.is_set():
        line = stream.readline()
        if line == "":
            return
        output.put(line)


def _start_reader(stream: Any) -> tuple["queue.Queue[str]", threading.Event, threading.Thread]:
    output: "queue.Queue[str]" = queue.Queue()
    stop = threading.Event()
    thread = threading.Thread(target=_reader, args=(stream, output, stop), daemon=True)
    thread.start()
    return output, stop, thread


def _decode_line(line: str) -> Dict[str, Any]:
    return json.loads(line.strip())


def _wait_for_response(
    output: "queue.Queue[str]",
    *,
    request_id: int,
    timeout_seconds: float,
    notifications: List[Dict[str, Any]],
) -> Dict[str, Any]:
    deadline = time.monotonic() + timeout_seconds
    while True:
        remaining = deadline - time.monotonic()
        if remaining <= 0:
            raise TimeoutError(f"timeout_waiting_for_response:{request_id}")
        line = output.get(timeout=remaining)
        message = _decode_line(line)
        if message.get("id") == request_id:
            return message
        notifications.append(message)


def _write_message(stdin: Any, message: Mapping[str, Any]) -> None:
    stdin.write(encode_stdio_message(message))
    stdin.flush()


def _tool_summary(tools_result: Mapping[str, Any]) -> List[Dict[str, Any]]:
    tools = tools_result.get("tools", [])
    if not isinstance(tools, list):
        return []
    summarized = []
    for tool in tools:
        if not isinstance(tool, dict):
            continue
        schema = tool.get("inputSchema") if isinstance(tool.get("inputSchema"), dict) else {}
        summarized.append(
            {
                "name": tool.get("name", ""),
                "title": tool.get("title", ""),
                "description": tool.get("description", ""),
                "input_schema_type": schema.get("type", ""),
                "parameters": sorted((schema.get("properties") or {}).keys()),
                "required": schema.get("required", []),
            }
        )
    return summarized


def run_mcp_protocol_validation(
    *,
    command: List[str],
    sandbox_dir: Path | str = DEFAULT_SANDBOX,
    report_path: Path | str | None = DEFAULT_REPORT,
    project: str = "codex-atlas-v4-mcp-protocol",
    request_timeout_seconds: float = 5.0,
    shutdown_timeout_seconds: float = 5.0,
    popen_factory: Any = subprocess.Popen,
) -> Dict[str, Any]:
    sandbox = Path(sandbox_dir)
    sandbox.mkdir(parents=True, exist_ok=True)
    resolved_sandbox = sandbox.resolve()

    env = os.environ.copy()
    env["ENGRAM_DATA_DIR"] = str(resolved_sandbox)
    env["ENGRAM_PROJECT"] = project

    report: Dict[str, Any] = {
        "client_name": "mcp_stdio_diagnostic_client",
        "version": "v1",
        "generated_at": _utc_now(),
        "protocol_version_requested": PROTOCOL_VERSION,
        "command": command,
        "sandbox_dir": str(resolved_sandbox),
        "env": {
            "ENGRAM_DATA_DIR": str(resolved_sandbox),
            "ENGRAM_PROJECT": project,
        },
        "initialize": {"status": "UNKNOWN", "response": None},
        "initialized": {"status": "UNKNOWN"},
        "tools_list": {"status": "UNKNOWN", "tool_count": 0, "tools": []},
        "shutdown": {"status": "UNKNOWN", "exit_code": None},
        "notifications_received": [],
        "stderr": [],
        "errors": [],
        "classification": "UNKNOWN",
    }

    process = None
    stdout_stop: Optional[threading.Event] = None
    stderr_stop: Optional[threading.Event] = None
    stderr_queue: Optional["queue.Queue[str]"] = None
    try:
        process = popen_factory(
            command,
            cwd=str(Path.cwd()),
            env=env,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            encoding="utf-8",
            errors="replace",
            bufsize=1,
        )
        stdout_queue, stdout_stop, _stdout_thread = _start_reader(process.stdout)
        stderr_queue, stderr_stop, _stderr_thread = _start_reader(process.stderr)

        _write_message(process.stdin, build_initialize_request(1))
        initialize_response = _wait_for_response(
            stdout_queue,
            request_id=1,
            timeout_seconds=request_timeout_seconds,
            notifications=report["notifications_received"],
        )
        report["initialize"]["response"] = initialize_response
        if "result" in initialize_response:
            report["initialize"]["status"] = "PASS"
        else:
            report["initialize"]["status"] = "FAIL"
            report["errors"].append("initialize_error_response")

        if report["initialize"]["status"] == "PASS":
            _write_message(process.stdin, build_initialized_notification())
            report["initialized"]["status"] = "PASS"

            _write_message(process.stdin, build_tools_list_request(2))
            tools_response = _wait_for_response(
                stdout_queue,
                request_id=2,
                timeout_seconds=request_timeout_seconds,
                notifications=report["notifications_received"],
            )
            if "result" in tools_response:
                tools = _tool_summary(tools_response["result"])
                report["tools_list"] = {
                    "status": "PASS",
                    "tool_count": len(tools),
                    "tools": tools,
                }
            else:
                report["tools_list"]["status"] = "FAIL"
                report["errors"].append("tools_list_error_response")
    except Exception as exc:
        report["errors"].append(f"{type(exc).__name__}:{exc}")
        if report["initialize"]["status"] == "UNKNOWN":
            report["initialize"]["status"] = "FAIL"
        if report["tools_list"]["status"] == "UNKNOWN":
            report["tools_list"]["status"] = "FAIL"
    finally:
        if process is not None:
            if process.stdin is not None:
                try:
                    process.stdin.close()
                except OSError:
                    pass
            try:
                process.wait(timeout=shutdown_timeout_seconds)
                report["shutdown"]["status"] = "PASS"
            except subprocess.TimeoutExpired:
                process.terminate()
                try:
                    process.wait(timeout=shutdown_timeout_seconds)
                    report["shutdown"]["status"] = "TERMINATED"
                except subprocess.TimeoutExpired:
                    process.kill()
                    process.wait(timeout=shutdown_timeout_seconds)
                    report["shutdown"]["status"] = "KILLED"
            report["shutdown"]["exit_code"] = process.returncode

        for stop in (stdout_stop, stderr_stop):
            if stop is not None:
                stop.set()
        if stderr_queue is not None:
            report["stderr"] = _drain_queue(stderr_queue)

    if (
        report["initialize"]["status"] == "PASS"
        and report["initialized"]["status"] == "PASS"
        and report["tools_list"]["status"] == "PASS"
        and report["shutdown"]["status"] in {"PASS", "TERMINATED"}
    ):
        report["classification"] = "MCP_PROTOCOL_VALIDATED"
    else:
        report["classification"] = "MCP_PROTOCOL_PARTIAL"

    _write_report(report, report_path)
    return report


def _drain_queue(values: "queue.Queue[str]") -> List[str]:
    drained: List[str] = []
    while True:
        try:
            drained.append(values.get_nowait().strip())
        except queue.Empty:
            return [line for line in drained if line]


def _write_report(report: Mapping[str, Any], report_path: Path | str | None) -> None:
    if report_path is None:
        return
    output = Path(report_path)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def validate_mcp_protocol_report(report: Mapping[str, Any]) -> Dict[str, Any]:
    required = (
        "client_name",
        "version",
        "generated_at",
        "protocol_version_requested",
        "command",
        "initialize",
        "initialized",
        "tools_list",
        "shutdown",
        "classification",
    )
    findings = [f"missing:{key}" for key in required if key not in report]
    valid = not findings
    return {"status": "PASS" if valid else "FAIL", "valid": valid, "findings": findings}


def main(argv: Optional[Iterable[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Validate a minimal MCP stdio lifecycle.")
    parser.add_argument("--command", nargs="+", default=["engram", "mcp", "--tools=agent"])
    parser.add_argument("--sandbox-dir", default=str(DEFAULT_SANDBOX))
    parser.add_argument("--report", default=str(DEFAULT_REPORT))
    parser.add_argument("--project", default="codex-atlas-v4-mcp-protocol")
    parser.add_argument("--request-timeout-seconds", type=float, default=5.0)
    parser.add_argument("--shutdown-timeout-seconds", type=float, default=5.0)
    args = parser.parse_args(list(argv) if argv is not None else None)

    report = run_mcp_protocol_validation(
        command=args.command,
        sandbox_dir=args.sandbox_dir,
        report_path=args.report,
        project=args.project,
        request_timeout_seconds=args.request_timeout_seconds,
        shutdown_timeout_seconds=args.shutdown_timeout_seconds,
    )
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0 if report["classification"] == "MCP_PROTOCOL_VALIDATED" else 1


if __name__ == "__main__":
    raise SystemExit(main())
