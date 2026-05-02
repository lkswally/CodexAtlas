from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Dict, List, Optional

try:
    from tools.decision_feedback import _load_feedback_entries, _resolve_log_path
except ModuleNotFoundError:
    from decision_feedback import _load_feedback_entries, _resolve_log_path


DEFAULT_ROOT = Path(__file__).resolve().parents[1]


def _normalize(text: str) -> str:
    return " ".join(str(text).lower().split())


def analyze_feedback(
    root: Path,
    project_path: Optional[Path] = None,
    log_path: Optional[Path] = None,
) -> Dict[str, Any]:
    root = root.resolve()
    destination = _resolve_log_path(root, log_path)
    try:
        entries = _load_feedback_entries(destination)
    except Exception as exc:
        return {
            "status": "failed",
            "reason": f"feedback_load_failed:{exc}",
            "project_path": str(project_path.resolve()) if project_path else None,
            "action_feedback": [],
            "detected_patterns": [],
            "log_path": str(destination),
        }

    project_key = str(project_path.resolve()) if project_path else None
    filtered: List[Dict[str, Any]] = []
    for entry in entries:
        if project_key and str(entry.get("project_path", "")).strip() != project_key:
            continue
        action = str(entry.get("action", "")).strip()
        if not action:
            continue
        filtered.append(entry)

    by_action: Dict[str, Dict[str, Any]] = {}
    for entry in filtered:
        action = str(entry.get("action", "")).strip()
        key = _normalize(action)
        item = by_action.setdefault(
            key,
            {
                "action": action,
                "frequency": 0,
                "accepted_count": 0,
                "ignored_count": 0,
                "deferred_count": 0,
                "replaced_count": 0,
                "last_decision": None,
                "last_timestamp": None,
            },
        )
        item["frequency"] += 1
        decision = str(entry.get("decision", "")).strip()
        if decision == "accepted":
            item["accepted_count"] += 1
        elif decision == "ignored":
            item["ignored_count"] += 1
        elif decision == "deferred":
            item["deferred_count"] += 1
        elif decision == "replaced":
            item["replaced_count"] += 1

        timestamp = str(entry.get("timestamp", "")).strip() or None
        if item["last_timestamp"] is None or (timestamp and timestamp >= str(item["last_timestamp"])):
            item["last_timestamp"] = timestamp
            item["last_decision"] = decision or None

    action_feedback: List[Dict[str, Any]] = []
    detected_patterns: List[Dict[str, Any]] = []
    for item in by_action.values():
        frequency = int(item["frequency"])
        accepted_count = int(item["accepted_count"])
        ignored_count = int(item["ignored_count"])
        action_feedback.append(
            {
                "action": item["action"],
                "frequency": frequency,
                "acceptance_rate": round(accepted_count / frequency, 2) if frequency else 0.0,
                "ignore_rate": round(ignored_count / frequency, 2) if frequency else 0.0,
                "last_decision": item["last_decision"],
            }
        )

        if frequency >= 2 and ignored_count / frequency >= 0.75:
            detected_patterns.append(
                {
                    "pattern": f"Action `{item['action']}` is repeatedly ignored.",
                    "impact": "Lower its priority or drop it when stronger signals exist.",
                    "recommendation": "Stop surfacing this action as a top recommendation unless a new blocker reintroduces it.",
                }
            )
        elif frequency >= 2 and accepted_count / frequency >= 0.75:
            detected_patterns.append(
                {
                    "pattern": f"Action `{item['action']}` is consistently accepted.",
                    "impact": "Promote it earlier when similar conditions reappear.",
                    "recommendation": "Use this action as a stronger default when the same project state returns.",
                }
            )

    action_feedback.sort(key=lambda item: (-int(item["frequency"]), item["action"].lower()))
    return {
        "status": "ok",
        "reason": None,
        "project_path": project_key,
        "analyzed_entries": len(filtered),
        "action_feedback": action_feedback,
        "detected_patterns": detected_patterns[:5],
        "log_path": str(destination),
    }


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(add_help=True)
    parser.add_argument("--root", default=None)
    parser.add_argument("--project", default=None)
    args = parser.parse_args(argv)
    root = Path(args.root).resolve() if args.root else DEFAULT_ROOT
    project = Path(args.project).resolve() if args.project else None
    result = analyze_feedback(root=root, project_path=project)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
