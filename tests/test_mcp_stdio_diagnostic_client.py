import io

from tools.mcp_stdio_diagnostic_client import (
    PROTOCOL_VERSION,
    build_initialize_request,
    build_initialized_notification,
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


def test_build_initialize_request_matches_mcp_lifecycle():
    request = build_initialize_request(7)

    assert request["jsonrpc"] == "2.0"
    assert request["id"] == 7
    assert request["method"] == "initialize"
    assert request["params"]["protocolVersion"] == PROTOCOL_VERSION
    assert request["params"]["capabilities"] == {}
    assert request["params"]["clientInfo"]["name"] == "codex-atlas-mcp-diagnostic-client"


def test_initialized_notification_and_tools_list_messages():
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


def test_encode_stdio_message_is_newline_delimited_json():
    encoded = encode_stdio_message({"jsonrpc": "2.0", "id": 1, "method": "ping"})

    assert encoded.endswith("\n")
    assert encoded.count("\n") == 1
    assert '"method":"ping"' in encoded


def test_protocol_validation_lists_tools_with_fake_server(tmp_path):
    initialize_response = (
        '{"jsonrpc":"2.0","id":1,"result":{"protocolVersion":"2025-06-18",'
        '"capabilities":{"tools":{"listChanged":true}},'
        '"serverInfo":{"name":"fake","version":"1"}}}\n'
    )
    tools_response = (
        '{"jsonrpc":"2.0","id":2,"result":{"tools":[{"name":"mem_search",'
        '"description":"Search memory","inputSchema":{"type":"object",'
        '"properties":{"query":{"type":"string"},"limit":{"type":"integer"}},'
        '"required":["query"]}}]}}\n'
    )
    fake = FakeProcess([initialize_response, tools_response])
    captured = {}

    def popen(command, **kwargs):
        captured["command"] = command
        captured["env"] = kwargs["env"]
        return fake

    report = run_mcp_protocol_validation(
        command=["fake-mcp"],
        sandbox_dir=tmp_path / "mcp",
        report_path=None,
        popen_factory=popen,
    )

    assert report["classification"] == "MCP_PROTOCOL_VALIDATED"
    assert report["initialize"]["status"] == "PASS"
    assert report["initialized"]["status"] == "PASS"
    assert report["tools_list"]["status"] == "PASS"
    assert report["tools_list"]["tool_count"] == 1
    assert report["tools_list"]["tools"][0]["name"] == "mem_search"
    assert report["tools_list"]["tools"][0]["parameters"] == ["limit", "query"]
    assert "notifications/initialized" in fake.stdin.getvalue()
    assert captured["env"]["ENGRAM_DATA_DIR"] == str((tmp_path / "mcp").resolve())


def test_validate_protocol_report_rejects_missing_fields():
    report = {
        "client_name": "mcp_stdio_diagnostic_client",
        "version": "v1",
        "generated_at": "2026-06-18T00:00:00+00:00",
        "protocol_version_requested": PROTOCOL_VERSION,
        "command": ["fake-mcp"],
        "initialize": {},
        "initialized": {},
        "tools_list": {},
        "shutdown": {},
        "classification": "MCP_PROTOCOL_VALIDATED",
    }

    assert validate_mcp_protocol_report(report)["valid"] is True
    del report["tools_list"]
    validation = validate_mcp_protocol_report(report)
    assert validation["valid"] is False
    assert "missing:tools_list" in validation["findings"]
