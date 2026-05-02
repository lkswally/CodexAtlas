from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence

DEFAULT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_LOG = Path("memory") / "decision_feedback.jsonl"
VALID_DECISIONS = {"accepted", "ignored", "deferred", "replaced"}
VALID_SOURCES = {"quality_gate_report", "priority_engine", "manual"}


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _resolve_log_path(root: Path, log_path: Optional[Path] = None) -> Path:
    if log_path is not None:
        return log_path.resolve()
    return (root / DEFAULT_LOG).resolve()


def _normalize_optional_text(value: Optional[str]) -> Optional[str]:
    if value is None:
        return None
    normalized = str(value).strip()
    return normalized or None


def _load_feedback_entries(log_path: Path) -> List[Dict[str, Any]]:
    if not log_path.exists():
        return []
    entries: List[Dict[str, Any]] = []
    for raw_line in log_path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line:
            continue
        payload = json.loads(line)
        if isinstance(payload, dict):
            entries.append(payload)
    return entries


def append_decision_feedback(
    root: Path,
    project_path: Path,
    decision: str,
    reason: str,
    source: str,
    recommendation_id: Optional[str] = None,
    action: Optional[str] = None,
    log_path: Optional[Path] = None,
) -> Dict[str, Any]:
    normalized_decision = str(decision).strip()
    normalized_source = str(source).strip()
    normalized_reason = str(reason).strip()
    normalized_recommendation_id = _normalize_optional_text(recommendation_id)
    normalized_action = _normalize_optional_text(action)

    if normalized_decision not in VALID_DECISIONS:
        raise ValueError(f"invalid_decision:{normalized_decision}")
    if normalized_source not in VALID_SOURCES:
        raise ValueError(f"invalid_source:{normalized_source}")
    if not normalized_reason:
        raise ValueError("reason_required")
    if not normalized_recommendation_id and not normalized_action:
        raise ValueError("recommendation_id_or_action_required")

    destination = _resolve_log_path(root.resolve(), log_path)
    destination.parent.mkdir(parents=True, exist_ok=True)

    entry = {
        "project_path": str(project_path.resolve()),
        "recommendation_id": normalized_recommendation_id,
        "action": normalized_action,
        "decision": normalized_decision,
        "reason": normalized_reason,
        "timestamp": _utc_now_iso(),
        "source": normalized_source,
    }
    with destination.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(entry, ensure_ascii=False) + "\n")
    return {
        "status": "ok",
        "entry": entry,
        "log_path": str(destination),
    }


def find_relevant_feedback(
    root: Path,
    project_path: Path,
    recommendation_ids: Optional[Sequence[str]] = None,
    actions: Optional[Sequence[str]] = None,
    limit: int = 5,
    log_path: Optional[Path] = None,
) -> Dict[str, Any]:
    destination = _resolve_log_path(root.resolve(), log_path)
    recommendation_set = {
        str(item).strip()
        for item in (recommendation_ids or [])
        if str(item).strip()
    }
    action_set = {
        str(item).strip()
        for item in (actions or [])
        if str(item).strip()
    }

    try:
        entries = _load_feedback_entries(destination)
    except Exception as exc:
        return {
            "status": "failed",
            "reason": f"decision_feedback_load_failed:{exc}",
            "has_relevant_feedback": False,
            "relevant_feedback": [],
            "matched_recommendation_ids": sorted(recommendation_set),
            "matched_actions": sorted(action_set),
            "log_path": str(destination),
        }

    project_key = str(project_path.resolve())
    relevant: List[Dict[str, Any]] = []
    for entry in reversed(entries):
        if str(entry.get("project_path", "")).strip() != project_key:
            continue
        recommendation_id = _normalize_optional_text(entry.get("recommendation_id"))
        action = _normalize_optional_text(entry.get("action"))
        if recommendation_set and recommendation_id in recommendation_set:
            relevant.append(entry)
            continue
        if action_set and action in action_set:
            relevant.append(entry)
            continue
    relevant = relevant[: max(limit, 0)]
    return {
        "status": "ok",
        "reason": None,
        "has_relevant_feedback": bool(relevant),
        "relevant_feedback": relevant,
        "matched_recommendation_ids": sorted(recommendation_set),
        "matched_actions": sorted(action_set),
        "log_path": str(destination),
    }


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(add_help=True)
    subparsers = parser.add_subparsers(dest="command", required=True)

    record_parser = subparsers.add_parser("record")
    record_parser.add_argument("--root", default=None)
    record_parser.add_argument("--project", required=True)
    record_parser.add_argument("--recommendation-id", default=None)
    record_parser.add_argument("--action", default=None)
    record_parser.add_argument("--decision", required=True)
    record_parser.add_argument("--reason", required=True)
    record_parser.add_argument("--source", default="manual")

    find_parser = subparsers.add_parser("find")
    find_parser.add_argument("--root", default=None)
    find_parser.add_argument("--project", required=True)
    find_parser.add_argument("--recommendation-id", action="append", default=[])
    find_parser.add_argument("--action", action="append", default=[])
    find_parser.add_argument("--limit", type=int, default=5)

    args = parser.parse_args(argv)
    root = Path(args.root).resolve() if args.root else DEFAULT_ROOT

    if args.command == "record":
        result = append_decision_feedback(
            root=root,
            project_path=Path(args.project),
            recommendation_id=args.recommendation_id,
            action=args.action,
            decision=args.decision,
            reason=args.reason,
            source=args.source,
        )
    else:
        result = find_relevant_feedback(
            root=root,
            project_path=Path(args.project),
            recommendation_ids=args.recommendation_id,
            actions=args.action,
            limit=args.limit,
        )
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
