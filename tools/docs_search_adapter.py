from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List

DEFAULT_ROOT = Path(__file__).resolve().parents[1]
DOCS_SEARCH_CATALOG_PATH = DEFAULT_ROOT / "config" / "docs_search_catalog.json"
VALID_CATALOG_STATUSES = {"active", "watchlist", "deprecated"}


def _normalize(text: str) -> str:
    return " ".join(text.lower().split())


def _tokens(text: str) -> List[str]:
    return [token for token in re.findall(r"[a-z0-9]+", _normalize(text)) if len(token) >= 3]


def _today_date() -> datetime.date:
    return datetime.now(timezone.utc).date()


def _days_since(date_text: str, fallback_days: int) -> int:
    try:
        verified_date = datetime.strptime(date_text, "%Y-%m-%d").date()
    except ValueError:
        return fallback_days + 1
    return (_today_date() - verified_date).days


def _catalog_path(root: Path | None = None) -> Path:
    resolved_root = (root or DEFAULT_ROOT).resolve()
    return resolved_root / "config" / "docs_search_catalog.json"


def load_docs_search_catalog(root: Path | None = None) -> List[Dict[str, Any]]:
    catalog_path = _catalog_path(root)
    payload = json.loads(catalog_path.read_text(encoding="utf-8-sig"))
    entries = payload.get("entries", [])
    if not isinstance(entries, list):
        return []
    return [entry for entry in entries if isinstance(entry, dict)]


def _entry_staleness(entry: Dict[str, Any]) -> Dict[str, Any]:
    last_verified = str(entry.get("last_verified", "")).strip()
    freshness_window_days = int(entry.get("freshness_window_days", 0) or 0)
    if freshness_window_days <= 0:
        freshness_window_days = 1
    days_old = _days_since(last_verified, freshness_window_days) if last_verified else freshness_window_days + 1
    possibly_outdated = days_old > freshness_window_days
    return {
        "last_verified": last_verified or None,
        "freshness_window_days": freshness_window_days,
        "days_since_verification": days_old,
        "possibly_outdated": possibly_outdated,
        "reason": (
            "catalog_entry_is_older_than_freshness_window"
            if possibly_outdated
            else "catalog_entry_within_freshness_window"
        ),
    }


def _score_entry(normalized_query: str, query_tokens: set[str], entry: Dict[str, Any]) -> int:
    title = str(entry.get("title", ""))
    description = str(entry.get("description", ""))
    topics = [str(topic) for topic in entry.get("topics", [])]
    status = str(entry.get("status", "active")).strip()
    haystack = " ".join([title, description, " ".join(topics)])
    haystack_normalized = _normalize(haystack)
    haystack_tokens = set(_tokens(haystack))

    score = len(query_tokens & haystack_tokens)
    title_normalized = _normalize(title)
    if normalized_query and normalized_query in haystack_normalized:
        score += 4
    if normalized_query and normalized_query in title_normalized:
        score += 3
    if any(token in title_normalized for token in query_tokens):
        score += 2
    if any(token in _normalize(" ".join(topics)) for token in query_tokens):
        score += 1

    staleness = _entry_staleness(entry)
    if not staleness["possibly_outdated"]:
        score += 1
    if status == "watchlist":
        score -= 1
    return score


def _dedupe_ranked_results(results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    deduped: List[Dict[str, Any]] = []
    seen_keys: set[str] = set()
    for item in results:
        dedupe_key = str(item.get("url") or item.get("canonical_topic") or item.get("id"))
        if dedupe_key in seen_keys:
            continue
        seen_keys.add(dedupe_key)
        deduped.append(item)
    return deduped


def _entry_confidence(score: int, staleness: Dict[str, Any]) -> str:
    if score >= 8 and not staleness["possibly_outdated"]:
        return "high"
    if score >= 4:
        return "medium"
    return "low"


def search_official_docs_catalog(query: str, limit: int = 3, catalog: List[Dict[str, Any]] | None = None) -> List[Dict[str, Any]]:
    normalized_query = _normalize(query)
    query_tokens = set(_tokens(query))
    scored: List[Dict[str, Any]] = []
    catalog_entries = catalog if catalog is not None else load_docs_search_catalog()

    for entry in catalog_entries:
        status = str(entry.get("status", "")).strip()
        if status not in VALID_CATALOG_STATUSES:
            continue
        if status == "deprecated":
            continue
        score = _score_entry(normalized_query, query_tokens, entry)
        if score <= 0:
            continue

        staleness = _entry_staleness(entry)
        scored.append(
            {
                "id": entry["id"],
                "title": entry["title"],
                "url": entry["url"],
                "source_type": entry.get("source_type"),
                "summary": entry["description"],
                "tags": entry["topics"],
                "status": status,
                "score": score,
                "source": "official_openai_docs_catalog",
                "canonical_topic": entry.get("id"),
                "confidence_level": _entry_confidence(score, staleness),
                "staleness": staleness,
            }
        )

    scored.sort(
        key=lambda item: (
            -int(item["score"]),
            0 if item["confidence_level"] == "high" else 1 if item["confidence_level"] == "medium" else 2,
            str(item["title"]),
        )
    )
    return _dedupe_ranked_results(scored)[:limit]


def _overall_confidence(results: List[Dict[str, Any]]) -> str:
    if not results:
        return "low"
    top_score = int(results[0].get("score", 0))
    if top_score >= 8 and any(item.get("confidence_level") == "high" for item in results):
        return "high"
    if top_score >= 4:
        return "medium"
    return "low"


def _result_key_points(results: List[Dict[str, Any]]) -> List[str]:
    if not results:
        return ["No curated official docs entry matched the query strongly enough."]

    key_points: List[str] = []
    top = results[0]
    key_points.append(f"Top match: {top['title']} ({top['url']})")
    key_points.append(f"Top match confidence: {top['confidence_level']}")
    if len(results) > 1:
        key_points.append(f"{len(results)} deduplicated official references were returned.")
    else:
        key_points.append("A single deduplicated official reference was returned.")
    if any(item.get("staleness", {}).get("possibly_outdated") for item in results):
        key_points.append("At least one result may be stale and should be re-verified before relying on version-sensitive details.")
    else:
        key_points.append("Returned references are recently verified in the local curated catalog.")
    return key_points


def _structured_summary(query: str, results: List[Dict[str, Any]]) -> Dict[str, Any]:
    return {
        "query": query,
        "top_match_title": results[0]["title"] if results else None,
        "top_match_url": results[0]["url"] if results else None,
        "result_count": len(results),
        "deduplicated": True,
        "confidence_level": _overall_confidence(results),
        "possible_outdated_results": any(item.get("staleness", {}).get("possibly_outdated") for item in results),
        "recommended_next_step": (
            "Use the top official docs result as the first source, then cross-check time-sensitive details if versions or release status matter."
            if results
            else "Fall back to manual verification because the curated local catalog did not return a strong match."
        ),
    }


def execute_docs_search_adapter(query: str) -> Dict[str, Any]:
    normalized_query = _normalize(query)
    if not normalized_query:
        return {
            "ok": False,
            "mode": "adapter_read_only",
            "error": "empty_query",
            "results": [],
        }

    results = search_official_docs_catalog(normalized_query)
    summary = _structured_summary(normalized_query, results)
    return {
        "ok": True,
        "mode": "adapter_read_only",
        "source": "official_openai_docs_catalog",
        "catalog_path": str(DOCS_SEARCH_CATALOG_PATH),
        "query": normalized_query,
        "results": results,
        "result_count": len(results),
        "confidence_level": summary["confidence_level"],
        "possible_outdated_results": summary["possible_outdated_results"],
        "summary": summary,
        "key_points": _result_key_points(results),
        "adapter_note": "Read-only adapter execution over curated official OpenAI docs references. No external MCP server was invoked.",
    }
