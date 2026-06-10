from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List

from tools.evidence_session import read_evidence_bundle


def _empty_summary() -> Dict[str, Any]:
    return {
        "status": "FAIL",
        "contract_version": "",
        "source_commit": "",
        "evidence_timestamp": "",
        "screenshots_count": 0,
        "viewport_reports_count": 0,
        "console_errors_count": 0,
        "network_errors_count": 0,
        "has_build_report": False,
        "warnings": [],
        "failures": [],
    }


def summarize_evidence_bundle(path: Path) -> Dict[str, Any]:
    try:
        bundle = read_evidence_bundle(path)
    except Exception as exc:
        summary = _empty_summary()
        summary["failures"].append(str(exc))
        return summary

    warnings: List[str] = []
    failures: List[str] = []
    screenshots_count = len(bundle["screenshots"])
    viewport_reports_count = len(bundle["viewport_reports"])
    console_errors_count = len(bundle["console_errors"])
    network_errors_count = len(bundle["network_errors"])

    if bundle["validation_status"] != "PASS":
        failures.append("Evidence Bundle validation_status is not PASS.")
    if screenshots_count == 0:
        warnings.append("Evidence Bundle has no screenshots.")
    if viewport_reports_count == 0:
        warnings.append("Evidence Bundle has no viewport reports.")
    if console_errors_count > 0:
        warnings.append("Evidence Bundle contains console errors.")
    if network_errors_count > 0:
        warnings.append("Evidence Bundle contains network errors.")

    status = "PASS"
    if failures:
        status = "FAIL"
    elif warnings:
        status = "WARN"

    return {
        "status": status,
        "contract_version": bundle["contract_version"],
        "source_commit": bundle["source_commit"],
        "evidence_timestamp": bundle["evidence_timestamp"],
        "screenshots_count": screenshots_count,
        "viewport_reports_count": viewport_reports_count,
        "console_errors_count": console_errors_count,
        "network_errors_count": network_errors_count,
        "has_build_report": isinstance(bundle["build_report"], dict),
        "warnings": warnings,
        "failures": failures,
    }
