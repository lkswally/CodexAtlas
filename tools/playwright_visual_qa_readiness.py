from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional


DEFAULT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_RULES = {
    "version": "1.0",
    "advisory_only": True,
    "profiles": {},
}
SAFE_PROFILE_STATES = {"advisory", "approval_required"}
WATCHLIST_PROFILE_STATES = {"watchlist"}
PLAYWRIGHT_BROWSER_PREFIXES = ("chromium-", "firefox-", "webkit-", "ffmpeg-")


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _read_json(path: Path) -> Dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def _load_profiles(root: Path) -> Dict[str, Any]:
    path = root / "config" / "playwright_visual_qa_profiles.json"
    if not path.exists():
        return dict(DEFAULT_RULES)
    data = _read_json(path)
    if not isinstance(data, dict):
        return dict(DEFAULT_RULES)
    merged = dict(DEFAULT_RULES)
    merged.update(data)
    if not isinstance(merged.get("profiles"), dict):
        merged["profiles"] = {}
    return merged


def _probe_playwright_cli() -> Dict[str, Any]:
    try:
        result = subprocess.run(
            [sys.executable, "-m", "playwright", "--version"],
            capture_output=True,
            text=True,
            timeout=15,
            check=False,
        )
    except Exception as exc:
        return {
            "available": False,
            "returncode": None,
            "stdout": "",
            "stderr": str(exc),
        }

    return {
        "available": result.returncode == 0,
        "returncode": result.returncode,
        "stdout": (result.stdout or "").strip(),
        "stderr": (result.stderr or "").strip(),
    }


def _browser_dir_candidates() -> List[Path]:
    candidates: List[Path] = []
    custom = os.getenv("PLAYWRIGHT_BROWSERS_PATH", "").strip()
    if custom and custom != "0":
        candidates.append(Path(custom).expanduser())

    local_appdata = os.getenv("LOCALAPPDATA", "").strip()
    if local_appdata:
        candidates.append(Path(local_appdata) / "ms-playwright")

    user_profile = os.getenv("USERPROFILE", "").strip()
    if user_profile:
        candidates.append(Path(user_profile) / "AppData" / "Local" / "ms-playwright")

    unique: List[Path] = []
    seen: set[str] = set()
    for path in candidates:
        key = str(path).lower()
        if key not in seen:
            seen.add(key)
            unique.append(path)
    return unique


def _detect_browsers() -> Dict[str, Any]:
    checked_paths: List[str] = []
    detected_browsers: List[str] = []
    for base in _browser_dir_candidates():
        checked_paths.append(str(base))
        if not base.exists() or not base.is_dir():
            continue
        try:
            for child in base.iterdir():
                name = child.name.lower()
                if child.is_dir() and name.startswith(PLAYWRIGHT_BROWSER_PREFIXES):
                    detected_browsers.append(child.name)
        except OSError:
            continue

    detected_browsers = sorted(dict.fromkeys(detected_browsers))
    return {
        "available": bool(detected_browsers),
        "checked_paths": checked_paths,
        "detected_browsers": detected_browsers,
    }


def check_playwright_visual_qa_readiness(root: Optional[Path] = None) -> Dict[str, Any]:
    root = (root or DEFAULT_ROOT).resolve()
    rules = _load_profiles(root)
    cli_probe = _probe_playwright_cli()
    browser_probe = _detect_browsers()

    playwright_available = bool(cli_probe.get("available"))
    browsers_available = bool(browser_probe.get("available"))
    safe_to_run = playwright_available and browsers_available

    blocked_profiles: List[Dict[str, Any]] = []
    watchlist_profiles: List[Dict[str, Any]] = []
    required_manual_steps: List[str] = []
    risks: List[str] = [
        "visual_false_positive_risk",
        "hung_browser_process_risk",
        "screenshot_environment_drift_risk",
        "responsive_breakpoint_noise_risk",
        "visual_qa_is_not_brand_or_intent_proof",
    ]
    requires_human_approval = False
    requires_decision_council = False

    for profile_id, profile in rules.get("profiles", {}).items():
        if not isinstance(profile, dict):
            continue
        profile_name = str(profile_id)
        initial_state = str(profile.get("initial_state", "watchlist")).strip() or "watchlist"
        risk_level = str(profile.get("risk_level", "medium")).strip() or "medium"
        payload = {
            "profile": profile_name,
            "requirements": list(profile.get("requirements", [])),
            "risk_level": risk_level,
            "initial_state": initial_state,
            "requires_human_approval": bool(profile.get("requires_human_approval", True)),
            "fallback": str(profile.get("fallback", "")).strip(),
        }
        if payload["requires_human_approval"]:
            requires_human_approval = True
        if risk_level == "high":
            requires_decision_council = True

        if initial_state in WATCHLIST_PROFILE_STATES:
            payload["why"] = (
                "This profile stays on watchlist until Atlas has explicit approval, a stable baseline and a concrete need for browser-driven evidence."
            )
            watchlist_profiles.append(payload)
            continue

        if safe_to_run and initial_state in SAFE_PROFILE_STATES:
            continue

        reasons: List[str] = []
        if not playwright_available:
            reasons.append("playwright_not_available")
        if playwright_available and not browsers_available:
            reasons.append("browsers_not_available")
        payload["why"] = (
            "Atlas cannot mark this visual-QA profile ready because the Playwright runtime or browser binaries are not locally verifiable yet."
        )
        payload["blockers"] = reasons
        blocked_profiles.append(payload)

    if not playwright_available:
        required_manual_steps.append(
            "Install Playwright manually only after approval, then verify with `python -m playwright --version`."
        )
    if playwright_available and not browsers_available:
        required_manual_steps.append(
            "Install Playwright browsers manually only after approval, then re-check local browser caches."
        )
    required_manual_steps.append(
        "Keep `visual_intent_contract`, `brand_profile_schema` and `ui_pre_return_audit` as the primary readiness chain before any screenshot-based QA."
    )
    required_manual_steps.append(
        "Treat `component_inspiration_readiness` and `creative_pipeline_readiness` as separate readiness layers; they do not prove visual QA safety."
    )
    required_manual_steps = list(dict.fromkeys(required_manual_steps))

    status = "ok" if safe_to_run else "needs_attention"
    recommended_next_action = (
        "Keep visual QA approval-bound and use it only after the local design chain is explicit."
        if safe_to_run
        else "Stay with local design audits until Playwright and browser binaries are manually approved and locally verifiable."
    )

    return {
        "status": status,
        "playwright_available": playwright_available,
        "browsers_available": browsers_available,
        "safe_to_run": safe_to_run,
        "blocked_profiles": blocked_profiles,
        "watchlist_profiles": watchlist_profiles,
        "required_manual_steps": required_manual_steps,
        "recommended_next_action": recommended_next_action,
        "risks": risks,
        "requires_human_approval": requires_human_approval,
        "requires_decision_council": requires_decision_council,
        "why": "Playwright visual-QA readiness is derived only from local CLI detection, local browser-cache inspection and governed profile metadata.",
        "advisory_only": bool(rules.get("advisory_only", True)),
        "timestamp": _utc_now_iso(),
    }


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(add_help=True)
    parser.add_argument("--root", default=None, help="Atlas root to use.")
    args = parser.parse_args(argv)
    root = Path(args.root).resolve() if args.root else DEFAULT_ROOT
    result = check_playwright_visual_qa_readiness(root=root)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
