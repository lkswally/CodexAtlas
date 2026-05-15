from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Dict, List, Optional

try:
    from tools.brand_profile_schema import build_brand_profile_assessment
except ModuleNotFoundError:
    from brand_profile_schema import build_brand_profile_assessment


DEFAULT_ROOT = Path(__file__).resolve().parents[1]
RULES_PATH = Path("config/brand_json_v2_readiness_rules.json")


def load_brand_json_v2_rules(root: Path = DEFAULT_ROOT) -> Dict[str, Any]:
    return json.loads((root / RULES_PATH).read_text(encoding="utf-8-sig"))


def assess_brand_json_v2_readiness(
    *,
    project_type: Optional[str],
    visual_intent_contract: Optional[Dict[str, Any]] = None,
    profile: Optional[Dict[str, Any]] = None,
    profile_review: Optional[Dict[str, Any]] = None,
    surface: Optional[Dict[str, str]] = None,
    metadata: Optional[Dict[str, Any]] = None,
    project_name: Optional[str] = None,
    objective: Optional[str] = None,
    root: Path = DEFAULT_ROOT,
) -> Dict[str, Any]:
    rules = load_brand_json_v2_rules(root)
    project_type_value = str(project_type or "").strip()
    if project_type_value in set(rules.get("backend_exempt_project_types", [])):
        return {
            "status": "skipped",
            "requires_brand_json_v2": False,
            "explicit_profile_present": False,
            "missing_sections": [],
            "weak_sections": [],
            "derivative_risks": [],
            "accessibility_risks": [],
            "export_candidate": False,
            "evidence_expectations": list(rules.get("minimum_evidence_expectations", [])),
            "next_action": "No brand.json v2 equivalent is required for the current project type.",
            "why": "This project does not currently look like a UI-facing surface that needs an explicit brand artifact.",
            "advisory_only": bool(rules.get("advisory_only", True)),
        }

    review = profile_review or build_brand_profile_assessment(
        project_type=project_type_value,
        visual_intent_contract=visual_intent_contract,
        profile=profile,
        surface=surface,
        metadata=metadata,
        project_name=project_name,
        objective=objective,
        root=root,
    )
    resolved_profile = review.get("profile") if isinstance(review, dict) else {}
    if not isinstance(resolved_profile, dict):
        resolved_profile = {}

    required_sections = list(rules.get("required_sections", []))
    missing_sections = [
        field_name
        for field_name in required_sections
        if (
            field_name not in resolved_profile
            or resolved_profile.get(field_name) in (None, "", [])
            or resolved_profile.get(field_name) == {}
        )
    ]
    weak_sections = list(review.get("weak_fields", [])) + list(review.get("invalid_fields", []))
    derivative_risks = list(review.get("derivative_risks", []))
    accessibility_risks = list(review.get("accessibility_risks", []))
    anti_generic_risks = list(review.get("anti_generic_risks", []))
    explicit_profile_present = bool(review.get("explicit_profile_present"))
    requires_explicit = bool(rules.get("explicit_profile_required_for_ready", True))
    export_candidate = (
        (explicit_profile_present or not requires_explicit)
        and not missing_sections
        and not weak_sections
        and not derivative_risks
        and not accessibility_risks
    )
    status = "ready" if export_candidate else "needs_input"

    why_parts = [
        "Atlas uses this readiness layer to decide whether the current brand profile is explicit and strong enough to count as a governed brand.json v2 equivalent."
    ]
    if not explicit_profile_present:
        why_parts.append("The current brand profile is still inferred instead of explicitly documented.")
    if missing_sections:
        why_parts.append(f"Missing: {', '.join(missing_sections[:5])}.")
    if weak_sections:
        why_parts.append(f"Weak: {', '.join(weak_sections[:5])}.")
    if derivative_risks:
        why_parts.append(f"Derivative risks: {', '.join(derivative_risks[:4])}.")

    return {
        "status": status,
        "requires_brand_json_v2": True,
        "explicit_profile_present": explicit_profile_present,
        "missing_sections": missing_sections,
        "weak_sections": weak_sections,
        "anti_generic_risks": anti_generic_risks,
        "derivative_risks": derivative_risks,
        "accessibility_risks": accessibility_risks,
        "export_candidate": export_candidate,
        "evidence_expectations": resolved_profile.get("evidence_expectations", []) or list(rules.get("minimum_evidence_expectations", [])),
        "profile": resolved_profile,
        "profile_source": review.get("profile_source"),
        "next_action": "Document an explicit brand profile with complete v2 sections before stronger branding or UI-ready claims."
        if status != "ready"
        else "The brand profile is explicit and strong enough to serve as a governed brand.json v2 equivalent.",
        "why": " ".join(why_parts),
        "advisory_only": bool(rules.get("advisory_only", True)),
    }


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(add_help=True)
    parser.add_argument("--project-type", default=None)
    parser.add_argument("--visual-intent-json", default=None)
    parser.add_argument("--brand-profile-json", default=None)
    parser.add_argument("--brand-profile-review-json", default=None)
    args = parser.parse_args(argv)

    visual_intent = json.loads(args.visual_intent_json) if args.visual_intent_json else None
    profile = json.loads(args.brand_profile_json) if args.brand_profile_json else None
    profile_review = json.loads(args.brand_profile_review_json) if args.brand_profile_review_json else None
    result = assess_brand_json_v2_readiness(
        project_type=args.project_type,
        visual_intent_contract=visual_intent,
        profile=profile,
        profile_review=profile_review,
        root=DEFAULT_ROOT,
    )
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
