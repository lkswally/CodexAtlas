import os
import shutil
import uuid
from pathlib import Path

os.environ["ATLAS_DISABLE_EVENT_LOGS"] = "1"

from tools.atlas_dispatcher import _audit_repo_stub, dispatch


ROOT = Path(r"C:\Proyectos\Codex-Atlas")
TMP_ROOT = ROOT / "tests" / "_tmp_audit_repo"


def _make_case_dir(name: str) -> Path:
    case_root = TMP_ROOT / f"{name}_{uuid.uuid4().hex}"
    case_root.mkdir(parents=True, exist_ok=True)
    return case_root


def test_audit_repo_returns_useful_structure_report_for_atlas_root():
    result = dispatch("audit-repo", root=ROOT)

    assert result.ok is True
    report = result.output["result"]
    assert report["status"] == "ok"
    assert report["summary"]["target_root"] == str(ROOT)
    assert "AGENTS.md" in report["summary"]["present_allowed_paths"]
    assert "README.md" in report["summary"]["top_level"]["files"]
    assert isinstance(report["summary"]["top_level"]["directories"], list)
    assert isinstance(report["summary"]["top_level"]["files"], list)
    assert isinstance(report["summary"]["relevant_paths"], list)
    assert isinstance(report["findings"], list)
    assert isinstance(report["risks"], list)
    assert report["recommendations"]
    assert report["recommended_next_steps"]


def test_audit_repo_reports_missing_governance_files_from_evidence():
    case_root = _make_case_dir("missing_governance")
    try:
        project = case_root / "SparseAtlasLikeProject"
        project.mkdir()
        (project / "README.md").write_text("# Sparse\n", encoding="utf-8")

        report = _audit_repo_stub(
            project,
            {"allowed_paths": ["README.md", "AGENTS.md", "docs"]},
            project_metadata=None,
        )

        assert report["status"] == "partial"
        assert "AGENTS.md" in report["summary"]["missing_allowed_paths"]
        assert "AGENTS.md" in report["summary"]["missing_governance_files"]
        finding_codes = {item["code"] for item in report["findings"]}
        assert "missing_allowed_path" in finding_codes
        assert "missing_governance_file" in finding_codes
        assert report["risks"]
        assert "Restore missing governance files before certification or handoff." in report["recommendations"]
    finally:
        shutil.rmtree(case_root, ignore_errors=True)


def test_audit_repo_detects_derived_project_residue():
    case_root = _make_case_dir("derived_residue")
    try:
        project = case_root / "DerivedProject"
        project.mkdir()
        for rel in ["docs", "memory", "workflows", "policies", "tools"]:
            (project / rel).mkdir()
        (project / ".atlas-project.json").write_text("{}", encoding="utf-8")
        (project / "README.md").write_text("# Derived\n", encoding="utf-8")
        (project / "AGENTS.md").write_text("# Agents\n", encoding="utf-8")
        (project / "tools" / "atlas_dispatcher.py").write_text("print('residue')\n", encoding="utf-8")

        metadata = {
            "project_name": "DerivedProject",
            "project_type": "atlas-derived-project",
            "project_profile": "internal_tool",
            "derived_from": "Codex-Atlas",
            "status": "bootstrapped",
            "audit_paths": ["docs", "memory", "workflows", "policies", "tools"],
        }
        report = _audit_repo_stub(project, {"allowed_paths": []}, project_metadata=metadata)

        assert report["status"] == "partial"
        finding_codes = {item["code"] for item in report["findings"]}
        assert "forbidden_or_foreign_artifact" in finding_codes
        assert report["summary"]["metadata"]["project_profile"] == "internal_tool"
        assert any("Atlas/Claude-specific artifact" in item["message"] for item in report["findings"])
    finally:
        shutil.rmtree(case_root, ignore_errors=True)
