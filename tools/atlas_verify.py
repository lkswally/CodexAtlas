from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

try:
    from tools.atlas_dispatcher import dispatch
    from tools.atlas_governance_check import run_check
except ModuleNotFoundError:
    from atlas_dispatcher import dispatch
    from atlas_governance_check import run_check


DEFAULT_ROOT = Path(__file__).resolve().parents[1]


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _summarize_dispatch(command_id: str, output: Dict[str, Any]) -> Dict[str, Any]:
    result = output.get("result", {}) if isinstance(output, dict) else {}
    return {
        "command": command_id,
        "ok": bool(output.get("ok", False)),
        "status": str(result.get("status", "failed")).strip() or "failed",
        "error": output.get("error"),
        "summary": result.get("summary"),
        "warnings": result.get("warnings", []),
        "findings": result.get("findings", []),
        "recommended_next_steps": result.get("recommended_next_steps", []),
    }


def _governance_summary(result: Dict[str, Any]) -> Dict[str, Any]:
    findings = list(result.get("findings", []))
    return {
        "command": "governance-check",
        "ok": bool(result.get("ok", False)),
        "status": "ok" if bool(result.get("ok", False)) else "failed",
        "findings": findings,
        "findings_count": len(findings),
        "profile": result.get("profile"),
    }


def build_verify_report(root: Path, project: Optional[Path] = None) -> Dict[str, Any]:
    root = root.resolve()
    project = project.resolve() if project else None

    governance = run_check(root=root, project=project)
    audit_repo = dispatch("audit-repo", root=root, project=project).output
    surface_audit = dispatch("surface-audit", root=root).output

    checks: Dict[str, Dict[str, Any]] = {
        "governance_check": _governance_summary(governance),
        "audit_repo": _summarize_dispatch("audit-repo", audit_repo),
        "surface_audit": _summarize_dispatch("surface-audit", surface_audit),
    }

    if project is not None:
        quality_gate = dispatch("quality-gate-report", root=root, project=project).output
        checks["quality_gate_report"] = _summarize_dispatch("quality-gate-report", quality_gate)
        checks["quality_gate_report"]["overall_status"] = (
            quality_gate.get("result", {}).get("overall_status")
        )
        checks["quality_gate_report"]["public_readiness"] = (
            quality_gate.get("result", {}).get("public_readiness")
        )

    failed_checks = [name for name, item in checks.items() if not bool(item.get("ok", False))]
    warnings: List[str] = []
    evidence: List[str] = []
    next_action = "Post-setup verification passed. Keep using the existing Atlas commands as the canonical workflow."
    status = "ok"

    for name, item in checks.items():
        evidence.append(f"{name}:{item.get('status')}")
        if item.get("findings"):
            warnings.append(f"{name} reported findings")
        if item.get("warnings"):
            warnings.append(f"{name} reported warnings")

    if failed_checks:
        status = "failed"
        next_action = f"Resolve the first failing check: {failed_checks[0]}."
    elif project is not None:
        quality_overall = str(
            checks.get("quality_gate_report", {}).get("overall_status", "")
        ).strip()
        if quality_overall and quality_overall != "ready":
            status = "needs_attention"
            next_action = (
                "Project verification is structurally healthy, but the quality gate still needs follow-up."
            )

    return {
        "status": status,
        "root": str(root),
        "project": str(project) if project else None,
        "checks": checks,
        "warnings": warnings,
        "evidence": evidence,
        "failed_checks": failed_checks,
        "next_action": next_action,
        "timestamp": _utc_now_iso(),
    }


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(add_help=True)
    parser.add_argument("--root", default=None, help="Atlas root to verify.")
    parser.add_argument("--project", default=None, help="Optional derived project path for quality-gate verification.")
    args = parser.parse_args(argv)

    root = Path(args.root).resolve() if args.root else DEFAULT_ROOT
    project = Path(args.project).resolve() if args.project else None
    report = build_verify_report(root, project=project)
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if report["status"] in {"ok", "needs_attention"} else 1


if __name__ == "__main__":
    raise SystemExit(main())
