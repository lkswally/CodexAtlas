from __future__ import annotations

import argparse
import json
import subprocess
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


def _run_gh(args: List[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["gh", *args],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=False,
    )


def _parse_auth_identity(auth_output: str) -> Optional[str]:
    normalized_lines = [line.strip() for line in str(auth_output or "").splitlines() if line.strip()]
    for line in normalized_lines:
        lower = line.lower()
        if "logged in to github.com account " in lower:
            fragment = line.rsplit("account ", 1)[-1].strip()
            return fragment or None
        if "account " in line and "(" in line:
            fragment = line.split("account ", 1)[-1]
            return fragment.split(" ", 1)[0].strip() or None
        if line.lower().startswith("- active account:"):
            fragment = line.split(":", 1)[-1].strip()
            if fragment and fragment.lower() not in {"true", "false"}:
                return fragment
    return None


def _gh_json(args: List[str]) -> Dict[str, Any]:
    completed = _run_gh(args)
    if completed.returncode != 0:
        raise RuntimeError((completed.stderr or completed.stdout or "gh_command_failed").strip())
    stdout = (completed.stdout or "").strip()
    return json.loads(stdout) if stdout else {}


def _build_runtime_probe(
    payload: Dict[str, Any],
    *,
    rules: Dict[str, Any],
) -> Dict[str, Any]:
    blocked_write_capabilities = list(rules.get("runtime_blocked_write_capabilities", []))
    read_checks = list(rules.get("runtime_read_checks", []))
    runtime_probe = {
        "probe_mode": "not_requested",
        "runtime_read_only_available": False,
        "runtime_write_blocked": True,
        "authenticated_user_known": False,
        "authenticated_user": None,
        "repo_accessible": None,
        "default_branch_readable": None,
        "prs_readable": None,
        "issues_readable": None,
        "actions_readable": None,
        "write_attempted": False,
        "blocked_write_capabilities": blocked_write_capabilities,
        "checked_read_surfaces": read_checks,
        "probe_warnings": [],
        "probe_errors": [],
    }

    payload_runtime = payload.get("runtime_probe")
    if isinstance(payload_runtime, dict):
        runtime_probe["probe_mode"] = "payload_only"
        runtime_probe["authenticated_user_known"] = bool(payload_runtime.get("authenticated_user_known"))
        runtime_probe["authenticated_user"] = payload_runtime.get("authenticated_user")
        for key in ("repo_accessible", "default_branch_readable", "prs_readable", "issues_readable", "actions_readable"):
            if key in payload_runtime:
                runtime_probe[key] = bool(payload_runtime.get(key))
        runtime_probe["runtime_read_only_available"] = all(
            runtime_probe.get(key) is True
            for key in ("repo_accessible", "default_branch_readable", "prs_readable", "issues_readable", "actions_readable")
        )
        return runtime_probe

    if not bool(payload.get("perform_runtime_probe")):
        runtime_probe["probe_warnings"].append("runtime_probe_not_requested")
        return runtime_probe

    repo = str(payload.get("repo") or "").strip()
    if not repo:
        runtime_probe["probe_mode"] = "gh_cli_read_only"
        runtime_probe["probe_errors"].append("missing_repo_for_runtime_probe")
        return runtime_probe

    runtime_probe["probe_mode"] = "gh_cli_read_only"
    auth_status = _run_gh(["auth", "status"])
    combined_auth_output = "\n".join(part for part in (auth_status.stdout, auth_status.stderr) if part).strip()
    authenticated_user = _parse_auth_identity(combined_auth_output)
    if authenticated_user:
        runtime_probe["authenticated_user_known"] = True
        runtime_probe["authenticated_user"] = authenticated_user

    if auth_status.returncode != 0:
        runtime_probe["probe_errors"].append("gh_auth_unavailable_or_invalid")
        return runtime_probe

    try:
        repo_view = _gh_json(
            ["repo", "view", repo, "--json", "name,owner,defaultBranchRef,url"]
        )
        prs = _gh_json(["pr", "list", "--repo", repo, "--limit", "1", "--json", "number"])
        runs = _gh_json(["run", "list", "--repo", repo, "--limit", "1", "--json", "databaseId"])
        issues = _gh_json(["issue", "list", "--repo", repo, "--limit", "1", "--json", "number"])
    except Exception as exc:
        runtime_probe["probe_errors"].append(f"gh_read_probe_failed:{exc}")
        return runtime_probe

    runtime_probe["repo_accessible"] = bool(repo_view.get("name"))
    runtime_probe["default_branch_readable"] = bool((repo_view.get("defaultBranchRef") or {}).get("name"))
    runtime_probe["prs_readable"] = isinstance(prs, list)
    runtime_probe["actions_readable"] = isinstance(runs, list)
    runtime_probe["issues_readable"] = isinstance(issues, list)
    runtime_probe["runtime_read_only_available"] = all(
        runtime_probe.get(key) is True
        for key in ("repo_accessible", "default_branch_readable", "prs_readable", "issues_readable", "actions_readable")
    )
    return runtime_probe


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
    runtime_probe = _build_runtime_probe(payload, rules=rules)

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
        "theoretical_readiness_state": "ready_for_read_only_governance",
        "allowed_capabilities": allowed_capabilities,
        "approval_gated_capabilities": approval_gated_capabilities,
        "blocked_capabilities": blocked_capabilities,
        "requires_human_approval": True,
        "risk_level": risk_level,
        "blocked_reasons": list(dict.fromkeys(reason for reason in blocked_reasons if reason)),
        "next_safe_step": next_safe_step,
        "runtime_probe_state": "read_only_available" if runtime_probe["runtime_read_only_available"] else runtime_probe["probe_mode"],
        "runtime_probe": runtime_probe,
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
