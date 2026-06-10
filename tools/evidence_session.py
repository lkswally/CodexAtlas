from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List

from tools.evidence_contract_validator import validate_evidence_contract


BUNDLE_VERSION = "v1"
BUNDLE_FIELDS = (
    "contract_version",
    "validation_status",
    "evidence_timestamp",
    "source_commit",
    "screenshots",
    "viewport_reports",
    "console_errors",
    "network_errors",
    "build_report",
)


class EvidenceSessionError(ValueError):
    def __init__(self, message: str, findings: List[Dict[str, str]]) -> None:
        super().__init__(message)
        self.findings = findings


class EvidenceBundleWriteError(OSError):
    pass


class EvidenceBundleReadError(ValueError):
    pass


def build_evidence_bundle(contract: Any) -> Dict[str, Any]:
    validation = validate_evidence_contract(contract)
    if not validation["valid"]:
        raise EvidenceSessionError("Evidence Contract V1 validation failed.", validation["findings"])

    bundle = {
        "contract_version": BUNDLE_VERSION,
        "validation_status": validation["status"],
        "evidence_timestamp": contract["evidence_timestamp"],
        "source_commit": contract["source_commit"],
        "screenshots": contract["screenshots"],
        "viewport_reports": contract["viewport_reports"],
        "console_errors": contract["console_errors"],
        "network_errors": contract["network_errors"],
        "build_report": contract["build_report"],
    }
    return {field: bundle[field] for field in BUNDLE_FIELDS}


def _validate_evidence_bundle(bundle: Any) -> Dict[str, Any]:
    if not isinstance(bundle, dict):
        raise EvidenceBundleReadError("Evidence Bundle V1 must be a JSON object.")

    expected = set(BUNDLE_FIELDS)
    actual = set(bundle.keys())
    missing = sorted(expected - actual)
    extra = sorted(actual - expected)
    if missing:
        raise EvidenceBundleReadError(f"Evidence Bundle V1 is missing fields: {', '.join(missing)}.")
    if extra:
        raise EvidenceBundleReadError(f"Evidence Bundle V1 has unexpected fields: {', '.join(extra)}.")

    if bundle["contract_version"] != BUNDLE_VERSION:
        raise EvidenceBundleReadError("Evidence Bundle V1 must have contract_version `v1`.")
    if bundle["validation_status"] != "PASS":
        raise EvidenceBundleReadError("Evidence Bundle V1 must have validation_status `PASS`.")

    for field in ("screenshots", "viewport_reports", "console_errors", "network_errors"):
        if not isinstance(bundle[field], list):
            raise EvidenceBundleReadError(f"Evidence Bundle V1 field `{field}` must be a list.")
    if not isinstance(bundle["build_report"], dict):
        raise EvidenceBundleReadError("Evidence Bundle V1 field `build_report` must be a dict.")
    for field in ("evidence_timestamp", "source_commit"):
        if not isinstance(bundle[field], str) or not bundle[field].strip():
            raise EvidenceBundleReadError(f"Evidence Bundle V1 field `{field}` must be a non-empty string.")

    return {field: bundle[field] for field in BUNDLE_FIELDS}


def write_evidence_bundle(bundle: Dict[str, Any], output_path: Path) -> Path:
    path = Path(output_path)
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        rendered = json.dumps(
            {field: bundle[field] for field in BUNDLE_FIELDS},
            ensure_ascii=False,
            indent=2,
        )
        path.write_text(rendered + "\n", encoding="utf-8")
    except (KeyError, OSError, TypeError, ValueError) as exc:
        raise EvidenceBundleWriteError(f"Could not write Evidence Bundle V1 to `{path}`.") from exc
    return path


def read_evidence_bundle(path: Path) -> Dict[str, Any]:
    bundle_path = Path(path)
    try:
        payload = json.loads(bundle_path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise EvidenceBundleReadError(f"Evidence Bundle V1 file does not exist: `{bundle_path}`.") from exc
    except json.JSONDecodeError as exc:
        raise EvidenceBundleReadError(f"Evidence Bundle V1 file is not valid JSON: `{bundle_path}`.") from exc
    except OSError as exc:
        raise EvidenceBundleReadError(f"Could not read Evidence Bundle V1 from `{bundle_path}`.") from exc
    return _validate_evidence_bundle(payload)
