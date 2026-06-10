from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, Optional


DEFAULT_RULES_PATH = Path(__file__).resolve().parents[1] / "config" / "model_routing_rules.json"


class ModelRoutingPolicyError(ValueError):
    pass


def load_model_routing_rules(path: Path = DEFAULT_RULES_PATH) -> Dict[str, Any]:
    try:
        return json.loads(Path(path).read_text(encoding="utf-8"))
    except OSError as exc:
        raise ModelRoutingPolicyError(f"Could not read model routing rules: `{path}`.") from exc
    except json.JSONDecodeError as exc:
        raise ModelRoutingPolicyError(f"Model routing rules are not valid JSON: `{path}`.") from exc


def select_model_class(
    task_type: str,
    risk_level: str,
    *,
    cost_sensitivity: Optional[str] = None,
    criticality: Optional[str] = None,
    rules: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    rules = rules or load_model_routing_rules()
    task = str(task_type)
    risk = str(risk_level)

    if task not in rules["task_types"]:
        raise ModelRoutingPolicyError(f"Unknown task_type `{task}`.")
    if risk not in rules["risk_levels"]:
        raise ModelRoutingPolicyError(f"Unknown risk_level `{risk}`.")

    selected = rules["default_task_routes"][task]
    reason_parts = [f"`{task}` defaults to `{selected}`."]
    requires_human_approval = task in rules["human_approval_task_types"]

    if risk == "blocked":
        selected = "blocked"
        requires_human_approval = True
        reason_parts.append(rules["risk_overrides"]["blocked"]["reason"])
    elif task in rules["blocked_task_types"]:
        selected = "blocked"
        requires_human_approval = True
        reason_parts.append("Task type is blocked because it involves secrets or credentials.")
    elif requires_human_approval:
        reason_parts.append("Task type requires human approval before execution.")
    elif risk == "high" and selected == "cheap_fast":
        selected = rules["risk_overrides"]["high"]["minimum_model_class"]
        reason_parts.append(rules["risk_overrides"]["high"]["reason"])

    if cost_sensitivity:
        reason_parts.append(f"Cost sensitivity noted as `{cost_sensitivity}`; V1 does not auto-switch.")
    if criticality:
        reason_parts.append(f"Criticality noted as `{criticality}`; V1 does not auto-switch.")

    return {
        "task_type": task,
        "risk_level": risk,
        "selected_model_class": selected,
        "reason": " ".join(reason_parts),
        "requires_human_approval": requires_human_approval,
        "auto_switch_allowed": False,
    }
