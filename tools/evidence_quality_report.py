from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict

from tools.evidence_quality_gate_adapter import build_evidence_quality_gate


REPORT_NAME = "evidence_quality_report"
REPORT_MODE = "opt_in_non_blocking"
RECOMMENDATIONS = {
    "PASS": "Evidence bundle is technically healthy.",
    "WARN": "Evidence bundle has warnings; review before approval.",
    "FAIL": "Evidence bundle failed technical validation; do not approve as PASS.",
}


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def build_evidence_quality_report(path: Path) -> Dict[str, Any]:
    try:
        gate = build_evidence_quality_gate(path)
    except Exception as exc:
        gate = {
            "gate_name": "evidence_bundle_quality",
            "status": "FAIL",
            "source": "evidence_summary_v1",
            "source_commit": "",
            "evidence_timestamp": "",
            "warnings": [],
            "failures": [str(exc)],
            "details": {
                "screenshots_count": 0,
                "viewport_reports_count": 0,
                "console_errors_count": 0,
                "network_errors_count": 0,
                "has_build_report": False,
            },
        }

    result = gate["status"]
    return {
        "report_name": REPORT_NAME,
        "mode": REPORT_MODE,
        "gate": gate,
        "result": result,
        "blocking": False,
        "recommendation": RECOMMENDATIONS[result],
        "generated_at": _utc_now_iso(),
    }
