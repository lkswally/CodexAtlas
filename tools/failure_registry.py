from __future__ import annotations

import json
import re
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional


FAILURE_RECORD_FIELDS = (
    "failure_id",
    "timestamp",
    "task_type",
    "status",
    "summary",
    "root_cause",
    "resolution",
    "evidence_ref",
    "source_commit",
    "tags",
)
FAILURE_STATUSES = {"FAIL", "WARN", "BLOCKED"}
SENSITIVE_FIELDS = ("summary", "root_cause", "resolution")
SECRET_PATTERNS = (
    re.compile(r"sk-", re.IGNORECASE),
    re.compile(r"ghp_", re.IGNORECASE),
    re.compile(r"password\s*=", re.IGNORECASE),
    re.compile(r"token\s*=", re.IGNORECASE),
    re.compile(r"\.env", re.IGNORECASE),
)


class FailureRecordValidationError(ValueError):
    def __init__(self, message: str, findings: List[Dict[str, str]]) -> None:
        super().__init__(message)
        self.findings = findings


class FailureRecordWriteError(OSError):
    pass


class FailureRecordReadError(ValueError):
    pass


def _finding(code: str, message: str, field: Optional[str] = None) -> Dict[str, str]:
    item = {"code": code, "message": message}
    if field:
        item["field"] = field
    return item


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def validate_failure_record(record: Any) -> Dict[str, Any]:
    findings: List[Dict[str, str]] = []
    if not isinstance(record, dict):
        return {
            "status": "FAIL",
            "valid": False,
            "findings": [
                _finding("record_not_object", "Failure Record V1 must be a JSON object.")
            ],
        }

    expected = set(FAILURE_RECORD_FIELDS)
    actual = set(record.keys())
    for field in FAILURE_RECORD_FIELDS:
        if field not in record:
            findings.append(
                _finding("missing_required_field", f"Missing required field `{field}`.", field)
            )
    for field in sorted(actual - expected):
        findings.append(
            _finding(
                "unexpected_field",
                f"Unexpected field `{field}` is not part of Failure Record V1.",
                field,
            )
        )

    required_strings = ("failure_id", "timestamp", "task_type", "summary", "root_cause")
    optional_strings = ("resolution", "evidence_ref", "source_commit")
    for field in required_strings:
        if field not in record:
            continue
        value = record[field]
        if not isinstance(value, str):
            findings.append(
                _finding("invalid_field_type", f"Field `{field}` must be `str`.", field)
            )
        elif not value.strip():
            findings.append(
                _finding("empty_required_string", f"Field `{field}` must be non-empty.", field)
            )
    for field in optional_strings:
        if field in record and not isinstance(record[field], str):
            findings.append(
                _finding("invalid_field_type", f"Field `{field}` must be `str`.", field)
            )

    status = record.get("status")
    if not isinstance(status, str) or status not in FAILURE_STATUSES:
        findings.append(
            _finding(
                "invalid_status",
                "Field `status` must be one of: BLOCKED, FAIL, WARN.",
                "status",
            )
        )

    tags = record.get("tags")
    if not isinstance(tags, list) or any(not isinstance(tag, str) for tag in tags):
        findings.append(
            _finding("invalid_tags", "Field `tags` must be a list of strings.", "tags")
        )

    for field in SENSITIVE_FIELDS:
        value = record.get(field)
        if not isinstance(value, str):
            continue
        if any(pattern.search(value) for pattern in SECRET_PATTERNS):
            findings.append(
                _finding(
                    "potential_secret_detected",
                    f"Field `{field}` contains a prohibited secret-like pattern.",
                    field,
                )
            )

    valid = not findings
    return {
        "status": "PASS" if valid else "FAIL",
        "valid": valid,
        "findings": findings,
    }


def create_failure_record(
    *,
    task_type: str,
    status: str,
    summary: str,
    root_cause: str,
    resolution: str = "",
    evidence_ref: str = "",
    source_commit: str = "",
    tags: Optional[List[str]] = None,
    failure_id: Optional[str] = None,
    timestamp: Optional[str] = None,
) -> Dict[str, Any]:
    record = {
        "failure_id": failure_id or f"failure-{uuid.uuid4().hex}",
        "timestamp": timestamp or _utc_now_iso(),
        "task_type": task_type,
        "status": status,
        "summary": summary,
        "root_cause": root_cause,
        "resolution": resolution,
        "evidence_ref": evidence_ref,
        "source_commit": source_commit,
        "tags": tags if tags is not None else [],
    }
    validation = validate_failure_record(record)
    if not validation["valid"]:
        raise FailureRecordValidationError(
            "Failure Record V1 validation failed.", validation["findings"]
        )
    return {field: record[field] for field in FAILURE_RECORD_FIELDS}


def write_failure_record(record: Any, path: Path) -> Path:
    validation = validate_failure_record(record)
    if not validation["valid"]:
        raise FailureRecordValidationError(
            "Failure Record V1 validation failed.", validation["findings"]
        )

    output_path = Path(path)
    try:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        payload = {field: record[field] for field in FAILURE_RECORD_FIELDS}
        output_path.write_text(
            json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
    except (OSError, TypeError, ValueError) as exc:
        raise FailureRecordWriteError("Could not write Failure Record V1.") from exc
    return output_path


def read_failure_record(path: Path) -> Dict[str, Any]:
    record_path = Path(path)
    try:
        payload = json.loads(record_path.read_text(encoding="utf-8-sig"))
    except FileNotFoundError as exc:
        raise FailureRecordReadError("Failure Record V1 file does not exist.") from exc
    except json.JSONDecodeError as exc:
        raise FailureRecordReadError("Failure Record V1 file is not valid JSON.") from exc
    except OSError as exc:
        raise FailureRecordReadError("Could not read Failure Record V1.") from exc

    validation = validate_failure_record(payload)
    if not validation["valid"]:
        raise FailureRecordValidationError(
            "Failure Record V1 validation failed.", validation["findings"]
        )
    return {field: payload[field] for field in FAILURE_RECORD_FIELDS}
