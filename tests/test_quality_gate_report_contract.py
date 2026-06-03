import os
from functools import lru_cache

os.environ["ATLAS_DISABLE_EVENT_LOGS"] = "1"

from tests._support_paths import ATLAS_ROOT, WEB_ROOT
from tools.quality_gate_schema import (
    QUALITY_GATE_CORE_POSTURE_KEYS,
    QUALITY_GATE_CORE_SOURCE_REPORT_KEYS,
    QUALITY_GATE_MINIMUM_TOP_LEVEL_KEY_ALIASES,
    WARNING_FIELD_ALIASES,
    expected_posture_keys,
)
from tools.quality_gate_report import build_quality_gate_report


@lru_cache(maxsize=1)
def _quality_gate_report():
    return build_quality_gate_report(ATLAS_ROOT, WEB_ROOT)


def _first_present_key(payload, aliases):
    for key in aliases:
        if key in payload:
            return key
    return None


def test_quality_gate_contract_keeps_minimum_top_level_schema():
    report = _quality_gate_report()

    for semantic_name, aliases in QUALITY_GATE_MINIMUM_TOP_LEVEL_KEY_ALIASES.items():
        present_key = _first_present_key(report, aliases)
        assert present_key is not None, f"Missing top-level contract key for {semantic_name}: {sorted(aliases)}"

    project_key = _first_present_key(report, QUALITY_GATE_MINIMUM_TOP_LEVEL_KEY_ALIASES["project"])
    confidence_key = _first_present_key(report, QUALITY_GATE_MINIMUM_TOP_LEVEL_KEY_ALIASES["confidence"])

    assert report["status"] == "ok"
    assert isinstance(report[project_key], str)
    assert report[project_key]
    assert report["overall_status"] in {"ready", "needs_improvement", "not_ready"}
    assert report[confidence_key] in {"low", "medium", "high"}
    assert isinstance(report["summary_for_human"], str)
    assert report["summary_for_human"].strip()
    assert isinstance(report["recommended_next_action"], str)
    assert report["recommended_next_action"].strip()
    assert isinstance(report["source_reports"], dict)
    assert isinstance(report["warnings"], list)
    assert isinstance(report["blockers"], list)


def test_quality_gate_contract_keeps_core_posture_keys():
    report = _quality_gate_report()

    expected_keys = set(expected_posture_keys())
    assert expected_keys.issubset(report.keys())
    for posture_key in expected_keys:
        assert isinstance(report[posture_key], dict), f"{posture_key} should remain a posture dict"


def test_quality_gate_contract_keeps_core_source_reports():
    report = _quality_gate_report()
    source_reports = report["source_reports"]

    assert set(QUALITY_GATE_CORE_SOURCE_REPORT_KEYS).issubset(source_reports.keys())

    allowed_statuses = {
        "ok",
        "failed",
        "ready",
        "needs_improvement",
        "blocked",
        "skipped",
        "not_applicable",
    }

    for source_key in QUALITY_GATE_CORE_SOURCE_REPORT_KEYS:
        entry = source_reports[source_key]
        assert isinstance(entry, dict), f"{source_key} should remain a structured source report"
        assert isinstance(entry.get("status"), str), f"{source_key} must expose a status string"
        assert entry["status"] in allowed_statuses
        assert "report" in entry or "reason" in entry, f"{source_key} should expose report or reason"


def test_quality_gate_contract_warning_items_keep_minimum_shape():
    report = _quality_gate_report()
    items = [*report["warnings"], *report["blockers"]]

    for item in items:
        assert isinstance(item, dict)
        assert any(key in item for key in WARNING_FIELD_ALIASES["identifier"]), item
        assert any(str(item.get(key, "")).strip() for key in WARNING_FIELD_ALIASES["message"]), item
        if "severity" in item:
            assert str(item["severity"]).strip()
        if "source" in item:
            assert str(item["source"]).strip()


def test_quality_gate_contract_detects_core_posture_deletion_regressions():
    report = _quality_gate_report()

    missing_postures = sorted(key for key in QUALITY_GATE_CORE_POSTURE_KEYS if key not in report)
    missing_sources = sorted(key for key in QUALITY_GATE_CORE_SOURCE_REPORT_KEYS if key not in report["source_reports"])

    assert missing_postures == []
    assert missing_sources == []
