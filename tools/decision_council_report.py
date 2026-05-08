from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

try:
    from tools.project_intent_analyzer import analyze_project_intent
    from tools.project_phase_resolver import build_project_phase_report
except ModuleNotFoundError:
    from project_intent_analyzer import analyze_project_intent
    from project_phase_resolver import build_project_phase_report


DEFAULT_ROOT = Path(__file__).resolve().parents[1]

TRIGGER_RULES = {
    "architecture": {
        "terms": (
            "architecture",
            "architectural",
            "boundary",
            "boundaries",
            "system design",
            "refactor architecture",
            "module split",
        ),
        "risk": "Architecture changes can create durable factory drift across future projects.",
    },
    "external_tooling": {
        "terms": (
            "mcp",
            "external tool",
            "external tools",
            "github cli",
            "openrouter",
            "connector",
            "tooling",
            "docs mcp",
        ),
        "risk": "External-tool decisions can widen permissions, context cost and runtime surface.",
    },
    "skill_creation": {
        "terms": (
            "new skill",
            "create skill",
            "skill creation",
            "reusable skill",
            "new capability",
        ),
        "risk": "A weak skill decision can create capability sprawl in the Atlas factory.",
    },
    "signal_conflict": {
        "terms": (
            "conflict",
            "contradiction",
            "ambiguous",
            "unclear",
            "disagree",
            "low confidence",
            "competing recommendations",
        ),
        "risk": "Conflicting signals are exactly where a structured dissent pass is more useful than a single-path recommendation.",
    },
    "high_risk_change": {
        "terms": (
            "high risk",
            "dangerous",
            "global config",
            "config global",
            "runtime",
            "production",
            "destructive",
        ),
        "risk": "High-risk changes need explicit challenge before Atlas normalizes them as guidance.",
    },
    "derived_project_impact": {
        "terms": (
            "derived project",
            "derived projects",
            "reyesoft",
            "before touching projects",
            "project boundary",
            "certify-project",
        ),
        "risk": "Changes that could affect derived projects need stronger boundary review before execution.",
    },
}

LOW_RISK_TERMS = (
    "readme",
    "documentation",
    "copy edit",
    "small copy",
    "typo",
    "summarize",
    "list files",
)


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _normalize(text: str) -> str:
    return " ".join(str(text).lower().split())


def _detect_triggers(topic: str) -> List[Dict[str, str]]:
    normalized = _normalize(topic)
    triggers: List[Dict[str, str]] = []
    for trigger_id, rule in TRIGGER_RULES.items():
        hits = [term for term in rule["terms"] if term in normalized]
        if hits:
            triggers.append(
                {
                    "id": trigger_id,
                    "hits": ", ".join(hits),
                    "risk": rule["risk"],
                }
            )
    return triggers


def _is_low_risk_topic(topic: str) -> bool:
    normalized = _normalize(topic)
    return any(term in normalized for term in LOW_RISK_TERMS)


def _build_role_briefs(triggers: List[Dict[str, str]]) -> List[Dict[str, str]]:
    trigger_labels = [item["id"] for item in triggers]
    trigger_text = ", ".join(trigger_labels) if trigger_labels else "general decision framing"
    return [
        {
            "role": "Architect",
            "focus": f"Test whether the decision improves Atlas structure, boundaries and long-term maintainability around {trigger_text}.",
        },
        {
            "role": "Skeptic",
            "focus": "Look for hidden assumptions, easier alternatives and reasons the decision should be rejected or delayed.",
        },
        {
            "role": "Governance Reviewer",
            "focus": "Check whether the proposal stays read-only by default, preserves Atlas vs derived-project boundaries and avoids hidden automation.",
        },
        {
            "role": "Cost Controller",
            "focus": "Challenge context cost, model cost, maintenance burden and operational sprawl.",
        },
        {
            "role": "Product/UX Reviewer",
            "focus": "Check whether the decision helps real operator clarity instead of adding internal cleverness.",
        },
        {
            "role": "Chairman",
            "focus": "Synthesize agreement, dissent, residual risks and the next safe action without pretending consensus exists when it does not.",
        },
    ]


def _build_open_questions(
    *,
    topic: str,
    council_recommended: bool,
    intent_report: Optional[Dict[str, Any]],
) -> List[str]:
    questions: List[str] = []
    normalized = _normalize(topic)
    if "project" not in normalized and "atlas" not in normalized:
        questions.append("Which repo or decision surface is actually affected by this decision?")
    if "constraint" not in normalized and "no " not in normalized:
        questions.append("What hard constraints or non-goals should the council treat as binding?")
    if council_recommended:
        questions.append("What local evidence should each council role treat as the source of truth before recommending action?")
    if isinstance(intent_report, dict) and intent_report.get("missing_definition"):
        questions.append("Which missing project or scope details should be clarified before treating the decision as final?")
    return questions[:4]


def build_decision_council_report(
    *,
    topic: str,
    root: Optional[Path] = None,
    project: Optional[Path] = None,
) -> Dict[str, Any]:
    resolved_root = (root or DEFAULT_ROOT).resolve()
    resolved_project = project.resolve() if project else None

    triggers = _detect_triggers(topic)
    low_risk = _is_low_risk_topic(topic)
    phase_report: Optional[Dict[str, Any]] = None
    intent_report: Optional[Dict[str, Any]] = None
    evidence: List[str] = []

    if resolved_project is not None:
        phase_report = build_project_phase_report(resolved_root, resolved_project)
        intent_report = analyze_project_intent(project=resolved_project)
        evidence.append(f"project_phase={phase_report.get('current_phase')}")
        evidence.append(f"project_phase_confidence={phase_report.get('confidence')}")
        evidence.append(f"project_intent_status={intent_report.get('status')}")
        evidence.extend(str(item) for item in intent_report.get("evidence", [])[:4])

    for trigger in triggers:
        evidence.append(f"trigger:{trigger['id']}:{trigger['hits']}")

    council_recommended = bool(triggers) and not low_risk
    if council_recommended:
        decision = "Use a structured decision council before implementing or approving this change."
        agreement_level = "undetermined"
        dissenting_views = [
            "A lighter single-path review may still be enough if existing Atlas evidence already resolves the decision cleanly."
        ]
        recommended_next_action = (
            "Run the `decision-council` skill or follow `decision_council_review.md`, then let the Chairman section record the final decision."
        )
    else:
        decision = "A full decision council is not required for the current topic."
        agreement_level = "high"
        dissenting_views = [
            "Escalate to a decision council if the task expands into architecture, external tools, skill creation or derived-project impact."
        ]
        recommended_next_action = (
            "Proceed with the normal Atlas flow and keep a council review in reserve if new ambiguity appears."
        )

    risks = [
        {
            "trigger": item["id"],
            "message": item["risk"],
        }
        for item in triggers
    ]

    open_questions = _build_open_questions(
        topic=topic,
        council_recommended=council_recommended,
        intent_report=intent_report,
    )

    return {
        "status": "ok",
        "topic": topic,
        "project_path": str(resolved_project) if resolved_project else None,
        "council_recommended": council_recommended,
        "decision": decision,
        "agreement_level": agreement_level,
        "dissenting_views": dissenting_views,
        "risks": risks,
        "evidence": evidence,
        "open_questions": open_questions,
        "recommended_next_action": recommended_next_action,
        "workflow": "decision_council_review",
        "role_briefs": _build_role_briefs(triggers),
        "phase_context": phase_report,
        "intent_context": intent_report,
        "timestamp": _utc_now_iso(),
    }


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(add_help=True)
    parser.add_argument("--root", default=None, help="Atlas root to use. Defaults to this repository root.")
    parser.add_argument("--project", default=None, help="Optional derived project path for extra local evidence.")
    parser.add_argument("--topic", required=True, help="Decision topic or difficult question to frame.")
    args = parser.parse_args(argv)

    root = Path(args.root).resolve() if args.root else DEFAULT_ROOT
    project = Path(args.project).resolve() if args.project else None
    report = build_decision_council_report(topic=args.topic, root=root, project=project)
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
