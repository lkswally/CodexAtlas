from __future__ import annotations

from tools.scheduled_automation_readiness import assess_scheduled_automation_readiness

from tests._support_paths import ATLAS_ROOT


def test_simple_weekly_reminder_is_manual_reminder_ready():
    result = assess_scheduled_automation_readiness(
        {
            "task_description": "Weekly reminder to review Atlas backlog manually.",
            "requested_schedule": "weekly",
        },
        root=ATLAS_ROOT,
    )

    posture = result["scheduled_automation_posture"]
    assert posture["recommended_state"] == "manual_reminder_ready"
    assert posture["schedule_type"] == "weekly"
    assert posture["has_side_effects"] is False


def test_github_trending_radar_without_write_is_dry_run_ready():
    result = assess_scheduled_automation_readiness(
        {
            "task_description": "Weekly GitHub Trending radar report for utility-first libraries.",
            "requested_schedule": "weekly",
            "requires_external_service": True,
            "dry_run_available": True,
        },
        root=ATLAS_ROOT,
    )

    posture = result["scheduled_automation_posture"]
    assert posture["recommended_state"] == "dry_run_ready"
    assert posture["requires_external_service"] is True
    assert posture["has_side_effects"] is False


def test_scheduled_email_without_approval_is_blocked():
    result = assess_scheduled_automation_readiness(
        {
            "task_description": "Send weekly email summary to leads automatically.",
            "requested_schedule": "weekly",
            "sends_email": True,
            "requires_external_service": True,
        },
        root=ATLAS_ROOT,
    )

    posture = result["scheduled_automation_posture"]
    assert posture["recommended_state"] == "blocked"
    assert "notification_without_approval" in posture["blocked_operations"]


def test_db_write_without_rollback_is_blocked():
    result = assess_scheduled_automation_readiness(
        {
            "task_description": "Weekly database write of validated leads.",
            "requested_schedule": "weekly",
            "writes_data": True,
            "sandbox_target": True,
            "dry_run_available": True,
            "rollback_available": False,
            "explicit_human_approval": True,
        },
        root=ATLAS_ROOT,
    )

    posture = result["scheduled_automation_posture"]
    assert posture["recommended_state"] == "blocked"
    assert "write_without_rollback" in posture["blocked_operations"]


def test_scheduled_n8n_execution_is_blocked():
    result = assess_scheduled_automation_readiness(
        {
            "task_description": "Execute n8n workflow every day.",
            "requested_schedule": "daily",
            "execute_n8n_workflow": True,
        },
        root=ATLAS_ROOT,
    )

    posture = result["scheduled_automation_posture"]
    assert posture["recommended_state"] == "blocked"
    assert "execute_workflow" in posture["blocked_operations"]


def test_recursive_or_self_mutating_task_is_blocked():
    result = assess_scheduled_automation_readiness(
        {
            "task_description": "Every week, reschedule itself and rewrite its own prompts.",
            "requested_schedule": "weekly",
            "recursive_scheduling": True,
            "auto_mutation": True,
        },
        root=ATLAS_ROOT,
    )

    posture = result["scheduled_automation_posture"]
    assert posture["recommended_state"] == "blocked"
    assert "recursive_scheduling" in posture["blocked_operations"]
    assert "auto_mutating_behavior" in posture["blocked_operations"]
