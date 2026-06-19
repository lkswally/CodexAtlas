import io
import json

from tools.mcp_stdio_diagnostic_client import (
    PROTOCOL_VERSION,
    build_initialize_request,
    build_initialized_notification,
    build_prompts_list_request,
    build_resources_list_request,
    build_tools_call_request,
    build_tools_list_request,
    encode_stdio_message,
    run_mcp_protocol_validation,
    validate_mcp_protocol_report,
)


class RecordingStdin(io.StringIO):
    def close(self):
        self.seek(0)


class FakeProcess:
    def __init__(self, stdout_lines):
        self.stdin = RecordingStdin()
        self.stdout = io.StringIO("".join(stdout_lines))
        self.stderr = io.StringIO("")
        self.returncode = None

    def wait(self, timeout=None):
        self.returncode = 0
        return 0

    def terminate(self):
        self.returncode = 1

    def kill(self):
        self.returncode = -9


def _initialize_response(capabilities):
    return (
        '{"jsonrpc":"2.0","id":1,"result":{"protocolVersion":"2025-06-18",'
        f'"capabilities":{capabilities},'
        '"serverInfo":{"name":"fake","version":"1"}}}\n'
    )


def _tools_response(tool_name="mem_search", schema=None, description="Search memory"):
    schema = schema or {
        "type": "object",
        "properties": {"query": {"type": "string"}, "limit": {"type": "integer"}},
        "required": ["query"],
    }
    return (
        '{"jsonrpc":"2.0","id":2,"result":{"tools":[{"name":'
        + repr(tool_name).replace("'", '"')
        + ',"description":'
        + repr(description).replace("'", '"')
        + ',"inputSchema":'
        + json.dumps(schema, separators=(",", ":"))
        + "}]}}\n"
    )


def _policy():
    return {
        "tool_allowlist": {
            "mem_doctor": {
                "classification": "read_only",
                "side_effects_expected": False,
                "allowed_arguments": ["check", "project"],
            }
        }
    }


def _run_fake(stdout_lines, tmp_path, **kwargs):
    fake = FakeProcess(stdout_lines)
    captured = {}

    def popen(command, **popen_kwargs):
        captured["command"] = command
        captured["env"] = popen_kwargs["env"]
        return fake

    report = run_mcp_protocol_validation(
        command=["fake-mcp"],
        sandbox_dir=tmp_path / "mcp",
        report_path=None,
        popen_factory=popen,
        **kwargs,
    )
    return report, fake, captured


def test_build_initialize_request_matches_mcp_lifecycle():
    request = build_initialize_request(7)

    assert request["jsonrpc"] == "2.0"
    assert request["id"] == 7
    assert request["method"] == "initialize"
    assert request["params"]["protocolVersion"] == PROTOCOL_VERSION
    assert request["params"]["capabilities"] == {}
    assert request["params"]["clientInfo"]["name"] == "codex-atlas-mcp-diagnostic-client"


def test_initialized_notification_and_list_messages():
    assert build_initialized_notification() == {
        "jsonrpc": "2.0",
        "method": "notifications/initialized",
    }
    assert build_tools_list_request(9) == {
        "jsonrpc": "2.0",
        "id": 9,
        "method": "tools/list",
        "params": {},
    }
    assert build_resources_list_request(10)["method"] == "resources/list"
    assert build_prompts_list_request(11)["method"] == "prompts/list"
    assert build_tools_call_request("safe_tool", {"limit": 1}, 12) == {
        "jsonrpc": "2.0",
        "id": 12,
        "method": "tools/call",
        "params": {"name": "safe_tool", "arguments": {"limit": 1}},
    }


def test_encode_stdio_message_is_newline_delimited_json():
    encoded = encode_stdio_message({"jsonrpc": "2.0", "id": 1, "method": "ping"})

    assert encoded.endswith("\n")
    assert encoded.count("\n") == 1
    assert '"method":"ping"' in encoded


def test_protocol_validation_lists_tools_with_fake_server(tmp_path):
    report, fake, captured = _run_fake(
        [_initialize_response('{"tools":{"listChanged":true}}'), _tools_response()],
        tmp_path,
    )

    assert report["classification"] == "MCP_PROTOCOL_VALIDATED"
    assert report["initialize"]["status"] == "PASS"
    assert report["initialized"]["status"] == "PASS"
    assert report["tools_list"]["status"] == "PASS"
    assert report["tools_list"]["tool_count"] == 1
    assert report["tools_list"]["tools"][0]["name"] == "mem_search"
    assert report["tools_list"]["tools"][0]["parameters"] == ["limit", "query"]
    assert report["resources_list"]["status"] == "NOT_SUPPORTED"
    assert report["prompts_list"]["status"] == "NOT_SUPPORTED"
    assert report["tool_call"]["call_status"] == "BLOCKED"
    assert "notifications/initialized" in fake.stdin.getvalue()
    assert captured["env"]["ENGRAM_DATA_DIR"] == str((tmp_path / "mcp").resolve())


def test_resources_list_supported(tmp_path):
    resources_response = (
        '{"jsonrpc":"2.0","id":3,"result":{"resources":[{"uri":"file:///a",'
        '"name":"alpha","description":"A","mimeType":"text/plain"}]}}\n'
    )
    report, _fake, _captured = _run_fake(
        [
            _initialize_response('{"tools":{},"resources":{"listChanged":true}}'),
            _tools_response(),
            resources_response,
        ],
        tmp_path,
    )

    assert report["resources_list"]["status"] == "PASS"
    assert report["resources_list"]["resource_count"] == 1
    assert report["resources_list"]["resources"][0]["uri"] == "file:///a"
    assert report["prompts_list"]["status"] == "NOT_SUPPORTED"


def test_resources_list_not_supported_by_capability_absence(tmp_path):
    report, fake, _captured = _run_fake(
        [_initialize_response('{"tools":{}}'), _tools_response()],
        tmp_path,
    )

    assert report["resources_list"]["status"] == "NOT_SUPPORTED"
    assert "resources/list" not in fake.stdin.getvalue()


def test_prompts_list_supported(tmp_path):
    prompts_response = (
        '{"jsonrpc":"2.0","id":4,"result":{"prompts":[{"name":"review",'
        '"description":"Review code","arguments":[{"name":"code","required":true}]}]}}\n'
    )
    report, _fake, _captured = _run_fake(
        [
            _initialize_response('{"tools":{},"prompts":{"listChanged":true}}'),
            _tools_response(),
            prompts_response,
        ],
        tmp_path,
    )

    assert report["prompts_list"]["status"] == "PASS"
    assert report["prompts_list"]["prompt_count"] == 1
    assert report["prompts_list"]["prompts"][0]["name"] == "review"
    assert report["resources_list"]["status"] == "NOT_SUPPORTED"


def test_prompts_list_not_supported_by_method_not_found(tmp_path):
    prompts_error = (
        '{"jsonrpc":"2.0","id":4,"error":{"code":-32601,'
        '"message":"Method not found"}}\n'
    )
    report, _fake, _captured = _run_fake(
        [
            _initialize_response('{"tools":{},"prompts":{"listChanged":true}}'),
            _tools_response(),
            prompts_error,
        ],
        tmp_path,
    )

    assert report["prompts_list"]["status"] == "NOT_SUPPORTED"
    assert report["classification"] == "MCP_PROTOCOL_VALIDATED"


def test_jsonrpc_error_for_optional_list_is_controlled_fail(tmp_path):
    resources_error = (
        '{"jsonrpc":"2.0","id":3,"error":{"code":-32603,'
        '"message":"Internal error"}}\n'
    )
    report, _fake, _captured = _run_fake(
        [
            _initialize_response('{"tools":{},"resources":{"listChanged":true}}'),
            _tools_response(),
            resources_error,
        ],
        tmp_path,
    )

    assert report["resources_list"]["status"] == "FAIL"
    assert "resources_list_error_response" in report["errors"]
    assert report["classification"] == "MCP_PROTOCOL_PARTIAL"


def test_read_only_allowlisted_tool_call_executes(tmp_path):
    schema = {"type": "object", "properties": {"check": {"type": "string"}, "project": {"type": "string"}}, "required": []}
    tool_call_response = '{"jsonrpc":"2.0","id":5,"result":{"status":"ok","total":4}}\n'
    report, fake, _captured = _run_fake(
        [
            _initialize_response('{"tools":{}}'),
            _tools_response("mem_doctor", schema, "Run read-only operational diagnostics."),
            tool_call_response,
        ],
        tmp_path,
        enable_read_only_tool_call=True,
        read_only_tool_name="mem_doctor",
        read_only_tool_arguments={},
        read_only_tool_policy=_policy(),
    )

    assert report["tool_call"]["tool_call_supported"] is True
    assert report["tool_call"]["policy_status"] == "ALLOWED"
    assert report["tool_call"]["call_status"] == "PASS"
    assert report["tool_call"]["side_effects_expected"] is False
    assert '"status": "ok"' in report["tool_call"]["result_excerpt"]
    assert '"method":"tools/call"' in fake.stdin.getvalue()


def test_tool_not_allowlisted_is_blocked(tmp_path):
    schema = {"type": "object", "properties": {}, "required": []}
    report, fake, _captured = _run_fake(
        [_initialize_response('{"tools":{}}'), _tools_response("mem_save", schema, "Save memory")],
        tmp_path,
        enable_read_only_tool_call=True,
        read_only_tool_name="mem_save",
        read_only_tool_arguments={},
        read_only_tool_policy=_policy(),
    )

    assert report["tool_call"]["policy_status"] == "DENIED"
    assert report["tool_call"]["call_status"] == "BLOCKED"
    assert "tool_not_allowlisted" in report["tool_call"]["errors"]
    assert "tools/call" not in fake.stdin.getvalue()


def test_unknown_policy_blocks_tool_call(tmp_path):
    schema = {"type": "object", "properties": {}, "required": []}
    report, fake, _captured = _run_fake(
        [_initialize_response('{"tools":{}}'), _tools_response("mem_doctor", schema, "Read-only")],
        tmp_path,
        enable_read_only_tool_call=True,
        read_only_tool_name="mem_doctor",
        read_only_tool_arguments={},
        read_only_tool_policy=None,
    )

    assert report["tool_call"]["policy_status"] == "UNKNOWN"
    assert report["tool_call"]["call_status"] == "BLOCKED"
    assert "policy_missing" in report["tool_call"]["errors"]
    assert "tools/call" not in fake.stdin.getvalue()


def test_unexpected_schema_blocks_tool_call(tmp_path):
    schema = {"type": "array", "items": {"type": "string"}}
    report, fake, _captured = _run_fake(
        [_initialize_response('{"tools":{}}'), _tools_response("mem_doctor", schema, "Read-only")],
        tmp_path,
        enable_read_only_tool_call=True,
        read_only_tool_name="mem_doctor",
        read_only_tool_arguments={},
        read_only_tool_policy=_policy(),
    )

    assert report["tool_call"]["policy_status"] == "DENIED"
    assert report["tool_call"]["call_status"] == "BLOCKED"
    assert "schema_not_understood" in report["tool_call"]["errors"]
    assert "tools/call" not in fake.stdin.getvalue()


def test_tools_call_jsonrpc_error_is_controlled(tmp_path):
    schema = {"type": "object", "properties": {}, "required": []}
    tool_call_error = '{"jsonrpc":"2.0","id":5,"error":{"code":-32603,"message":"boom"}}\n'
    report, _fake, _captured = _run_fake(
        [
            _initialize_response('{"tools":{}}'),
            _tools_response("mem_doctor", schema, "Read-only"),
            tool_call_error,
        ],
        tmp_path,
        enable_read_only_tool_call=True,
        read_only_tool_name="mem_doctor",
        read_only_tool_arguments={},
        read_only_tool_policy=_policy(),
    )

    assert report["tool_call"]["policy_status"] == "ALLOWED"
    assert report["tool_call"]["call_status"] == "FAIL"
    assert "tools_call_error_response" in report["tool_call"]["errors"]
    assert report["classification"] == "MCP_PROTOCOL_PARTIAL"


def test_validate_protocol_report_rejects_missing_fields():
    report = {
        "client_name": "mcp_stdio_diagnostic_client",
        "version": "v1",
        "generated_at": "2026-06-18T00:00:00+00:00",
        "protocol_version_requested": PROTOCOL_VERSION,
        "protocol_version": PROTOCOL_VERSION,
        "server_info": {},
        "capabilities": {},
        "command": ["fake-mcp"],
        "initialize": {},
        "initialized": {},
        "tools_list": {},
        "resources_list": {},
        "prompts_list": {},
        "tool_call": {},
        "summary": {},
        "shutdown": {},
        "classification": "MCP_PROTOCOL_VALIDATED",
    }

    assert validate_mcp_protocol_report(report)["valid"] is True
    del report["tools_list"]
    validation = validate_mcp_protocol_report(report)
    assert validation["valid"] is False
    assert "missing:tools_list" in validation["findings"]
