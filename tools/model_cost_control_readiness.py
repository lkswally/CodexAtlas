from __future__ import annotations

import argparse
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple


DEFAULT_ROOT = Path(__file__).resolve().parents[1]
CONFIG_PATH = Path("config/model_cost_control_profiles.json")
RISK_LEVELS = {"low", "medium", "high"}
COMPLEXITY_LEVELS = {"low", "medium", "high"}
TASK_TYPES = {
    "planning",
    "architecture",
    "code_execution",
    "audit_review",
    "documentation",
    "design_reasoning",
    "security_review",
    "lightweight_editing",
    "triage",
}


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def load_model_cost_control_profiles(root: Path = DEFAULT_ROOT) -> Dict[str, Any]:
    return json.loads((root / CONFIG_PATH).read_text(encoding="utf-8-sig"))


def _normalize(text: str) -> str:
    return re.sub(r"\s+", " ", str(text or "").strip().lower())


def _normalize_level(value: Optional[str], allowed: set[str], default: str) -> str:
    candidate = _normalize(value or "")
    return candidate if candidate in allowed else default


def _detect_privacy_risk(task: str, rules: Dict[str, Any]) -> Tuple[str, List[str]]:
    normalized_task = _normalize(task)
    signals = rules.get("privacy_signals", {})
    high_terms = [str(term).strip().lower() for term in signals.get("high", []) if str(term).strip()]
    medium_terms = [str(term).strip().lower() for term in signals.get("medium", []) if str(term).strip()]

    high_hits = [term for term in high_terms if term in normalized_task]
    if high_hits:
        return "high", [f"privacy_high_hits={high_hits}"]

    medium_hits = [term for term in medium_terms if term in normalized_task]
    if medium_hits:
        return "medium", [f"privacy_medium_hits={medium_hits}"]

    return "low", ["privacy_risk_low"]


def _build_fallback_posture(
    *,
    task: str,
    resolved_task_type: Optional[str],
    recommended_model_tier: str,
    normalized_risk: str,
    normalized_complexity: str,
    privacy_risk: str,
    explicit_cost_priority: Optional[str],
    rules: Dict[str, Any],
) -> Dict[str, Any]:
    normalized_task = _normalize(task)
    allowed_task_types = [str(item).strip() for item in rules.get("allowed_task_types", []) if str(item).strip()]
    watchlist_task_types = [str(item).strip() for item in rules.get("watchlist_task_types", []) if str(item).strip()]
    blocked_task_types = [str(item).strip() for item in rules.get("blocked_task_types", []) if str(item).strip()]
    provider_terms = [str(item).strip().lower() for item in rules.get("watchlist_provider_terms", []) if str(item).strip()]
    provider_hits = [term for term in provider_terms if term in normalized_task]
    fallback_tier_map = rules.get("fallback_tier_map", {})

    fallback_tier = str(fallback_tier_map.get(recommended_model_tier, "not_allowed")).strip() or "not_allowed"
    status = "not_required"
    fallback_allowed = False
    why_parts: List[str] = []

    if provider_hits:
        status = "watchlist"
        fallback_tier = "local_watchlist"
        why_parts.append(f"provider_runtime_terms={provider_hits}")
    elif resolved_task_type in blocked_task_types or normalized_risk == "high" or normalized_complexity == "high" or privacy_risk == "high":
        status = "blocked"
        fallback_tier = "not_allowed"
        if resolved_task_type in blocked_task_types:
            why_parts.append(f"blocked_task_type={resolved_task_type}")
        if normalized_risk == "high":
            why_parts.append("risk_high")
        if normalized_complexity == "high":
            why_parts.append("complexity_high")
        if privacy_risk == "high":
            why_parts.append("privacy_high")
    elif resolved_task_type in watchlist_task_types or privacy_risk == "medium":
        status = "watchlist"
        fallback_tier = "local_watchlist"
        if resolved_task_type in watchlist_task_types:
            why_parts.append(f"watchlist_task_type={resolved_task_type}")
        if privacy_risk == "medium":
            why_parts.append("privacy_medium")
    elif resolved_task_type in allowed_task_types and fallback_tier != "not_allowed":
        if recommended_model_tier == "mini":
            status = "not_required"
            fallback_tier = "not_allowed"
            why_parts.append("primary_tier_already_mini")
        else:
            status = "recommended"
            fallback_allowed = True
            why_parts.append(f"allowed_task_type={resolved_task_type}")
            if explicit_cost_priority == "high":
                why_parts.append("explicit_cost_saving_request")
            else:
                why_parts.append("bounded_low_risk_task")
    else:
        status = "not_required"
        fallback_tier = "not_allowed"
        if resolved_task_type:
            why_parts.append(f"task_type_not_fallback_target={resolved_task_type}")
        else:
            why_parts.append("task_type_unresolved_for_fallback")

    return {
        "status": status,
        "primary_tier": recommended_model_tier,
        "fallback_tier": fallback_tier,
        "fallback_allowed": fallback_allowed,
        "fallback_mode": str(rules.get("fallback_mode", "manual_only")).strip() or "manual_only",
        "auto_switch_enabled": bool(rules.get("auto_switch_enabled", False)),
        "allowed_task_types": allowed_task_types,
        "blocked_task_types": blocked_task_types,
        "privacy_risk": privacy_risk,
        "requires_human_approval": True,
        "why": "; ".join(why_parts) or "manual_fallback_not_needed",
    }


def _infer_task_type(task: str, hints: Dict[str, List[str]], provided: Optional[str]) -> Tuple[Optional[str], bool, List[str]]:
    normalized_provided = _normalize(provided or "")
    if normalized_provided in TASK_TYPES:
        return normalized_provided, False, [f"task_type_provided={normalized_provided}"]

    normalized_task = _normalize(task)
    candidates: List[str] = []
    evidence: List[str] = []
    for task_type, keywords in hints.items():
        hits = [keyword for keyword in keywords if keyword in normalized_task]
        if hits:
            candidates.append(task_type)
            evidence.append(f"{task_type}_hits={hits}")
    candidates = list(dict.fromkeys(candidates))
    if len(candidates) == 1:
        return candidates[0], False, evidence
    if len(candidates) > 1:
        return None, True, evidence or ["ambiguous_task_type"]
    return None, True, ["task_type_unresolved"]


def _derive_context_band(task: str, estimated_context_chars: Optional[int], thresholds: Dict[str, Any]) -> Tuple[str, int]:
    measured = int(estimated_context_chars) if isinstance(estimated_context_chars, int) and estimated_context_chars >= 0 else len(task or "")
    if measured >= int(thresholds.get("large_chars", 3200)):
        return "large", measured
    if measured >= int(thresholds.get("medium_chars", 1200)):
        return "medium", measured
    return "small", measured


def _cost_priority_explicit(task: str) -> Tuple[Optional[str], List[str]]:
    normalized = _normalize(task)
    evidence: List[str] = []
    if any(term in normalized for term in ("save tokens", "cheaper", "budget", "low cost", "mini model", "fast")):
        evidence.append("explicit_cost_priority=high")
        return "high", evidence
    if any(term in normalized for term in ("best quality", "highest quality", "deep reasoning", "max quality", "careful")):
        evidence.append("explicit_cost_priority=low")
        return "low", evidence
    evidence.append("cost_priority_not_explicit")
    return None, evidence


def assess_model_cost_control(
    *,
    root: Path,
    task: str = "",
    task_type: Optional[str] = None,
    risk_level: str = "low",
    complexity: str = "low",
    current_phase: Optional[str] = None,
    estimated_context_chars: Optional[int] = None,
) -> Dict[str, Any]:
    root = root.resolve()
    config = load_model_cost_control_profiles(root)
    tiers = config.get("tiers", {})
    hints = config.get("task_type_hints", {})
    thresholds = config.get("context_thresholds", {})
    split_rules = config.get("split_task_rules", {})
    confirmation_triggers = config.get("confirmation_triggers", {})
    fallback_rules = config.get("fallback_manual_rules", {})

    normalized_risk = _normalize_level(risk_level, RISK_LEVELS, "medium")
    normalized_complexity = _normalize_level(complexity, COMPLEXITY_LEVELS, "medium")
    resolved_task_type, ambiguous_task_type, task_type_evidence = _infer_task_type(task, hints, task_type)
    context_band, measured_context = _derive_context_band(task, estimated_context_chars, thresholds)
    explicit_cost_priority, cost_evidence = _cost_priority_explicit(task)
    privacy_risk, privacy_evidence = _detect_privacy_risk(task, fallback_rules)
    normalized_task = _normalize(task)

    mixed_planning_and_execution = (
        any(term in normalized_task for term in ("plan", "architecture", "strategy"))
        and any(term in normalized_task for term in ("implement", "edit", "fix", "refactor", "code"))
    )

    if normalized_risk == "high" or normalized_complexity == "high" or resolved_task_type in {"architecture", "security_review", "planning"}:
        recommended_model_tier = "strong"
    elif normalized_risk == "low" and normalized_complexity == "low" and resolved_task_type in {"documentation", "triage", "lightweight_editing"}:
        recommended_model_tier = "mini"
    else:
        recommended_model_tier = "medium"

    tier_profile = tiers.get(recommended_model_tier, {})
    cost_saver_strategy = str(tier_profile.get("default_cost_saver_strategy", "")).strip() or "start_with_mid_tier_and_escalate_only_if_blocked"
    context_reduction_strategy = str(tier_profile.get("default_context_reduction_strategy", "")).strip() or "trim_background_to_relevant_files_and_findings"

    if context_band == "large":
        context_reduction_strategy = "summarize_prior_evidence_and_trim_scope_before_model_escalation"
    elif context_band == "medium" and recommended_model_tier == "strong":
        context_reduction_strategy = "reduce_background_to_only_the_decision-critical_context"

    split_task_recommended = bool(
        (context_band == "large" and bool(split_rules.get("large_context_requires_split", True)))
        or (mixed_planning_and_execution and bool(split_rules.get("mixed_planning_and_execution_requires_split", True)))
        or (
            normalized_risk == "high"
            and normalized_complexity == "high"
            and bool(split_rules.get("high_risk_plus_high_complexity_requires_split", True))
        )
    )

    risks: List[str] = []
    if context_band == "large" and recommended_model_tier == "strong":
        risks.append("oversized_context_for_strong_tier")
    if recommended_model_tier == "strong" and normalized_risk == "low":
        risks.append("strong_tier_for_low_risk_task")
    if ambiguous_task_type:
        risks.append("ambiguous_task_type")
    if mixed_planning_and_execution:
        risks.append("mixed_task_without_split")
    cost_tradeoff_unclear = explicit_cost_priority is None and (
        recommended_model_tier == "strong"
        or context_band == "large"
        or mixed_planning_and_execution
    )

    if cost_tradeoff_unclear:
        risks.append("cost_vs_quality_not_explicit")

    fallback_posture = _build_fallback_posture(
        task=task,
        resolved_task_type=resolved_task_type,
        recommended_model_tier=recommended_model_tier,
        normalized_risk=normalized_risk,
        normalized_complexity=normalized_complexity,
        privacy_risk=privacy_risk,
        explicit_cost_priority=explicit_cost_priority,
        rules=fallback_rules,
    )

    requires_user_confirmation = bool(
        (recommended_model_tier == "strong" and confirmation_triggers.get("strong_tier_requires_confirmation", True))
        or (ambiguous_task_type and confirmation_triggers.get("ambiguous_task_type_requires_confirmation", True))
        or (context_band == "large" and confirmation_triggers.get("large_context_requires_confirmation", True))
        or (cost_tradeoff_unclear and confirmation_triggers.get("cost_vs_quality_unclear_requires_confirmation", True))
        or (
            bool(fallback_posture.get("requires_human_approval"))
            and str(fallback_posture.get("status", "")).strip() in {"recommended", "watchlist", "blocked"}
        )
    )

    if recommended_model_tier == "mini":
        manual_action_required = "Select a cheaper mini-tier model manually in Codex Desktop if the task stays low-risk after review."
    elif recommended_model_tier == "medium":
        manual_action_required = "Keep the current recommendation manual: start with a mid-tier model in Codex Desktop and escalate only if needed."
    else:
        manual_action_required = "Select a stronger model manually in Codex Desktop only after confirming the task really needs the extra cost."

    why_parts = [
        *task_type_evidence,
        *cost_evidence,
        *privacy_evidence,
        f"risk={normalized_risk}",
        f"complexity={normalized_complexity}",
        f"context_band={context_band}",
        f"context_chars={measured_context}",
    ]
    if current_phase:
        why_parts.append(f"phase={_normalize(current_phase)}")
    if split_task_recommended:
        why_parts.append("split_task_recommended")

    status = "needs_confirmation" if requires_user_confirmation else "ok"

    return {
        "status": status,
        "recommended_model_tier": recommended_model_tier,
        "cost_saver_strategy": cost_saver_strategy,
        "context_reduction_strategy": context_reduction_strategy,
        "split_task_recommended": split_task_recommended,
        "requires_user_confirmation": requires_user_confirmation,
        "risks": risks,
        "fallback_posture": fallback_posture,
        "why": "; ".join(why_parts),
        "manual_action_required": manual_action_required,
        "advisory_only": bool(config.get("advisory_only", True)),
        "timestamp": _utc_now_iso(),
    }


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(add_help=True)
    parser.add_argument("--task", default="")
    parser.add_argument("--task-type", default=None)
    parser.add_argument("--risk", default="low")
    parser.add_argument("--complexity", default="low")
    parser.add_argument("--phase", default=None)
    parser.add_argument("--estimated-context-chars", type=int, default=None)
    args = parser.parse_args(argv)

    result = assess_model_cost_control(
        root=DEFAULT_ROOT,
        task=args.task,
        task_type=args.task_type,
        risk_level=args.risk,
        complexity=args.complexity,
        current_phase=args.phase,
        estimated_context_chars=args.estimated_context_chars,
    )
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
