from __future__ import annotations

import argparse
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

try:
    from tools.project_intent_analyzer import analyze_project_intent
except ModuleNotFoundError:
    from project_intent_analyzer import analyze_project_intent


DEFAULT_ROOT = Path(__file__).resolve().parents[1]
HIGH_COMPLEXITY_TERMS = ("hook", "mcp", "deploy", "autonomous", "self-heal", "runtime", "agent fleet")
REUSE_TERMS = ("reusable", "factory", "global", "cross-project", "repeatable", "system", "governance", "workflow", "skill")
LOCAL_ONLY_TERMS = ("landing", "copy", "page", "hero", "single project", "one project", "local", "codexatlas-web")
HIGH_EXTERNAL_DEPENDENCY_TERMS = (
    "mcp",
    "playwright",
    "docker",
    "install",
    "sync",
    "autonomous",
    "self-heal",
    "runtime",
    "browser automation",
    "provider token",
    "secret",
)
MEDIUM_EXTERNAL_DEPENDENCY_TERMS = (
    "api",
    "sdk",
    "provider",
    "github",
    "vercel",
    "external service",
    "remote docs",
)
HIGH_RISK_TERMS = ("mcp", "runtime", "install", "sync", "self-heal", "autonomous")
DEFAULT_LIFECYCLE_RULES = {
    "states": ["candidate", "experimental", "stable", "deprecated", "archived", "rejected"],
    "human_approval_required_by_state": {
        "candidate": False,
        "experimental": True,
        "stable": True,
        "deprecated": True,
        "archived": True,
        "rejected": False,
    },
    "external_dependency_signals": {
        "high_terms": list(HIGH_EXTERNAL_DEPENDENCY_TERMS),
        "medium_terms": list(MEDIUM_EXTERNAL_DEPENDENCY_TERMS),
    },
    "decision_council_triggers": [
        "duplication_risk_high",
        "external_dependency_risk_high",
        "high_complexity",
        "surface_change_high",
    ],
}


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _normalize(text: str) -> str:
    return re.sub(r"\s+", " ", text.lower()).strip()


def _normalize_compact(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", " ", text.lower()).strip()


def _read_json(path: Path) -> Dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def _load_lifecycle_rules(root: Path) -> Dict[str, Any]:
    path = root / "config" / "skill_lifecycle_rules.json"
    if not path.exists():
        return dict(DEFAULT_LIFECYCLE_RULES)
    data = _read_json(path)
    if not isinstance(data, dict):
        return dict(DEFAULT_LIFECYCLE_RULES)
    merged = dict(DEFAULT_LIFECYCLE_RULES)
    merged.update(data)
    return merged


def _load_skill_catalog(root: Path) -> List[Dict[str, Any]]:
    skills_dir = root / "skills"
    skills: List[Dict[str, Any]] = []
    if not skills_dir.exists():
        return skills
    for skill_dir in sorted(path for path in skills_dir.iterdir() if path.is_dir() and not path.name.startswith("_")):
        skill_json = skill_dir / "skill.json"
        if not skill_json.exists():
            continue
        try:
            metadata = _read_json(skill_json)
        except Exception:
            continue
        if not isinstance(metadata, dict):
            continue
        skills.append(
            {
                "id": skill_dir.name,
                "name": str(metadata.get("name", "")).strip() or skill_dir.name,
                "intent_keywords": [str(item).strip().lower() for item in metadata.get("intent_keywords", []) if str(item).strip()],
                "risk_level": str(metadata.get("risk_level", "")).strip(),
            }
        )
    return skills


def _match_existing_skills(candidate_name: str, problem_statement: str, skills: List[Dict[str, Any]]) -> List[Dict[str, str]]:
    normalized_name = _normalize(candidate_name)
    normalized_problem = _normalize(problem_statement)
    overlaps: List[Dict[str, str]] = []
    for skill in skills:
        skill_name = str(skill.get("name", "")).strip().lower()
        skill_id = str(skill.get("id", "")).strip()
        keywords = list(skill.get("intent_keywords", []))
        signals = [skill_name, skill_id.lower(), *keywords]
        matched_signal = next(
            (
                signal
                for signal in signals
                if signal and (signal in normalized_name or signal in normalized_problem)
            ),
            None,
        )
        if matched_signal:
            overlaps.append({"skill_id": skill_id, "matched_signal": matched_signal})
    deduped: Dict[str, Dict[str, str]] = {}
    for overlap in overlaps:
        deduped.setdefault(overlap["skill_id"], overlap)
    return [deduped[key] for key in sorted(deduped)]


def _evaluate_reuse(problem_statement: str, project_type: str, overlaps: List[Dict[str, str]]) -> Tuple[str, List[str]]:
    normalized = _normalize(problem_statement)
    evidence: List[str] = []
    reuse_hits = [term for term in REUSE_TERMS if term in normalized]
    if reuse_hits:
        evidence.append(f"reuse_terms={reuse_hits}")
    if project_type in {"internal_tool", "frontend_app", "backend_service", "fullstack", "ai_agent_system"}:
        evidence.append(f"project_type={project_type}")
    if overlaps:
        evidence.append(f"overlap={[item['skill_id'] for item in overlaps]}")
        if len(overlaps) >= 2:
            return "low", evidence
    if reuse_hits and project_type != "unknown":
        return "high", evidence
    if project_type != "unknown":
        return "medium", evidence
    return "low", evidence or ["limited_reuse_signal"]


def _evaluate_complexity(problem_statement: str) -> Tuple[str, List[str]]:
    normalized = _normalize(problem_statement)
    hits = [term for term in HIGH_COMPLEXITY_TERMS if term in normalized]
    if hits:
        return "high", [f"high_complexity_terms={hits}"]
    if any(term in normalized for term in ("prompt", "report", "review", "audit", "guidance", "checklist")):
        return "low", ["helper_pattern_detected"]
    return "medium", ["default_complexity=medium"]


def _evaluate_need_score(problem_statement: str, project_type: str, overlaps: List[Dict[str, str]], reuse_potential: str, complexity: str) -> Tuple[int, List[str]]:
    normalized = _normalize(problem_statement)
    score = 45
    evidence: List[str] = []
    if reuse_potential == "high":
        score += 25
        evidence.append("reuse_potential_high")
    elif reuse_potential == "medium":
        score += 10
        evidence.append("reuse_potential_medium")
    else:
        score -= 15
        evidence.append("reuse_potential_low")

    if overlaps:
        score -= min(len(overlaps) * 15, 30)
        evidence.append(f"existing_skill_overlap={[item['skill_id'] for item in overlaps]}")

    local_hits = [term for term in LOCAL_ONLY_TERMS if term in normalized]
    if local_hits:
        score -= 15
        evidence.append(f"local_only_terms={local_hits}")

    if project_type == "unknown":
        score -= 10
        evidence.append("project_type_unknown")

    if complexity == "high":
        score -= 20
        evidence.append("complexity_high")
    elif complexity == "low":
        score += 5
        evidence.append("complexity_low")

    return max(0, min(score, 100)), evidence


def _find_term_hits(normalized_text: str, terms: List[str]) -> List[str]:
    hits: List[str] = []
    for term in terms:
        candidate = str(term).strip().lower()
        if candidate and candidate in normalized_text:
            hits.append(candidate)
    return sorted(set(hits))


def _evaluate_duplication_risk(
    candidate_name: str,
    overlaps: List[Dict[str, str]],
    problem_statement: str,
) -> Tuple[str, List[str]]:
    if not overlaps:
        return "low", ["no_catalog_overlap_detected"]

    normalized_name = _normalize(candidate_name)
    compact_name = _normalize_compact(candidate_name)
    exact_name_match = any(
        normalized_name == _normalize(item["skill_id"])
        or normalized_name == _normalize(item["matched_signal"])
        or compact_name == _normalize_compact(item["skill_id"])
        or compact_name == _normalize_compact(item["matched_signal"])
        or _normalize_compact(item["skill_id"]) in compact_name
        or _normalize_compact(item["matched_signal"]) in compact_name
        for item in overlaps
    )
    if exact_name_match or len(overlaps) >= 2:
        return "high", [
            f"overlap_skills={[item['skill_id'] for item in overlaps]}",
            "same_trigger_same_output_risk",
        ]

    normalized_problem = _normalize(problem_statement)
    if any(item["matched_signal"] in normalized_problem for item in overlaps):
        return "high", [f"overlap_skills={[item['skill_id'] for item in overlaps]}"]

    return "medium", [f"partial_overlap_skills={[item['skill_id'] for item in overlaps]}"]


def _evaluate_external_dependency_risk(problem_statement: str, lifecycle_rules: Dict[str, Any]) -> Tuple[str, List[str]]:
    normalized = _normalize(problem_statement)
    signals = lifecycle_rules.get("external_dependency_signals", {})
    high_terms = signals.get("high_terms", list(HIGH_EXTERNAL_DEPENDENCY_TERMS))
    medium_terms = signals.get("medium_terms", list(MEDIUM_EXTERNAL_DEPENDENCY_TERMS))

    high_hits = _find_term_hits(normalized, list(high_terms))
    if high_hits:
        return "high", [f"external_high_terms={high_hits}"]

    medium_hits = _find_term_hits(normalized, list(medium_terms))
    if medium_hits:
        return "medium", [f"external_medium_terms={medium_hits}"]

    return "low", ["external_dependency_signals=none"]


def _requires_decision_council(
    *,
    duplication_risk: str,
    external_dependency_risk: str,
    complexity: str,
    need_score: int,
    lifecycle_rules: Dict[str, Any],
) -> Tuple[bool, List[str]]:
    triggers: List[str] = []
    configured_triggers = set(lifecycle_rules.get("decision_council_triggers", []))

    if duplication_risk == "high" and "duplication_risk_high" in configured_triggers:
        triggers.append("duplication_risk_high")
    if external_dependency_risk == "high" and "external_dependency_risk_high" in configured_triggers:
        triggers.append("external_dependency_risk_high")
    if complexity == "high" and "high_complexity" in configured_triggers:
        triggers.append("high_complexity")
    if need_score >= 80 and (duplication_risk != "low" or external_dependency_risk != "low") and "surface_change_high" in configured_triggers:
        triggers.append("surface_change_high")

    return bool(triggers), [f"decision_council_triggers={triggers}"] if triggers else ["decision_council_not_required"]


def _derive_lifecycle_outcome(
    *,
    need_score: int,
    reuse_potential: str,
    complexity: str,
    duplication_risk: str,
    external_dependency_risk: str,
    lifecycle_rules: Dict[str, Any],
) -> Tuple[str, str, List[str]]:
    blockers: List[str] = []
    if duplication_risk != "low":
        blockers.append("existing_capability_overlap")
    if reuse_potential != "high":
        blockers.append("reuse_signal_not_strong_enough")
    if need_score < 70:
        blockers.append("need_score_below_experimental_threshold")
    if complexity == "high":
        blockers.append("implementation_complexity_too_high_for_initial_promotion")
    if external_dependency_risk == "high":
        blockers.append("external_dependency_risk_high")

    valid_states = set(lifecycle_rules.get("states", DEFAULT_LIFECYCLE_RULES["states"]))
    if duplication_risk == "high":
        return (
            "reject_candidate",
            "rejected" if "rejected" in valid_states else "candidate",
            blockers,
        )
    if external_dependency_risk == "high" or complexity == "high":
        return (
            "watchlist_only",
            "candidate" if "candidate" in valid_states else "experimental",
            blockers,
        )
    if need_score >= 70 and reuse_potential == "high" and not blockers:
        return (
            "promote_to_experimental",
            "experimental" if "experimental" in valid_states else "candidate",
            [],
        )
    if need_score >= 45:
        return (
            "hold_as_candidate",
            "candidate" if "candidate" in valid_states else "experimental",
            blockers,
        )
    return (
        "reject_candidate",
        "rejected" if "rejected" in valid_states else "candidate",
        blockers,
    )


def _requires_human_approval(
    *,
    recommended_state: str,
    duplication_risk: str,
    external_dependency_risk: str,
    complexity: str,
    lifecycle_rules: Dict[str, Any],
) -> bool:
    approval_by_state = lifecycle_rules.get(
        "human_approval_required_by_state",
        DEFAULT_LIFECYCLE_RULES["human_approval_required_by_state"],
    )
    if bool(approval_by_state.get(recommended_state)):
        return True
    return duplication_risk == "high" or external_dependency_risk != "low" or complexity == "high"


def evaluate_skill_candidate(
    *,
    root: Path,
    candidate_name: str,
    problem_statement: str,
    project: Optional[Path] = None,
) -> Dict[str, Any]:
    root = root.resolve()
    project = project.resolve() if project is not None else None
    lifecycle_rules = _load_lifecycle_rules(root)
    intent = analyze_project_intent(project=project, brief=problem_statement if project is None else None)
    project_type = str(intent.get("project_type", "unknown")).strip() or "unknown"
    skills = _load_skill_catalog(root)
    overlaps = _match_existing_skills(candidate_name, problem_statement, skills)
    reuse_potential, reuse_evidence = _evaluate_reuse(problem_statement, project_type, overlaps)
    complexity, complexity_evidence = _evaluate_complexity(problem_statement)
    need_score, score_evidence = _evaluate_need_score(problem_statement, project_type, overlaps, reuse_potential, complexity)
    duplication_risk, duplication_evidence = _evaluate_duplication_risk(candidate_name, overlaps, problem_statement)
    external_dependency_risk, dependency_evidence = _evaluate_external_dependency_risk(problem_statement, lifecycle_rules)
    requires_decision_council, council_evidence = _requires_decision_council(
        duplication_risk=duplication_risk,
        external_dependency_risk=external_dependency_risk,
        complexity=complexity,
        need_score=need_score,
        lifecycle_rules=lifecycle_rules,
    )
    lifecycle_recommendation, recommended_state, promotion_blockers = _derive_lifecycle_outcome(
        need_score=need_score,
        reuse_potential=reuse_potential,
        complexity=complexity,
        duplication_risk=duplication_risk,
        external_dependency_risk=external_dependency_risk,
        lifecycle_rules=lifecycle_rules,
    )
    requires_human_approval = _requires_human_approval(
        recommended_state=recommended_state,
        duplication_risk=duplication_risk,
        external_dependency_risk=external_dependency_risk,
        complexity=complexity,
        lifecycle_rules=lifecycle_rules,
    )
    should_create = recommended_state in {"experimental", "stable"} and lifecycle_recommendation == "promote_to_experimental"

    reasoning: List[str] = []
    if overlaps:
        reasoning.append(
            "Atlas already has overlapping capability signals in: "
            + ", ".join(item["skill_id"] for item in overlaps)
            + "."
        )
    else:
        reasoning.append("No strong overlap with the current Atlas skill catalog was detected.")
    reasoning.append(f"Reuse potential is `{reuse_potential}` and implementation complexity is `{complexity}`.")
    if should_create:
        reasoning.append("The gap looks reusable enough to justify a dedicated skill instead of repeating the guidance ad hoc.")
    else:
        reasoning.append("The safer decision is to reuse existing skills or prompts until the need becomes more cross-project and durable.")
    reasoning.append(
        f"Lifecycle recommendation is `{lifecycle_recommendation}` toward state `{recommended_state}`"
        f" with duplication risk `{duplication_risk}` and external dependency risk `{external_dependency_risk}`."
    )
    if promotion_blockers:
        reasoning.append(f"Current promotion blockers: {', '.join(promotion_blockers)}.")
    if requires_decision_council:
        reasoning.append("Decision-council is recommended before promotion because the proposal changes Atlas surface under meaningful uncertainty.")

    overlap_ids = [item["skill_id"] for item in overlaps]
    why = (
        f"State `{recommended_state}` because reuse is `{reuse_potential}`, duplication risk is `{duplication_risk}`, "
        f"external dependency risk is `{external_dependency_risk}`, complexity is `{complexity}` and need score is {need_score}."
    )

    return {
        "status": "ok",
        "candidate_name": candidate_name,
        "project_path": str(project) if project is not None else None,
        "project_type": project_type,
        "need_score": need_score,
        "reuse_potential": reuse_potential,
        "complexity": complexity,
        "should_create": should_create,
        "overlapping_skills": overlap_ids,
        "lifecycle_recommendation": lifecycle_recommendation,
        "recommended_state": recommended_state,
        "promotion_blockers": promotion_blockers,
        "duplication_risk": duplication_risk,
        "external_dependency_risk": external_dependency_risk,
        "requires_human_approval": requires_human_approval,
        "requires_decision_council": requires_decision_council,
        "why": why,
        "reasoning": reasoning,
        "evidence": [
            *reuse_evidence,
            *complexity_evidence,
            *score_evidence,
            *duplication_evidence,
            *dependency_evidence,
            *council_evidence,
        ][:12],
        "timestamp": _utc_now_iso(),
    }


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(add_help=True)
    parser.add_argument("--root", default=None, help="Atlas root to use. Defaults to this repository root.")
    parser.add_argument("--project", default=None, help="Derived project path to use as context.")
    parser.add_argument("--candidate", required=True, help="Candidate skill name to evaluate.")
    parser.add_argument("--problem", required=True, help="Problem statement the new skill would solve.")
    args = parser.parse_args(argv)

    root = Path(args.root).resolve() if args.root else DEFAULT_ROOT
    project = Path(args.project).resolve() if args.project else None
    result = evaluate_skill_candidate(
        root=root,
        candidate_name=args.candidate,
        problem_statement=args.problem,
        project=project,
    )
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
