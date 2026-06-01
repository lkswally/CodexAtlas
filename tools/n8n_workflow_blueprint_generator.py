from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from tools.n8n_automation_readiness import assess_n8n_automation_readiness


DEFAULT_ROOT = Path(__file__).resolve().parents[1]
RULES_PATH = Path("config/n8n_workflow_generation_rules.json")


def load_n8n_workflow_generation_rules(root: Path = DEFAULT_ROOT) -> Dict[str, Any]:
    return json.loads((root / RULES_PATH).read_text(encoding="utf-8-sig"))


def _normalize(value: Any) -> str:
    return " ".join(str(value or "").strip().lower().split())


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


def _has_any_signal(text: str, signals: List[str]) -> bool:
    normalized = _normalize(text)
    return any(_normalize(signal) in normalized for signal in signals)


def _derive_trigger(task_text: str, payload: Dict[str, Any], rules: Dict[str, Any]) -> str:
    explicit = _normalize(payload.get("trigger_preference"))
    if explicit in {"manual", "webhook", "schedule"}:
        return explicit
    if _has_any_signal(task_text, rules["task_signals"].get("schedule", [])):
        return "schedule"
    if _has_any_signal(task_text, rules["task_signals"].get("webhook", [])):
        return "webhook"
    return "manual"


def _build_data_contract(task_text: str, wants_email: bool, rules: Dict[str, Any]) -> Dict[str, Any]:
    if _has_any_signal(task_text, rules["task_signals"].get("business_idea", [])):
        input_fields = {
            "idea_title": "Short name for the business idea.",
            "problem": "Problem the idea claims to solve.",
            "target_audience": "Who the idea is for.",
            "solution": "Short description of the proposed solution.",
            "constraints": "Budget, timing or implementation constraints."
        }
        if wants_email:
            input_fields["email"] = "Optional review recipient for the final report."
        return {
            "input_fields": input_fields,
            "output_fields": {
                "summary": "Short analysis of the idea.",
                "risks": "Main execution or market risks.",
                "opportunities": "Potential upside or fit signals.",
                "recommended_next_steps": "Human review actions before doing anything real."
            }
        }

    return {
        "input_fields": {
            "request_id": "Internal request identifier.",
            "input_text": "Primary workflow input to evaluate.",
            "context": "Optional additional context for the workflow."
        },
        "output_fields": {
            "result": "Structured workflow result.",
            "notes": "Human review notes.",
            "recommended_next_steps": "Actions required before activation."
        }
    }


def _default_test_payload(task_text: str, data_contract: Dict[str, Any], rules: Dict[str, Any]) -> Dict[str, Any]:
    if _has_any_signal(task_text, rules["task_signals"].get("business_idea", [])):
        payload = {
            "idea_title": "Marketplace de auditoria UX para pymes",
            "problem": "Las pymes no detectan rapido problemas de conversion y claridad en sus sitios.",
            "target_audience": "Fundadores de negocios online pequeños y medianos.",
            "solution": "Una auditoria estructurada con hallazgos accionables y roadmap inicial.",
            "constraints": "Presupuesto acotado y equipo chico."
        }
        if "email" in data_contract.get("input_fields", {}):
            payload["email"] = rules["safe_placeholder_values"]["email_recipient"]
        return payload

    return {
        "request_id": "REQ-TEST-001",
        "input_text": "Texto de prueba para revisar el flujo sin tocar sistemas reales.",
        "context": "Contexto ficticio para validacion local."
    }


def _credential_placeholders(wants_llm: bool, wants_email: bool, wants_sheets: bool, wants_db: bool, rules: Dict[str, Any]) -> List[str]:
    binding = rules["safe_placeholder_values"]["credential_binding"]
    placeholders: List[str] = []
    if wants_llm:
        placeholders.append(f"LLM_PROVIDER_{binding}")
    if wants_email:
        placeholders.append(f"EMAIL_PROVIDER_{binding}")
    if wants_sheets:
        placeholders.append(f"SHEETS_PROVIDER_{binding}")
    if wants_db:
        placeholders.append(f"DATABASE_PROVIDER_{binding}")
    return placeholders


def _workflow_name(task_text: str, payload: Dict[str, Any]) -> str:
    explicit = _stringify(payload.get("workflow_name"))
    if explicit:
        return explicit
    compact = re.sub(r"[^a-zA-Z0-9 ]+", " ", task_text).strip()
    compact = re.sub(r"\s+", " ", compact)
    if not compact:
        return "Atlas Generated Workflow Blueprint"
    words = compact.split()[:7]
    return "Atlas " + " ".join(word.capitalize() for word in words)


def _build_blueprint_nodes(
    *,
    trigger_kind: str,
    wants_llm: bool,
    wants_email: bool,
    wants_sheets: bool,
    wants_db: bool,
) -> List[Dict[str, Any]]:
    nodes: List[Dict[str, Any]] = []
    nodes.append(
        {
            "id": "trigger",
            "name": {
                "manual": "Manual Trigger",
                "webhook": "Webhook Intake",
                "schedule": "Schedule Trigger",
            }[trigger_kind],
            "type": {
                "manual": "manual trigger",
                "webhook": "webhook",
                "schedule": "schedule trigger",
            }[trigger_kind],
            "role": "entry_trigger",
            "side_effect": False,
        }
    )
    nodes.append(
        {
            "id": "normalize_input",
            "name": "Normalize Input",
            "type": "set",
            "role": "normalize_input",
            "side_effect": False,
        }
    )
    if wants_llm:
        nodes.append(
            {
                "id": "llm_analysis",
                "name": "LLM Analysis Placeholder",
                "type": "openai",
                "role": "analysis",
                "side_effect": False,
            }
        )
    nodes.append(
        {
            "id": "format_report",
            "name": "Format Report",
            "type": "set",
            "role": "format_output",
            "side_effect": False,
        }
    )
    if wants_email or wants_sheets or wants_db or trigger_kind == "webhook":
        nodes.append(
            {
                "id": "approval_gate",
                "name": "Human Approval Required",
                "type": "manual approval",
                "role": "approval_gate",
                "side_effect": False,
            }
        )
    if wants_email:
        nodes.append(
            {
                "id": "email_delivery",
                "name": "Send Email Placeholder",
                "type": "send email",
                "role": "delivery",
                "side_effect": True,
            }
        )
    if wants_sheets:
        nodes.append(
            {
                "id": "sheets_write",
                "name": "Google Sheets Write Placeholder",
                "type": "google sheets",
                "role": "data_write",
                "side_effect": True,
            }
        )
    if wants_db:
        nodes.append(
            {
                "id": "db_write",
                "name": "Database Write Placeholder",
                "type": "postgres",
                "role": "data_write",
                "side_effect": True,
            }
        )
    return nodes


def generate_n8n_workflow_blueprint(
    payload: Dict[str, Any],
    *,
    root: Path = DEFAULT_ROOT,
    project: Optional[Path] = None,
) -> Dict[str, Any]:
    root = root.resolve()
    project = (project or root).resolve()
    rules = load_n8n_workflow_generation_rules(root)

    task_text = _stringify(payload.get("task") or payload.get("goal") or payload.get("description"))
    if not task_text:
        task_text = "Offline workflow review"

    trigger_kind = _derive_trigger(task_text, payload, rules)
    wants_llm = _has_any_signal(task_text, rules["task_signals"].get("llm", []))
    wants_email = _has_any_signal(task_text, rules["task_signals"].get("email", []))
    wants_sheets = _has_any_signal(task_text, rules["task_signals"].get("sheets", []))
    wants_db = _has_any_signal(task_text, rules["task_signals"].get("database", []))
    wants_scraping = _has_any_signal(task_text, rules["task_signals"].get("scraping", []))

    data_contract = _build_data_contract(task_text, wants_email, rules)
    test_payload = payload.get("test_payload") if isinstance(payload.get("test_payload"), dict) else _default_test_payload(task_text, data_contract, rules)
    credentials_placeholders = _credential_placeholders(wants_llm, wants_email, wants_sheets, wants_db, rules)
    nodes = _build_blueprint_nodes(
        trigger_kind=trigger_kind,
        wants_llm=wants_llm,
        wants_email=wants_email,
        wants_sheets=wants_sheets,
        wants_db=wants_db,
    )

    side_effects: List[str] = []
    if wants_email:
        side_effects.append("send_email_real")
    if wants_sheets or wants_db:
        side_effects.append("sheets_or_db_write")
    if trigger_kind == "webhook":
        side_effects.append("public_webhook_without_auth")
    if wants_scraping:
        side_effects.append("scraping_without_limits")

    human_approval_required = bool(side_effects)
    readiness_payload = {
        "project_type": "automation_blueprint",
        "trigger": trigger_kind,
        "expected_output": "Structured workflow draft for human review.",
        "input_payload": test_payload,
        "test_payload_available": True,
        "human_approval_required": True,
        "dry_run_available": not side_effects,
        "rollback_documented": not side_effects,
        "logging_documented": True,
        "error_handling_documented": True,
        "retry_strategy_documented": not side_effects,
        "idempotency_documented": not side_effects,
        "contains_sensitive_data": bool(payload.get("contains_sensitive_data", False)),
        "public_webhook": trigger_kind == "webhook",
        "credentials_required": credentials_placeholders,
        "side_effects": side_effects,
        "nodes": nodes,
    }
    readiness_posture = assess_n8n_automation_readiness(readiness_payload, root=root, project=project)

    recommended_next_steps = list(rules.get("default_checklist", []))
    recommended_next_steps.extend(readiness_posture.get("recommended_next_steps", []))

    return {
        "status": "ok",
        "workflow_name": _workflow_name(task_text, payload),
        "trigger": trigger_kind,
        "nodes": nodes,
        "data_contract": data_contract,
        "test_payload": test_payload,
        "side_effects": side_effects,
        "credentials_placeholders": credentials_placeholders,
        "human_approval_required": human_approval_required,
        "import_ready": bool(
            readiness_posture.get("automation_ready")
            and not readiness_posture.get("blocked_reasons")
        ),
        "recommended_next_steps": recommended_next_steps,
        "readiness_posture": readiness_posture,
        "advisory_only": bool(rules.get("advisory_only", True)),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate an offline n8n workflow blueprint.")
    parser.add_argument("--root", type=Path, default=DEFAULT_ROOT)
    parser.add_argument("--project", type=Path, default=None)
    parser.add_argument("--input", type=Path, default=None, help="Optional JSON payload.")
    parser.add_argument("--task", default="", help="Plain-language workflow request.")
    args = parser.parse_args()

    payload: Dict[str, Any] = {}
    if args.input:
        payload = json.loads(args.input.read_text(encoding="utf-8"))
    if args.task and not payload.get("task"):
        payload["task"] = args.task

    report = generate_n8n_workflow_blueprint(payload, root=args.root, project=args.project)
    print(json.dumps(report, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
