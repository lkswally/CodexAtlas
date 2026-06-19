from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any, Dict, Mapping, Optional


DEFAULT_PATTERNS_PATH = (
    Path(__file__).resolve().parents[1] / "config" / "dangerous_command_patterns.json"
)
ALLOWED_STATUSES = {"SAFE", "WARN", "DENY"}
OUTPUT_FIELDS = (
    "command",
    "status",
    "category",
    "reason",
    "matched_pattern",
    "requires_human_approval",
    "confidence",
)


class DangerousCommandPolicyError(ValueError):
    """Raised when the declarative policy configuration is unusable."""


def load_dangerous_command_patterns(
    path: Path = DEFAULT_PATTERNS_PATH,
) -> Dict[str, Any]:
    try:
        config = json.loads(Path(path).read_text(encoding="utf-8"))
    except OSError as exc:
        raise DangerousCommandPolicyError(f"Could not read command policy: `{path}`.") from exc
    except json.JSONDecodeError as exc:
        raise DangerousCommandPolicyError(f"Command policy is not valid JSON: `{path}`.") from exc
    _validate_config(config)
    return config


def _validate_config(config: Any) -> None:
    if not isinstance(config, dict):
        raise DangerousCommandPolicyError("Command policy must be a JSON object.")
    if config.get("status_order") != ["DENY", "WARN", "SAFE"]:
        raise DangerousCommandPolicyError("Command policy status_order must be DENY, WARN, SAFE.")
    categories = config.get("categories")
    rules = config.get("rules")
    if not isinstance(categories, dict) or not categories:
        raise DangerousCommandPolicyError("Command policy categories must be a non-empty object.")
    if not isinstance(rules, list) or not rules:
        raise DangerousCommandPolicyError("Command policy rules must be a non-empty array.")

    required = {"id", "status", "category", "pattern", "reason", "confidence"}
    seen_ids = set()
    for rule in rules:
        if not isinstance(rule, dict) or not required.issubset(rule):
            raise DangerousCommandPolicyError("Every command policy rule is incomplete.")
        if rule["id"] in seen_ids:
            raise DangerousCommandPolicyError(f"Duplicate command policy rule id: `{rule['id']}`.")
        seen_ids.add(rule["id"])
        if rule["status"] not in ALLOWED_STATUSES:
            raise DangerousCommandPolicyError(f"Invalid status for rule `{rule['id']}`.")
        if rule["category"] not in categories:
            raise DangerousCommandPolicyError(f"Unknown category for rule `{rule['id']}`.")
        if not isinstance(rule["reason"], str) or not rule["reason"].strip():
            raise DangerousCommandPolicyError(f"Missing reason for rule `{rule['id']}`.")
        if not isinstance(rule["confidence"], (int, float)) or not 0 <= rule["confidence"] <= 1:
            raise DangerousCommandPolicyError(f"Invalid confidence for rule `{rule['id']}`.")
        try:
            re.compile(rule["pattern"], re.IGNORECASE)
        except (re.error, TypeError) as exc:
            raise DangerousCommandPolicyError(
                f"Invalid regular expression for rule `{rule['id']}`."
            ) from exc


def _result(
    command: str,
    status: str,
    *,
    category: str = "",
    reason: str = "",
    matched_pattern: str = "",
    confidence: float = 0.0,
) -> Dict[str, Any]:
    values = (
        command,
        status,
        category,
        reason,
        matched_pattern,
        status != "SAFE",
        float(confidence),
    )
    return dict(zip(OUTPUT_FIELDS, values))


def classify_command(
    command: str,
    *,
    config: Optional[Mapping[str, Any]] = None,
) -> Dict[str, Any]:
    """Classify one command without executing or modifying it."""
    original = command if isinstance(command, str) else str(command)
    normalized = original.strip()
    if not normalized:
        return _result(
            original,
            "UNKNOWN",
            reason="Empty commands are not recognized as safe.",
        )

    loaded = config if config is not None else load_dangerous_command_patterns()
    _validate_config(loaded)
    for status in loaded["status_order"]:
        for rule in loaded["rules"]:
            if rule["status"] == status and re.search(
                rule["pattern"], normalized, re.IGNORECASE
            ):
                return _result(
                    original,
                    status,
                    category=rule["category"],
                    reason=rule["reason"],
                    matched_pattern=rule["id"],
                    confidence=rule["confidence"],
                )

    return _result(
        original,
        "UNKNOWN",
        reason="No configured rule recognizes this command; UNKNOWN is never assumed safe.",
    )
