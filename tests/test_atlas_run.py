import json
import shutil
from pathlib import Path

from tests._support_paths import TEMP_ROOT
from tools.atlas_project_bootstrap import bootstrap_project
from tools.atlas_run import run_atlas


def _fresh_project_dir(name: str) -> Path:
    root = TEMP_ROOT / name
    if root.exists():
        shutil.rmtree(root, ignore_errors=True)
    root.mkdir(parents=True, exist_ok=True)
    return root


def test_atlas_run_blocks_when_git_root_is_missing():
    project = _fresh_project_dir("atlas_run_blocked")
    (project / "README.md").write_text("# Demo\n\nTest project.\n", encoding="utf-8")
    (project / "package.json").write_text(json.dumps({"dependencies": {"next": "^14.0.0"}}), encoding="utf-8")
    bootstrap_project(project)

    result = run_atlas(
        project_path=project,
        task="mejorar empty states del marketplace",
        mode="plan",
        dry_run=True,
        require_dispatcher=True,
    )

    assert result["status"] == "blocked"
    assert result["operating_mode"] != "ATLAS completo"
    assert result["dispatcher_invoked"] is False
    assert result["codex_executor_ready"] is False
    assert result["envelope"]["bloqueadores"][0]["code"] == "missing_git_root"


def test_atlas_run_reaches_full_mode_when_git_and_governance_are_present(monkeypatch):
    project = _fresh_project_dir("atlas_run_ready")
    (project / "README.md").write_text("# Demo\n\nTest project.\n", encoding="utf-8")
    (project / "package.json").write_text(json.dumps({"dependencies": {"next": "^14.0.0"}}), encoding="utf-8")
    (project / ".git").mkdir()
    bootstrap_project(project)
    sprint = project / "SPRINT_STATUS.md"
    sprint.write_text(
        "# SPRINT_STATUS - Demo\n\n## Governance\n- Atlas root: `C:\\Proyectos\\Codex-Atlas`\n\n## Current Sprint\n- Status: `product-qa-demo-readiness`\n\n## In Scope Now\n- Product QA\n- Demo Readiness\n",
        encoding="utf-8",
    )

    def _fake_executor(**_: object) -> dict[str, object]:
        return {
            "status": "ready",
            "codex_executor_ready": True,
            "invoked": False,
            "mode": "plan",
            "dry_run": True,
            "capabilities": {
                "detected": True,
                "supports_cd": True,
                "supports_sandbox": True,
                "supports_output_last_message": True,
                "supports_ask_for_approval": False,
            },
            "compatibility_warnings": ["missing_exec_flag:ask_for_approval"],
            "command_preview": ["codex", "exec", "--cd", str(project), "--sandbox", "workspace-write", "prompt"],
            "reason": "executor_ready_but_not_invoked",
        }

    monkeypatch.setattr("tools.atlas_run.execute_via_atlas_codex", _fake_executor)

    result = run_atlas(
        project_path=project,
        task="mejorar empty states del marketplace",
        mode="plan",
        dry_run=True,
        require_dispatcher=True,
    )

    assert result["status"] == "ready"
    assert result["operating_mode"] == "ATLAS completo"
    assert result["dispatcher_invoked"] is True
    assert result["registry_checked"] is True
    assert result["phase_gate_checked"] is True
    assert result["agent_selected"] is True
    assert result["codex_executor_ready"] is True
    assert result["executor"]["status"] == "ready"
    assert "--ask-for-approval" not in result["executor"]["command_preview"]
    assert result["envelope"]["status"] == "ready"


def test_atlas_run_blocks_non_demo_architecture_task_during_product_qa_sprint(monkeypatch):
    project = _fresh_project_dir("atlas_run_architecture_blocked")
    (project / "README.md").write_text("# Demo\n\nTest project.\n", encoding="utf-8")
    (project / "package.json").write_text(json.dumps({"dependencies": {"next": "^14.0.0"}}), encoding="utf-8")
    (project / ".git").mkdir()
    bootstrap_project(project)
    (project / "SPRINT_STATUS.md").write_text(
        "# SPRINT_STATUS - Demo\n\n## Governance\n- Atlas root: `C:\\Proyectos\\Codex-Atlas`\n\n## Current Sprint\n- Status: `product-qa-demo-readiness`\n\n## In Scope Now\n- Product QA\n- Demo Readiness\n",
        encoding="utf-8",
    )

    def _fake_executor(**_: object) -> dict[str, object]:
        return {
            "status": "ready",
            "codex_executor_ready": True,
            "invoked": False,
            "mode": "plan",
            "dry_run": True,
            "capabilities": {
                "detected": True,
                "supports_cd": True,
                "supports_sandbox": True,
                "supports_output_last_message": True,
                "supports_ask_for_approval": False,
            },
            "compatibility_warnings": [],
            "command_preview": ["codex", "exec", "--cd", str(project), "--sandbox", "workspace-write", "prompt"],
            "reason": "executor_ready_but_not_invoked",
        }

    monkeypatch.setattr("tools.atlas_run.execute_via_atlas_codex", _fake_executor)

    result = run_atlas(
        project_path=project,
        task="document state machine architecture",
        mode="plan",
        dry_run=True,
        require_dispatcher=True,
    )

    assert result["status"] == "ready"
    assert result["functional_work_allowed"] is False
    assert result["functional_work_reason"] == "Current sprint only allows Product QA / Demo Readiness work."
