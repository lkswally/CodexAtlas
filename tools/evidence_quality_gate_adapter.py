from __future__ import annotations

from pathlib import Path
from typing import Any, Dict

from tools.evidence_bundle_summary import summarize_evidence_bundle


GATE_NAME = "evidence_bundle_quality"
SOURCE_NAME = "evidence_summary_v1"


def build_evidence_quality_gate(path: Path) -> Dict[str, Any]:
    summary = summarize_evidence_bundle(path)
    return {
        "gate_name": GATE_NAME,
        "status": summary["status"],
        "source": SOURCE_NAME,
        "source_commit": summary["source_commit"],
        "evidence_timestamp": summary["evidence_timestamp"],
        "warnings": list(summary["warnings"]),
        "failures": list(summary["failures"]),
        "details": {
            "screenshots_count": summary["screenshots_count"],
            "viewport_reports_count": summary["viewport_reports_count"],
            "console_errors_count": summary["console_errors_count"],
            "network_errors_count": summary["network_errors_count"],
            "has_build_report": summary["has_build_report"],
        },
    }
