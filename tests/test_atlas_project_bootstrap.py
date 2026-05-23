import json
import shutil
from pathlib import Path
from unittest.mock import patch

from tests._support_paths import TEMP_ROOT
from tools.atlas_context_audit import audit_project_context
from tools.atlas_project_bootstrap import _read_text, bootstrap_project, infer_project_profile


def _fresh_project_dir(name: str) -> Path:
    root = TEMP_ROOT / name
    if root.exists():
        shutil.rmtree(root, ignore_errors=True)
    root.mkdir(parents=True, exist_ok=True)
    return root


def test_infer_project_profile_detects_frontend_app_from_next_package():
    project = _fresh_project_dir("atlas_bootstrap_profile_frontend")
    (project / "package.json").write_text(
        json.dumps({"dependencies": {"next": "^14.0.0", "react": "^18.0.0"}}),
        encoding="utf-8",
    )
    assert infer_project_profile(project) == "frontend_app"


def test_bootstrap_project_creates_governance_files_without_overwriting_existing():
    project = _fresh_project_dir("atlas_bootstrap_governance_files")
    (project / "README.md").write_text("# Demo\n\nAtlas bootstrap target.\n", encoding="utf-8")
    (project / "package.json").write_text(json.dumps({"dependencies": {"next": "^14.0.0"}}), encoding="utf-8")

    first = bootstrap_project(project)
    second = bootstrap_project(project)

    assert sorted(first["created_files"]) == [".atlas-project.json", "AGENTS.md", "SPRINT_STATUS.md"]
    assert sorted(second["skipped_files"]) == [".atlas-project.json", "AGENTS.md", "SPRINT_STATUS.md"]
    assert "git init" in first["suggested_git_init_command"]
    assert (project / "AGENTS.md").exists()
    assert (project / ".atlas-project.json").exists()
    assert (project / "SPRINT_STATUS.md").exists()
    for rel in ("docs", "memory", "workflows", "policies", "tools"):
        assert (project / rel).is_dir()
    payload = json.loads((project / ".atlas-project.json").read_text(encoding="utf-8"))
    assert payload["atlas_root"] == str(Path(__file__).resolve().parent.parent)
    assert payload["project_profile"] == "frontend_app"


def test_context_audit_blocks_functional_work_when_git_or_governance_is_missing():
    project = _fresh_project_dir("atlas_bootstrap_audit_blocked")
    (project / "README.md").write_text("# Demo\n\nNo governance yet.\n", encoding="utf-8")

    result = audit_project_context(project)

    assert result["operating_mode"] == "Codex directo bloqueado"
    assert result["functional_work_allowed"] is False
    assert "git_root" in result["missing_governance"]
    assert ".atlas-project.json" in result["missing_governance"]


def test_context_audit_moves_project_to_light_governance_after_bootstrap():
    project = _fresh_project_dir("atlas_bootstrap_audit_light")
    (project / "README.md").write_text("# Demo\n\nBootstrap target.\n", encoding="utf-8")
    (project / "package.json").write_text(json.dumps({"dependencies": {"next": "^14.0.0"}}), encoding="utf-8")

    bootstrap_project(project)
    result = audit_project_context(project)

    assert result["operating_mode"] == "ATLAS gobernanza ligera"
    assert result["functional_work_allowed"] is False
    assert result["atlas_linked"] is True
    assert result["has_local_agents"] is True
    assert result["has_status_file"] is True


def test_bootstrap_project_uses_full_governance_mode_when_git_exists():
    project = _fresh_project_dir("atlas_bootstrap_full_mode")
    (project / "README.md").write_text("# Demo\n\nBootstrap target.\n", encoding="utf-8")
    (project / "package.json").write_text(json.dumps({"dependencies": {"next": "^14.0.0"}}), encoding="utf-8")
    (project / ".git").mkdir()

    bootstrap_project(project, overwrite=True)

    payload = json.loads((project / ".atlas-project.json").read_text(encoding="utf-8"))
    agents_text = (project / "AGENTS.md").read_text(encoding="utf-8")
    sprint_text = (project / "SPRINT_STATUS.md").read_text(encoding="utf-8")

    assert payload["governance_mode"] == "atlas_completo"
    assert "ATLAS completo" in agents_text
    assert "ATLAS completo" in sprint_text


def test_bootstrap_project_rejects_unknown_global_template_placeholders():
    project = _fresh_project_dir("atlas_bootstrap_invalid_template")
    (project / "README.md").write_text("# Demo\n\nBootstrap target.\n", encoding="utf-8")

    original_read_text = _read_text

    def fake_read_text(path: Path):
        if path.name == "AGENTS.md.template" and path.parent.name == "project":
            return "# {project_name}\n\nUnsupported {project_profile}\n"
        return original_read_text(path)

    with patch("tools.atlas_project_bootstrap._read_text", side_effect=fake_read_text):
        try:
            bootstrap_project(project)
        except ValueError as exc:
            message = str(exc)
        else:
            raise AssertionError("bootstrap_project should reject invalid global template placeholders")

    assert "atlas_project_bootstrap:invalid_template_placeholder:" in message
    assert "template=AGENTS" in message
    assert "placeholder={project_profile}" in message
