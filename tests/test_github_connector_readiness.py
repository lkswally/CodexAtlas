import os
from types import SimpleNamespace
from unittest.mock import patch

os.environ["ATLAS_DISABLE_EVENT_LOGS"] = "1"

from tests._support_paths import ATLAS_ROOT
from tools.github_connector_readiness import assess_github_connector_readiness


def _matrix_stub(*, allowed: bool, requested_capability: str, risk_level: str = "low", blocked_reasons=None):
    return {
        "status": "ok",
        "mcp_permission_posture": {
            "platform": "github",
            "requested_capability": requested_capability,
            "allowed": allowed,
            "recommended_mode": "read_only",
            "risk_level": risk_level,
            "human_approval_required": requested_capability != "read_only",
            "dry_run_required": requested_capability in {"production_write", "execute"},
            "rollback_required": requested_capability in {"sandbox_write", "production_write", "execute"},
            "blocked_reasons": blocked_reasons or [],
            "next_safe_step": "Use read-only inspection first.",
            "configured_mcp_servers": ["openaiDeveloperDocs"],
            "mcp_readiness_state": "cli_ready_no_servers_configured",
            "advisory_only": True,
        },
        "advisory_only": True,
    }


def test_github_connector_allows_read_only_repo_status():
    with patch(
        "tools.github_connector_readiness.assess_mcp_permission_matrix_readiness",
        return_value=_matrix_stub(allowed=True, requested_capability="read_only"),
    ):
        result = assess_github_connector_readiness({"requested_capability": "repo_status"}, root=ATLAS_ROOT)

    posture = result["github_connector_posture"]
    assert posture["requested_capability"] == "repo_status"
    assert posture["requested_level"] == "read_only"
    assert posture["requested_allowed"] is True
    assert "repo_status" in posture["allowed_capabilities"]
    assert posture["runtime_probe"]["write_attempted"] is False
    assert posture["runtime_probe_state"] == "not_requested"


def test_github_connector_allows_pr_draft_as_draft_only():
    with patch(
        "tools.github_connector_readiness.assess_mcp_permission_matrix_readiness",
        return_value=_matrix_stub(allowed=True, requested_capability="draft_only", risk_level="medium"),
    ):
        result = assess_github_connector_readiness({"requested_capability": "pr_draft"}, root=ATLAS_ROOT)

    posture = result["github_connector_posture"]
    assert posture["requested_capability"] == "pr_draft"
    assert posture["requested_level"] == "draft_only"
    assert posture["requested_allowed"] is True
    assert "pr_draft" in posture["approval_gated_capabilities"]


def test_github_connector_blocks_merge():
    with patch(
        "tools.github_connector_readiness.assess_mcp_permission_matrix_readiness",
        return_value=_matrix_stub(
            allowed=False,
            requested_capability="production_write",
            risk_level="high",
            blocked_reasons=["production_write_blocked_by_default"],
        ),
    ):
        result = assess_github_connector_readiness({"requested_capability": "merge"}, root=ATLAS_ROOT)

    posture = result["github_connector_posture"]
    assert posture["requested_allowed"] is False
    assert "merge" in posture["blocked_capabilities"]
    assert "merge_blocked_by_github_policy" in posture["blocked_reasons"]


def test_github_connector_blocks_workflow_dispatch():
    with patch(
        "tools.github_connector_readiness.assess_mcp_permission_matrix_readiness",
        return_value=_matrix_stub(
            allowed=False,
            requested_capability="execute",
            risk_level="high",
            blocked_reasons=["execute_blocked_by_default"],
        ),
    ):
        result = assess_github_connector_readiness({"requested_capability": "workflow_dispatch"}, root=ATLAS_ROOT)

    posture = result["github_connector_posture"]
    assert posture["requested_allowed"] is False
    assert "workflow_dispatch" in posture["blocked_capabilities"]
    assert "workflow_dispatch_blocked_by_github_policy" in posture["blocked_reasons"]


def test_github_connector_blocks_secrets_access():
    with patch(
        "tools.github_connector_readiness.assess_mcp_permission_matrix_readiness",
        return_value=_matrix_stub(
            allowed=False,
            requested_capability="execute",
            risk_level="high",
            blocked_reasons=["sensitive_data_requires_read_only_or_additional_review"],
        ),
    ):
        result = assess_github_connector_readiness({"requested_capability": "secrets_access"}, root=ATLAS_ROOT)

    posture = result["github_connector_posture"]
    assert posture["requested_allowed"] is False
    assert "secrets_access" in posture["blocked_capabilities"]
    assert posture["risk_level"] == "high"


def test_github_connector_blocks_delete_and_force_push():
    with patch(
        "tools.github_connector_readiness.assess_mcp_permission_matrix_readiness",
        return_value=_matrix_stub(
            allowed=False,
            requested_capability="production_write",
            risk_level="high",
            blocked_reasons=["production_write_blocked_by_default"],
        ),
    ):
        delete_result = assess_github_connector_readiness({"requested_capability": "delete"}, root=ATLAS_ROOT)
        force_push_result = assess_github_connector_readiness({"requested_capability": "force_push"}, root=ATLAS_ROOT)

    assert delete_result["github_connector_posture"]["requested_allowed"] is False
    assert force_push_result["github_connector_posture"]["requested_allowed"] is False
    assert "delete" in delete_result["github_connector_posture"]["blocked_capabilities"]
    assert "force_push" in force_push_result["github_connector_posture"]["blocked_capabilities"]


def test_github_connector_embeds_mcp_permission_posture():
    matrix_response = _matrix_stub(allowed=True, requested_capability="read_only")
    with patch(
        "tools.github_connector_readiness.assess_mcp_permission_matrix_readiness",
        return_value=matrix_response,
    ):
        result = assess_github_connector_readiness({"requested_capability": "commits/read"}, root=ATLAS_ROOT)

    posture = result["github_connector_posture"]
    assert posture["requested_capability"] == "commits"
    assert posture["mcp_permission_posture"]["platform"] == "github"
    assert posture["mcp_permission_posture"]["requested_capability"] == "read_only"


def test_github_connector_runtime_probe_can_use_payload_evidence_only():
    matrix_response = _matrix_stub(allowed=True, requested_capability="read_only")
    with patch(
        "tools.github_connector_readiness.assess_mcp_permission_matrix_readiness",
        return_value=matrix_response,
    ):
        result = assess_github_connector_readiness(
            {
                "requested_capability": "repo_status",
                "runtime_probe": {
                    "authenticated_user_known": True,
                    "authenticated_user": "lkswally",
                    "repo_accessible": True,
                    "default_branch_readable": True,
                    "prs_readable": True,
                    "issues_readable": True,
                    "actions_readable": True,
                },
            },
            root=ATLAS_ROOT,
        )

    runtime_probe = result["github_connector_posture"]["runtime_probe"]
    assert result["github_connector_posture"]["runtime_probe_state"] == "read_only_available"
    assert runtime_probe["runtime_read_only_available"] is True
    assert runtime_probe["authenticated_user_known"] is True
    assert runtime_probe["authenticated_user"] == "lkswally"
    assert runtime_probe["write_attempted"] is False


def test_github_connector_runtime_probe_uses_gh_read_only_when_requested():
    matrix_response = _matrix_stub(allowed=True, requested_capability="read_only")

    def fake_run(command, capture_output, text, encoding, errors, check):
        joined = " ".join(command)
        if joined == "gh auth status":
            return SimpleNamespace(
                returncode=0,
                stdout="github.com\n  ✓ Logged in to github.com account lkswally\n  - Active account: true\n",
                stderr="",
            )
        if joined.startswith("gh repo view "):
            return SimpleNamespace(
                returncode=0,
                stdout='{"name":"CodexAtlas","owner":{"login":"lkswally"},"defaultBranchRef":{"name":"main"},"url":"https://github.com/lkswally/CodexAtlas"}',
                stderr="",
            )
        if joined.startswith("gh pr list "):
            return SimpleNamespace(returncode=0, stdout="[]", stderr="")
        if joined.startswith("gh run list "):
            return SimpleNamespace(returncode=0, stdout="[]", stderr="")
        if joined.startswith("gh issue list "):
            return SimpleNamespace(returncode=0, stdout="[]", stderr="")
        raise AssertionError(f"Unexpected command: {joined}")

    with patch(
        "tools.github_connector_readiness.assess_mcp_permission_matrix_readiness",
        return_value=matrix_response,
    ):
        with patch("tools.github_connector_readiness.subprocess.run", side_effect=fake_run):
            result = assess_github_connector_readiness(
                {
                    "requested_capability": "repo_status",
                    "perform_runtime_probe": True,
                    "repo": "lkswally/CodexAtlas",
                },
                root=ATLAS_ROOT,
            )

    runtime_probe = result["github_connector_posture"]["runtime_probe"]
    assert result["github_connector_posture"]["runtime_probe_state"] == "read_only_available"
    assert runtime_probe["runtime_read_only_available"] is True
    assert runtime_probe["authenticated_user_known"] is True
    assert runtime_probe["repo_accessible"] is True
    assert runtime_probe["default_branch_readable"] is True
    assert runtime_probe["prs_readable"] is True
    assert runtime_probe["actions_readable"] is True
    assert runtime_probe["issues_readable"] is True
    assert runtime_probe["write_attempted"] is False
