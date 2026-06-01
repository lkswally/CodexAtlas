from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional


DEFAULT_ROOT = Path(__file__).resolve().parents[1]
RULES_PATH = Path("config/n8n_automation_readiness_rules.json")


def load_n8n_automation_readiness_rules(root: Path = DEFAULT_ROOT) -> Dict[str, Any]:
    return json.loads((root / RULES_PATH).read_text(encoding="utf-8-sig"))


def _normalize(value: Any) -> str:
    return " ".join(str(value or "").strip().lower().split())


def _has_value(value: Any) -> bool:
    if value is None:
        return False
    if isinstance(value, str):
        return bool(value.strip())
    if isinstance(value, (list, tuple, set, dict)):
        return bool(value)
    return True


def _stringify(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, str):
        return value.strip()
    if isinstance(value, (list, tuple, set)):
        return ", ".join(str(item).strip() for item in value if str(item).strip())
    if isinstance(value, dict):
        return ", ".join(f"{key}: {value[key]}" for key in value if str(value[key]).strip())
    return str(value).strip()


def _listify(value: Any) -> List[str]:
    if isinstance(value, list):
        return [str(item).strip() for item in value if str(item).strip()]
    if isinstance(value, tuple):
        return [str(item).strip() for item in value if str(item).strip()]
    text = _stringify(value)
    if not text:
        return []
    return [part.strip() for part in re.split(r"[,|\n]+", text) if part.strip()]


def _extract_inputs(payload: Dict[str, Any], rules: Dict[str, Any]) -> Dict[str, Any]:
    aliases = rules.get("input_aliases", {})
    extracted: Dict[str, Any] = {}
    for canonical in aliases:
        candidates = [canonical, *list(aliases.get(canonical, []))]
        for name in candidates:
            value = payload.get(name)
            if _has_value(value):
                extracted[canonical] = value
                break
    if _has_value(payload.get("project_type")):
        extracted["project_type"] = payload.get("project_type")
    return extracted


def _candidate_files(project: Path, rules: Dict[str, Any]) -> List[Path]:
    ordered: List[Path] = []
    seen: set[Path] = set()
    for relative in rules.get("project_scan_files", []):
        candidate = project / str(relative)
        if candidate.exists() and candidate.is_file() and candidate not in seen:
            seen.add(candidate)
            ordered.append(candidate)
    for pattern in ("*.json", "docs/*.json", "*.md", "docs/*.md"):
        for candidate in sorted(project.glob(pattern)):
            if candidate.is_file() and candidate not in seen:
                seen.add(candidate)
                ordered.append(candidate)
    return ordered[:16]


def _read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        return path.read_text(encoding="latin-1")


def _parse_workflow_json(raw_text: str) -> Optional[Dict[str, Any]]:
    try:
        payload = json.loads(raw_text)
    except Exception:
        return None
    if isinstance(payload, dict):
        if isinstance(payload.get("nodes"), list):
            return payload
        if isinstance(payload.get("workflow"), dict) and isinstance(payload["workflow"].get("nodes"), list):
            return payload["workflow"]
    return None


def _scan_project_for_workflow(project: Path, rules: Dict[str, Any]) -> Dict[str, Any]:
    files = _candidate_files(project, rules)
    workflow_payload: Optional[Dict[str, Any]] = None
    source_files: List[str] = []
    blueprint_text_parts: List[str] = []

    for path in files:
        source_files.append(str(path.relative_to(project)).replace("\\", "/"))
        raw_text = _read_text(path)
        if path.suffix.lower() == ".json" and workflow_payload is None:
            workflow_payload = _parse_workflow_json(raw_text)
        if path.suffix.lower() in {".md", ".json"}:
            compact = re.sub(r"\s+", " ", raw_text).strip()
            if compact:
                blueprint_text_parts.append(compact[:4000])

    return {
        "workflow_json": workflow_payload,
        "source_files": source_files,
        "blueprint_text": " ".join(blueprint_text_parts)[:12000],
    }


def _node_type(node: Dict[str, Any]) -> str:
    return _stringify(node.get("type") or node.get("name") or node.get("nodeType"))


def _contains_any(surface: str, signals: Iterable[str]) -> List[str]:
    normalized_surface = _normalize(surface)
    matches: List[str] = []
    for signal in signals:
        cleaned = str(signal).strip()
        if cleaned and _normalize(cleaned) in normalized_surface:
            matches.append(cleaned)
    return matches


def _collect_nodes(extracted: Dict[str, Any], scanned: Dict[str, Any]) -> List[Dict[str, Any]]:
    value = extracted.get("nodes")
    if isinstance(value, list):
        return [item for item in value if isinstance(item, dict)]
    workflow_json = extracted.get("workflow_json")
    if isinstance(workflow_json, dict) and isinstance(workflow_json.get("nodes"), list):
        return [item for item in workflow_json.get("nodes", []) if isinstance(item, dict)]
    scanned_workflow = scanned.get("workflow_json")
    if isinstance(scanned_workflow, dict) and isinstance(scanned_workflow.get("nodes"), list):
        return [item for item in scanned_workflow.get("nodes", []) if isinstance(item, dict)]
    return []


def _workflow_surface(
    nodes: List[Dict[str, Any]],
    extracted: Dict[str, Any],
    scanned: Dict[str, Any],
) -> str:
    node_bits = []
    for node in nodes:
        node_bits.append(_node_type(node))
        node_bits.append(_stringify(node.get("name")))
        if isinstance(node.get("credentials"), dict):
            node_bits.extend(str(key) for key in node.get("credentials", {}).keys())
        parameters = node.get("parameters")
        if isinstance(parameters, dict):
            node_bits.append(_stringify(parameters))
    return " ".join(
        part
        for part in [
            " ".join(node_bits),
            _stringify(extracted.get("trigger")),
            _stringify(extracted.get("expected_output")),
            _stringify(extracted.get("input_payload")),
            _stringify(extracted.get("side_effects")),
            _stringify(extracted.get("credentials_required")),
            _stringify(extracted.get("workflow_json")),
            _stringify(scanned.get("blueprint_text")),
        ]
        if part
    )


def _detect_workflow_shape(
    *,
    project_type: str,
    nodes: List[Dict[str, Any]],
    extracted: Dict[str, Any],
    scanned: Dict[str, Any],
    rules: Dict[str, Any],
) -> bool:
    if _normalize(project_type) in {_normalize(item) for item in rules.get("applicable_project_types", [])}:
        return True
    if nodes:
        return True
    if isinstance(extracted.get("workflow_json"), dict) or isinstance(scanned.get("workflow_json"), dict):
        return True
    blueprint_text = _stringify(scanned.get("blueprint_text"))
    normalized_blueprint = _normalize(blueprint_text)
    if "n8n" in normalized_blueprint:
        return True
    if _has_value(extracted.get("trigger")) or _has_value(extracted.get("input_payload")) or _has_value(extracted.get("expected_output")):
        return True
    return False


def assess_n8n_automation_readiness(
    payload: Dict[str, Any],
    *,
    root: Path = DEFAULT_ROOT,
    project: Optional[Path] = None,
) -> Dict[str, Any]:
    root = root.resolve()
    project = (project or root).resolve()
    rules = load_n8n_automation_readiness_rules(root)
    extracted = _extract_inputs(payload, rules)
    scanned = _scan_project_for_workflow(project, rules) if project.exists() else {}
    project_type = _stringify(extracted.get("project_type")) or "unknown"
    nodes = _collect_nodes(extracted, scanned)

    if not _detect_workflow_shape(
        project_type=project_type,
        nodes=nodes,
        extracted=extracted,
        scanned=scanned,
        rules=rules,
    ):
        return {
            "status": "ok",
            "automation_ready": False,
            "risk_level": "low",
            "side_effects": [],
            "credentials_required": [],
            "human_approval_required": True,
            "dry_run_available": False,
            "test_payload_required": False,
            "blocked_reasons": [],
            "recommended_next_steps": [],
            "why": "n8n automation readiness is only relevant for workflow-like surfaces, blueprints or exported workflow JSON.",
            "source_files": scanned.get("source_files", []),
            "advisory_only": bool(rules.get("advisory_only", True)),
        }

    workflow_surface = _workflow_surface(nodes, extracted, scanned)
    signal_map = rules.get("node_type_signals", {})
    side_effects: List[str] = []
    blocked_reasons: List[str] = []
    warnings: List[str] = []
    credentials_required: List[str] = []
    sensitive_hits = _contains_any(workflow_surface, rules.get("sensitive_data_signals", []))

    send_email_hits = _contains_any(workflow_surface, signal_map.get("send_email", []))
    sheets_hits = _contains_any(workflow_surface, signal_map.get("sheets_write", []))
    db_hits = _contains_any(workflow_surface, signal_map.get("db_write", []))
    webhook_hits = _contains_any(workflow_surface, signal_map.get("webhook", []))
    scraping_hits = _contains_any(workflow_surface, signal_map.get("scraping", []))
    llm_hits = _contains_any(workflow_surface, signal_map.get("llm", []))

    for node in nodes:
        creds = node.get("credentials")
        if isinstance(creds, dict):
            for key in creds:
                cleaned = str(key).strip()
                if cleaned and cleaned not in credentials_required:
                    credentials_required.append(cleaned)

    credentials_required.extend(
        item for item in _listify(extracted.get("credentials_required")) if item not in credentials_required
    )

    trigger = _stringify(extracted.get("trigger"))
    input_payload = extracted.get("input_payload")
    expected_output = _stringify(extracted.get("expected_output"))
    explicit_side_effects = _listify(extracted.get("side_effects"))
    dry_run_available = bool(extracted.get("dry_run_available", False))
    human_approval_required = bool(extracted.get("human_approval_required", True))
    test_payload_available = bool(extracted.get("test_payload_available", False)) or _has_value(input_payload)
    rollback_documented = bool(extracted.get("rollback_documented", False))
    logging_documented = bool(extracted.get("logging_documented", False))
    error_handling_documented = bool(extracted.get("error_handling_documented", False))
    retry_strategy_documented = bool(extracted.get("retry_strategy_documented", False))
    idempotency_documented = bool(extracted.get("idempotency_documented", False))
    contains_sensitive_data = bool(extracted.get("contains_sensitive_data", False)) or bool(sensitive_hits)
    production_active = bool(extracted.get("production_active", False))
    public_webhook = bool(extracted.get("public_webhook", False)) or (
        bool(webhook_hits) and "auth" not in _normalize(workflow_surface)
    )

    if explicit_side_effects:
        side_effects.extend(item for item in explicit_side_effects if item not in side_effects)
    if send_email_hits:
        side_effects.append("send_email_real")
        blocked_reasons.append("send_email_real")
    if sheets_hits or db_hits:
        side_effects.append("sheets_or_db_write")
        blocked_reasons.append("sheets_or_db_write")
    if public_webhook:
        side_effects.append("public_webhook_without_auth")
        blocked_reasons.append("public_webhook_without_auth")
    if scraping_hits:
        side_effects.append("scraping_without_limits")
        blocked_reasons.append("scraping_without_limits")
    if llm_hits and contains_sensitive_data:
        side_effects.append("llm_with_sensitive_data")
        blocked_reasons.append("llm_with_sensitive_data")
    if production_active:
        side_effects.append("production_active")
        blocked_reasons.append("production_active")
    if credentials_required:
        warnings.append("credentials_missing_review")
    if side_effects and not rollback_documented:
        blocked_reasons.append("no_rollback_for_side_effects")

    test_payload_required = not test_payload_available
    if test_payload_required:
        warnings.append("missing_test_payload")
    if side_effects and not dry_run_available:
        warnings.append("missing_dry_run")
    if not logging_documented:
        warnings.append("missing_logging")
    if not error_handling_documented:
        warnings.append("missing_error_handling")
    if not retry_strategy_documented and side_effects:
        warnings.append("missing_retries")
    if not idempotency_documented and side_effects:
        warnings.append("missing_idempotency")

    risk_level = "low"
    if blocked_reasons:
        risk_level = "high"
    elif warnings:
        risk_level = "medium"

    automation_ready = bool(
        not blocked_reasons
        and not test_payload_required
        and (dry_run_available or not side_effects)
        and human_approval_required
        and bool(expected_output or nodes or trigger)
    )

    recommended_next_steps: List[str] = []
    if test_payload_required:
        recommended_next_steps.append("Document at least one safe test payload before touching any real system.")
    if side_effects and not dry_run_available:
        recommended_next_steps.append("Define a dry-run or simulation path before any workflow with side effects.")
    if credentials_required:
        recommended_next_steps.append("Keep credentials out of Atlas and require manual approval before any live connection.")
    if public_webhook:
        recommended_next_steps.append("Document webhook authentication and exposure boundaries before any activation.")
    if scraping_hits:
        recommended_next_steps.append("Review ToS, rate limits and anti-abuse constraints before any scraping workflow.")
    if llm_hits and contains_sensitive_data:
        recommended_next_steps.append("Remove or redact sensitive data before any LLM node evaluation.")
    if side_effects and not rollback_documented:
        recommended_next_steps.append("Document rollback and recovery steps before any production-facing automation.")
    if not recommended_next_steps:
        recommended_next_steps.append("Keep the workflow in blueprint or test-payload review until a human approves real execution.")

    return {
        "status": "ok",
        "automation_ready": automation_ready,
        "risk_level": risk_level,
        "side_effects": side_effects,
        "credentials_required": credentials_required,
        "human_approval_required": human_approval_required,
        "dry_run_available": dry_run_available,
        "test_payload_required": test_payload_required,
        "blocked_reasons": blocked_reasons,
        "warnings": warnings,
        "recommended_next_steps": recommended_next_steps,
        "trigger": trigger,
        "expected_output_defined": bool(expected_output),
        "rollback_documented": rollback_documented,
        "logging_documented": logging_documented,
        "error_handling_documented": error_handling_documented,
        "retry_strategy_documented": retry_strategy_documented,
        "idempotency_documented": idempotency_documented,
        "source_files": scanned.get("source_files", []),
        "why": "Atlas can review workflow risk, but real automation should stay manual and approval-bound.",
        "advisory_only": bool(rules.get("advisory_only", True)),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Assess n8n automation readiness without executing workflows.")
    parser.add_argument("--root", type=Path, default=DEFAULT_ROOT)
    parser.add_argument("--project", type=Path, default=None)
    parser.add_argument("--input", type=Path, default=None, help="Optional JSON payload to assess.")
    args = parser.parse_args()

    payload: Dict[str, Any] = {}
    if args.input:
        payload = json.loads(args.input.read_text(encoding="utf-8"))

    report = assess_n8n_automation_readiness(payload, root=args.root, project=args.project)
    print(json.dumps(report, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
