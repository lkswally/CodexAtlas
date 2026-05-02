from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional


DEFAULT_ROOT = Path(__file__).resolve().parents[1]
ROUTING_LOG_PATH = Path("memory") / "routing_log.jsonl"
GOVERNANCE_LOG_PATH = Path("memory") / "governance_events.jsonl"
MCP_LOG_PATH = Path("memory") / "mcp_events.jsonl"
DECISION_FEEDBACK_PATH = Path("memory") / "decision_feedback.jsonl"


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _iter_jsonl(path: Path) -> Iterable[Dict[str, Any]]:
    if not path.exists():
        return []

    def _generator() -> Iterable[Dict[str, Any]]:
        for raw_line in path.read_text(encoding="utf-8-sig").splitlines():
            line = raw_line.strip()
            if not line:
                continue
            try:
                record = json.loads(line)
            except Exception:
                continue
            if isinstance(record, dict):
                yield record

    return _generator()


def _append_pattern(patterns: List[Dict[str, Any]], pattern: str, impact: str, recommendation: str, evidence: List[str], severity: str) -> None:
    patterns.append(
        {
            "pattern": pattern,
            "impact": impact,
            "recommendation": recommendation,
            "evidence": evidence[:4],
            "severity": severity,
        }
    )


def analyze_error_patterns(*, root: Path, project: Optional[Path] = None) -> Dict[str, Any]:
    root = root.resolve()
    project = project.resolve() if project is not None else None
    project_path = str(project) if project is not None else None

    patterns: List[Dict[str, Any]] = []

    routing_entries = list(_iter_jsonl(root / ROUTING_LOG_PATH))
    if project_path:
        routing_entries = [entry for entry in routing_entries if str(entry.get("project", "")).strip() in {"", project_path}]

    failed_dispatch: Dict[str, int] = {}
    for entry in routing_entries:
        if str(entry.get("event_type", "")).strip() != "dispatcher_command":
            continue
        if bool(entry.get("ok")):
            continue
        command_id = str(entry.get("command_id", "")).strip() or "unknown_command"
        failed_dispatch[command_id] = failed_dispatch.get(command_id, 0) + 1

    for command_id, count in sorted(failed_dispatch.items()):
        if count < 2:
            continue
        _append_pattern(
            patterns,
            pattern=f"Command `{command_id}` is failing repeatedly.",
            impact="Atlas is spending time on a route that is already known to fail or block.",
            recommendation=f"Review `{command_id}` gating or prompt guidance before surfacing it again in the same context.",
            evidence=[f"failed_dispatch_count={count}"],
            severity="medium",
        )

    feedback_entries = list(_iter_jsonl(root / DECISION_FEEDBACK_PATH))
    if project_path:
        feedback_entries = [entry for entry in feedback_entries if str(entry.get("project_path", "")).strip() == project_path]

    feedback_by_action: Dict[str, List[Dict[str, Any]]] = {}
    for entry in feedback_entries:
        action = str(entry.get("action", "")).strip()
        if not action:
            continue
        feedback_by_action.setdefault(action, []).append(entry)

    for action, entries in sorted(feedback_by_action.items()):
        ignored = [entry for entry in entries if str(entry.get("decision", "")).strip() == "ignored"]
        replaced = [entry for entry in entries if str(entry.get("decision", "")).strip() == "replaced"]
        if len(ignored) >= 2:
            _append_pattern(
                patterns,
                pattern=f"Action `{action}` is repeatedly ignored.",
                impact="This recommendation is likely noise for the current workflow and can lower trust in the gate output.",
                recommendation="Lower its ranking or replace it with a more actionable next step when stronger evidence exists.",
                evidence=[f"ignored_count={len(ignored)}", f"feedback_count={len(entries)}"],
                severity="medium",
            )
        if len(replaced) >= 2:
            _append_pattern(
                patterns,
                pattern=f"Action `{action}` is often replaced by a different decision.",
                impact="Atlas may be proposing a generic step where the user already has a better alternative pattern.",
                recommendation="Capture the replacement rationale and tighten the recommendation wording for that action family.",
                evidence=[f"replaced_count={len(replaced)}"],
                severity="low",
            )

    mcp_entries = list(_iter_jsonl(root / MCP_LOG_PATH))
    blocked_mcp = [entry for entry in mcp_entries if str(entry.get("state", "")).strip() == "blocked"]
    access_denied = [
        entry for entry in mcp_entries
        if "access is denied" in str(entry.get("runtime_support", {}).get("cli_error", "")).lower()
        or "access is denied" in str(entry.get("cli_error", "")).lower()
    ]
    if len(blocked_mcp) >= 2:
        _append_pattern(
            patterns,
            pattern="MCP requests keep hitting blocked lifecycle states.",
            impact="Atlas is surfacing external-context paths that the environment or policy still cannot execute.",
            recommendation="Keep adapter fallbacks explicit and avoid suggesting real MCP activation until readiness changes.",
            evidence=[f"blocked_mcp_events={len(blocked_mcp)}"],
            severity="medium",
        )
    if access_denied:
        _append_pattern(
            patterns,
            pattern="Codex MCP runtime is still failing with Access is denied.",
            impact="Real MCP activation is not currently safe to configure on this machine.",
            recommendation="Do not touch `~/.codex/config.toml`; keep `docs_search_adapter` as the only safe fallback.",
            evidence=["codex_cli_error=Access is denied", f"access_denied_events={len(access_denied)}"],
            severity="high",
        )

    governance_entries = list(_iter_jsonl(root / GOVERNANCE_LOG_PATH))
    failed_governance = [entry for entry in governance_entries if not bool(entry.get("ok"))]
    if len(failed_governance) >= 2:
        _append_pattern(
            patterns,
            pattern="Governance failures recur before execution.",
            impact="Atlas may be drifting between documented contract and executable surface.",
            recommendation="Review governance findings before expanding capabilities or changing registries.",
            evidence=[f"failed_governance_events={len(failed_governance)}"],
            severity="medium",
        )

    severity = "low"
    if any(item["severity"] == "high" for item in patterns):
        severity = "high"
    elif any(item["severity"] == "medium" for item in patterns):
        severity = "medium"

    if patterns:
        suggested_system_improvement = patterns[0]["recommendation"]
        evidence = [f"{item['pattern']} :: {item['evidence'][0]}" for item in patterns if item.get("evidence")]
    else:
        suggested_system_improvement = "No repeated error pattern is strong enough yet to justify a system change."
        evidence = ["no_recurrent_error_pattern_detected"]

    return {
        "status": "ok",
        "project_path": project_path,
        "patterns": patterns,
        "severity": severity,
        "suggested_system_improvement": suggested_system_improvement,
        "evidence": evidence[:6],
        "should_create_issue": False,
        "timestamp": _utc_now_iso(),
    }


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(add_help=True)
    parser.add_argument("--root", default=None, help="Atlas root to use.")
    parser.add_argument("--project", default=None, help="Optional project path to scope the analysis.")
    args = parser.parse_args(argv)

    root = Path(args.root).resolve() if args.root else DEFAULT_ROOT
    project = Path(args.project).resolve() if args.project else None
    result = analyze_error_patterns(root=root, project=project)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
