from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

try:
    from tools.project_intent_analyzer import analyze_project_intent
    from tools.project_phase_resolver import resolve_project_phase
except ModuleNotFoundError:
    from project_intent_analyzer import analyze_project_intent
    from project_phase_resolver import resolve_project_phase


DEFAULT_ROOT = Path(__file__).resolve().parents[1]


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _recommended_command_for_phase(phase_report: Dict[str, Any]) -> Optional[str]:
    allowed = list(phase_report.get("allowed_commands", []))
    return allowed[0] if allowed else None


def _phase_prompt_kind(current_phase: str) -> str:
    mapping = {
        "idea": "bootstrap_brief",
        "planning": "bootstrap_brief",
        "bootstrap": "post_bootstrap_review",
        "build": "build_iteration",
        "audit": "certification_ready",
        "certified": "next_iteration",
    }
    return mapping.get(current_phase, "generic_guidance")


def _prompt_lines(
    *,
    project: Optional[Path],
    current_phase: str,
    project_type: str,
    objective: Optional[str],
    recommended_command: Optional[str],
    phase_report: Dict[str, Any],
    intent: Dict[str, Any],
) -> List[str]:
    lines: List[str] = []
    if project is not None:
        lines.append(f"Quiero trabajar sobre `{project}` usando Codex-Atlas de forma controlada.")
    else:
        lines.append("Quiero usar Codex-Atlas para avanzar con un proyecto nuevo de forma controlada.")
    lines.append(f"Fase actual: `{current_phase}`.")
    if project_type and project_type != "unknown":
        lines.append(f"Tipo de proyecto: `{project_type}`.")
    if objective:
        lines.append(f"Objetivo: {objective}")
    lines.append("Restricciones:")
    lines.append("- no tocar REYESOFT")
    lines.append("- no hooks")
    lines.append("- no MCP real")
    lines.append("- cambios mínimos, trazables y reversibles")

    if current_phase in {"idea", "planning"}:
        lines.append("Proceso pedido:")
        lines.append("- inspeccionar el brief")
        lines.append("- confirmar alcance y restricciones")
        lines.append("- ejecutar `project-bootstrap` solo si el output_dir es seguro")
    elif current_phase == "bootstrap":
        lines.append("Proceso pedido:")
        lines.append("- revisar estructura generada")
        lines.append("- validar README y AGENTS")
        lines.append("- ejecutar `audit-repo` antes de editar")
    elif current_phase == "build":
        lines.append("Proceso pedido:")
        lines.append("- mantener la estructura Atlas-derived")
        lines.append("- enfocar el cambio en el núcleo funcional")
        lines.append("- ejecutar `audit-repo` al cerrar")
    elif current_phase == "audit":
        lines.append("Proceso pedido:")
        lines.append("- resolver warnings reales")
        lines.append("- revisar design intelligence y documentación")
        lines.append("- ejecutar `certify-project` cuando el proyecto esté listo")
    elif current_phase == "certified":
        lines.append("Proceso pedido:")
        lines.append("- proponer una iteración nueva y acotada")
        lines.append("- explicar impacto antes de editar")
        lines.append("- re-auditar y re-certificar si hay cambios materiales")

    recommended_next_steps = list(phase_report.get("recommended_next_steps", []))
    if recommended_next_steps:
        lines.append("Siguientes pasos sugeridos por Atlas:")
        for item in recommended_next_steps[:3]:
            lines.append(f"- {item}")

    missing_definition = list(intent.get("missing_definition", []))
    if missing_definition:
        lines.append("Definición faltante detectada:")
        for item in missing_definition[:3]:
            lines.append(f"- {item}")

    if recommended_command:
        lines.append(f"Comando Atlas más alineado ahora: `{recommended_command}`.")
    lines.append("Quiero un informe final breve con lo hecho, lo validado y los riesgos residuales.")
    return lines


def build_prompt(
    *,
    root: Path,
    project: Optional[Path] = None,
    brief: Optional[str] = None,
) -> Dict[str, Any]:
    root = root.resolve()
    if project is None and not brief:
        return {
            "status": "skipped",
            "reason": "missing_project_or_brief",
            "timestamp": _utc_now_iso(),
        }

    if project is not None:
        project = project.resolve()
        phase_report = resolve_project_phase(root, project)
        intent = analyze_project_intent(project=project)
    else:
        phase_report = {
            "current_phase": "planning",
            "confidence": "medium",
            "allowed_commands": ["project-bootstrap"],
            "recommended_next_steps": [
                "finalize project brief",
                "choose project type",
                "prepare output_dir",
            ],
            "common_mistakes": [
                "starting implementation too early",
                "not defining clear scope",
            ],
        }
        intent = analyze_project_intent(brief=brief)

    current_phase = str(phase_report.get("current_phase", "planning")).strip() or "planning"
    recommended_command = _recommended_command_for_phase(phase_report)
    prompt = "\n".join(
        _prompt_lines(
            project=project,
            current_phase=current_phase,
            project_type=str(intent.get("project_type", "unknown")).strip(),
            objective=str(intent.get("objective", "")).strip() or None,
            recommended_command=recommended_command,
            phase_report=phase_report,
            intent=intent,
        )
    )
    return {
        "status": "ok",
        "project_path": str(project) if project is not None else None,
        "current_phase": current_phase,
        "prompt_kind": _phase_prompt_kind(current_phase),
        "recommended_command": recommended_command,
        "project_type": intent.get("project_type"),
        "objective": intent.get("objective"),
        "risk_level": intent.get("risk_level"),
        "complexity": intent.get("complexity"),
        "missing_definition": intent.get("missing_definition", []),
        "prompt": prompt,
        "phase_evidence": phase_report.get("evidence", []),
        "intent_evidence": intent.get("evidence", []),
        "timestamp": _utc_now_iso(),
    }


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(add_help=True)
    parser.add_argument("--root", default=None, help="Atlas root to use. Defaults to this repository root.")
    parser.add_argument("--project", default=None, help="Derived project path to inspect.")
    parser.add_argument("--brief", default=None, help="Brief text to use when there is no project path yet.")
    args = parser.parse_args(argv)

    root = Path(args.root).resolve() if args.root else DEFAULT_ROOT
    project = Path(args.project).resolve() if args.project else None
    result = build_prompt(root=root, project=project, brief=args.brief)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
