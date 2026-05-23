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


def test_atlas_run_reaches_full_mode_when_git_and_governance_are_present():
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
    assert result["envelope"]["status"] == "ready"
