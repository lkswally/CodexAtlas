from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Dict, List, Optional


CONTRACT_FIELDS = (
    "screenshots",
    "viewport_reports",
    "build_report",
    "console_errors",
    "network_errors",
    "evidence_timestamp",
    "source_commit",
)


def _finding(code: str, message: str, field: Optional[str] = None) -> Dict[str, str]:
    item = {"code": code, "message": message}
    if field:
        item["field"] = field
    return item


def validate_evidence_contract(contract: Any) -> Dict[str, Any]:
    findings: List[Dict[str, str]] = []

    if not isinstance(contract, dict):
        return {
            "status": "FAIL",
            "valid": False,
            "findings": [
                _finding("contract_not_object", "Evidence Contract V1 must be a JSON object.")
            ],
        }

    expected = set(CONTRACT_FIELDS)
    actual = set(contract.keys())
    for field in CONTRACT_FIELDS:
        if field not in contract:
            findings.append(
                _finding("missing_required_field", f"Missing required field `{field}`.", field)
            )
    for field in sorted(actual - expected):
        findings.append(
            _finding("unexpected_field", f"Unexpected field `{field}` is not part of Evidence Contract V1.", field)
        )

    type_checks = {
        "screenshots": list,
        "viewport_reports": list,
        "build_report": dict,
        "console_errors": list,
        "network_errors": list,
        "evidence_timestamp": str,
        "source_commit": str,
    }
    for field, expected_type in type_checks.items():
        if field not in contract:
            continue
        if not isinstance(contract[field], expected_type):
            findings.append(
                _finding(
                    "invalid_field_type",
                    f"Field `{field}` must be `{expected_type.__name__}`.",
                    field,
                )
            )

    for field in ("evidence_timestamp", "source_commit"):
        value = contract.get(field)
        if isinstance(value, str) and not value.strip():
            findings.append(
                _finding("empty_required_string", f"Field `{field}` must be a non-empty string.", field)
            )

    screenshots = contract.get("screenshots")
    if isinstance(screenshots, list):
        for index, item in enumerate(screenshots):
            field = f"screenshots[{index}]"
            if not isinstance(item, dict):
                findings.append(
                    _finding("invalid_screenshot_item", f"`{field}` must be an object.", field)
                )
                continue
            for required in ("path", "viewport"):
                value = item.get(required)
                if not isinstance(value, str) or not value.strip():
                    findings.append(
                        _finding(
                            "invalid_screenshot_item",
                            f"`{field}.{required}` must be a non-empty string.",
                            field,
                        )
                    )

    valid = not findings
    return {
        "status": "PASS" if valid else "FAIL",
        "valid": valid,
        "findings": findings,
    }


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(add_help=True)
    parser.add_argument("--contract", required=True, help="Path to an Evidence Contract V1 JSON file.")
    args = parser.parse_args(argv)

    path = Path(args.contract).resolve()
    payload = json.loads(path.read_text(encoding="utf-8-sig"))
    result = validate_evidence_contract(payload)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["valid"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
