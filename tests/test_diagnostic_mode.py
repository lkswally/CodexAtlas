import copy
import json
from pathlib import Path

import pytest

from tools.dangerous_command_policy import classify_command
from tools.diagnostic_mode import (
    DECISION_FIELDS,
    ENVELOPE_FIELDS,
    DiagnosticModeError,
    build_diagnostic_return_envelope,
    combine_with_dangerous_command_policy,
    evaluate_diagnostic_action,
    load_diagnostic_mode_checklist,
    validate_diagnostic_mode_config,
    validate_diagnostic_return_envelope,
)


def test_loads_valid_data_only_configuration():
    config = load_diagnostic_mode_checklist()
    assert config["policy_name"] == "diagnostic_mode_checklist"
    assert config["contract"]["mode"] == "diagnostic"
    assert config["contract"]["read_only"] is True
    assert config["contract"]["unknown_action_policy"] == "BLOCK"
    assert config["contract"]["allow_file_writes"] is False
    assert config["contract"]["allow_mcp_writes"] is False
    assert config["contract"]["allow_memory_writes"] is False
    assert config["contract"]["allow_deploy"] is False


@pytest.mark.parametrize(
    ("mutation", "message"),
    [
        (lambda c: c.update(policy_name="other"), "policy_name"),
        (lambda c: c.update(version="v2"), "version"),
        (lambda c: c["contract"].update(read_only=False), "read_only"),
        (lambda c: c["contract"].update(allow_file_writes=True), "allow_file_writes"),
        (lambda c: c["contract"].update(unknown_action_policy="ALLOW"), "unknown_action_policy"),
        (lambda c: c.update(allowed_actions=[]), "allowed_actions"),
        (lambda c: c["allowed_actions"][0].update(reason=""), "reason"),
        (lambda c: c["blocked_actions"].append(copy.deepcopy(c["blocked_actions"][0])), "Duplicate"),
        (lambda c: c.update(limits={}), "limit"),
    ],
)
def test_invalid_configuration_fails_closed(mutation, message):
    config = load_diagnostic_mode_checklist()
    mutation(config)
    with pytest.raises(DiagnosticModeError, match=message):
        validate_diagnostic_mode_config(config)


@pytest.mark.parametrize(
    "action",
    [
        "read_file",
        "list files",
        "git status",
        "git diff",
        "run_read_only_tests",
        "compileall",
        "governance checks",
        "atlas_verify",
        "analyze_logs",
        "generate_findings_in_memory",
        "prepare_report_without_persisting",
    ],
)
def test_read_only_actions_are_allowed(action):
    decision = evaluate_diagnostic_action(action)
    assert decision["status"] == "ALLOW"
    assert decision["mode"] == "diagnostic"
    assert decision["read_only"] is True
    assert decision["evidence_required"] is True
    assert decision["side_effect_detected"] is False
    assert decision["matched_rule"]


def test_mcp_read_only_action_requires_explicit_metadata():
    assert evaluate_diagnostic_action("mcp_tools_list")["status"] == "UNKNOWN"
    decision = evaluate_diagnostic_action("mcp_tools_list", metadata={"read_only": True})
    assert decision["status"] == "ALLOW"
    assert decision["matched_rule"] == "mcp_tools_list"


@pytest.mark.parametrize(
    "action",
    [
        "modify_file",
        "create_file",
        "delete_file",
        "move_file",
        "install_dependency",
        "update_dependency",
        "git commit",
        "git push",
        "git reset",
        "git clean",
        "deploy",
        "change_secrets",
        "change_config",
        "change_workflow",
        "mcp_write",
        "memory_write",
        "database_write",
        "auto-fix",
        "runtime_integration",
    ],
)
def test_mutating_actions_are_blocked(action):
    decision = evaluate_diagnostic_action(action)
    assert decision["status"] == "BLOCK"
    assert decision["side_effect_detected"] is True
    assert decision["matched_rule"]


def test_unknown_actions_are_not_assumed_safe():
    decision = evaluate_diagnostic_action("run mysterious external tool")
    assert decision["status"] == "UNKNOWN"
    assert decision["matched_rule"] == "unknown_action_policy"
    assert decision["side_effect_detected"] is False


def test_metadata_side_effect_blocks_otherwise_allowed_action():
    decision = evaluate_diagnostic_action("read_file", metadata={"writes_files": True})
    assert decision["status"] == "BLOCK"
    assert decision["matched_rule"] == "metadata_side_effect"
    assert decision["side_effect_detected"] is True


def test_decision_output_contract_is_exact_and_deterministic():
    first = evaluate_diagnostic_action("git status")
    second = evaluate_diagnostic_action("git status")
    assert first == second
    assert tuple(first) == DECISION_FIELDS
    assert set(first) == set(DECISION_FIELDS)


def test_dangerous_command_policy_compatibility_uses_more_restrictive_result():
    diagnostic = evaluate_diagnostic_action("git status")
    safe_command = classify_command("git status -sb")
    assert combine_with_dangerous_command_policy(diagnostic, safe_command)["status"] == "ALLOW"

    blocked = combine_with_dangerous_command_policy(
        evaluate_diagnostic_action("git commit"),
        classify_command("git commit -m test"),
    )
    assert blocked["status"] == "BLOCK"
    assert blocked["side_effect_detected"] is True

    unknown = combine_with_dangerous_command_policy(
        evaluate_diagnostic_action("git status"),
        classify_command("python custom.py"),
    )
    assert unknown["status"] == "UNKNOWN"
    assert unknown["matched_rule"] == "unknown_action_policy"


def test_diagnostic_return_envelope_contract_requires_empty_changes_and_evidence_for_pass():
    envelope = build_diagnostic_return_envelope(
        agent="CodexAtlas Verifier",
        status="PASS",
        summary="Reviewed diagnostic evidence.",
        evidence=["git status -sb clean"],
        risks=[],
        recommendation="Proceed to a separate implementation phase if approved.",
    )
    assert tuple(envelope) == ENVELOPE_FIELDS
    assert envelope["changes"] == []
    validate_diagnostic_return_envelope(envelope)

    bad_changes = dict(envelope)
    bad_changes["changes"] = ["modified file"]
    with pytest.raises(DiagnosticModeError, match="changes must be empty"):
        validate_diagnostic_return_envelope(bad_changes)

    no_evidence = dict(envelope)
    no_evidence["evidence"] = []
    with pytest.raises(DiagnosticModeError, match="PASS requires evidence"):
        validate_diagnostic_return_envelope(no_evidence)


def test_blocked_envelope_can_record_prohibited_action_without_changes():
    envelope = build_diagnostic_return_envelope(
        agent="CodexAtlas Verifier",
        status="BLOCKED",
        summary="Diagnostic Mode blocked git push.",
        evidence=["action=git_push"],
        risks=["git_push is outside read-only scope"],
        recommendation="Exit Diagnostic Mode and request explicit implementation approval.",
        needs_followup=True,
    )
    assert envelope["changes"] == []
    assert envelope["needs_followup"] is True


def test_config_file_is_json_data_only():
    path = Path(__file__).parents[1] / "config" / "diagnostic_mode_checklist.json"
    config = json.loads(path.read_text(encoding="utf-8"))
    assert config["policy_name"] == "diagnostic_mode_checklist"
    assert "allowed_actions" in config
    assert "blocked_actions" in config
    assert "contract" in config

def test_safety_no_subprocess_network_or_filesystem_write_helpers():
    source = Path(__file__).parents[1] / "tools" / "diagnostic_mode.py"
    text = source.read_text(encoding="utf-8").lower()
    assert "import subprocess" not in text
    assert "from subprocess" not in text
    assert "import socket" not in text
    assert "import requests" not in text
    assert "urllib" not in text
    assert ".write_text(" not in text
    assert "open(" not in text
    assert "set-content" not in text


def test_safety_actions_cover_no_auto_fix_deploy_config_mcp_memory_writes():
    for action in ("auto_fix", "deploy", "change_config", "mcp_write", "memory_write"):
        decision = evaluate_diagnostic_action(action)
        assert decision["status"] == "BLOCK"
        assert decision["side_effect_detected"] is True
