from __future__ import annotations

import importlib.util
import json
import sys
from collections import Counter
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

DEFAULT_ROOT = Path(__file__).resolve().parents[1]
NEAR_EXPIRY_WINDOW_DAYS = 14

try:
    from tools.docs_search_adapter import load_docs_search_catalog
except ModuleNotFoundError:
    adapter_path = DEFAULT_ROOT / "tools" / "docs_search_adapter.py"
    spec = importlib.util.spec_from_file_location("_atlas_docs_search_adapter", str(adapter_path))
    if not spec or not spec.loader:
        raise RuntimeError("failed_to_load_docs_search_adapter_spec")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    load_docs_search_catalog = module.load_docs_search_catalog


def _today_date() -> date:
    return datetime.now(timezone.utc).date()


def _days_since(date_text: str, fallback_days: int) -> int:
    try:
        verified_date = datetime.strptime(date_text, "%Y-%m-%d").date()
    except ValueError:
        return fallback_days + 1
    return (_today_date() - verified_date).days


def _entry_staleness(entry: Dict[str, Any]) -> Dict[str, Any]:
    last_verified = str(entry.get("last_verified", "")).strip()
    freshness_window_days = int(entry.get("freshness_window_days", 0) or 0)
    if freshness_window_days <= 0:
        freshness_window_days = 1
    days_old = _days_since(last_verified, freshness_window_days) if last_verified else freshness_window_days + 1
    days_until_expiry = freshness_window_days - days_old
    expired = days_old > freshness_window_days
    near_expiry = (not expired) and days_until_expiry <= NEAR_EXPIRY_WINDOW_DAYS
    return {
        "last_verified": last_verified or None,
        "freshness_window_days": freshness_window_days,
        "days_since_verification": days_old,
        "days_until_expiry": days_until_expiry,
        "expired": expired,
        "near_expiry": near_expiry,
    }


def _top_topics(entries: List[Dict[str, Any]], limit: int = 5) -> List[Dict[str, Any]]:
    topic_counter: Counter[str] = Counter()
    for entry in entries:
        if str(entry.get("status", "")).strip() == "deprecated":
            continue
        for topic in entry.get("topics", []):
            normalized = str(topic).strip()
            if normalized:
                topic_counter[normalized] += 1

    return [
        {"topic": topic, "count": count}
        for topic, count in topic_counter.most_common(limit)
    ]


def _maintenance_recommendations(report: Dict[str, Any]) -> List[str]:
    recommendations: List[str] = []
    if report["expired_entries"]:
        recommendations.append(
            "Re-verify expired catalog entries before relying on them for version-sensitive guidance."
        )
    if report["near_expiry_entries"]:
        recommendations.append(
            "Schedule a light freshness review for entries that are within 14 days of expiry."
        )
    if report["deprecated_count"]:
        recommendations.append(
            "Review deprecated entries periodically and remove them when they are no longer needed for audit history."
        )
    if not recommendations:
        recommendations.append(
            "Catalog freshness is healthy; keep `last_verified` current when official docs or MCP guidance changes."
        )
    return recommendations


def build_docs_catalog_report(
    root: Optional[Path] = None,
    catalog: Optional[List[Dict[str, Any]]] = None,
) -> Dict[str, Any]:
    resolved_root = (root or DEFAULT_ROOT).resolve()
    entries = list(catalog) if catalog is not None else load_docs_search_catalog(resolved_root)

    statuses = Counter(str(entry.get("status", "")).strip() for entry in entries)
    analyzed_entries: List[Dict[str, Any]] = []
    expired_entries: List[Dict[str, Any]] = []
    near_expiry_entries: List[Dict[str, Any]] = []

    for entry in entries:
        staleness = _entry_staleness(entry)
        analyzed = {
            "id": entry.get("id"),
            "title": entry.get("title"),
            "status": entry.get("status"),
            "topics": list(entry.get("topics", [])),
            "url": entry.get("url"),
            "staleness": staleness,
        }
        analyzed_entries.append(analyzed)
        if staleness["expired"]:
            expired_entries.append(analyzed)
        elif staleness["near_expiry"]:
            near_expiry_entries.append(analyzed)

    report = {
        "ok": True,
        "mode": "read_only_catalog_report",
        "catalog_path": str((resolved_root / "config" / "docs_search_catalog.json").resolve()),
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "total_entries": len(entries),
        "active_count": statuses.get("active", 0),
        "watchlist_count": statuses.get("watchlist", 0),
        "deprecated_count": statuses.get("deprecated", 0),
        "expired_entries_count": len(expired_entries),
        "near_expiry_entries_count": len(near_expiry_entries),
        "expired_entries": expired_entries,
        "near_expiry_entries": near_expiry_entries,
        "top_topics": _top_topics(entries),
    }
    report["recommendations"] = _maintenance_recommendations(report)
    return report


def format_docs_catalog_report(report: Dict[str, Any]) -> str:
    lines = [
        "ATLAS DOCS CATALOG REPORT",
        f"Catalog: {report['catalog_path']}",
        f"Generated: {report['generated_at']}",
        f"Total entries: {report['total_entries']}",
        (
            "Status counts: "
            f"active={report['active_count']}, "
            f"watchlist={report['watchlist_count']}, "
            f"deprecated={report['deprecated_count']}"
        ),
        (
            "Freshness: "
            f"expired={report['expired_entries_count']}, "
            f"near_expiry={report['near_expiry_entries_count']}"
        ),
    ]

    if report["top_topics"]:
        topic_summary = ", ".join(f"{item['topic']} ({item['count']})" for item in report["top_topics"])
        lines.append(f"Top topics: {topic_summary}")
    else:
        lines.append("Top topics: none")

    if report["expired_entries"]:
        lines.append("Expired entries:")
        lines.extend(
            f"- {item['id']} ({item['staleness']['days_since_verification']} days old)"
            for item in report["expired_entries"]
        )

    if report["near_expiry_entries"]:
        lines.append("Near-expiry entries:")
        lines.extend(
            f"- {item['id']} ({item['staleness']['days_until_expiry']} days until expiry)"
            for item in report["near_expiry_entries"]
        )

    lines.append("Recommendations:")
    lines.extend(f"- {item}" for item in report["recommendations"])
    return "\n".join(lines)


def main() -> int:
    report = build_docs_catalog_report()
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
