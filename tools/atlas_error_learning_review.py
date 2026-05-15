from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Dict, List, Optional


DEFAULT_ROOT = Path(__file__).resolve().parents[1]
RULES_PATH = Path("config/atlas_error_learning_rules.json")


def load_atlas_error_learning_rules(root: Path = DEFAULT_ROOT) -> Dict[str, Any]:
    return json.loads((root / RULES_PATH).read_text(encoding="utf-8-sig"))


def _normalize(value: Any) -> str:
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


def _build_item(code: str, rule: Dict[str, Any], evidence: List[str]) -> Dict[str, Any]:
    return {
        "check": code,
        "severity": str(rule.get("severity", "medium")),
        "message": str(rule.get("recommended_fix", "Review this learned error before claiming the project is ready.")),
        "why_it_matters": str(rule.get("why_it_matters", "")).strip(),
        "evidence": [str(item).strip() for item in evidence if str(item).strip()][:4],
    }


def _certify_signal(certify_report: Dict[str, Any], *terms: str) -> bool:
    if not isinstance(certify_report, dict):
        return False
    haystack: List[str] = []
    result = certify_report.get("result") if isinstance(certify_report.get("result"), dict) else certify_report
    for bucket_name in ("blockers", "warnings"):
        for item in result.get(bucket_name, []):
            if isinstance(item, dict):
                haystack.append(_normalize(item.get("code")))
                haystack.append(_normalize(item.get("message")))
                haystack.append(_normalize(item.get("path")))
            else:
                haystack.append(_normalize(item))
    blob = " ".join(haystack)
    return any(term in blob for term in [term.strip().lower() for term in terms if term.strip()])


def review_atlas_error_learning(payload: Dict[str, Any], *, root: Path = DEFAULT_ROOT) -> Dict[str, Any]:
    rules = load_atlas_error_learning_rules(root)
    project_type = str(payload.get("project_type", "")).strip() or "unknown"
    ui_project = project_type in set(rules.get("ui_project_types", []))

    design_report = payload.get("design_report") or {}
    design_checks = _index_checks(list(payload.get("design_checks", [])))
    ui_pre_return_review = payload.get("ui_pre_return_review") or {}
    frontend_auto_audit_review = payload.get("frontend_auto_audit_review") or {}
    visual_qa_posture = payload.get("visual_qa_readiness_posture") or {}
    certify_report = payload.get("certify_report") or {}
    integration_surfaces = list(payload.get("integration_surfaces", []))

    hero_failure = bool(payload.get("hero_overflow")) or any(
        _normalize((design_checks.get(check_id) or {}).get("status")) in {"warning", "fail"}
        for check_id in ("hero_structure", "above_the_fold_clarity", "responsive_baseline")
    )
    font_failure = bool(payload.get("fonts_declared_not_loaded")) or (
        _normalize((design_checks.get("typography_coherence") or {}).get("status")) in {"warning", "fail"}
    )
    cta_failure = bool(payload.get("ctas_not_working")) or any(
        _normalize((design_checks.get(check_id) or {}).get("status")) in {"warning", "fail"}
        for check_id in ("cta_clarity", "cta_integrity")
    )
    onboarding_failure = bool(payload.get("onboarding_missing")) or bool(payload.get("copy_repeated")) or (
        _normalize((design_checks.get("landing_vs_documentation_balance") or {}).get("status")) in {"warning", "fail"}
    )
    touch_accessibility_failure = any(
        bool(payload.get(flag))
        for flag in ("tap_targets_too_small", "buttons_inside_summary", "focus_visible_missing")
    )
    seo_security_missing = _certify_signal(
        certify_report,
        "seo",
        "security",
        "headers",
        "csp",
        "x-frame-options",
        "strict-transport-security",
    )
    visual_evidence_required = bool(payload.get("requires_visual_evidence"))
    visual_evidence_missing = bool(payload.get("visual_evidence_missing")) or bool(ui_pre_return_review.get("missing_evidence")) or (
        visual_evidence_required
        and ui_project
        and not bool(visual_qa_posture.get("safe_to_run"))
        and not bool(payload.get("manual_visual_review_recorded"))
    )
    landing_readme_like = bool(payload.get("landing_reads_like_readme")) or (
        _normalize((design_checks.get("landing_vs_documentation_balance") or {}).get("status")) in {"warning", "fail"}
    )
    cta_or_onboarding_failure = cta_failure or onboarding_failure
    integration_claims_ahead = False
    integration_missing_labels = False
    for surface in integration_surfaces:
        if not isinstance(surface, dict):
            continue
        claim_active = bool(surface.get("claim_active"))
        declared_state = _normalize(surface.get("declared_state"))
        actual_state = _normalize(surface.get("actual_state"))
        tests_present = bool(surface.get("tests_present", True))
        if claim_active and actual_state in {"advisory", "readiness", "watchlist", "blocked", "needs_attention"}:
            integration_claims_ahead = True
        if not declared_state or declared_state not in {"ready", "readiness", "watchlist", "blocked", "advisory"}:
            integration_missing_labels = True
        if not tests_present:
            integration_missing_labels = True
        if actual_state in {"watchlist", "blocked", "needs_attention"} and claim_active:
            integration_claims_ahead = True

    signal_map = {
        "hero_or_mobile_header_failure": hero_failure,
        "font_or_typography_failure": font_failure,
        "cta_or_onboarding_failure": cta_or_onboarding_failure,
        "touch_accessibility_failure": touch_accessibility_failure,
        "seo_or_security_baseline_missing": seo_security_missing,
        "visual_evidence_missing": visual_evidence_missing,
        "landing_reads_like_readme": landing_readme_like,
        "landing_copy_or_onboarding_weak": onboarding_failure,
        "integration_claims_ahead_of_readiness": integration_claims_ahead,
        "integration_missing_tests_or_labels": integration_missing_labels,
    }

    blockers: List[Dict[str, Any]] = []
    warnings: List[Dict[str, Any]] = []
    triggered_signals: List[str] = []
    for check_id, rule in rules.get("checks", {}).items():
        signal_name = str(rule.get("signal", "")).strip()
        if not signal_name or not signal_map.get(signal_name):
            continue
        triggered_signals.append(signal_name)
        evidence = [signal_name]
        item = _build_item(check_id, rule, evidence)
        if bool(rule.get("blocks_ready_if_present")):
            blockers.append(item)
        else:
            warnings.append(item)

    requires_human_clarification = bool(visual_evidence_missing and not payload.get("manual_visual_review_recorded"))
    requires_decision_council = bool(integration_claims_ahead)

    if blockers:
        status = "needs_improvement"
    elif warnings:
        status = "needs_attention"
    else:
        status = "ready"

    warning_codes: List[str] = []
    if any(item["check"].startswith("hero_") or item["check"].startswith("cta_") or item["check"].startswith("touch_") or item["check"] == "seo_or_security_baseline_missing" for item in blockers):
        warning_codes.append("error_learning_ui_not_ready")
    if landing_readme_like or onboarding_failure:
        warning_codes.append("error_learning_landing_not_ready")
    if integration_claims_ahead:
        warning_codes.append("error_learning_integration_not_ready")
        warning_codes.append("error_learning_readiness_label_mismatch")
    if visual_evidence_missing:
        warning_codes.append("error_learning_visual_evidence_missing")

    warning_codes = list(dict.fromkeys(warning_codes))
    recommended_next_action = (
        "Do not call this surface ready yet; resolve the learned UI and landing regressions before handoff."
        if status == "needs_improvement"
        else "Keep the current posture advisory and tighten the weak readiness labels or evidence trail before promotion."
        if status == "needs_attention"
        else "The current payload does not repeat the known UI, landing or integration mistakes Atlas is tracking."
    )

    why = (
        "Atlas converts past delivery mistakes into local checks so the same visual, landing and integration failures are less likely to be reintroduced."
    )
    return {
        "status": status,
        "blockers": blockers,
        "warnings": warnings,
        "triggered_signals": triggered_signals,
        "warning_codes": warning_codes,
        "requires_human_clarification": requires_human_clarification,
        "requires_decision_council": requires_decision_council,
        "recommended_next_action": recommended_next_action,
        "why": why,
        "advisory_only": bool(rules.get("advisory_only", True)),
    }


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(add_help=True)
    parser.add_argument("--payload-json", required=True)
    args = parser.parse_args(argv)
    payload = json.loads(args.payload_json)
    result = review_atlas_error_learning(payload, root=DEFAULT_ROOT)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
