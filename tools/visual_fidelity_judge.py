from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple


DEFAULT_ROOT = Path(__file__).resolve().parents[1]
RULES_PATH = Path("config/visual_fidelity_judge_rules.json")
IMAGE_SUFFIXES = {".png", ".jpg", ".jpeg", ".webp"}


def load_visual_fidelity_judge_rules(root: Path = DEFAULT_ROOT) -> Dict[str, Any]:
    return json.loads((root / RULES_PATH).read_text(encoding="utf-8-sig"))


def _normalize(value: Any) -> str:
    return " ".join(str(value or "").strip().lower().split())


def _normalize_list(items: Any) -> List[str]:
    if not isinstance(items, list):
        return []
    normalized: List[str] = []
    seen: set[str] = set()
    for item in items:
        value = _normalize(item)
        if value and value not in seen:
            seen.add(value)
            normalized.append(value)
    return normalized


def _string_list(items: Any) -> List[str]:
    if not isinstance(items, list):
        return []
    values: List[str] = []
    for item in items:
        text = str(item).strip()
        if text:
            values.append(text)
    return values


def _load_structured_report(project: Path, rules: Dict[str, Any], payload: Dict[str, Any]) -> Tuple[Optional[Path], Optional[Dict[str, Any]], Optional[str]]:
    explicit_report = payload.get("visual_fidelity_report")
    if isinstance(explicit_report, dict):
        return None, explicit_report, None

    for relative in rules.get("candidate_report_paths", []):
        candidate = project / str(relative)
        if not candidate.exists() or not candidate.is_file():
            continue
        try:
            loaded = json.loads(candidate.read_text(encoding="utf-8-sig"))
        except Exception as exc:  # pragma: no cover - defensive malformed JSON guard.
            return candidate, None, f"invalid_json:{exc}"
        if isinstance(loaded, dict):
            return candidate, loaded, None
        return candidate, None, "report_not_object"
    return None, None, None


def _collect_viewports_from_report(report: Dict[str, Any], project: Path) -> Tuple[List[str], List[str]]:
    provided: List[str] = []
    referenced_files: List[str] = []

    for key in ("provided_viewports", "viewports"):
        for viewport in _normalize_list(report.get(key)):
            if viewport not in provided:
                provided.append(viewport)

    screenshots = report.get("screenshots")
    if isinstance(screenshots, list):
        for item in screenshots:
            if isinstance(item, str):
                candidate = project / item
                if candidate.exists():
                    referenced_files.append(str(candidate))
            elif isinstance(item, dict):
                viewport = _normalize(item.get("viewport"))
                path_value = str(item.get("path", "")).strip()
                if viewport and viewport not in provided:
                    provided.append(viewport)
                if path_value:
                    candidate = (project / path_value).resolve() if not Path(path_value).is_absolute() else Path(path_value)
                    if candidate.exists():
                        referenced_files.append(str(candidate))
    return provided, referenced_files


def _discover_screenshot_viewports(project: Path, rules: Dict[str, Any]) -> Tuple[List[str], List[str]]:
    found_viewports: List[str] = []
    found_files: List[str] = []
    token_map = {
        _normalize(key): [str(token).strip().lower() for token in values if str(token).strip()]
        for key, values in (rules.get("viewport_filename_tokens") or {}).items()
        if isinstance(values, list)
    }

    for relative in rules.get("candidate_screenshot_dirs", []):
        base = project / str(relative)
        if not base.exists() or not base.is_dir():
            continue
        for child in base.rglob("*"):
            if not child.is_file() or child.suffix.lower() not in IMAGE_SUFFIXES:
                continue
            lower_name = child.name.lower()
            found_files.append(str(child))
            for viewport, tokens in token_map.items():
                if viewport in found_viewports:
                    continue
                if any(token in lower_name for token in tokens):
                    found_viewports.append(viewport)
    return found_viewports, found_files


def _required_compared_layers(payload: Dict[str, Any], rules: Dict[str, Any]) -> List[str]:
    required: List[str] = []
    for layer_name, payload_key in (
        ("visual_intent_contract", "visual_intent_contract_review"),
        ("brand_profile", "brand_profile_review"),
    ):
        review = payload.get(payload_key)
        if not isinstance(review, dict):
            continue
        status = _normalize(review.get("status"))
        if layer_name in rules.get("core_compared_layers", []) and status in {"ready", "pass", "pass_ready", "needs_input"}:
            required.append(layer_name)
    return required


def assess_visual_fidelity_judge(
    payload: Dict[str, Any],
    *,
    root: Path = DEFAULT_ROOT,
    project: Optional[Path] = None,
) -> Dict[str, Any]:
    root = root.resolve()
    project = (project or root).resolve()
    rules = load_visual_fidelity_judge_rules(root)

    project_type = str(payload.get("project_type", "")).strip() or "unknown"
    if project_type not in {str(item).strip() for item in rules.get("frontend_project_types", [])}:
        return {
            "status": "ok",
            "fidelity_state": "not_applicable",
            "report_detected": False,
            "report_path": None,
            "screenshot_evidence_present": False,
            "required_viewports": [],
            "provided_viewports": [],
            "missing_viewports": [],
            "compared_layers": [],
            "missing_compared_layers": [],
            "matched_signals": [],
            "drift_signals": [],
            "confidence": "low",
            "can_support_visual_pass": False,
            "must_not_claim_visual_pass_without_evidence": True,
            "manual_next_steps": [],
            "why": "Visual fidelity judgment is only relevant for frontend-oriented projects.",
            "advisory_only": bool(rules.get("advisory_only", True)),
        }

    report_path, report, report_error = _load_structured_report(project, rules, payload)
    report_detected = report_path is not None or isinstance(report, dict)

    report_viewports, report_files = _collect_viewports_from_report(report or {}, project)
    discovered_viewports, discovered_files = _discover_screenshot_viewports(project, rules)
    declared_evidence = {_normalize(item) for item in payload.get("provided_evidence", []) if str(item).strip()}
    declared_viewports: List[str] = []
    if "screenshot_desktop" in declared_evidence:
        declared_viewports.append("desktop")
    if "screenshot_mobile" in declared_evidence:
        declared_viewports.append("mobile")
    provided_viewports = list(dict.fromkeys([*report_viewports, *discovered_viewports, *declared_viewports]))
    required_viewports = [str(item).strip().lower() for item in rules.get("required_viewports", []) if str(item).strip()]
    missing_viewports = [viewport for viewport in required_viewports if viewport not in provided_viewports]

    compared_layers = _normalize_list((report or {}).get("compared_layers"))
    required_layers = _required_compared_layers(payload, rules)
    missing_compared_layers = [layer for layer in required_layers if layer not in compared_layers]

    matched_signals = _string_list((report or {}).get("matched_signals"))
    drift_signals = _string_list((report or {}).get("drift_signals"))
    signal_count = len(matched_signals) + len(drift_signals)
    minimum_signal_count = int(rules.get("minimum_signal_count", 2))
    summary_text = str((report or {}).get("judge_summary") or (report or {}).get("summary") or "").strip()

    screenshot_evidence_present = bool(provided_viewports or report_files or discovered_files)

    fidelity_state = "insufficient_evidence"
    if report_error:
        fidelity_state = "blocked"
    elif drift_signals and not missing_viewports and not missing_compared_layers:
        fidelity_state = "drift_detected"
    elif (
        screenshot_evidence_present
        and report_detected
        and summary_text
        and not missing_viewports
        and not missing_compared_layers
        and signal_count >= minimum_signal_count
    ):
        fidelity_state = "aligned"

    can_support_visual_pass = fidelity_state == "aligned"
    if fidelity_state == "aligned":
        confidence = "high"
    elif fidelity_state == "drift_detected":
        confidence = "medium"
    else:
        confidence = "low"

    manual_next_steps: List[str] = []
    if fidelity_state == "blocked":
        manual_next_steps.append("Repair the visual fidelity report JSON before using it as evidence.")
    if missing_viewports:
        manual_next_steps.append(
            f"Capture or document screenshot evidence for: {', '.join(missing_viewports)}."
        )
    if screenshot_evidence_present and not report_detected:
        manual_next_steps.append(
            "Add a structured visual_fidelity_report.json comparing screenshots against the visual intent and brand profile."
        )
    if report_detected and missing_compared_layers:
        manual_next_steps.append(
            f"Extend the visual fidelity report to compare: {', '.join(missing_compared_layers)}."
        )
    if report_detected and not summary_text:
        manual_next_steps.append("Add a short judge_summary describing whether the screenshots align with the intended visual system.")
    if report_detected and signal_count < minimum_signal_count:
        manual_next_steps.append("Document at least two concrete matched or drift signals so the judgment is auditable.")
    if fidelity_state == "drift_detected":
        manual_next_steps.append("Resolve the reported visual drift before claiming a strong frontend PASS.")
    manual_next_steps = list(dict.fromkeys(step for step in manual_next_steps if step))

    if fidelity_state == "aligned":
        why = "Atlas found screenshot coverage plus a structured screenshot-versus-intent comparison strong enough to support a visual PASS."
    elif fidelity_state == "drift_detected":
        why = "Screenshot evidence exists, but the structured comparison found relevant visual drift against the intended spec or brand system."
    elif fidelity_state == "blocked":
        why = "A visual fidelity artifact exists, but Atlas cannot trust it because the report is malformed."
    else:
        why = "Atlas still lacks enough screenshot-backed comparison evidence to judge visual fidelity confidently."

    return {
        "status": "ok" if fidelity_state in {"aligned", "not_applicable"} else "needs_attention",
        "fidelity_state": fidelity_state,
        "report_detected": report_detected,
        "report_path": str(report_path) if report_path else None,
        "report_error": report_error,
        "screenshot_evidence_present": screenshot_evidence_present,
        "required_viewports": required_viewports,
        "provided_viewports": provided_viewports,
        "missing_viewports": missing_viewports,
        "compared_layers": compared_layers,
        "missing_compared_layers": missing_compared_layers,
        "matched_signals": matched_signals,
        "drift_signals": drift_signals,
        "confidence": confidence,
        "can_support_visual_pass": can_support_visual_pass,
        "must_not_claim_visual_pass_without_evidence": True,
        "manual_next_steps": manual_next_steps,
        "why": why,
        "advisory_only": bool(rules.get("advisory_only", True)),
    }


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(add_help=True)
    parser.add_argument("--project", default=None)
    parser.add_argument("--payload-json", default="{}")
    args = parser.parse_args(argv)

    project = Path(args.project).resolve() if args.project else DEFAULT_ROOT
    payload = json.loads(args.payload_json)
    result = assess_visual_fidelity_judge(payload, root=DEFAULT_ROOT, project=project)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
