from __future__ import annotations

import argparse
import json
import re
import subprocess
import tomllib
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple


DEFAULT_ROOT = Path(__file__).resolve().parents[1]
MODEL_PROFILES_PATH = Path("config") / "model_profiles.json"
MODEL_ROUTING_RULES_PATH = Path("config") / "model_routing_rules.json"
TASK_TYPE_BY_INTENT = {
    "planning": "planning",
    "architecture": "architecture",
    "code_execution": "code_execution",
    "code_review": "audit_review",
    "branding_ux": "design_reasoning",
    "documentation": "documentation",
    "security": "security_review",
    "research": "audit_review",
    "project_creation": "project_creation",
    "deployment_or_destructive_action": "security_review",
}
TASK_TYPE_BY_SKILL = {
    "project-bootstrap": "project_creation",
    "repo-audit": "audit_review",
    "product-branding-review": "design_reasoning",
    "visual-direction-checkpoint": "design_reasoning",
    "anti-generic-ui-audit": "design_reasoning",
    "design-system-review": "design_reasoning",
}
TASK_TYPE_KEYWORDS = {
    "planning": ("plan", "planning", "roadmap", "prioritize", "next steps", "brief"),
    "architecture": ("architecture", "boundary", "system design", "contracts", "refactor architecture"),
    "code_execution": ("implement", "fix", "code", "edit", "refactor", "change file", "build feature"),
    "lightweight_editing": ("small", "simple", "minor", "quick", "lightweight", "tiny", "copy edit"),
    "documentation": ("readme", "documentation", "docs", "copy", "status", "content"),
    "audit_review": ("audit", "review", "certify", "quality gate", "validation", "governance"),
    "design_reasoning": ("design", "branding", "ux", "visual", "hero", "landing", "copywriting"),
    "security_review": ("security", "secrets", "credentials", "auth", "permission", "destructive"),
}
LOW_RISK_INFORMATIONAL_PREFIXES = (
    "avoid ",
    "review ",
    "document ",
    "list ",
    "check ",
    "summarize ",
)
PHASE_TO_TASK_TYPE = {
    "idea": "planning",
    "planning": "planning",
    "bootstrap": "code_execution",
    "build": "code_execution",
    "audit": "audit_review",
    "certified": "planning",
}
TASK_TYPE_TO_FALLBACK_PHASE = {
    "planning": "planning",
    "architecture": "planning",
    "project_creation": "planning",
    "code_execution": "build",
    "lightweight_editing": "build",
    "documentation": "certified",
    "audit_review": "audit",
    "security_review": "audit",
    "design_reasoning": "build",
}
COST_HIGH_TERMS = ("save tokens", "cheaper", "budget", "low cost", "cost saver", "mini model", "fast")
COST_LOW_TERMS = ("best quality", "highest quality", "strongest model", "deep reasoning", "careful", "max quality")
QUALITY_TERMS = ("careful", "strategic", "deep", "complex", "delicate", "architecture", "security")
RISK_LEVELS = {"low", "medium", "high"}
COMPLEXITY_LEVELS = {"low", "medium", "high"}


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _read_json(path: Path) -> Dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def _normalize(text: str) -> str:
    return re.sub(r"\s+", " ", str(text).lower()).strip()


def _load_profiles(root: Path) -> Dict[str, Any]:
    return _read_json(root / MODEL_PROFILES_PATH)


def _load_rules(root: Path) -> Dict[str, Any]:
    return _read_json(root / MODEL_ROUTING_RULES_PATH)


def _read_toml_if_exists(path: Path) -> Dict[str, Any]:
    if not path.exists():
        return {}
    try:
        return tomllib.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}


def _probe_codex_cli() -> Tuple[bool, Optional[str]]:
    try:
        result = subprocess.run(
            ["codex", "--version"],
            capture_output=True,
            text=True,
            timeout=8,
            check=False,
        )
    except Exception as exc:
        return False, str(exc)
    if result.returncode == 0:
        return True, None
    error = (result.stderr or result.stdout or "").strip() or f"codex_exit_{result.returncode}"
    return False, error


def inspect_model_switch_support(*, root: Path) -> Dict[str, Any]:
    root = root.resolve()
    global_config_path = Path.home() / ".codex" / "config.toml"
    project_config_path = root / ".codex" / "config.toml"
    global_config = _read_toml_if_exists(global_config_path)
    project_config = _read_toml_if_exists(project_config_path)
    cli_available, cli_error = _probe_codex_cli()

    global_model = str(global_config.get("model", "")).strip() or None
    project_model = str(project_config.get("model", "")).strip() or None
    can_auto_switch = False
    if cli_available and project_model:
        auto_switch_method = "config"
        can_auto_switch = True
    elif cli_available:
        auto_switch_method = "unknown"
    else:
        auto_switch_method = "not_available"

    evidence: List[str] = []
    if global_model:
        evidence.append(f"global_config_model={global_model}")
    if project_model:
        evidence.append(f"project_config_model={project_model}")
    evidence.append("project_scoped_config_exists" if project_config_path.exists() else "project_scoped_config_missing")
    if cli_available:
        evidence.append("codex_cli_invocable")
    elif cli_error:
        evidence.append(f"codex_cli_error={cli_error}")

    return {
        "status": "ok",
        "global_config_path": str(global_config_path),
        "project_config_path": str(project_config_path),
        "current_global_model": global_model,
        "current_project_model": project_model,
        "codex_cli_available": cli_available,
        "codex_cli_error": cli_error,
        "can_auto_switch": can_auto_switch,
        "auto_switch_method": auto_switch_method,
        "evidence": evidence,
        "timestamp": _utc_now_iso(),
    }


def _normalize_level(value: Optional[str], allowed: set[str], default: str) -> str:
    candidate = str(value or "").strip().lower()
    return candidate if candidate in allowed else default


def _derive_cost_sensitivity(task: str) -> Tuple[str, List[str], bool]:
    normalized = _normalize(task)
    evidence: List[str] = []
    if any(term in normalized for term in COST_HIGH_TERMS):
        evidence.append("explicit_cost_priority=high")
        return "high", evidence, True
    if any(term in normalized for term in COST_LOW_TERMS):
        evidence.append("explicit_cost_priority=low")
        return "low", evidence, True
    if any(term in normalized for term in QUALITY_TERMS):
        evidence.append("quality_signal_detected")
        return "low", evidence, True
    evidence.append("cost_priority_not_explicit")
    return "medium", evidence, False


def _derive_task_type(*, task: str, intent: Optional[str], recommended_skill: Optional[str], current_phase: Optional[str]) -> Dict[str, Any]:
    evidence: List[str] = []
    normalized = _normalize(task)
    if any(normalized.startswith(prefix.strip()) for prefix in LOW_RISK_INFORMATIONAL_PREFIXES):
        return {"task_type": "documentation", "confidence": "medium", "ambiguous": False, "candidates": ["documentation"], "evidence": ["low_risk_informational_action"]}

    if recommended_skill and recommended_skill in TASK_TYPE_BY_SKILL:
        task_type = TASK_TYPE_BY_SKILL[recommended_skill]
        return {"task_type": task_type, "confidence": "high", "ambiguous": False, "candidates": [task_type], "evidence": [f"skill={recommended_skill}->{task_type}"]}
    if intent and intent in TASK_TYPE_BY_INTENT:
        task_type = TASK_TYPE_BY_INTENT[intent]
        return {"task_type": task_type, "confidence": "high", "ambiguous": False, "candidates": [task_type], "evidence": [f"intent={intent}->{task_type}"]}

    candidates: List[str] = []
    for task_type, keywords in TASK_TYPE_KEYWORDS.items():
        hits = [keyword for keyword in keywords if keyword in normalized]
        if hits:
            candidates.append(task_type)
            evidence.append(f"{task_type}_hits={hits}")
    deduped = list(dict.fromkeys(candidates))
    if len(deduped) == 1:
        return {"task_type": deduped[0], "confidence": "medium", "ambiguous": False, "candidates": deduped, "evidence": evidence}
    if len(deduped) > 1:
        return {"task_type": None, "confidence": "low", "ambiguous": True, "candidates": deduped, "evidence": evidence or ["multiple_task_type_candidates"]}

    phase_value = str(current_phase or "").strip().lower()
    if phase_value in PHASE_TO_TASK_TYPE:
        task_type = PHASE_TO_TASK_TYPE[phase_value]
        return {"task_type": task_type, "confidence": "medium", "ambiguous": False, "candidates": [task_type], "evidence": [f"phase={phase_value}->{task_type}"]}
    return {"task_type": None, "confidence": "low", "ambiguous": True, "candidates": [], "evidence": ["task_type_unresolved"]}


def _matches_rule(rule: Dict[str, Any], *, task_type: str, phase: str, complexity: str, risk_level: str, cost_sensitivity: str) -> bool:
    checks = {"task_type": task_type, "phase": phase, "complexity": complexity, "risk_level": risk_level, "cost_sensitivity": cost_sensitivity}
    for field, current_value in checks.items():
        allowed_values = [str(item).strip().lower() for item in rule.get(field, []) if str(item).strip()]
        if not allowed_values:
            return False
        if "*" in allowed_values:
            continue
        if current_value not in allowed_values:
            return False
    return True


def _rule_specificity(rule: Dict[str, Any]) -> int:
    score = 0
    for field in ("task_type", "phase", "complexity", "risk_level", "cost_sensitivity"):
        if "*" not in [str(item).strip().lower() for item in rule.get(field, []) if str(item).strip()]:
            score += 1
    return score


def _reasoning_required(task_type: str, complexity: str, risk_level: str, recommended_model: str) -> str:
    if recommended_model in {"GPT-5.4", "GPT-5.1-Codex-Max"} or complexity == "high" or risk_level == "high":
        return "high"
    if task_type in {"planning", "architecture", "audit_review", "security_review", "design_reasoning", "code_execution"}:
        return "medium"
    return "low"


def _profile_from_rule(rule: Dict[str, Any], task_type: str) -> str:
    if task_type == "security_review":
        return "security"
    profile = str(rule.get("recommended_model_profile", "")).strip()
    if profile:
        return profile
    return {
        "planning": "deep_reasoning",
        "architecture": "deep_reasoning",
        "project_creation": "deep_reasoning",
        "code_execution": "code_execution",
        "audit_review": "reviewer",
        "security_review": "security",
        "documentation": "cost_saver",
        "lightweight_editing": "cost_saver",
        "design_reasoning": "creative_product",
    }.get(task_type, "deep_reasoning")


def _default_route(rules: Dict[str, Any]) -> Dict[str, Any]:
    return dict(rules.get("default_rule", {}))


def _build_missing_information(*, task_type_bundle: Dict[str, Any], current_phase: Optional[str]) -> List[str]:
    missing: List[str] = []
    if not task_type_bundle.get("task_type"):
        missing.append("task_type")
    if task_type_bundle.get("ambiguous"):
        missing.append("planning_vs_execution")
    if not current_phase:
        missing.append("phase")
    return missing


def _user_question(*, missing_information: List[str], task_type_bundle: Dict[str, Any], switch_support: Dict[str, Any], recommended_model: str, cost_priority_explicit: bool) -> str:
    if "planning_vs_execution" in missing_information:
        return "Should Atlas treat this task as planning/architecture work or as hands-on code execution?"
    if "task_type" in missing_information:
        return "What kind of task is this: planning, implementation, audit, documentation, or design review?"
    if "phase" in missing_information:
        return "What project phase should Atlas use for this task: idea, planning, bootstrap, build, audit, or certified?"
    if not cost_priority_explicit and task_type_bundle.get("task_type") in {"design_reasoning", "documentation", "code_execution"}:
        return "For this task, should Atlas prioritize maximum quality or lower token cost?"
    if not bool(switch_support.get("can_auto_switch")):
        return f"Atlas recommends `{recommended_model}`, but safe Codex model switching is not verified in this environment. Do you want to keep this as a recommendation only?"
    return "Please confirm the model choice before Atlas changes any model configuration."


def recommend_model_profile(*, root: Path, task: str = "", intent: Optional[str] = None, current_phase: Optional[str] = None, risk_level: str = "low", complexity: str = "low", project_type: Optional[str] = None, recommended_skill: Optional[str] = None, switch_support: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    root = root.resolve()
    profiles = _load_profiles(root).get("profiles", {})
    rules = _load_rules(root)
    normalized_phase = str(current_phase or "").strip().lower()
    normalized_risk = _normalize_level(risk_level, RISK_LEVELS, "medium")
    normalized_complexity = _normalize_level(complexity, COMPLEXITY_LEVELS, "medium")
    cost_sensitivity, cost_evidence, cost_priority_explicit = _derive_cost_sensitivity(task)
    task_type_bundle = _derive_task_type(task=task, intent=intent, recommended_skill=recommended_skill, current_phase=current_phase)
    if "low_risk_informational_action" in task_type_bundle.get("evidence", []):
        normalized_risk = "low"
        normalized_complexity = "low"
        if not cost_priority_explicit:
            cost_sensitivity = "high"
            cost_evidence.append("informational_action_prefers_cost_saver")
    missing_information = _build_missing_information(task_type_bundle=task_type_bundle, current_phase=current_phase)
    effective_phase = normalized_phase
    task_type = str(task_type_bundle.get("task_type") or "").strip().lower()
    if not effective_phase and task_type:
        effective_phase = TASK_TYPE_TO_FALLBACK_PHASE.get(task_type, "")

    matched_rules: List[Dict[str, Any]] = []
    if task_type and effective_phase:
        for candidate in rules.get("routing_rules", []):
            if isinstance(candidate, dict) and _matches_rule(candidate, task_type=task_type, phase=effective_phase, complexity=normalized_complexity, risk_level=normalized_risk, cost_sensitivity=cost_sensitivity):
                matched_rules.append(candidate)

    matched_rules.sort(key=_rule_specificity, reverse=True)
    ambiguous_route = False
    if matched_rules:
        top_specificity = _rule_specificity(matched_rules[0])
        top_rules = [rule for rule in matched_rules if _rule_specificity(rule) == top_specificity]
        ambiguous_route = len({str(rule.get("recommended_model", "")).strip() for rule in top_rules}) > 1
        selected_rule = top_rules[0]
    else:
        selected_rule = _default_route(rules)
        ambiguous_route = True

    switch_support = switch_support or inspect_model_switch_support(root=root)
    recommended_model = str(selected_rule.get("recommended_model", "")).strip() or str(_default_route(rules).get("recommended_model", "")).strip()
    fallback_model = str(selected_rule.get("fallback_model", "")).strip() or str(_default_route(rules).get("fallback_model", "")).strip()
    recommended_profile = _profile_from_rule(selected_rule, task_type or "planning")
    reasoning_required = _reasoning_required(task_type or "planning", normalized_complexity, normalized_risk, recommended_model)
    cost_saver_model = str(selected_rule.get("cost_saver_model", "")).strip() or None
    use_stronger_model_when = str(selected_rule.get("use_stronger_model_when", "")).strip() or None
    avoid_models = [str(item).strip() for item in selected_rule.get("avoid_models", []) if str(item).strip()]

    confidence = "high"
    if missing_information or ambiguous_route:
        confidence = "low"
    elif task_type_bundle.get("confidence") == "medium" or not cost_priority_explicit:
        confidence = "medium"

    requires_confirmation = bool(
        confidence == "low"
        or ambiguous_route
        or bool(selected_rule.get("requires_confirmation_when_ambiguous"))
        or not bool(switch_support.get("can_auto_switch"))
    )
    question_for_user = _user_question(
        missing_information=missing_information,
        task_type_bundle=task_type_bundle,
        switch_support=switch_support,
        recommended_model=recommended_model,
        cost_priority_explicit=cost_priority_explicit,
    ) if requires_confirmation else ""

    why_parts = list(task_type_bundle.get("evidence", []))
    why_parts.extend(cost_evidence)
    if project_type:
        why_parts.append(f"project_type={project_type}")
    if effective_phase and effective_phase != normalized_phase:
        why_parts.append(f"fallback_phase={effective_phase}")
    why_parts.append(f"rule={selected_rule.get('id', 'default')}")
    why_parts.append(f"risk_level={normalized_risk}")
    why_parts.append(f"complexity={normalized_complexity}")
    why_parts.append(f"reasoning_required={reasoning_required}")
    why_parts.extend(list(switch_support.get("evidence", []))[:3])

    result = {
        "status": "ok",
        "recommended_model": recommended_model,
        "fallback_model": fallback_model,
        "recommended_model_profile": recommended_profile,
        "reasoning_required": reasoning_required,
        "cost_sensitivity": cost_sensitivity,
        "why": f"{selected_rule.get('reason', '').strip()} {'; '.join(item for item in why_parts if item)}".strip(),
        "confidence": confidence,
        "missing_information": missing_information,
        "requires_user_confirmation": requires_confirmation,
        "question_for_user": question_for_user,
        "can_auto_switch": False,
        "auto_switch_method": "not_available" if not bool(switch_support.get("can_auto_switch")) else str(switch_support.get("auto_switch_method", "unknown")).strip() or "unknown",
        "cost_saver_model": cost_saver_model,
        "cheaper_alternative_model": cost_saver_model,
        "use_stronger_model_when": use_stronger_model_when,
        "avoid_models": avoid_models,
        "task_type": task_type or None,
        "matched_rule": selected_rule.get("id"),
        "current_configured_model": switch_support.get("current_project_model") or switch_support.get("current_global_model"),
        "switch_support": switch_support,
        "evidence": why_parts,
        "timestamp": _utc_now_iso(),
        "fallback_profile": recommended_profile,
    }
    if recommended_profile in profiles:
        result["profile_description"] = profiles[recommended_profile].get("description")
    return result


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(add_help=True)
    parser.add_argument("--root", default=None, help="Atlas root to use.")
    parser.add_argument("--task", default="", help="Task text to route.")
    parser.add_argument("--intent", default=None, help="Optional intent hint.")
    parser.add_argument("--phase", default=None, help="Optional current phase hint.")
    parser.add_argument("--risk", default="low", help="Optional risk hint.")
    parser.add_argument("--complexity", default="low", help="Optional complexity hint.")
    parser.add_argument("--project-type", default=None, help="Optional project type hint.")
    parser.add_argument("--skill", default=None, help="Optional recommended skill hint.")
    args = parser.parse_args(argv)

    root = Path(args.root).resolve() if args.root else DEFAULT_ROOT
    result = recommend_model_profile(
        root=root,
        task=args.task,
        intent=args.intent,
        current_phase=args.phase,
        risk_level=args.risk,
        complexity=args.complexity,
        project_type=args.project_type,
        recommended_skill=args.skill,
    )
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0
