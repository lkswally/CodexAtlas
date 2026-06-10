import json

from tools.evidence_bundle_summary import summarize_evidence_bundle
from tools.evidence_session import build_evidence_bundle, write_evidence_bundle


def _valid_contract():
    return {
        "screenshots": [
            {
                "path": "evidence/screenshots/desktop.png",
                "viewport": "desktop",
            }
        ],
        "viewport_reports": [
            {
                "viewport": "desktop",
                "url": "http://localhost:3000",
                "width": 1440,
                "height": 1000,
            }
        ],
        "build_report": {},
        "console_errors": [],
        "network_errors": [],
        "evidence_timestamp": "2026-06-10T00:00:00+00:00",
        "source_commit": "abc123",
    }


def _write_bundle(tmp_path, bundle):
    output_path = tmp_path / "bundle.json"
    write_evidence_bundle(bundle, output_path)
    return output_path


def test_complete_valid_bundle_summary_passes(tmp_path):
    bundle = build_evidence_bundle(_valid_contract())

    summary = summarize_evidence_bundle(_write_bundle(tmp_path, bundle))

    assert summary["status"] == "PASS"
    assert summary["warnings"] == []
    assert summary["failures"] == []


def test_valid_bundle_without_screenshots_warns(tmp_path):
    contract = _valid_contract()
    contract["screenshots"] = []
    bundle = build_evidence_bundle(contract)

    summary = summarize_evidence_bundle(_write_bundle(tmp_path, bundle))

    assert summary["status"] == "WARN"
    assert "Evidence Bundle has no screenshots." in summary["warnings"]


def test_valid_bundle_without_viewport_reports_warns(tmp_path):
    contract = _valid_contract()
    contract["viewport_reports"] = []
    bundle = build_evidence_bundle(contract)

    summary = summarize_evidence_bundle(_write_bundle(tmp_path, bundle))

    assert summary["status"] == "WARN"
    assert "Evidence Bundle has no viewport reports." in summary["warnings"]


def test_bundle_with_console_errors_warns(tmp_path):
    contract = _valid_contract()
    contract["console_errors"] = [{"text": "boom"}]
    bundle = build_evidence_bundle(contract)

    summary = summarize_evidence_bundle(_write_bundle(tmp_path, bundle))

    assert summary["status"] == "WARN"
    assert summary["console_errors_count"] == 1
    assert "Evidence Bundle contains console errors." in summary["warnings"]


def test_bundle_with_network_errors_warns(tmp_path):
    contract = _valid_contract()
    contract["network_errors"] = [{"url": "http://localhost/missing", "status": 404}]
    bundle = build_evidence_bundle(contract)

    summary = summarize_evidence_bundle(_write_bundle(tmp_path, bundle))

    assert summary["status"] == "WARN"
    assert summary["network_errors_count"] == 1
    assert "Evidence Bundle contains network errors." in summary["warnings"]


def test_missing_bundle_path_fails_controlled(tmp_path):
    summary = summarize_evidence_bundle(tmp_path / "missing.json")

    assert summary["status"] == "FAIL"
    assert summary["failures"]


def test_summary_contains_correct_counts(tmp_path):
    contract = _valid_contract()
    contract["screenshots"].append(
        {
            "path": "evidence/screenshots/mobile.png",
            "viewport": "mobile",
        }
    )
    contract["console_errors"] = [{"text": "one"}, {"text": "two"}]
    bundle = build_evidence_bundle(contract)

    summary = summarize_evidence_bundle(_write_bundle(tmp_path, bundle))

    assert summary["screenshots_count"] == 2
    assert summary["viewport_reports_count"] == 1
    assert summary["console_errors_count"] == 2
    assert summary["network_errors_count"] == 0
    assert summary["has_build_report"] is True


def test_summary_preserves_source_commit_and_timestamp(tmp_path):
    bundle = build_evidence_bundle(_valid_contract())

    summary = summarize_evidence_bundle(_write_bundle(tmp_path, bundle))

    assert summary["source_commit"] == "abc123"
    assert summary["evidence_timestamp"] == "2026-06-10T00:00:00+00:00"


def test_invalid_bundle_status_fails_controlled(tmp_path):
    bundle = build_evidence_bundle(_valid_contract())
    bundle["validation_status"] = "FAIL"
    output_path = tmp_path / "bundle.json"
    output_path.write_text(json.dumps(bundle), encoding="utf-8")

    summary = summarize_evidence_bundle(output_path)

    assert summary["status"] == "FAIL"
    assert summary["failures"]
