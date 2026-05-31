from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Dict, List, Optional

try:
    from tools.mcp_readiness_check import check_mcp_readiness
except ModuleNotFoundError:
    from mcp_readiness_check import check_mcp_readiness


DEFAULT_ROOT = Path(__file__).resolve().parents[1]
RULES_PATH = Path("config/chrome_devtools_mcp_rules.json")


def load_chrome_devtools_mcp_rules(root: Path = DEFAULT_ROOT) -> Dict[str, Any]:
    return json.loads((root / RULES_PATH).read_text(encoding="utf-8-sig"))


def _normalize(value: Any) -> str:
    return " ".join(str(value or "").strip().lower().split())


def _flatten_text(value: Any) -> List[str]:
    values: List[str] = []
    if isinstance(value, dict):
        for nested in value.values():
            values.extend(_flatten_text(nested))
    elif isinstance(value, list):
        for nested in value:
            values.extend(_flatten_text(nested))
    else:
        text = str(value or "").strip()
        if text:
            values.append(text)
    return values


def _detect_frontend_project(payload: Dict[str, Any], rules: Dict[str, Any], project: Path) -> bool:
    project_type = _normalize(payload.get("project_type"))
    if project_type in {_normalize(item) for item in rules.get("frontend_project_types", [])}:
        return True

    for candidate in (
        project / "package.json",
        project / "index.html",
        project / "src",
        project / "app",
        project / "public",
    ):
        if candidate.exists():
            return True
    return False


def _has_any_signal(surface: str, signals: List[str]) -> bool:
    normalized_surface = _normalize(surface)
    return any(_normalize(signal) in normalized_surface for signal in signals if str(signal).strip())


def _build_best_for_current_case(
    *,
    layout_debugging: bool,
    console_errors: bool,
    network: bool,
    performance: bool,
) -> List[str]:
    selected: List[str] = []
    if layout_debugging:
        selected.extend(["layout_debugging", "css_inspection"])
    if console_errors:
        selected.append("console_errors")
    if network:
        selected.append("network")
    if performance:
        selected.append("performance")
    return list(dict.fromkeys(selected))


def assess_chrome_devtools_mcp_readiness(
    payload: Dict[str, Any],
    *,
    root: Path = DEFAULT_ROOT,
    project: Optional[Path] = None,
) -> Dict[str, Any]:
    root = root.resolve()
    project = (project or root).resolve()
    rules = load_chrome_devtools_mcp_rules(root)
    mcp_readiness = check_mcp_readiness(root=root)

    frontend_project = _detect_frontend_project(payload, rules, project)
    surface = " ".join(_flatten_text(payload))

    visual_fidelity = payload.get("visual_fidelity_posture") or payload.get("visual_fidelity_review") or {}
    fidelity_state = _normalize(visual_fidelity.get("fidelity_state"))
    drift_states = {_normalize(item) for item in rules.get("drift_trigger_states", [])}
    visual_drift = fidelity_state in drift_states or bool(visual_fidelity.get("drift_signals"))
    screenshot_evidence_present = bool(visual_fidelity.get("screenshot_evidence_present"))
    screenshot_gap = screenshot_evidence_present and (
        bool(visual_fidelity.get("missing_viewports"))
        or bool(visual_fidelity.get("missing_compared_layers"))
        or not bool(visual_fidelity.get("can_support_visual_pass", False))
    )

    layout_debugging = _has_any_signal(surface, list(rules.get("layout_debug_signals", []))) or visual_drift
    console_errors = _has_any_signal(surface, list(rules.get("console_debug_signals", [])))
    network = _has_any_signal(surface, list(rules.get("network_debug_signals", [])))
    performance = _has_any_signal(surface, list(rules.get("performance_debug_signals", [])))

    symptom_count = sum(1 for item in (layout_debugging, console_errors, network, performance, screenshot_gap) if item)
    minimum_symptom_count = int((rules.get("recommendation_thresholds") or {}).get("minimum_symptom_count", 1))

    recommended = frontend_project and symptom_count >= minimum_symptom_count
    current_checks_sufficient = frontend_project and not recommended

    chrome_configured = bool(mcp_readiness.get("chrome_devtools_mcp_configured"))
    current_mcp_state = (
        "not_needed"
        if not recommended
        else "configured_manual_opt_in"
        if chrome_configured
        else "manual_setup_recommended"
    )

    best_for_current_case = _build_best_for_current_case(
        layout_debugging=layout_debugging or screenshot_gap,
        console_errors=console_errors,
        network=network,
        performance=performance,
    )

    manual_next_steps: List[str] = []
    if recommended:
        manual_next_steps.extend(list(rules.get("manual_setup_steps", [])))
        if not chrome_configured:
            manual_next_steps.append(
                "Chrome DevTools MCP is not configured locally, so keep this as readiness until manual setup is explicitly approved."
            )
        else:
            manual_next_steps.append(
                "Chrome DevTools MCP appears configured locally, but Atlas still requires explicit human approval before any real browser use."
            )
    else:
        manual_next_steps.append(
            "Current Atlas visual and design checks appear sufficient, so Chrome DevTools MCP is not recommended right now."
        )
    manual_next_steps = list(dict.fromkeys(step for step in manual_next_steps if step))

    risks = dict(rules.get("risks", {}))
    why: str
    if not frontend_project:
        why = "Chrome DevTools MCP readiness is only relevant for frontend or web surfaces."
    elif recommended:
        triggers: List[str] = []
        if visual_drift:
            triggers.append("visual drift against intended design")
        if screenshot_gap:
            triggers.append("screenshots exist but stronger browser-truth debugging is still missing")
        if layout_debugging and not visual_drift:
            triggers.append("layout/CSS/responsive symptoms")
        if console_errors:
            triggers.append("console or runtime symptoms")
        if network:
            triggers.append("network or request symptoms")
        if performance:
            triggers.append("performance symptoms")
        why = "Chrome DevTools MCP is recommended as a manual opt-in because Atlas detected " + ", ".join(triggers) + "."
    else:
        why = "Atlas does not see enough browser-only risk yet; current local checks appear sufficient for now."

    posture = {
        "recommended": recommended,
        "activation_mode": "manual_opt_in",
        "auto_activate": False,
        "mcp_configured": chrome_configured,
        "current_mcp_state": current_mcp_state,
        "best_for": list(rules.get("best_for", [])),
        "best_for_current_case": best_for_current_case,
        "requires_human_approval": True,
        "telemetry_risk": str(risks.get("telemetry_risk", "medium")),
        "browser_profile_risk": str(risks.get("browser_profile_risk", "medium")),
        "privacy_risk": str(risks.get("privacy_risk", "medium")),
        "recommended_flags": list(rules.get("recommended_flags", [])),
        "manual_setup_required": recommended and not chrome_configured,
        "symptoms": {
            "layout_css_responsive": layout_debugging,
            "visual_fidelity_drift": visual_drift,
            "console_errors": console_errors,
            "network": network,
            "performance": performance,
            "screenshots_need_browser_truth": screenshot_gap,
        },
        "current_checks_sufficient": current_checks_sufficient,
        "manual_next_steps": manual_next_steps,
        "why": why,
        "advisory_only": bool(rules.get("advisory_only", True)),
    }

    return {
        "status": "ok",
        "chrome_devtools_mcp_posture": posture,
        "frontend_project": frontend_project,
        "mcp_readiness_state": mcp_readiness.get("readiness_state"),
        "configured_mcp_servers": mcp_readiness.get("configured_mcp_servers", []),
        "advisory_only": bool(rules.get("advisory_only", True)),
    }


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(add_help=True)
    parser.add_argument("--project", default=None)
    parser.add_argument("--payload-json", default="{}")
    args = parser.parse_args(argv)

    project = Path(args.project).resolve() if args.project else DEFAULT_ROOT
    payload = json.loads(args.payload_json)
    result = assess_chrome_devtools_mcp_readiness(payload, root=DEFAULT_ROOT, project=project)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
