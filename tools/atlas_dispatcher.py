from __future__ import annotations

import argparse
import importlib.util
import json
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional


DEFAULT_ROOT = Path(__file__).resolve().parents[1]
CANONICAL_TOOLS_DIR = Path(__file__).resolve().parent


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _read_json(path: Path) -> Dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8-sig"))


@dataclass(frozen=True)
class DispatchResult:
    ok: bool
    output: Dict[str, Any]
    exit_code: int


def _is_canonical_root(root: Path) -> bool:
    return root.resolve() == DEFAULT_ROOT.resolve()


def _registry_path(root: Path) -> Path:
    primary = root / "commands" / "atomic_command_registry.json"
    legacy = root / "00_SISTEMA" / "_meta" / "atlas" / "atomic_command_registry.json"
    if _is_canonical_root(root) or primary.exists():
        return primary
    return legacy


def _project_metadata_path(project_root: Path) -> Path:
    return project_root / ".atlas-project.json"


def _load_registry(root: Path) -> Dict[str, Any]:
    reg_path = _registry_path(root)
    if not reg_path.exists():
        raise FileNotFoundError(f"missing_registry:{reg_path}")
    registry = _read_json(reg_path)
    if not isinstance(registry, dict):
        raise ValueError("invalid_registry_root")
    return registry


def _load_project_metadata(project_root: Path) -> Dict[str, Any]:
    path = _project_metadata_path(project_root)
    if not path.exists():
        raise FileNotFoundError(f"missing_project_metadata:{path}")
    data = _read_json(path)
    if not isinstance(data, dict):
        raise ValueError("invalid_project_metadata_root")
    return data


def _find_command(registry: Dict[str, Any], command_id: str) -> Optional[Dict[str, Any]]:
    commands = registry.get("commands", [])
    if not isinstance(commands, list):
        return None
    for cmd in commands:
        if isinstance(cmd, dict) and str(cmd.get("id", "")).strip() == command_id:
            return cmd
    return None


def _load_canonical_governance_check():
    path = CANONICAL_TOOLS_DIR / "atlas_governance_check.py"
    spec = importlib.util.spec_from_file_location("_atlas_canonical_governance_check", str(path))
    if not spec or not spec.loader:
        raise RuntimeError("failed_to_load_governance_check_spec")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _run_governance_check(root: Path) -> Dict[str, Any]:
    mod = _load_canonical_governance_check()
    result = mod.run_check(root=root)
    if not isinstance(result, dict) or "ok" not in result or "findings" not in result:
        return {"ok": False, "findings": ["governance_check_return_invalid"]}
    return {"ok": bool(result["ok"]), "findings": list(result["findings"])}


def _run_project_governance_check(root: Path, project_root: Path) -> Dict[str, Any]:
    mod = _load_canonical_governance_check()
    result = mod.run_check(root=root, project=project_root)
    if not isinstance(result, dict) or "ok" not in result or "findings" not in result:
        return {"ok": False, "findings": ["governance_check_return_invalid"]}
    return {
        "ok": bool(result["ok"]),
        "findings": list(result["findings"]),
        "atlas": result.get("atlas"),
        "project": result.get("project"),
    }


def _load_bootstrap_contract(root: Path) -> Dict[str, Any]:
    path = root / "skills" / "project-bootstrap" / "bootstrap_contract.json"
    if not path.exists():
        return {}
    data = _read_json(path)
    return data if isinstance(data, dict) else {}


def _recommendation_from_issue(issue_code: str) -> str:
    recommendations = {
        "missing_project_metadata": "Generate or restore `.atlas-project.json` using the canonical Atlas bootstrap contract.",
        "invalid_project_type": "Set `project_type` to `atlas-derived-project` in `.atlas-project.json`.",
        "invalid_derived_from": "Set `derived_from` to `Codex-Atlas` so the derivative relationship stays explicit.",
        "invalid_atlas_root": "Point `atlas_root` to the canonical `C:\\Proyectos\\Codex-Atlas` path.",
        "missing_required_file": "Restore the missing root document so the derived project can be audited and handed off safely.",
        "missing_required_directory": "Create the missing minimum Atlas-derived directory at the project root.",
        "missing_profile_directory": "Align the project structure with the expected directories of its declared `project_profile`.",
        "unknown_project_profile": "Use a supported `project_profile` from the bootstrap contract or remove the field until it is defined.",
        "atlas_core_residue": "Remove Atlas core internals from the derived project and keep only `.atlas-project.json` as the integration surface.",
        "claude_artifact": "Remove Claude-specific artifacts from the derived project and keep the repo Codex-native.",
        "embedded_atlas_tool": "Move Atlas dispatcher/governance tooling back to the canonical Atlas repo and operate from outside with `--project`.",
    }
    return recommendations.get(issue_code, "Review the finding and realign the derived project with the Atlas factory contract.")


def _append_issue(
    findings: List[Dict[str, str]],
    recommendations: List[str],
    severity: str,
    issue_code: str,
    message: str,
    path: Optional[str] = None,
) -> None:
    finding: Dict[str, str] = {
        "severity": severity,
        "code": issue_code,
        "message": message,
    }
    if path:
        finding["path"] = path
    findings.append(finding)
    recommendation = _recommendation_from_issue(issue_code)
    if recommendation not in recommendations:
        recommendations.append(recommendation)


def _certification_score(blockers: List[Dict[str, str]], warnings: List[Dict[str, str]]) -> int:
    return max(0, 100 - (len(blockers) * 20) - (len(warnings) * 7))


def _expected_profile_directories(root: Path, profile: str) -> List[str]:
    contract = _load_bootstrap_contract(root)
    if not contract:
        return []
    base_dirs = list(contract.get("generated_structure", {}).get("directories", []))
    profile_dirs = list(contract.get("templates_by_type", {}).get(profile, {}).get("additional_directories", []))
    expected: List[str] = []
    for item in base_dirs + profile_dirs:
        item_s = str(item).strip()
        if item_s and item_s not in expected:
            expected.append(item_s)
    return expected


def _certify_project_stub(
    root: Path,
    project_root: Path,
    command: Dict[str, Any],
    project_metadata: Optional[Dict[str, Any]],
) -> Dict[str, Any]:
    findings: List[Dict[str, str]] = []
    blockers: List[Dict[str, str]] = []
    warnings: List[Dict[str, str]] = []
    recommendations: List[str] = []

    metadata = project_metadata or {}
    if not metadata:
        issue = {
            "severity": "blocker",
            "code": "missing_project_metadata",
            "message": "Missing `.atlas-project.json` prevents derivative certification.",
            "path": str(_project_metadata_path(project_root)),
        }
        blockers.append(issue)
        findings.append(issue)
        recommendations.append(_recommendation_from_issue("missing_project_metadata"))
        return {
            "status": "partial",
            "summary": {
                "target_root": str(project_root),
                "score": _certification_score(blockers, warnings),
                "certification_status": "failed",
                "project_profile": None,
            },
            "blockers": blockers,
            "warnings": warnings,
            "findings": findings,
            "recommendations": recommendations,
        }

    project_type = str(metadata.get("project_type", "")).strip()
    if project_type != "atlas-derived-project":
        _append_issue(
            blockers,
            recommendations,
            "blocker",
            "invalid_project_type",
            f"Expected `project_type = atlas-derived-project` but found `{project_type or 'empty'}`.",
            path=str(_project_metadata_path(project_root)),
        )

    derived_from = str(metadata.get("derived_from", "")).strip()
    if derived_from != "Codex-Atlas":
        _append_issue(
            blockers,
            recommendations,
            "blocker",
            "invalid_derived_from",
            f"Expected `derived_from = Codex-Atlas` but found `{derived_from or 'empty'}`.",
            path=str(_project_metadata_path(project_root)),
        )

    atlas_root = str(metadata.get("atlas_root", "")).strip()
    if atlas_root != str(root):
        _append_issue(
            blockers,
            recommendations,
            "blocker",
            "invalid_atlas_root",
            f"Expected `atlas_root = {root}` but found `{atlas_root or 'empty'}`.",
            path=str(_project_metadata_path(project_root)),
        )

    for rel in ("README.md", "AGENTS.md"):
        path = project_root / rel
        if not path.exists():
            _append_issue(
                blockers,
                recommendations,
                "blocker",
                "missing_required_file",
                f"Missing required root file `{rel}`.",
                path=str(path),
            )

    minimum_dirs = ["docs", "memory", "workflows", "policies", "tools"]
    for rel in minimum_dirs:
        path = project_root / rel
        if not path.exists() or not path.is_dir():
            _append_issue(
                blockers,
                recommendations,
                "blocker",
                "missing_required_directory",
                f"Missing minimum directory `{rel}/`.",
                path=str(path),
            )

    project_profile = str(metadata.get("project_profile", "")).strip()
    if project_profile:
        expected_profile_dirs = _expected_profile_directories(root, project_profile)
        if expected_profile_dirs:
            for rel in expected_profile_dirs:
                path = project_root / rel
                if not path.exists() or not path.is_dir():
                    _append_issue(
                        blockers,
                        recommendations,
                        "blocker",
                        "missing_profile_directory",
                        f"Declared profile `{project_profile}` expects `{rel}/` but it is missing.",
                        path=str(path),
                    )
        else:
            _append_issue(
                warnings,
                recommendations,
                "warning",
                "unknown_project_profile",
                f"Unknown `project_profile` `{project_profile}`; Atlas cannot validate profile-specific directories.",
                path=str(_project_metadata_path(project_root)),
            )

    forbidden_atlas_paths = (
        ("00_SISTEMA/_meta/atlas", "atlas_core_residue"),
        ("commands/atomic_command_registry.json", "atlas_core_residue"),
        ("tools/atlas_dispatcher.py", "embedded_atlas_tool"),
        ("tools/atlas_governance_check.py", "embedded_atlas_tool"),
    )
    for rel, issue_code in forbidden_atlas_paths:
        path = project_root / rel
        if path.exists():
            _append_issue(
                blockers,
                recommendations,
                "blocker",
                issue_code,
                f"Derived project contains forbidden Atlas internal path `{rel}`.",
                path=str(path),
            )

    claude_artifacts = (
        (".claude", "Claude-specific `.claude` directory should not exist in a Codex-native derived project."),
        ("CLAUDE.md", "`CLAUDE.md` should not be the source of truth in a Codex-native derived project."),
    )
    for rel, message in claude_artifacts:
        path = project_root / rel
        if path.exists():
            _append_issue(
                blockers,
                recommendations,
                "blocker",
                "claude_artifact",
                message,
                path=str(path),
            )

    for issue in blockers:
        findings.append(issue)
    for issue in warnings:
        findings.append(issue)

    score = _certification_score(blockers, warnings)
    certification_status = "passed"
    if blockers:
        certification_status = "failed"
    elif warnings:
        certification_status = "warning"

    return {
        "status": "ok" if not blockers else "partial",
        "summary": {
            "target_root": str(project_root),
            "project_profile": project_profile or None,
            "score": score,
            "certification_status": certification_status,
            "checked_paths": command.get("allowed_paths", []),
        },
        "blockers": blockers,
        "warnings": warnings,
        "findings": findings,
        "recommendations": recommendations,
    }


def _audit_repo_stub(target_root: Path, command: Dict[str, Any], project_metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    allowed = command.get("allowed_paths", [])
    if project_metadata is not None:
        allowed = project_metadata.get("audit_paths", allowed)
    if not isinstance(allowed, list) or not allowed:
        return {"status": "error", "summary": {}, "findings": ["invalid_allowed_paths"]}

    present: List[str] = []
    missing: List[str] = []
    counts: Dict[str, int] = {}

    for rel in allowed:
        rel_s = str(rel).strip()
        if not rel_s:
            continue
        path = (target_root / rel_s).resolve()
        if path.exists():
            present.append(rel_s)
            if path.is_dir():
                try:
                    counts[rel_s] = sum(1 for _ in path.iterdir())
                except Exception:
                    counts[rel_s] = -1
        else:
            missing.append(rel_s)

    findings: List[str] = []
    if missing:
        findings.append(f"missing_allowed_paths:{','.join(missing)}")

    return {
        "status": "ok" if not missing else "partial",
        "summary": {
            "target_root": str(target_root),
            "present_allowed_paths": present,
            "missing_allowed_paths": missing,
            "entry_counts": counts,
        },
        "findings": findings,
        "recommended_next_steps": [
            "Fix missing allowlisted paths or update registry allowed_paths (docs-only decision)." if missing else
            "Registry allowlist matches current structure."
        ],
    }


def _run_workflow(
    command_id: str,
    root: Path,
    target_root: Path,
    cmd: Dict[str, Any],
    project_metadata: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    if command_id == "audit-repo":
        return _audit_repo_stub(target_root, cmd, project_metadata=project_metadata)
    if command_id == "certify-project":
        return _certify_project_stub(root, target_root, cmd, project_metadata=project_metadata)
    return {"status": "error", "summary": {}, "findings": ["workflow_not_implemented_in_minimal_mode"]}


def dispatch(command_id: str, root: Optional[Path] = None, project: Optional[Path] = None) -> DispatchResult:
    root = (root or DEFAULT_ROOT).resolve()
    target_root = (project or root).resolve()
    started_at = _utc_now_iso()
    t0 = time.time()

    try:
        registry = _load_registry(root)
    except Exception as exc:
        return DispatchResult(
            ok=False,
            exit_code=2,
            output={"ok": False, "command": command_id, "started_at": started_at, "error": f"registry_load_failed:{exc}"},
        )

    cmd = _find_command(registry, command_id)
    if not cmd:
        return DispatchResult(
            ok=False,
            exit_code=2,
            output={
                "ok": False,
                "command": command_id,
                "started_at": started_at,
                "error": "unknown_command",
                "known_commands": [
                    c.get("id") for c in registry.get("commands", []) if isinstance(c, dict) and c.get("id")
                ],
            },
        )

    project_metadata = None
    project_metadata_error: Optional[str] = None
    if project is not None:
        try:
            project_metadata = _load_project_metadata(target_root)
        except Exception as exc:
            project_metadata_error = f"{exc}"
            if command_id == "certify-project":
                project_metadata = None
            else:
                return DispatchResult(
                    ok=False,
                    exit_code=2,
                    output={
                        "ok": False,
                        "command": command_id,
                        "alias": cmd.get("alias"),
                        "started_at": started_at,
                        "error": f"project_metadata_load_failed:{exc}",
                        "project_root": str(target_root),
                    },
                )

    governance_before = _run_project_governance_check(root, target_root) if project is not None else _run_governance_check(root)
    if not governance_before.get("ok", False) and command_id != "certify-project":
        return DispatchResult(
            ok=False,
            exit_code=2,
            output={
                "ok": False,
                "command": command_id,
                "alias": cmd.get("alias"),
                "started_at": started_at,
                "error": "governance_check_failed_before_execution",
                "governance": governance_before,
            },
        )

    if command_id not in {"audit-repo", "certify-project"}:
        return DispatchResult(
            ok=False,
            exit_code=2,
            output={"ok": False, "command": command_id, "alias": cmd.get("alias"), "started_at": started_at, "error": "workflow_not_implemented_in_minimal_mode"},
        )

    if command_id == "certify-project" and project is None:
        return DispatchResult(
            ok=False,
            exit_code=2,
            output={
                "ok": False,
                "command": command_id,
                "alias": cmd.get("alias"),
                "started_at": started_at,
                "error": "certify_project_requires_project",
            },
        )

    if str(cmd.get("execution_mode", "")).strip() != "read_only":
        return DispatchResult(
            ok=False,
            exit_code=2,
            output={
                "ok": False,
                "command": command_id,
                "alias": cmd.get("alias"),
                "started_at": started_at,
                "error": "audit_repo_must_be_read_only",
            },
        )

    result = _run_workflow(command_id, root, target_root, cmd, project_metadata=project_metadata)
    if project_metadata_error and command_id == "certify-project":
        result.setdefault("warnings", []).append(
            {
                "severity": "warning",
                "code": "project_metadata_load_error",
                "message": f"Project metadata could not be loaded before certification: {project_metadata_error}",
                "path": str(_project_metadata_path(target_root)),
            }
        )
        result.setdefault("findings", []).append(result["warnings"][-1])
        recommendation = "Create a valid `.atlas-project.json` before relying on Atlas certification."
        if recommendation not in result.setdefault("recommendations", []):
            result["recommendations"].append(recommendation)

    governance_after = _run_project_governance_check(root, target_root) if project is not None else _run_governance_check(root)
    elapsed_ms = int((time.time() - t0) * 1000)
    finished_at = _utc_now_iso()
    ok = isinstance(result, dict) and result.get("status") in {"ok", "partial"}
    if command_id != "certify-project":
        ok = ok and bool(governance_after.get("ok", False))

    return DispatchResult(
        ok=ok,
        exit_code=0 if ok else 2,
        output={
            "ok": ok,
            "command": command_id,
            "alias": cmd.get("alias"),
            "purpose": cmd.get("purpose"),
            "execution_mode": cmd.get("execution_mode"),
            "root": str(root),
            "target_project": str(target_root) if project is not None else None,
            "started_at": started_at,
            "finished_at": finished_at,
            "elapsed_ms": elapsed_ms,
            "result": result,
            "governance": {"before": governance_before, "after": governance_after},
        },
    )


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(add_help=True)
    parser.add_argument("--root", default=None, help="Workspace root to dispatch against (defaults to this repo root).")
    parser.add_argument("--project", default=None, help="Derived project root to audit from Atlas.")
    parser.add_argument("command_id", nargs="?", help="Command id (example: audit-repo)")
    args = parser.parse_args(argv)

    if not args.command_id:
        print("Usage: python tools/atlas_dispatcher.py [--root <path>] [--project <path>] <command_id>")
        print("Example: python tools/atlas_dispatcher.py audit-repo")
        print(r"Example: python tools/atlas_dispatcher.py --project C:\Proyectos\REYESOFT audit-repo")
        print(r"Example: python tools/atlas_dispatcher.py --project C:\Proyectos\ATLAS_SANDBOX_DEMO_TEMPLATES certify-project")
        return 2

    root = Path(args.root).resolve() if args.root else None
    project = Path(args.project).resolve() if args.project else None
    res = dispatch(args.command_id.strip(), root=root, project=project)
    print(json.dumps(res.output, ensure_ascii=False, indent=2))
    return res.exit_code


if __name__ == "__main__":
    raise SystemExit(main())
