from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, Mapping, Optional


DEFAULT_CHECKLIST_PATH = (
    Path(__file__).resolve().parents[1] / "config" / "diagnostic_mode_checklist.json"
)

DECISION_FIELDS = (
    "status",
    "mode",
    "read_only",
    "action",
    "reason",
    "matched_rule",
    "evidence_required",
    "side_effect_detected",
)
ENVELOPE_FIELDS = (
    "agent",
    "status",
    "summary",
    "evidence",
    "changes",
    "risks",
    "recommendation",
    "needs_followup",
)
ALLOWED_DECISION_STATUSES = {"ALLOW", "BLOCK", "UNKNOWN"}
ALLOWED_ENVELOPE_STATUSES = {"PASS", "WARN", "FAIL", "BLOCKED"}
REQUIRED_CONTRACT = {
    "mode": "diagnostic",
    "read_only": True,
    "allow_file_writes": False,
    "allow_shell_mutations": False,
    "allow_dependency_install": False,
    "allow_network_writes": False,
    "allow_mcp_writes": False,
    "allow_memory_writes": False,
    "allow_config_changes": False,
    "allow_runtime_changes": False,
    "allow_deploy": False,
    "allow_auto_fix": False,
    "evidence_required": True,
    "unknown_action_policy": "BLOCK",
}
REQUIRED_ALLOWED_OUTPUTS = {
    "analysis",
    "evidence",
    "findings",
    "risks",
    "recommendations",
    "report",
}


class DiagnosticModeError(ValueError):
    """Raised when Diagnostic Mode configuration or output contracts are invalid."""


def load_diagnostic_mode_checklist(path: Path = DEFAULT_CHECKLIST_PATH) -> Dict[str, Any]:
    try:
        config = json.loads(Path(path).read_text(encoding="utf-8"))
    except OSError as exc:
        raise DiagnosticModeError(f"Could not read diagnostic checklist: `{path}`.") from exc
    except json.JSONDecodeError as exc:
        raise DiagnosticModeError(f"Diagnostic checklist is not valid JSON: `{path}`.") from exc
    validate_diagnostic_mode_config(config)
    return config


def validate_diagnostic_mode_config(config: Any) -> None:
    if not isinstance(config, dict):
        raise DiagnosticModeError("Diagnostic checklist must be a JSON object.")
    if config.get("policy_name") != "diagnostic_mode_checklist":
        raise DiagnosticModeError("Diagnostic checklist policy_name is invalid.")
    if config.get("version") != "v1":
        raise DiagnosticModeError("Diagnostic checklist version must be v1.")

    contract = config.get("contract")
    if not isinstance(contract, dict):
        raise DiagnosticModeError("Diagnostic checklist contract must be an object.")
    for field, expected in REQUIRED_CONTRACT.items():
        if contract.get(field) != expected:
            raise DiagnosticModeError(
                f"Diagnostic checklist contract `{field}` must be {expected!r}."
            )
    outputs = contract.get("allowed_outputs")
    if not isinstance(outputs, list) or set(outputs) != REQUIRED_ALLOWED_OUTPUTS:
        raise DiagnosticModeError("Diagnostic checklist allowed_outputs are incomplete.")

    _validate_rules(config.get("allowed_actions"), "allowed_actions")
    _validate_rules(config.get("blocked_actions"), "blocked_actions")

    allowed_ids = {rule["id"] for rule in config["allowed_actions"]}
    blocked_ids = {rule["id"] for rule in config["blocked_actions"]}
    if allowed_ids & blocked_ids:
        raise DiagnosticModeError("Diagnostic checklist cannot allow and block the same rule id.")

    limits = config.get("limits")
    if not isinstance(limits, dict):
        raise DiagnosticModeError("Diagnostic checklist limits must be an object.")
    for field in ("filesystem", "shell", "mcp", "memory", "network", "configuration", "deploy"):
        if not isinstance(limits.get(field), str) or not limits[field].strip():
            raise DiagnosticModeError(f"Diagnostic checklist limit `{field}` is required.")


def evaluate_diagnostic_action(
    action: str,
    *,
    target: str | None = None,
    metadata: Optional[Mapping[str, Any]] = None,
    config: Optional[Mapping[str, Any]] = None,
) -> Dict[str, Any]:
    """Evaluate an action label for Diagnostic Mode without executing it."""
    loaded = dict(config) if config is not None else load_diagnostic_mode_checklist()
    validate_diagnostic_mode_config(loaded)

    original = action if isinstance(action, str) else str(action)
    normalized = _normalize_action(original)
    if not normalized:
        return _decision(
            "UNKNOWN",
            original,
            "Empty actions are not allowed in Diagnostic Mode; unknown policy is BLOCK.",
            "",
            False,
            loaded,
        )

    metadata_map = dict(metadata or {})
    if _metadata_declares_side_effect(metadata_map):
        return _decision(
            "BLOCK",
            original,
            "Metadata declares side effects, so Diagnostic Mode blocks the action.",
            "metadata_side_effect",
            True,
            loaded,
        )

    for rule in loaded["blocked_actions"]:
        if normalized in _normalized_aliases(rule):
            return _decision("BLOCK", original, rule["reason"], rule["id"], True, loaded)

    for rule in loaded["allowed_actions"]:
        if normalized in _normalized_aliases(rule):
            if _requires_mcp_readonly_metadata(rule["id"], metadata_map):
                return _decision(
                    "UNKNOWN",
                    original,
                    "MCP actions require explicit read-only side-effect metadata; unknown policy is BLOCK.",
                    "unknown_action_policy",
                    False,
                    loaded,
                )
            return _decision("ALLOW", original, rule["reason"], rule["id"], False, loaded)

    if target and _looks_mutating_target(str(target)):
        return _decision(
            "BLOCK",
            original,
            "Target indicates a mutating operation, so Diagnostic Mode blocks it.",
            "target_side_effect",
            True,
            loaded,
        )

    return _decision(
        "UNKNOWN",
        original,
        "Action is not classified; Diagnostic Mode unknown policy is BLOCK.",
        "unknown_action_policy",
        False,
        loaded,
    )


def combine_with_dangerous_command_policy(
    diagnostic_decision: Mapping[str, Any],
    command_decision: Mapping[str, Any],
) -> Dict[str, Any]:
    """Return the restrictive Diagnostic Mode view of an existing command decision."""
    status = str(diagnostic_decision.get("status", "UNKNOWN"))
    command_status = str(command_decision.get("status", "UNKNOWN"))
    if status == "BLOCK" or command_status in {"DENY", "WARN"}:
        return _copy_decision(
            diagnostic_decision,
            status="BLOCK",
            reason="Diagnostic Mode uses the most restrictive decision across policies.",
            matched_rule=str(
                diagnostic_decision.get("matched_rule")
                or command_decision.get("matched_pattern")
                or "dangerous_command_policy"
            ),
            side_effect_detected=True,
        )
    if status == "ALLOW" and command_status == "SAFE":
        return _copy_decision(diagnostic_decision)
    return _copy_decision(
        diagnostic_decision,
        status="UNKNOWN",
        reason="At least one policy returned UNKNOWN; Diagnostic Mode consumers must block.",
        matched_rule="unknown_action_policy",
        side_effect_detected=False,
    )


def build_diagnostic_return_envelope(
    *,
    agent: str,
    status: str,
    summary: str,
    evidence: list[Any],
    risks: list[Any],
    recommendation: str,
    needs_followup: bool = False,
) -> Dict[str, Any]:
    envelope = {
        "agent": str(agent),
        "status": str(status),
        "summary": str(summary),
        "evidence": list(evidence),
        "changes": [],
        "risks": list(risks),
        "recommendation": str(recommendation),
        "needs_followup": bool(needs_followup),
    }
    validate_diagnostic_return_envelope(envelope)
    return envelope


def validate_diagnostic_return_envelope(envelope: Any) -> None:
    if not isinstance(envelope, dict):
        raise DiagnosticModeError("Diagnostic return envelope must be an object.")
    if set(envelope) != set(ENVELOPE_FIELDS):
        raise DiagnosticModeError("Diagnostic return envelope fields are not exact.")
    if envelope["status"] not in ALLOWED_ENVELOPE_STATUSES:
        raise DiagnosticModeError("Diagnostic return envelope status is invalid.")
    for field in ("agent", "summary", "recommendation"):
        if not isinstance(envelope[field], str):
            raise DiagnosticModeError(f"Diagnostic return envelope `{field}` must be a string.")
    for field in ("evidence", "changes", "risks"):
        if not isinstance(envelope[field], list):
            raise DiagnosticModeError(f"Diagnostic return envelope `{field}` must be a list.")
    if envelope["changes"] != []:
        raise DiagnosticModeError("Diagnostic Mode return envelope changes must be empty.")
    if envelope["status"] == "PASS" and not envelope["evidence"]:
        raise DiagnosticModeError("Diagnostic Mode PASS requires evidence.")
    if not isinstance(envelope["needs_followup"], bool):
        raise DiagnosticModeError("Diagnostic return envelope needs_followup must be boolean.")


def _validate_rules(rules: Any, field_name: str) -> None:
    if not isinstance(rules, list) or not rules:
        raise DiagnosticModeError(f"Diagnostic checklist `{field_name}` must be a non-empty list.")
    seen_ids: set[str] = set()
    seen_aliases: dict[str, str] = {}
    for rule in rules:
        if not isinstance(rule, dict):
            raise DiagnosticModeError(f"Diagnostic checklist `{field_name}` entries must be objects.")
        if set(rule) != {"id", "aliases", "reason"}:
            raise DiagnosticModeError(
                f"Diagnostic checklist `{field_name}` rule fields are not exact."
            )
        rule_id = rule["id"]
        if not isinstance(rule_id, str) or not rule_id.strip():
            raise DiagnosticModeError(f"Diagnostic checklist `{field_name}` rule id is required.")
        if rule_id in seen_ids:
            raise DiagnosticModeError(f"Duplicate diagnostic checklist rule id: `{rule_id}`.")
        seen_ids.add(rule_id)
        aliases = rule["aliases"]
        if not isinstance(aliases, list) or not aliases:
            raise DiagnosticModeError(f"Diagnostic checklist rule `{rule_id}` aliases are required.")
        rule_aliases: set[str] = set()
        for alias in aliases:
            normalized = _normalize_action(str(alias))
            if not normalized:
                raise DiagnosticModeError(f"Diagnostic checklist rule `{rule_id}` has an empty alias.")
            if normalized in seen_aliases and seen_aliases[normalized] != rule_id:
                raise DiagnosticModeError(f"Duplicate diagnostic checklist alias: `{alias}`.")
            rule_aliases.add(normalized)
        for normalized in rule_aliases:
            seen_aliases[normalized] = rule_id
        if not isinstance(rule["reason"], str) or not rule["reason"].strip():
            raise DiagnosticModeError(f"Diagnostic checklist rule `{rule_id}` reason is required.")


def _decision(
    status: str,
    action: str,
    reason: str,
    matched_rule: str,
    side_effect_detected: bool,
    config: Mapping[str, Any],
) -> Dict[str, Any]:
    if status not in ALLOWED_DECISION_STATUSES:
        raise DiagnosticModeError("Diagnostic decision status is invalid.")
    values = (
        status,
        config["contract"]["mode"],
        config["contract"]["read_only"],
        action,
        reason,
        matched_rule,
        config["contract"]["evidence_required"],
        side_effect_detected,
    )
    return dict(zip(DECISION_FIELDS, values))


def _copy_decision(decision: Mapping[str, Any], **overrides: Any) -> Dict[str, Any]:
    copied = {field: decision.get(field) for field in DECISION_FIELDS}
    copied.update(overrides)
    if copied.get("status") not in ALLOWED_DECISION_STATUSES:
        copied["status"] = "UNKNOWN"
    copied["mode"] = "diagnostic"
    copied["read_only"] = True
    copied["evidence_required"] = True
    return copied


def _normalize_action(value: str) -> str:
    return " ".join(value.strip().lower().replace("_", " ").replace("-", " ").split())


def _normalized_aliases(rule: Mapping[str, Any]) -> set[str]:
    return {_normalize_action(str(alias)) for alias in rule.get("aliases", [])}


def _metadata_declares_side_effect(metadata: Mapping[str, Any]) -> bool:
    return any(
        bool(metadata.get(field))
        for field in (
            "side_effect",
            "writes_files",
            "writes_network",
            "writes_mcp",
            "writes_memory",
            "changes_config",
            "changes_runtime",
            "deploys",
            "auto_fix",
        )
    )


def _requires_mcp_readonly_metadata(rule_id: str, metadata: Mapping[str, Any]) -> bool:
    if not rule_id.startswith("mcp_"):
        return False
    return metadata.get("read_only") is not True


def _looks_mutating_target(target: str) -> bool:
    lowered = target.lower()
    return any(
        token in lowered
        for token in (
            "write",
            "delete",
            "create",
            "modify",
            "deploy",
            "push",
            "commit",
            "install",
            "update",
        )
    )

