from __future__ import annotations

import re
from datetime import datetime, timezone
from typing import Any, Dict, List


OFFICIAL_DOCS_CATALOG: List[Dict[str, Any]] = [
    {
        "id": "openai_docs_mcp",
        "title": "Docs MCP",
        "url": "https://developers.openai.com/learn/docs-mcp",
        "summary": "Configure Codex to use the official OpenAI developer documentation MCP server in read-only mode.",
        "tags": ["docs", "mcp", "codex", "developer docs", "read-only"],
        "last_verified": "2026-04-24",
        "time_sensitive": True,
        "canonical_topic": "openai_docs_mcp",
    },
    {
        "id": "openai_mcp_connectors",
        "title": "MCP and Connectors",
        "url": "https://developers.openai.com/api/docs/guides/tools-connectors-mcp",
        "summary": "Guide to remote MCP servers and connectors, including approval policies and read-only tool usage.",
        "tags": ["mcp", "connectors", "approval", "read-only", "tools"],
        "last_verified": "2026-04-24",
        "time_sensitive": True,
        "canonical_topic": "openai_connectors_mcp",
    },
    {
        "id": "openai_codex_config_mcp",
        "title": "Codex Configuration and MCP",
        "url": "https://developers.openai.com/learn/docs-mcp",
        "summary": "Shows how Codex can reference MCP servers from ~/.codex/config.toml and use the shared configuration in CLI or IDE.",
        "tags": ["codex", "config", "mcp", "config.toml", "cli"],
        "last_verified": "2026-04-24",
        "time_sensitive": True,
        "canonical_topic": "openai_docs_mcp",
    },
]

STALE_AFTER_DAYS = 120


def _normalize(text: str) -> str:
    return " ".join(text.lower().split())


def _tokens(text: str) -> List[str]:
    return [token for token in re.findall(r"[a-z0-9]+", _normalize(text)) if len(token) >= 3]


def _today_date() -> datetime.date:
    return datetime.now(timezone.utc).date()


def _days_since(date_text: str) -> int:
    try:
        verified_date = datetime.strptime(date_text, "%Y-%m-%d").date()
    except ValueError:
        return STALE_AFTER_DAYS + 1
    return (_today_date() - verified_date).days


def _entry_staleness(entry: Dict[str, Any]) -> Dict[str, Any]:
    last_verified = str(entry.get("last_verified", "")).strip()
    days_old = _days_since(last_verified) if last_verified else STALE_AFTER_DAYS + 1
    possibly_outdated = days_old > STALE_AFTER_DAYS
    return {
        "last_verified": last_verified or None,
        "days_since_verification": days_old,
        "possibly_outdated": possibly_outdated,
        "reason": (
            "catalog_entry_is_older_than_staleness_threshold"
            if possibly_outdated
            else "catalog_entry_recently_verified"
        ),
    }


def _score_entry(normalized_query: str, query_tokens: set[str], entry: Dict[str, Any]) -> int:
    title = str(entry.get("title", ""))
    summary = str(entry.get("summary", ""))
    tags = [str(tag) for tag in entry.get("tags", [])]
    haystack = " ".join([title, summary, " ".join(tags)])
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
    if any(token in _normalize(" ".join(tags)) for token in query_tokens):
        score += 1

    staleness = _entry_staleness(entry)
    if not staleness["possibly_outdated"]:
        score += 1
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


def search_official_docs_catalog(query: str, limit: int = 3) -> List[Dict[str, Any]]:
    normalized_query = _normalize(query)
    query_tokens = set(_tokens(query))
    scored: List[Dict[str, Any]] = []

    for entry in OFFICIAL_DOCS_CATALOG:
        score = _score_entry(normalized_query, query_tokens, entry)
        if score <= 0:
            continue

        staleness = _entry_staleness(entry)
        scored.append(
            {
                "id": entry["id"],
                "title": entry["title"],
                "url": entry["url"],
                "summary": entry["summary"],
                "tags": entry["tags"],
                "score": score,
                "source": "official_openai_docs_catalog",
                "canonical_topic": entry.get("canonical_topic"),
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
        "query": normalized_query,
        "results": results,
        "result_count": len(results),
        "confidence_level": summary["confidence_level"],
        "possible_outdated_results": summary["possible_outdated_results"],
        "summary": summary,
        "key_points": _result_key_points(results),
        "adapter_note": "Read-only adapter execution over curated official OpenAI docs references. No external MCP server was invoked.",
    }
