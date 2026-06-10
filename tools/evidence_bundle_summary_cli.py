from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import List, Optional

from tools.evidence_bundle_summary import summarize_evidence_bundle


def main(argv: Optional[List[str]] = None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    if len(args) != 1:
        print("Usage: evidence_bundle_summary_cli.py <bundle-json-path>", file=sys.stderr)
        return 1

    summary = summarize_evidence_bundle(Path(args[0]))
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 1 if summary["status"] == "FAIL" else 0


if __name__ == "__main__":
    raise SystemExit(main())
