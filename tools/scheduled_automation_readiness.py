from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Dict, List, Optional


DEFAULT_ROOT = Path(__file__).resolve().parents[1]
RULES_PATH = Path("config/scheduled_automation_rules.json")


def load_scheduled_automation_rules(root: Path = DEFAULT_ROOT) -> Dict[str, Any]:
    return json.loads((root / RULES_PATH).read_text(encoding="utf-8-sig"))


def _normalize(value: Any) -> str:
    return " ".join(str(value or "").strip().lower().split())


def _stringify(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, str):
        return value.strip()
    if isinstance(value, (list, tuple, set)):
        return ", ".join(str(item).strip() for item in value if str(item).strip())
    if isinstance(value, dict):
        return ", ".join(f"{key}: {value[key]}" for key in value if str(value[key]).strip())
    return str(value).strip()


def _has_value(value: Any) -> bool:
    if value is None:
        return False
    if isinstance(value, str):
        return bool(value.strip())
    if isinstance(value, (list, tuple, set, dict)):
        return bool(value)
    return True


def _extract_inputs(payload: Dict[str, Any], rules: Dict[str, Any]) -> Dict[str, Any]:
    aliases = rules.get("input_aliases", {})
    extracted: Dict[str, Any] = {}
    for canonical in aliases:
        candidates = [canonical, *list(aliases.get(canonical, []))]
        for name in candidates:
            value = payload.get(name)
            if _has_value(value):
                extracted[canonical] = value
                break
    return extracted


def _bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    normalized = _normalize(value)
    if normalized in {"true", "yes", "1"}:
        return True
    if normalized in {"false", "no", "0", ""}:
        return False
    return bool(value)


def _contains_any(surface: str, terms: List[str]) -> List[str]:
    normalized_surface = _normalize(surface)
    return [term for term in terms if _normalize(term) and _normalize(term) in normalized_surface]


def _detect_schedule_type(requested_schedule: str, rules: Dict[str, Any]) -> str:
    aliases = {_normalize(alias): canonical for alias, canonical in (rules.get("schedule_type_aliases") or {}).items()}
    requested = _normalize(requested_schedule)
    if requested in aliases:
        return aliases[requested]
    if "week" in requested:
        return "weekly"
    if "month" in requested:
        return "monthly"
    if "day" in requested or "daily" in requested:
        return "daily"
    if "event" in requested or "webhook" in requested:
        return "event_based"
    return "unknown"


def assess_scheduled_automation_readiness(
    payload: Dict[str, Any],
    *,
    root: Path = DEFAULT_ROOT,
    project: Optional[Path] = None,
) -> Dict[str, Any]:
    del project
    root = root.resolve()
    rules = load_scheduled_automation_rules(root)
    extracted = _extract_inputs(payload, rules)

    task_description = _stringify(extracted.get("task_description") or payload.get("task_description"))
    requested_schedule = _stringify(extracted.get("requested_schedule") or payload.get("requested_schedule"))
    task_type = _normalize(extracted.get("task_type") or payload.get("task_type") or "unknown")
    surface = " ".join(
        part for part in [task_description, requested_schedule, task_type, _stringify(payload)] if part
    )
    normalized_surface = _normalize(surface)

    schedule_type = _detect_schedule_type(requested_schedule, rules)

    requires_external_service = _bool(extracted.get("requires_external_service")) or bool(
        _contains_any(surface, list(rules.get("external_service_terms", [])))
    )
    requires_credentials = _bool(extracted.get("requires_credentials")) or bool(
        _contains_any(surface, list(rules.get("credential_terms", [])))
    )
    touches_sensitive_data = _bool(extracted.get("touches_sensitive_data")) or bool(
        _contains_any(surface, list(rules.get("sensitive_data_terms", [])))
    )
    writes_data = _bool(extracted.get("writes_data")) or bool(
        _contains_any(surface, list(rules.get("write_terms", [])))
    )
    sends_notifications = _bool(extracted.get("sends_notifications")) or (
        "email" in normalized_surface or "send" in normalized_surface
    )
    deletes_data = _bool(extracted.get("deletes_data")) or bool(
        _contains_any(surface, list(rules.get("delete_terms", [])))
    )
    modifies_code = _bool(extracted.get("modifies_code")) or (
        "code" in normalized_surface and "modify" in normalized_surface
    )
    recursive_risk = _bool(extracted.get("recursive_risk")) or bool(
        _contains_any(surface, list(rules.get("recursion_terms", [])))
    )
    auto_mutating = _bool(extracted.get("auto_mutating")) or bool(
        _contains_any(surface, list(rules.get("auto_mutation_terms", [])))
    )
    n8n_execute_requested = _bool(extracted.get("n8n_execute_requested")) or (
        "n8n" in normalized_surface
        and bool(_contains_any(surface, ["execute workflow", "activate workflow", "run workflow"]))
    )
    production_target = _bool(extracted.get("production_target")) or "production" in normalized_surface
    sandbox_target = _bool(extracted.get("sandbox_target")) or "sandbox" in normalized_surface
    dry_run_available = _bool(extracted.get("dry_run_available"))
    rollback_available = _bool(extracted.get("rollback_available"))
    explicit_human_approval = _bool(extracted.get("explicit_human_approval"))

    reminder_hits = _contains_any(surface, list(rules.get("manual_reminder_terms", [])))
    report_hits = _contains_any(surface, list(rules.get("report_terms", [])))

    has_side_effects = writes_data or sends_notifications or deletes_data or modifies_code or n8n_execute_requested
    blocked_operations: List[str] = []
    risks: List[str] = []

    if recursive_risk:
        blocked_operations.append("recursive_scheduling")
        risks.append("recursive_or_self_triggering_schedule")
    if auto_mutating:
        blocked_operations.append("auto_mutating_behavior")
        risks.append("self_modifying_or_self_improving_behavior")
    if n8n_execute_requested:
        blocked_operations.extend(["execute_workflow", "activate_workflow"])
        risks.append("n8n_runtime_execution_blocked")
    if modifies_code:
        blocked_operations.append("auto_modify_code")
        risks.append("scheduled_code_mutation_blocked")
    if deletes_data:
        blocked_operations.append("delete_data")
        risks.append("destructive_side_effect")
    if requires_credentials:
        risks.append("credentials_or_secrets_required")
    if touches_sensitive_data:
        risks.append("sensitive_data_in_scope")
    if production_target and not sandbox_target:
        blocked_operations.append("production_write")
        risks.append("production_without_sandbox")

    blocked = bool(blocked_operations)
    if writes_data and not sandbox_target:
        blocked = True
        blocked_operations.append("write_without_sandbox")
        risks.append("write_path_not_sandboxed")
    if writes_data and not rollback_available:
        blocked = True
        blocked_operations.append("write_without_rollback")
        risks.append("rollback_missing")
    if writes_data and not dry_run_available:
        blocked = True
        blocked_operations.append("write_without_dry_run")
        risks.append("dry_run_missing")
    if sends_notifications and not explicit_human_approval:
        blocked = True
        blocked_operations.append("notification_without_approval")
        risks.append("outbound_notification_requires_approval")

    if blocked:
        recommended_state = "blocked"
    elif reminder_hits and not requires_external_service and not has_side_effects:
        recommended_state = "manual_reminder_ready"
    elif writes_data and sandbox_target and dry_run_available and rollback_available and explicit_human_approval:
        recommended_state = "sandbox_ready"
    elif report_hits and requires_external_service and not has_side_effects and dry_run_available and not requires_credentials:
        recommended_state = "dry_run_ready"
    elif requires_credentials or touches_sensitive_data or sends_notifications or requires_external_service:
        recommended_state = "manual_review_only"
    else:
        recommended_state = "watchlist"

    human_approval_required = bool(
        recommended_state in {"manual_review_only", "sandbox_ready", "blocked"}
        or has_side_effects
        or requires_credentials
        or touches_sensitive_data
    )
    dry_run_required = bool(requires_external_service or has_side_effects or writes_data)
    rollback_required = bool(writes_data or deletes_data)

    next_safe_steps = rules.get("next_safe_steps", {})
    recommended_next_steps = [
        str(next_safe_steps.get(recommended_state) or next_safe_steps.get("watchlist") or "").strip()
    ]
    if requires_external_service and recommended_state != "blocked":
        recommended_next_steps.append("Keep external reads read-only and document the preview output before any runtime integration.")
    if writes_data and recommended_state != "blocked":
        recommended_next_steps.append("Keep any future write path sandbox-only with explicit approval, dry-run evidence and rollback notes.")
    if requires_credentials:
        recommended_next_steps.append("Do not bind credentials until a separate connector readiness layer is approved.")
    if n8n_execute_requested:
        recommended_next_steps.append("Use workflow JSON export or readiness review instead of scheduled execution.")

    return {
        "status": "ok",
        "scheduled_automation_posture": {
            "recommended_state": recommended_state,
            "schedule_type": schedule_type,
            "task_type": task_type or "unknown",
            "requires_credentials": requires_credentials,
            "requires_external_service": requires_external_service,
            "touches_sensitive_data": touches_sensitive_data,
            "has_side_effects": has_side_effects,
            "human_approval_required": human_approval_required,
            "dry_run_required": dry_run_required,
            "dry_run_available": dry_run_available,
            "rollback_required": rollback_required,
            "rollback_available": rollback_available,
            "sandbox_target": sandbox_target,
            "production_target": production_target,
            "blocked_operations": list(dict.fromkeys(item for item in blocked_operations if item)),
            "risks": list(dict.fromkeys(item for item in risks if item)),
            "recommended_next_steps": list(dict.fromkeys(item for item in recommended_next_steps if item)),
            "advisory_only": bool(rules.get("advisory_only", True)),
        },
        "advisory_only": bool(rules.get("advisory_only", True)),
    }


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(add_help=True)
    parser.add_argument("--payload-json", default=None)
    args = parser.parse_args(argv)

    payload: Dict[str, Any] = {}
    if args.payload_json:
        payload.update(json.loads(args.payload_json))

    result = assess_scheduled_automation_readiness(payload, root=DEFAULT_ROOT)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
