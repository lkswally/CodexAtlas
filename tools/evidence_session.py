from __future__ import annotations

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
