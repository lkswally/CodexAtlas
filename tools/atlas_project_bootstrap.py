from __future__ import annotations

import argparse
import json
import os
import re
import tempfile
from pathlib import Path
from typing import Any, Dict, List


ATLAS_ROOT = Path(__file__).resolve().parent.parent
TEMPLATE_ROOT = ATLAS_ROOT / "templates" / "project"
DEFAULT_OPERATING_MODE = "ATLAS gobernanza ligera"
DERIVED_PROJECTS_REGISTRY = ATLAS_ROOT / "memory" / "derived_projects.json"
TEST_TEMP_ROOT = Path(
    os.environ.get("ATLAS_TEST_TEMP_ROOT", Path(tempfile.gettempdir()) / "codex-atlas-tests")
).resolve()
ALLOWED_TEMPLATE_PLACEHOLDERS = {
    "project_name",
    "project_type",
    "project_goal",
    "scope",
    "atlas_root",
    "generated_from_skill",
}
TEMPLATE_PLACEHOLDER_RE = re.compile(
    r"(?P<double>\{\{(?P<double_name>[a-zA-Z0-9_]+)\}\})|"
    r"(?P<dollar>\$\{(?P<dollar_name>[a-zA-Z0-9_]+)\})|"
    r"(?P<single>\{(?P<single_name>[a-zA-Z0-9_]+)\})"
)


def _read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _write_if_missing(path: Path, content: str) -> bool:
    if path.exists():
        return False
    path.write_text(content, encoding="utf-8")
    return True


def _write_with_overwrite(path: Path, content: str) -> None:
    path.write_text(content, encoding="utf-8")


def _extract_template_placeholders(template_text: str) -> List[tuple[str, str]]:
    placeholders: List[tuple[str, str]] = []
    for match in TEMPLATE_PLACEHOLDER_RE.finditer(template_text):
        raw = match.group(0)
        name = (
            match.group("double_name")
            or match.group("dollar_name")
            or match.group("single_name")
            or ""
        )
        if name:
            placeholders.append((raw, name))
    return placeholders


def _render_template_text(template_text: str, values: Dict[str, str]) -> str:
    rendered = template_text
    for key, value in values.items():
        rendered = rendered.replace(f"{{{{{key}}}}}", value)
        rendered = rendered.replace(f"${{{key}}}", value)
        rendered = rendered.replace(f"{{{key}}}", value)
    return rendered


def _validate_project_templates(templates: Dict[str, Path], values: Dict[str, str]) -> List[str]:
    findings: List[str] = []
    label_by_name = {
        "AGENTS.md": "AGENTS",
        ".atlas-project.json": "PROJECT_METADATA",
        "SPRINT_STATUS.md": "SPRINT_STATUS",
    }
    for target_name, template_path in templates.items():
        template_label = label_by_name.get(target_name, target_name)
        relative_path = template_path.relative_to(ATLAS_ROOT)
        template_text = _read_text(template_path)
        placeholders = _extract_template_placeholders(template_text)
        for raw_placeholder, placeholder_name in placeholders:
            if placeholder_name not in ALLOWED_TEMPLATE_PLACEHOLDERS:
                findings.append(
                    "atlas_project_bootstrap:"
                    "invalid_template_placeholder:"
                    "profile=global_project_governance:"
                    f"template={template_label}:file={relative_path}:"
                    f"placeholder={raw_placeholder}:"
                    "recommendation=replace_with_whitelisted_placeholder_or_static_text"
                )
        render_values = values
        if target_name == ".atlas-project.json":
            render_values = {key: json.dumps(value, ensure_ascii=False)[1:-1] for key, value in values.items()}
        rendered = _render_template_text(template_text, render_values)
        unresolved = _extract_template_placeholders(rendered)
        for raw_placeholder, _placeholder_name in unresolved:
            findings.append(
                "atlas_project_bootstrap:"
                "unresolved_template_placeholder:"
                "profile=global_project_governance:"
                f"template={template_label}:file={relative_path}:"
                f"placeholder={raw_placeholder}:"
                "recommendation=ensure_the_placeholder_is_whitelisted_and_rendered_or_convert_it_to_static_text"
            )
    return findings


def _load_registry(path: Path) -> Dict[str, Any]:
    if not path.exists():
        return {"schema_version": "1.0", "projects": []}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {"schema_version": "1.0", "projects": []}
    if not isinstance(data, dict):
        return {"schema_version": "1.0", "projects": []}
    projects = data.get("projects")
    if not isinstance(projects, list):
        data["projects"] = []
    else:
        data["projects"] = [
            item
            for item in projects
            if isinstance(item, dict) and not _is_ephemeral_test_project_root(item.get("project_root"))
        ]
    return data


def _is_ephemeral_test_project_root(project_root: Any) -> bool:
    if not project_root:
        return False
    try:
        resolved = Path(str(project_root)).resolve()
    except (OSError, RuntimeError, ValueError):
        return False
    return resolved == TEST_TEMP_ROOT or TEST_TEMP_ROOT in resolved.parents


def register_project_in_registry(project_root: Path, project_profile: str, governance_mode: str) -> None:
    if _is_ephemeral_test_project_root(project_root):
        return
    registry = _load_registry(DERIVED_PROJECTS_REGISTRY)
    project_root_s = str(project_root.resolve())
    projects = list(registry.get("projects", []))
    updated = False
    for item in projects:
        if not isinstance(item, dict):
            continue
        if str(item.get("project_root", "")).strip() == project_root_s:
            item["project_profile"] = project_profile
            item["atlas_root"] = str(ATLAS_ROOT)
            item["derived_from"] = "Codex-Atlas"
            item["governance_mode"] = governance_mode
            item["status"] = "registered"
            updated = True
            break
    if not updated:
        projects.append(
            {
                "project_name": project_root.name,
                "project_root": project_root_s,
                "project_profile": project_profile,
                "atlas_root": str(ATLAS_ROOT),
                "derived_from": "Codex-Atlas",
                "governance_mode": governance_mode,
                "status": "registered",
            }
        )
    registry["projects"] = projects
    DERIVED_PROJECTS_REGISTRY.write_text(json.dumps(registry, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def _load_package_json(project_root: Path) -> Dict[str, Any]:
    package_json = project_root / "package.json"
    if not package_json.exists():
        return {}
    try:
        return json.loads(package_json.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {}


def detect_runtime_markers(project_root: Path) -> List[str]:
    markers: List[str] = []
    for name in ("package.json", "pyproject.toml", "next.config.js", "prisma", "src", "README.md"):
        if (project_root / name).exists():
            markers.append(name)
    return markers


def infer_project_profile(project_root: Path) -> str:
    package_data = _load_package_json(project_root)
    dependencies = {
        **package_data.get("dependencies", {}),
        **package_data.get("devDependencies", {}),
    }
    if "next" in dependencies or "react" in dependencies or "vite" in dependencies:
        return "frontend_app"
    if "fastapi" in dependencies or "flask" in dependencies or (project_root / "pyproject.toml").exists():
        return "backend_service"
    return "internal_tool"


def infer_project_goal(project_root: Path) -> str:
    readme = project_root / "README.md"
    if not readme.exists():
        return "Project goal not documented yet."
    lines = [line.strip() for line in readme.read_text(encoding="utf-8").splitlines()]
    for line in lines:
        if line and not line.startswith("#"):
            return line
    return f"Governed Atlas-derived project for {project_root.name}."


def _template_variables(project_root: Path, project_name: str | None = None, project_profile: str | None = None) -> Dict[str, str]:
    resolved_profile = project_profile or infer_project_profile(project_root)
    goal = infer_project_goal(project_root)
    return {
        "project_name": project_name or project_root.name,
        "project_type": resolved_profile,
        "generated_from_skill": "atlas_project_bootstrap",
        "atlas_root": str(ATLAS_ROOT),
        "project_goal": goal,
        "scope": "Bootstrap Atlas governance before functional implementation.",
    }


def bootstrap_project(
    project_root: Path,
    project_name: str | None = None,
    project_profile: str | None = None,
    overwrite: bool = False,
) -> Dict[str, Any]:
    project_root = project_root.resolve()
    variables = _template_variables(project_root, project_name=project_name, project_profile=project_profile)

    templates = {
        "AGENTS.md": TEMPLATE_ROOT / "AGENTS.md.template",
        ".atlas-project.json": TEMPLATE_ROOT / ".atlas-project.json.template",
        "SPRINT_STATUS.md": TEMPLATE_ROOT / "SPRINT_STATUS.md.template",
    }
    governance_dirs = ["docs", "memory", "workflows", "policies", "tools"]

    for rel in governance_dirs:
        (project_root / rel).mkdir(parents=True, exist_ok=True)

    template_findings = _validate_project_templates(templates, variables)
    if template_findings:
        raise ValueError("Invalid Atlas project template set: " + " | ".join(template_findings))

    created_files: List[str] = []
    skipped_files: List[str] = []
    for target_name, template_path in templates.items():
        render_values = variables
        if target_name == ".atlas-project.json":
            render_values = {key: json.dumps(value, ensure_ascii=False)[1:-1] for key, value in variables.items()}
        content = _render_template_text(_read_text(template_path), render_values)
        if target_name == ".atlas-project.json":
            payload = json.loads(content)
            payload["governance_mode"] = "atlas_completo" if (project_root / ".git").exists() else "atlas_governanza_ligera"
            payload["runtime_markers"] = detect_runtime_markers(project_root)
            content = json.dumps(payload, indent=2, ensure_ascii=False)
        final_content = content + ("" if content.endswith("\n") else "\n")
        if overwrite:
            _write_with_overwrite(project_root / target_name, final_content)
            created_files.append(target_name)
        else:
            wrote = _write_if_missing(project_root / target_name, final_content)
            if wrote:
                created_files.append(target_name)
            else:
                skipped_files.append(target_name)

    register_project_in_registry(
        project_root=project_root,
        project_profile=variables["project_type"],
        governance_mode="atlas_completo" if (project_root / ".git").exists() else "atlas_governanza_ligera",
    )

    return {
        "status": "ok",
        "project_root": str(project_root),
        "project_profile": variables["project_type"],
        "operating_mode": "ATLAS completo" if (project_root / ".git").exists() else DEFAULT_OPERATING_MODE,
        "created_files": created_files,
        "skipped_files": skipped_files,
        "git_present": (project_root / ".git").exists(),
        "suggested_git_init_command": None
        if (project_root / ".git").exists()
        else f'git init "{project_root}"',
        "functional_work_blocked": True,
        "why": "Atlas governance files are now present, but functional implementation stays blocked until Git and local scope discipline are confirmed.",
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Create minimal Atlas governance files in an existing project.")
    parser.add_argument("--project", required=True, help="Project root to bootstrap under Atlas governance.")
    parser.add_argument("--project-name", help="Optional explicit project name.")
    parser.add_argument(
        "--project-profile",
        choices=["frontend_app", "backend_service", "fullstack", "internal_tool", "ai_agent_system"],
        help="Optional explicit Atlas project profile.",
    )
    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="Overwrite only the governance files managed by this bootstrap tool.",
    )
    args = parser.parse_args()

    result = bootstrap_project(
        Path(args.project),
        project_name=args.project_name,
        project_profile=args.project_profile,
        overwrite=args.overwrite,
    )
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
