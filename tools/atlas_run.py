from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from tools.atlas_codex_executor import execute_via_atlas_codex
from tools.atlas_context_audit import audit_project_context
from tools.atlas_dispatcher import dispatch
from tools.atlas_orchestrator import get_skill_execution_behavior_specs, orchestrate_task
from tools.atlas_project_bootstrap import ATLAS_ROOT, DERIVED_PROJECTS_REGISTRY


REGISTRY_PATH = ATLAS_ROOT / "commands" / "atomic_command_registry.json"
PHASE_PLAYBOOK_PATH = ATLAS_ROOT / "config" / "phase_playbook.json"
DIRECT_CODEX_BLOCK_MESSAGE = "Esta tarea requiere ATLAS completo. Ejecutá atlas_run.py o atlas.ps1."


def _read_json(path: Path) -> Dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def _load_skill_registry(root: Path) -> Dict[str, Any]:
    registry: Dict[str, Any] = {}
    for skill_dir in sorted((root / "skills").iterdir()):
        if not skill_dir.is_dir() or skill_dir.name.startswith("_"):
            continue
        skill_json = skill_dir / "skill.json"
        if not skill_json.exists():
            continue
        try:
            registry[skill_dir.name] = _read_json(skill_json)
        except Exception:
            continue
    return registry


def _read_sprint_status(project_path: Path) -> str:
    for name in ("SPRINT_STATUS.md", "PROJECT_STATUS.md"):
        path = project_path / name
        if path.exists():
            return path.read_text(encoding="utf-8")
    return ""


def _functional_work_allowed(audit: Dict[str, Any], task: str, sprint_status_text: str) -> Dict[str, Any]:
    if not audit.get("functional_work_allowed", False):
        return {
            "allowed": False,
            "reason": audit.get("why", "Atlas governance is incomplete."),
        }

    normalized_task = task.lower()
    normalized_status = sprint_status_text.lower()
    if "product qa" in normalized_status or "demo readiness" in normalized_status:
        task_tokens = set(re.findall(r"[a-z0-9]+", normalized_task))
        if "empty state" in normalized_task or "empty states" in normalized_task:
            return {"allowed": True, "reason": "Task fits the current Product QA / Demo Readiness sprint guardrail."}
        if {"qa", "demo"} & task_tokens:
            return {"allowed": True, "reason": "Task fits the current Product QA / Demo Readiness sprint guardrail."}
        if "copy" in task_tokens and {"cta", "hero", "button", "microcopy", "landing"} & task_tokens:
            return {"allowed": True, "reason": "Task fits the current Product QA / Demo Readiness sprint guardrail."}
        return {
            "allowed": False,
            "reason": "Current sprint only allows Product QA / Demo Readiness work.",
        }
    return {"allowed": True, "reason": "No narrower sprint restriction blocks this task."}


def _build_plan(task: str, phase_report: Dict[str, Any], route: Dict[str, Any]) -> List[str]:
    plan: List[str] = []
    plan.extend([f"Confirm current phase: {phase_report.get('current_phase')}", "Use Atlas-selected workflow and skill guidance"])
    if route.get("recommended_skill"):
        plan.append(f"Route task through skill `{route['recommended_skill']}`")
    if route.get("recommended_workflow"):
        plan.append(f"Follow workflow `{route['recommended_workflow']}`")
    if route.get("next_action"):
        plan.append(str(route["next_action"]))
    plan.append(f"Task focus: {task}")
    return plan[:5]


def run_atlas(
    *,
    project_path: Path,
    task: str,
    mode: str,
    dry_run: bool,
    require_dispatcher: bool,
) -> Dict[str, Any]:
    project_path = project_path.resolve()
    audit = audit_project_context(project_path)
    registry_checked = REGISTRY_PATH.exists()
    project_registry_checked = DERIVED_PROJECTS_REGISTRY.exists()
    phase_playbook_checked = PHASE_PLAYBOOK_PATH.exists()
    skill_registry = _load_skill_registry(ATLAS_ROOT)
    behavior_registry = get_skill_execution_behavior_specs(ATLAS_ROOT)

    blockers: List[Dict[str, str]] = []
    if not audit.get("git_repo_root"):
        blockers.append({"severity": "blocker", "code": "missing_git_root", "message": DIRECT_CODEX_BLOCK_MESSAGE})
    if not audit.get("has_local_agents"):
        blockers.append({"severity": "blocker", "code": "missing_local_agents", "message": DIRECT_CODEX_BLOCK_MESSAGE})
    if not audit.get("has_atlas_project_json"):
        blockers.append({"severity": "blocker", "code": "missing_atlas_project_json", "message": DIRECT_CODEX_BLOCK_MESSAGE})
    if not audit.get("has_status_file"):
        blockers.append({"severity": "blocker", "code": "missing_status_file", "message": DIRECT_CODEX_BLOCK_MESSAGE})
    if require_dispatcher and not audit.get("dispatcher_exists"):
        blockers.append({"severity": "blocker", "code": "missing_dispatcher", "message": "Atlas dispatcher is required."})
    if require_dispatcher and not audit.get("command_registry_exists"):
        blockers.append({"severity": "blocker", "code": "missing_command_registry", "message": "Atlas command registry is required."})

    phase_report_output: Optional[Dict[str, Any]] = None
    dispatcher_invoked = False
    phase_gate_checked = False
    route: Dict[str, Any] = {}
    executor_result: Dict[str, Any] = {"status": "blocked", "codex_executor_ready": False}
    plan: List[str] = []
    functional_gate = {"allowed": False, "reason": "Atlas prerequisites not satisfied yet."}

    if not blockers:
        phase_dispatch = dispatch("project-phase-report", root=ATLAS_ROOT, project=project_path)
        dispatcher_invoked = True
        phase_report_output = phase_dispatch.output.get("result", {})
        phase_gate_checked = True
        route = orchestrate_task(task, root=ATLAS_ROOT)
        functional_gate = _functional_work_allowed(audit, task, _read_sprint_status(project_path))
        plan = _build_plan(task, phase_report_output, route)
        executor_result = execute_via_atlas_codex(
            project_path=project_path,
            task=task,
            mode=mode,
            dry_run=dry_run,
            workflow=str(route.get("recommended_workflow", "orchestrator_routing")),
            agent=str(route.get("recommended_agent", "orchestrator")),
            skill=route.get("recommended_skill"),
            plan=plan,
        )

    operating_mode = "ATLAS completo" if not blockers else audit.get("operating_mode", "Codex directo bloqueado")
    status = "ready" if not blockers else "blocked"
    envelope = {
        "status": status,
        "tarea": task,
        "archivos": [str(project_path)],
        "verificacion": {
            "status": status,
            "findings_count": 0 if not blockers else len(blockers),
            "blockers_count": len(blockers),
            "warnings_count": 0,
        },
        "bloqueadores": blockers,
        "notas": plan or [DIRECT_CODEX_BLOCK_MESSAGE],
    }

    return {
        "status": status,
        "project_path": str(project_path),
        "task": task,
        "mode": mode,
        "dry_run": dry_run,
        "operating_mode": operating_mode,
        "dispatcher_invoked": dispatcher_invoked,
        "registry_checked": registry_checked and project_registry_checked and phase_playbook_checked,
        "phase_gate_checked": phase_gate_checked,
        "agent_selected": bool(route.get("recommended_agent")),
        "codex_executor_ready": bool(executor_result.get("codex_executor_ready")),
        "functional_work_allowed": functional_gate["allowed"],
        "functional_work_reason": functional_gate["reason"],
        "context_audit": audit,
        "phase_report": phase_report_output,
        "route": {
            "recommended_agent": route.get("recommended_agent"),
            "recommended_skill": route.get("recommended_skill"),
            "recommended_workflow": route.get("recommended_workflow"),
            "next_action": route.get("next_action"),
        },
        "skill_registry_size": len(skill_registry),
        "behavior_registry_size": len(behavior_registry),
        "executor": executor_result,
        "plan": plan,
        "envelope": envelope,
    }


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Mandatory Atlas entrypoint before Codex execution.")
    parser.add_argument("--project-path", required=True)
    parser.add_argument("--task", required=True)
    parser.add_argument("--mode", choices=["plan", "execute", "audit"], required=True)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument(
        "--require-dispatcher",
        default="true",
        choices=["true", "false"],
        help="Whether dispatcher/registry are mandatory for the run.",
    )
    args = parser.parse_args(argv)

    result = run_atlas(
        project_path=Path(args.project_path),
        task=args.task,
        mode=args.mode,
        dry_run=args.dry_run,
        require_dispatcher=args.require_dispatcher == "true",
    )
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0 if result["status"] == "ready" else 1


if __name__ == "__main__":
    raise SystemExit(main())
