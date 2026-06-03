from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Dict, List, Optional

try:
    from tools.mcp_readiness_check import check_mcp_readiness
except ModuleNotFoundError:
    from mcp_readiness_check import check_mcp_readiness


DEFAULT_ROOT = Path(__file__).resolve().parents[1]
RULES_PATH = Path("config/mcp_permission_matrix_rules.json")


def load_mcp_permission_matrix_rules(root: Path = DEFAULT_ROOT) -> Dict[str, Any]:
    return json.loads((root / RULES_PATH).read_text(encoding="utf-8-sig"))


def _normalize(value: Any) -> str:
    return " ".join(str(value or "").strip().lower().split())


def _flatten_text(value: Any) -> List[str]:
    values: List[str] = []
    if isinstance(value, dict):
        for nested in value.values():
            values.extend(_flatten_text(nested))
    elif isinstance(value, list):
        for nested in value:
            values.extend(_flatten_text(nested))
    else:
        text = str(value or "").strip()
        if text:
            values.append(text)
    return values


def _normalize_platform(value: Any, rules: Dict[str, Any]) -> str:
    platform = _normalize(value) or "generic_mcp"
    aliases = {_normalize(alias): canonical for alias, canonical in (rules.get("platform_aliases") or {}).items()}
    supported = {_normalize(item) for item in rules.get("supported_platforms", [])}
    normalized = aliases.get(platform, platform)
    if normalized not in supported:
        return "generic_mcp"
    return normalized


def _normalize_capability(value: Any, rules: Dict[str, Any]) -> str:
    capability = _normalize(value) or "read_only"
    aliases = {_normalize(alias): canonical for alias, canonical in (rules.get("capability_aliases") or {}).items()}
    supported = {_normalize(item) for item in rules.get("capability_levels", [])}
    normalized = aliases.get(capability, capability)
    if normalized not in supported:
        return "read_only"
    return normalized


def _bool_from_payload(payload: Dict[str, Any], *keys: str) -> bool:
    for key in keys:
        if key in payload:
            value = payload.get(key)
            if isinstance(value, bool):
                return value
            if isinstance(value, str):
                if _normalize(value) in {"true", "yes", "1"}:
                    return True
                if _normalize(value) in {"false", "no", "0"}:
                    return False
            if value is not None:
                return bool(value)
    return False


def _is_within(base: Path, candidate: Path) -> bool:
    try:
        candidate.relative_to(base)
        return True
    except ValueError:
        return False


def _risk_rank(value: str) -> int:
    return {"low": 1, "medium": 2, "high": 3}.get(_normalize(value), 1)


def _risk_label(rank: int) -> str:
    if rank >= 3:
        return "high"
    if rank == 2:
        return "medium"
    return "low"


def assess_mcp_permission_matrix_readiness(
    payload: Dict[str, Any],
    *,
    root: Path = DEFAULT_ROOT,
    project: Optional[Path] = None,
) -> Dict[str, Any]:
    root = root.resolve()
    project = (project or root).resolve()
    rules = load_mcp_permission_matrix_rules(root)
    mcp_readiness = check_mcp_readiness(root=root)

    platform = _normalize_platform(payload.get("platform"), rules)
    capability = _normalize_capability(payload.get("requested_capability"), rules)
    platform_defaults = (rules.get("platform_defaults") or {}).get(platform, {})

    default_risk_rank = _risk_rank(str(platform_defaults.get("default_risk", "medium")))
    risk_rank = default_risk_rank
    recommended_mode = str(platform_defaults.get("recommended_mode", "read_only")).strip() or "read_only"

    blocked_reasons: List[str] = []
    privacy_warnings: List[str] = []
    next_safe_steps = platform_defaults.get("next_safe_steps") or {}
    next_safe_step = str(next_safe_steps.get(recommended_mode) or next_safe_steps.get("read_only") or "").strip()

    surface = " ".join(_flatten_text(payload))
    normalized_surface = _normalize(surface)

    sensitive_data_detected = _bool_from_payload(payload, "has_sensitive_data", "contains_sensitive_data") or any(
        _normalize(signal) in normalized_surface for signal in rules.get("sensitive_data_signals", [])
    )
    credentials_detected = _bool_from_payload(payload, "uses_credentials", "has_credentials") or any(
        _normalize(signal) in normalized_surface for signal in rules.get("credential_signals", [])
    )
    side_effect_signals_detected = any(
        _normalize(signal) in normalized_surface for signal in rules.get("side_effect_action_signals", [])
    )

    human_approval_required = capability in {
        _normalize(item) for item in rules.get("human_approval_required_for", [])
    }
    explicit_human_approval = _bool_from_payload(
        payload,
        "human_approval_granted",
        "has_human_approval",
        "approval_granted",
    )
    dry_run_required = capability in {_normalize(item) for item in rules.get("dry_run_required_for", [])}
    rollback_required = capability in {_normalize(item) for item in rules.get("rollback_required_for", [])}
    dry_run_available = _bool_from_payload(payload, "dry_run_available", "has_dry_run", "supports_dry_run")
    rollback_available = _bool_from_payload(payload, "rollback_available", "has_rollback", "supports_rollback")

    allowed = bool(platform_defaults.get(f"allow_{capability}", capability == "read_only"))

    if capability in {_normalize(item) for item in rules.get("blocked_by_default", [])}:
        allowed = False
        blocked_reasons.append(f"{capability}_blocked_by_default")

    if capability == "sandbox_write" and not explicit_human_approval:
        allowed = False
        blocked_reasons.append("sandbox_write_requires_explicit_human_approval")

    if rollback_required and not rollback_available:
        allowed = False
        blocked_reasons.append("rollback_required_before_write_or_execute")

    if dry_run_required and not dry_run_available:
        allowed = False
        blocked_reasons.append("dry_run_required_before_production_or_execute")

    if platform == "gmail" and capability == "execute":
        allowed = False
        blocked_reasons.append("real_email_send_blocked_by_default")
    if platform == "n8n" and capability in {"production_write", "execute"}:
        allowed = False
        blocked_reasons.append("workflow_activation_or_live_mutation_blocked_by_default")
    if platform == "google_sheets" and capability in {"production_write", "execute"}:
        allowed = False
        blocked_reasons.append("sheet_write_or_execute_blocked_by_default")
    if platform == "database" and capability in {"production_write", "execute"}:
        allowed = False
        blocked_reasons.append("database_write_or_execute_blocked_by_default")
    if platform == "vercel" and capability in {"production_write", "execute"}:
        allowed = False
        blocked_reasons.append("deploy_or_execute_blocked_by_default")

    if platform == "filesystem" and capability in {"sandbox_write", "production_write"}:
        target_path_value = payload.get("target_path")
        if target_path_value:
            target_path = Path(str(target_path_value)).resolve()
            if not (_is_within(project, target_path) or _is_within(root, target_path)):
                allowed = False
                blocked_reasons.append("filesystem_write_outside_governed_workspace_blocked")
                next_safe_step = "Restrict writes to the governed workspace or a sandbox directory only."

    if sensitive_data_detected:
        risk_rank = max(risk_rank, 3 if capability != "read_only" else 2)
        if capability != "read_only":
            blocked_reasons.append("sensitive_data_requires_read_only_or_additional_review")
    if credentials_detected:
        risk_rank = max(risk_rank, 3 if capability != "read_only" else 2)
        if capability in {"sandbox_write", "production_write", "execute"}:
            blocked_reasons.append("credential_bound_mutation_requires_explicit_human_review")
    if side_effect_signals_detected and capability in {"draft_only", "sandbox_write"}:
        risk_rank = max(risk_rank, 3)

    if platform == "chrome_devtools":
        risk_rank = max(risk_rank, 2)
        privacy_warnings.extend(
            [
                "Chrome DevTools MCP may expose browser profile or session context.",
                "Prefer --no-usage-statistics if configured manually later.",
            ]
        )
        if capability == "read_only":
            allowed = True
            next_safe_step = next_safe_step or "Use manual opt-in browser inspection only after human approval."

    if capability == "read_only" and not sensitive_data_detected and not credentials_detected:
        recommended_mode = "read_only"
    elif capability in {"production_write", "execute"} or sensitive_data_detected or credentials_detected:
        recommended_mode = "read_only"
    elif capability == "sandbox_write":
        recommended_mode = "draft_only"

    if not next_safe_step:
        if recommended_mode == "read_only":
            next_safe_step = "Start with read-only inspection until a safer platform-specific path is approved."
        elif recommended_mode == "draft_only":
            next_safe_step = "Prepare a draft or offline artifact for human review first."
        else:
            next_safe_step = "Keep this capability blocked until approval, dry-run and rollback requirements are satisfied."

    posture = {
        "platform": platform,
        "requested_capability": capability,
        "allowed": allowed,
        "recommended_mode": recommended_mode,
        "risk_level": _risk_label(risk_rank),
        "human_approval_required": human_approval_required or side_effect_signals_detected or platform == "chrome_devtools",
        "dry_run_required": dry_run_required,
        "rollback_required": rollback_required,
        "blocked_reasons": list(dict.fromkeys(reason for reason in blocked_reasons if reason)),
        "next_safe_step": next_safe_step,
        "sensitive_data_detected": sensitive_data_detected,
        "credentials_detected": credentials_detected,
        "privacy_warnings": list(dict.fromkeys(privacy_warnings)),
        "configured_mcp_servers": mcp_readiness.get("configured_mcp_servers", []),
        "mcp_readiness_state": mcp_readiness.get("readiness_state"),
        "advisory_only": bool(rules.get("advisory_only", True)),
    }

    return {
        "status": "ok",
        "mcp_permission_posture": posture,
        "advisory_only": bool(rules.get("advisory_only", True)),
    }


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(add_help=True)
    parser.add_argument("--project", default=None)
    parser.add_argument("--platform", default="generic_mcp")
    parser.add_argument("--capability", default="read_only")
    parser.add_argument("--payload-json", default=None)
    args = parser.parse_args(argv)

    payload = {"platform": args.platform, "requested_capability": args.capability}
    if args.payload_json:
        payload.update(json.loads(args.payload_json))
    project = Path(args.project).resolve() if args.project else DEFAULT_ROOT
    result = assess_mcp_permission_matrix_readiness(payload, root=DEFAULT_ROOT, project=project)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
