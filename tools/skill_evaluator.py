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


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _normalize(text: str) -> str:
    return re.sub(r"\s+", " ", text.lower()).strip()


def _read_json(path: Path) -> Dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8-sig"))


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


def _match_existing_skills(candidate_name: str, problem_statement: str, skills: List[Dict[str, Any]]) -> List[str]:
    normalized_name = _normalize(candidate_name)
    normalized_problem = _normalize(problem_statement)
    overlaps: List[str] = []
    for skill in skills:
        skill_name = str(skill.get("name", "")).strip().lower()
        skill_id = str(skill.get("id", "")).strip()
        keywords = list(skill.get("intent_keywords", []))
        signals = [skill_name, skill_id.lower(), *keywords]
        if any(signal and (signal in normalized_name or signal in normalized_problem) for signal in signals):
            overlaps.append(skill_id)
    return sorted(set(overlaps))


def _evaluate_reuse(problem_statement: str, project_type: str, overlaps: List[str]) -> Tuple[str, List[str]]:
    normalized = _normalize(problem_statement)
    evidence: List[str] = []
    reuse_hits = [term for term in REUSE_TERMS if term in normalized]
    if reuse_hits:
        evidence.append(f"reuse_terms={reuse_hits}")
    if project_type in {"internal_tool", "frontend_app", "backend_service", "fullstack", "ai_agent_system"}:
        evidence.append(f"project_type={project_type}")
    if overlaps:
        evidence.append(f"overlap={overlaps}")
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


def _evaluate_need_score(problem_statement: str, project_type: str, overlaps: List[str], reuse_potential: str, complexity: str) -> Tuple[int, List[str]]:
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
        evidence.append(f"existing_skill_overlap={overlaps}")

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


def evaluate_skill_candidate(
    *,
    root: Path,
    candidate_name: str,
    problem_statement: str,
    project: Optional[Path] = None,
) -> Dict[str, Any]:
    root = root.resolve()
    project = project.resolve() if project is not None else None
    intent = analyze_project_intent(project=project, brief=problem_statement if project is None else None)
    project_type = str(intent.get("project_type", "unknown")).strip() or "unknown"
    skills = _load_skill_catalog(root)
    overlaps = _match_existing_skills(candidate_name, problem_statement, skills)
    reuse_potential, reuse_evidence = _evaluate_reuse(problem_statement, project_type, overlaps)
    complexity, complexity_evidence = _evaluate_complexity(problem_statement)
    need_score, score_evidence = _evaluate_need_score(problem_statement, project_type, overlaps, reuse_potential, complexity)
    should_create = need_score >= 70 and reuse_potential == "high" and complexity != "high" and not overlaps

    reasoning: List[str] = []
    if overlaps:
        reasoning.append(f"Atlas already has overlapping capability signals in: {', '.join(overlaps)}.")
    else:
        reasoning.append("No strong overlap with the current Atlas skill catalog was detected.")
    reasoning.append(f"Reuse potential is `{reuse_potential}` and implementation complexity is `{complexity}`.")
    if should_create:
        reasoning.append("The gap looks reusable enough to justify a dedicated skill instead of repeating the guidance ad hoc.")
    else:
        reasoning.append("The safer decision is to reuse existing skills or prompts until the need becomes more cross-project and durable.")

    return {
        "status": "ok",
        "candidate_name": candidate_name,
        "project_path": str(project) if project is not None else None,
        "project_type": project_type,
        "need_score": need_score,
        "reuse_potential": reuse_potential,
        "complexity": complexity,
        "should_create": should_create,
        "overlapping_skills": overlaps,
        "reasoning": reasoning,
        "evidence": [
            *reuse_evidence,
            *complexity_evidence,
            *score_evidence,
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
