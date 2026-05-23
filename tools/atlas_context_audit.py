from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from tools.atlas_project_bootstrap import ATLAS_ROOT, DERIVED_PROJECTS_REGISTRY, detect_runtime_markers, infer_project_profile


GLOBAL_CODEX_ROOT = Path.home() / ".codex"
GLOBAL_AGENTS = GLOBAL_CODEX_ROOT / "AGENTS.md"
GLOBAL_CONFIG = GLOBAL_CODEX_ROOT / "config.toml"
DISPATCHER = ATLAS_ROOT / "tools" / "atlas_dispatcher.py"
REGISTRY = ATLAS_ROOT / "commands" / "atomic_command_registry.json"
PHASE_PLAYBOOK = ATLAS_ROOT / "config" / "phase_playbook.json"


def _find_git_root(project_root: Path) -> Optional[Path]:
    current = project_root.resolve()
    for candidate in (current, *current.parents):
        if (candidate / ".git").exists():
            return candidate
    return None


def _load_derived_projects_registry() -> Dict[str, Any]:
    if not DERIVED_PROJECTS_REGISTRY.exists():
        return {"schema_version": "1.0", "projects": []}
    try:
        data = json.loads(DERIVED_PROJECTS_REGISTRY.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {"schema_version": "1.0", "projects": []}
    if not isinstance(data, dict):
        return {"schema_version": "1.0", "projects": []}
    return data


def _project_registered(project_root: Path) -> bool:
    registry = _load_derived_projects_registry()
    for item in registry.get("projects", []):
        if isinstance(item, dict) and str(item.get("project_root", "")).strip() == str(project_root.resolve()):
            return True
    return False


def audit_project_context(project_root: Path) -> Dict[str, Any]:
    project_root = project_root.resolve()
    git_root = _find_git_root(project_root)
    local_agents = project_root / "AGENTS.md"
    atlas_json = project_root / ".atlas-project.json"
    sprint_status = project_root / "SPRINT_STATUS.md"
    project_status = project_root / "PROJECT_STATUS.md"

    has_git = git_root is not None
    has_local_agents = local_agents.exists()
    has_atlas_json = atlas_json.exists()
    has_status = sprint_status.exists() or project_status.exists()
    project_registered = _project_registered(project_root)

    missing: List[str] = []
    if not has_git:
        missing.append("git_root")
    if not has_local_agents:
        missing.append("AGENTS.md")
    if not has_atlas_json:
        missing.append(".atlas-project.json")
    if not has_status:
        missing.append("status_file")

    if not missing and project_registered:
        operating_mode = "ATLAS completo"
    elif has_local_agents or has_atlas_json or has_status or project_registered:
        operating_mode = "ATLAS gobernanza ligera"
    else:
        operating_mode = "Codex directo bloqueado"

    functional_work_allowed = not missing
    runtime_markers = detect_runtime_markers(project_root)

    allowed_work = (
        ["functional implementation under Atlas controls", "governance maintenance", "dispatcher-led audits"]
        if functional_work_allowed
        else ["create governance files", "prepare bootstrap", "generate an audit report", "initialize Git with approval"]
    )
    blocked_work = (
        []
        if functional_work_allowed
        else ["functional implementation", "major architecture changes", "external integrations", "hidden automation"]
    )

    return {
        "status": "ok",
        "project_root": str(project_root),
        "git_repo_root": str(git_root) if git_root else None,
        "global_instruction_files_read": [str(path) for path in (GLOBAL_AGENTS, GLOBAL_CONFIG) if path.exists()],
        "local_instruction_files_read": [str(path) for path in (local_agents, sprint_status, project_status) if path.exists()],
        "has_atlas_project_json": has_atlas_json,
        "has_local_agents": has_local_agents,
        "has_status_file": has_status,
        "atlas_linked": has_atlas_json,
        "project_registered": project_registered,
        "dispatcher_exists": DISPATCHER.exists(),
        "command_registry_exists": REGISTRY.exists(),
        "phase_playbook_exists": PHASE_PLAYBOOK.exists(),
        "runtime_markers": runtime_markers,
        "project_profile_guess": infer_project_profile(project_root),
        "operating_mode": operating_mode,
        "functional_work_allowed": functional_work_allowed,
        "direct_codex_detected": operating_mode == "Codex directo bloqueado",
        "missing_governance": missing,
        "allowed_work": allowed_work,
        "blocked_work": blocked_work,
        "mandatory_checks": [
            "atlas_context_audit",
            "atlas dispatcher availability",
            "local project build/test checks once governance is complete",
        ],
        "suggested_git_init_command": None if has_git else f'git init "{project_root}"',
        "why": (
            "Project has the minimum Atlas governance surface."
            if functional_work_allowed
            else "Functional implementation is blocked until Atlas governance files and Git root are present."
        ),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Audit whether a project is operating under Atlas governance.")
    parser.add_argument("--project", required=True, help="Project root to audit.")
    args = parser.parse_args()
    result = audit_project_context(Path(args.project))
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
