from __future__ import annotations

import argparse
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Sequence, Set, Tuple

try:
    from tools.skill_evaluator import evaluate_skill_candidate
except ModuleNotFoundError:
    from skill_evaluator import evaluate_skill_candidate


DEFAULT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_RULES = {
    "version": "1.0",
    "advisory_only": True,
    "scoring_rules": {
        "base_score": 100,
        "missing_tests_penalty": 25,
        "missing_docs_penalty": 20,
        "missing_behavior_penalty": 15,
        "missing_skill_json_penalty": 15,
        "duplicate_penalty_medium": 20,
        "duplicate_penalty_high": 40,
        "external_dependency_penalty_medium": 10,
        "external_dependency_penalty_high": 25,
        "stale_state_penalty": 10,
        "minimum_score_for_keep": 80,
        "minimum_score_for_improve": 55,
    },
    "recommendation_types": [
        "keep",
        "improve",
        "merge",
        "split",
        "deprecate",
        "archive",
        "reject",
        "candidate_review",
        "decision_council_required",
    ],
    "external_dependency_signals": {
        "high_terms": [
            "mcp",
            "playwright",
            "install",
            "sync",
            "runtime",
            "autonomous",
            "self-heal",
            "browser automation",
            "secret",
            "provider token",
        ],
        "medium_terms": [
            "api",
            "sdk",
            "external service",
            "github",
            "vercel",
            "remote docs",
        ],
    },
}
DOCUMENTATION_HEADINGS = ("## When to use", "## Steps", "## Inputs", "## Outputs", "## Validation")
ACTIVE_STATES = {"candidate", "experimental", "stable", "deprecated", "archived", "rejected"}


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _read_json(path: Path) -> Dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def _read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8-sig")


def _normalize(text: str) -> str:
    return re.sub(r"\s+", " ", str(text).lower()).strip()


def _tokenize(*parts: str) -> Set[str]:
    tokens: Set[str] = set()
    for part in parts:
        for token in re.findall(r"[a-z0-9]+", str(part).lower()):
            if len(token) >= 3:
                tokens.add(token)
    return tokens


def _load_rules(root: Path) -> Dict[str, Any]:
    path = root / "config" / "skill_improvement_review_rules.json"
    if not path.exists():
        return dict(DEFAULT_RULES)
    data = _read_json(path)
    if not isinstance(data, dict):
        return dict(DEFAULT_RULES)
    merged = dict(DEFAULT_RULES)
    merged.update(data)
    merged["scoring_rules"] = {
        **DEFAULT_RULES["scoring_rules"],
        **dict(data.get("scoring_rules", {})),
    }
    merged["external_dependency_signals"] = {
        **DEFAULT_RULES["external_dependency_signals"],
        **dict(data.get("external_dependency_signals", {})),
    }
    return merged


def _load_lifecycle_rules(root: Path) -> Dict[str, Any]:
    path = root / "config" / "skill_lifecycle_rules.json"
    if not path.exists():
        return {}
    data = _read_json(path)
    return data if isinstance(data, dict) else {}


def _skill_dirs(root: Path) -> Iterable[Path]:
    skills_dir = root / "skills"
    if not skills_dir.exists():
        return []
    return sorted(path for path in skills_dir.iterdir() if path.is_dir() and not path.name.startswith("_"))


def _test_files(root: Path) -> List[Path]:
    tests_dir = root / "tests"
    if not tests_dir.exists():
        return []
    files: List[Path] = []
    for path in sorted(tests_dir.glob("test_*.py")):
        try:
            if path.is_file():
                files.append(path)
        except OSError:
            continue
    return files


def _match_test_references(skill_id: str, test_files: Sequence[Path]) -> List[str]:
    variants = {
        skill_id,
        skill_id.replace("-", "_"),
        skill_id.replace("-", " "),
    }
    matched: List[str] = []
    for test_file in test_files:
        try:
            text = _read_text(test_file).lower()
        except OSError:
            continue
        if any(variant.lower() in text for variant in variants):
            matched.append(test_file.name)
    return matched


def _documentation_quality(skill_md_text: str) -> Tuple[bool, List[str]]:
    lowered = skill_md_text.lower()
    matched = [heading for heading in DOCUMENTATION_HEADINGS if heading.lower() in lowered]
    return len(matched) >= 2, matched


def _dependency_risk(text: str, rules: Dict[str, Any]) -> Tuple[str, List[str]]:
    normalized = _normalize(text)
    signals = rules.get("external_dependency_signals", {})
    high_terms = [str(term).strip().lower() for term in signals.get("high_terms", []) if str(term).strip()]
    medium_terms = [str(term).strip().lower() for term in signals.get("medium_terms", []) if str(term).strip()]

    high_hits = sorted({term for term in high_terms if term in normalized})
    if high_hits:
        return "high", [f"external_high_terms={high_hits}"]

    medium_hits = sorted({term for term in medium_terms if term in normalized})
    if medium_hits:
        return "medium", [f"external_medium_terms={medium_hits}"]

    return "low", ["external_dependency_signals=none"]


def _build_catalog(root: Path) -> List[Dict[str, Any]]:
    test_files = _test_files(root)
    catalog: List[Dict[str, Any]] = []
    for skill_dir in _skill_dirs(root):
        skill_id = skill_dir.name
        skill_md = skill_dir / "skill.md"
        skill_json = skill_dir / "skill.json"
        behavior_json = skill_dir / "behavior.json"

        skill_md_text = ""
        metadata: Dict[str, Any] = {}
        behavior: Dict[str, Any] = {}
        if skill_md.exists():
            try:
                skill_md_text = _read_text(skill_md)
            except OSError:
                skill_md_text = ""
        if skill_json.exists():
            try:
                metadata = _read_json(skill_json)
            except Exception:
                metadata = {}
        if behavior_json.exists():
            try:
                behavior = _read_json(behavior_json)
            except Exception:
                behavior = {}

        docs_quality_ok, matched_headings = _documentation_quality(skill_md_text)
        intent_keywords = [str(item).strip() for item in metadata.get("intent_keywords", []) if str(item).strip()]
        combined_surface = " ".join(
            [
                skill_id,
                str(metadata.get("name", "")),
                " ".join(intent_keywords),
                str(metadata.get("workflow", "")),
            ]
        )
        catalog.append(
            {
                "skill_id": skill_id,
                "name": str(metadata.get("name", "")).strip() or skill_id,
                "metadata": metadata,
                "behavior": behavior,
                "skill_dir": str(skill_dir),
                "has_skill_md": skill_md.exists(),
                "has_skill_json": skill_json.exists(),
                "has_behavior_json": behavior_json.exists(),
                "documentation_headings": matched_headings,
                "documentation_quality_ok": docs_quality_ok,
                "test_references": _match_test_references(skill_id, test_files),
                "intent_keywords": intent_keywords,
                "workflow": str(metadata.get("workflow", "")).strip(),
                "risk_level": str(metadata.get("risk_level", "low")).strip() or "low",
                "declared_state": str(metadata.get("lifecycle_state", "undeclared")).strip() or "undeclared",
                "supports_execution": bool(metadata.get("supports_execution", False)),
                "surface_text": combined_surface,
                "tokens": _tokenize(skill_id, str(metadata.get("name", "")), " ".join(intent_keywords)),
            }
        )
    return catalog


def _overlap_details(a: Dict[str, Any], b: Dict[str, Any]) -> Tuple[str, List[str]]:
    reasons: List[str] = []
    a_tokens = set(a.get("tokens", set()))
    b_tokens = set(b.get("tokens", set()))
    shared = sorted(a_tokens & b_tokens)
    union = a_tokens | b_tokens
    similarity = (len(shared) / len(union)) if union else 0.0

    if _normalize(a["name"]) == _normalize(b["name"]) or a["skill_id"] == b["skill_id"]:
        reasons.append("same_or_near_identical_name")
    if similarity >= 0.5 and shared:
        reasons.append("high_keyword_overlap")
    elif similarity >= 0.3 and shared:
        reasons.append("partial_keyword_overlap")
    if a.get("workflow") and a.get("workflow") == b.get("workflow") and similarity >= 0.3:
        reasons.append("same_workflow_same_audience")

    if "same_or_near_identical_name" in reasons or (
        "high_keyword_overlap" in reasons and "same_workflow_same_audience" in reasons
    ):
        return "high", reasons + [f"shared_tokens={shared[:6]}"]
    if reasons:
        return "medium", reasons + [f"shared_tokens={shared[:6]}"]
    return "low", []


def _duplicate_map(catalog: Sequence[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
    duplicates: Dict[str, List[Dict[str, Any]]] = {item["skill_id"]: [] for item in catalog}
    for index, left in enumerate(catalog):
        for right in catalog[index + 1 :]:
            risk, reasons = _overlap_details(left, right)
            if risk == "low":
                continue
            duplicates[left["skill_id"]].append({"skill_id": right["skill_id"], "risk": risk, "reasons": reasons})
            duplicates[right["skill_id"]].append({"skill_id": left["skill_id"], "risk": risk, "reasons": reasons})
    return duplicates


def _recommend_for_skill(
    skill: Dict[str, Any],
    duplicates: List[Dict[str, Any]],
    rules: Dict[str, Any],
) -> Dict[str, Any]:
    scoring = rules.get("scoring_rules", {})
    score = int(scoring.get("base_score", 100))
    missing_docs: List[str] = []
    missing_tests: List[str] = []
    weak_fields: List[str] = []
    stale_signals: List[str] = []

    if not skill.get("has_skill_md"):
        score -= int(scoring.get("missing_docs_penalty", 20))
        missing_docs.append("missing_skill_md")
    if not skill.get("has_skill_json"):
        score -= int(scoring.get("missing_skill_json_penalty", 15))
        missing_docs.append("missing_skill_json")
    if skill.get("has_skill_md") and not skill.get("documentation_quality_ok"):
        score -= int(scoring.get("missing_docs_penalty", 20))
        weak_fields.append("insufficient_documentation_headings")
    if not skill.get("has_behavior_json"):
        score -= int(scoring.get("missing_behavior_penalty", 15))
        weak_fields.append("missing_behavior")
    if not skill.get("test_references"):
        score -= int(scoring.get("missing_tests_penalty", 25))
        missing_tests.append("no_skill_specific_test_reference")

    declared_state = str(skill.get("declared_state", "undeclared")).strip()
    if declared_state in {"deprecated", "archived"}:
        stale_signals.append(f"declared_{declared_state}")
        score -= int(scoring.get("stale_state_penalty", 10))

    highest_duplicate = "low"
    overlap_ids: List[str] = []
    duplicate_reasons: List[str] = []
    for item in duplicates:
        overlap_ids.append(str(item.get("skill_id", "")))
        duplicate_reasons.extend([str(reason) for reason in item.get("reasons", []) if reason])
        if item.get("risk") == "high":
            highest_duplicate = "high"
        elif highest_duplicate != "high":
            highest_duplicate = "medium"

    if highest_duplicate == "high":
        score -= int(scoring.get("duplicate_penalty_high", 40))
    elif highest_duplicate == "medium":
        score -= int(scoring.get("duplicate_penalty_medium", 20))

    dependency_risk, dependency_evidence = _dependency_risk(str(skill.get("surface_text", "")), rules)
    if dependency_risk == "high":
        score -= int(scoring.get("external_dependency_penalty_high", 25))
    elif dependency_risk == "medium":
        score -= int(scoring.get("external_dependency_penalty_medium", 10))

    score = max(0, min(score, 100))
    minimum_keep = int(scoring.get("minimum_score_for_keep", 80))
    minimum_improve = int(scoring.get("minimum_score_for_improve", 55))

    requires_decision_council = highest_duplicate == "high" and score >= minimum_improve
    requires_human_approval = False

    if declared_state == "archived":
        recommendation = "archive"
        recommended_state = "archived"
        requires_human_approval = True
    elif highest_duplicate == "high":
        recommendation = "deprecate"
        recommended_state = "deprecated"
        requires_human_approval = True
    elif score >= minimum_keep and not missing_docs and not missing_tests and dependency_risk == "low":
        recommendation = "keep"
        recommended_state = "stable"
    elif score >= minimum_improve:
        recommendation = "improve"
        recommended_state = "experimental" if declared_state == "undeclared" else declared_state
        requires_human_approval = recommendation != "keep" and bool(overlap_ids)
    else:
        recommendation = "improve"
        recommended_state = "experimental"

    why_parts = [
        f"score={score}",
        f"duplication_risk={highest_duplicate}",
        f"dependency_risk={dependency_risk}",
    ]
    if missing_docs:
        why_parts.append(f"missing_docs={missing_docs}")
    if missing_tests:
        why_parts.append(f"missing_tests={missing_tests}")
    if weak_fields:
        why_parts.append(f"weak_fields={weak_fields}")

    return {
        "skill_id": skill["skill_id"],
        "declared_state": declared_state,
        "recommended_state": recommended_state,
        "recommendation": recommendation,
        "score": score,
        "missing_docs": missing_docs,
        "missing_tests": missing_tests,
        "weak_fields": weak_fields,
        "stale_signals": stale_signals,
        "duplicate_risk": highest_duplicate,
        "overlapping_skills": sorted(set(overlap_ids)),
        "duplicate_reasons": sorted(set(duplicate_reasons)),
        "external_dependency_risk": dependency_risk,
        "external_dependency_evidence": dependency_evidence,
        "requires_human_approval": requires_human_approval,
        "requires_decision_council": requires_decision_council,
        "why": "; ".join(why_parts),
    }


def _review_external_candidates(
    root: Path,
    external_candidates: Optional[Sequence[Dict[str, Any]]],
) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]], bool, bool]:
    opportunities: List[Dict[str, Any]] = []
    blocked: List[Dict[str, Any]] = []
    requires_human_approval = False
    requires_decision_council = False

    for candidate in list(external_candidates or []):
        candidate_name = str(candidate.get("candidate_name", "")).strip()
        problem_statement = str(candidate.get("problem_statement", "")).strip()
        source = str(candidate.get("source", "")).strip() or "external_candidate"

        if not candidate_name or not problem_statement:
            blocked.append(
                {
                    "source": source,
                    "candidate_name": candidate_name or "unknown_candidate",
                    "recommendation": "reject",
                    "reason": "candidate_name_and_problem_statement_required",
                }
            )
            continue

        evaluation = evaluate_skill_candidate(
            root=root,
            candidate_name=candidate_name,
            problem_statement=problem_statement,
            project=None,
        )
        entry = {
            "source": source,
            "candidate_name": candidate_name,
            "recommended_state": evaluation.get("recommended_state"),
            "lifecycle_recommendation": evaluation.get("lifecycle_recommendation"),
            "duplication_risk": evaluation.get("duplication_risk"),
            "external_dependency_risk": evaluation.get("external_dependency_risk"),
            "requires_human_approval": bool(evaluation.get("requires_human_approval")),
            "requires_decision_council": bool(evaluation.get("requires_decision_council")),
            "why": evaluation.get("why"),
        }
        atlas_fit_decision, atlas_fit_reason = _atlas_fit_decision(candidate, evaluation)
        entry["atlas_fit_decision"] = atlas_fit_decision
        entry["atlas_fit_reason"] = atlas_fit_reason
        requires_human_approval = requires_human_approval or bool(entry["requires_human_approval"])
        requires_decision_council = requires_decision_council or bool(entry["requires_decision_council"])

        if atlas_fit_decision == "discard":
            entry["recommendation"] = "reject"
            blocked.append(entry)
        elif entry["requires_decision_council"] or atlas_fit_decision == "watchlist":
            entry["recommendation"] = "decision_council_required"
            blocked.append(entry)
        elif atlas_fit_decision == "adapt_now" or entry["lifecycle_recommendation"] == "promote_to_experimental":
            entry["recommendation"] = "candidate_review"
            opportunities.append(entry)
        elif atlas_fit_decision == "design_later" or entry["lifecycle_recommendation"] == "hold_as_candidate":
            entry["recommendation"] = "candidate_review"
            opportunities.append(entry)
        else:
            entry["recommendation"] = "reject"
            blocked.append(entry)

    return opportunities, blocked, requires_human_approval, requires_decision_council


def _atlas_fit_decision(candidate: Dict[str, Any], evaluation: Dict[str, Any]) -> Tuple[str, str]:
    claude_only = bool(candidate.get("claude_only"))
    requires_runtime = bool(candidate.get("requires_runtime"))
    requires_secrets = bool(candidate.get("requires_secrets"))
    duplication_risk = str(evaluation.get("duplication_risk", "low")).strip()
    dependency_risk = str(evaluation.get("external_dependency_risk", "low")).strip()
    lifecycle = str(evaluation.get("lifecycle_recommendation", "")).strip()

    if claude_only:
        return "discard", "candidate_is_claude_only_or_runtime_locked"
    if duplication_risk == "high":
        return "discard", "candidate_overlaps_existing_atlas_capability"
    if requires_runtime or requires_secrets or dependency_risk == "high" or bool(evaluation.get("requires_decision_council")):
        return "watchlist", "candidate_requires_runtime_or_secret_surface"
    if lifecycle == "promote_to_experimental" and not bool(evaluation.get("requires_human_approval")):
        return "adapt_now", "candidate_fits_atlas_without_new_runtime_surface"
    if lifecycle in {"promote_to_experimental", "hold_as_candidate"}:
        return "design_later", "candidate_has_potential_but_needs_human_review"
    return "discard", "candidate_does_not_improve_atlas_enough"


def _build_next_actions(
    weak_skills: Sequence[Dict[str, Any]],
    duplicate_risks: Sequence[Dict[str, Any]],
    candidate_opportunities: Sequence[Dict[str, Any]],
    blocked_candidates: Sequence[Dict[str, Any]],
) -> List[str]:
    actions: List[str] = []
    if weak_skills:
        first = weak_skills[0]
        if first.get("missing_tests") or first.get("missing_docs"):
            actions.append(
                f"Review `{first['skill_id']}` and close the highest-priority missing tests/docs gap before adding new skills."
            )
        elif first.get("duplicate_risk") != "low":
            actions.append(
                f"Review `{first['skill_id']}` for overlap and decide whether it should merge with an adjacent Atlas skill."
            )
        elif first.get("external_dependency_risk") == "high":
            actions.append(
                f"Review whether `{first['skill_id']}` still belongs in Atlas core or should keep a more explicit boundary due to external/runtime signals."
            )
        else:
            actions.append(
                f"Review `{first['skill_id']}` and tighten its weakest catalog-health signal before adding new skills."
            )
    if duplicate_risks:
        pair = duplicate_risks[0]
        actions.append(f"Compare `{pair['skill_id']}` against `{pair['overlapping_with']}` and decide whether Atlas should merge or deprecate one path.")
    if candidate_opportunities:
        candidate = candidate_opportunities[0]
        actions.append(f"Review external candidate `{candidate['candidate_name']}` manually before adding any new skill surface.")
    if blocked_candidates:
        blocked = blocked_candidates[0]
        actions.append(f"Do not advance `{blocked['candidate_name']}` until the blocking risk is clarified explicitly.")
    return actions[:3]


def review_skill_catalog(
    *,
    root: Path,
    external_candidates: Optional[Sequence[Dict[str, Any]]] = None,
) -> Dict[str, Any]:
    root = root.resolve()
    rules = _load_rules(root)
    lifecycle_rules = _load_lifecycle_rules(root)
    catalog = _build_catalog(root)
    duplicate_map = _duplicate_map(catalog)

    reviewed_skills: List[Dict[str, Any]] = []
    weak_skills: List[Dict[str, Any]] = []
    duplicate_risks: List[Dict[str, Any]] = []
    lifecycle_recommendations: List[Dict[str, Any]] = []
    requires_human_approval = False
    requires_decision_council = False

    for skill in catalog:
        review = _recommend_for_skill(skill, duplicate_map.get(skill["skill_id"], []), rules)
        reviewed_skills.append(review)
        lifecycle_recommendations.append(
            {
                "skill_id": review["skill_id"],
                "declared_state": review["declared_state"],
                "recommended_state": review["recommended_state"],
                "recommendation": review["recommendation"],
                "why": review["why"],
            }
        )
        if review["recommendation"] != "keep" or review["missing_docs"] or review["missing_tests"] or review["weak_fields"]:
            weak_skills.append(review)
        if review["duplicate_risk"] != "low":
            for overlap in review["overlapping_skills"]:
                duplicate_risks.append(
                    {
                        "skill_id": review["skill_id"],
                        "overlapping_with": overlap,
                        "risk": review["duplicate_risk"],
                        "reasons": review["duplicate_reasons"],
                    }
                )
        requires_human_approval = requires_human_approval or bool(review["requires_human_approval"])
        requires_decision_council = requires_decision_council or bool(review["requires_decision_council"])

    candidate_opportunities, blocked_candidates, candidate_requires_human, candidate_requires_council = _review_external_candidates(
        root,
        external_candidates,
    )
    requires_human_approval = requires_human_approval or candidate_requires_human
    requires_decision_council = requires_decision_council or candidate_requires_council

    weak_skills.sort(key=lambda item: item["score"])
    duplicate_risks.sort(key=lambda item: (0 if item["risk"] == "high" else 1, item["skill_id"], item["overlapping_with"]))
    reviewed_skills.sort(key=lambda item: (item["recommendation"] != "keep", item["score"], item["skill_id"]))

    status = "ok"
    if weak_skills or blocked_candidates:
        status = "needs_attention"

    next_actions = _build_next_actions(weak_skills, duplicate_risks, candidate_opportunities, blocked_candidates)
    why = (
        f"Reviewed {len(reviewed_skills)} Atlas skills with advisory rules, found {len(weak_skills)} weak skill signals, "
        f"{len(duplicate_risks)} duplicate-risk links and {len(candidate_opportunities)} candidate opportunities."
    )

    return {
        "status": status,
        "reviewed_skills": reviewed_skills,
        "weak_skills": weak_skills,
        "duplicate_risks": duplicate_risks,
        "lifecycle_recommendations": lifecycle_recommendations,
        "candidate_opportunities": candidate_opportunities,
        "blocked_candidates": blocked_candidates,
        "requires_human_approval": requires_human_approval,
        "requires_decision_council": requires_decision_council,
        "recommended_next_actions": next_actions,
        "why": why,
        "advisory_only": bool(rules.get("advisory_only", True)),
        "lifecycle_states": list(lifecycle_rules.get("states", [])),
        "timestamp": _utc_now_iso(),
    }


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(add_help=True)
    parser.add_argument("--root", default=None, help="Atlas root to use. Defaults to this repository root.")
    parser.add_argument(
        "--external-candidates",
        default=None,
        help="Optional JSON file with external candidate payloads.",
    )
    args = parser.parse_args(argv)

    root = Path(args.root).resolve() if args.root else DEFAULT_ROOT
    external_candidates: Optional[List[Dict[str, Any]]] = None
    if args.external_candidates:
        payload = _read_json(Path(args.external_candidates).resolve())
        if isinstance(payload, list):
            external_candidates = payload
        else:
            raise SystemExit("--external-candidates must point to a JSON array.")

    result = review_skill_catalog(root=root, external_candidates=external_candidates)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
