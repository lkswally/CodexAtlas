from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Dict, List, Optional


DEFAULT_ROOT = Path(__file__).resolve().parents[1]
RULES_PATH = Path("config/n8n_api_connector_rules.json")


def load_n8n_api_connector_rules(root: Path = DEFAULT_ROOT) -> Dict[str, Any]:
    return json.loads((root / RULES_PATH).read_text(encoding="utf-8-sig"))


def _normalize(value: Any) -> str:
    return " ".join(str(value or "").strip().lower().split())


def _has_value(value: Any) -> bool:
    if value is None:
        return False
    if isinstance(value, str):
        return bool(value.strip())
    if isinstance(value, (list, tuple, set, dict)):
        return bool(value)
    return True


def _stringify(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, str):
        return value.strip()
    if isinstance(value, (list, tuple, set)):
        return ", ".join(str(item).strip() for item in value if str(item).strip())
    return str(value).strip()


def _listify(value: Any) -> List[str]:
    if isinstance(value, list):
        return [str(item).strip() for item in value if str(item).strip()]
    if isinstance(value, tuple):
        return [str(item).strip() for item in value if str(item).strip()]
    text = _stringify(value)
    return [text] if text else []


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


def _normalize_operation(value: Any, rules: Dict[str, Any]) -> str:
    aliases = {_normalize(alias): canonical for alias, canonical in (rules.get("operation_aliases") or {}).items()}
    requested = _normalize(value) or "list_workflows"
    operation = aliases.get(requested, requested)
    supported = set(rules.get("supported_operations", []))
    return operation if operation in supported else "list_workflows"


def _contains_sandbox_tag(tags: List[str], rules: Dict[str, Any]) -> bool:
    signals = {_normalize(item) for item in rules.get("sandbox_tag_signals", []) if _normalize(item)}
    normalized_tags = {_normalize(tag) for tag in tags if _normalize(tag)}
    return bool(signals & normalized_tags)


def assess_n8n_api_connector_readiness(
    payload: Dict[str, Any],
    *,
    root: Path = DEFAULT_ROOT,
    project: Optional[Path] = None,
) -> Dict[str, Any]:
    del project
    root = root.resolve()
    rules = load_n8n_api_connector_rules(root)
    extracted = _extract_inputs(payload, rules)

    base_url = _stringify(extracted.get("n8n_base_url"))
    base_url_configured = bool(base_url) or bool(extracted.get("base_url_configured", False))
    requested_operation = _normalize_operation(extracted.get("requested_operation"), rules)
    read_only_operations = list(rules.get("read_only_operations", []))
    write_operations = list(rules.get("write_operations", []))
    blocked_operations = list(rules.get("blocked_operations", []))
    production_blocked_operations = set(rules.get("production_blocked_operations", []))

    api_key_required = bool(rules.get("api_key_required", True))
    api_key_read = False
    allow_execute = False
    allow_write_requested = bool(extracted.get("allow_write", False))
    explicit_human_approval = bool(extracted.get("explicit_human_approval", False))
    dry_run_available = bool(extracted.get("dry_run_available", False))
    rollback_available = bool(extracted.get("rollback_available", False))
    workflow_active = bool(extracted.get("workflow_active", False))
    production_target = bool(extracted.get("production_target", False))
    webhook_production_url = bool(extracted.get("webhook_production_url", False))
    sandbox_tags = _listify(extracted.get("sandbox_tags"))
    sandbox_tag_present = bool(extracted.get("sandbox_tag_present", False)) or _contains_sandbox_tag(sandbox_tags, rules)

    effective_allow_write = False
    connection_mode = "not_configured"
    blocked_reasons: List[str] = []
    warnings: List[str] = []

    if not base_url_configured:
        blocked_reasons.append("n8n_base_url_not_configured")
    else:
        connection_mode = "read_only_ready"

    if bool(extracted.get("allow_execute", False)):
        blocked_reasons.append("allow_execute_must_remain_false")
    if requested_operation == "execute_workflow":
        blocked_reasons.append("execute_workflow_blocked")
    if requested_operation == "activate_workflow":
        blocked_reasons.append("activate_workflow_blocked")
    if requested_operation == "read_credentials":
        blocked_reasons.append("credentials_access_blocked")
    if requested_operation in {"delete_workflow"}:
        blocked_reasons.append("delete_workflow_blocked")

    if webhook_production_url:
        warnings.append("production_webhook_url_requires_human_approval")

    if requested_operation in production_blocked_operations or production_target:
        blocked_reasons.append("production_write_blocked")

    if allow_write_requested or requested_operation in write_operations:
        if not base_url_configured:
            connection_mode = "not_configured"
        elif requested_operation in production_blocked_operations or production_target:
            connection_mode = "blocked"
        elif not sandbox_tag_present:
            connection_mode = "blocked"
            blocked_reasons.append("sandbox_tag_required_for_write")
        elif not explicit_human_approval:
            connection_mode = "blocked"
            blocked_reasons.append("human_approval_required_for_write")
        elif workflow_active:
            connection_mode = "blocked"
            blocked_reasons.append("workflow_must_remain_inactive")
        elif requested_operation not in write_operations:
            connection_mode = "blocked"
            blocked_reasons.append("requested_operation_not_write_safe")
        else:
            connection_mode = "sandbox_write_ready"
            effective_allow_write = True
            if not rollback_available:
                warnings.append("rollback_not_declared_for_future_write")
            if not dry_run_available:
                warnings.append("dry_run_not_declared_for_future_write")

    if requested_operation in blocked_operations:
        connection_mode = "blocked" if base_url_configured else connection_mode

    allowed_operations: List[str] = []
    if base_url_configured:
        allowed_operations.extend(read_only_operations)
        if connection_mode == "sandbox_write_ready":
            allowed_operations.extend(operation for operation in write_operations if operation not in allowed_operations)

    final_blocked_operations = [
        operation
        for operation in rules.get("supported_operations", [])
        if operation not in allowed_operations
    ]

    next_safe_step = str(
        rules.get("next_safe_steps", {}).get(connection_mode)
        or rules.get("next_safe_steps", {}).get("default")
        or "Keep the connector advisory-only until manual configuration is reviewed."
    ).strip()

    return {
        "status": "ok",
        "n8n_api_connector_posture": {
            "connection_mode": connection_mode,
            "base_url_configured": base_url_configured,
            "api_key_required": api_key_required,
            "api_key_read": api_key_read,
            "allow_write": effective_allow_write,
            "allow_execute": allow_execute,
            "sandbox_required": True,
            "requested_operation": requested_operation,
            "sandbox_tag_present": sandbox_tag_present,
            "allowed_operations": allowed_operations,
            "blocked_operations": final_blocked_operations,
            "human_approval_required": True,
            "blocked_reasons": list(dict.fromkeys(reason for reason in blocked_reasons if reason)),
            "warnings": list(dict.fromkeys(warning for warning in warnings if warning)),
            "next_safe_step": next_safe_step,
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

    result = assess_n8n_api_connector_readiness(payload, root=DEFAULT_ROOT)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
