from __future__ import annotations

from typing import Any, Dict, List, Optional


EXTERNAL_TOOL_HINTS = (
    "mcp",
    "github cli",
    "external tool",
    "official docs",
    "web search",
    "context7",
    "serena",
    "playwright",
)


def _normalize(text: str) -> str:
    return " ".join(str(text).lower().split())


def _dedupe_strings(values: List[str], limit: int) -> List[str]:
    unique: List[str] = []
    seen: set[str] = set()
    for value in values:
        value_s = str(value).strip()
        if not value_s:
            continue
        key = _normalize(value_s)
        if key in seen:
            continue
        seen.add(key)
        unique.append(value_s)
        if len(unique) >= limit:
            break
    return unique


def _candidate(
    *,
    action: str,
    reason: str,
    impact: str,
    effort: str,
    source: str,
    score: int,
) -> Dict[str, Any]:
    return {
        "action": action,
        "reason": reason,
        "impact": impact,
        "effort": effort,
        "source": source,
        "_score": score,
    }


def _feedback_weight_for_action(
    feedback_analysis: Optional[Dict[str, Any]],
    action: str,
    source: str,
) -> Dict[str, Any]:
    action_key = _normalize(action)
    if not isinstance(feedback_analysis, dict):
        return {"score_delta": 0, "feedback_weight": "neutral", "feedback_reason": None, "should_filter": False}

    for item in feedback_analysis.get("action_feedback", []):
        if not isinstance(item, dict):
            continue
        if _normalize(str(item.get("action", ""))) != action_key:
            continue
        frequency = int(item.get("frequency", 0) or 0)
        acceptance_rate = float(item.get("acceptance_rate", 0.0) or 0.0)
        ignore_rate = float(item.get("ignore_rate", 0.0) or 0.0)
        last_decision = str(item.get("last_decision", "")).strip() or None

        if source == "phase":
            return {
                "score_delta": 0,
                "feedback_weight": "neutral",
                "feedback_reason": "Phase guidance keeps precedence over historical preference.",
                "should_filter": False,
            }
        if frequency >= 2 and ignore_rate >= 0.75:
            return {
                "score_delta": -20,
                "feedback_weight": "down",
                "feedback_reason": "Repeatedly ignored in prior decision feedback.",
                "should_filter": True,
            }
        if ignore_rate >= 0.5 or last_decision == "ignored":
            return {
                "score_delta": -10,
                "feedback_weight": "down",
                "feedback_reason": "Recently ignored in prior decision feedback.",
                "should_filter": False,
            }
        if acceptance_rate >= 0.75 and frequency >= 2:
            return {
                "score_delta": 12,
                "feedback_weight": "up",
                "feedback_reason": "Consistently accepted in prior decision feedback.",
                "should_filter": False,
            }
        if acceptance_rate >= 0.5 or last_decision == "accepted":
            return {
                "score_delta": 6,
                "feedback_weight": "up",
                "feedback_reason": "Accepted in prior decision feedback.",
                "should_filter": False,
            }
    return {"score_delta": 0, "feedback_weight": "neutral", "feedback_reason": None, "should_filter": False}


def _phase_candidates(
    phase_guidance: Dict[str, Any],
    phase_validity: str,
    overall_status: str,
) -> List[Dict[str, Any]]:
    current_phase = str(phase_guidance.get("current_phase", "")).strip()
    next_steps = [str(item).strip() for item in phase_guidance.get("recommended_next_steps", []) if str(item).strip()]
    risks = [str(item).strip() for item in phase_guidance.get("top_phase_risks", []) if str(item).strip()]
    candidates: List[Dict[str, Any]] = []
    if not next_steps:
        return candidates

    base_score = 95 if phase_validity != "valid" else 78
    if overall_status != "ready":
        base_score += 6
    candidates.append(
        _candidate(
            action=next_steps[0],
            reason=f"Phase `{current_phase}` defines the safest next move before taking broader actions.",
            impact="high",
            effort="low",
            source="phase",
            score=base_score,
        )
    )
    if len(next_steps) > 1:
        candidates.append(
            _candidate(
                action=next_steps[1],
                reason=f"Phase guidance highlights this as the next controlled follow-up after `{next_steps[0]}`.",
                impact="medium",
                effort="low",
                source="phase",
                score=base_score - 8,
            )
        )
    if risks:
        candidates.append(
            _candidate(
                action=f"Avoid {risks[0]}",
                reason=f"Current phase risk: {risks[0]}.",
                impact="medium",
                effort="low",
                source="phase",
                score=base_score - 12,
            )
        )
    return candidates


def _intent_candidates(intent_analysis: Optional[Dict[str, Any]]) -> List[Dict[str, Any]]:
    if not isinstance(intent_analysis, dict):
        return []
    missing = [str(item).strip() for item in intent_analysis.get("missing_definition", []) if str(item).strip()]
    if not missing:
        return []
    return [
        _candidate(
            action=f"Clarify {missing[0]}",
            reason="Intent analysis still reports missing definition, so later recommendations are less trustworthy until this is explicit.",
            impact="high",
            effort="low",
            source="intent",
            score=88,
        )
    ]


def _priority_candidates(
    top_priorities: List[Dict[str, Any]],
    current_phase: str,
) -> List[Dict[str, Any]]:
    candidates: List[Dict[str, Any]] = []
    for item in top_priorities:
        message = str(item.get("message", "")).strip()
        if not message:
            continue
        source = str(item.get("source", "")).strip()
        severity = str(item.get("severity", "medium")).strip()
        check = str(item.get("check", "")).strip() or "priority"
        score = {"blocker": 92, "high": 82, "medium": 72, "low": 62}.get(severity, 60)
        mapped_source = "design_audit" if source == "design_intelligence_audit" else source or "priority"
        if mapped_source == "design_audit" and current_phase not in {"audit", "certified", "build"}:
            score -= 10
        impact = "high" if severity in {"blocker", "high"} else "medium"
        effort = "medium" if mapped_source == "design_audit" else "low"
        candidates.append(
            _candidate(
                action=message,
                reason=f"Originates from `{check}` with `{severity}` severity.",
                impact=impact,
                effort=effort,
                source=mapped_source,
                score=score,
            )
        )
    return candidates


def _quick_win_candidates(quick_wins: List[str], current_phase: str) -> List[Dict[str, Any]]:
    candidates: List[Dict[str, Any]] = []
    for idx, message in enumerate(_dedupe_strings(quick_wins, 2), start=1):
        score = 64 - ((idx - 1) * 4)
        if current_phase not in {"audit", "certified", "build"}:
            score -= 6
        candidates.append(
            _candidate(
                action=message,
                reason="This is already classified as a quick win by the upstream report.",
                impact="medium",
                effort="low",
                source="quick_win",
                score=score,
            )
        )
    return candidates


def _skill_candidate(skill_creation_signal: Optional[Dict[str, Any]], overall_status: str) -> List[Dict[str, Any]]:
    if not isinstance(skill_creation_signal, dict):
        return []
    if not bool(skill_creation_signal.get("should_create")):
        return []
    candidate_name = str(skill_creation_signal.get("candidate_name", "new-skill")).strip()
    score = 58 if overall_status == "ready" else 44
    return [
        _candidate(
            action=f"Evaluate creation of `{candidate_name}` as a reusable Atlas skill",
            reason="The skill evaluator sees enough cross-project value to justify a dedicated capability.",
            impact="medium",
            effort="high",
            source="skill",
            score=score,
        )
    ]


def _dedupe_candidates(candidates: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    deduped: List[Dict[str, Any]] = []
    seen: set[str] = set()
    for item in sorted(candidates, key=lambda candidate: candidate["_score"], reverse=True):
        key = _normalize(item["action"])
        if key in seen:
            continue
        seen.add(key)
        deduped.append(item)
    return deduped


def _is_external_tool_action(action: str) -> bool:
    normalized = _normalize(action)
    return any(hint in normalized for hint in EXTERNAL_TOOL_HINTS)


def _prefer_local_resolution(candidates: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    if not candidates:
        return candidates
    local_candidates = [item for item in candidates if not _is_external_tool_action(str(item.get("action", "")))]
    if local_candidates:
        return local_candidates
    return candidates


def _apply_feedback_weights(
    candidates: List[Dict[str, Any]],
    feedback_analysis: Optional[Dict[str, Any]],
) -> List[Dict[str, Any]]:
    adjusted: List[Dict[str, Any]] = []
    for item in candidates:
        feedback_meta = _feedback_weight_for_action(
            feedback_analysis=feedback_analysis,
            action=str(item.get("action", "")),
            source=str(item.get("source", "")),
        )
        candidate = dict(item)
        candidate["_score"] = int(candidate["_score"]) + int(feedback_meta["score_delta"])
        candidate["feedback_weight"] = feedback_meta["feedback_weight"]
        candidate["feedback_reason"] = feedback_meta["feedback_reason"]
        candidate["_should_filter"] = bool(feedback_meta["should_filter"])
        adjusted.append(candidate)
    return adjusted


def build_execution_plan(
    *,
    phase_guidance: Dict[str, Any],
    phase_validity: str,
    top_priorities: List[Dict[str, Any]],
    quick_wins: List[str],
    intent_analysis: Optional[Dict[str, Any]],
    skill_creation_signal: Optional[Dict[str, Any]],
    overall_status: str,
    feedback_analysis: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    current_phase = str(phase_guidance.get("current_phase", "")).strip()
    candidates = [
        *_phase_candidates(phase_guidance, phase_validity, overall_status),
        *_intent_candidates(intent_analysis),
        *_priority_candidates(top_priorities, current_phase),
        *_quick_win_candidates(quick_wins, current_phase),
        *_skill_candidate(skill_creation_signal, overall_status),
    ]
    adjusted_candidates = _apply_feedback_weights(candidates, feedback_analysis)
    ranked = _dedupe_candidates(_prefer_local_resolution(adjusted_candidates))
    limited = [item for item in ranked if not item.get("_should_filter")][:3]
    if not limited:
        limited = ranked[:3]

    execution_plan = [
        {
            "step": index,
            "action": item["action"],
            "reason": item["reason"],
            "impact": item["impact"],
            "effort": item["effort"],
            "source": item["source"],
            "feedback_weight": item.get("feedback_weight", "neutral"),
        }
        for index, item in enumerate(limited, start=1)
    ]
    feedback_adjusted_priorities = [
        {
            "action": item["action"],
            "source": item["source"],
            "feedback_weight": item.get("feedback_weight", "neutral"),
            "feedback_reason": item.get("feedback_reason"),
        }
        for item in limited
    ]
    primary_action = execution_plan[0]["action"] if execution_plan else None
    why_now = execution_plan[0]["reason"] if execution_plan else "No action is more urgent than keeping the current validated state."
    return {
        "execution_plan": execution_plan,
        "primary_action": primary_action,
        "why_now": why_now,
        "quick_wins": _dedupe_strings(quick_wins, 2),
        "feedback_adjusted_priorities": feedback_adjusted_priorities,
    }
