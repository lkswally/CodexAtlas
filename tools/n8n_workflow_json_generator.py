from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any, Dict, List, Optional

from tools.n8n_automation_readiness import assess_n8n_automation_readiness
from tools.n8n_workflow_blueprint_generator import (
    DEFAULT_ROOT,
    generate_n8n_workflow_blueprint,
    load_n8n_workflow_generation_rules,
)


def _normalize(value: Any) -> str:
    return " ".join(str(value or "").strip().lower().split())


def _value_looks_safe(value: Any, markers: List[str]) -> bool:
    normalized = _normalize(value)
    return any(_normalize(marker) in normalized for marker in markers)


def _contains_real_credentials(value: Any, markers: List[str], key_signals: List[str], key_name: str = "") -> bool:
    if isinstance(value, dict):
        for key, nested in value.items():
            key_text = str(key).strip().lower()
            if any(signal in key_text for signal in key_signals):
                if nested and not _value_looks_safe(nested, markers):
                    return True
            if _contains_real_credentials(nested, markers, key_signals, key_text):
                return True
        return False
    if isinstance(value, list):
        return any(_contains_real_credentials(item, markers, key_signals, key_name) for item in value)
    if key_name and any(signal in key_name for signal in key_signals):
        return bool(value) and not _value_looks_safe(value, markers)
    return False


def _positions_for(nodes: List[Dict[str, Any]]) -> Dict[str, List[int]]:
    positions: Dict[str, List[int]] = {}
    x = 260
    for node in nodes:
        positions[str(node["id"])] = [x, 280]
        x += 280
    return positions


def _json_node_for_blueprint_node(node: Dict[str, Any], positions: Dict[str, List[int]], rules: Dict[str, Any]) -> Dict[str, Any]:
    node_id = str(node["id"])
    kind = str(node["role"])
    template_name = {
        "entry_trigger": {
            "manual trigger": "manual",
            "webhook": "webhook",
            "schedule trigger": "schedule",
        }.get(_normalize(node["type"]), "manual"),
        "normalize_input": "normalize_input",
        "analysis": "llm_analysis",
        "format_output": "format_report",
        "approval_gate": "approval_gate",
        "delivery": "email_delivery",
        "data_write": "sheets_write" if "sheet" in _normalize(node["name"]) else "db_write",
    }[kind]
    if template_name in {"manual", "webhook", "schedule"}:
        type_name = rules["trigger_templates"][template_name]["n8n_type"]
    else:
        type_name = rules["node_templates"][template_name]["n8n_type"]

    safe = rules["safe_placeholder_values"]
    parameters: Dict[str, Any] = {}
    if template_name == "webhook":
        parameters = {"httpMethod": "POST", "path": safe["webhook_path"], "responseMode": "lastNode"}
    elif template_name == "schedule":
        parameters = {"rule": {"interval": [{"field": "minutes", "minutesInterval": 60}]}}
    elif template_name == "normalize_input":
        parameters = {
            "keepOnlySet": False,
            "values": {
                "string": [
                    {"name": "atlas_review_mode", "value": "manual_only"},
                    {"name": "request_source", "value": "offline_blueprint"}
                ]
            }
        }
    elif template_name == "llm_analysis":
        parameters = {
            "language": "javaScript",
            "jsCode": (
                "// Placeholder step only. Bind a real LLM node manually after review.\n"
                "const incoming = $input.first()?.json ?? {};\n"
                "return [{ json: { ...incoming, llm_analysis_status: 'manual_binding_required', llm_model_placeholder: '"
                + safe["llm_model"]
                + "' } }];"
            ),
        }
    elif template_name == "format_report":
        parameters = {
            "keepOnlySet": False,
            "values": {
                "string": [
                    {"name": "report_status", "value": "draft_only"},
                    {"name": "approval_required", "value": "true"}
                ]
            }
        }
    elif template_name == "approval_gate":
        parameters = {
            "keepOnlySet": False,
            "values": {
                "string": [
                    {"name": "human_approval_required", "value": "true"},
                    {"name": "activation_block", "value": "manual_review_before_live_use"}
                ]
            }
        }
    elif template_name == "email_delivery":
        parameters = {
            "keepOnlySet": False,
            "values": {
                "string": [
                    {"name": "email_placeholder_recipient", "value": safe["email_recipient"]},
                    {"name": "email_credential_placeholder", "value": f"EMAIL_PROVIDER_{safe['credential_binding']}"}
                ]
            }
        }
    elif template_name == "sheets_write":
        parameters = {
            "keepOnlySet": False,
            "values": {
                "string": [
                    {"name": "sheet_id_placeholder", "value": safe["sheet_identifier"]},
                    {"name": "sheet_credential_placeholder", "value": f"SHEETS_PROVIDER_{safe['credential_binding']}"}
                ]
            }
        }
    elif template_name == "db_write":
        parameters = {
            "keepOnlySet": False,
            "values": {
                "string": [
                    {"name": "database_target_placeholder", "value": safe["database_target"]},
                    {"name": "db_credential_placeholder", "value": f"DATABASE_PROVIDER_{safe['credential_binding']}"}
                ]
            }
        }

    return {
        "id": node_id,
        "name": str(node["name"]),
        "type": type_name,
        "typeVersion": 1,
        "position": positions[node_id],
        "parameters": parameters,
    }


def generate_n8n_workflow_json(
    payload: Dict[str, Any],
    *,
    root: Path = DEFAULT_ROOT,
    project: Optional[Path] = None,
) -> Dict[str, Any]:
    root = root.resolve()
    project = (project or root).resolve()
    rules = load_n8n_workflow_generation_rules(root)

    contains_real_credentials = _contains_real_credentials(
        payload,
        rules.get("safe_placeholder_markers", []),
        rules.get("disallowed_credential_key_signals", []),
    )
    if contains_real_credentials:
        return {
            "status": "blocked",
            "workflow_json_generated": False,
            "workflow_active": False,
            "contains_real_credentials": True,
            "requires_manual_credential_binding": True,
            "import_instructions": [],
            "readiness_posture": {},
            "blocked_reasons": ["real_credentials_not_allowed"],
        }

    blueprint = payload.get("blueprint") if isinstance(payload.get("blueprint"), dict) else None
    if blueprint is None:
        blueprint = generate_n8n_workflow_blueprint(payload, root=root, project=project)

    nodes = blueprint.get("nodes", [])
    positions = _positions_for(nodes)
    json_nodes = [_json_node_for_blueprint_node(node, positions, rules) for node in nodes]

    connections: Dict[str, Dict[str, List[List[Dict[str, Any]]]]] = {}
    for current, nxt in zip(json_nodes, json_nodes[1:]):
        connections[current["name"]] = {
            "main": [[{"node": nxt["name"], "type": "main", "index": 0}]]
        }
    if json_nodes:
        connections.setdefault(json_nodes[-1]["name"], {"main": [[]]})

    workflow_json = {
        "name": blueprint.get("workflow_name", "Atlas Generated Workflow"),
        "active": bool(rules.get("workflow_active_by_default", False)),
        "nodes": json_nodes,
        "connections": connections,
        "settings": {"executionOrder": "v1"},
        "pinData": {},
        "meta": {
            "atlasGenerated": True,
            "manualReviewRequired": True,
            "requiresManualCredentialBinding": True
        },
        "tags": [
            {"name": "atlas-generated"},
            {"name": "manual-review-required"}
        ]
    }

    readiness_payload = {
        "project_type": "automation_blueprint",
        "workflow_json": workflow_json,
        "nodes": blueprint.get("nodes", []),
        "trigger": blueprint.get("trigger"),
        "input_payload": blueprint.get("test_payload"),
        "expected_output": "Generated offline workflow skeleton for manual n8n import.",
        "credentials_required": blueprint.get("credentials_placeholders", []),
        "side_effects": blueprint.get("side_effects", []),
        "human_approval_required": True,
        "test_payload_available": bool(blueprint.get("test_payload")),
        "dry_run_available": not bool(blueprint.get("side_effects")),
        "rollback_documented": not bool(blueprint.get("side_effects")),
        "logging_documented": True,
        "error_handling_documented": True,
        "retry_strategy_documented": not bool(blueprint.get("side_effects")),
        "idempotency_documented": not bool(blueprint.get("side_effects")),
        "public_webhook": blueprint.get("trigger") == "webhook",
    }
    readiness_posture = assess_n8n_automation_readiness(readiness_payload, root=root, project=project)

    import_instructions = [
        "Import the JSON into a non-production n8n workspace first.",
        "Keep the workflow inactive after import.",
        "Bind credentials manually inside n8n only after review.",
        "Run only with fake or redacted test payloads first.",
    ]
    import_instructions.extend(blueprint.get("recommended_next_steps", []))

    return {
        "status": "ok",
        "workflow_json_generated": True,
        "workflow_active": bool(workflow_json.get("active", False)),
        "contains_real_credentials": False,
        "requires_manual_credential_binding": bool(blueprint.get("credentials_placeholders")),
        "import_instructions": import_instructions,
        "readiness_posture": readiness_posture,
        "workflow_json": workflow_json,
        "credential_placeholders": blueprint.get("credentials_placeholders", []),
        "human_approval_required": bool(readiness_posture.get("human_approval_required", True)),
        "test_payload": blueprint.get("test_payload", {}),
        "blocked_reasons": readiness_posture.get("blocked_reasons", []),
        "advisory_only": bool(rules.get("advisory_only", True)),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate an offline importable n8n workflow JSON skeleton.")
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

    report = generate_n8n_workflow_json(payload, root=args.root, project=args.project)
    print(json.dumps(report, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
