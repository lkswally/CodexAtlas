from __future__ import annotations

import argparse
import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

try:
    from tools.mcp_readiness_check import check_mcp_readiness
except ModuleNotFoundError:
    from mcp_readiness_check import check_mcp_readiness


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
    path = root / "config" / "creative_pipeline_profiles.json"
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


def _load_atlas_mcp_profiles(root: Path) -> Dict[str, Any]:
    path = root / "config" / "mcp_profiles.json"
    if not path.exists():
        return {}
    data = _read_json(path)
    if not isinstance(data, dict):
        return {}
    profiles = data.get("profiles", {})
    return profiles if isinstance(profiles, dict) else {}


def _service_snapshot(
    *,
    service_id: str,
    service: Dict[str, Any],
    configured_mcp_servers: List[str],
    atlas_mcp_profiles: Dict[str, Any],
) -> Dict[str, Any]:
    expected_env_vars = [
        str(item).strip() for item in service.get("expected_env_vars", []) if str(item).strip()
    ]
    related_mcp_servers = [
        str(item).strip() for item in service.get("related_mcp_servers", []) if str(item).strip()
    ]
    atlas_profile_names = [
        str(item).strip() for item in service.get("atlas_mcp_profiles", []) if str(item).strip()
    ]

    env_vars_present = [name for name in expected_env_vars if bool(os.getenv(name))]
    configured_related_servers = [
        name for name in related_mcp_servers if name in configured_mcp_servers
    ]
    present_atlas_profiles = [
        name for name in atlas_profile_names if name in atlas_mcp_profiles
    ]
    available = bool(env_vars_present or configured_related_servers)

    return {
        "service": service_id,
        "display_name": str(service.get("display_name", service_id)).strip() or service_id,
        "purpose": str(service.get("purpose", "")).strip(),
        "risk_level": str(service.get("risk_level", "medium")).strip() or "medium",
        "expected_env_vars": expected_env_vars,
        "env_vars_present": env_vars_present,
        "missing_env_vars": [name for name in expected_env_vars if name not in env_vars_present],
        "related_mcp_servers": related_mcp_servers,
        "configured_related_mcp_servers": configured_related_servers,
        "atlas_mcp_profiles": atlas_profile_names,
        "atlas_mcp_profiles_present": present_atlas_profiles,
        "available": available,
        "availability_reason": (
            "env_or_mcp_present"
            if available
            else "no_expected_env_or_related_mcp_detected"
        ),
    }


def _profile_service_matches(
    *,
    profile: Dict[str, Any],
    service_index: Dict[str, Dict[str, Any]],
) -> List[Dict[str, Any]]:
    matched: List[Dict[str, Any]] = []
    for service_id in profile.get("suggested_services", []):
        service_key = str(service_id).strip()
        if service_key and service_key in service_index:
            matched.append(service_index[service_key])
    return matched


def check_creative_pipeline_readiness(root: Optional[Path] = None) -> Dict[str, Any]:
    root = (root or DEFAULT_ROOT).resolve()
    rules = _load_profiles(root)
    atlas_mcp_profiles = _load_atlas_mcp_profiles(root)
    mcp_readiness = check_mcp_readiness(root=root)
    configured_mcp_servers = list(mcp_readiness.get("configured_mcp_servers", []))

    services = rules.get("services", {})
    service_index: Dict[str, Dict[str, Any]] = {}
    for service_id, service in services.items():
        if not isinstance(service, dict):
            continue
        service_index[str(service_id)] = _service_snapshot(
            service_id=str(service_id),
            service=service,
            configured_mcp_servers=configured_mcp_servers,
            atlas_mcp_profiles=atlas_mcp_profiles,
        )

    available_services = [item for item in service_index.values() if item["available"]]
    missing_services = [item for item in service_index.values() if not item["available"]]

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
        matched_services = _profile_service_matches(profile=profile, service_index=service_index)
        available_matches = [item["service"] for item in matched_services if item.get("available")]
        missing_env_vars = sorted(
            {
                env_var
                for service in matched_services
                for env_var in service.get("missing_env_vars", [])
            }
        )
        initial_state = str(profile.get("initial_state", "watchlist")).strip() or "watchlist"
        risk_level = str(profile.get("risk_level", "medium")).strip() or "medium"
        payload = {
            "profile": profile_name,
            "suggested_services": [item["service"] for item in matched_services],
            "available_services": available_matches,
            "requirements": list(profile.get("requirements", [])),
            "risk_level": risk_level,
            "initial_state": initial_state,
            "requires_human_approval": bool(profile.get("requires_human_approval", True)),
        }

        if risk_level == "high":
            requires_decision_council = True
        if payload["requires_human_approval"]:
            requires_human_approval = True

        if initial_state in WATCHLIST_PROFILE_STATES:
            payload["why"] = (
                "This profile stays on watchlist until Atlas receives explicit approval and a concrete derived-project need."
            )
            watchlist_profiles.append(payload)
            if profile_name == "visual_qa_watchlist":
                risks.append("playwright_visual_qa_watchlist")
            if profile_name == "video_generation":
                risks.append("video_generation_high_runtime_risk")
            if profile_name == "component_inspiration":
                risks.append("component_inspiration_external_tool_risk")
            continue

        if initial_state in SAFE_PROFILE_STATES and available_matches:
            payload["why"] = (
                "Prerequisites look locally present, but this profile still requires explicit human approval before any real asset work."
            )
            safe_to_use_profiles.append(payload)
        else:
            payload["missing_env_vars"] = missing_env_vars
            payload["why"] = "Atlas does not see enough local readiness evidence for this profile yet."
            blocked_profiles.append(payload)
            if missing_env_vars:
                required_manual_steps.append(
                    f"Set one of {', '.join(missing_env_vars)} locally before enabling `{profile_name}`."
                )

    if any(item["service"] == "twentyfirst_magic" and not item["available"] for item in missing_services):
        required_manual_steps.append(
            "Keep `21st Magic` blocked until a fresh key exists outside the repo and a separate approval allows a controlled test."
        )
    if any(item["service"] == "context7" and not item["available"] for item in missing_services):
        required_manual_steps.append(
            "Keep `Context7` in watchlist until a verified MCP or approved read-only path exists."
        )
    if "playwright_visual_qa" in service_index:
        required_manual_steps.append(
            "Treat browser-driven visual QA as watchlist until a separate readiness review approves screenshot automation."
        )

    required_manual_steps = list(dict.fromkeys(required_manual_steps))
    risks = list(
        dict.fromkeys(
            risks
            + [
                "derivative_logo_or_brand_risk",
                "unclear_asset_ownership_risk",
                "external_generation_without_visual_intent_or_brand_profile",
            ]
        )
    )

    status = "ok" if safe_to_use_profiles else "needs_attention"
    recommended_next_action = (
        "Use local design audits first, and approve only one concrete creative profile at a time for a derived project."
        if safe_to_use_profiles
        else "Keep creative work in readiness mode until a concrete derived-project need and approved provider path exist."
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
        "related_mcp_servers": configured_mcp_servers,
        "recommended_next_action": recommended_next_action,
        "why": "Creative readiness is derived only from local env-var presence, current MCP readiness, Atlas policy and service profile metadata.",
        "timestamp": _utc_now_iso(),
    }


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(add_help=True)
    parser.add_argument("--root", default=None, help="Atlas root to use.")
    args = parser.parse_args(argv)
    root = Path(args.root).resolve() if args.root else DEFAULT_ROOT
    result = check_creative_pipeline_readiness(root=root)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
