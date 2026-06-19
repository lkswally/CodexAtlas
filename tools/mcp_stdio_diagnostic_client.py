"""Minimal generic MCP stdio diagnostic client for Atlas.

This client validates the base MCP lifecycle only:

1. launch an MCP stdio server,
2. send initialize,
3. send notifications/initialized,
4. request tools/list,
5. optionally request resources/list and prompts/list when supported,
6. optionally call one allowlisted read-only tool in a sandbox,
7. close stdin and shut the server down.

It intentionally does not read resources, get prompts, call write-capable tools,
or integrate with Atlas runtime components.
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
DEFAULT_POLICY = Path("config") / "mcp_read_only_tool_policy.json"
TOOL_CALL_REQUEST_ID = 5


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


def build_resources_list_request(request_id: int = 3) -> Dict[str, Any]:
    return {"jsonrpc": "2.0", "id": request_id, "method": "resources/list", "params": {}}


def build_prompts_list_request(request_id: int = 4) -> Dict[str, Any]:
    return {"jsonrpc": "2.0", "id": request_id, "method": "prompts/list", "params": {}}


def build_tools_call_request(tool_name: str, arguments: Mapping[str, Any], request_id: int = TOOL_CALL_REQUEST_ID) -> Dict[str, Any]:
    return {
        "jsonrpc": "2.0",
        "id": request_id,
        "method": "tools/call",
        "params": {"name": tool_name, "arguments": dict(arguments)},
    }


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


def _schema_parameters(schema: Mapping[str, Any]) -> List[str]:
    return sorted((schema.get("properties") or {}).keys())


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
                "parameters": _schema_parameters(schema),
                "required": schema.get("required", []),
            }
        )
    return summarized


def _tool_by_name(tools_result: Mapping[str, Any], tool_name: str) -> Dict[str, Any] | None:
    tools = tools_result.get("tools", [])
    if not isinstance(tools, list):
        return None
    for tool in tools:
        if isinstance(tool, dict) and tool.get("name") == tool_name:
            return tool
    return None


def _resource_summary(resources_result: Mapping[str, Any]) -> List[Dict[str, Any]]:
    resources = resources_result.get("resources", [])
    if not isinstance(resources, list):
        return []
    summarized = []
    for resource in resources:
        if not isinstance(resource, dict):
            continue
        summarized.append(
            {
                "uri": resource.get("uri", ""),
                "name": resource.get("name", ""),
                "title": resource.get("title", ""),
                "description": resource.get("description", ""),
                "mime_type": resource.get("mimeType", ""),
            }
        )
    return summarized


def _prompt_summary(prompts_result: Mapping[str, Any]) -> List[Dict[str, Any]]:
    prompts = prompts_result.get("prompts", [])
    if not isinstance(prompts, list):
        return []
    summarized = []
    for prompt in prompts:
        if not isinstance(prompt, dict):
            continue
        arguments = prompt.get("arguments", [])
        if not isinstance(arguments, list):
            arguments = []
        summarized.append(
            {
                "name": prompt.get("name", ""),
                "title": prompt.get("title", ""),
                "description": prompt.get("description", ""),
                "arguments": [
                    argument.get("name", "")
                    for argument in arguments
                    if isinstance(argument, dict) and argument.get("name")
                ],
            }
        )
    return summarized


def _jsonrpc_error_code(response: Mapping[str, Any]) -> Any:
    error = response.get("error")
    if not isinstance(error, dict):
        return None
    return error.get("code")


def _optional_list_status(
    *,
    capability_name: str,
    capabilities: Mapping[str, Any],
    response: Mapping[str, Any] | None,
) -> str:
    if capability_name not in capabilities:
        return "NOT_SUPPORTED"
    if response is None:
        return "FAIL"
    if "result" in response:
        return "PASS"
    if _jsonrpc_error_code(response) == -32601:
        return "NOT_SUPPORTED"
    return "FAIL"


def load_read_only_tool_policy(policy_path: Path | str = DEFAULT_POLICY) -> Dict[str, Any]:
    path = Path(policy_path)
    return json.loads(path.read_text(encoding="utf-8"))


def _empty_tool_call_report() -> Dict[str, Any]:
    return {
        "tool_call_supported": False,
        "tool_name": "",
        "input": {},
        "policy_status": "UNKNOWN",
        "call_status": "BLOCKED",
        "side_effects_expected": False,
        "result_excerpt": "",
        "errors": [],
    }


def _tool_policy_entry(policy: Mapping[str, Any], tool_name: str) -> Mapping[str, Any] | None:
    allowlist = policy.get("tool_allowlist", {})
    if not isinstance(allowlist, dict):
        return None
    entry = allowlist.get(tool_name)
    return entry if isinstance(entry, dict) else None


def _schema_is_understood(schema: Mapping[str, Any]) -> bool:
    schema_type = schema.get("type")
    properties = schema.get("properties", {})
    required = schema.get("required", [])
    return (
        schema_type == "object"
        and isinstance(properties, dict)
        and isinstance(required, list)
        and all(isinstance(item, str) for item in required)
    )


def _evaluate_read_only_tool_policy(
    *,
    policy: Mapping[str, Any] | None,
    tool: Mapping[str, Any] | None,
    tool_name: str,
    arguments: Mapping[str, Any],
) -> Dict[str, Any]:
    report = _empty_tool_call_report()
    report["tool_name"] = tool_name
    report["input"] = dict(arguments)

    if policy is None:
        report["policy_status"] = "UNKNOWN"
        report["errors"].append("policy_missing")
        return report
    entry = _tool_policy_entry(policy, tool_name)
    if entry is None:
        report["policy_status"] = "DENIED"
        report["errors"].append("tool_not_allowlisted")
        return report
    if tool is None:
        report["policy_status"] = "DENIED"
        report["errors"].append("tool_not_advertised")
        return report
    if entry.get("classification") != "read_only":
        report["policy_status"] = "DENIED"
        report["errors"].append("tool_not_read_only")
        return report
    if entry.get("side_effects_expected") is not False:
        report["policy_status"] = "DENIED"
        report["side_effects_expected"] = True
        report["errors"].append("side_effects_not_false")
        return report

    schema = tool.get("inputSchema") if isinstance(tool.get("inputSchema"), dict) else {}
    if not _schema_is_understood(schema):
        report["policy_status"] = "DENIED"
        report["errors"].append("schema_not_understood")
        return report

    properties = schema.get("properties", {})
    schema_parameters = set(properties.keys())
    allowed_arguments = entry.get("allowed_arguments", [])
    if not isinstance(allowed_arguments, list) or not all(isinstance(arg, str) for arg in allowed_arguments):
        report["policy_status"] = "DENIED"
        report["errors"].append("policy_allowed_arguments_invalid")
        return report
    allowed_set = set(allowed_arguments)
    required = set(schema.get("required", []))
    input_set = set(arguments.keys())

    if not input_set <= allowed_set:
        report["policy_status"] = "DENIED"
        report["errors"].append("argument_not_allowlisted")
        return report
    if not input_set <= schema_parameters:
        report["policy_status"] = "DENIED"
        report["errors"].append("argument_not_in_schema")
        return report
    if not required <= input_set:
        report["policy_status"] = "DENIED"
        report["errors"].append("required_argument_missing")
        return report
    if not required <= allowed_set:
        report["policy_status"] = "DENIED"
        report["errors"].append("required_argument_not_allowlisted")
        return report

    report["tool_call_supported"] = True
    report["policy_status"] = "ALLOWED"
    return report


def _result_excerpt(response: Mapping[str, Any], max_chars: int = 500) -> str:
    result = response.get("result", {})
    encoded = json.dumps(result, sort_keys=True, ensure_ascii=False)
    if len(encoded) <= max_chars:
        return encoded
    return encoded[:max_chars] + "..."


def run_mcp_protocol_validation(
    *,
    command: List[str],
    sandbox_dir: Path | str = DEFAULT_SANDBOX,
    report_path: Path | str | None = DEFAULT_REPORT,
    project: str = "codex-atlas-v4-mcp-protocol",
    request_timeout_seconds: float = 5.0,
    shutdown_timeout_seconds: float = 5.0,
    popen_factory: Any = subprocess.Popen,
    enable_read_only_tool_call: bool = False,
    read_only_tool_name: str = "",
    read_only_tool_arguments: Mapping[str, Any] | None = None,
    read_only_tool_policy: Mapping[str, Any] | None = None,
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
        "protocol_version": "",
        "server_info": {},
        "capabilities": {},
        "command": command,
        "sandbox_dir": str(resolved_sandbox),
        "env": {
            "ENGRAM_DATA_DIR": str(resolved_sandbox),
            "ENGRAM_PROJECT": project,
        },
        "initialize": {"status": "UNKNOWN", "response": None},
        "initialized": {"status": "UNKNOWN"},
        "tools_list": {"status": "UNKNOWN", "tool_count": 0, "tools": []},
        "resources_list": {"status": "UNKNOWN", "resource_count": 0, "resources": []},
        "prompts_list": {"status": "UNKNOWN", "prompt_count": 0, "prompts": []},
        "tool_call": _empty_tool_call_report(),
        "summary": {
            "tools_count": 0,
            "resources_status": "UNKNOWN",
            "prompts_status": "UNKNOWN",
            "tool_call_status": "BLOCKED",
        },
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
            initialize_result = initialize_response["result"]
            if isinstance(initialize_result, dict):
                report["protocol_version"] = initialize_result.get("protocolVersion", "")
                report["server_info"] = initialize_result.get("serverInfo", {})
                capabilities = initialize_result.get("capabilities", {})
                report["capabilities"] = capabilities if isinstance(capabilities, dict) else {}
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
            raw_tools_result: Mapping[str, Any] = {}
            if "result" in tools_response:
                raw_tools_result = tools_response["result"]
                tools = _tool_summary(raw_tools_result)
                report["tools_list"] = {
                    "status": "PASS",
                    "tool_count": len(tools),
                    "tools": tools,
                }
                report["summary"]["tools_count"] = len(tools)
            else:
                report["tools_list"]["status"] = "FAIL"
                report["errors"].append("tools_list_error_response")

            resources_response = None
            if "resources" in report["capabilities"]:
                _write_message(process.stdin, build_resources_list_request(3))
                resources_response = _wait_for_response(
                    stdout_queue,
                    request_id=3,
                    timeout_seconds=request_timeout_seconds,
                    notifications=report["notifications_received"],
                )
            resources_status = _optional_list_status(
                capability_name="resources",
                capabilities=report["capabilities"],
                response=resources_response,
            )
            if resources_status == "PASS" and resources_response is not None:
                resources = _resource_summary(resources_response["result"])
                report["resources_list"] = {
                    "status": "PASS",
                    "resource_count": len(resources),
                    "resources": resources,
                }
            else:
                report["resources_list"]["status"] = resources_status
                if resources_status == "FAIL":
                    report["errors"].append("resources_list_error_response")
            report["summary"]["resources_status"] = report["resources_list"]["status"]

            prompts_response = None
            if "prompts" in report["capabilities"]:
                _write_message(process.stdin, build_prompts_list_request(4))
                prompts_response = _wait_for_response(
                    stdout_queue,
                    request_id=4,
                    timeout_seconds=request_timeout_seconds,
                    notifications=report["notifications_received"],
                )
            prompts_status = _optional_list_status(
                capability_name="prompts",
                capabilities=report["capabilities"],
                response=prompts_response,
            )
            if prompts_status == "PASS" and prompts_response is not None:
                prompts = _prompt_summary(prompts_response["result"])
                report["prompts_list"] = {
                    "status": "PASS",
                    "prompt_count": len(prompts),
                    "prompts": prompts,
                }
            else:
                report["prompts_list"]["status"] = prompts_status
                if prompts_status == "FAIL":
                    report["errors"].append("prompts_list_error_response")
            report["summary"]["prompts_status"] = report["prompts_list"]["status"]

            if enable_read_only_tool_call:
                tool_arguments = dict(read_only_tool_arguments or {})
                advertised_tool = _tool_by_name(raw_tools_result, read_only_tool_name)
                tool_call_report = _evaluate_read_only_tool_policy(
                    policy=read_only_tool_policy,
                    tool=advertised_tool,
                    tool_name=read_only_tool_name,
                    arguments=tool_arguments,
                )
                if tool_call_report["policy_status"] == "ALLOWED":
                    _write_message(process.stdin, build_tools_call_request(read_only_tool_name, tool_arguments))
                    tool_call_response = _wait_for_response(
                        stdout_queue,
                        request_id=TOOL_CALL_REQUEST_ID,
                        timeout_seconds=request_timeout_seconds,
                        notifications=report["notifications_received"],
                    )
                    if "result" in tool_call_response:
                        tool_call_report["call_status"] = "PASS"
                        tool_call_report["result_excerpt"] = _result_excerpt(tool_call_response)
                    else:
                        tool_call_report["call_status"] = "FAIL"
                        tool_call_report["errors"].append("tools_call_error_response")
                report["tool_call"] = tool_call_report
            report["summary"]["tool_call_status"] = report["tool_call"]["call_status"]
    except Exception as exc:
        report["errors"].append(f"{type(exc).__name__}:{exc}")
        if report["initialize"]["status"] == "UNKNOWN":
            report["initialize"]["status"] = "FAIL"
        if report["tools_list"]["status"] == "UNKNOWN":
            report["tools_list"]["status"] = "FAIL"
        for optional_key in ("resources_list", "prompts_list"):
            if report[optional_key]["status"] == "UNKNOWN":
                report[optional_key]["status"] = "FAIL"
        if report["tool_call"]["call_status"] == "BLOCKED" and enable_read_only_tool_call:
            report["tool_call"]["call_status"] = "FAIL"
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
        and report["resources_list"]["status"] in {"PASS", "NOT_SUPPORTED"}
        and report["prompts_list"]["status"] in {"PASS", "NOT_SUPPORTED"}
        and report["shutdown"]["status"] in {"PASS", "TERMINATED"}
        and report["tool_call"]["call_status"] in {"PASS", "BLOCKED"}
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
        "protocol_version",
        "server_info",
        "capabilities",
        "command",
        "initialize",
        "initialized",
        "tools_list",
        "resources_list",
        "prompts_list",
        "tool_call",
        "summary",
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
    parser.add_argument("--enable-read-only-tool-call", action="store_true")
    parser.add_argument("--read-only-tool-name", default="mem_doctor")
    parser.add_argument("--read-only-tool-arguments", default="{}")
    parser.add_argument("--read-only-tool-policy", default=str(DEFAULT_POLICY))
    args = parser.parse_args(list(argv) if argv is not None else None)

    policy = None
    if args.enable_read_only_tool_call:
        policy = load_read_only_tool_policy(args.read_only_tool_policy)
    tool_arguments = json.loads(args.read_only_tool_arguments)
    if not isinstance(tool_arguments, dict):
        raise ValueError("--read-only-tool-arguments must be a JSON object")

    report = run_mcp_protocol_validation(
        command=args.command,
        sandbox_dir=args.sandbox_dir,
        report_path=args.report,
        project=args.project,
        request_timeout_seconds=args.request_timeout_seconds,
        shutdown_timeout_seconds=args.shutdown_timeout_seconds,
        enable_read_only_tool_call=args.enable_read_only_tool_call,
        read_only_tool_name=args.read_only_tool_name,
        read_only_tool_arguments=tool_arguments,
        read_only_tool_policy=policy,
    )
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0 if report["classification"] == "MCP_PROTOCOL_VALIDATED" else 1


if __name__ == "__main__":
    raise SystemExit(main())
