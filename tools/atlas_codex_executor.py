from __future__ import annotations

import argparse
import json
import subprocess
import tempfile
from pathlib import Path
from typing import Any, Dict, List, Optional


DEFAULT_ROOT = Path(__file__).resolve().parent.parent


def _build_codex_prompt(*, project_path: Path, task: str, plan: List[str], workflow: str, agent: str, skill: Optional[str]) -> str:
    plan_block = "\n".join(f"{idx + 1}. {item}" for idx, item in enumerate(plan)) if plan else "1. Follow the validated Atlas plan."
    skill_line = skill or "none"
    return (
        "This task is being executed under CODEX ATLAS.\n\n"
        f"Project: {project_path}\n"
        f"Workflow: {workflow}\n"
        f"Agent: {agent}\n"
        f"Skill: {skill_line}\n"
        f"Task: {task}\n\n"
        "Validated Atlas plan:\n"
        f"{plan_block}\n\n"
        "Respect local governance and do not bypass Atlas phase gates."
    )


def codex_executor_readiness() -> Dict[str, Any]:
    try:
        process = subprocess.run(
            ["codex", "--version"],
            check=False,
            capture_output=True,
            text=True,
            timeout=20,
        )
    except Exception as exc:
        return {
            "status": "blocked",
            "codex_executor_ready": False,
            "reason": f"codex_cli_unavailable:{exc}",
        }
    return {
        "status": "ready" if process.returncode == 0 else "blocked",
        "codex_executor_ready": process.returncode == 0,
        "stdout": (process.stdout or "").strip(),
        "stderr": (process.stderr or "").strip(),
        "reason": "codex_cli_available" if process.returncode == 0 else "codex_cli_not_callable",
    }


def execute_via_atlas_codex(
    *,
    project_path: Path,
    task: str,
    mode: str,
    dry_run: bool,
    workflow: str,
    agent: str,
    skill: Optional[str],
    plan: List[str],
) -> Dict[str, Any]:
    readiness = codex_executor_readiness()
    if not readiness.get("codex_executor_ready"):
        return readiness

    prompt = _build_codex_prompt(
        project_path=project_path,
        task=task,
        plan=plan,
        workflow=workflow,
        agent=agent,
        skill=skill,
    )

    if dry_run or mode != "execute":
        return {
            "status": "ready",
            "codex_executor_ready": True,
            "invoked": False,
            "mode": mode,
            "dry_run": dry_run,
            "command_preview": [
                "codex",
                "exec",
                "--cd",
                str(project_path),
                "--sandbox",
                "workspace-write",
                "--ask-for-approval",
                "on-request",
                prompt,
            ],
            "reason": "executor_ready_but_not_invoked",
        }

    with tempfile.NamedTemporaryFile(prefix="atlas-codex-last-message-", suffix=".txt", delete=False) as handle:
        output_file = Path(handle.name)

    command = [
        "codex",
        "exec",
        "--cd",
        str(project_path),
        "--sandbox",
        "workspace-write",
        "--ask-for-approval",
        "on-request",
        "--output-last-message",
        str(output_file),
        prompt,
    ]
    process = subprocess.run(
        command,
        check=False,
        capture_output=True,
        text=True,
        timeout=1800,
    )
    last_message = output_file.read_text(encoding="utf-8") if output_file.exists() else ""
    return {
        "status": "ok" if process.returncode == 0 else "failed",
        "codex_executor_ready": True,
        "invoked": True,
        "mode": mode,
        "dry_run": dry_run,
        "return_code": process.returncode,
        "stdout": (process.stdout or "").strip(),
        "stderr": (process.stderr or "").strip(),
        "last_message": last_message.strip(),
        "command_preview": command,
    }


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Invoke Codex from Atlas as a controlled executor.")
    parser.add_argument("--project-path", required=True)
    parser.add_argument("--task", required=True)
    parser.add_argument("--mode", choices=["plan", "execute", "audit"], required=True)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--workflow", required=True)
    parser.add_argument("--agent", required=True)
    parser.add_argument("--skill", default=None)
    parser.add_argument("--plan-step", action="append", default=[])
    args = parser.parse_args(argv)

    result = execute_via_atlas_codex(
        project_path=Path(args.project_path).resolve(),
        task=args.task,
        mode=args.mode,
        dry_run=args.dry_run,
        workflow=args.workflow,
        agent=args.agent,
        skill=args.skill,
        plan=list(args.plan_step),
    )
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0 if result.get("status") in {"ready", "ok"} else 1


if __name__ == "__main__":
    raise SystemExit(main())
