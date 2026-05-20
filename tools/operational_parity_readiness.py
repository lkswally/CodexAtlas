from __future__ import annotations

import argparse
import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple


DEFAULT_ROOT = Path(__file__).resolve().parents[1]

REQUIRED_ARTIFACTS = {
    "atlas_handoff_envelope": [
        "docs/operational_parity_codex_native.md",
        "policies/operational_parity_policy.md",
        "tools/atlas_dispatcher.py",
    ],
    "evidence_index": [
        "tools/operational_parity_readiness.py",
        "docs/operational_parity_codex_native.md",
    ],
    "delegation_stop_rules": [
        "docs/operational_parity_codex_native.md",
        "policies/operational_parity_policy.md",
    ],
    "context_resume_protocol": [
        "docs/operational_parity_codex_native.md",
        "memory/context_refresh_protocol.md",
        "memory/breadcrumbs.md",
    ],
    "manual_quality_hook_bundle": [
        "docs/operational_parity_codex_native.md",
        "commands/atomic_command_registry.json",
    ],
}

FORBIDDEN_RUNTIME_ARTIFACTS = (
    ".claude",
    "CLAUDE.md",
    "hooks",
    "pixel-bridge",
    "install.sh",
)


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _rel(path: Path, root: Path) -> str:
    try:
        return str(path.relative_to(root)).replace("\\", "/")
    except ValueError:
        return str(path).replace("\\", "/")


def _git_changed_files(root: Path) -> Tuple[List[str], Optional[str]]:
    try:
        process = subprocess.run(
            ["git", "-C", str(root), "status", "--porcelain", "--untracked-files=all"],
            check=False,
            capture_output=True,
            text=True,
            timeout=15,
        )
    except Exception as exc:  # pragma: no cover - depends on local git availability.
        return [], f"git_status_failed:{exc}"

    if process.returncode != 0:
        message = (process.stderr or process.stdout or "").strip()
        return [], f"git_status_failed:{message or process.returncode}"

    changed: List[str] = []
    seen: set[str] = set()
    for line in process.stdout.splitlines():
        if not line.strip():
            continue
        raw_path = line[3:] if len(line) > 3 else line
        if " -> " in raw_path:
            raw_path = raw_path.split(" -> ", 1)[1]
        path = raw_path.strip().replace("\\", "/").strip("/")
        if path and path not in seen:
            seen.add(path)
            changed.append(path)
    return changed, None


def _artifact_status(root: Path, component: str, artifacts: List[str]) -> Dict[str, Any]:
    present = [item for item in artifacts if (root / item).exists()]
    missing = [item for item in artifacts if not (root / item).exists()]
    if missing:
        status = "needs_artifacts"
    else:
        status = "ready"
    return {
        "component": component,
        "status": status,
        "advisory_only": True,
        "present_artifacts": present,
        "missing_artifacts": missing,
    }


def _find_forbidden_runtime_artifacts(root: Path) -> List[str]:
    found: List[str] = []
    for relative in FORBIDDEN_RUNTIME_ARTIFACTS:
        candidate = root / relative
        if candidate.exists():
            found.append(_rel(candidate, root))
    return found


def build_operational_parity_report(root: Path) -> Dict[str, Any]:
    root = root.resolve()
    components = {
        name: _artifact_status(root, name, artifacts)
        for name, artifacts in REQUIRED_ARTIFACTS.items()
    }
    missing_components = [
        name for name, item in components.items() if item["status"] != "ready"
    ]
    forbidden_runtime_artifacts = _find_forbidden_runtime_artifacts(root)
    changed_files, git_error = _git_changed_files(root)

    blockers: List[Dict[str, Any]] = []
    warnings: List[Dict[str, Any]] = []

    if forbidden_runtime_artifacts:
        blockers.append(
            {
                "code": "claude_runtime_artifacts_detected",
                "severity": "blocker",
                "message": "Atlas operational parity must not introduce Claude-only runtime artifacts.",
                "evidence": forbidden_runtime_artifacts,
            }
        )

    for component_name in missing_components:
        warnings.append(
            {
                "code": f"{component_name}_not_closed",
                "severity": "medium",
                "message": f"{component_name} still lacks one or more explicit Atlas artifacts.",
                "evidence": components[component_name]["missing_artifacts"],
            }
        )

    if git_error:
        warnings.append(
            {
                "code": "git_status_unavailable",
                "severity": "low",
                "message": "Atlas could not collect working-tree evidence.",
                "evidence": [git_error],
            }
        )

    if blockers:
        status = "blocked"
    elif warnings:
        status = "needs_improvement"
    else:
        status = "ready"

    return {
        "status": status,
        "root": str(root),
        "benchmark": "Emaleo0522/claude-vibecoding",
        "adaptation_mode": "codex_native_advisory_readiness",
        "components": components,
        "evidence_index": {
            "changed_files": changed_files,
            "git_error": git_error,
            "required_artifacts_checked": sorted(
                {item for values in REQUIRED_ARTIFACTS.values() for item in values}
            ),
            "forbidden_runtime_artifacts_checked": list(FORBIDDEN_RUNTIME_ARTIFACTS),
        },
        "blockers": blockers,
        "warnings": warnings,
        "manual_quality_hook_bundle": [
            "python tools\\atlas_verify.py",
            "python tools\\atlas_governance_check.py",
            "python tools\\atlas_dispatcher.py audit-repo",
            "python tools\\mcp_readiness_check.py",
            "python tools\\atlas_dispatcher.py operational-parity-report",
        ],
        "public_claim": (
            "Atlas adapts operational discipline from the benchmark as explicit, read-only, "
            "Codex-native governance. It does not copy Claude hooks or runtime automation."
        ),
        "advisory_only": True,
        "timestamp": _utc_now_iso(),
    }


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(add_help=True)
    parser.add_argument("--root", default=None, help="Atlas root to inspect.")
    args = parser.parse_args(argv)

    root = Path(args.root).resolve() if args.root else DEFAULT_ROOT
    report = build_operational_parity_report(root)
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if report["status"] in {"ready", "needs_improvement"} else 1


if __name__ == "__main__":
    raise SystemExit(main())
