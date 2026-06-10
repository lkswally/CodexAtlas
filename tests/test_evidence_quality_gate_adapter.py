import copy
import json

from tools.evidence_bundle_summary import summarize_evidence_bundle
from tools.evidence_quality_gate_adapter import build_evidence_quality_gate
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


def _write_contract_bundle(tmp_path, contract):
    bundle = build_evidence_bundle(contract)
    output_path = tmp_path / "bundle.json"
    write_evidence_bundle(bundle, output_path)
    return output_path


def test_pass_bundle_builds_pass_gate(tmp_path):
    bundle_path = _write_contract_bundle(tmp_path, _valid_contract())

    gate = build_evidence_quality_gate(bundle_path)

    assert gate["gate_name"] == "evidence_bundle_quality"
    assert gate["status"] == "PASS"
    assert gate["source"] == "evidence_summary_v1"


def test_warn_bundle_builds_warn_gate(tmp_path):
    contract = _valid_contract()
    contract["screenshots"] = []
    bundle_path = _write_contract_bundle(tmp_path, contract)

    gate = build_evidence_quality_gate(bundle_path)

    assert gate["status"] == "WARN"


def test_invalid_path_builds_fail_gate(tmp_path):
    gate = build_evidence_quality_gate(tmp_path / "missing.json")

    assert gate["status"] == "FAIL"
    assert gate["failures"]


def test_preserves_warnings(tmp_path):
    contract = _valid_contract()
    contract["network_errors"] = [{"url": "http://localhost/missing", "status": 404}]
    bundle_path = _write_contract_bundle(tmp_path, contract)

    gate = build_evidence_quality_gate(bundle_path)

    assert gate["status"] == "WARN"
    assert "Evidence Bundle contains network errors." in gate["warnings"]


def test_preserves_failures(tmp_path):
    bundle = build_evidence_bundle(_valid_contract())
    bundle["validation_status"] = "FAIL"
    output_path = tmp_path / "bundle.json"
    output_path.write_text(json.dumps(bundle), encoding="utf-8")

    gate = build_evidence_quality_gate(output_path)

    assert gate["status"] == "FAIL"
    assert gate["failures"]


def test_preserves_source_commit(tmp_path):
    bundle_path = _write_contract_bundle(tmp_path, _valid_contract())

    gate = build_evidence_quality_gate(bundle_path)

    assert gate["source_commit"] == "abc123"


def test_preserves_evidence_timestamp(tmp_path):
    bundle_path = _write_contract_bundle(tmp_path, _valid_contract())

    gate = build_evidence_quality_gate(bundle_path)

    assert gate["evidence_timestamp"] == "2026-06-10T00:00:00+00:00"


def test_details_contain_correct_counts(tmp_path):
    contract = _valid_contract()
    contract["screenshots"].append(
        {
            "path": "evidence/screenshots/mobile.png",
            "viewport": "mobile",
        }
    )
    contract["console_errors"] = [{"text": "one"}]
    contract["network_errors"] = [{"url": "http://localhost/missing", "status": 404}]
    bundle_path = _write_contract_bundle(tmp_path, contract)

    gate = build_evidence_quality_gate(bundle_path)

    assert gate["details"] == {
        "screenshots_count": 2,
        "viewport_reports_count": 1,
        "console_errors_count": 1,
        "network_errors_count": 1,
        "has_build_report": True,
    }


def test_adapter_does_not_alter_summary_v1(tmp_path):
    bundle_path = _write_contract_bundle(tmp_path, _valid_contract())
    before = summarize_evidence_bundle(bundle_path)
    snapshot = copy.deepcopy(before)

    build_evidence_quality_gate(bundle_path)
    after = summarize_evidence_bundle(bundle_path)

    assert before == snapshot
    assert after == snapshot
