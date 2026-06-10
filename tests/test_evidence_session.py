import pytest

from tools.evidence_session import EvidenceSessionError, build_evidence_bundle


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
