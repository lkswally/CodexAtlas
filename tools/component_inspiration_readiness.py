from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

try:
    from tools.creative_pipeline_readiness import check_creative_pipeline_readiness
except ModuleNotFoundError:
    from creative_pipeline_readiness import check_creative_pipeline_readiness


DEFAULT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_RULES = {
    "version": "1.0",
    "advisory_only": True,
    "services": {},
    "profiles": {},
}
SAFE_PROFILE_STATES = {"advisory", "approval_required"}
WATCHLIST_PROFILE_STATES = {"watchlist"}


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _read_json(path: Path) -> Dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def _load_profiles(root: Path) -> Dict[str, Any]:
    path = root / "config" / "component_inspiration_profiles.json"
    if not path.exists():
        return dict(DEFAULT_RULES)
    data = _read_json(path)
    if not isinstance(data, dict):
        return dict(DEFAULT_RULES)
    merged = dict(DEFAULT_RULES)
    merged.update(data)
    if not isinstance(merged.get("services"), dict):
        merged["services"] = {}
    if not isinstance(merged.get("profiles"), dict):
        merged["profiles"] = {}
    return merged


def _service_index(creative_report: Dict[str, Any]) -> Dict[str, Dict[str, Any]]:
    index: Dict[str, Dict[str, Any]] = {}
    for item in list(creative_report.get("available_services", [])) + list(creative_report.get("missing_services", [])):
        if isinstance(item, dict):
            service_id = str(item.get("service", "")).strip()
            if service_id:
                index[service_id] = dict(item)
    return index


def check_component_inspiration_readiness(root: Optional[Path] = None) -> Dict[str, Any]:
    root = (root or DEFAULT_ROOT).resolve()
    rules = _load_profiles(root)
    creative_report = check_creative_pipeline_readiness(root=root)
    creative_service_index = _service_index(creative_report)

    configured_creative_services = {"twentyfirst_magic", "context7"}
    available_services = [
        creative_service_index[service_id]
        for service_id in configured_creative_services
        if service_id in creative_service_index and creative_service_index[service_id].get("available")
    ]
    missing_services = [
        creative_service_index[service_id]
        for service_id in configured_creative_services
        if service_id in creative_service_index and not creative_service_index[service_id].get("available")
    ]

    safe_to_use_profiles: List[Dict[str, Any]] = []
    watchlist_profiles: List[Dict[str, Any]] = []
    blocked_profiles: List[Dict[str, Any]] = []
    required_manual_steps: List[str] = []
    risks: List[str] = []
    requires_human_approval = False
    requires_decision_council = False

    for profile_id, profile in rules.get("profiles", {}).items():
        if not isinstance(profile, dict):
            continue
        profile_name = str(profile_id)
        suggested_services = [str(item).strip() for item in profile.get("suggested_services", []) if str(item).strip()]
        matched = [creative_service_index[item] for item in suggested_services if item in creative_service_index]
        available_matches = [item["service"] for item in matched if item.get("available")]
        missing_env_vars = sorted(
            {
                env_var
                for item in matched
                for env_var in item.get("missing_env_vars", [])
            }
        )
        initial_state = str(profile.get("initial_state", "watchlist")).strip() or "watchlist"
        risk_level = str(profile.get("risk_level", "medium")).strip() or "medium"
        payload = {
            "profile": profile_name,
            "suggested_services": suggested_services,
            "available_services": available_matches,
            "requirements": list(profile.get("requirements", [])),
            "risk_level": risk_level,
            "initial_state": initial_state,
            "requires_human_approval": bool(profile.get("requires_human_approval", True)),
            "fallback": str(profile.get("fallback", "")).strip(),
        }

        if payload["requires_human_approval"]:
            requires_human_approval = True
        if risk_level == "high":
            requires_decision_council = True

        if initial_state in WATCHLIST_PROFILE_STATES:
            payload["why"] = "This profile stays on watchlist until Atlas has explicit approval and a concrete non-generic design need."
            watchlist_profiles.append(payload)
            risks.append(f"{profile_name}_watchlist")
            continue

        if initial_state in SAFE_PROFILE_STATES and available_matches:
            payload["why"] = "A related inspiration service looks locally available, but use remains approval-bound and differentiation-first."
            safe_to_use_profiles.append(payload)
        else:
            payload["missing_env_vars"] = missing_env_vars
            payload["why"] = "Atlas does not see enough local inspiration-readiness evidence for this profile yet."
            blocked_profiles.append(payload)
            if missing_env_vars:
                required_manual_steps.append(
                    f"Set one of {', '.join(missing_env_vars)} locally before enabling `{profile_name}`."
                )

    if any(item.get("service") == "twentyfirst_magic" for item in missing_services):
        required_manual_steps.append(
            "Keep `21st Magic` blocked until a fresh key exists outside the repo and a separate approval allows a controlled test."
        )
    if any(item.get("service") == "context7" for item in missing_services):
        required_manual_steps.append(
            "Keep `Context7` in watchlist until a verified MCP or approved read-only path exists."
        )
    required_manual_steps.append(
        "Use `visual_intent_contract`, `brand_profile_schema` and local design audits first; external inspiration must not replace them."
    )

    required_manual_steps = list(dict.fromkeys(required_manual_steps))
    risks = list(
        dict.fromkeys(
            risks
            + [
                "derivative_component_copy_risk",
                "generic_pattern_overfitting_risk",
                "design_system_dependency_risk",
            ]
        )
    )

    status = "ok" if safe_to_use_profiles else "needs_attention"
    recommended_next_action = (
        "Use external component inspiration only as a constrained input to local design direction, never as a substitute for brand or UI readiness."
        if safe_to_use_profiles
        else "Stay local-first until 21st Magic or Context7 are explicitly approved and locally ready."
    )

    return {
        "status": status,
        "advisory_only": bool(rules.get("advisory_only", True)),
        "available_services": available_services,
        "missing_services": missing_services,
        "safe_to_use_profiles": safe_to_use_profiles,
        "watchlist_profiles": watchlist_profiles,
        "blocked_profiles": blocked_profiles,
        "required_manual_steps": required_manual_steps,
        "risks": risks,
        "requires_human_approval": requires_human_approval,
        "requires_decision_council": requires_decision_council,
        "recommended_next_action": recommended_next_action,
        "why": "Component inspiration readiness is derived from existing creative readiness signals, local MCP/config presence and governed profile metadata.",
        "timestamp": _utc_now_iso(),
    }


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(add_help=True)
    parser.add_argument("--root", default=None, help="Atlas root to use.")
    args = parser.parse_args(argv)
    root = Path(args.root).resolve() if args.root else DEFAULT_ROOT
    result = check_component_inspiration_readiness(root=root)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
