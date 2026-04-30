import json
import shutil
import uuid
from pathlib import Path

from tools.atlas_surface_audit import run_surface_audit


ROOT = Path(r"C:\Proyectos\Codex-Atlas")
TMP_ROOT = ROOT / "tests" / "_tmp_surface_audit"


def _write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def test_current_readme_surface_is_coherent():
    result = run_surface_audit(ROOT)

    assert result["status"] == "ok"
    assert result["warnings"] == []
    assert result["summary"]["missing_skill_mentions"] == []
    assert result["summary"]["missing_workflow_mentions"] == []
    assert result["summary"]["missing_command_mentions"] == []


def test_surface_audit_detects_missing_skill_mentions():
    root = TMP_ROOT / f"surface_audit_{uuid.uuid4().hex}"
    root.mkdir(parents=True, exist_ok=True)
    try:
        _write(
            root / "commands" / "atomic_command_registry.json",
            json.dumps(
                {
                    "registry_version": "0.1",
                    "status": "bootstrap",
                    "scope": "atlas-governance",
                    "commands": [{"id": "audit-repo"}, {"id": "surface-audit"}],
                },
                indent=2,
            )
            + "\n",
        )
        _write(root / "README.md", "# Atlas\n\nThis README only mentions repo-audit.\n")
        _write(root / "skills" / "repo-audit" / "skill.json", "{}\n")
        _write(root / "skills" / "visual-direction-checkpoint" / "skill.json", "{}\n")
        _write(root / "workflows" / "audit_project.md", "# audit_project\n")

        result = run_surface_audit(root)

        assert result["status"] == "warning"
        warning_codes = {item["code"] for item in result["warnings"]}
        assert "readme_missing_skill_mentions" in warning_codes
        assert "visual-direction-checkpoint" in result["summary"]["missing_skill_mentions"]
    finally:
        shutil.rmtree(root, ignore_errors=True)
