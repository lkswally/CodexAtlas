from __future__ import annotations

from tests._support_paths import ATLAS_ROOT
from tools.post_execution_learning_review import review_post_execution_learning


def test_repeated_generic_frontend_issue_becomes_readiness_or_policy_candidate():
    result = review_post_execution_learning(
        {
            "task_summary": "Landing update closed with generic frontend output again.",
            "repeated_error_patterns": ["generic frontend"],
            "user_feedback": "Still feels template-like and too safe.",
        },
        root=ATLAS_ROOT,
    )

    posture = result["post_execution_learning_posture"]
    assert posture["state"] in {"learning_candidate", "readiness_candidate", "policy_candidate"}
    assert posture["auto_mutation_allowed"] is False


def test_bug_fix_without_test_becomes_test_candidate():
    result = review_post_execution_learning(
        {
            "task_summary": "Fixed executor temp file leak.",
            "bug_fixed": True,
            "files_changed": ["tools/atlas_codex_executor.py"],
            "validations_run": ["python tools/atlas_verify.py"],
        },
        root=ATLAS_ROOT,
    )

    posture = result["post_execution_learning_posture"]
    assert posture["state"] == "test_candidate"
    assert posture["recommended_tests"]


def test_external_integration_request_becomes_readiness_candidate():
    result = review_post_execution_learning(
        {
            "task_summary": "Planned GitHub connector integration for external API usage.",
            "feature_scope": "external_surface",
            "blocked_reasons": ["api integration pending approval"],
        },
        root=ATLAS_ROOT,
    )

    posture = result["post_execution_learning_posture"]
    assert posture["state"] == "readiness_candidate"
    assert posture["recommended_readiness_layers"]


def test_auto_skill_rewrite_attempt_is_blocked():
    result = review_post_execution_learning(
        {
            "task_summary": "Automatically rewrite skill and create policy from runtime feedback.",
            "attempts_auto_mutation": True,
        },
        root=ATLAS_ROOT,
    )

    posture = result["post_execution_learning_posture"]
    assert posture["state"] == "blocked_auto_mutation"
    assert posture["auto_mutation_allowed"] is False


def test_clean_block_without_findings_needs_no_learning():
    result = review_post_execution_learning(
        {
            "task_summary": "Closed small documentation block cleanly.",
            "files_changed": ["docs/example.md", "tests/test_example.py"],
            "validations_run": ["python -m pytest tests/test_example.py -q"],
        },
        root=ATLAS_ROOT,
    )

    posture = result["post_execution_learning_posture"]
    assert posture["state"] == "no_learning_needed"
    assert posture["learning_candidates"] == []
