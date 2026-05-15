from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any, Dict, List, Optional

try:
    from tools.project_intent_analyzer import analyze_project_intent
except ModuleNotFoundError:
    from project_intent_analyzer import analyze_project_intent


DEFAULT_ROOT = Path(__file__).resolve().parents[1]
RULES_PATH = Path("config/intent_clarifier_contract_rules.json")


def load_intent_clarifier_rules(root: Path = DEFAULT_ROOT) -> Dict[str, Any]:
    return json.loads((root / RULES_PATH).read_text(encoding="utf-8-sig"))


def _normalize(value: str) -> str:
    return re.sub(r"\s+", " ", str(value or "").strip().lower())


def _dedupe_preserve_order(values: List[str]) -> List[str]:
    seen: set[str] = set()
    deduped: List[str] = []
    for value in values:
        normalized = _normalize(value)
        if not normalized or normalized in seen:
            continue
        seen.add(normalized)
        deduped.append(str(value).strip())
    return deduped


def _contains_any(text: str, patterns: List[str]) -> bool:
    normalized = _normalize(text)
    return any(_normalize(pattern) in normalized for pattern in patterns)


def _infer_domain_context(
    source_text: str,
    domain_signals: Dict[str, List[str]],
) -> Optional[str]:
    normalized = _normalize(source_text)
    for label, terms in domain_signals.items():
        if any(_normalize(term) in normalized for term in terms):
            return label
    return None


def _infer_constraints(source_text: str) -> List[str]:
    normalized = _normalize(source_text)
    constraints: List[str] = []
    for term in ("no deploy", "read-only", "no mcp", "no backend", "manual", "advisory"):
        if term in normalized:
            constraints.append(term)
    return constraints


def _requires_intent_clarifier(project_type: str, rules: Dict[str, Any], source_text: str) -> bool:
    if project_type in set(rules.get("backend_exempt_project_types", [])):
        return False
    if project_type in set(rules.get("required_for_project_types", [])):
        return True
    normalized = _normalize(source_text)
    return any(term in normalized for term in ("landing", "dashboard", "ui", "website", "homepage", "workflow"))


def assess_intent_clarifier_contract(
    *,
    project: Optional[Path] = None,
    brief: Optional[str] = None,
    payload: Optional[Dict[str, Any]] = None,
    root: Path = DEFAULT_ROOT,
) -> Dict[str, Any]:
    rules = load_intent_clarifier_rules(root)
    payload = payload or {}

    intent_report = analyze_project_intent(project=project, brief=brief) if project is not None or brief else {}
    visual_review = payload.get("visual_intent_contract") or intent_report.get("visual_intent_contract") or {}
    contract_data = visual_review.get("contract") if isinstance(visual_review, dict) else {}
    if not isinstance(contract_data, dict):
        contract_data = {}

    project_type = str(payload.get("project_type") or intent_report.get("project_type") or contract_data.get("project_type") or "").strip()
    primary_goal = str(payload.get("primary_goal") or intent_report.get("objective") or "").strip() or None
    style_direction = str(payload.get("style_direction") or contract_data.get("mood_or_vibe") or "").strip() or None
    originality_level = str(payload.get("originality_level") or contract_data.get("originality_level") or "").strip() or None
    target_audience = str(payload.get("target_audience") or contract_data.get("audience") or "").strip() or None
    source_text = "\n".join(
        [
            str(brief or ""),
            str(primary_goal or ""),
            json.dumps(payload, ensure_ascii=False),
            json.dumps(contract_data, ensure_ascii=False),
        ]
    )
    domain_context = str(payload.get("domain_context") or "").strip() or _infer_domain_context(
        source_text,
        {key: list(value) for key, value in (rules.get("domain_signals") or {}).items()},
    )
    reference_direction = str(payload.get("reference_direction") or "").strip() or None
    success_criteria = str(payload.get("success_criteria") or "").strip() or None
    constraints = payload.get("constraints")
    if not isinstance(constraints, list):
        constraints = _infer_constraints(source_text)
    constraints = [str(item).strip() for item in constraints if str(item).strip()]

    contract = {
        "project_type": project_type or None,
        "domain_context": domain_context,
        "target_audience": target_audience,
        "primary_goal": primary_goal,
        "style_direction": style_direction,
        "originality_level": originality_level,
        "reference_direction": reference_direction,
        "success_criteria": success_criteria,
        "constraints": constraints,
    }

    if not _requires_intent_clarifier(project_type, rules, source_text):
        return {
            "status": "skipped",
            "requires_contract": False,
            "required_questions": list(rules.get("required_fields", [])),
            "answered_questions": [],
            "missing_questions": [],
            "weak_answers": [],
            "must_block_strong_ready": False,
            "requires_human_clarification": False,
            "next_action": "No intent clarifier contract is required for the current project type.",
            "why": "This project does not currently look like a UI-facing or workflow-facing surface that needs an intent clarifier contract.",
            "contract": contract,
            "advisory_only": bool(rules.get("advisory_only", True)),
        }

    required_questions = list(rules.get("required_fields", []))
    if project_type in set(rules.get("required_for_project_types", [])):
        required_questions.extend(list(rules.get("ui_required_fields", [])))
    required_questions = _dedupe_preserve_order(required_questions)

    answered_questions = [field for field in required_questions if contract.get(field)]
    missing_questions = [field for field in required_questions if field not in answered_questions]
    weak_answers: List[str] = []
    for field_name in [*required_questions, *list(rules.get("recommended_fields", []))]:
        value = contract.get(field_name)
        if not value or isinstance(value, list):
            continue
        if _contains_any(str(value), list(rules.get("weak_answer_patterns", []))):
            weak_answers.append(field_name)

    explicit_answer_count = sum(1 for field in required_questions if contract.get(field))
    inferred_fields = [
        field
        for field in ("domain_context", "target_audience", "style_direction", "originality_level")
        if contract.get(field) and not payload.get(field)
    ]
    triggers: List[str] = []
    if not project_type:
        triggers.append("project_type_unknown")
    if not target_audience:
        triggers.append("missing_target_audience")
    if not primary_goal:
        triggers.append("missing_primary_goal")
    if project_type in set(rules.get("required_for_project_types", [])) and not style_direction:
        triggers.append("missing_style_direction")
    if project_type in set(rules.get("required_for_project_types", [])) and not originality_level:
        triggers.append("missing_originality_level")
    if inferred_fields and explicit_answer_count < len(required_questions):
        triggers.append("mostly_inferred_contract")

    status = "ready" if not missing_questions and not weak_answers and explicit_answer_count >= int(rules.get("minimum_ready_fields", 1)) else "needs_input"
    requires_human_clarification = bool(triggers or missing_questions or weak_answers)

    why_parts = [
        f"Atlas requires explicit intent answers for UI-facing work before stronger design-readiness claims.",
        f"Answered {explicit_answer_count}/{len(required_questions)} required questions.",
    ]
    if missing_questions:
        why_parts.append(f"Missing: {', '.join(missing_questions[:5])}.")
    if weak_answers:
        why_parts.append(f"Weak: {', '.join(weak_answers[:5])}.")

    return {
        "status": status,
        "requires_contract": True,
        "required_questions": required_questions,
        "answered_questions": answered_questions,
        "missing_questions": missing_questions,
        "weak_answers": weak_answers,
        "must_block_strong_ready": status != "ready",
        "requires_human_clarification": requires_human_clarification,
        "approval_triggers": triggers,
        "next_action": "Fill the missing intent answers explicitly before treating the design direction as settled."
        if status != "ready"
        else "Intent clarifier answers are strong enough for the next visual guardrails.",
        "why": " ".join(why_parts),
        "contract": contract,
        "advisory_only": bool(rules.get("advisory_only", True)),
    }


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(add_help=True)
    parser.add_argument("--project", default=None)
    parser.add_argument("--brief", default=None)
    parser.add_argument("--payload-json", default=None)
    args = parser.parse_args(argv)

    payload = json.loads(args.payload_json) if args.payload_json else None
    project = Path(args.project).resolve() if args.project else None
    result = assess_intent_clarifier_contract(project=project, brief=args.brief, payload=payload, root=DEFAULT_ROOT)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
