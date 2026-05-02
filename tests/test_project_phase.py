import json
import os
import shutil
import uuid
from pathlib import Path

os.environ["ATLAS_DISABLE_EVENT_LOGS"] = "1"

from tools.atlas_dispatcher import dispatch
from tools.project_phase_resolver import build_project_phase_report


ROOT = Path(r"C:\Proyectos\Codex-Atlas")
TMP_ROOT = ROOT / "tests" / "_tmp_project_phase"


def _write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def _bootstrap_like_project(project_root: Path, status: str = "bootstrapped", extras: list[str] | None = None) -> None:
    extras = extras or []
    metadata = {
        "schema_version": "1.0",
        "project_name": project_root.name,
        "project_type": "atlas-derived-project",
        "project_profile": "internal_tool",
        "bootstrap_template": "internal_tool",
        "generated_from_skill": "project-bootstrap",
        "derived_from": "Codex-Atlas",
        "atlas_root": str(ROOT),
        "audit_paths": ["docs", "memory", "workflows", "policies", "tools", *extras],
        "status": status,
    }
    _write(project_root / ".atlas-project.json", json.dumps(metadata, indent=2) + "\n")
    _write(project_root / "README.md", "# Derived\n")
    _write(project_root / "AGENTS.md", "# AGENTS\n")
    for rel in ["docs", "memory", "workflows", "policies", "tools", *extras]:
        (project_root / rel).mkdir(parents=True, exist_ok=True)


def _make_case_dir(name: str) -> Path:
    case_root = TMP_ROOT / f"{name}_{uuid.uuid4().hex}"
    case_root.mkdir(parents=True, exist_ok=True)
    return case_root


def test_project_phase_report_detects_recent_bootstrap_project():
    case_root = _make_case_dir("bootstrap")
    try:
        project_root = case_root / "BootstrapProject"
        _bootstrap_like_project(project_root, status="bootstrapped")

        result = build_project_phase_report(ROOT, project_root)

        assert result["status"] == "ok"
        assert result["current_phase"] == "bootstrap"
        assert result["confidence"] in {"high", "medium"}
        assert result["allowed_commands"] == ["audit-repo"]
        assert result["recommended_next_steps"]
        assert result["common_mistakes"]
        assert "certify-project" in result["blocked_actions"]
    finally:
        shutil.rmtree(case_root, ignore_errors=True)


def test_project_phase_report_detects_audited_project():
    case_root = _make_case_dir("audited")
    try:
        project_root = case_root / "AuditedProject"
        _bootstrap_like_project(project_root, status="audited", extras=["site"])
        _write(project_root / "index.html", "<!doctype html><title>Atlas</title>\n")

        result = build_project_phase_report(ROOT, project_root)

        assert result["current_phase"] == "audit"
        assert result["allowed_commands"] == ["certify-project"]
        assert "certify-project" not in result["blocked_actions"]
        assert result["next_valid_phases"]
    finally:
        shutil.rmtree(case_root, ignore_errors=True)


def test_project_phase_report_detects_certified_project():
    case_root = _make_case_dir("certified")
    try:
        project_root = case_root / "CertifiedProject"
        _bootstrap_like_project(project_root, status="certified", extras=["site"])
        _write(project_root / "index.html", "<!doctype html><title>Atlas</title>\n")

        result = build_project_phase_report(ROOT, project_root)

        assert result["current_phase"] == "certified"
        assert result["confidence"] == "high"
    finally:
        shutil.rmtree(case_root, ignore_errors=True)


def test_dispatcher_blocks_invalid_phase_actions():
    case_root = _make_case_dir("phase_block")
    try:
        project_root = case_root / "BlockedProject"
        _bootstrap_like_project(project_root, status="bootstrapped")

        result = dispatch("certify-project", root=ROOT, project=project_root)

        assert result.ok is False
        assert result.exit_code == 2
        assert result.output["error"] == "phase_blocked"
        assert "bootstrap" in result.output["message"]
        assert result.output["suggested_command"] == "audit-repo"
        assert result.output["phase_report"]["current_phase"] == "bootstrap"
    finally:
        shutil.rmtree(case_root, ignore_errors=True)
