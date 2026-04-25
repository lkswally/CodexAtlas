import os
from unittest.mock import patch

os.environ["ATLAS_DISABLE_EVENT_LOGS"] = "1"

from tools.docs_search_adapter import execute_docs_search_adapter, load_docs_search_catalog, search_official_docs_catalog
from tools.atlas_mcp_manager import (
    approve_mcp,
    execute_mcp_request,
    evaluate_mcp_request,
    inspect_docs_search_runtime_support,
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


def test_docs_search_can_execute_through_adapter_after_approval():
    approval = approve_mcp("docs_search", "Approved for a read-only documentation lookup dry run.")
    with patch(
        "tools.atlas_mcp_manager.inspect_docs_search_runtime_support",
        return_value={"real_mcp_supported": False, "blockers": ["codex_cli_not_invocable"]},
    ):
        execution = execute_mcp_request(
            "docs_search",
            "current official SDK docs",
            approval=approval,
        )

    assert approval["ok"] is True
    assert approval["state"] == "approved"
    assert execution["ok"] is True
    assert execution["state"] == "executed_adapter"
    assert execution["execution_mode"] == "adapter_read_only"
    assert execution["adapter"]["mode"] == "adapter_read_only"
    assert execution["adapter"]["result_count"] >= 1
    assert execution["adapter"]["confidence_level"] in {"medium", "high"}
    assert execution["adapter"]["summary"]["deduplicated"] is True
    assert len(execution["adapter"]["key_points"]) >= 3


def test_docs_search_execute_falls_back_to_simulation_if_adapter_fails():
    approval = approve_mcp("docs_search", "Approved for fallback testing.")

    with patch("tools.atlas_mcp_manager.inspect_docs_search_runtime_support", return_value={"real_mcp_supported": False, "blockers": ["codex_cli_not_invocable"]}):
        with patch("tools.atlas_mcp_manager._execute_docs_search_adapter", side_effect=RuntimeError("adapter failed")):
            execution = execute_mcp_request(
                "docs_search",
                "current official SDK docs",
                approval=approval,
            )

    assert execution["ok"] is True
    assert execution["state"] == "executed_simulated"
    assert execution["fallback_reason"] == "adapter_unavailable_or_failed"
    assert execution["runtime_support"]["real_mcp_supported"] is False


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
            with patch(
                "tools.atlas_mcp_manager.inspect_docs_search_runtime_support",
                return_value={"real_mcp_supported": False, "blockers": ["codex_cli_not_invocable"]},
            ):
                execution = execute_mcp_request(
                    "docs_search",
                    "current official SDK docs",
                    approval=approval,
                )

    assert approval["state"] == "approved"
    assert execution["state"] == "executed_adapter"
    assert len(captured) == 4
    assert captured[0][0].name == "mcp_events.jsonl"
    assert captured[1][0].name == "governance_events.jsonl"
    assert captured[2][0].name == "mcp_events.jsonl"
    assert captured[3][0].name == "governance_events.jsonl"
    assert captured[0][1]["event_type"] == "approve"
    assert captured[2][1]["event_type"] == "execute"


def test_runtime_support_inspection_reports_unconfigured_or_unverified_state():
    with patch("tools.atlas_mcp_manager._load_global_codex_config_text", return_value=""):
        with patch("tools.atlas_mcp_manager.subprocess.run", side_effect=PermissionError("Access is denied")):
            result = inspect_docs_search_runtime_support()

    assert result["real_mcp_supported"] is False
    assert "codex_docs_mcp_not_configured" in result["blockers"]
    assert "codex_cli_not_invocable" in result["blockers"]


def test_docs_search_adapter_deduplicates_duplicate_urls_and_ranks_results():
    results = search_official_docs_catalog("codex mcp docs config")

    urls = [item["url"] for item in results]
    assert len(urls) == len(set(urls))
    assert results[0]["score"] >= results[-1]["score"]
    assert results[0]["confidence_level"] in {"medium", "high"}


def test_docs_search_adapter_returns_structured_summary_and_staleness_signal():
    result = execute_docs_search_adapter("current official SDK docs and connectors")

    assert result["ok"] is True
    assert result["mode"] == "adapter_read_only"
    assert result["summary"]["result_count"] == result["result_count"]
    assert result["summary"]["confidence_level"] == result["confidence_level"]
    assert isinstance(result["summary"]["possible_outdated_results"], bool)
    assert len(result["key_points"]) >= 3
    assert all("staleness" in item for item in result["results"])


def test_docs_search_catalog_loads_from_external_config():
    catalog = load_docs_search_catalog()

    assert len(catalog) >= 2
    assert all(item["id"] for item in catalog)
    assert all(item["url"] for item in catalog)
    assert all(item["status"] in {"active", "watchlist", "deprecated"} for item in catalog)


def test_docs_search_adapter_marks_stale_entries_as_possible_outdated():
    stale_catalog = [
        {
            "id": "stale_docs",
            "title": "Stale Docs",
            "url": "https://example.com/stale-docs",
            "source_type": "official_openai_docs",
            "topics": ["sdk", "docs", "connectors"],
            "description": "Old reference that still matches the query strongly.",
            "last_verified": "2025-01-01",
            "freshness_window_days": 30,
            "status": "active",
        }
    ]

    with patch("tools.docs_search_adapter.load_docs_search_catalog", return_value=stale_catalog):
        result = execute_docs_search_adapter("sdk docs connectors")

    assert result["ok"] is True
    assert result["result_count"] == 1
    assert result["possible_outdated_results"] is True
    assert result["results"][0]["staleness"]["possibly_outdated"] is True


def test_docs_search_adapter_does_not_rank_deprecated_entries_as_active_results():
    catalog = [
        {
            "id": "deprecated_docs",
            "title": "Deprecated Docs",
            "url": "https://example.com/deprecated-docs",
            "source_type": "official_openai_docs",
            "topics": ["sdk", "docs"],
            "description": "Deprecated entry that should not surface as an active result.",
            "last_verified": "2026-04-24",
            "freshness_window_days": 120,
            "status": "deprecated",
        },
        {
            "id": "active_docs",
            "title": "Active Docs",
            "url": "https://example.com/active-docs",
            "source_type": "official_openai_docs",
            "topics": ["sdk", "docs"],
            "description": "Active entry that should be ranked.",
            "last_verified": "2026-04-24",
            "freshness_window_days": 120,
            "status": "active",
        },
    ]

    results = search_official_docs_catalog("sdk docs", catalog=catalog)

    assert len(results) == 1
    assert results[0]["id"] == "active_docs"
    assert results[0]["status"] == "active"
