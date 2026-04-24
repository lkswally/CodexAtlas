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


def _run_workflow(command_id: str, target_root: Path, cmd: Dict[str, Any], project_metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    if command_id != "audit-repo":
        return {"status": "error", "summary": {}, "findings": ["workflow_not_implemented_in_minimal_mode"]}
    return _audit_repo_stub(target_root, cmd, project_metadata=project_metadata)


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
    if project is not None:
        try:
            project_metadata = _load_project_metadata(target_root)
        except Exception as exc:
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
    if not governance_before.get("ok", False):
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

    if command_id != "audit-repo":
        return DispatchResult(
            ok=False,
            exit_code=2,
            output={"ok": False, "command": command_id, "alias": cmd.get("alias"), "started_at": started_at, "error": "workflow_not_implemented_in_minimal_mode"},
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

    result = _run_workflow(command_id, target_root, cmd, project_metadata=project_metadata)
    governance_after = _run_project_governance_check(root, target_root) if project is not None else _run_governance_check(root)
    elapsed_ms = int((time.time() - t0) * 1000)
    finished_at = _utc_now_iso()
    ok = bool(governance_after.get("ok", False)) and isinstance(result, dict) and result.get("status") in {"ok", "partial"}

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
        return 2

    root = Path(args.root).resolve() if args.root else None
    project = Path(args.project).resolve() if args.project else None
    res = dispatch(args.command_id.strip(), root=root, project=project)
    print(json.dumps(res.output, ensure_ascii=False, indent=2))
    return res.exit_code


if __name__ == "__main__":
    raise SystemExit(main())
