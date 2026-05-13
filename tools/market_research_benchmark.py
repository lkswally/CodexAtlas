from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Sequence


DEFAULT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_RULES = {
    "version": "1.0",
    "advisory_only": True,
    "primary_reference_repo": {
        "id": "claude-vibecoding",
        "source_type": "local_reference_clone",
        "path": "_reference/claude-vibecoding",
    },
    "allowed_source_types": [
        "local_reference_clone",
        "documented_repo",
        "explicit_payload",
    ],
    "benchmark_axes": [
        "design_quality",
        "skill_governance",
        "evidence_discipline",
        "runtime_risk",
        "reuse_fit",
        "cost_context",
    ],
    "recommendation_types": [
        "adapt_now",
        "design_later",
        "watchlist",
        "discard",
    ],
    "required_output_sections": [
        "reviewed_references",
        "atlas_capabilities",
        "prioritized_opportunities",
        "blocked_references",
        "recommended_next_actions",
    ],
    "high_risk_signals": [
        "requires_mcp",
        "requires_install",
        "auto_modifies_skills",
        "auto_sync",
        "claude_only_runtime",
        "browser_automation",
        "creative_runtime",
    ],
    "requires_decision_council_signals": [
        "automation_heavy",
        "conflicting_reference_patterns",
        "runtime_expansion",
        "global_factory_surface_change",
    ],
    "reference_catalog": [],
}
REFERENCE_SENTINELS = ("README.md", "CLAUDE.md", "UPGRADE_LOG.md", "agents", "docs")
ATLAS_CAPABILITY_PATHS = {
    "intent_clarifier": [
        "tools/project_intent_analyzer.py",
        "config/visual_intent_contract_rules.json",
    ],
    "visual_direction": [
        "skills/visual-direction-checkpoint/skill.json",
        "workflows/design_intelligence_pipeline.md",
    ],
    "brand_profile": [
        "tools/brand_profile_schema.py",
        "config/brand_profile_schema_rules.json",
    ],
    "ui_pre_return_audit": [
        "tools/ui_pre_return_audit.py",
        "config/ui_pre_return_audit_rules.json",
    ],
    "anti_generic_guardrails": [
        "policies/anti_generic_ui_policy.md",
        "skills/anti-generic-ui-audit/skill.json",
    ],
    "evidence_discipline": [
        "policies/design_evidence_policy.md",
        "tools/quality_gate_report.py",
        "agents/reality_checker.md",
    ],
    "skill_lifecycle": [
        "config/skill_lifecycle_rules.json",
        "policies/skill_lifecycle_policy.md",
    ],
    "skill_improvement_loop": [
        "tools/skill_improvement_review.py",
        "config/skill_improvement_review_rules.json",
    ],
    "market_research_benchmark": [
        "tools/market_research_benchmark.py",
        "config/market_research_benchmark_rules.json",
    ],
    "mcp_readiness": [
        "tools/mcp_readiness_check.py",
        "config/mcp_profiles.json",
    ],
    "decision_council": [
        "tools/decision_council_report.py",
        "skills/decision-council/skill.json",
    ],
    "visual_qa_real": [],
    "creative_pipeline": [],
    "skill_distribution": [],
    "continuous_review": [],
}
REFERENCE_TO_CAPABILITY = {
    "intent_clarifier": "intent_clarifier",
    "visual_direction": "visual_direction",
    "brand_profile": "brand_profile",
    "ui_pre_return_audit": "ui_pre_return_audit",
    "evidence_discipline": "evidence_discipline",
    "anti_generic_guardrails": "anti_generic_guardrails",
    "skill_improvement_loop": "skill_improvement_loop",
    "continuous_review": "skill_improvement_loop",
    "curated_skill_discovery": "market_research_benchmark",
    "benchmark_driven_skill_evolution": "market_research_benchmark",
    "skill_catalog_scale": "skill_improvement_loop",
    "stdlib_helper_tools": "skill_improvement_loop",
    "skill_packaging": "skill_distribution",
    "skill_distribution": "skill_distribution",
    "cross_tool_sync": "skill_distribution",
    "creative_pipeline": "creative_pipeline",
    "visual_qa_real": "visual_qa_real",
}
RISKY_GAP_CAPABILITIES = {
    "creative_pipeline",
    "visual_qa_real",
    "skill_distribution",
    "continuous_improvement",
    "auto_skill_creation",
    "self_improvement",
}


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _read_json(path: Path) -> Dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def _read_json_any(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def _load_rules(root: Path) -> Dict[str, Any]:
    path = root / "config" / "market_research_benchmark_rules.json"
    if not path.exists():
        return dict(DEFAULT_RULES)
    data = _read_json(path)
    if not isinstance(data, dict):
        return dict(DEFAULT_RULES)
    merged = dict(DEFAULT_RULES)
    merged.update(data)
    return merged


def _reference_is_complete(path: Path) -> tuple[bool, List[str]]:
    missing = [name for name in REFERENCE_SENTINELS if not (path / name).exists()]
    return not missing, missing


def _capability_status(root: Path, relpaths: Sequence[str]) -> str:
    if not relpaths:
        return "missing"
    existing = sum(1 for relpath in relpaths if (root / relpath).exists())
    if existing == len(relpaths):
        return "adapted"
    if existing:
        return "partially_adapted"
    return "missing"


def _atlas_capabilities(root: Path) -> List[Dict[str, Any]]:
    items: List[Dict[str, Any]] = []
    for capability_id, relpaths in sorted(ATLAS_CAPABILITY_PATHS.items()):
        status = _capability_status(root, relpaths)
        items.append(
            {
                "capability": capability_id,
                "status": status,
                "evidence_paths": relpaths,
            }
        )
    return items


def _reference_catalog(rules: Dict[str, Any], reference_payload: Optional[Sequence[Dict[str, Any]]]) -> List[Dict[str, Any]]:
    catalog = list(rules.get("reference_catalog", []))
    if reference_payload:
        catalog.extend(reference_payload)
    return [item for item in catalog if isinstance(item, dict) and str(item.get("id", "")).strip()]


def _capability_index(atlas_capabilities: Sequence[Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:
    return {str(item["capability"]): dict(item) for item in atlas_capabilities}


def _derive_capability_gap(focus_areas: Sequence[str], atlas_index: Dict[str, Dict[str, Any]]) -> List[Dict[str, str]]:
    gaps: List[Dict[str, str]] = []
    for focus_area in focus_areas:
        mapped = REFERENCE_TO_CAPABILITY.get(str(focus_area), str(focus_area))
        atlas_signal = atlas_index.get(mapped, {"status": "missing"})
        gaps.append(
            {
                "focus_area": str(focus_area),
                "atlas_capability": mapped,
                "atlas_status": str(atlas_signal.get("status", "missing")),
            }
        )
    return gaps


def _has_risk_signal(reference: Dict[str, Any], signal: str) -> bool:
    return signal in {str(item) for item in reference.get("risk_signals", [])}


def _review_reference(
    *,
    root: Path,
    reference: Dict[str, Any],
    atlas_index: Dict[str, Dict[str, Any]],
    rules: Dict[str, Any],
) -> Dict[str, Any]:
    source_type = str(reference.get("source_type", "documented_repo")).strip() or "documented_repo"
    reviewed: Dict[str, Any] = {
        "id": str(reference.get("id", "unknown_reference")).strip() or "unknown_reference",
        "source_type": source_type,
        "source": str(reference.get("source", "")).strip(),
        "focus_areas": [str(item) for item in reference.get("focus_areas", []) if str(item).strip()],
        "benefit": str(reference.get("benefit", "medium")).strip() or "medium",
        "risk": str(reference.get("risk", "medium")).strip() or "medium",
        "fit": str(reference.get("fit", "medium")).strip() or "medium",
        "notes": [str(item) for item in reference.get("notes", []) if str(item).strip()],
        "risk_signals": [str(item) for item in reference.get("risk_signals", []) if str(item).strip()],
        "default_recommendation": str(reference.get("default_recommendation", "watchlist")).strip() or "watchlist",
    }

    if source_type == "local_reference_clone":
        path = (root / reviewed["source"]).resolve()
        complete, missing = _reference_is_complete(path)
        reviewed["evidence_status"] = "local_verified" if complete else "local_incomplete"
        reviewed["missing_reference_surface"] = missing
    elif source_type == "explicit_payload":
        reviewed["evidence_status"] = "explicit_payload_only"
        reviewed["missing_reference_surface"] = []
    else:
        reviewed["evidence_status"] = "documented_only"
        reviewed["missing_reference_surface"] = []

    reviewed["capability_gaps"] = _derive_capability_gap(reviewed["focus_areas"], atlas_index)
    missing_risky_capabilities = {
        item["atlas_capability"]
        for item in reviewed["capability_gaps"]
        if item["atlas_status"] == "missing" and item["atlas_capability"] in RISKY_GAP_CAPABILITIES
    }

    recommendation = reviewed["default_recommendation"]
    if reviewed["evidence_status"] == "local_incomplete":
        recommendation = "watchlist"
    if any(item["atlas_status"] == "missing" for item in reviewed["capability_gaps"]) and recommendation == "design_later":
        recommendation = "adapt_now"
    if missing_risky_capabilities and recommendation == "adapt_now":
        recommendation = "design_later" if source_type == "local_reference_clone" else "watchlist"
    if source_type != "local_reference_clone" and any(
        _has_risk_signal(reference, signal) for signal in rules.get("high_risk_signals", [])
    ):
        if recommendation == "adapt_now":
            recommendation = "watchlist"
    reviewed["recommendation"] = recommendation

    reviewed["requires_human_approval"] = recommendation in {"adapt_now", "design_later"} and bool(reviewed["capability_gaps"])
    reviewed["requires_decision_council"] = bool(missing_risky_capabilities) or any(
        signal in {str(item) for item in reviewed["risk_signals"]}
        for signal in rules.get("requires_decision_council_signals", [])
    )
    reviewed["why"] = (
        f"Reference `{reviewed['id']}` is `{reviewed['evidence_status']}` with fit `{reviewed['fit']}` and risk `{reviewed['risk']}`; "
        f"Atlas gap signals: {[item['atlas_capability'] + '=' + item['atlas_status'] for item in reviewed['capability_gaps']]}"
    )
    return reviewed


def _prioritized_opportunities(reviewed_references: Sequence[Dict[str, Any]]) -> List[Dict[str, Any]]:
    opportunities: List[Dict[str, Any]] = []
    for reference in reviewed_references:
        if reference.get("recommendation") not in {"adapt_now", "design_later"}:
            continue
        for gap in reference.get("capability_gaps", []):
            if gap.get("atlas_status") == "adapted":
                continue
            opportunities.append(
                {
                    "reference_id": reference["id"],
                    "focus_area": gap["focus_area"],
                    "atlas_capability": gap["atlas_capability"],
                    "atlas_status": gap["atlas_status"],
                    "recommendation": reference["recommendation"],
                    "benefit": reference["benefit"],
                    "risk": reference["risk"],
                    "why": reference["why"],
                }
            )
    opportunities.sort(
        key=lambda item: (
            0 if item["recommendation"] == "adapt_now" else 1,
            0 if item["atlas_status"] == "missing" else 1,
            item["risk"],
        )
    )
    return opportunities[:6]


def _blocked_references(reviewed_references: Sequence[Dict[str, Any]]) -> List[Dict[str, Any]]:
    blocked: List[Dict[str, Any]] = []
    for reference in reviewed_references:
        if reference.get("recommendation") in {"watchlist", "discard"}:
            blocked.append(
                {
                    "reference_id": reference["id"],
                    "recommendation": reference["recommendation"],
                    "risk_signals": reference.get("risk_signals", []),
                    "why": reference.get("why"),
                }
            )
    return blocked


def _recommended_next_actions(
    opportunities: Sequence[Dict[str, Any]],
    blocked: Sequence[Dict[str, Any]],
) -> List[str]:
    actions: List[str] = []
    if opportunities:
        top = opportunities[0]
        actions.append(
            f"Review `{top['focus_area']}` from `{top['reference_id']}` and decide whether Atlas should adapt it as a governed read-only layer."
        )
    if len(opportunities) > 1:
        second = opportunities[1]
        actions.append(
            f"Compare `{second['reference_id']}` against existing Atlas capability `{second['atlas_capability']}` before adding any new skill or workflow."
        )
    if blocked:
        first = blocked[0]
        actions.append(
            f"Keep `{first['reference_id']}` in `{first['recommendation']}` posture until its runtime or automation risk is explicitly reconsidered."
        )
    return actions[:3]


def build_market_research_benchmark(
    *,
    root: Path,
    topic: str,
    reference_payload: Optional[Sequence[Dict[str, Any]]] = None,
) -> Dict[str, Any]:
    root = root.resolve()
    rules = _load_rules(root)
    atlas_capabilities = _atlas_capabilities(root)
    atlas_index = _capability_index(atlas_capabilities)
    catalog = _reference_catalog(rules, reference_payload)
    reviewed_references = [
        _review_reference(root=root, reference=reference, atlas_index=atlas_index, rules=rules)
        for reference in catalog
    ]
    opportunities = _prioritized_opportunities(reviewed_references)
    blocked = _blocked_references(reviewed_references)
    requires_human_approval = any(bool(item.get("requires_human_approval")) for item in reviewed_references)
    requires_decision_council = any(bool(item.get("requires_decision_council")) for item in reviewed_references)
    status = "ok" if reviewed_references else "needs_reference"
    if blocked and not opportunities:
        status = "needs_attention"

    return {
        "status": status,
        "topic": topic,
        "advisory_only": bool(rules.get("advisory_only", True)),
        "benchmark_axes": list(rules.get("benchmark_axes", [])),
        "atlas_capabilities": atlas_capabilities,
        "reviewed_references": reviewed_references,
        "prioritized_opportunities": opportunities,
        "blocked_references": blocked,
        "requires_human_approval": requires_human_approval,
        "requires_decision_council": requires_decision_council,
        "recommended_next_actions": _recommended_next_actions(opportunities, blocked),
        "why": (
            f"Benchmarked {len(reviewed_references)} references against {len(atlas_capabilities)} Atlas capability signals "
            f"without fetching external runtime data or modifying the catalog."
        ),
        "timestamp": _utc_now_iso(),
    }


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(add_help=True)
    parser.add_argument("--root", default=None, help="Atlas root to use. Defaults to this repository root.")
    parser.add_argument("--topic", required=True, help="Benchmark topic or comparison goal.")
    parser.add_argument("--references", default=None, help="Optional JSON array with explicit reference payloads.")
    args = parser.parse_args(argv)

    root = Path(args.root).resolve() if args.root else DEFAULT_ROOT
    references: Optional[List[Dict[str, Any]]] = None
    if args.references:
        payload = _read_json_any(Path(args.references).resolve())
        if not isinstance(payload, list):
            raise SystemExit("--references must point to a JSON array.")
        references = payload

    report = build_market_research_benchmark(root=root, topic=args.topic, reference_payload=references)
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
