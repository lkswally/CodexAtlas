import json
import os
import shutil
from pathlib import Path
from uuid import uuid4

os.environ["ATLAS_DISABLE_EVENT_LOGS"] = "1"

from tests._support_paths import ATLAS_ROOT
from tools.market_research_benchmark import build_market_research_benchmark


ROOT = ATLAS_ROOT


def test_market_research_benchmark_returns_structured_report_for_current_atlas():
    result = build_market_research_benchmark(
        root=ROOT,
        topic="Benchmark Atlas against claude-vibecoding and current radar repos.",
    )

    assert result["status"] in {"ok", "needs_attention"}
    assert result["reviewed_references"]
    assert any(item["id"] == "claude-vibecoding" for item in result["reviewed_references"])
    assert any(
        item["capability"] == "market_research_benchmark" and item["status"] == "adapted"
        for item in result["atlas_capabilities"]
    )


def test_market_research_benchmark_marks_incomplete_local_reference():
    temp_root = ROOT / "tests" / f"_tmp_market_research_{uuid4().hex}" / "atlas"
    shutil.rmtree(temp_root.parent, ignore_errors=True)
    (temp_root / "config").mkdir(parents=True, exist_ok=True)
    rules = json.loads((ROOT / "config" / "market_research_benchmark_rules.json").read_text(encoding="utf-8"))
    (temp_root / "config" / "market_research_benchmark_rules.json").write_text(
        json.dumps(rules, indent=2),
        encoding="utf-8",
    )
    try:
        result = build_market_research_benchmark(
            root=temp_root,
            topic="Benchmark Atlas against the local primary reference.",
        )
    finally:
        shutil.rmtree(temp_root.parent, ignore_errors=True)

    claude_reference = next(item for item in result["reviewed_references"] if item["id"] == "claude-vibecoding")
    assert claude_reference["evidence_status"] == "local_incomplete"
    assert claude_reference["recommendation"] == "watchlist"


def test_market_research_benchmark_blocks_high_risk_documented_reference():
    payload = [
        {
            "id": "auto-runtime-lab",
            "source_type": "explicit_payload",
            "source": "manual_payload",
            "focus_areas": ["continuous_review"],
            "benefit": "medium",
            "risk": "high",
            "fit": "low",
            "notes": ["runtime-heavy benchmark"],
            "risk_signals": ["auto_modifies_skills", "global_factory_surface_change"],
            "default_recommendation": "adapt_now"
        }
    ]

    result = build_market_research_benchmark(
        root=ROOT,
        topic="Review a runtime-heavy benchmark candidate.",
        reference_payload=payload,
    )

    blocked = next(item for item in result["blocked_references"] if item["reference_id"] == "auto-runtime-lab")
    assert blocked["recommendation"] == "watchlist"
    assert result["requires_decision_council"] is True


def test_market_research_benchmark_surfaces_low_risk_missing_capability_opportunity():
    payload = [
        {
            "id": "safe-visual-qa-notes",
            "source_type": "explicit_payload",
            "source": "manual_payload",
            "focus_areas": ["reference_benchmark_notes"],
            "benefit": "high",
            "risk": "low",
            "fit": "medium",
            "notes": ["manual benchmark payload"],
            "risk_signals": [],
            "default_recommendation": "adapt_now"
        }
    ]

    result = build_market_research_benchmark(
        root=ROOT,
        topic="Check if Atlas still lacks visual QA readiness.",
        reference_payload=payload,
    )

    assert any(item["atlas_capability"] == "reference_benchmark_notes" for item in result["prioritized_opportunities"])
    assert result["recommended_next_actions"]
