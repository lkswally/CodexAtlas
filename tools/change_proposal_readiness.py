from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Dict, List, Optional


DEFAULT_ROOT = Path(__file__).resolve().parents[1]
RULES_PATH = Path("config/change_proposal_rules.json")


def load_change_proposal_rules(root: Path = DEFAULT_ROOT) -> Dict[str, Any]:
    return json.loads((root / RULES_PATH).read_text(encoding="utf-8-sig"))


def _normalize_list(items: Any) -> List[str]:
    if not isinstance(items, list):
        return []
    normalized: List[str] = []
    for item in items:
        value = str(item).strip()
        if value and value not in normalized:
            normalized.append(value)
    return normalized


def _artifact_section_names(value: Any) -> List[str]:
    if isinstance(value, dict):
        return [str(key).strip() for key, item in value.items() if str(key).strip() and item not in (None, "", [], {})]
    if isinstance(value, list):
        return _normalize_list(value)
    return []


def _infer_change_size(payload: Dict[str, Any]) -> str:
    explicit = str(payload.get("change_size", "")).strip().lower()
    if explicit:
        return explicit
    complexity = str(payload.get("complexity", "")).strip().lower()
    return {
        "high": "large",
        "medium": "medium",
        "low": "small",
    }.get(complexity, "small")


def _requires_change_proposal(payload: Dict[str, Any], rules: Dict[str, Any]) -> bool:
    required_when = rules.get("required_when") or {}
    change_size = _infer_change_size(payload)
    risk_level = str(payload.get("risk_level", "")).strip().lower()

    if change_size in set(_normalize_list(required_when.get("change_sizes"))):
        return True
    if risk_level in set(_normalize_list(required_when.get("risk_levels"))):
        return True

    for flag_name in _normalize_list(required_when.get("change_flags")):
        if bool(payload.get(flag_name)):
            return True
    return False


def assess_change_proposal_readiness(
    payload: Dict[str, Any],
    *,
    root: Path = DEFAULT_ROOT,
) -> Dict[str, Any]:
    rules = load_change_proposal_rules(root)
    advisory_only = bool(rules.get("advisory_only", True))
    required = _requires_change_proposal(payload, rules)
    change_size = _infer_change_size(payload)
    required_artifacts = _normalize_list(rules.get("required_artifacts"))

    if not required:
        return {
            "status": "not_required",
            "required": False,
            "change_size": change_size,
            "provided_artifacts": [],
            "missing_artifacts": [],
            "missing_sections": {},
            "artifact_statuses": {},
            "manual_next_steps": [],
            "why": "Atlas only requires this workflow for medium or large changes, high-risk work, or explicit governance, contract or architecture shifts.",
            "advisory_only": advisory_only,
        }

    provided_artifact_map = payload.get("provided_artifacts")
    if not isinstance(provided_artifact_map, dict):
        provided_artifact_map = {}

    provided_artifacts: List[str] = []
    missing_artifacts: List[str] = []
    missing_sections: Dict[str, List[str]] = {}
    artifact_statuses: Dict[str, str] = {}

    artifact_requirements = rules.get("artifact_requirements") or {}

    for artifact_name in required_artifacts:
        artifact_rules = artifact_requirements.get(artifact_name) or {}
        required_fields = _normalize_list(artifact_rules.get("required_fields"))
        present_sections = _artifact_section_names(provided_artifact_map.get(artifact_name))

        if artifact_name in provided_artifact_map:
            provided_artifacts.append(artifact_name)

        missing_for_artifact = [field for field in required_fields if field not in present_sections]
        if artifact_name not in provided_artifact_map:
            missing_artifacts.append(artifact_name)
            missing_sections[artifact_name] = required_fields
            artifact_statuses[artifact_name] = "missing"
        elif missing_for_artifact:
            missing_sections[artifact_name] = missing_for_artifact
            artifact_statuses[artifact_name] = "partial"
        else:
            artifact_statuses[artifact_name] = "ready"

    if not provided_artifacts:
        status = "missing"
    elif missing_artifacts or missing_sections:
        status = "partial"
    else:
        status = "ready"

    manual_next_steps: List[str] = []
    if missing_artifacts:
        manual_next_steps.append(
            f"Create the missing artifacts before implementation: {', '.join(missing_artifacts)}."
        )
    for artifact_name, fields in missing_sections.items():
        if artifact_name not in missing_artifacts and fields:
            manual_next_steps.append(
                f"Complete `{artifact_name}` with: {', '.join(fields)}."
            )
    if str(payload.get("risk_level", "")).strip().lower() == "high":
        manual_next_steps.append(
            "Keep human approval explicit before implementation because the change is high-risk."
        )
    manual_next_steps = list(dict.fromkeys(manual_next_steps))

    return {
        "status": status,
        "required": True,
        "change_size": change_size,
        "provided_artifacts": provided_artifacts,
        "missing_artifacts": missing_artifacts,
        "missing_sections": missing_sections,
        "artifact_statuses": artifact_statuses,
        "manual_next_steps": manual_next_steps,
        "why": "Atlas uses this workflow to make medium and large changes reviewable before implementation, instead of relying on implicit scope, hidden design assumptions or informal task memory.",
        "advisory_only": advisory_only,
    }


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(add_help=True)
    parser.add_argument("--payload-json", required=True)
    args = parser.parse_args(argv)
    payload = json.loads(args.payload_json)
    result = assess_change_proposal_readiness(payload, root=DEFAULT_ROOT)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
