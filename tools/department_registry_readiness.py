from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Dict, List, Optional

try:
    from tools.project_intent_analyzer import analyze_project_intent
except ModuleNotFoundError:
    from project_intent_analyzer import analyze_project_intent


DEFAULT_ROOT = Path(__file__).resolve().parents[1]
REGISTRY_PATH = Path("config/department_registry_rules.json")


def load_department_registry(root: Path = DEFAULT_ROOT) -> Dict[str, Any]:
    return json.loads((root / REGISTRY_PATH).read_text(encoding="utf-8-sig"))


def _normalize(value: Any) -> str:
    return " ".join(str(value or "").strip().lower().split())


def _stringify(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, str):
        return value.strip()
    if isinstance(value, (list, tuple, set)):
        return ", ".join(str(item).strip() for item in value if str(item).strip())
    if isinstance(value, dict):
        return ", ".join(f"{key}: {value[key]}" for key in value if str(value[key]).strip())
    return str(value).strip()


def _has_value(value: Any) -> bool:
    if value is None:
        return False
    if isinstance(value, str):
        return bool(value.strip())
    if isinstance(value, (list, tuple, set, dict)):
        return bool(value)
    return True


def _listify(value: Any) -> List[str]:
    if isinstance(value, list):
        return [str(item).strip() for item in value if str(item).strip()]
    if isinstance(value, tuple):
        return [str(item).strip() for item in value if str(item).strip()]
    text = _stringify(value)
    if not text:
        return []
    return [part.strip() for part in text.replace("|", ",").split(",") if part.strip()]


def _contains_any(surface: str, terms: List[str]) -> List[str]:
    normalized_surface = _normalize(surface)
    matches: List[str] = []
    for term in terms:
        cleaned = str(term).strip()
        if cleaned and _normalize(cleaned) in normalized_surface:
            matches.append(cleaned)
    return matches


def _infer_context(payload: Dict[str, Any], project: Path) -> Dict[str, Any]:
    context = {
        "project_type": _stringify(payload.get("project_type")) or "unknown",
        "objective": _stringify(payload.get("objective")),
        "domain_context": _stringify(payload.get("domain_context")),
        "target_audience": _stringify(payload.get("target_audience")),
        "problem_statement": _stringify(payload.get("problem_statement") or payload.get("problem")),
        "project_name": _stringify(payload.get("project_name")) or project.name,
    }

    if context["project_type"] != "unknown" and context["objective"]:
        return context

    try:
        intent = analyze_project_intent(project=project)
    except Exception:
        intent = {}

    if context["project_type"] == "unknown":
        context["project_type"] = _stringify(intent.get("project_type")) or "unknown"
    if not context["objective"]:
        context["objective"] = _stringify(intent.get("objective"))
    if not context["domain_context"]:
        context["domain_context"] = _stringify(intent.get("domain_context"))
    if not context["problem_statement"]:
        context["problem_statement"] = _stringify(intent.get("problem_statement"))
    return context


def _payload_surface(payload: Dict[str, Any], context: Dict[str, Any]) -> str:
    parts = [
        context.get("project_type", ""),
        context.get("objective", ""),
        context.get("domain_context", ""),
        context.get("target_audience", ""),
        context.get("problem_statement", ""),
        _stringify((payload.get("visual_fidelity_posture") or {}).get("fidelity_state")),
        " ".join(_listify((payload.get("visual_fidelity_posture") or {}).get("drift_signals"))),
        _stringify((payload.get("copywriting_conversion_posture") or {}).get("copy_readiness_state")),
        " ".join(_listify((payload.get("copywriting_conversion_posture") or {}).get("warnings"))),
        _stringify((payload.get("brand_strategy_posture") or {}).get("brand_readiness_state")),
        " ".join(_listify((payload.get("brand_strategy_posture") or {}).get("warnings"))),
        _stringify((payload.get("n8n_automation_posture") or {}).get("risk_level")),
        " ".join(_listify((payload.get("n8n_automation_posture") or {}).get("side_effects"))),
        " ".join(_listify((payload.get("n8n_automation_posture") or {}).get("source_files"))),
        " ".join(_listify((payload.get("repo_graph_posture") or {}).get("watchlist"))),
        _stringify((payload.get("model_cost_control_posture") or {}).get("recommended_model_tier")),
        _stringify(((payload.get("model_cost_control_posture") or {}).get("fallback_posture") or {}).get("fallback_mode")),
        _stringify((payload.get("skill_improvement_posture") or {}).get("status")),
    ]
    return " ".join(part for part in parts if part)


def _is_frontend_project(project_type: str, payload: Dict[str, Any], registry: Dict[str, Any]) -> bool:
    normalized_type = _normalize(project_type)
    if normalized_type in {_normalize(item) for item in registry.get("frontend_project_types", [])}:
        return True
    visual = payload.get("visual_fidelity_posture") or {}
    copy = payload.get("copywriting_conversion_posture") or {}
    brand = payload.get("brand_strategy_posture") or {}
    return any(
        _stringify(source.get(key))
        for source, key in (
            (visual, "fidelity_state"),
            (copy, "copy_readiness_state"),
            (brand, "brand_readiness_state"),
        )
    )


def _missing_inputs(
    department_id: str,
    definition: Dict[str, Any],
    context: Dict[str, Any],
    payload: Dict[str, Any],
) -> List[str]:
    missing: List[str] = []
    required_inputs = _listify(definition.get("required_inputs"))
    n8n_posture = payload.get("n8n_automation_posture") or {}

    for field_name in required_inputs:
        normalized = _normalize(field_name)
        if normalized == "project_type" and context.get("project_type", "unknown") == "unknown":
            missing.append(field_name)
        elif normalized == "objective" and not context.get("objective"):
            missing.append(field_name)
        elif normalized == "target_audience" and not (
            context.get("target_audience")
            or _stringify(((payload.get("brand_strategy_posture") or {}).get("audience_fit_score")))
            or _stringify(((payload.get("copywriting_conversion_posture") or {}).get("hero_message")))
        ):
            missing.append(field_name)
        elif normalized == "problem_statement" and not context.get("problem_statement"):
            missing.append(field_name)
        elif normalized == "workflow_blueprint" and not (
            _listify(n8n_posture.get("source_files")) or _listify(n8n_posture.get("side_effects"))
        ):
            missing.append(field_name)
        elif normalized == "test_payload" and bool(n8n_posture) and bool(n8n_posture.get("test_payload_required", False)):
            missing.append(field_name)
        elif normalized == "side_effect_boundaries" and bool(n8n_posture) and not _listify(n8n_posture.get("side_effects")):
            missing.append(field_name)
        elif normalized == "project_path" and not _has_value(payload.get("project_path")):
            missing.append(field_name)
        elif normalized == "scope_declaration" and not context.get("objective"):
            missing.append(field_name)
        elif normalized == "research_goal" and not (
            context.get("objective") or context.get("domain_context")
        ):
            missing.append(field_name)
        elif normalized == "comparison_scope" and department_id == "research" and not context.get("objective"):
            missing.append(field_name)
        elif normalized == "cost_or_provider_context" and not _stringify(payload.get("model_cost_control_posture")):
            missing.append(field_name)
    return missing


def assess_department_registry_readiness(
    payload: Dict[str, Any],
    *,
    root: Path = DEFAULT_ROOT,
    project: Optional[Path] = None,
) -> Dict[str, Any]:
    root = root.resolve()
    project = (project or root).resolve()
    registry = load_department_registry(root)
    context = _infer_context(payload, project)
    project_type = context.get("project_type", "unknown")
    surface = _payload_surface(payload, context)

    frontend_signal = _is_frontend_project(project_type, payload, registry)
    product_signal = bool(_contains_any(surface, list(registry.get("product_signal_terms", []))))
    growth_signal = bool(_contains_any(surface, list(registry.get("growth_signal_terms", []))))
    research_signal = bool(_contains_any(surface, list(registry.get("research_signal_terms", []))))
    n8n_signal = bool(_contains_any(surface, list(registry.get("n8n_signal_terms", []))))
    engineering_signal = bool(_contains_any(surface, list(registry.get("engineering_signal_terms", []))))
    cost_signal = bool(_contains_any(surface, list(registry.get("cost_signal_terms", []))))

    visual_fidelity = payload.get("visual_fidelity_posture") or {}
    copywriting = payload.get("copywriting_conversion_posture") or {}
    brand_strategy = payload.get("brand_strategy_posture") or {}
    n8n_posture = payload.get("n8n_automation_posture") or {}
    repo_graph = payload.get("repo_graph_posture") or {}
    business_idea = payload.get("business_idea_simulation_posture") or {}
    skill_improvement = payload.get("skill_improvement_posture") or {}

    recommended_departments: List[str] = []
    available_departments: List[str] = []
    watchlist_departments: List[str] = []
    department_reports: List[Dict[str, Any]] = []

    for department_id in registry.get("department_activation_order", []):
        definition = (registry.get("departments") or {}).get(department_id, {})
        status = _stringify(definition.get("status")) or "active"
        why = "Atlas keeps this department available but not strongly triggered for the current surface."
        recommended = False

        if department_id == "qa_governance":
            recommended = True
            why = "Atlas-governed work always benefits from explicit QA and governance posture before stronger ready claims."
        elif department_id == "web_ux":
            recommended = frontend_signal or bool(
                _stringify(visual_fidelity.get("fidelity_state"))
                or _stringify(copywriting.get("copy_readiness_state"))
                or _stringify(brand_strategy.get("brand_readiness_state"))
            )
            if recommended:
                why = "The project shows frontend, visual, copy or brand signals that benefit from explicit Web/UX governance."
        elif department_id == "growth_marketing":
            recommended = frontend_signal and (
                growth_signal
                or _stringify(copywriting.get("copy_readiness_state")) not in {"", "not_applicable"}
                or _stringify(brand_strategy.get("brand_readiness_state")) not in {"", "not_applicable"}
            )
            if recommended:
                why = "The surface is public-facing enough that positioning, CTA and trust posture need a growth/marketing pass."
        elif department_id == "automation_n8n":
            recommended = bool(n8n_signal or _stringify(n8n_posture.get("risk_level")) or _listify(n8n_posture.get("source_files")))
            if recommended:
                why = "Workflow and automation signals are present, so n8n design and safety boundaries should stay explicit."
        elif department_id == "engineering":
            normalized_type = _normalize(project_type)
            recommended = normalized_type in {
                "backend_service",
                "internal_tool",
                "ai_agent_system",
                "atlas-factory-core",
            } or bool(engineering_signal or repo_graph.get("repo_graph_recommended"))
            if recommended:
                why = "Implementation, runtime or repository-shape signals make an engineering handoff appropriate."
        elif department_id == "product":
            recommended = bool(
                product_signal
                or _stringify(business_idea.get("readiness_state") or business_idea.get("status")) not in {"", "not_applicable"}
                or _stringify(payload.get("change_proposal_posture")) not in {"", "{}"}
            )
            if recommended:
                why = "The current scope still has product-definition or decision-framing signals that deserve a product pass."
        elif department_id == "research":
            recommended = bool(
                research_signal
                or _stringify(skill_improvement.get("status"))
                or _stringify(payload.get("market_research_posture"))
            )
            if recommended:
                why = "The request includes reference, benchmark or radar signals that fit Atlas research posture."
        elif department_id == "operations_finance":
            recommended = False
            if cost_signal or _stringify(payload.get("model_cost_control_posture")):
                why = "Operations/Finance remains watchlist-only; Atlas can surface cost and provider posture without activating runtime ops."

        report = {
            "id": department_id,
            "status": status,
            "recommended": recommended if status == "active" else False,
            "purpose": _stringify(definition.get("purpose")),
            "activate_when": _listify(definition.get("activate_when")),
            "required_inputs": _listify(definition.get("required_inputs")),
            "missing_inputs": _missing_inputs(department_id, definition, context, payload),
            "expected_outputs": _listify(definition.get("expected_outputs")),
            "capabilities": _listify(definition.get("capabilities")),
            "must_not_do": _listify(definition.get("must_not_do")),
            "required_checks": _listify(definition.get("required_checks")),
            "handoff_to": _listify(definition.get("handoff_to")),
            "project_type_fit": _listify(definition.get("project_type_fit")),
            "signal_triggers": _listify(definition.get("signal_triggers")),
            "why": why,
        }
        department_reports.append(report)

        if status == "watchlist":
            watchlist_departments.append(department_id)
        elif report["recommended"]:
            recommended_departments.append(department_id)
        else:
            available_departments.append(department_id)

    registry_state = "ready" if department_reports else "missing"
    why_summary = (
        "Atlas now has an explicit department registry that maps existing governed capabilities into operational areas without creating autonomous agents."
        if department_reports
        else "Atlas is missing a usable department registry."
    )

    return {
        "status": "ok",
        "department_registry_posture": {
            "registry_state": registry_state,
            "activation_mode": _stringify(registry.get("activation_mode")) or "manual_governed",
            "auto_activate": False,
            "project_type": project_type,
            "project_name": context.get("project_name") or project.name,
            "recommended_departments": recommended_departments,
            "available_departments": available_departments,
            "watchlist_departments": watchlist_departments,
            "department_count": len(department_reports),
            "departments": department_reports,
            "why": why_summary,
            "advisory_only": bool(registry.get("advisory_only", True)),
        },
    }


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(add_help=True)
    parser.add_argument("--project", default=None)
    parser.add_argument("--payload-json", default="{}")
    args = parser.parse_args(argv)

    project = Path(args.project).resolve() if args.project else DEFAULT_ROOT
    payload = json.loads(args.payload_json)
    result = assess_department_registry_readiness(payload, root=DEFAULT_ROOT, project=project)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
