from __future__ import annotations

import argparse
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional


DEFAULT_ROOT = Path(__file__).resolve().parents[1]
MODEL_PROFILES_PATH = Path("config") / "model_profiles.json"
MODEL_ROUTING_RULES_PATH = Path("config") / "model_routing_rules.json"
TASK_MODE_KEYWORDS = {
    "documentation": ("readme", "document", "docs", "copy", "content", "status"),
    "audit": ("audit", "review", "certify", "validation", "governance"),
    "design": ("design", "branding", "ux", "hero", "landing", "visual"),
    "implementation": ("implement", "build", "refactor", "edit", "code", "fix"),
    "research": ("research", "look up", "docs search", "official docs", "compare"),
    "security": ("security", "secret", "auth", "permission", "credentials"),
}
HIGH_REASONING_INTENTS = {"planning", "architecture", "research", "project_creation", "security"}
MEDIUM_REASONING_INTENTS = {"code_review", "branding_ux", "code_execution"}
LOW_COMPLEXITY_TERMS = ("small", "simple", "minor", "quick", "lightweight", "copy edit")
COST_SAVING_TERMS = ("save tokens", "cheaper", "cost", "low cost", "budget", "lightweight")


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


def _resolve_alias(alias: str, aliases: Dict[str, str], profiles: Dict[str, Any], default_profile: str) -> str:
    profile_name = str(aliases.get(alias, alias)).strip() or default_profile
    if profile_name not in profiles:
        return default_profile
    return profile_name


def _detect_task_mode(*, task: str, intent: Optional[str], recommended_skill: Optional[str]) -> str:
    normalized = _normalize(task)
    if recommended_skill in {"product-branding-review", "visual-direction-checkpoint", "design-system-review"}:
        return "design"
    if recommended_skill == "repo-audit":
        return "audit"
    if recommended_skill == "project-bootstrap":
        return "implementation"
    if intent == "documentation":
        return "documentation"
    if intent in {"code_review", "security"}:
        return "audit" if intent == "code_review" else "security"
    if intent == "branding_ux":
        return "design"
    if intent == "code_execution":
        return "implementation"
    if intent == "research":
        return "research"
    for task_mode, keywords in TASK_MODE_KEYWORDS.items():
        if any(keyword in normalized for keyword in keywords):
            return task_mode
    return "documentation"


def _reasoning_required(intent: Optional[str], complexity: str, risk_level: str, task_mode: str) -> str:
    if risk_level == "high" or complexity == "high" or task_mode in {"security", "research"}:
        return "high"
    if intent in HIGH_REASONING_INTENTS or task_mode in {"audit", "design", "implementation"}:
        return "medium"
    if intent in MEDIUM_REASONING_INTENTS:
        return "medium"
    return "low"


def _cost_sensitivity(task: str, task_mode: str, risk_level: str, complexity: str) -> str:
    normalized = _normalize(task)
    if any(term in normalized for term in COST_SAVING_TERMS):
        return "high"
    if risk_level == "high" or complexity == "high" or task_mode in {"security", "research"}:
        return "low"
    if task_mode in {"documentation", "audit"}:
        return "high"
    return "medium"


def _base_alias(
    *,
    rules: Dict[str, Any],
    intent: Optional[str],
    recommended_skill: Optional[str],
    current_phase: Optional[str],
    task_mode: str,
    risk_level: str,
    complexity: str,
    task: str,
) -> Dict[str, Any]:
    evidence: List[str] = []
    intent_aliases = rules.get("intent_aliases", {})
    skill_aliases = rules.get("skill_aliases", {})
    phase_bias = rules.get("phase_bias", {})

    alias = str(intent_aliases.get(intent or "", rules.get("default_profile_alias", "cost_saver"))).strip()
    evidence.append(f"intent_alias={intent or 'unknown'}->{alias}")

    if recommended_skill:
        skill_alias = str(skill_aliases.get(recommended_skill, "")).strip()
        if skill_alias:
            alias = skill_alias
            evidence.append(f"skill_alias={recommended_skill}->{alias}")

    phase_alias = str(phase_bias.get(current_phase or "", "")).strip()
    if current_phase and phase_alias and task_mode in {"documentation", "audit"}:
        alias = phase_alias
        evidence.append(f"phase_bias={current_phase}->{alias}")

    normalized = _normalize(task)
    if risk_level == "high":
        alias = "security_review"
        evidence.append("risk_bias=high->security_review")
    elif complexity == "high" and task_mode not in {"design", "audit"}:
        alias = "deep_reasoning"
        evidence.append("complexity_bias=high->deep_reasoning")
    elif task_mode == "design":
        alias = "design_reasoning"
        evidence.append("task_mode=design")
    elif task_mode == "audit":
        alias = "audit_review"
        evidence.append("task_mode=audit")
    elif task_mode == "implementation" and any(term in normalized for term in LOW_COMPLEXITY_TERMS):
        alias = "lightweight_editing"
        evidence.append("low_complexity_edit_detected")
    elif task_mode == "implementation":
        alias = "code_execution"
        evidence.append("task_mode=implementation")
    elif task_mode == "documentation":
        alias = "documentation"
        evidence.append("task_mode=documentation")
    elif task_mode == "research":
        alias = "deep_reasoning"
        evidence.append("task_mode=research")

    if any(term in normalized for term in COST_SAVING_TERMS) and risk_level != "high":
        alias = "cost_saver"
        evidence.append("explicit_cost_saving_bias")

    return {"alias": alias, "evidence": evidence}


def recommend_model_profile(
    *,
    root: Path,
    task: str = "",
    intent: Optional[str] = None,
    current_phase: Optional[str] = None,
    risk_level: str = "low",
    complexity: str = "low",
    project_type: Optional[str] = None,
    recommended_skill: Optional[str] = None,
) -> Dict[str, Any]:
    root = root.resolve()
    profiles_config = _load_profiles(root)
    rules = _load_rules(root)
    profiles = profiles_config.get("profiles", {})
    default_profile = str(profiles_config.get("default_profile", "cost_saver")).strip() or "cost_saver"
    aliases = {str(key).strip(): str(value).strip() for key, value in rules.get("aliases", {}).items()}
    fallback_aliases = {str(key).strip(): str(value).strip() for key, value in rules.get("fallback_by_alias", {}).items()}

    task_mode = _detect_task_mode(task=task, intent=intent, recommended_skill=recommended_skill)
    alias_bundle = _base_alias(
        rules=rules,
        intent=intent,
        recommended_skill=recommended_skill,
        current_phase=current_phase,
        task_mode=task_mode,
        risk_level=risk_level,
        complexity=complexity,
        task=task,
    )
    selected_alias = alias_bundle["alias"]
    recommended_profile = _resolve_alias(selected_alias, aliases, profiles, default_profile)
    fallback_alias = str(fallback_aliases.get(selected_alias, rules.get("default_fallback_alias", "deep_reasoning"))).strip()
    fallback_profile = _resolve_alias(fallback_alias, aliases, profiles, default_profile)
    reasoning_required = _reasoning_required(intent, complexity, risk_level, task_mode)
    cost_sensitivity = _cost_sensitivity(task, task_mode, risk_level, complexity)

    avoid_profiles: List[str] = []
    if recommended_profile == "security":
        avoid_profiles.extend(["cost_saver", "creative_product"])
    elif recommended_profile == "creative_product":
        avoid_profiles.extend(["security", "cost_saver"])
    elif recommended_profile == "reviewer":
        avoid_profiles.append("creative_product")
    elif recommended_profile == "cost_saver":
        avoid_profiles.extend(["security", "creative_product"])
    elif recommended_profile == "code_execution":
        avoid_profiles.append("creative_product")
    avoid_profiles = [profile for profile in avoid_profiles if profile in profiles and profile != recommended_profile]

    why_parts = list(alias_bundle["evidence"])
    if project_type:
        why_parts.append(f"project_type={project_type}")
    why_parts.append(f"reasoning_required={reasoning_required}")
    why_parts.append(f"cost_sensitivity={cost_sensitivity}")

    return {
        "status": "ok",
        "recommended_model_profile": recommended_profile,
        "recommended_alias": selected_alias,
        "task_mode": task_mode,
        "reasoning_required": reasoning_required,
        "cost_sensitivity": cost_sensitivity,
        "fallback_profile": fallback_profile,
        "why": "; ".join(why_parts),
        "avoid_profiles": avoid_profiles,
        "evidence": why_parts,
        "timestamp": _utc_now_iso(),
    }


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


if __name__ == "__main__":
    raise SystemExit(main())
