from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Dict, List, Optional


DEFAULT_ROOT = Path(__file__).resolve().parents[1]
RULES_PATH = Path("config/post_execution_learning_rules.json")


def load_post_execution_learning_rules(root: Path = DEFAULT_ROOT) -> Dict[str, Any]:
    return json.loads((root / RULES_PATH).read_text(encoding="utf-8-sig"))


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


def _listify(value: Any) -> List[str]:
    if isinstance(value, list):
        return [str(item).strip() for item in value if str(item).strip()]
    if isinstance(value, tuple):
        return [str(item).strip() for item in value if str(item).strip()]
    text = _stringify(value)
    return [text] if text else []


def _has_value(value: Any) -> bool:
    if value is None:
        return False
    if isinstance(value, str):
        return bool(value.strip())
    if isinstance(value, (list, tuple, set, dict)):
        return bool(value)
    return True


def _extract_inputs(payload: Dict[str, Any], rules: Dict[str, Any]) -> Dict[str, Any]:
    aliases = rules.get("input_aliases", {})
    extracted: Dict[str, Any] = {}
    for canonical in aliases:
        candidates = [canonical, *list(aliases.get(canonical, []))]
        for name in candidates:
            value = payload.get(name)
            if _has_value(value):
                extracted[canonical] = value
                break
    return extracted


def _contains_any(surface: str, terms: List[str]) -> List[str]:
    normalized_surface = _normalize(surface)
    return [term for term in terms if _normalize(term) and _normalize(term) in normalized_surface]


def _has_test_validation(validations_run: List[str], rules: Dict[str, Any]) -> bool:
    joined = " ".join(validations_run)
    return bool(_contains_any(joined, list(rules.get("test_validation_terms", []))))


def review_post_execution_learning(
    payload: Dict[str, Any],
    *,
    root: Path = DEFAULT_ROOT,
    project: Optional[Path] = None,
) -> Dict[str, Any]:
    del project
    root = root.resolve()
    rules = load_post_execution_learning_rules(root)
    extracted = _extract_inputs(payload, rules)

    task_summary = _stringify(extracted.get("task_summary"))
    files_changed = _listify(extracted.get("files_changed"))
    validations_run = _listify(extracted.get("validations_run"))
    blocked_reasons = _listify(extracted.get("blocked_reasons"))
    user_feedback = _stringify(extracted.get("user_feedback"))
    repeated_error_patterns = _listify(extracted.get("repeated_error_patterns"))
    missing_evidence = _listify(extracted.get("missing_evidence"))
    rollback_needed = bool(extracted.get("rollback_needed"))
    bug_fixed = bool(extracted.get("bug_fixed"))
    attempts_auto_mutation = bool(extracted.get("attempts_auto_mutation"))
    feature_scope = _normalize(extracted.get("feature_scope") or payload.get("feature_scope") or "normal")

    surface = " ".join(
        part
        for part in [
            task_summary,
            " ".join(files_changed),
            " ".join(validations_run),
            " ".join(blocked_reasons),
            user_feedback,
            " ".join(repeated_error_patterns),
            " ".join(missing_evidence),
            feature_scope,
        ]
        if part
    )

    repeated_patterns: List[str] = []
    learning_candidates: List[str] = []
    recommended_policy_changes: List[str] = []
    recommended_tests: List[str] = []
    recommended_readiness_layers: List[str] = []
    blocked_reasons_out: List[str] = []

    auto_mutation_hits = _contains_any(surface, list(rules.get("auto_mutation_terms", [])))
    dangerous_hits = _contains_any(surface, list(rules.get("dangerous_behavior_terms", [])))
    external_hits = _contains_any(surface, list(rules.get("external_integration_terms", [])))
    frontend_generic_hits = _contains_any(surface, list(rules.get("frontend_generic_repeat_terms", [])))
    readiness_hits = _contains_any(surface, list(rules.get("readiness_candidate_terms", [])))
    policy_hits = _contains_any(surface, list(rules.get("policy_candidate_terms", [])))

    if auto_mutation_hits or attempts_auto_mutation:
        blocked_reasons_out.append("auto_mutation_blocked")
        if auto_mutation_hits:
            repeated_patterns.extend(auto_mutation_hits)
        state = "blocked_auto_mutation"
        learning_disposition = "rejected"
    else:
        has_test_file = any(path.replace("\\", "/").startswith("tests/") for path in files_changed)
        has_test_validation = _has_test_validation(validations_run, rules)

        if frontend_generic_hits or repeated_error_patterns:
            repeated_patterns.extend(frontend_generic_hits)
            repeated_patterns.extend(repeated_error_patterns)
            learning_candidates.append(
                "Capture the repeated frontend/quality drift as a reusable Atlas lesson instead of leaving it in chat memory."
            )

        if dangerous_hits or policy_hits:
            recommended_policy_changes.append(
                "Review whether a tighter guardrail or approval policy should be added for the risky behavior observed."
            )

        if bug_fixed and not has_test_file and not has_test_validation:
            recommended_tests.append(
                "Add focused regression coverage for the corrected bug before calling the learning durable."
            )

        if external_hits or readiness_hits or feature_scope == "external_surface":
            recommended_readiness_layers.append(
                "Frame the new external/runtime surface as readiness first before any executable integration."
            )

        if rollback_needed and not dangerous_hits:
            learning_candidates.append(
                "Document rollback expectations earlier when the task introduces reversible risk."
            )

        if missing_evidence:
            learning_candidates.append(
                "Strengthen evidence collection earlier in the block so closure is not based on conversation alone."
            )

        if recommended_policy_changes:
            state = "policy_candidate"
            learning_disposition = "deferred"
        elif recommended_tests:
            state = "test_candidate"
            learning_disposition = "deferred"
        elif recommended_readiness_layers:
            state = "readiness_candidate"
            learning_disposition = "deferred"
        elif repeated_patterns or learning_candidates:
            state = "learning_candidate"
            learning_disposition = "accepted"
        elif user_feedback or blocked_reasons or missing_evidence:
            state = "needs_human_review"
            learning_disposition = "deferred"
        else:
            state = "no_learning_needed"
            learning_disposition = "accepted"

    recommended_next_steps = [
        str((rules.get("next_safe_steps") or {}).get(state, "")).strip()
    ]
    if recommended_policy_changes:
        recommended_next_steps.append("Treat any policy change as a separate human-approved block.")
    if recommended_tests:
        recommended_next_steps.append("Treat missing regression coverage as a separate test-focused follow-up.")
    if recommended_readiness_layers:
        recommended_next_steps.append("Prefer a readiness posture over a runtime feature when the surface is external.")

    return {
        "status": "ok",
        "post_execution_learning_posture": {
            "state": state,
            "learning_disposition": learning_disposition,
            "repeated_patterns": list(dict.fromkeys(item for item in repeated_patterns if item)),
            "learning_candidates": list(dict.fromkeys(item for item in learning_candidates if item)),
            "recommended_policy_changes": list(dict.fromkeys(item for item in recommended_policy_changes if item)),
            "recommended_tests": list(dict.fromkeys(item for item in recommended_tests if item)),
            "recommended_readiness_layers": list(
                dict.fromkeys(item for item in recommended_readiness_layers if item)
            ),
            "blocked_reasons": list(dict.fromkeys(item for item in blocked_reasons_out if item)),
            "requires_human_approval": True,
            "auto_mutation_allowed": False,
            "recommended_next_steps": list(dict.fromkeys(item for item in recommended_next_steps if item)),
            "advisory_only": bool(rules.get("advisory_only", True)),
        },
        "advisory_only": bool(rules.get("advisory_only", True)),
    }


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(add_help=True)
    parser.add_argument("--payload-json", default=None)
    args = parser.parse_args(argv)

    payload: Dict[str, Any] = {}
    if args.payload_json:
        payload.update(json.loads(args.payload_json))

    result = review_post_execution_learning(payload, root=DEFAULT_ROOT)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
