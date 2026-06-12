from __future__ import annotations

import json
import re
import unicodedata
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


class FailureSimilarityLookupError(ValueError):
    pass


def _finding(code: str, message: str, field: Optional[str] = None) -> Dict[str, str]:
    item = {"code": code, "message": message}
    if field:
        item["field"] = field
    return item


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _normalized_tokens(value: str) -> set[str]:
    normalized = unicodedata.normalize("NFKD", value.casefold())
    without_marks = "".join(char for char in normalized if not unicodedata.combining(char))
    return set(re.findall(r"[a-z0-9]+", without_marks))


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


def find_similar_failures(
    query: str,
    records: List[Dict[str, Any]],
    *,
    min_overlap: int = 1,
) -> List[Dict[str, Any]]:
    if not isinstance(query, str) or not query.strip():
        raise FailureSimilarityLookupError("Failure similarity query must be a non-empty string.")
    if isinstance(min_overlap, bool) or not isinstance(min_overlap, int) or min_overlap < 1:
        raise FailureSimilarityLookupError("Failure similarity min_overlap must be an integer >= 1.")
    if not isinstance(records, list):
        raise FailureSimilarityLookupError("Failure similarity records must be a list.")

    query_tokens = _normalized_tokens(query)
    matches: List[Dict[str, Any]] = []
    for index, record in enumerate(records):
        validation = validate_failure_record(record)
        if not validation["valid"]:
            raise FailureRecordValidationError(
                f"Failure Record V1 validation failed at records[{index}].",
                validation["findings"],
            )

        searchable_values = [
            record["summary"],
            record["root_cause"],
            record["task_type"],
            *record["tags"],
        ]
        record_tokens: set[str] = set()
        for value in searchable_values:
            record_tokens.update(_normalized_tokens(value))
        matched_terms = sorted(query_tokens & record_tokens)
        if len(matched_terms) < min_overlap:
            continue
        matches.append(
            {
                "failure_id": record["failure_id"],
                "overlap_score": len(matched_terms),
                "matched_terms": matched_terms,
                "summary": record["summary"],
                "root_cause": record["root_cause"],
                "resolution": record["resolution"],
                "evidence_ref": record["evidence_ref"],
                "source_commit": record["source_commit"],
            }
        )

    return sorted(matches, key=lambda item: (-item["overlap_score"], item["failure_id"]))
