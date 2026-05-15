from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Dict, List, Optional


DEFAULT_ROOT = Path(__file__).resolve().parents[1]
RULES_PATH = Path("config/frontend_auto_audit_rules.json")


def load_frontend_auto_audit_rules(root: Path = DEFAULT_ROOT) -> Dict[str, Any]:
    return json.loads((root / RULES_PATH).read_text(encoding="utf-8-sig"))


def _normalize(value: str) -> str:
    return str(value or "").strip().lower()


def _index_checks(checks: List[Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:
    indexed: Dict[str, Dict[str, Any]] = {}
    for item in checks:
        if not isinstance(item, dict):
            continue
        check_id = str(item.get("id", "")).strip()
        if check_id:
            indexed[check_id] = item
    return indexed


def _build_item(check_id: str, severity: str, message: str, evidence: List[str]) -> Dict[str, Any]:
    return {
        "check": check_id,
        "severity": severity,
        "message": message,
        "evidence": evidence[:4],
    }


def audit_frontend_auto_readiness(payload: Dict[str, Any], *, root: Path = DEFAULT_ROOT) -> Dict[str, Any]:
    rules = load_frontend_auto_audit_rules(root)
    project_type = str(payload.get("project_type", "")).strip()
    if project_type in set(rules.get("backend_exempt_project_types", [])):
        return {
            "status": "skipped",
            "can_support_pre_return": False,
            "blockers": [],
            "warnings": [],
            "ready_guardrails": [],
            "missing_guardrails": [],
            "evidence_gaps": [],
            "watchlist_dependencies": list(rules.get("watchlist_dependencies", [])),
            "recommended_next_action": "No frontend auto audit is required for the current project type.",
            "why": "This project does not currently look like a frontend-facing surface that needs the local auto-audit guardrail bundle.",
            "advisory_only": bool(rules.get("advisory_only", True)),
        }

    intent_review = payload.get("intent_clarifier_contract") or {}
    visual_review = payload.get("visual_intent_contract_review") or {}
    brand_json_review = payload.get("brand_json_v2_readiness") or {}
    ui_pre_return_review = payload.get("ui_pre_return_review") or {}
    design_quality_review = payload.get("design_quality_review") or {}
    design_checks = _index_checks(list(payload.get("design_checks", [])))

    blockers: List[Dict[str, Any]] = []
    warnings: List[Dict[str, Any]] = []
    ready_guardrails: List[str] = []
    missing_guardrails: List[str] = []
    evidence_gaps: List[str] = []

    def evaluate(check_id: str, passed: bool, evidence: List[str], *, warning_code: str) -> None:
        rule = rules.get("checks", {}).get(check_id, {})
        severity = str(rule.get("severity", "medium"))
        if passed:
            ready_guardrails.append(check_id)
            return
        missing_guardrails.append(check_id)
        item = _build_item(
            warning_code,
            severity,
            str(rule.get("recommended_fix", "Review this frontend guardrail before final handoff.")),
            evidence,
        )
        warnings.append(item)
        if bool(rule.get("blocks_ready_if_present")):
            blockers.append(item)

    evaluate(
        "intent_clarifier_ready",
        str(intent_review.get("status", "")).strip() == "ready",
        list(intent_review.get("missing_questions", []))[:4] + list(intent_review.get("weak_answers", []))[:4],
        warning_code="frontend_auto_audit_missing_intent_clarifier",
    )
    evaluate(
        "visual_intent_contract_ready",
        str(visual_review.get("status", "")).strip() == "ready",
        list(visual_review.get("missing_fields", []))[:4] + list(visual_review.get("weak_fields", []))[:4],
        warning_code="frontend_auto_audit_missing_intent_clarifier",
    )
    evaluate(
        "brand_json_v2_ready",
        str(brand_json_review.get("status", "")).strip() == "ready",
        list(brand_json_review.get("missing_sections", []))[:4] + list(brand_json_review.get("weak_sections", []))[:4],
        warning_code="frontend_auto_audit_missing_brand_json_v2",
    )
    evaluate(
        "ui_pre_return_ready",
        bool(ui_pre_return_review.get("pass_ready")) and str(ui_pre_return_review.get("status", "")).strip() in {"ready", "pass"},
        [item.get("id", "unknown_blocker") for item in ui_pre_return_review.get("blockers", [])[:4]],
        warning_code="frontend_auto_audit_not_ready",
    )
    evaluate(
        "design_quality_ready",
        bool(design_quality_review.get("ready_for_handoff")) and str(design_quality_review.get("status", "")).strip() == "ready",
        list(design_quality_review.get("detected_risks", []))[:4],
        warning_code="frontend_auto_audit_not_ready",
    )

    responsive_check = design_checks.get("responsive_baseline")
    responsive_passed = isinstance(responsive_check, dict) and str(responsive_check.get("status", "")).strip() == "pass"
    evaluate(
        "responsive_baseline_present",
        responsive_passed,
        list((responsive_check or {}).get("evidence", []))[:4] if isinstance(responsive_check, dict) else ["responsive_baseline_missing"],
        warning_code="frontend_auto_audit_not_ready",
    )

    evidence_expectations = []
    if isinstance(visual_review.get("contract"), dict):
        evidence_expectations.extend(list(visual_review["contract"].get("evidence_expectations", [])))
    evidence_expectations.extend(list(brand_json_review.get("evidence_expectations", [])))
    evidence_expectations = [str(item).strip() for item in evidence_expectations if str(item).strip()]
    evidence_defined = bool(evidence_expectations) and not ui_pre_return_review.get("missing_evidence")
    evaluate(
        "evidence_expectations_defined",
        evidence_defined,
        list(ui_pre_return_review.get("missing_evidence", []))[:4] or ["evidence_expectations_missing"],
        warning_code="frontend_auto_audit_missing_evidence",
    )
    if not evidence_defined:
        evidence_gaps.extend(list(ui_pre_return_review.get("missing_evidence", []))[:4] or ["evidence_expectations"])

    watchlist_dependencies = list(rules.get("watchlist_dependencies", []))
    warnings.extend(
        [
            _build_item(
                "frontend_auto_audit_watchlist_screenshots",
                "low",
                "Screenshot evidence is still a watchlist dependency; manual review is still needed for visual proof.",
                ["evidence_collector_screenshots"],
            ),
            _build_item(
                "frontend_auto_audit_watchlist_visual_fidelity",
                "low",
                "Visual fidelity judgment remains a readiness layer until screenshot- or browser-based evidence is approved.",
                ["visual_fidelity_judge"],
            ),
            _build_item(
                "frontend_auto_audit_watchlist_reality_check",
                "low",
                "A stronger final reality-checker remains advisory until Atlas has richer execution evidence.",
                ["final_reality_checker"],
            ),
        ]
    )

    status = "ready" if not blockers else "needs_improvement"
    can_support_pre_return = not blockers
    why = (
        "The current local guardrails are strong enough to support a pre-return frontend decision."
        if can_support_pre_return
        else "Core frontend guardrails are still incomplete, so Atlas should not treat the current UI as strongly handoff-ready."
    )
    return {
        "status": status,
        "can_support_pre_return": can_support_pre_return,
        "blockers": blockers,
        "warnings": warnings,
        "ready_guardrails": ready_guardrails,
        "missing_guardrails": missing_guardrails,
        "evidence_gaps": evidence_gaps,
        "watchlist_dependencies": watchlist_dependencies,
        "recommended_next_action": "Resolve the missing local guardrails before trusting a final frontend handoff claim."
        if blockers
        else "Local guardrails are in place; keep screenshot and fidelity evidence in watchlist until separately approved.",
        "why": why,
        "advisory_only": bool(rules.get("advisory_only", True)),
    }


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(add_help=True)
    parser.add_argument("--payload-json", required=True)
    args = parser.parse_args(argv)

    payload = json.loads(args.payload_json)
    result = audit_frontend_auto_readiness(payload, root=DEFAULT_ROOT)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
