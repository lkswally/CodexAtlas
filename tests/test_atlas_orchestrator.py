import os
from pathlib import Path
from unittest.mock import patch

os.environ["ATLAS_DISABLE_EVENT_LOGS"] = "1"

from tools.atlas_orchestrator import orchestrate_task


def test_planning_task_routes_to_deep_reasoning():
    result = orchestrate_task("Plan the next architecture phases for Atlas.")
    assert result["intent"] == "planning"
    assert result["model_profile"] == "deep_reasoning"
    assert result["recommended_agent"] == "planner"
    assert result["recommended_skill"] is None


def test_code_execution_task_routes_to_code_execution():
    result = orchestrate_task("Implement a new Python command and update the function.")
    assert result["intent"] == "code_execution"
    assert result["model_profile"] == "code_execution"
    assert result["recommended_agent"] == "implementer"


def test_branding_task_routes_to_creative_product():
    result = orchestrate_task("Define branding, UX direction and audience for the landing page.")
    assert result["intent"] == "branding_ux"
    assert result["model_profile"] == "creative_product"
    assert result["recommended_agent"] == "ux_brand"
    assert result["recommended_skill"] == "product-branding-review"
    assert result["skill_metadata"]["supports_execution"] is True


def test_security_task_routes_to_security_profile():
    result = orchestrate_task("Review secrets exposure and auth boundary risks.")
    assert result["intent"] == "security"
    assert result["model_profile"] == "security"
    assert result["recommended_agent"] == "security_guard"
    assert result["requires_human_approval"] is True
    assert any("dangerous_task_keyword:secrets" == reason for reason in result["approval_reasons"])


def test_deploy_or_delete_requires_human_approval():
    result = orchestrate_task("Deploy to production and delete the old environment.")
    assert result["intent"] == "deployment_or_destructive_action"
    assert result["requires_human_approval"] is True
    assert result["risk_level"] == "high"
    assert result["execution_allowed"] is False


def test_database_task_suggests_database_schema_read_only():
    result = orchestrate_task("Research the database schema and review table relationships.")
    assert result["intent"] == "research"
    assert any(item["id"] == "database_schema" for item in result["suggested_mcps"])
    database_mcp = next(item for item in result["suggested_mcps"] if item["id"] == "database_schema")
    assert database_mcp["default_mode"] == "read_only"


def test_docs_search_is_the_only_experimental_read_only_mcp():
    result = orchestrate_task("Look up the current official SDK docs and latest release notes.")
    assert any(item["id"] == "docs_search" for item in result["suggested_mcps"])
    docs_search = next(item for item in result["suggested_mcps"] if item["id"] == "docs_search")
    assert docs_search["default_mode"] == "read_only"
    assert docs_search["experimental_enabled"] is True
    assert docs_search["atlas_decision"] == "experimental_read_only"


def test_github_task_stays_watchlist_and_requires_approval():
    result = orchestrate_task("Inspect the GitHub pull request state before review.")
    assert any(item["id"] == "github" for item in result["suggested_mcps"])
    github_mcp = next(item for item in result["suggested_mcps"] if item["id"] == "github")
    assert github_mcp["experimental_enabled"] is False
    assert github_mcp["atlas_decision"] == "watchlist"
    assert result["requires_human_approval"] is True


def test_simple_documentation_task_routes_to_cost_saver():
    result = orchestrate_task("Update the README and document the current status.")
    assert result["intent"] == "documentation"
    assert result["model_profile"] == "cost_saver"


def test_project_creation_task_recommends_project_bootstrap_skill():
    result = orchestrate_task(
        "Create a new project from Atlas and scaffold the initial structure.",
        output_dir=Path(r"C:\Temp\atlas_bootstrap_candidate"),
    )
    assert result["intent"] == "project_creation"
    assert result["recommended_skill"] == "project-bootstrap"
    assert result["recommended_workflow"] == "create_project"
    assert result["skill_metadata"]["name"] == "project-bootstrap"
    assert result["skill_metadata"]["supports_execution"] is True
    assert result["preflight"]["safe_to_execute"] is True
    assert result["project_type"] == "internal_tool"


def test_repo_audit_task_recommends_repo_audit_skill():
    result = orchestrate_task("Run a repo audit to check governance drift and boundary issues.")
    assert result["recommended_skill"] == "repo-audit"
    assert result["recommended_workflow"] == "audit_project"
    assert result["skill_metadata"]["name"] == "repo-audit"


def test_forbidden_actions_and_approval_triggers_influence_execution_output():
    result = orchestrate_task("Delete project files while running a repo audit in production.")
    assert result["recommended_skill"] == "repo-audit"
    assert result["requires_human_approval"] is True
    assert result["execution_allowed"] is False
    assert any(reason.startswith("dangerous_task_keyword:delete") for reason in result["approval_reasons"])
    assert any(blocker.startswith("skill_forbidden_action:") for blocker in result["execution_blockers"])


def test_skill_human_approval_triggers_influence_output():
    result = orchestrate_task("Bootstrap project and the task asks for automatic dependency installation or deployment.")
    assert result["recommended_skill"] == "project-bootstrap"
    assert result["requires_human_approval"] is True
    assert any(reason.startswith("skill_human_approval_trigger:") for reason in result["approval_reasons"])
    assert result["execution_allowed"] is False


def test_project_bootstrap_preflight_nonexistent_output_dir_is_safe():
    target = Path(r"C:\Temp\atlas_bootstrap_new_project")
    result = orchestrate_task("Bootstrap project for a sandbox demo.", output_dir=target)
    assert result["recommended_skill"] == "project-bootstrap"
    assert result["preflight"]["exists"] is False
    assert result["preflight"]["safe_to_execute"] is True
    assert result["safe_to_execute"] is True
    assert result["execution_allowed"] is True


def test_project_bootstrap_infers_ai_agent_system_project_type():
    result = orchestrate_task(
        "Bootstrap a new AI agent system for internal orchestration.",
        output_dir=Path(r"C:\Temp\atlas_agent_system_candidate"),
    )
    assert result["recommended_skill"] == "project-bootstrap"
    assert result["project_type"] == "ai_agent_system"
    assert "ai_agent_system" in result["project_type_reason"]


def test_project_bootstrap_invalid_explicit_project_type_blocks_execution():
    result = orchestrate_task(
        "Bootstrap a new project.",
        output_dir=Path(r"C:\Temp\atlas_invalid_project_type"),
        project_type="desktop_app",
    )
    assert result["recommended_skill"] == "project-bootstrap"
    assert result["execution_allowed"] is False
    assert "project_bootstrap_invalid_project_type:desktop_app" in result["execution_blockers"]


def test_project_bootstrap_preflight_existing_empty_output_dir_is_safe():
    target = Path(r"C:\Temp\atlas_preflight_empty")

    original_exists = Path.exists
    original_is_dir = Path.is_dir
    original_iterdir = Path.iterdir

    def fake_exists(path):
        if path == target:
            return True
        return original_exists(path)

    def fake_is_dir(path):
        if path == target:
            return True
        return original_is_dir(path)

    def fake_iterdir(path):
        if path == target:
            return iter(())
        return original_iterdir(path)

    with patch("pathlib.Path.exists", new=fake_exists):
        with patch("pathlib.Path.is_dir", new=fake_is_dir):
            with patch("pathlib.Path.iterdir", new=fake_iterdir):
                result = orchestrate_task("Bootstrap project for a sandbox demo.", output_dir=target)
                assert result["recommended_skill"] == "project-bootstrap"
                assert result["preflight"]["exists"] is True
                assert result["preflight"]["is_empty"] is True
                assert result["safe_to_execute"] is True
                assert result["execution_allowed"] is True


def test_project_bootstrap_preflight_existing_non_empty_output_dir_blocks_execution():
    target = Path(r"C:\Temp\atlas_preflight_non_empty")
    readme = target / "README.md"

    original_exists = Path.exists
    original_is_dir = Path.is_dir
    original_iterdir = Path.iterdir

    def fake_exists(path):
        if path == target or path == readme:
            return True
        return original_exists(path)

    def fake_is_dir(path):
        if path == target:
            return True
        if path == readme:
            return False
        return original_is_dir(path)

    def fake_iterdir(path):
        if path == target:
            return iter((readme,))
        return original_iterdir(path)

    with patch("pathlib.Path.exists", new=fake_exists):
        with patch("pathlib.Path.is_dir", new=fake_is_dir):
            with patch("pathlib.Path.iterdir", new=fake_iterdir):
                result = orchestrate_task("Bootstrap project for a sandbox demo.", output_dir=target)
                assert result["recommended_skill"] == "project-bootstrap"
                assert result["preflight"]["exists"] is True
                assert result["preflight"]["is_empty"] is False
                assert result["preflight"]["seems_existing_project"] is True
                assert result["safe_to_execute"] is False
                assert result["execution_allowed"] is False
                assert "project_bootstrap_output_dir_not_empty" in result["execution_blockers"]


def test_project_bootstrap_preflight_inside_reyesoft_is_blocked():
    target = Path(r"C:\Proyectos\REYESOFT\demo-bootstrap")
    result = orchestrate_task("Bootstrap project for a sandbox demo.", output_dir=target)
    assert result["recommended_skill"] == "project-bootstrap"
    assert result["preflight"]["inside_reyesoft"] is True
    assert result["safe_to_execute"] is False
    assert "project_bootstrap_output_dir_inside_reyesoft" in result["execution_blockers"]


def test_project_bootstrap_preflight_inside_atlas_root_is_blocked():
    target = Path(r"C:\Proyectos\Codex-Atlas\demo-bootstrap")
    result = orchestrate_task("Bootstrap project for a sandbox demo.", output_dir=target)
    assert result["recommended_skill"] == "project-bootstrap"
    assert result["preflight"]["inside_atlas_root"] is True
    assert result["safe_to_execute"] is False
    assert "project_bootstrap_output_dir_inside_atlas_root" in result["execution_blockers"]


def test_bootstrap_project_text_does_not_trigger_false_deploy_or_delete_blockers():
    target = Path(r"C:\Temp\atlas_bootstrap_phrase_check")
    result = orchestrate_task("Bootstrap project in a safe sandbox with explicit output_dir.", output_dir=target)
    assert result["recommended_skill"] == "project-bootstrap"
    assert not any(reason.startswith("dangerous_task_keyword:deploy") for reason in result["approval_reasons"])
    assert not any(reason.startswith("dangerous_task_keyword:delete") for reason in result["approval_reasons"])
    assert not any(blocker.startswith("skill_forbidden_action:deploy") for blocker in result["execution_blockers"])


def test_orchestrator_appends_structured_routing_log():
    captured = []

    def fake_append(path, record):
        captured.append((path, record))

    with patch("tools.atlas_orchestrator._event_logging_enabled", return_value=True):
        with patch("tools.atlas_orchestrator._append_jsonl_record", side_effect=fake_append):
            result = orchestrate_task("Plan the next architecture phases for Atlas.")

    assert result["intent"] == "planning"
    assert len(captured) == 1
    path, record = captured[0]
    assert path.name == "routing_log.jsonl"
    assert record["intent"] == "planning"
    assert record["recommended_agent"] == "planner"
    assert record["recommended_workflow"] == "orchestrator_routing"
    assert record["task_fingerprint"]
    assert "task" not in record
