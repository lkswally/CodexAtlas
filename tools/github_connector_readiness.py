from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Dict, List, Optional

try:
    from tools.mcp_permission_matrix_readiness import assess_mcp_permission_matrix_readiness
except ModuleNotFoundError:
    from mcp_permission_matrix_readiness import assess_mcp_permission_matrix_readiness


DEFAULT_ROOT = Path(__file__).resolve().parents[1]
RULES_PATH = Path("config/github_connector_rules.json")


def load_github_connector_rules(root: Path = DEFAULT_ROOT) -> Dict[str, Any]:
    return json.loads((root / RULES_PATH).read_text(encoding="utf-8-sig"))


def _normalize(value: Any) -> str:
    return " ".join(str(value or "").strip().lower().split())


def _normalize_capability(value: Any, rules: Dict[str, Any]) -> str:
    requested = _normalize(value) or "repo_status"
    aliases = {_normalize(alias): canonical for alias, canonical in (rules.get("capability_aliases") or {}).items()}
    capability = aliases.get(requested, requested)
    if capability not in (rules.get("capability_levels") or {}):
        return "repo_status"
    return capability


def assess_github_connector_readiness(
    payload: Dict[str, Any],
    *,
    root: Path = DEFAULT_ROOT,
    project: Optional[Path] = None,
) -> Dict[str, Any]:
    root = root.resolve()
    project = (project or root).resolve()
    rules = load_github_connector_rules(root)

    capability = _normalize_capability(payload.get("requested_capability"), rules)
    capability_levels = rules.get("capability_levels") or {}
    requested_level = str(capability_levels.get(capability, "read_only")).strip() or "read_only"

    matrix_payload = dict(payload)
    matrix_payload.update(
        {
            "platform": "github",
            "requested_capability": requested_level,
        }
    )

    if capability == "secrets_access":
        matrix_payload["has_sensitive_data"] = True
        matrix_payload["uses_credentials"] = True
    if capability in {"merge", "workflow_dispatch", "delete", "force_push"}:
        matrix_payload.setdefault("rollback_available", False)
        if capability == "workflow_dispatch":
            matrix_payload.setdefault("dry_run_available", False)

    matrix_result = assess_mcp_permission_matrix_readiness(matrix_payload, root=root, project=project)
    matrix_posture = matrix_result["mcp_permission_posture"]

    hard_blocked = set(rules.get("hard_blocked_capabilities", []))
    blocked_capabilities = list(rules.get("blocked_capabilities", []))
    approval_gated_capabilities = list(rules.get("approval_gated_capabilities", []))
    allowed_capabilities = list(rules.get("allowed_capabilities", []))
    next_safe_steps = rules.get("capability_next_safe_steps") or {}

    requested_allowed = bool(matrix_posture.get("allowed"))
    blocked_reasons = list(matrix_posture.get("blocked_reasons", []))
    risk_level = str(matrix_posture.get("risk_level", "medium")).strip() or "medium"

    if capability in hard_blocked:
        requested_allowed = False
        blocked_reasons.append(f"{capability}_blocked_by_github_policy")
        risk_level = "high"

    next_safe_step = str(next_safe_steps.get(capability) or matrix_posture.get("next_safe_step") or "").strip()

    posture = {
        "recommended_mode": str(rules.get("recommended_mode", "read_only")).strip() or "read_only",
        "requested_capability": capability,
        "requested_level": requested_level,
        "requested_allowed": requested_allowed,
        "allowed_capabilities": allowed_capabilities,
        "approval_gated_capabilities": approval_gated_capabilities,
        "blocked_capabilities": blocked_capabilities,
        "requires_human_approval": True,
        "risk_level": risk_level,
        "blocked_reasons": list(dict.fromkeys(reason for reason in blocked_reasons if reason)),
        "next_safe_step": next_safe_step,
        "mcp_permission_posture": matrix_posture,
        "advisory_only": bool(rules.get("advisory_only", True)),
    }

    return {
        "status": "ok",
        "github_connector_posture": posture,
        "advisory_only": bool(rules.get("advisory_only", True)),
    }


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(add_help=True)
    parser.add_argument("--project", default=None)
    parser.add_argument("--capability", default="repo_status")
    parser.add_argument("--payload-json", default=None)
    args = parser.parse_args(argv)

    payload = {"requested_capability": args.capability}
    if args.payload_json:
        payload.update(json.loads(args.payload_json))
    project = Path(args.project).resolve() if args.project else DEFAULT_ROOT
    result = assess_github_connector_readiness(payload, root=DEFAULT_ROOT, project=project)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
