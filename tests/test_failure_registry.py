import json

import pytest

from tools.failure_registry import (
    FAILURE_RECORD_FIELDS,
    FailureRecordValidationError,
    create_failure_record,
    read_failure_record,
    validate_failure_record,
    write_failure_record,
)


def _valid_record():
    return create_failure_record(
        failure_id="failure-atlas-ci-001",
        timestamp="2026-06-11T00:00:00+00:00",
        task_type="test_execution_analysis",
        status="FAIL",
        summary="Atlas CI governance check rejected the routing configuration.",
        root_cause="The validator expected the legacy routing schema.",
        resolution="Added strict support for Model Routing Policy V1.",
        evidence_ref="github-actions:27251498044",
        source_commit="cfed81a",
        tags=["ci", "governance", "model-routing"],
    )


def test_creates_valid_record():
    record = _valid_record()

    assert tuple(record.keys()) == FAILURE_RECORD_FIELDS
    assert record["failure_id"] == "failure-atlas-ci-001"
    assert record["status"] == "FAIL"


def test_validates_valid_record():
    result = validate_failure_record(_valid_record())

    assert result == {"status": "PASS", "valid": True, "findings": []}


def test_missing_field_fails_validation():
    record = _valid_record()
    del record["summary"]

    result = validate_failure_record(record)

    assert result["valid"] is False
    assert any(item.get("field") == "summary" for item in result["findings"])


def test_extra_field_fails_validation():
    record = _valid_record()
    record["stack_trace"] = "not allowed"

    result = validate_failure_record(record)

    assert result["valid"] is False
    assert any(item["code"] == "unexpected_field" for item in result["findings"])


def test_invalid_status_fails_validation():
    record = _valid_record()
    record["status"] = "PASS"

    result = validate_failure_record(record)

    assert result["valid"] is False
    assert any(item["code"] == "invalid_status" for item in result["findings"])


def test_invalid_tags_fail_validation():
    record = _valid_record()
    record["tags"] = ["ci", 3]

    result = validate_failure_record(record)

    assert result["valid"] is False
    assert any(item["code"] == "invalid_tags" for item in result["findings"])


def test_create_rejects_non_list_tags():
    with pytest.raises(FailureRecordValidationError):
        create_failure_record(
            task_type="test_execution_analysis",
            status="WARN",
            summary="A test emitted a warning.",
            root_cause="The local environment differed from CI.",
            tags="ci",
        )


def test_write_read_roundtrip(tmp_path):
    record = _valid_record()
    output_path = tmp_path / "failure.json"

    written = write_failure_record(record, output_path)
    loaded = read_failure_record(output_path)

    assert written == output_path
    assert loaded == record
    assert json.loads(output_path.read_text(encoding="utf-8")) == record


@pytest.mark.parametrize("secret", ["sk-example", "ghp_example", "password=value", "token=value", ".env"])
def test_rejects_obvious_secret_patterns(secret):
    record = _valid_record()
    record["root_cause"] = f"Unsafe diagnostic contained {secret}."

    result = validate_failure_record(record)

    assert result["valid"] is False
    assert any(item["code"] == "potential_secret_detected" for item in result["findings"])


def test_create_rejects_obvious_secret():
    with pytest.raises(FailureRecordValidationError):
        create_failure_record(
            task_type="security_review",
            status="BLOCKED",
            summary="A token= value was exposed.",
            root_cause="Unsafe input.",
        )


def test_allows_empty_resolution():
    record = _valid_record()
    record["resolution"] = ""

    assert validate_failure_record(record)["valid"] is True


def test_allows_empty_evidence_ref():
    record = _valid_record()
    record["evidence_ref"] = ""

    assert validate_failure_record(record)["valid"] is True


def test_allows_empty_source_commit():
    record = _valid_record()
    record["source_commit"] = ""

    assert validate_failure_record(record)["valid"] is True


def test_read_rejects_invalid_record(tmp_path):
    record = _valid_record()
    record["status"] = "PASS"
    output_path = tmp_path / "failure.json"
    output_path.write_text(json.dumps(record), encoding="utf-8")

    with pytest.raises(FailureRecordValidationError):
        read_failure_record(output_path)
