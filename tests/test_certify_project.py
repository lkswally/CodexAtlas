import os
import json
import shutil
import uuid
from pathlib import Path

os.environ["ATLAS_DISABLE_EVENT_LOGS"] = "1"

from tools.atlas_dispatcher import dispatch


ROOT = Path(r"C:\Proyectos\Codex-Atlas")
TMP_ROOT = ROOT / "tests" / "_tmp_certify_cases"


def _write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def _bootstrap_like_project(project_root: Path, project_profile: str, extra_dirs: list[str], status: str = "bootstrapped") -> None:
    metadata = {
        "schema_version": "1.0",
        "project_name": project_root.name,
        "project_type": "atlas-derived-project",
        "project_profile": project_profile,
        "bootstrap_template": project_profile,
        "generated_from_skill": "project-bootstrap",
        "derived_from": "Codex-Atlas",
        "atlas_root": str(ROOT),
        "audit_paths": ["docs", "memory", "workflows", "policies", "tools"] + extra_dirs,
        "status": status,
    }
    _write(project_root / ".atlas-project.json", json.dumps(metadata, indent=2) + "\n")
    _write(project_root / "README.md", f"# {project_root.name}\n\nBootstrap README.\n")
    _write(project_root / "AGENTS.md", f"# AGENTS for {project_root.name}\n\nBootstrap AGENTS.\n")
    for rel in ["docs", "memory", "workflows", "policies", "tools", *extra_dirs]:
        (project_root / rel).mkdir(parents=True, exist_ok=True)


def _make_case_dir(name: str) -> Path:
    case_root = TMP_ROOT / f"{name}_{uuid.uuid4().hex}"
    case_root.mkdir(parents=True, exist_ok=True)
    return case_root


def test_certify_project_passes_clean_backend_service():
    case_root = _make_case_dir("clean_backend")
    try:
        project_root = case_root / "DerivedBackend"
        _bootstrap_like_project(project_root, "backend_service", ["api", "services", "tests"], status="audited")

        result = dispatch("certify-project", root=ROOT, project=project_root)

        assert result.ok is True
        assert result.exit_code == 0
        assert result.output["result"]["summary"]["certification_status"] == "passed"
        assert result.output["result"]["summary"]["score"] == 100
        assert result.output["result"]["blockers"] == []
        assert result.output["result"]["warnings"] == []
    finally:
        shutil.rmtree(case_root, ignore_errors=True)


def test_certify_project_reports_blockers_for_atlas_and_claude_residue():
    case_root = _make_case_dir("contaminated")
    try:
        project_root = case_root / "ContaminatedDerived"
        _bootstrap_like_project(project_root, "ai_agent_system", ["agents", "skills", "evaluations", "prompts"], status="audited")
        _write(project_root / "CLAUDE.md", "# legacy claude instructions\n")
        _write(project_root / "tools" / "atlas_dispatcher.py", "print('legacy shim')\n")

        result = dispatch("certify-project", root=ROOT, project=project_root)
        blockers = result.output["result"]["blockers"]
        blocker_codes = {item["code"] for item in blockers}

        assert result.ok is True
        assert result.output["result"]["summary"]["certification_status"] == "failed"
        assert "claude_artifact" in blocker_codes
        assert "embedded_atlas_tool" in blocker_codes
        assert result.output["governance"]["before"]["ok"] is False
        assert result.output["governance"]["after"]["ok"] is False
    finally:
        shutil.rmtree(case_root, ignore_errors=True)


def test_certify_project_requires_project_path():
    result = dispatch("certify-project", root=ROOT)
    assert result.ok is False
    assert result.exit_code == 2
    assert result.output["error"] == "project_argument_required"
