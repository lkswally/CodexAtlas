from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Dict, List, Optional


DEFAULT_ROOT = Path(__file__).resolve().parents[1]
RULES_PATH = Path("config/evidence_collector_readiness_rules.json")


def load_evidence_collector_readiness_rules(root: Path = DEFAULT_ROOT) -> Dict[str, Any]:
    return json.loads((root / RULES_PATH).read_text(encoding="utf-8-sig"))


def _normalize_list(items: Any) -> List[str]:
    if not isinstance(items, list):
        return []
    normalized: List[str] = []
    for item in items:
        value = str(item).strip()
        if value and value not in normalized:
            normalized.append(value)
    return normalized


def _infer_task_type(payload: Dict[str, Any], rules: Dict[str, Any]) -> str:
    explicit = str(payload.get("task_type", "")).strip()
    if explicit:
        return explicit

    project_type = str(payload.get("project_type", "")).strip()
    mapped = (rules.get("project_type_map") or {}).get(project_type)
    if isinstance(mapped, str) and mapped.strip():
        return mapped.strip()

    if bool(payload.get("requires_decision_council")) or str(payload.get("risk_level", "")).strip() == "high":
        return "high_risk_decision"

    if bool(payload.get("is_skill_change")) or bool(payload.get("is_governance_change")):
        return "skill_governance_change"

    if payload.get("sources") or payload.get("selection_criteria") or payload.get("research_mode"):
        return "research_benchmark"

    return "not_applicable"


def review_evidence_collector_readiness(
    payload: Dict[str, Any],
    *,
    root: Path = DEFAULT_ROOT,
) -> Dict[str, Any]:
    rules = load_evidence_collector_readiness_rules(root)
    task_type = _infer_task_type(payload, rules)

    task_rules = (rules.get("task_types") or {}).get(task_type)
    if not isinstance(task_rules, dict):
        return {
            "status": "ok",
            "readiness_state": "not_applicable",
            "task_type": task_type,
            "required_evidence": [],
            "provided_evidence": [],
            "missing_evidence": [],
            "blocking_gaps": [],
            "advisory_gaps": [],
            "can_claim_ready": False,
            "can_claim_pass_with_caution": False,
            "manual_next_steps": [],
            "why": "Atlas does not have a governed evidence contract for this task type yet.",
            "advisory_only": bool(rules.get("advisory_only", True)),
        }

    required_evidence = _normalize_list(task_rules.get("required_evidence"))
    blocking_evidence = set(_normalize_list(task_rules.get("blocking_evidence")))
    advisory_evidence = set(_normalize_list(task_rules.get("advisory_evidence")))
    caution_allowed = set(_normalize_list(task_rules.get("can_pass_with_caution_when_missing_only")))
    provided_evidence = _normalize_list(payload.get("provided_evidence"))

    missing_evidence = [item for item in required_evidence if item not in provided_evidence]
    blocking_gaps = [item for item in missing_evidence if item in blocking_evidence]
    advisory_gaps = [item for item in missing_evidence if item in advisory_evidence or item not in blocking_evidence]

    if not required_evidence:
        readiness_state = "not_applicable"
    elif not missing_evidence:
        readiness_state = "evidence_ready"
    elif len(missing_evidence) == len(required_evidence):
        readiness_state = "evidence_missing"
    else:
        readiness_state = "evidence_partial"

    can_claim_ready = readiness_state == "evidence_ready"
    can_claim_pass_with_caution = bool(
        not can_claim_ready
        and not blocking_gaps
        and missing_evidence
        and set(missing_evidence).issubset(caution_allowed)
    )

    manual_next_steps: List[str] = []
    if missing_evidence:
        manual_next_steps.append(
            f"Collect or document: {', '.join(missing_evidence)}."
        )
    if task_type == "frontend_ui_landing" and {"screenshot_desktop", "screenshot_mobile"} & set(missing_evidence):
        manual_next_steps.append(
            "Keep screenshot evidence in readiness/manual mode until browser QA is separately approved."
        )
    if task_type == "high_risk_decision" and blocking_gaps:
        manual_next_steps.append(
            "Do not finalize the decision until alternatives, tradeoffs, risks and explicit approval are documented."
        )
    if task_type == "skill_governance_change" and "governance_check" in missing_evidence:
        manual_next_steps.append(
            "Run the governance check before calling the factory change strongly ready."
        )
    manual_next_steps = list(dict.fromkeys(manual_next_steps))

    status = "ok" if readiness_state in {"evidence_ready", "not_applicable"} else "needs_attention"
    why = (
        "Atlas uses this layer to distinguish proof-backed readiness from advisory-only confidence. Missing evidence can still allow cautionary posture, but not a strong PASS."
    )
    return {
        "status": status,
        "readiness_state": readiness_state,
        "task_type": task_type,
        "required_evidence": required_evidence,
        "provided_evidence": provided_evidence,
        "missing_evidence": missing_evidence,
        "blocking_gaps": blocking_gaps,
        "advisory_gaps": advisory_gaps,
        "can_claim_ready": can_claim_ready,
        "can_claim_pass_with_caution": can_claim_pass_with_caution,
        "manual_next_steps": manual_next_steps,
        "why": why,
        "advisory_only": bool(rules.get("advisory_only", True)),
    }


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(add_help=True)
    parser.add_argument("--payload-json", required=True)
    args = parser.parse_args(argv)
    payload = json.loads(args.payload_json)
    result = review_evidence_collector_readiness(payload, root=DEFAULT_ROOT)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
