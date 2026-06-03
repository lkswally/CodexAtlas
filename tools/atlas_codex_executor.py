from __future__ import annotations

import argparse
import json
import os
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


def _detect_codex_exec_capabilities() -> Dict[str, Any]:
    try:
        process = subprocess.run(
            ["codex", "exec", "--help"],
            check=False,
            capture_output=True,
            text=True,
            timeout=20,
        )
    except Exception as exc:
        return {
            "detected": False,
            "reason": f"codex_exec_help_unavailable:{exc}",
            "supports_cd": False,
            "supports_sandbox": False,
            "supports_output_last_message": False,
            "supports_ask_for_approval": False,
        }

    help_text = "\n".join(part for part in ((process.stdout or ""), (process.stderr or "")) if part)
    return {
        "detected": process.returncode == 0,
        "reason": "codex_exec_help_available" if process.returncode == 0 else "codex_exec_help_not_callable",
        "supports_cd": "--cd" in help_text or "-C, --cd" in help_text,
        "supports_sandbox": "--sandbox" in help_text,
        "supports_output_last_message": "--output-last-message" in help_text,
        "supports_ask_for_approval": "--ask-for-approval" in help_text,
    }


def _build_codex_exec_command(
    *,
    project_path: Path,
    prompt: str,
    output_file: Optional[Path],
    capabilities: Dict[str, Any],
) -> tuple[List[str], List[str]]:
    command = ["codex", "exec"]
    warnings: List[str] = []

    if capabilities.get("supports_cd"):
        command.extend(["--cd", str(project_path)])
    else:
        warnings.append("missing_exec_flag:cd")

    if capabilities.get("supports_sandbox"):
        command.extend(["--sandbox", "workspace-write"])
    else:
        warnings.append("missing_exec_flag:sandbox")

    if capabilities.get("supports_ask_for_approval"):
        command.extend(["--ask-for-approval", "on-request"])
    else:
        warnings.append("missing_exec_flag:ask_for_approval")

    if output_file is not None:
        if capabilities.get("supports_output_last_message"):
            command.extend(["--output-last-message", str(output_file)])
        else:
            warnings.append("missing_exec_flag:output_last_message")

    command.append(prompt)
    return command, warnings


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
    capabilities = _detect_codex_exec_capabilities()
    return {
        "status": "ready" if process.returncode == 0 else "blocked",
        "codex_executor_ready": process.returncode == 0,
        "stdout": (process.stdout or "").strip(),
        "stderr": (process.stderr or "").strip(),
        "reason": "codex_cli_available" if process.returncode == 0 else "codex_cli_not_callable",
        "capabilities": capabilities,
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
    capabilities = readiness.get("capabilities", {})

    prompt = _build_codex_prompt(
        project_path=project_path,
        task=task,
        plan=plan,
        workflow=workflow,
        agent=agent,
        skill=skill,
    )

    preview_command, compatibility_warnings = _build_codex_exec_command(
        project_path=project_path,
        prompt=prompt,
        output_file=None,
        capabilities=capabilities,
    )

    if dry_run or mode != "execute":
        return {
            "status": "ready",
            "codex_executor_ready": True,
            "invoked": False,
            "mode": mode,
            "dry_run": dry_run,
            "capabilities": capabilities,
            "compatibility_warnings": compatibility_warnings,
            "command_preview": preview_command,
            "reason": "executor_ready_but_not_invoked",
        }

    with tempfile.NamedTemporaryFile(prefix="atlas-codex-last-message-", suffix=".txt", delete=False) as handle:
        output_file = Path(handle.name)

    command, compatibility_warnings = _build_codex_exec_command(
        project_path=project_path,
        prompt=prompt,
        output_file=output_file,
        capabilities=capabilities,
    )
    try:
        process = subprocess.run(
            command,
            check=False,
            capture_output=True,
            text=True,
            timeout=1800,
        )
        last_message = output_file.read_text(encoding="utf-8") if output_file.exists() else ""
    finally:
        try:
            if output_file.exists():
                os.unlink(output_file)
        except OSError:
            # Best effort cleanup only; executor output should still be returned.
            pass
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
        "capabilities": capabilities,
        "compatibility_warnings": compatibility_warnings,
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
