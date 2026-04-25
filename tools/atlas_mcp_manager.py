from __future__ import annotations

import argparse
import hashlib
import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional


DEFAULT_ROOT = Path(__file__).resolve().parents[1]
MEMORY_DIR_NAME = "memory"
ROUTING_LOG = "routing_log.jsonl"
GOVERNANCE_EVENTS_LOG = "governance_events.jsonl"
MCP_EVENTS_LOG = "mcp_events.jsonl"


def _load_json(path: Path) -> Dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _memory_dir(root: Path) -> Path:
    return root / MEMORY_DIR_NAME


def _event_logging_enabled(root: Path) -> bool:
    if os.environ.get("ATLAS_DISABLE_EVENT_LOGS", "").strip() == "1":
        return False
    return root.resolve() == DEFAULT_ROOT.resolve()


def _append_jsonl_record(path: Path, record: Dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(record, ensure_ascii=False) + "\n")


def _text_fingerprint(text: str) -> str:
    return hashlib.sha256(text.strip().encode("utf-8")).hexdigest()[:16]


def _preview(text: str, limit: int = 96) -> str:
    normalized = " ".join(text.split())
    if len(normalized) <= limit:
        return normalized
    return normalized[: limit - 3] + "..."


def _load_mcp_profiles(root: Path) -> Dict[str, Any]:
    return _load_json(root / "config" / "mcp_profiles.json")


def _profile_lifecycle_state(profile: Dict[str, Any]) -> str:
    if not bool(profile.get("experimental_enabled")):
        return "blocked"
    if bool(profile.get("requires_approval")):
        return "approval_required"
    return "suggested"


def _profile_is_eligible(profile: Dict[str, Any]) -> bool:
    return (
        str(profile.get("default_mode", "")).strip() == "read_only"
        and str(profile.get("atlas_decision", "")).strip() == "experimental_read_only"
        and bool(profile.get("experimental_enabled"))
    )


def _record_mcp_event(root: Path, payload: Dict[str, Any]) -> None:
    if not _event_logging_enabled(root):
        return

    event = {"timestamp": _utc_now_iso(), **payload}
    _append_jsonl_record(_memory_dir(root) / MCP_EVENTS_LOG, event)

    governance_entry = {
        "timestamp": event["timestamp"],
        "root": str(root),
        "project": None,
        "profile": "mcp_lifecycle",
        "ok": bool(payload.get("ok", True)),
        "findings_count": len(list(payload.get("blockers", []))),
        "findings": list(payload.get("blockers", [])),
        "event_type": payload.get("event_type"),
        "mcp_profile": payload.get("profile"),
        "mcp_state": payload.get("state"),
        "experimental_mcp_profiles": [payload.get("profile")] if payload.get("state") != "blocked" else [],
    }
    _append_jsonl_record(_memory_dir(root) / GOVERNANCE_EVENTS_LOG, governance_entry)


def list_mcp_profiles(root: Optional[Path] = None) -> Dict[str, Any]:
    resolved_root = (root or DEFAULT_ROOT).resolve()
    config = _load_mcp_profiles(resolved_root)
    profiles = config.get("profiles", {})
    result_profiles: List[Dict[str, Any]] = []

    if isinstance(profiles, dict):
        for profile_id in sorted(profiles.keys()):
            profile = profiles[profile_id]
            if not isinstance(profile, dict):
                continue
            result_profiles.append(
                {
                    "id": profile_id,
                    "purpose": profile.get("purpose"),
                    "risk_level": profile.get("risk_level"),
                    "default_mode": profile.get("default_mode"),
                    "requires_approval": bool(profile.get("requires_approval")),
                    "provider_kind": profile.get("provider_kind"),
                    "atlas_decision": profile.get("atlas_decision"),
                    "experimental_enabled": bool(profile.get("experimental_enabled")),
                    "read_only_scope": profile.get("read_only_scope"),
                    "lifecycle_state": _profile_lifecycle_state(profile),
                }
            )

    return {
        "default_policy": config.get("default_policy"),
        "profiles": result_profiles,
    }


def evaluate_mcp_request(task: str, root: Optional[Path] = None) -> Dict[str, Any]:
    from tools.atlas_orchestrator import orchestrate_task

    resolved_root = (root or DEFAULT_ROOT).resolve()
    route = orchestrate_task(task, root=resolved_root)
    evaluations: List[Dict[str, Any]] = []

    for item in route.get("suggested_mcps", []):
        if not isinstance(item, dict):
            continue
        state = str(item.get("lifecycle_state") or "blocked")
        evaluations.append(
            {
                "id": item.get("id"),
                "state": state,
                "default_mode": item.get("default_mode"),
                "requires_approval": bool(item.get("requires_approval")),
                "risk_level": item.get("risk_level"),
                "provider_kind": item.get("provider_kind"),
                "atlas_decision": item.get("atlas_decision"),
                "experimental_enabled": bool(item.get("experimental_enabled")),
                "read_only_scope": item.get("read_only_scope"),
            }
        )

    result = {
        "task_fingerprint": _text_fingerprint(task),
        "task_preview": _preview(task),
        "intent": route.get("intent"),
        "recommended_agent": route.get("recommended_agent"),
        "profiles": evaluations,
        "status": "ok",
    }

    _record_mcp_event(
        resolved_root,
        {
            "event_type": "evaluate",
            "ok": True,
            "profile": evaluations[0]["id"] if evaluations else None,
            "state": evaluations[0]["state"] if evaluations else "blocked",
            "task_fingerprint": result["task_fingerprint"],
            "task_preview": result["task_preview"],
            "suggested_profiles": [item["id"] for item in evaluations],
            "blockers": [],
        },
    )
    return result


def approve_mcp(profile: str, reason: str, root: Optional[Path] = None) -> Dict[str, Any]:
    resolved_root = (root or DEFAULT_ROOT).resolve()
    config = _load_mcp_profiles(resolved_root)
    profiles = config.get("profiles", {})
    profile_data = profiles.get(profile) if isinstance(profiles, dict) else None

    if not isinstance(profile_data, dict):
        result = {
            "profile": profile,
            "state": "blocked",
            "ok": False,
            "blockers": [f"unknown_mcp_profile:{profile}"],
        }
        _record_mcp_event(resolved_root, {"event_type": "approve", **result})
        return result

    if not reason or not reason.strip():
        result = {
            "profile": profile,
            "state": "blocked",
            "ok": False,
            "blockers": [f"mcp_approval_reason_required:{profile}"],
        }
        _record_mcp_event(resolved_root, {"event_type": "approve", **result})
        return result

    blockers: List[str] = []
    if not _profile_is_eligible(profile_data):
        blockers.append(f"mcp_profile_not_approved_for_experiment:{profile}")
    if str(profile_data.get("default_mode", "")).strip() != "read_only":
        blockers.append(f"mcp_profile_not_read_only:{profile}")

    if blockers:
        result = {
            "profile": profile,
            "state": "blocked",
            "ok": False,
            "reason_preview": _preview(reason),
            "blockers": blockers,
        }
        _record_mcp_event(resolved_root, {"event_type": "approve", **result})
        return result

    approval = {
        "profile": profile,
        "state": "approved",
        "ok": True,
        "approval_id": _text_fingerprint(f"{profile}:{reason}:{_utc_now_iso()}"),
        "reason_preview": _preview(reason),
        "blockers": [],
    }
    _record_mcp_event(resolved_root, {"event_type": "approve", **approval})
    return approval


def simulate_mcp_execution(
    profile: str,
    query: str,
    root: Optional[Path] = None,
    approval: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    resolved_root = (root or DEFAULT_ROOT).resolve()
    config = _load_mcp_profiles(resolved_root)
    profiles = config.get("profiles", {})
    profile_data = profiles.get(profile) if isinstance(profiles, dict) else None

    if not isinstance(profile_data, dict):
        result = {
            "profile": profile,
            "state": "blocked",
            "ok": False,
            "query_fingerprint": _text_fingerprint(query),
            "query_preview": _preview(query),
            "blockers": [f"unknown_mcp_profile:{profile}"],
        }
        _record_mcp_event(resolved_root, {"event_type": "simulate", **result})
        return result

    blockers: List[str] = []
    if not _profile_is_eligible(profile_data):
        blockers.append(f"mcp_profile_not_executable_in_current_stage:{profile}")
    if bool(profile_data.get("requires_approval")):
        if not isinstance(approval, dict) or approval.get("state") != "approved" or approval.get("profile") != profile:
            blockers.append(f"mcp_approval_missing_or_invalid:{profile}")

    if blockers:
        result = {
            "profile": profile,
            "state": "blocked",
            "ok": False,
            "query_fingerprint": _text_fingerprint(query),
            "query_preview": _preview(query),
            "blockers": blockers,
        }
        _record_mcp_event(resolved_root, {"event_type": "simulate", **result})
        return result

    simulated = {
        "profile": profile,
        "state": "executed_simulated",
        "ok": True,
        "query_fingerprint": _text_fingerprint(query),
        "query_preview": _preview(query),
        "mode": "read_only_simulation",
        "simulation": {
            "provider_kind": profile_data.get("provider_kind"),
            "default_mode": profile_data.get("default_mode"),
            "result_summary": f"Simulated read-only MCP execution for `{profile}`. No external connector was invoked.",
            "next_step": "Keep this as a dry run until real connector enablement is approved separately.",
        },
        "blockers": [],
    }
    _record_mcp_event(resolved_root, {"event_type": "simulate", **simulated})
    return simulated


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(add_help=True)
    parser.add_argument("--root", default=None, help="Atlas root to use.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    subparsers.add_parser("list", help="List current MCP profiles.")

    evaluate_parser = subparsers.add_parser("evaluate", help="Evaluate MCP lifecycle for a task.")
    evaluate_parser.add_argument("task", nargs="+", help="Task to evaluate.")

    approve_parser = subparsers.add_parser("approve", help="Approve an MCP profile for simulated use.")
    approve_parser.add_argument("profile", help="Profile id.")
    approve_parser.add_argument("--reason", required=True, help="Human approval reason.")

    simulate_parser = subparsers.add_parser("simulate", help="Simulate a read-only MCP execution.")
    simulate_parser.add_argument("profile", help="Profile id.")
    simulate_parser.add_argument("query", nargs="+", help="Read-only query to simulate.")
    simulate_parser.add_argument("--reason", default=None, help="Approval reason to attach before simulation.")

    args = parser.parse_args(argv)
    root = Path(args.root).resolve() if args.root else DEFAULT_ROOT

    if args.command == "list":
        result = list_mcp_profiles(root=root)
    elif args.command == "evaluate":
        result = evaluate_mcp_request(" ".join(args.task), root=root)
    elif args.command == "approve":
        result = approve_mcp(args.profile, args.reason, root=root)
    else:
        approval = approve_mcp(args.profile, args.reason, root=root) if args.reason else None
        result = simulate_mcp_execution(args.profile, " ".join(args.query), root=root, approval=approval)

    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
