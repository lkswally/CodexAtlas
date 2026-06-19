import subprocess

from tools.engram_mcp_harness import (
    build_engram_mcp_command,
    run_engram_mcp_harness,
    validate_engram_mcp_harness_report,
)


class FakeProcess:
    def __init__(self, *, startup_exit=None, final_returncode=0):
        self._startup_exit = startup_exit
        self.returncode = startup_exit
        self.final_returncode = final_returncode
        self.terminated = False
        self.killed = False

    def poll(self):
        return None if self.returncode is None else self.returncode

    def terminate(self):
        self.terminated = True

    def kill(self):
        self.killed = True
        self.returncode = -9

    def communicate(self, timeout=None):
        if self.returncode is None:
            self.returncode = self.final_returncode
        return "", ""


def test_build_command_uses_official_mcp_agent_profile():
    assert build_engram_mcp_command(project="atlas") == [
        "engram",
        "mcp",
        "--tools=agent",
        "--project",
        "atlas",
    ]


def test_harness_marks_partial_mcp_available_with_sandbox_env(tmp_path, monkeypatch):
    monkeypatch.setattr("time.sleep", lambda _seconds: None)
    captured = {}
    fake = FakeProcess(startup_exit=None, final_returncode=0)

    def popen(command, **kwargs):
        captured["command"] = command
        captured["env"] = kwargs["env"]
        return fake

    report = run_engram_mcp_harness(
        sandbox_dir=tmp_path / "engram_sandbox",
        report_path=None,
        project="codex-atlas-v4-mcp-sandbox",
        startup_seconds=0,
        popen_factory=popen,
    )

    assert report["classification"] == "PARTIAL_MCP_AVAILABLE"
    assert report["startup"]["status"] == "PASS"
    assert report["shutdown"]["status"] == "PASS"
    assert fake.terminated is True
    assert captured["command"] == [
        "engram",
        "mcp",
        "--tools=agent",
        "--project",
        "codex-atlas-v4-mcp-sandbox",
    ]
    assert captured["env"]["ENGRAM_DATA_DIR"] == str((tmp_path / "engram_sandbox").resolve())
    assert captured["env"]["ENGRAM_PROJECT"] == "codex-atlas-v4-mcp-sandbox"
    assert report["handshake_attempted"] is False
    assert report["handshake_status"] == "NOT_ATTEMPTED"


def test_harness_reports_startup_failure(tmp_path, monkeypatch):
    monkeypatch.setattr("time.sleep", lambda _seconds: None)

    report = run_engram_mcp_harness(
        sandbox_dir=tmp_path / "engram_sandbox",
        report_path=None,
        startup_seconds=0,
        popen_factory=lambda *_args, **_kwargs: FakeProcess(startup_exit=2),
    )

    assert report["classification"] == "BROKEN_SANDBOX"
    assert report["startup"]["status"] == "FAIL"
    assert "process_exited_during_startup:2" in report["errors"]


def test_harness_kills_on_shutdown_timeout(tmp_path, monkeypatch):
    monkeypatch.setattr("time.sleep", lambda _seconds: None)

    class TimeoutProcess(FakeProcess):
        def communicate(self, timeout=None):
            if not self.killed:
                raise subprocess.TimeoutExpired(cmd="engram", timeout=timeout)
            return "", ""

    process = TimeoutProcess(startup_exit=None)
    report = run_engram_mcp_harness(
        sandbox_dir=tmp_path / "engram_sandbox",
        report_path=None,
        startup_seconds=0,
        shutdown_timeout_seconds=0,
        popen_factory=lambda *_args, **_kwargs: process,
    )

    assert process.killed is True
    assert report["classification"] == "PARTIAL_MCP_AVAILABLE"
    assert report["shutdown"]["status"] == "TIMEOUT_KILLED"
    assert "shutdown_timeout" in report["errors"]


def test_validate_report_rejects_missing_fields(tmp_path, monkeypatch):
    monkeypatch.setattr("time.sleep", lambda _seconds: None)
    report = run_engram_mcp_harness(
        sandbox_dir=tmp_path / "engram_sandbox",
        report_path=None,
        startup_seconds=0,
        popen_factory=lambda *_args, **_kwargs: FakeProcess(startup_exit=None),
    )

    assert validate_engram_mcp_harness_report(report)["valid"] is True
    del report["command"]
    validation = validate_engram_mcp_harness_report(report)
    assert validation["valid"] is False
    assert "missing:command" in validation["findings"]
