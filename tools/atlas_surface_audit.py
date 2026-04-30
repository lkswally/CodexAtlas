from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any, Dict, List


README_LINK_RE = re.compile(r"\[[^\]]+\]\((/[^)]+)\)")


def _read_json(path: Path) -> Dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def _read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8-sig")


def _canonical_skill_ids(root: Path) -> List[str]:
    skills_dir = root / "skills"
    ids: List[str] = []
    for path in sorted(skills_dir.iterdir(), key=lambda item: item.name):
        if not path.is_dir() or path.name.startswith("_"):
            continue
        if (path / "skill.json").exists():
            ids.append(path.name)
    return ids


def _workflow_ids(root: Path) -> List[str]:
    workflows_dir = root / "workflows"
    ids: List[str] = []
    for path in sorted(workflows_dir.glob("*.md"), key=lambda item: item.name):
        ids.append(path.stem)
    return ids


def _command_ids(root: Path) -> List[str]:
    registry = _read_json(root / "commands" / "atomic_command_registry.json")
    commands = registry.get("commands", [])
    ids: List[str] = []
    if isinstance(commands, list):
        for item in commands:
            if isinstance(item, dict):
                command_id = str(item.get("id", "")).strip()
                if command_id:
                    ids.append(command_id)
    return ids


def _existing_readme_links(readme_text: str) -> List[str]:
    return [match.group(1) for match in README_LINK_RE.finditer(readme_text)]


def _resolve_local_link(target: str) -> Path:
    if re.match(r"^/[A-Za-z]:/", target):
        return Path(target[1:])
    return Path(target)


def run_surface_audit(root: Path) -> Dict[str, Any]:
    root = root.resolve()
    readme_path = root / "README.md"
    readme_text = _read_text(readme_path)

    skill_ids = _canonical_skill_ids(root)
    workflow_ids = _workflow_ids(root)
    command_ids = _command_ids(root)

    missing_skill_mentions = [skill_id for skill_id in skill_ids if skill_id not in readme_text]
    missing_workflow_mentions = [workflow_id for workflow_id in workflow_ids if workflow_id not in readme_text]
    missing_command_mentions = [
        command_id for command_id in ("audit-repo", "certify-project", "surface-audit")
        if command_id in command_ids and command_id not in readme_text
    ]

    broken_links: List[str] = []
    for link_target in _existing_readme_links(readme_text):
        candidate = _resolve_local_link(link_target)
        if not candidate.exists():
            broken_links.append(link_target)

    warnings: List[Dict[str, Any]] = []
    findings: List[Dict[str, Any]] = []
    recommendations: List[str] = []
    evidence: List[str] = [
        f"skills_count={len(skill_ids)}",
        f"workflows_count={len(workflow_ids)}",
        f"commands_count={len(command_ids)}",
    ]

    def add_warning(code: str, message: str, details: List[str]) -> None:
        warning = {"severity": "warning", "code": code, "message": message, "details": details}
        warnings.append(warning)
        findings.append(warning)

    if missing_skill_mentions:
        add_warning(
            "readme_missing_skill_mentions",
            "README does not mention all canonical skills.",
            missing_skill_mentions,
        )
        recommendations.append("Update README skill coverage so the public factory surface reflects the real skill catalog.")
        evidence.append(f"missing_skill_mentions={','.join(missing_skill_mentions)}")

    if missing_workflow_mentions:
        add_warning(
            "readme_missing_workflow_mentions",
            "README does not mention all canonical workflows.",
            missing_workflow_mentions,
        )
        recommendations.append("Update README workflow coverage so onboarding and public docs reflect the real workflow surface.")
        evidence.append(f"missing_workflow_mentions={','.join(missing_workflow_mentions)}")

    if missing_command_mentions:
        add_warning(
            "readme_missing_command_mentions",
            "README does not mention all key canonical commands.",
            missing_command_mentions,
        )
        recommendations.append("Document the key read-only factory commands in README so installation and audit paths stay coherent.")
        evidence.append(f"missing_command_mentions={','.join(missing_command_mentions)}")

    if broken_links:
        add_warning(
            "readme_broken_links",
            "README contains local links that do not resolve.",
            broken_links,
        )
        recommendations.append("Fix broken local README links so the published Atlas surface stays navigable.")
        evidence.append(f"broken_links={','.join(broken_links)}")

    status = "ok" if not warnings else "warning"
    next_action = (
        "README surface matches the canonical Atlas structure."
        if not warnings
        else "Update README coverage and rerun the surface audit."
    )

    return {
        "status": status,
        "warnings": warnings,
        "findings": findings,
        "evidence": evidence,
        "next_action": next_action,
        "summary": {
            "root": str(root),
            "skills_count": len(skill_ids),
            "workflows_count": len(workflow_ids),
            "commands_count": len(command_ids),
            "missing_skill_mentions": missing_skill_mentions,
            "missing_workflow_mentions": missing_workflow_mentions,
            "missing_command_mentions": missing_command_mentions,
            "broken_links": broken_links,
        },
        "recommendations": recommendations,
    }
