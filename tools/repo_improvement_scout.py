from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional


DEFAULT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_REFERENCE = DEFAULT_ROOT / "_reference" / "claude-vibecoding"
REFERENCE_SENTINELS = ("README.md", "CLAUDE.md", "UPGRADE_LOG.md", "agents", "docs")
REFERENCE_MATRIX = [
    {
        "component_original": "Intent Clarifier",
        "purpose": "Make task understanding explicit before execution.",
        "claude_dependency": "low",
        "equivalent_codex_atlas": "project_intent_analyzer + prompt_builder",
        "benefit": "high",
        "effort": "low",
        "risk": "low",
        "fit": "high",
        "requires_mcp": False,
        "requires_hooks": False,
        "requires_external_dependencies": False,
        "recommendation": "adaptar ahora"
    },
    {
        "component_original": "Evidence Collector + Reality Checker",
        "purpose": "Keep recommendations tied to evidence and readiness gates.",
        "claude_dependency": "low",
        "equivalent_codex_atlas": "design_intelligence_audit + quality_gate_report + error_pattern_analyzer",
        "benefit": "high",
        "effort": "low",
        "risk": "low",
        "fit": "high",
        "requires_mcp": False,
        "requires_hooks": False,
        "requires_external_dependencies": False,
        "recommendation": "adaptar ahora"
    },
    {
        "component_original": "Readiness before handoff",
        "purpose": "Aggregate checks into a single decision gate.",
        "claude_dependency": "low",
        "equivalent_codex_atlas": "quality_gate_report + project_phase_resolver",
        "benefit": "high",
        "effort": "low",
        "risk": "low",
        "fit": "high",
        "requires_mcp": False,
        "requires_hooks": False,
        "requires_external_dependencies": False,
        "recommendation": "adaptar ahora"
    },
    {
        "component_original": "Light boot / full boot context discipline",
        "purpose": "Load only the depth of context that a task actually needs.",
        "claude_dependency": "medium",
        "equivalent_codex_atlas": "model_router + prompt_builder + phase guidance",
        "benefit": "medium",
        "effort": "medium",
        "risk": "low",
        "fit": "high",
        "requires_mcp": False,
        "requires_hooks": False,
        "requires_external_dependencies": False,
        "recommendation": "diseñar después"
    },
    {
        "component_original": "design-data",
        "purpose": "Use a richer local taste/reference base for design work.",
        "claude_dependency": "low",
        "equivalent_codex_atlas": "possible future local design dataset",
        "benefit": "medium",
        "effort": "medium",
        "risk": "medium",
        "fit": "medium",
        "requires_mcp": False,
        "requires_hooks": False,
        "requires_external_dependencies": False,
        "recommendation": "watchlist"
    },
    {
        "component_original": "Hooks / auto runtime guards",
        "purpose": "Automate checks before and after actions.",
        "claude_dependency": "high",
        "equivalent_codex_atlas": "none by design",
        "benefit": "low",
        "effort": "medium",
        "risk": "high",
        "fit": "low",
        "requires_mcp": False,
        "requires_hooks": True,
        "requires_external_dependencies": False,
        "recommendation": "descartar"
    },
    {
        "component_original": "Pixel Bridge / Playwright MCP / browser automation",
        "purpose": "Visual QA with real rendering and browser evidence.",
        "claude_dependency": "high",
        "equivalent_codex_atlas": "none in current safe scope",
        "benefit": "medium",
        "effort": "high",
        "risk": "high",
        "fit": "low",
        "requires_mcp": True,
        "requires_hooks": False,
        "requires_external_dependencies": True,
        "recommendation": "descartar"
    }
]


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def scout_reference_repo(*, source: Optional[Path] = None) -> Dict[str, Any]:
    reference_root = (source or DEFAULT_REFERENCE).resolve()
    if not reference_root.exists():
        return {
            "status": "needs_reference",
            "source": str(reference_root),
            "reason": "reference_local_clone_missing",
            "recommendation": "Clone or refresh `_reference/claude-vibecoding` before using the improvement scout.",
            "timestamp": _utc_now_iso(),
        }

    missing = [name for name in REFERENCE_SENTINELS if not (reference_root / name).exists()]
    if missing:
        return {
            "status": "needs_reference",
            "source": str(reference_root),
            "reason": "reference_surface_incomplete",
            "missing": missing,
            "recommendation": "Refresh the local reference clone before trusting the improvement matrix.",
            "timestamp": _utc_now_iso(),
        }

    summary = {
        "adaptar_ahora": sum(1 for item in REFERENCE_MATRIX if item["recommendation"] == "adaptar ahora"),
        "diseñar_despues": sum(1 for item in REFERENCE_MATRIX if item["recommendation"] == "diseñar después"),
        "watchlist": sum(1 for item in REFERENCE_MATRIX if item["recommendation"] == "watchlist"),
        "descartar": sum(1 for item in REFERENCE_MATRIX if item["recommendation"] == "descartar"),
    }

    return {
        "status": "ok",
        "source": str(reference_root),
        "patterns": REFERENCE_MATRIX,
        "summary": summary,
        "recommended_next_move": "Keep adapting evidence-driven and readiness-gated patterns before any runtime-heavy Claude-only capability.",
        "timestamp": _utc_now_iso(),
    }


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(add_help=True)
    parser.add_argument("--source", default=None, help="Optional local reference repo path.")
    args = parser.parse_args(argv)

    source = Path(args.source).resolve() if args.source else None
    result = scout_reference_repo(source=source)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
