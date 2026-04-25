import os
from unittest.mock import patch

os.environ["ATLAS_DISABLE_EVENT_LOGS"] = "1"

from tools.atlas_mcp_manager import (
    approve_mcp,
    evaluate_mcp_request,
    list_mcp_profiles,
    simulate_mcp_execution,
)


def test_list_mcp_profiles_exposes_docs_search_as_only_experimental_profile():
    result = list_mcp_profiles()
    docs_search = next(item for item in result["profiles"] if item["id"] == "docs_search")
    github = next(item for item in result["profiles"] if item["id"] == "github")

    assert result["default_policy"] == "deny"
    assert docs_search["experimental_enabled"] is True
    assert docs_search["lifecycle_state"] == "approval_required"
    assert github["experimental_enabled"] is False
    assert github["lifecycle_state"] == "blocked"


def test_docs_search_requires_approval_before_simulated_execution():
    evaluation = evaluate_mcp_request("Look up the current official SDK docs and latest release notes.")
    docs_search = next(item for item in evaluation["profiles"] if item["id"] == "docs_search")

    assert docs_search["state"] == "approval_required"

    simulation = simulate_mcp_execution("docs_search", "current official SDK docs")
    assert simulation["ok"] is False
    assert simulation["state"] == "blocked"
    assert "mcp_approval_missing_or_invalid:docs_search" in simulation["blockers"]


def test_docs_search_can_simulate_execution_after_approval():
    approval = approve_mcp("docs_search", "Approved for a read-only documentation lookup dry run.")
    simulation = simulate_mcp_execution(
        "docs_search",
        "current official SDK docs",
        approval=approval,
    )

    assert approval["ok"] is True
    assert approval["state"] == "approved"
    assert simulation["ok"] is True
    assert simulation["state"] == "executed_simulated"
    assert simulation["simulation"]["default_mode"] == "read_only"


def test_watchlist_or_deferred_mcps_stay_blocked():
    github_approval = approve_mcp("github", "Trying to approve a watchlist MCP should fail.")
    filesystem_simulation = simulate_mcp_execution("filesystem", "external file inventory")
    engram_approval = approve_mcp("engram", "Trying to approve a deferred MCP should fail.")

    assert github_approval["state"] == "blocked"
    assert "mcp_profile_not_approved_for_experiment:github" in github_approval["blockers"]
    assert filesystem_simulation["state"] == "blocked"
    assert "mcp_profile_not_executable_in_current_stage:filesystem" in filesystem_simulation["blockers"]
    assert engram_approval["state"] == "blocked"
    assert "mcp_profile_not_approved_for_experiment:engram" in engram_approval["blockers"]


def test_mcp_manager_logs_structured_lifecycle_events():
    captured = []

    def fake_append(path, record):
        captured.append((path, record))

    with patch("tools.atlas_mcp_manager._event_logging_enabled", return_value=True):
        with patch("tools.atlas_mcp_manager._append_jsonl_record", side_effect=fake_append):
            approval = approve_mcp("docs_search", "Approved for lifecycle logging test.")
            simulation = simulate_mcp_execution(
                "docs_search",
                "current official SDK docs",
                approval=approval,
            )

    assert approval["state"] == "approved"
    assert simulation["state"] == "executed_simulated"
    assert len(captured) == 4
    assert captured[0][0].name == "mcp_events.jsonl"
    assert captured[1][0].name == "governance_events.jsonl"
    assert captured[2][0].name == "mcp_events.jsonl"
    assert captured[3][0].name == "governance_events.jsonl"
    assert captured[0][1]["event_type"] == "approve"
    assert captured[2][1]["event_type"] == "simulate"
