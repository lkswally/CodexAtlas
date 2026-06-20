import copy

import pytest

from tools.architecture_state_model import (
    ARCHITECTURE_DOMAINS,
    ArchitectureStateError,
    build_architecture_state,
    validate_architecture_state,
)


def _pass_observations():
    return {
        domain: {
            "status": "PASS",
            "evidence": [f"{domain}:verified"],
            "freshness": {"is_stale": False},
            "risks": [],
            "dependencies": [],
            "confidence": 0.9,
            "next_actions": [],
        }
        for domain in ARCHITECTURE_DOMAINS
    }


def test_default_state_is_unknown_and_complete():
    report = build_architecture_state(generated_at="2026-06-19T00:00:00+00:00")

    assert report["overall_status"] == "UNKNOWN"
    assert tuple(report["domains"]) == ARCHITECTURE_DOMAINS
    assert all(item["status"] == "UNKNOWN" for item in report["domains"].values())
    assert validate_architecture_state(report) is True


def test_all_domains_pass_only_with_evidence():
    report = build_architecture_state(_pass_observations())

    assert report["overall_status"] == "PASS"
    assert report["domains"]["governance"]["evidence"] == ["governance:verified"]


def test_pass_without_evidence_is_rejected_to_unknown():
    report = build_architecture_state({"governance": {"status": "PASS", "confidence": 1.0}})
    domain = report["domains"]["governance"]

    assert domain["status"] == "UNKNOWN"
    assert "pass_without_evidence_rejected" in domain["risks"]
    assert report["overall_status"] == "UNKNOWN"


def test_stale_pass_is_downgraded_to_warn():
    observations = _pass_observations()
    observations["workflows"]["freshness"] = {"is_stale": True, "age_hours": 200}

    report = build_architecture_state(observations)

    assert report["domains"]["workflows"]["status"] == "WARN"
    assert "stale_pass_downgraded" in report["domains"]["workflows"]["risks"]
    assert report["overall_status"] == "WARN"


def test_fail_has_priority_for_overall_status():
    observations = _pass_observations()
    observations["security"]["status"] = "FAIL"

    assert build_architecture_state(observations)["overall_status"] == "FAIL"


def test_unknown_mixed_with_pass_produces_warn():
    observations = _pass_observations()
    observations.pop("docs")

    assert build_architecture_state(observations)["overall_status"] == "WARN"


def test_invalid_input_values_are_normalized_conservatively():
    report = build_architecture_state(
        {
            "mcp": {
                "status": "CONNECTED",
                "evidence": "not-a-list",
                "freshness": "fresh",
                "risks": "none",
                "dependencies": "network",
                "confidence": 5,
                "next_actions": "ship",
            }
        }
    )
    domain = report["domains"]["mcp"]

    assert domain["status"] == "UNKNOWN"
    assert domain["evidence"] == []
    assert domain["freshness"] == {}
    assert domain["dependencies"] == []
    assert domain["confidence"] == 1.0
    assert "invalid_status_rejected" in domain["risks"]


def test_validator_rejects_missing_report_fields():
    with pytest.raises(ArchitectureStateError, match="missing required fields"):
        validate_architecture_state({"overall_status": "PASS"})


def test_validator_rejects_missing_domain():
    report = build_architecture_state()
    del report["domains"]["release"]

    with pytest.raises(ArchitectureStateError, match="every canonical domain"):
        validate_architecture_state(report)


def test_validator_rejects_manual_pass_without_evidence():
    report = build_architecture_state()
    report["domains"]["governance"]["status"] = "PASS"

    with pytest.raises(ArchitectureStateError, match="cannot PASS without evidence"):
        validate_architecture_state(report)


@pytest.mark.parametrize(
    ("mutation", "message"),
    [
        (lambda r: r.update(overall_status="READY"), "overall_status"),
        (lambda r: r["domains"]["docs"].update(confidence=2), "between 0 and 1"),
        (lambda r: r["domains"]["docs"].update(freshness=[]), "freshness"),
        (lambda r: r["domains"]["docs"].update(risks="none"), "risks"),
    ],
)
def test_validator_rejects_invalid_contract_values(mutation, message):
    report = copy.deepcopy(build_architecture_state())
    mutation(report)

    with pytest.raises(ArchitectureStateError, match=message):
        validate_architecture_state(report)

def test_validator_rejects_inconsistent_overall_status():
    report = build_architecture_state()
    report["overall_status"] = "PASS"

    with pytest.raises(ArchitectureStateError, match="must be UNKNOWN"):
        validate_architecture_state(report)
