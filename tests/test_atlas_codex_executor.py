import shutil
from pathlib import Path

from tests._support_paths import TEMP_ROOT
from tools.atlas_codex_executor import codex_executor_readiness, execute_via_atlas_codex


class _CompletedProcess:
    def __init__(self, *, returncode: int = 0, stdout: str = "", stderr: str = "") -> None:
        self.returncode = returncode
        self.stdout = stdout
        self.stderr = stderr


def _fresh_temp_dir(name: str) -> Path:
    root = TEMP_ROOT / name
    if root.exists():
        shutil.rmtree(root, ignore_errors=True)
    root.mkdir(parents=True, exist_ok=True)
    return root


def test_codex_executor_readiness_detects_unsupported_ask_for_approval(monkeypatch):
    def fake_run(command, **kwargs):
        if command == ["codex", "--version"]:
            return _CompletedProcess(returncode=0, stdout="codex 1.0.0")
        if command == ["codex", "exec", "--help"]:
            return _CompletedProcess(
                returncode=0,
                stdout=(
                    "Usage: codex exec [OPTIONS] [PROMPT]\n"
                    "  -C, --cd <DIR>\n"
                    "  -s, --sandbox <SANDBOX_MODE>\n"
                    "  -o, --output-last-message <FILE>\n"
                ),
            )
        raise AssertionError(f"Unexpected command: {command}")

    monkeypatch.setattr("tools.atlas_codex_executor.subprocess.run", fake_run)

    readiness = codex_executor_readiness()

    assert readiness["status"] == "ready"
    assert readiness["codex_executor_ready"] is True
    assert readiness["capabilities"]["supports_cd"] is True
    assert readiness["capabilities"]["supports_sandbox"] is True
    assert readiness["capabilities"]["supports_output_last_message"] is True
    assert readiness["capabilities"]["supports_ask_for_approval"] is False


def test_execute_via_atlas_codex_dry_run_omits_unsupported_ask_for_approval(monkeypatch):
    def fake_run(command, **kwargs):
        if command == ["codex", "--version"]:
            return _CompletedProcess(returncode=0, stdout="codex 1.0.0")
        if command == ["codex", "exec", "--help"]:
            return _CompletedProcess(
                returncode=0,
                stdout=(
                    "Usage: codex exec [OPTIONS] [PROMPT]\n"
                    "  -C, --cd <DIR>\n"
                    "  -s, --sandbox <SANDBOX_MODE>\n"
                    "  -o, --output-last-message <FILE>\n"
                ),
            )
        raise AssertionError(f"Unexpected command: {command}")

    monkeypatch.setattr("tools.atlas_codex_executor.subprocess.run", fake_run)
    project_path = _fresh_temp_dir("atlas_codex_executor_dry_run")

    result = execute_via_atlas_codex(
        project_path=project_path,
        task="mejorar empty states",
        mode="plan",
        dry_run=True,
        workflow="frontend_qa",
        agent="implementer",
        skill="ui-audit",
        plan=["Confirm current phase", "Review empty states"],
    )

    assert result["status"] == "ready"
    assert result["codex_executor_ready"] is True
    assert "--ask-for-approval" not in result["command_preview"]
    assert "missing_exec_flag:ask_for_approval" in result["compatibility_warnings"]


def test_execute_via_atlas_codex_execute_uses_only_supported_flags(monkeypatch):
    seen = {}

    def fake_run(command, **kwargs):
        if command == ["codex", "--version"]:
            return _CompletedProcess(returncode=0, stdout="codex 1.0.0")
        if command == ["codex", "exec", "--help"]:
            return _CompletedProcess(
                returncode=0,
                stdout=(
                    "Usage: codex exec [OPTIONS] [PROMPT]\n"
                    "  -C, --cd <DIR>\n"
                    "  -s, --sandbox <SANDBOX_MODE>\n"
                    "  -o, --output-last-message <FILE>\n"
                ),
            )
        seen["command"] = command
        output_file = Path(command[command.index("--output-last-message") + 1])
        output_file.write_text("Executor completed", encoding="utf-8")
        return _CompletedProcess(returncode=0, stdout="ok")

    monkeypatch.setattr("tools.atlas_codex_executor.subprocess.run", fake_run)
    project_path = _fresh_temp_dir("atlas_codex_executor_execute")

    result = execute_via_atlas_codex(
        project_path=project_path,
        task="mejorar empty states",
        mode="execute",
        dry_run=False,
        workflow="frontend_qa",
        agent="implementer",
        skill="ui-audit",
        plan=["Confirm current phase", "Review empty states"],
    )

    assert result["status"] == "ok"
    assert result["invoked"] is True
    assert "--ask-for-approval" not in seen["command"]
    assert "--output-last-message" in seen["command"]
    assert result["last_message"] == "Executor completed"


def test_execute_via_atlas_codex_cleans_last_message_temp_file(monkeypatch):
    project_path = _fresh_temp_dir("atlas_codex_executor_temp_cleanup")
    temp_output = project_path / "atlas-last-message.txt"

    class _FakeNamedTemporaryFile:
        def __init__(self, path: Path) -> None:
            self.name = str(path)

        def __enter__(self):
            temp_output.write_text("", encoding="utf-8")
            return self

        def __exit__(self, exc_type, exc, tb) -> None:
            return None

    def fake_run(command, **kwargs):
        if command == ["codex", "--version"]:
            return _CompletedProcess(returncode=0, stdout="codex 1.0.0")
        if command == ["codex", "exec", "--help"]:
            return _CompletedProcess(
                returncode=0,
                stdout=(
                    "Usage: codex exec [OPTIONS] [PROMPT]\n"
                    "  -C, --cd <DIR>\n"
                    "  -s, --sandbox <SANDBOX_MODE>\n"
                    "  -o, --output-last-message <FILE>\n"
                ),
            )
        output_file = Path(command[command.index("--output-last-message") + 1])
        output_file.write_text("Executor completed", encoding="utf-8")
        return _CompletedProcess(returncode=0, stdout="ok")

    monkeypatch.setattr("tools.atlas_codex_executor.subprocess.run", fake_run)
    monkeypatch.setattr(
        "tools.atlas_codex_executor.tempfile.NamedTemporaryFile",
        lambda **kwargs: _FakeNamedTemporaryFile(temp_output),
    )

    result = execute_via_atlas_codex(
        project_path=project_path,
        task="mejorar empty states",
        mode="execute",
        dry_run=False,
        workflow="frontend_qa",
        agent="implementer",
        skill="ui-audit",
        plan=["Confirm current phase", "Review empty states"],
    )

    assert result["status"] == "ok"
    assert temp_output.exists() is False
