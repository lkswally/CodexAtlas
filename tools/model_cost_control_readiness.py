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

    normalized_risk = _normalize_level(risk_level, RISK_LEVELS, "medium")
    normalized_complexity = _normalize_level(complexity, COMPLEXITY_LEVELS, "medium")
    resolved_task_type, ambiguous_task_type, task_type_evidence = _infer_task_type(task, hints, task_type)
    context_band, measured_context = _derive_context_band(task, estimated_context_chars, thresholds)
    explicit_cost_priority, cost_evidence = _cost_priority_explicit(task)
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

    requires_user_confirmation = bool(
        (recommended_model_tier == "strong" and confirmation_triggers.get("strong_tier_requires_confirmation", True))
        or (ambiguous_task_type and confirmation_triggers.get("ambiguous_task_type_requires_confirmation", True))
        or (context_band == "large" and confirmation_triggers.get("large_context_requires_confirmation", True))
        or (cost_tradeoff_unclear and confirmation_triggers.get("cost_vs_quality_unclear_requires_confirmation", True))
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
