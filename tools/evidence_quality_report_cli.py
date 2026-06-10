from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import List, Optional

from tools.evidence_quality_report import build_evidence_quality_report


def main(argv: Optional[List[str]] = None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    if len(args) != 1:
        print("Usage: evidence_quality_report_cli.py <bundle-json-path>", file=sys.stderr)
        return 1

    report = build_evidence_quality_report(Path(args[0]))
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 1 if report["result"] == "FAIL" else 0


if __name__ == "__main__":
    raise SystemExit(main())
