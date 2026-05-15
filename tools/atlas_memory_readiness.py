from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional


DEFAULT_ROOT = Path(__file__).resolve().parents[1]
RULES_PATH = Path("config/atlas_memory_readiness_profiles.json")
SAFE_PROFILE_STATES = {"advisory", "approval_required"}
WATCHLIST_PROFILE_STATES = {"watchlist"}


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _read_json(path: Path) -> Dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def load_atlas_memory_readiness_profiles(root: Path = DEFAULT_ROOT) -> Dict[str, Any]:
    return _read_json((root / RULES_PATH).resolve())


def _snapshot_source(root: Path, source_id: str, source: Dict[str, Any]) -> Dict[str, Any]:
    relative_path = Path(str(source.get("path", "")).strip())
    path = (root / relative_path).resolve()
    exists = path.exists()
    requires_content = bool(source.get("requires_content"))
    size_bytes = path.stat().st_size if exists else 0
    has_content = exists and (size_bytes > 0)
    available = exists and (has_content if requires_content else True)
    return {
        "source": source_id,
        "path": str(relative_path).replace("\\", "/"),
        "purpose": str(source.get("purpose", "")).strip(),
        "requires_content": requires_content,
        "exists": exists,
        "size_bytes": size_bytes,
        "has_content": has_content,
        "available": available,
        "availability_reason": (
            "present_and_contentful"
            if available and requires_content
            else "present"
            if available
            else "missing_or_empty"
        ),
    }


def check_atlas_memory_readiness(root: Optional[Path] = None) -> Dict[str, Any]:
    root = (root or DEFAULT_ROOT).resolve()
    rules = load_atlas_memory_readiness_profiles(root)
    local_sources = rules.get("local_sources", {})

    source_index: Dict[str, Dict[str, Any]] = {}
    for source_id, source in local_sources.items():
        if not isinstance(source, dict):
            continue
        source_index[str(source_id)] = _snapshot_source(root, str(source_id), source)

    available_sources = [item for item in source_index.values() if item["available"]]
    missing_sources = [item for item in source_index.values() if not item["available"]]

    safe_to_use_profiles: List[Dict[str, Any]] = []
    watchlist_profiles: List[Dict[str, Any]] = []
    blocked_profiles: List[Dict[str, Any]] = []
    required_manual_steps: List[str] = []
    risks: List[str] = list(rules.get("risk_categories", []))
    requires_human_approval = False
    requires_decision_council = False

    for profile_id, profile in rules.get("profiles", {}).items():
        if not isinstance(profile, dict):
            continue

        profile_name = str(profile_id)
        required_sources = [
            str(item).strip() for item in profile.get("required_sources", []) if str(item).strip()
        ]
        initial_state = str(profile.get("initial_state", "watchlist")).strip() or "watchlist"
        risk_level = str(profile.get("risk_level", "medium")).strip() or "medium"
        present_required_sources = [
            source_name
            for source_name in required_sources
            if source_index.get(source_name, {}).get("available")
        ]
        missing_required_sources = [
            source_name for source_name in required_sources if source_name not in present_required_sources
        ]

        payload = {
            "profile": profile_name,
            "required_sources": required_sources,
            "present_required_sources": present_required_sources,
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
            payload["why"] = (
                "This memory pattern remains blocked by policy until Atlas receives explicit approval and a safer runtime design."
            )
            watchlist_profiles.append(payload)
            continue

        if initial_state in SAFE_PROFILE_STATES and not missing_required_sources:
            payload["why"] = (
                "Atlas sees enough local-first memory evidence for this profile without adding hidden runtime behavior."
            )
            safe_to_use_profiles.append(payload)
            continue

        payload["missing_required_sources"] = missing_required_sources
        payload["why"] = "Atlas does not see enough local-first evidence for this profile yet."
        blocked_profiles.append(payload)
        if missing_required_sources:
            required_manual_steps.append(
                f"Restore or create {', '.join(missing_required_sources)} before relying on `{profile_name}`."
            )

    if not any(item["source"] == "decision_feedback" and item["available"] for item in available_sources):
        risks.append("decision_feedback_signal_thin")
    if blocked_profiles:
        risks.append("local_memory_continuity_partial")

    required_manual_steps.extend(
        [
            "Keep plugin, MCP and auto-injection memory blocked until a separate approval proves the runtime and governance model.",
            "Prefer explicit summaries or cited local files over hidden reinjection when context gets long.",
        ]
    )
    required_manual_steps = list(dict.fromkeys(required_manual_steps))
    risks = list(dict.fromkeys(risks))

    status = "ok" if safe_to_use_profiles else "needs_attention"
    recommended_next_action = (
        "Use Atlas local-first memory files for continuity, and keep automatic or external memory in watchlist posture."
        if safe_to_use_profiles
        else "Restore the local-first memory baseline before claiming Atlas memory continuity."
    )

    return {
        "status": status,
        "advisory_only": bool(rules.get("advisory_only", True)),
        "available_sources": available_sources,
        "missing_sources": missing_sources,
        "safe_to_use_profiles": safe_to_use_profiles,
        "watchlist_profiles": watchlist_profiles,
        "blocked_profiles": blocked_profiles,
        "required_manual_steps": required_manual_steps,
        "risks": risks,
        "requires_human_approval": requires_human_approval,
        "requires_decision_council": requires_decision_council,
        "recommended_next_action": recommended_next_action,
        "why": "Atlas memory readiness is derived only from local-first file presence, current policy and watchlist boundaries. It is not proof of automatic memory runtime.",
        "timestamp": _utc_now_iso(),
    }


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(add_help=True)
    parser.add_argument("--root", default=None, help="Atlas root to use.")
    args = parser.parse_args(argv)
    root = Path(args.root).resolve() if args.root else DEFAULT_ROOT
    result = check_atlas_memory_readiness(root=root)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
