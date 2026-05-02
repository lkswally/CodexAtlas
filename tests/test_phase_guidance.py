import os
import json
import shutil
import uuid
from pathlib import Path

os.environ["ATLAS_DISABLE_EVENT_LOGS"] = "1"

from tools.atlas_dispatcher import dispatch
from tools.project_phase_resolver import build_project_phase_report
from tools.quality_gate_report import build_quality_gate_report


ROOT = Path(r"C:\Proyectos\Codex-Atlas")
WEB_ROOT = Path(r"C:\Proyectos\CodexAtlas-Web")
TMP_ROOT = ROOT / "tests" / "_tmp_phase_guidance"


def _write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def _bootstrap_like_project(project_root: Path, status: str = "bootstrapped") -> None:
    metadata = {
        "schema_version": "1.0",
        "project_name": project_root.name,
        "project_type": "atlas-derived-project",
        "project_profile": "internal_tool",
        "bootstrap_template": "internal_tool",
        "generated_from_skill": "project-bootstrap",
        "derived_from": "Codex-Atlas",
        "atlas_root": str(ROOT),
        "audit_paths": ["docs", "memory", "workflows", "policies", "tools"],
        "status": status,
    }
    _write(project_root / ".atlas-project.json", json.dumps(metadata, indent=2) + "\n")
    _write(project_root / "README.md", "# Derived\n")
    _write(project_root / "AGENTS.md", "# AGENTS\n")
    for rel in ["docs", "memory", "workflows", "policies", "tools"]:
        (project_root / rel).mkdir(parents=True, exist_ok=True)


def _make_case_dir(name: str) -> Path:
    case_root = TMP_ROOT / f"{name}_{uuid.uuid4().hex}"
    case_root.mkdir(parents=True, exist_ok=True)
    return case_root


def test_bootstrap_phase_only_allows_audit_repo():
    case_root = _make_case_dir("bootstrap_guidance")
    try:
        project_root = case_root / "BootstrapGuidanceProject"
        _bootstrap_like_project(project_root, status="bootstrapped")
        phase = build_project_phase_report(ROOT, project_root)
        assert phase["current_phase"] == "bootstrap"
        assert phase["allowed_commands"] == ["audit-repo"]
    finally:
        shutil.rmtree(case_root, ignore_errors=True)


def test_phase_guidance_output_is_consistent_with_resolver():
    phase = build_project_phase_report(ROOT, WEB_ROOT)
    gate = build_quality_gate_report(ROOT, WEB_ROOT)
    assert gate["phase_guidance"]["current_phase"] == phase["current_phase"]
    assert gate["phase_guidance"]["recommended_next_steps"] == phase["recommended_next_steps"]
    assert gate["phase_guidance"]["top_phase_risks"] == phase["common_mistakes"][:3]


def test_blocked_command_returns_guidance_message():
    fake_project = Path(r"C:\Temp\atlas_phase_guidance_demo")
    phase = {
        "status": "ok",
        "current_phase": "bootstrap",
        "confidence": "high",
        "allowed_commands": ["audit-repo"],
        "next_valid_phases": ["build", "audit"],
        "recommended_actions": ["review generated structure"],
        "recommended_next_steps": ["review generated structure"],
        "common_mistakes": ["editing files before audit"],
        "blocked_actions": ["certify-project"],
        "evidence": ["bootstrap_scaffold_ok"],
    }

    from unittest.mock import patch

    with patch("tools.atlas_dispatcher._resolve_phase_report", return_value=phase):
        result = dispatch("certify-project", root=ROOT, project=fake_project)

    assert result.ok is False
    assert result.output["error"] == "phase_blocked"
    assert result.output["suggested_command"] == "audit-repo"
    assert "recommended next step" in result.output["message"].lower()


def test_quality_gate_report_includes_phase_guidance():
    gate = build_quality_gate_report(ROOT, WEB_ROOT)
    assert "phase_guidance" in gate
    assert gate["phase_guidance"]["current_phase"] == gate["phase_alignment"]["current_phase"]
    assert isinstance(gate["phase_guidance"]["recommended_next_steps"], list)
