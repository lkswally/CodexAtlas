import copy

from tools.evidence_quality_gate_adapter import build_evidence_quality_gate
from tools.evidence_quality_report import build_evidence_quality_report
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


def test_pass_bundle_builds_pass_report_non_blocking(tmp_path):
    bundle_path = _write_contract_bundle(tmp_path, _valid_contract())

    report = build_evidence_quality_report(bundle_path)

    assert report["report_name"] == "evidence_quality_report"
    assert report["mode"] == "opt_in_non_blocking"
    assert report["result"] == "PASS"
    assert report["blocking"] is False


def test_warn_bundle_builds_warn_report_non_blocking(tmp_path):
    contract = _valid_contract()
    contract["screenshots"] = []
    bundle_path = _write_contract_bundle(tmp_path, contract)

    report = build_evidence_quality_report(bundle_path)

    assert report["result"] == "WARN"
    assert report["blocking"] is False


def test_invalid_path_builds_fail_report_non_blocking(tmp_path):
    report = build_evidence_quality_report(tmp_path / "missing.json")

    assert report["result"] == "FAIL"
    assert report["blocking"] is False
    assert report["gate"]["failures"]


def test_report_includes_complete_gate(tmp_path):
    bundle_path = _write_contract_bundle(tmp_path, _valid_contract())
    gate = build_evidence_quality_gate(bundle_path)

    report = build_evidence_quality_report(bundle_path)

    assert report["gate"] == gate


def test_pass_recommendation_is_correct(tmp_path):
    bundle_path = _write_contract_bundle(tmp_path, _valid_contract())

    report = build_evidence_quality_report(bundle_path)

    assert report["recommendation"] == "Evidence bundle is technically healthy."


def test_warn_recommendation_is_correct(tmp_path):
    contract = _valid_contract()
    contract["viewport_reports"] = []
    bundle_path = _write_contract_bundle(tmp_path, contract)

    report = build_evidence_quality_report(bundle_path)

    assert report["recommendation"] == "Evidence bundle has warnings; review before approval."


def test_fail_recommendation_is_correct(tmp_path):
    report = build_evidence_quality_report(tmp_path / "missing.json")

    assert report["recommendation"] == "Evidence bundle failed technical validation; do not approve as PASS."


def test_generated_at_is_non_empty(tmp_path):
    bundle_path = _write_contract_bundle(tmp_path, _valid_contract())

    report = build_evidence_quality_report(bundle_path)

    assert isinstance(report["generated_at"], str)
    assert report["generated_at"].strip()


def test_report_does_not_alter_adapter_output(tmp_path):
    bundle_path = _write_contract_bundle(tmp_path, _valid_contract())
    before = build_evidence_quality_gate(bundle_path)
    snapshot = copy.deepcopy(before)

    build_evidence_quality_report(bundle_path)
    after = build_evidence_quality_gate(bundle_path)

    assert before == snapshot
    assert after == snapshot
