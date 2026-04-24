import os
from pathlib import Path
from unittest.mock import patch

os.environ["ATLAS_DISABLE_EVENT_LOGS"] = "1"

from tools.atlas_orchestrator import execute_skill, get_project_bootstrap_contract


def test_repo_audit_execution_uses_dispatcher():
    execution = execute_skill("repo-audit", "Run a repo audit.")
    assert execution["skill"] == "repo-audit"
    assert execution["mode"] == "dispatcher_audit_repo"
    assert execution["ok"] is True
    assert execution["output"]["command"] == "audit-repo"


def test_project_bootstrap_execution_requires_output_dir():
    execution = execute_skill("project-bootstrap", "Bootstrap a new derived project.")
    contract = get_project_bootstrap_contract()
    assert execution["skill"] == "project-bootstrap"
    assert execution["ok"] is False
    assert execution["error"] == "missing_output_dir"
    assert execution["contract"]["required_inputs"] == contract["required_inputs"]
    assert execution["contract"]["execution_mode"] == "write_docs"
    assert execution["contract"]["allowed_paths_policy"] == "explicit_output_dir_only"
    assert execution["contract"]["required_files"] == contract["required_files"]
    assert execution["contract"]["default_project_type"] == "internal_tool"
    assert execution["contract"]["type_template"]["readme_template"].endswith("README.md.template")


def test_project_bootstrap_execution_returns_contract_and_expected_writes():
    target = Path(r"C:\Temp\atlas_bootstrap_mock\DerivedProject")
    contract = get_project_bootstrap_contract()
    created_paths = []
    written_files = {}

    def fake_mkdir(self, parents=False, exist_ok=False):
        created_paths.append(str(self))

    def fake_write(path, content):
        written_files[path.name] = content

    derived_project_events = []

    def fake_record(root, payload):
        derived_project_events.append((root, payload))

    with patch("pathlib.Path.mkdir", new=fake_mkdir):
        with patch("tools.atlas_orchestrator._write_file_if_missing", side_effect=fake_write):
            with patch("tools.atlas_orchestrator._record_derived_project_creation", side_effect=fake_record):
                execution = execute_skill(
                    "project-bootstrap",
                    "Bootstrap a new derived project.",
                    output_dir=target,
                    project_type="ai_agent_system",
                )

    assert execution["skill"] == "project-bootstrap"
    assert execution["ok"] is True
    assert execution["project_type"] == "ai_agent_system"
    assert "agents" in execution["created_directories"]
    assert "skills" in execution["created_directories"]
    assert "evaluations" in execution["created_directories"]
    assert execution["created_files"] == contract["required_files"]
    assert "agents" in execution["contract"]["generated_structure"]["directories"]
    assert execution["contract"]["required_files"] == contract["required_files"]
    assert execution["contract"]["forbidden_actions"]
    assert execution["contract"]["human_approval_triggers"]
    assert str(target.resolve()) in created_paths
    for name in execution["created_directories"]:
        assert str((target.resolve() / name)) in created_paths
    assert sorted(written_files.keys()) == sorted(contract["required_files"])
    assert "AI Agent System" in written_files["README.md"]
    assert "Example Usage" in written_files["README.md"]
    assert "agents/" in written_files["README.md"]
    assert "C:\\Proyectos\\Codex-Atlas" in written_files["README.md"]
    assert "Project Context" in written_files["AGENTS.md"]
    assert "ai_agent_system" in written_files["AGENTS.md"]
    assert "{{" not in written_files["README.md"]
    assert "{{" not in written_files["AGENTS.md"]
    assert '"project_profile": "ai_agent_system"' in written_files[".atlas-project.json"]
    assert len(derived_project_events) == 1
    _, event_payload = derived_project_events[0]
    assert event_payload["project_name"] == "DerivedProject"
    assert event_payload["project_profile"] == "ai_agent_system"
    assert event_payload["generated_from_skill"] == "project-bootstrap"


def test_project_bootstrap_execution_rejects_invalid_project_type():
    execution = execute_skill(
        "project-bootstrap",
        "Bootstrap a new derived project.",
        output_dir=Path(r"C:\Temp\atlas_bootstrap_invalid_type"),
        project_type="desktop_app",
    )
    assert execution["skill"] == "project-bootstrap"
    assert execution["ok"] is False
    assert execution["error"] == "invalid_project_type"


def test_project_bootstrap_execution_blocks_output_dir_inside_atlas_root():
    execution = execute_skill(
        "project-bootstrap",
        "Bootstrap a new derived project.",
        output_dir=Path(r"C:\Proyectos\Codex-Atlas\demo-bootstrap"),
    )
    assert execution["skill"] == "project-bootstrap"
    assert execution["ok"] is False
    assert execution["error"] == "unsafe_output_dir"
    assert execution["preflight"]["inside_atlas_root"] is True
    assert "project_bootstrap_output_dir_inside_atlas_root" in execution["preflight"]["blockers"]


def test_project_bootstrap_default_internal_tool_template_is_used_when_not_specified():
    target = Path(r"C:\Temp\atlas_bootstrap_internal_tool")
    created_paths = []
    written_files = {}

    def fake_mkdir(self, parents=False, exist_ok=False):
        created_paths.append(str(self))

    def fake_write(path, content):
        written_files[path.name] = content

    with patch("pathlib.Path.mkdir", new=fake_mkdir):
        with patch("tools.atlas_orchestrator._write_file_if_missing", side_effect=fake_write):
            execution = execute_skill(
                "project-bootstrap",
                "Bootstrap a new internal operations tool.",
                output_dir=target,
            )

    assert execution["ok"] is True
    assert execution["project_type"] == "internal_tool"
    assert "automation" in execution["created_directories"]
    assert "reports" in execution["created_directories"]
    assert "Internal Tool" in written_files["README.md"]
    assert "{{" not in written_files["README.md"]


def test_project_bootstrap_templates_render_minimum_content_for_all_profiles():
    contract = get_project_bootstrap_contract()

    profile_expectations = {
        "backend_service": ("Backend Service", "api/"),
        "frontend_app": ("Frontend App", "app/"),
        "fullstack": ("Fullstack Project", "frontend/"),
        "internal_tool": ("Internal Tool", "automation/"),
        "ai_agent_system": ("AI Agent System", "agents/"),
    }

    for project_type, (profile_label, expected_directory_hint) in profile_expectations.items():
        target = Path(rf"C:\Temp\atlas_bootstrap_{project_type}")
        written_files = {}

        def fake_write(path, content):
            written_files[path.name] = content

        with patch("pathlib.Path.mkdir", new=lambda self, parents=False, exist_ok=False: None):
            with patch("tools.atlas_orchestrator._write_file_if_missing", side_effect=fake_write):
                execution = execute_skill(
                    "project-bootstrap",
                    f"Bootstrap a new {project_type} project.",
                    output_dir=target,
                    project_type=project_type,
                )

        assert execution["ok"] is True
        assert execution["project_type"] == project_type
        assert profile_label in written_files["README.md"]
        assert expected_directory_hint in written_files["README.md"]
        assert "Bootstrap source: `project-bootstrap`" in written_files["README.md"]
        assert "C:\\Proyectos\\Codex-Atlas" in written_files["README.md"]
        assert execution["project_type"] in written_files["AGENTS.md"]
        assert "{{" not in written_files["README.md"]
        assert "{{" not in written_files["AGENTS.md"]


def test_product_branding_review_execution_returns_checklist():
    execution = execute_skill("product-branding-review", "Review the positioning and visual direction.")
    assert execution["skill"] == "product-branding-review"
    assert execution["ok"] is True
    assert execution["mode"] == "structured_checklist"
    assert len(execution["checklist"]) >= 5


def test_repo_audit_execution_is_blocked_for_dangerous_task_when_requested_through_cli_logic():
    from tools.atlas_orchestrator import orchestrate_task

    result = orchestrate_task("Delete project files during a repo audit.")
    assert result["recommended_skill"] == "repo-audit"
    assert result["requires_human_approval"] is True
    assert result["execution_allowed"] is False
