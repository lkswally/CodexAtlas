from pathlib import Path
from unittest.mock import patch

from tools.atlas_memory_readiness import check_atlas_memory_readiness


ROOT = Path(r"C:\Proyectos\Codex-Atlas")


def _snapshot(source: str, available: bool) -> dict:
    return {
        "source": source,
        "path": f"memory/{source}",
        "purpose": source,
        "requires_content": True,
        "exists": available,
        "size_bytes": 10 if available else 0,
        "has_content": available,
        "available": available,
        "availability_reason": "present_and_contentful" if available else "missing_or_empty",
    }


def test_atlas_memory_readiness_reports_local_safe_profiles():
    result = check_atlas_memory_readiness(root=ROOT)
    assert result["status"] == "ok"
    assert any(item["profile"] == "local_session_summary" for item in result["safe_to_use_profiles"])
    assert any(item["profile"] == "plugin_memory_watchlist" for item in result["watchlist_profiles"])


def test_atlas_memory_readiness_blocks_local_session_summary_without_decision_log():
    def fake_snapshot(root, source_id, source):
        if source_id == "decision_log":
            return _snapshot(source_id, False)
        return _snapshot(source_id, True)

    with patch("tools.atlas_memory_readiness._snapshot_source", side_effect=fake_snapshot):
        result = check_atlas_memory_readiness(root=ROOT)

    blocked = next(item for item in result["blocked_profiles"] if item["profile"] == "local_session_summary")
    assert "decision_log" in blocked["missing_required_sources"]


def test_atlas_memory_readiness_flags_thin_feedback_signal_when_feedback_is_empty():
    def fake_snapshot(root, source_id, source):
        available = source_id != "decision_feedback"
        return _snapshot(source_id, available)

    with patch("tools.atlas_memory_readiness._snapshot_source", side_effect=fake_snapshot):
        result = check_atlas_memory_readiness(root=ROOT)

    assert "decision_feedback_signal_thin" in result["risks"]


def test_atlas_memory_readiness_keeps_plugin_memory_on_watchlist():
    result = check_atlas_memory_readiness(root=ROOT)
    watchlist = next(item for item in result["watchlist_profiles"] if item["profile"] == "plugin_memory_watchlist")
    assert watchlist["risk_level"] == "high"
    assert result["requires_decision_council"] is True
