import os
from datetime import date
from unittest.mock import patch

os.environ["ATLAS_DISABLE_EVENT_LOGS"] = "1"

from tools.docs_catalog_report import build_docs_catalog_report, format_docs_catalog_report


def test_docs_catalog_report_builds_summary_from_current_catalog():
    report = build_docs_catalog_report()

    assert report["ok"] is True
    assert report["mode"] == "read_only_catalog_report"
    assert report["total_entries"] >= 2
    assert report["active_count"] >= 1
    assert report["expired_entries_count"] == len(report["expired_entries"])
    assert report["near_expiry_entries_count"] == len(report["near_expiry_entries"])
    assert isinstance(report["recommendations"], list)
    assert report["catalog_path"].endswith("config\\docs_search_catalog.json")


def test_docs_catalog_report_flags_expired_and_near_expiry_entries():
    catalog = [
        {
            "id": "expired_docs",
            "title": "Expired Docs",
            "url": "https://example.com/expired",
            "source_type": "official_openai_docs",
            "topics": ["docs", "mcp"],
            "description": "Expired entry.",
            "last_verified": "2026-03-01",
            "freshness_window_days": 10,
            "status": "active",
        },
        {
            "id": "near_expiry_docs",
            "title": "Near Expiry Docs",
            "url": "https://example.com/near-expiry",
            "source_type": "official_openai_docs",
            "topics": ["docs", "connectors"],
            "description": "Almost stale entry.",
            "last_verified": "2026-04-20",
            "freshness_window_days": 10,
            "status": "watchlist",
        },
    ]

    with patch("tools.docs_catalog_report._today_date", return_value=date(2026, 4, 25)):
        report = build_docs_catalog_report(catalog=catalog)

    assert report["expired_entries_count"] == 1
    assert report["expired_entries"][0]["id"] == "expired_docs"
    assert report["near_expiry_entries_count"] == 1
    assert report["near_expiry_entries"][0]["id"] == "near_expiry_docs"
    assert any("Re-verify expired catalog entries" in item for item in report["recommendations"])


def test_docs_catalog_report_top_topics_ignore_deprecated_entries():
    catalog = [
        {
            "id": "active_docs",
            "title": "Active Docs",
            "url": "https://example.com/active",
            "source_type": "official_openai_docs",
            "topics": ["docs", "mcp"],
            "description": "Active entry.",
            "last_verified": "2026-04-24",
            "freshness_window_days": 120,
            "status": "active",
        },
        {
            "id": "deprecated_docs",
            "title": "Deprecated Docs",
            "url": "https://example.com/deprecated",
            "source_type": "official_openai_docs",
            "topics": ["deprecated-only-topic"],
            "description": "Deprecated entry.",
            "last_verified": "2026-04-24",
            "freshness_window_days": 120,
            "status": "deprecated",
        },
    ]

    report = build_docs_catalog_report(catalog=catalog)

    topic_names = [item["topic"] for item in report["top_topics"]]
    assert "docs" in topic_names
    assert "deprecated-only-topic" not in topic_names


def test_docs_catalog_report_formats_readable_output():
    report = build_docs_catalog_report()
    output = format_docs_catalog_report(report)

    assert "ATLAS DOCS CATALOG REPORT" in output
    assert "Total entries:" in output
    assert "Recommendations:" in output
