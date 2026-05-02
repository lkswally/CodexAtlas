from __future__ import annotations

from typing import Any, Dict, List, Optional


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


def build_execution_plan(
    *,
    phase_guidance: Dict[str, Any],
    phase_validity: str,
    top_priorities: List[Dict[str, Any]],
    quick_wins: List[str],
    intent_analysis: Optional[Dict[str, Any]],
    skill_creation_signal: Optional[Dict[str, Any]],
    overall_status: str,
) -> Dict[str, Any]:
    current_phase = str(phase_guidance.get("current_phase", "")).strip()
    candidates = [
        *_phase_candidates(phase_guidance, phase_validity, overall_status),
        *_intent_candidates(intent_analysis),
        *_priority_candidates(top_priorities, current_phase),
        *_quick_win_candidates(quick_wins, current_phase),
        *_skill_candidate(skill_creation_signal, overall_status),
    ]
    ranked = _dedupe_candidates(candidates)
    limited = ranked[:3]

    execution_plan = [
        {
            "step": index,
            "action": item["action"],
            "reason": item["reason"],
            "impact": item["impact"],
            "effort": item["effort"],
            "source": item["source"],
        }
        for index, item in enumerate(limited, start=1)
    ]
    primary_action = execution_plan[0]["action"] if execution_plan else None
    why_now = execution_plan[0]["reason"] if execution_plan else "No action is more urgent than keeping the current validated state."
    return {
        "execution_plan": execution_plan,
        "primary_action": primary_action,
        "why_now": why_now,
        "quick_wins": _dedupe_strings(quick_wins, 2),
    }
