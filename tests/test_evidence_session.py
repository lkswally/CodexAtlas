import json

import pytest

from tools.evidence_session import (
    EvidenceBundleReadError,
    EvidenceBundleWriteError,
    EvidenceSessionError,
    build_evidence_bundle,
    read_evidence_bundle,
    write_evidence_bundle,
)


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
        "build_report": {"status": "skipped"},
        "console_errors": [],
        "network_errors": [],
        "evidence_timestamp": "2026-06-10T00:00:00+00:00",
        "source_commit": "abc123",
    }


def test_valid_contract_builds_bundle():
    bundle = build_evidence_bundle(_valid_contract())

    assert bundle == {
        "contract_version": "v1",
        "validation_status": "PASS",
        "evidence_timestamp": "2026-06-10T00:00:00+00:00",
        "source_commit": "abc123",
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
        "console_errors": [],
        "network_errors": [],
        "build_report": {"status": "skipped"},
    }


def test_invalid_contract_raises_controlled_exception():
    contract = _valid_contract()
    del contract["screenshots"]

    with pytest.raises(EvidenceSessionError) as excinfo:
        build_evidence_bundle(contract)

    assert "Evidence Contract V1 validation failed." in str(excinfo.value)
    assert excinfo.value.findings


def test_validation_status_is_pass():
    bundle = build_evidence_bundle(_valid_contract())

    assert bundle["validation_status"] == "PASS"


def test_contract_version_is_v1():
    bundle = build_evidence_bundle(_valid_contract())

    assert bundle["contract_version"] == "v1"


def test_preserves_screenshots():
    contract = _valid_contract()
    bundle = build_evidence_bundle(contract)

    assert bundle["screenshots"] == contract["screenshots"]


def test_preserves_viewport_reports():
    contract = _valid_contract()
    bundle = build_evidence_bundle(contract)

    assert bundle["viewport_reports"] == contract["viewport_reports"]


def test_preserves_build_report():
    contract = _valid_contract()
    bundle = build_evidence_bundle(contract)

    assert bundle["build_report"] == contract["build_report"]


def test_preserves_source_commit():
    contract = _valid_contract()
    bundle = build_evidence_bundle(contract)

    assert bundle["source_commit"] == contract["source_commit"]


def test_writes_valid_bundle_to_file(tmp_path):
    bundle = build_evidence_bundle(_valid_contract())
    output_path = tmp_path / "bundle.json"

    written_path = write_evidence_bundle(bundle, output_path)

    assert written_path == output_path
    assert output_path.exists()
    assert output_path.read_text(encoding="utf-8").startswith("{\n  \"contract_version\"")


def test_reads_written_bundle_and_preserves_content(tmp_path):
    bundle = build_evidence_bundle(_valid_contract())
    output_path = tmp_path / "bundle.json"

    write_evidence_bundle(bundle, output_path)
    loaded = json.loads(output_path.read_text(encoding="utf-8"))

    assert loaded == bundle
    assert loaded["contract_version"] == bundle["contract_version"]
    assert loaded["validation_status"] == bundle["validation_status"]
    assert loaded["evidence_timestamp"] == bundle["evidence_timestamp"]
    assert loaded["source_commit"] == bundle["source_commit"]
    assert loaded["screenshots"] == bundle["screenshots"]
    assert loaded["viewport_reports"] == bundle["viewport_reports"]
    assert loaded["console_errors"] == bundle["console_errors"]
    assert loaded["network_errors"] == bundle["network_errors"]
    assert loaded["build_report"] == bundle["build_report"]


def test_invalid_bundle_output_fails_controlled(tmp_path):
    bundle = build_evidence_bundle(_valid_contract())
    del bundle["source_commit"]

    with pytest.raises(EvidenceBundleWriteError):
        write_evidence_bundle(bundle, tmp_path / "bundle.json")


def test_reads_valid_persisted_bundle(tmp_path):
    bundle = build_evidence_bundle(_valid_contract())
    output_path = tmp_path / "bundle.json"
    write_evidence_bundle(bundle, output_path)

    loaded = read_evidence_bundle(output_path)

    assert loaded == bundle


def test_read_missing_path_fails_controlled(tmp_path):
    with pytest.raises(EvidenceBundleReadError):
        read_evidence_bundle(tmp_path / "missing.json")


def test_read_invalid_json_fails_controlled(tmp_path):
    output_path = tmp_path / "bundle.json"
    output_path.write_text("{not-json", encoding="utf-8")

    with pytest.raises(EvidenceBundleReadError):
        read_evidence_bundle(output_path)


def test_read_missing_field_fails_controlled(tmp_path):
    bundle = build_evidence_bundle(_valid_contract())
    del bundle["screenshots"]
    output_path = tmp_path / "bundle.json"
    output_path.write_text(json.dumps(bundle), encoding="utf-8")

    with pytest.raises(EvidenceBundleReadError):
        read_evidence_bundle(output_path)


def test_read_extra_field_fails_controlled(tmp_path):
    bundle = build_evidence_bundle(_valid_contract())
    bundle["score"] = 100
    output_path = tmp_path / "bundle.json"
    output_path.write_text(json.dumps(bundle), encoding="utf-8")

    with pytest.raises(EvidenceBundleReadError):
        read_evidence_bundle(output_path)


def test_read_invalid_contract_version_fails_controlled(tmp_path):
    bundle = build_evidence_bundle(_valid_contract())
    bundle["contract_version"] = "v2"
    output_path = tmp_path / "bundle.json"
    output_path.write_text(json.dumps(bundle), encoding="utf-8")

    with pytest.raises(EvidenceBundleReadError):
        read_evidence_bundle(output_path)


def test_read_non_pass_validation_status_fails_controlled(tmp_path):
    bundle = build_evidence_bundle(_valid_contract())
    bundle["validation_status"] = "FAIL"
    output_path = tmp_path / "bundle.json"
    output_path.write_text(json.dumps(bundle), encoding="utf-8")

    with pytest.raises(EvidenceBundleReadError):
        read_evidence_bundle(output_path)


def test_read_invalid_types_fail_controlled(tmp_path):
    bundle = build_evidence_bundle(_valid_contract())
    bundle["network_errors"] = {}
    output_path = tmp_path / "bundle.json"
    output_path.write_text(json.dumps(bundle), encoding="utf-8")

    with pytest.raises(EvidenceBundleReadError):
        read_evidence_bundle(output_path)
