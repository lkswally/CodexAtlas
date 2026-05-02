from __future__ import annotations

import argparse
import json
import os
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

DEFAULT_ROOT = Path(__file__).resolve().parents[1]

PRIMARY_STRUCTURE_FILES = (
    "commands/atomic_command_registry.json",
    "policies/mcp_connector_policy.md",
    "memory/context_refresh_protocol.md",
)
LEGACY_COMPAT_FILES = (
    "00_SISTEMA/_meta/atlas/atomic_command_registry.json",
    "00_SISTEMA/_meta/atlas/mcp_connector_policy.md",
    "00_SISTEMA/_meta/atlas/context_refresh_protocol.md",
)
REQUIRED_ROOT_FILES = (
    "AGENTS.md",
    "ATLAS_STATUS.md",
    "ATLAS_NEXT_STEPS.md",
    "README.md",
    "config/model_profiles.json",
    "config/model_routing_rules.json",
    "config/mcp_profiles.json",
    "config/docs_search_catalog.json",
    "config/phase_playbook.json",
    "agents/orchestrator.md",
    "agents/planner.md",
    "agents/architect.md",
    "agents/implementer.md",
    "agents/reviewer.md",
    "agents/ux_brand.md",
    "agents/ux_architect.md",
    "agents/ui_designer.md",
    "agents/brand_agent.md",
    "agents/evidence_collector.md",
    "agents/security_guard.md",
    "agents/reality_checker.md",
    "workflows/atlas_project_pipeline.md",
    "workflows/create_project.md",
    "workflows/audit_project.md",
    "workflows/design_intelligence_pipeline.md",
    "workflows/certify_output.md",
    "workflows/certify_project.md",
    "workflows/audit_repo.md",
    "policies/anti_generic_output_policy.md",
    "policies/anti_generic_ui_policy.md",
    "policies/landing_quality_policy.md",
    "policies/visual_direction_policy.md",
    "policies/design_evidence_policy.md",
    "policies/evidence_required_policy.md",
    "policies/safe_execution_policy.md",
    "policies/human_approval_policy.md",
    "policies/project_boundary_check_policy.md",
    "policies/project_derivative_policy.md",
    "policies/template_quality_check_policy.md",
    "policies/mcp_connector_policy.md",
    "policies/model_routing_policy.md",
    "policies/mcp_routing_policy.md",
    "policies/cost_control_policy.md",
    "memory/decision_log.md",
    "memory/breadcrumbs.md",
    "memory/session_summaries.md",
    "memory/project_state.json",
    "memory/context_refresh_protocol.md",
    "memory/derived_projects.json",
    "memory/routing_log.jsonl",
    "memory/governance_events.jsonl",
    "memory/mcp_events.jsonl",
    "memory/decision_feedback.jsonl",
    "docs/architecture.md",
    "docs/claude_to_codex_mapping.md",
    "docs/codex_system_prompt.md",
    "docs/claude_vibecoding_assessment.md",
    "docs/claude_vibecoding_design_intelligence.md",
    "docs/mcp_read_only_evaluation.md",
    "adapters/reyesoft/README.md",
    "skills/README.md",
    "skills/project-bootstrap/skill.md",
    "skills/project-bootstrap/skill.json",
    "skills/project-bootstrap/behavior.json",
    "skills/project-bootstrap/bootstrap_contract.json",
    "skills/repo-audit/skill.md",
    "skills/repo-audit/skill.json",
    "skills/repo-audit/behavior.json",
    "skills/product-branding-review/skill.md",
    "skills/product-branding-review/skill.json",
    "skills/product-branding-review/behavior.json",
    "skills/visual-direction-checkpoint/skill.md",
    "skills/visual-direction-checkpoint/skill.json",
    "skills/visual-direction-checkpoint/behavior.json",
    "skills/anti-generic-ui-audit/skill.md",
    "skills/anti-generic-ui-audit/skill.json",
    "skills/anti-generic-ui-audit/behavior.json",
    "skills/design-system-review/skill.md",
    "skills/design-system-review/skill.json",
    "skills/design-system-review/behavior.json",
    "workflows/orchestrator_routing.md",
    "tools/atlas_orchestrator.py",
    "tools/design_intelligence_audit.py",
    "tools/atlas_mcp_manager.py",
    "tools/atlas_surface_audit.py",
    "tools/docs_search_adapter.py",
    "tools/docs_catalog_report.py",
    "tools/project_phase_resolver.py",
    "tools/project_intent_analyzer.py",
    "tools/priority_engine.py",
    "tools/decision_feedback.py",
    "tools/feedback_analyzer.py",
    "tools/model_router.py",
    "tools/error_pattern_analyzer.py",
    "tools/repo_improvement_scout.py",
    "tools/mcp_readiness_check.py",
    "tools/prompt_builder.py",
    "tools/quality_gate_report.py",
    "tools/skill_evaluator.py",
    "tests/test_atlas_orchestrator.py",
    "tests/test_certify_project.py",
    "tests/test_docs_catalog_report.py",
    "tests/test_design_intelligence_audit.py",
    "tests/test_mcp_manager.py",
    "tests/test_project_intent.py",
    "tests/test_project_phase.py",
    "tests/test_priority_engine.py",
    "tests/test_decision_feedback.py",
    "tests/test_feedback_analyzer.py",
    "tests/test_model_router.py",
    "tests/test_error_pattern_analyzer.py",
    "tests/test_repo_improvement_scout.py",
    "tests/test_mcp_readiness_check.py",
    "tests/test_prompt_builder.py",
    "tests/test_quality_gate_report.py",
    "tests/test_skill_evaluator.py",
    "tests/test_skill_execution.py",
    "tests/test_skill_governance.py",
    "tests/test_surface_audit.py",
    "templates/project_bootstrap_profiles.md",
)
REQUIRED_DIRS = (
    "adapters",
    "agents",
    "config",
    "skills",
    "workflows",
    "policies",
    "templates",
    "validators",
    "commands",
    "memory",
    "docs",
    "tests",
)

REQUIRED_TOP_LEVEL = {"registry_version", "status", "scope", "commands"}
REQUIRED_COMMAND_FIELDS = {
    "id",
    "alias",
    "purpose",
    "fit",
    "execution_mode",
    "allowed_paths",
    "guards",
    "outputs",
    "rollback",
}
VALID_FITS = {"high", "medium", "low"}
VALID_EXECUTION_MODES = {"read_only", "write_docs", "write_code"}
VALID_SKILL_RISK_LEVELS = {"low", "medium", "high"}
VALID_SKILL_ALLOWED_PATHS_POLICIES = {
    "atlas_root_or_derived_project_read_only",
    "explicit_output_dir_only",
    "no_filesystem_writes",
}
BEHAVIOR_REQUIRED_FIELDS = {
    "writes_files",
    "writes_code",
    "uses_output_dir",
    "read_only",
    "execution_helper",
    "side_effects",
    "requires_project_path",
    "requires_output_dir",
    "can_run_without_approval",
    "notes",
}
BOOTSTRAP_CONTRACT_REQUIRED_FIELDS = {
    "required_inputs",
    "optional_inputs",
    "supported_project_types",
    "default_project_type",
    "generated_structure",
    "required_files",
    "optional_files",
    "forbidden_outputs",
    "default_output_mode",
    "templates_by_type",
    "initial_content",
    "rollback_manual",
    "validation_steps",
    "safety_limits",
    "human_approval_triggers",
}
REQUIRED_BOOTSTRAP_PROJECT_TYPES = {
    "backend_service",
    "frontend_app",
    "fullstack",
    "internal_tool",
    "ai_agent_system",
}
SKILL_REQUIRED_FIELDS = {
    "name",
    "intent_keywords",
    "agent",
    "workflow",
    "model_profile",
    "risk_level",
    "requires_human_approval",
    "supports_execution",
    "expected_outputs",
    "validations",
    "required_inputs",
    "safety_limits",
    "rollback_manual",
    "execution_mode",
    "allowed_paths_policy",
    "forbidden_actions",
    "human_approval_triggers",
}
REQUIRED_PROJECT_STATE_KEYS = {
    "system_name",
    "canonical_root",
    "mode",
    "status",
    "layout",
    "restrictions",
    "executable_components",
    "documentary_components",
    "legacy_compatibility",
}
REQUIRED_DERIVED_PROJECT_KEYS = {
    "schema_version",
    "project_name",
    "project_type",
    "derived_from",
    "atlas_root",
    "audit_paths",
    "status",
}
DERIVED_PROJECT_TYPE = "atlas-derived-project"
DEPRECATED_ACTIVE_ATLAS_PATHS = (
    "tools/atlas_dispatcher.py",
    "tools/atlas_governance_check.py",
    "00_SISTEMA/_meta/atlas",
    "tests/test_atlas_dispatcher.py",
    "tests/test_atlas_governance_check.py",
)
ALLOWED_LEGACY_PREFIXES = (
    "00_SISTEMA/_legacy/",
)
ALLOWED_BOOTSTRAP_TEMPLATE_PLACEHOLDERS = {
    "project_name",
    "project_type",
    "project_goal",
    "scope",
    "atlas_root",
    "generated_from_skill",
}
BOOTSTRAP_TEMPLATE_PLACEHOLDER_RE = re.compile(
    r"(?P<double>\{\{(?P<double_name>[a-zA-Z0-9_]+)\}\})|"
    r"(?P<dollar>\$\{(?P<dollar_name>[a-zA-Z0-9_]+)\})|"
    r"(?P<single>\{(?P<single_name>[a-zA-Z0-9_]+)\})"
)
FORBIDDEN_CANONICAL_ROOT_ARTIFACTS = (
    ".claude",
    "CLAUDE.md",
)
GOVERNANCE_EVENTS_LOG = "governance_events.jsonl"
REQUIRED_MCP_PROFILE_FIELDS = {
    "purpose",
    "risk_level",
    "default_mode",
    "requires_approval",
    "provider_kind",
    "atlas_decision",
    "experimental_enabled",
    "read_only_scope",
    "rollback",
    "when_to_use",
    "when_not_to_use",
}
VALID_MCP_ATLAS_DECISIONS = {
    "experimental_read_only",
    "watchlist",
    "defer",
    "discard",
    "supporting_profile",
}
VALID_DOCS_SEARCH_CATALOG_STATUSES = {"active", "watchlist", "deprecated"}
PHASE_PLAYBOOK_PHASES = {"idea", "planning", "bootstrap", "build", "audit", "certified"}


def _primary_registry_path(root: Path) -> Path:
    return root / "commands" / "atomic_command_registry.json"


def _legacy_registry_path(root: Path) -> Path:
    return root / "00_SISTEMA" / "_meta" / "atlas" / "atomic_command_registry.json"


def _primary_mcp_policy_path(root: Path) -> Path:
    return root / "policies" / "mcp_connector_policy.md"


def _legacy_mcp_policy_path(root: Path) -> Path:
    return root / "00_SISTEMA" / "_meta" / "atlas" / "mcp_connector_policy.md"


def _primary_context_protocol_path(root: Path) -> Path:
    return root / "memory" / "context_refresh_protocol.md"


def _legacy_context_protocol_path(root: Path) -> Path:
    return root / "00_SISTEMA" / "_meta" / "atlas" / "context_refresh_protocol.md"


def _resolved_registry_path(root: Path, is_canonical_root: bool) -> Path:
    primary = _primary_registry_path(root)
    legacy = _legacy_registry_path(root)
    if is_canonical_root or primary.exists():
        return primary
    return legacy


def _read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _load_registry(root: Path, is_canonical_root: bool) -> dict:
    return json.loads(_resolved_registry_path(root, is_canonical_root).read_text(encoding="utf-8"))


def _load_project_state(root: Path) -> Dict[str, object]:
    return json.loads((root / "memory" / "project_state.json").read_text(encoding="utf-8"))


def _load_model_profiles(root: Path) -> Dict[str, Any]:
    return json.loads((root / "config" / "model_profiles.json").read_text(encoding="utf-8"))


def _load_model_routing_rules(root: Path) -> Dict[str, Any]:
    return json.loads((root / "config" / "model_routing_rules.json").read_text(encoding="utf-8"))


def _load_mcp_profiles(root: Path) -> Dict[str, Any]:
    return json.loads((root / "config" / "mcp_profiles.json").read_text(encoding="utf-8"))


def _load_docs_search_catalog(root: Path) -> Dict[str, Any]:
    return json.loads((root / "config" / "docs_search_catalog.json").read_text(encoding="utf-8"))


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _append_jsonl_record(path: Path, record: Dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(record, ensure_ascii=False) + "\n")


def _event_logging_enabled(root: Path) -> bool:
    if os.environ.get("ATLAS_DISABLE_EVENT_LOGS", "").strip() == "1":
        return False
    return root.resolve() == DEFAULT_ROOT.resolve()


def _record_governance_event(root: Path, project: Optional[Path], result: Dict[str, object]) -> None:
    if not _event_logging_enabled(root):
        return
    entry: Dict[str, Any] = {
        "timestamp": _utc_now_iso(),
        "root": str(root),
        "project": str(project.resolve()) if project else None,
        "profile": result.get("profile"),
        "ok": bool(result.get("ok")),
        "findings_count": len(list(result.get("findings", []))),
        "findings": list(result.get("findings", [])),
    }
    atlas = result.get("atlas")
    if isinstance(atlas, dict):
        entry["atlas_ok"] = bool(atlas.get("ok"))
    project_result = result.get("project")
    if isinstance(project_result, dict):
        entry["derived_project_ok"] = bool(project_result.get("ok"))
    try:
        mcp_profiles = _load_mcp_profiles(root)
        profiles = mcp_profiles.get("profiles", {})
        if isinstance(profiles, dict):
            entry["experimental_mcp_profiles"] = sorted(
                profile_id
                for profile_id, profile in profiles.items()
                if isinstance(profile, dict) and bool(profile.get("experimental_enabled"))
            )
    except Exception:
        entry["experimental_mcp_profiles"] = []
    _append_jsonl_record(root / "memory" / GOVERNANCE_EVENTS_LOG, entry)


def _finalize_governance_result(root: Path, project: Optional[Path], result: Dict[str, object]) -> Dict[str, object]:
    _record_governance_event(root, project, result)
    return result


def _find_forbidden_canonical_root_artifacts(root: Path) -> List[str]:
    findings: List[str] = []
    for rel in FORBIDDEN_CANONICAL_ROOT_ARTIFACTS:
        path = root / rel
        if path.exists():
            findings.append(f"forbidden_canonical_artifact:{rel}")
    return findings


def _validate_model_routing_rules(root: Path, findings: List[str]) -> None:
    try:
        rules = _load_model_routing_rules(root)
        profiles = _load_model_profiles(root)
    except Exception as exc:
        findings.append(f"invalid_model_routing_rules_json:{exc}")
        return

    if not isinstance(rules, dict):
        findings.append("model_routing_rules_not_object")
        return

    profile_names = set(profiles.get("profiles", {}).keys()) if isinstance(profiles, dict) else set()
    aliases = rules.get("aliases")
    if not isinstance(aliases, dict) or not aliases:
        findings.append("model_routing_rules_missing_aliases")
        return

    default_profile_alias = str(rules.get("default_profile_alias", "")).strip()
    default_fallback_alias = str(rules.get("default_fallback_alias", "")).strip()
    if default_profile_alias not in aliases:
        findings.append(f"model_routing_rules_invalid_default_profile_alias:{default_profile_alias}")
    if default_fallback_alias not in aliases:
        findings.append(f"model_routing_rules_invalid_default_fallback_alias:{default_fallback_alias}")

    for alias_name, profile_name in aliases.items():
        if str(profile_name).strip() not in profile_names:
            findings.append(f"model_routing_rules_unknown_profile:{alias_name}:{profile_name}")

    for mapping_name in ("intent_aliases", "skill_aliases", "phase_bias", "fallback_by_alias"):
        mapping = rules.get(mapping_name)
        if not isinstance(mapping, dict) or not mapping:
            findings.append(f"model_routing_rules_invalid_mapping:{mapping_name}")
            continue
        for key, alias_name in mapping.items():
            if str(alias_name).strip() not in aliases:
                findings.append(f"model_routing_rules_unknown_alias:{mapping_name}:{key}:{alias_name}")


def _validate_mcp_profiles(root: Path, findings: List[str]) -> None:
    try:
        config = _load_mcp_profiles(root)
    except Exception as exc:
        findings.append(f"invalid_mcp_profiles_json:{exc}")
        return

    if str(config.get("default_policy", "")).strip() != "deny":
        findings.append("mcp_profiles_default_policy_must_be_deny")

    profiles = config.get("profiles")
    if not isinstance(profiles, dict) or not profiles:
        findings.append("mcp_profiles_missing_profiles")
        return

    experimental_profiles: List[str] = []
    for profile_id, profile in profiles.items():
        if not isinstance(profile, dict):
            findings.append(f"mcp_profile_invalid_object:{profile_id}")
            continue

        missing_fields = REQUIRED_MCP_PROFILE_FIELDS - set(profile.keys())
        if missing_fields:
            findings.append(f"mcp_profile_missing_fields:{profile_id}:{','.join(sorted(missing_fields))}")

        if str(profile.get("default_mode", "")).strip() != "read_only":
            findings.append(f"mcp_profile_invalid_default_mode:{profile_id}:{profile.get('default_mode')}")

        if not isinstance(profile.get("requires_approval"), bool):
            findings.append(f"mcp_profile_requires_approval_not_boolean:{profile_id}")

        if not isinstance(profile.get("experimental_enabled"), bool):
            findings.append(f"mcp_profile_experimental_enabled_not_boolean:{profile_id}")

        if str(profile.get("atlas_decision", "")).strip() not in VALID_MCP_ATLAS_DECISIONS:
            findings.append(f"mcp_profile_invalid_atlas_decision:{profile_id}:{profile.get('atlas_decision')}")

        for list_field in ("when_to_use", "when_not_to_use"):
            value = profile.get(list_field)
            if not isinstance(value, list) or not value or not all(isinstance(item, str) and item.strip() for item in value):
                findings.append(f"mcp_profile_invalid_list:{profile_id}:{list_field}")

        if bool(profile.get("experimental_enabled")):
            experimental_profiles.append(profile_id)
            if str(profile.get("atlas_decision", "")).strip() != "experimental_read_only":
                findings.append(f"mcp_profile_experimental_requires_decision:{profile_id}")
            if not bool(profile.get("requires_approval")):
                findings.append(f"mcp_profile_experimental_requires_approval:{profile_id}")

    if len(experimental_profiles) > 1:
        findings.append(f"mcp_profiles_multiple_experimental:{','.join(sorted(experimental_profiles))}")


def _validate_docs_search_catalog(root: Path, findings: List[str]) -> None:
    try:
        catalog = _load_docs_search_catalog(root)
    except Exception as exc:
        findings.append(f"invalid_docs_search_catalog_json:{exc}")
        return

    if not isinstance(catalog, dict):
        findings.append("docs_search_catalog_not_object")
        return

    entries = catalog.get("entries")
    if not isinstance(entries, list) or not entries:
        findings.append("docs_search_catalog_missing_entries")
        return

    seen_ids: Set[str] = set()
    seen_urls: Set[str] = set()

    for idx, entry in enumerate(entries, start=1):
        label = f"docs_search_catalog_entry_{idx}"
        if not isinstance(entry, dict):
            findings.append(f"{label}:not_object")
            continue

        entry_id = str(entry.get("id", "")).strip()
        title = str(entry.get("title", "")).strip()
        url = str(entry.get("url", "")).strip()
        source_type = str(entry.get("source_type", "")).strip()
        description = str(entry.get("description", "")).strip()
        topics = entry.get("topics")
        last_verified = str(entry.get("last_verified", "")).strip()
        freshness_window_days = entry.get("freshness_window_days")
        status = str(entry.get("status", "")).strip()

        if not entry_id:
            findings.append(f"{label}:missing_id")
        elif entry_id in seen_ids:
            findings.append(f"docs_search_catalog_duplicate_id:{entry_id}")
        else:
            seen_ids.add(entry_id)

        if not title:
            findings.append(f"{label}:missing_title")

        if not url:
            findings.append(f"{label}:missing_url")
        elif url in seen_urls:
            findings.append(f"docs_search_catalog_duplicate_url:{url}")
        else:
            seen_urls.add(url)

        if not source_type:
            findings.append(f"{label}:missing_source_type")

        if not isinstance(topics, list) or not topics or not all(isinstance(item, str) and item.strip() for item in topics):
            findings.append(f"{label}:invalid_topics")

        if not description:
            findings.append(f"{label}:missing_description")

        try:
            datetime.strptime(last_verified, "%Y-%m-%d")
        except ValueError:
            findings.append(f"{label}:invalid_last_verified:{last_verified or 'empty'}")

        if not isinstance(freshness_window_days, int) or freshness_window_days <= 0:
            findings.append(f"{label}:invalid_freshness_window_days:{freshness_window_days}")

        if status not in VALID_DOCS_SEARCH_CATALOG_STATUSES:
            findings.append(f"{label}:invalid_status:{status}")


def _validate_phase_playbook(root: Path, findings: List[str]) -> None:
    path = root / "config" / "phase_playbook.json"
    try:
        playbook = json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:
        findings.append(f"invalid_phase_playbook_json:{exc}")
        return

    if not isinstance(playbook, dict):
        findings.append("phase_playbook_not_object")
        return

    missing_phases = PHASE_PLAYBOOK_PHASES - set(playbook.keys())
    if missing_phases:
        findings.append(f"phase_playbook_missing_phases:{','.join(sorted(missing_phases))}")

    for phase_name in sorted(PHASE_PLAYBOOK_PHASES):
        item = playbook.get(phase_name)
        if not isinstance(item, dict):
            findings.append(f"phase_playbook_invalid_phase_object:{phase_name}")
            continue
        for field in ("allowed_commands", "recommended_actions", "common_mistakes"):
            value = item.get(field)
            if not isinstance(value, list):
                findings.append(f"phase_playbook_invalid_list:{phase_name}:{field}")
                continue
            if field != "allowed_commands" and not value:
                findings.append(f"phase_playbook_empty_list:{phase_name}:{field}")
            if any(not isinstance(entry, str) or not entry.strip() for entry in value):
                findings.append(f"phase_playbook_invalid_list_item:{phase_name}:{field}")


def _load_skill_behavior_specs(root: Path) -> Dict[str, Dict[str, Any]]:
    behavior_specs: Dict[str, Dict[str, Any]] = {}
    skills_dir = root / "skills"
    if not skills_dir.exists():
        return behavior_specs

    for skill_dir in sorted(path for path in skills_dir.iterdir() if path.is_dir() and not path.name.startswith("_")):
        behavior_path = skill_dir / "behavior.json"
        if not behavior_path.exists():
            continue
        behavior = _load_json(behavior_path)
        if isinstance(behavior, dict):
            behavior_specs[skill_dir.name] = behavior
    return behavior_specs


def _derived_project_metadata_path(project_root: Path) -> Path:
    return project_root / ".atlas-project.json"


def _load_json(path: Path) -> Dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def _extract_template_placeholders(template_text: str) -> List[Tuple[str, str]]:
    placeholders: List[Tuple[str, str]] = []
    for match in BOOTSTRAP_TEMPLATE_PLACEHOLDER_RE.finditer(template_text):
        raw = match.group(0)
        name = (
            match.group("double_name")
            or match.group("dollar_name")
            or match.group("single_name")
            or ""
        )
        if name:
            placeholders.append((raw, name))
    return placeholders


def _render_template_with_sample_values(template_text: str, values: Dict[str, str]) -> str:
    rendered = template_text
    for key, value in values.items():
        rendered = rendered.replace(f"{{{{{key}}}}}", value)
        rendered = rendered.replace(f"${{{key}}}", value)
        rendered = rendered.replace(f"{{{key}}}", value)
    return rendered


def _sample_bootstrap_template_values(project_type: str) -> Dict[str, str]:
    return {
        "project_name": "Atlas Sandbox Sample",
        "project_type": project_type,
        "project_goal": f"Sample bootstrap goal for `{project_type}`.",
        "scope": "- Define the initial scaffold.\n- Keep runtime implementation out of bootstrap.",
        "atlas_root": str(DEFAULT_ROOT),
        "generated_from_skill": "project-bootstrap",
    }


def _is_valid_string_list(value: Any) -> bool:
    return isinstance(value, list) and bool(value) and all(isinstance(item, str) and item.strip() for item in value)


def _is_string_list(value: Any) -> bool:
    return isinstance(value, list) and all(isinstance(item, str) and item.strip() for item in value)


def _is_canonical_root(root: Path) -> bool:
    return root.resolve() == DEFAULT_ROOT.resolve()


def _resolve_adapter_surface(root: Path) -> Tuple[Path, Path, Path]:
    registry = _primary_registry_path(root)
    if not registry.exists():
        registry = _legacy_registry_path(root)

    mcp_policy = _primary_mcp_policy_path(root)
    if not mcp_policy.exists():
        mcp_policy = _legacy_mcp_policy_path(root)

    context_protocol = _primary_context_protocol_path(root)
    if not context_protocol.exists():
        context_protocol = _legacy_context_protocol_path(root)

    return registry, mcp_policy, context_protocol


def _validate_skill_metadata(
    root: Path,
    skill_dir: Path,
    metadata: Dict[str, Any],
    available_model_profiles: Set[str],
    findings: List[str],
) -> None:
    skill_name = skill_dir.name
    missing_fields = SKILL_REQUIRED_FIELDS - set(metadata.keys())
    if missing_fields:
        findings.append(f"skill_{skill_name}:missing_fields:{','.join(sorted(missing_fields))}")

    declared_name = str(metadata.get("name", "")).strip()
    if declared_name != skill_name:
        findings.append(f"skill_{skill_name}:name_mismatch:{declared_name or 'empty'}")

    agent_name = str(metadata.get("agent", "")).strip()
    if not agent_name:
        findings.append(f"skill_{skill_name}:empty_agent")
    elif not (root / "agents" / f"{agent_name}.md").exists():
        findings.append(f"skill_{skill_name}:missing_agent:{agent_name}")

    workflow_name = str(metadata.get("workflow", "")).strip()
    if not workflow_name:
        findings.append(f"skill_{skill_name}:empty_workflow")
    elif not (root / "workflows" / f"{workflow_name}.md").exists():
        findings.append(f"skill_{skill_name}:missing_workflow:{workflow_name}")

    model_profile = str(metadata.get("model_profile", "")).strip()
    if not model_profile:
        findings.append(f"skill_{skill_name}:empty_model_profile")
    elif model_profile not in available_model_profiles:
        findings.append(f"skill_{skill_name}:missing_model_profile:{model_profile}")

    risk_level = str(metadata.get("risk_level", "")).strip()
    if risk_level not in VALID_SKILL_RISK_LEVELS:
        findings.append(f"skill_{skill_name}:invalid_risk_level:{risk_level}")

    if not isinstance(metadata.get("requires_human_approval"), bool):
        findings.append(f"skill_{skill_name}:requires_human_approval_not_boolean")

    if not isinstance(metadata.get("supports_execution"), bool):
        findings.append(f"skill_{skill_name}:supports_execution_not_boolean")

    if not _is_valid_string_list(metadata.get("intent_keywords")):
        findings.append(f"skill_{skill_name}:invalid_intent_keywords")

    if not _is_valid_string_list(metadata.get("expected_outputs")):
        findings.append(f"skill_{skill_name}:invalid_expected_outputs")

    if not _is_valid_string_list(metadata.get("validations")):
        findings.append(f"skill_{skill_name}:invalid_validations")

    if not _is_valid_string_list(metadata.get("required_inputs")):
        findings.append(f"skill_{skill_name}:invalid_required_inputs")

    if not _is_valid_string_list(metadata.get("safety_limits")):
        findings.append(f"skill_{skill_name}:invalid_safety_limits")

    if not _is_valid_string_list(metadata.get("rollback_manual")):
        findings.append(f"skill_{skill_name}:invalid_rollback_manual")

    execution_mode = str(metadata.get("execution_mode", "")).strip()
    if execution_mode not in VALID_EXECUTION_MODES:
        findings.append(f"skill_{skill_name}:invalid_execution_mode:{execution_mode}")

    allowed_paths_policy = str(metadata.get("allowed_paths_policy", "")).strip()
    if allowed_paths_policy not in VALID_SKILL_ALLOWED_PATHS_POLICIES:
        findings.append(f"skill_{skill_name}:invalid_allowed_paths_policy:{allowed_paths_policy}")

    if not _is_valid_string_list(metadata.get("forbidden_actions")):
        findings.append(f"skill_{skill_name}:invalid_forbidden_actions")

    if not _is_valid_string_list(metadata.get("human_approval_triggers")):
        findings.append(f"skill_{skill_name}:invalid_human_approval_triggers")


def _validate_behavior_metadata(skill_name: str, behavior: Dict[str, Any], findings: List[str]) -> None:
    missing_fields = BEHAVIOR_REQUIRED_FIELDS - set(behavior.keys())
    if missing_fields:
        findings.append(f"skill_{skill_name}:behavior_missing_fields:{','.join(sorted(missing_fields))}")

    for bool_field in (
        "writes_files",
        "writes_code",
        "uses_output_dir",
        "read_only",
        "requires_project_path",
        "requires_output_dir",
        "can_run_without_approval",
    ):
        if not isinstance(behavior.get(bool_field), bool):
            findings.append(f"skill_{skill_name}:behavior_invalid_boolean:{bool_field}")

    execution_helper = str(behavior.get("execution_helper", "")).strip()
    if not execution_helper:
        findings.append(f"skill_{skill_name}:behavior_invalid_execution_helper")

    if not _is_valid_string_list(behavior.get("side_effects")):
        findings.append(f"skill_{skill_name}:behavior_invalid_side_effects")

    if not _is_valid_string_list(behavior.get("notes")):
        findings.append(f"skill_{skill_name}:behavior_invalid_notes")


def _validate_skill_behavior_consistency(
    skill_name: str,
    metadata: Dict[str, Any],
    behavior_specs: Dict[str, Dict[str, Any]],
    findings: List[str],
) -> None:
    behavior = behavior_specs.get(skill_name)
    if not behavior:
        findings.append(f"skill_{skill_name}:missing_behavior_spec")
        return

    declared_execution_mode = str(metadata.get("execution_mode", "")).strip()
    declared_allowed_paths_policy = str(metadata.get("allowed_paths_policy", "")).strip()
    declared_supports_execution = bool(metadata.get("supports_execution"))
    behavior_can_run_without_approval = bool(behavior.get("can_run_without_approval"))

    expected_execution_mode = "read_only" if bool(behavior.get("read_only")) else "write_docs"
    if bool(behavior.get("writes_code")):
        expected_execution_mode = "write_code"
    if declared_execution_mode != expected_execution_mode:
        findings.append(
            f"skill_{skill_name}:behavior_execution_mode_mismatch:{declared_execution_mode}->{expected_execution_mode}"
        )

    expected_allowed_paths_policy = "no_filesystem_writes"
    if bool(behavior.get("uses_output_dir")):
        expected_allowed_paths_policy = "explicit_output_dir_only"
    elif bool(behavior.get("writes_files")) or bool(behavior.get("requires_project_path")):
        expected_allowed_paths_policy = "atlas_root_or_derived_project_read_only"
    if declared_allowed_paths_policy != expected_allowed_paths_policy:
        findings.append(
            f"skill_{skill_name}:behavior_allowed_paths_policy_mismatch:{declared_allowed_paths_policy}->{expected_allowed_paths_policy}"
        )

    if declared_supports_execution is not True:
        findings.append(f"skill_{skill_name}:behavior_supports_execution_mismatch")

    if declared_execution_mode == "read_only" and bool(behavior.get("writes_files")):
        findings.append(f"skill_{skill_name}:read_only_but_behavior_writes_files")

    if declared_execution_mode == "write_docs" and bool(behavior.get("writes_code")):
        findings.append(f"skill_{skill_name}:write_docs_but_behavior_writes_code")

    if declared_allowed_paths_policy == "explicit_output_dir_only" and not bool(behavior.get("requires_output_dir")):
        findings.append(f"skill_{skill_name}:explicit_output_dir_only_without_output_dir_behavior")

    if declared_allowed_paths_policy == "no_filesystem_writes" and bool(behavior.get("writes_files")):
        findings.append(f"skill_{skill_name}:no_filesystem_writes_but_behavior_writes_files")

    if behavior_can_run_without_approval and bool(metadata.get("requires_human_approval")):
        findings.append(f"skill_{skill_name}:approval_default_mismatch")


def _validate_bootstrap_contract(root: Path, contract: Dict[str, Any], findings: List[str]) -> None:
    missing_fields = BOOTSTRAP_CONTRACT_REQUIRED_FIELDS - set(contract.keys())
    if missing_fields:
        findings.append(f"skill_project-bootstrap:bootstrap_contract_missing_fields:{','.join(sorted(missing_fields))}")

    if not _is_valid_string_list(contract.get("required_inputs")):
        findings.append("skill_project-bootstrap:bootstrap_contract_invalid_required_inputs")

    optional_inputs = contract.get("optional_inputs")
    if not isinstance(optional_inputs, list) or not _is_string_list(optional_inputs):
        findings.append("skill_project-bootstrap:bootstrap_contract_invalid_optional_inputs")

    supported_project_types = contract.get("supported_project_types")
    if not _is_valid_string_list(supported_project_types):
        findings.append("skill_project-bootstrap:bootstrap_contract_invalid_supported_project_types")
        supported_project_types = []
    else:
        missing_types = REQUIRED_BOOTSTRAP_PROJECT_TYPES - set(supported_project_types)
        if missing_types:
            findings.append(
                f"skill_project-bootstrap:bootstrap_contract_missing_supported_project_types:{','.join(sorted(missing_types))}"
            )

    default_project_type = str(contract.get("default_project_type", "")).strip()
    if not default_project_type:
        findings.append("skill_project-bootstrap:bootstrap_contract_invalid_default_project_type")
    elif default_project_type not in set(supported_project_types):
        findings.append(f"skill_project-bootstrap:bootstrap_contract_default_project_type_not_supported:{default_project_type}")

    generated_structure = contract.get("generated_structure")
    if not isinstance(generated_structure, dict):
        findings.append("skill_project-bootstrap:bootstrap_contract_invalid_generated_structure")
    else:
        directories = generated_structure.get("directories")
        if not _is_valid_string_list(directories):
            findings.append("skill_project-bootstrap:bootstrap_contract_invalid_generated_directories")

    if not _is_valid_string_list(contract.get("required_files")):
        findings.append("skill_project-bootstrap:bootstrap_contract_invalid_required_files")

    optional_files = contract.get("optional_files")
    if not isinstance(optional_files, list) or not _is_string_list(optional_files):
        findings.append("skill_project-bootstrap:bootstrap_contract_invalid_optional_files")

    if not _is_valid_string_list(contract.get("forbidden_outputs")):
        findings.append("skill_project-bootstrap:bootstrap_contract_invalid_forbidden_outputs")

    default_output_mode = str(contract.get("default_output_mode", "")).strip()
    if not default_output_mode:
        findings.append("skill_project-bootstrap:bootstrap_contract_invalid_default_output_mode")

    templates_by_type = contract.get("templates_by_type")
    if not isinstance(templates_by_type, dict) or not templates_by_type:
        findings.append("skill_project-bootstrap:bootstrap_contract_invalid_templates_by_type")
    else:
        for project_type in REQUIRED_BOOTSTRAP_PROJECT_TYPES:
            template = templates_by_type.get(project_type)
            if not isinstance(template, dict):
                findings.append(f"skill_project-bootstrap:bootstrap_contract_missing_template:{project_type}")
                continue
            if not str(template.get("label", "")).strip():
                findings.append(f"skill_project-bootstrap:bootstrap_contract_invalid_template_label:{project_type}")
            if not str(template.get("description", "")).strip():
                findings.append(f"skill_project-bootstrap:bootstrap_contract_invalid_template_description:{project_type}")
            readme_template = str(template.get("readme_template", "")).strip()
            if not readme_template:
                findings.append(f"skill_project-bootstrap:bootstrap_contract_invalid_readme_template:{project_type}")
            elif not (root / readme_template).exists():
                findings.append(f"skill_project-bootstrap:bootstrap_contract_missing_readme_template_file:{project_type}")
            agents_template = str(template.get("agents_template", "")).strip()
            if not agents_template:
                findings.append(f"skill_project-bootstrap:bootstrap_contract_invalid_agents_template:{project_type}")
            elif not (root / agents_template).exists():
                findings.append(f"skill_project-bootstrap:bootstrap_contract_missing_agents_template_file:{project_type}")
            if not _is_valid_string_list(template.get("additional_directories")):
                findings.append(f"skill_project-bootstrap:bootstrap_contract_invalid_template_directories:{project_type}")
            if not _is_valid_string_list(template.get("readme_focus")):
                findings.append(f"skill_project-bootstrap:bootstrap_contract_invalid_template_readme_focus:{project_type}")
            if not _is_valid_string_list(template.get("agents_focus")):
                findings.append(f"skill_project-bootstrap:bootstrap_contract_invalid_template_agents_focus:{project_type}")
            if not _is_valid_string_list(template.get("example_usage")):
                findings.append(f"skill_project-bootstrap:bootstrap_contract_invalid_template_example_usage:{project_type}")

    initial_content = contract.get("initial_content")
    if not isinstance(initial_content, dict):
        findings.append("skill_project-bootstrap:bootstrap_contract_invalid_initial_content")
    else:
        for field in ("readme_sections", "agents_sections", "metadata_fields"):
            if not _is_valid_string_list(initial_content.get(field)):
                findings.append(f"skill_project-bootstrap:bootstrap_contract_invalid_initial_content_field:{field}")

    if not _is_valid_string_list(contract.get("rollback_manual")):
        findings.append("skill_project-bootstrap:bootstrap_contract_invalid_rollback_manual")

    if not _is_valid_string_list(contract.get("validation_steps")):
        findings.append("skill_project-bootstrap:bootstrap_contract_invalid_validation_steps")

    if not _is_valid_string_list(contract.get("safety_limits")):
        findings.append("skill_project-bootstrap:bootstrap_contract_invalid_safety_limits")

    if not _is_valid_string_list(contract.get("human_approval_triggers")):
        findings.append("skill_project-bootstrap:bootstrap_contract_invalid_human_approval_triggers")


def _validate_bootstrap_templates(root: Path, contract: Dict[str, Any], findings: List[str]) -> None:
    templates_by_type = contract.get("templates_by_type")
    if not isinstance(templates_by_type, dict):
        return

    initial_content = contract.get("initial_content", {})
    readme_sections = list(initial_content.get("readme_sections", [])) if isinstance(initial_content, dict) else []
    agents_sections = list(initial_content.get("agents_sections", [])) if isinstance(initial_content, dict) else []

    for project_type in REQUIRED_BOOTSTRAP_PROJECT_TYPES:
        template = templates_by_type.get(project_type)
        if not isinstance(template, dict):
            continue

        sample_values = _sample_bootstrap_template_values(project_type)
        template_specs = (
            ("readme_template", "README", readme_sections),
            ("agents_template", "AGENTS", agents_sections),
        )

        for field_name, template_label, required_sections in template_specs:
            relative_path = str(template.get(field_name, "")).strip()
            if not relative_path:
                continue

            template_path = root / relative_path
            if not template_path.exists():
                continue

            template_text = _read_text(template_path)
            placeholders = _extract_template_placeholders(template_text)
            for raw_placeholder, placeholder_name in placeholders:
                if placeholder_name not in ALLOWED_BOOTSTRAP_TEMPLATE_PLACEHOLDERS:
                    findings.append(
                        "skill_project-bootstrap:"
                        "bootstrap_contract_invalid_template_placeholder:"
                        f"profile={project_type}:template={template_label}:file={relative_path}:"
                        f"placeholder={raw_placeholder}:"
                        "recommendation=replace_with_whitelisted_placeholder_or_static_text"
                    )

            rendered = _render_template_with_sample_values(template_text, sample_values)
            unresolved = _extract_template_placeholders(rendered)
            for raw_placeholder, placeholder_name in unresolved:
                findings.append(
                    "skill_project-bootstrap:"
                    "bootstrap_contract_unresolved_template_placeholder:"
                    f"profile={project_type}:template={template_label}:file={relative_path}:"
                    f"placeholder={raw_placeholder}:"
                    "recommendation=ensure_the_placeholder_is_whitelisted_and_rendered_or_convert_it_to_static_text"
                )

            if sample_values["project_name"] not in rendered:
                findings.append(
                    f"skill_project-bootstrap:bootstrap_contract_missing_rendered_project_name:{project_type}:{template_label}"
                )
            if sample_values["project_type"] not in rendered:
                findings.append(
                    f"skill_project-bootstrap:bootstrap_contract_missing_rendered_project_type:{project_type}:{template_label}"
                )

            if template_label == "README":
                for expected in (sample_values["generated_from_skill"], sample_values["atlas_root"]):
                    if expected not in rendered:
                        findings.append(
                            f"skill_project-bootstrap:bootstrap_contract_missing_rendered_readme_content:{project_type}:{expected}"
                        )

            for section in required_sections:
                expected_heading = f"## {section}"
                if expected_heading not in rendered:
                    findings.append(
                        f"skill_project-bootstrap:bootstrap_contract_missing_template_section:{project_type}:{template_label}:{section}"
                    )


def _validate_bootstrap_contract_consistency(
    metadata: Dict[str, Any],
    behavior: Dict[str, Any],
    contract: Dict[str, Any],
    findings: List[str],
) -> None:
    if list(metadata.get("required_inputs", [])) != list(contract.get("required_inputs", [])):
        findings.append("skill_project-bootstrap:bootstrap_contract_required_inputs_mismatch")

    if "project_type" not in list(contract.get("optional_inputs", [])):
        findings.append("skill_project-bootstrap:bootstrap_contract_missing_optional_project_type")

    if list(metadata.get("rollback_manual", [])) != list(contract.get("rollback_manual", [])):
        findings.append("skill_project-bootstrap:bootstrap_contract_rollback_mismatch")

    if list(metadata.get("safety_limits", [])) != list(contract.get("safety_limits", [])):
        findings.append("skill_project-bootstrap:bootstrap_contract_safety_limits_mismatch")

    if list(metadata.get("human_approval_triggers", [])) != list(contract.get("human_approval_triggers", [])):
        findings.append("skill_project-bootstrap:bootstrap_contract_approval_triggers_mismatch")

    if list(metadata.get("validations", [])) != list(contract.get("validation_steps", [])):
        findings.append("skill_project-bootstrap:bootstrap_contract_validation_steps_mismatch")

    declared_dirs = list(metadata.get("generated_structure", {}).get("directories", []))
    declared_files = list(metadata.get("generated_structure", {}).get("files", []))
    contract_dirs = list(contract.get("generated_structure", {}).get("directories", []))
    contract_files = list(contract.get("required_files", []))
    if declared_dirs != contract_dirs:
        findings.append("skill_project-bootstrap:bootstrap_contract_generated_directories_mismatch")
    if declared_files != contract_files:
        findings.append("skill_project-bootstrap:bootstrap_contract_required_files_mismatch")

    if bool(behavior.get("requires_output_dir")) and "output_dir" not in list(contract.get("required_inputs", [])):
        findings.append("skill_project-bootstrap:bootstrap_contract_missing_output_dir_input")

    if bool(behavior.get("uses_output_dir")) and str(metadata.get("allowed_paths_policy", "")).strip() != "explicit_output_dir_only":
        findings.append("skill_project-bootstrap:bootstrap_contract_output_dir_policy_mismatch")


def _validate_skill_catalog(root: Path, findings: List[str]) -> None:
    skills_dir = root / "skills"
    try:
        model_profiles = _load_model_profiles(root)
    except Exception as exc:
        findings.append(f"invalid_model_profiles_json:{exc}")
        return

    try:
        behavior_specs = _load_skill_behavior_specs(root)
    except Exception as exc:
        findings.append(f"invalid_skill_behavior_specs:{exc}")
        return

    available_profiles = set(model_profiles.get("profiles", {}).keys()) if isinstance(model_profiles, dict) else set()
    if not available_profiles:
        findings.append("model_profiles_empty_or_invalid")
        return

    for skill_dir in sorted(path for path in skills_dir.iterdir() if path.is_dir() and not path.name.startswith("_")):
        skill_md = skill_dir / "skill.md"
        skill_json = skill_dir / "skill.json"
        behavior_json = skill_dir / "behavior.json"
        bootstrap_contract_json = skill_dir / "bootstrap_contract.json"
        skill_name = skill_dir.name

        if not skill_md.exists():
            findings.append(f"skill_{skill_name}:missing_skill_md")
        if not skill_json.exists():
            findings.append(f"skill_{skill_name}:missing_skill_json")
            continue
        if not behavior_json.exists():
            findings.append(f"skill_{skill_name}:missing_behavior_json")
            continue

        try:
            metadata = _load_json(skill_json)
        except Exception as exc:
            findings.append(f"skill_{skill_name}:invalid_skill_json:{exc}")
            continue

        if not isinstance(metadata, dict):
            findings.append(f"skill_{skill_name}:skill_json_not_object")
            continue

        try:
            behavior = _load_json(behavior_json)
        except Exception as exc:
            findings.append(f"skill_{skill_name}:invalid_behavior_json:{exc}")
            continue

        if not isinstance(behavior, dict):
            findings.append(f"skill_{skill_name}:behavior_json_not_object")
            continue

        _validate_skill_metadata(root, skill_dir, metadata, available_profiles, findings)
        _validate_behavior_metadata(skill_name, behavior, findings)
        _validate_skill_behavior_consistency(skill_name, metadata, behavior_specs, findings)

        if skill_name == "project-bootstrap":
            if not bootstrap_contract_json.exists():
                findings.append("skill_project-bootstrap:missing_bootstrap_contract_json")
                continue
            try:
                bootstrap_contract = _load_json(bootstrap_contract_json)
            except Exception as exc:
                findings.append(f"skill_project-bootstrap:invalid_bootstrap_contract_json:{exc}")
                continue
            if not isinstance(bootstrap_contract, dict):
                findings.append("skill_project-bootstrap:bootstrap_contract_not_object")
                continue
            _validate_bootstrap_contract(root, bootstrap_contract, findings)
            _validate_bootstrap_templates(root, bootstrap_contract, findings)
            _validate_bootstrap_contract_consistency(metadata, behavior, bootstrap_contract, findings)


def _check_legacy_mirror(primary: Path, legacy: Path, label: str, findings: List[str]) -> None:
    if not legacy.exists():
        findings.append(f"missing_legacy_compat:{legacy.relative_to(DEFAULT_ROOT)}")
        return
    if _read_text(primary) != _read_text(legacy):
        findings.append(f"legacy_mismatch:{label}")


def _find_project_residues(project_root: Path) -> List[str]:
    findings: List[str] = []
    for rel in DEPRECATED_ACTIVE_ATLAS_PATHS:
        path = project_root / rel
        if path.exists():
            findings.append(f"deprecated_atlas_residue:{rel}")
    return findings


def _validate_derived_project(project_root: Path) -> Dict[str, object]:
    findings: List[str] = []
    metadata_path = _derived_project_metadata_path(project_root)
    if not metadata_path.exists():
        return {"ok": False, "findings": ["missing_file:.atlas-project.json"], "profile": "derived_project"}

    try:
        metadata = _load_json(metadata_path)
    except Exception as exc:
        return {"ok": False, "findings": [f"invalid_project_metadata_json:{exc}"], "profile": "derived_project"}

    if not isinstance(metadata, dict):
        return {"ok": False, "findings": ["project_metadata_not_object"], "profile": "derived_project"}

    missing_keys = REQUIRED_DERIVED_PROJECT_KEYS - set(metadata.keys())
    if missing_keys:
        findings.append(f"missing_project_metadata_keys:{','.join(sorted(missing_keys))}")

    if metadata.get("project_type") != DERIVED_PROJECT_TYPE:
        findings.append(f"invalid_project_type:{metadata.get('project_type')}")

    atlas_root = str(metadata.get("atlas_root", "")).strip()
    if atlas_root != str(DEFAULT_ROOT):
        findings.append(f"unexpected_atlas_root:{atlas_root}")

    audit_paths = metadata.get("audit_paths")
    if not isinstance(audit_paths, list) or not audit_paths:
        findings.append("invalid_project_audit_paths")

    legacy_paths = metadata.get("legacy_paths", [])
    if legacy_paths and not isinstance(legacy_paths, list):
        findings.append("invalid_legacy_paths")

    findings.extend(_find_project_residues(project_root))

    return {
        "ok": not findings,
        "findings": findings,
        "profile": "derived_project",
        "metadata_path": str(metadata_path),
        "metadata": metadata,
    }


def run_check(root: Optional[Path] = None, project: Optional[Path] = None) -> Dict[str, object]:
    root = (root or DEFAULT_ROOT).resolve()
    findings: List[str] = []

    is_canonical_root = _is_canonical_root(root)
    if is_canonical_root:
        for rel in PRIMARY_STRUCTURE_FILES:
            path = root / rel
            if not path.exists():
                findings.append(f"missing_file:{rel}")

        for rel in REQUIRED_ROOT_FILES:
            path = root / rel
            if not path.exists():
                findings.append(f"missing_file:{rel}")

        for rel in REQUIRED_DIRS:
            path = root / rel
            if not path.exists():
                findings.append(f"missing_dir:{rel}")
            elif not path.is_dir():
                findings.append(f"not_a_directory:{rel}")
        findings.extend(_find_forbidden_canonical_root_artifacts(root))
    else:
        registry_path, mcp_policy_path, context_protocol_path = _resolve_adapter_surface(root)
        for path, label in (
            (registry_path, "registry"),
            (mcp_policy_path, "mcp_connector_policy"),
            (context_protocol_path, "context_refresh_protocol"),
        ):
            if not path.exists():
                findings.append(f"missing_adapter_surface:{label}")

    if findings:
        return _finalize_governance_result(
            root,
            project.resolve() if project else None,
            {"ok": False, "findings": findings, "profile": "canonical" if is_canonical_root else "adapter"},
        )

    try:
        registry = _load_registry(root, is_canonical_root)
    except Exception as exc:
        return _finalize_governance_result(
            root,
            project.resolve() if project else None,
            {"ok": False, "findings": [f"invalid_registry_json:{exc}"], "profile": "canonical" if is_canonical_root else "adapter"},
        )

    project_state: Dict[str, object] = {}
    if is_canonical_root:
        try:
            project_state = _load_project_state(root)
        except Exception as exc:
            return _finalize_governance_result(
                root,
                project.resolve() if project else None,
                {"ok": False, "findings": [f"invalid_project_state_json:{exc}"], "profile": "canonical"},
            )

    missing_top_level = REQUIRED_TOP_LEVEL - set(registry.keys())
    if missing_top_level:
        findings.append(f"missing_top_level:{','.join(sorted(missing_top_level))}")

    commands = registry.get("commands", [])
    if not isinstance(commands, list) or not commands:
        findings.append("commands_empty_or_invalid")
        return _finalize_governance_result(
            root,
            project.resolve() if project else None,
            {"ok": False, "findings": findings, "profile": "canonical" if is_canonical_root else "adapter"},
        )

    seen_ids: Set[str] = set()
    seen_aliases: Set[str] = set()

    for idx, command in enumerate(commands, start=1):
        if not isinstance(command, dict):
            findings.append(f"command_{idx}:invalid_object")
            continue

        missing_fields = REQUIRED_COMMAND_FIELDS - set(command.keys())
        if missing_fields:
            findings.append(f"command_{idx}:missing_fields:{','.join(sorted(missing_fields))}")

        command_id = str(command.get("id", "")).strip()
        alias = str(command.get("alias", "")).strip()
        fit = str(command.get("fit", "")).strip()
        execution_mode = str(command.get("execution_mode", "")).strip()

        if not command_id:
            findings.append(f"command_{idx}:empty_id")
        elif command_id in seen_ids:
            findings.append(f"duplicate_id:{command_id}")
        else:
            seen_ids.add(command_id)

        if not alias:
            findings.append(f"command_{idx}:empty_alias")
        elif alias in seen_aliases:
            findings.append(f"duplicate_alias:{alias}")
        else:
            seen_aliases.add(alias)

        if fit not in VALID_FITS:
            findings.append(f"command_{idx}:invalid_fit:{fit}")

        if execution_mode not in VALID_EXECUTION_MODES:
            findings.append(f"command_{idx}:invalid_execution_mode:{execution_mode}")

        for list_field in ("allowed_paths", "guards", "outputs"):
            value = command.get(list_field)
            if not isinstance(value, list) or not value:
                findings.append(f"command_{idx}:invalid_list_field:{list_field}")

    if is_canonical_root:
        if not isinstance(project_state, dict):
            findings.append("project_state_not_object")
            return _finalize_governance_result(
                root,
                project.resolve() if project else None,
                {"ok": False, "findings": findings, "profile": "canonical"},
            )

        missing_state_keys = REQUIRED_PROJECT_STATE_KEYS - set(project_state.keys())
        if missing_state_keys:
            findings.append(f"missing_project_state_keys:{','.join(sorted(missing_state_keys))}")

        if not isinstance(project_state.get("restrictions"), dict):
            findings.append("project_state_invalid_restrictions")

        for list_field in ("executable_components", "documentary_components"):
            value = project_state.get(list_field)
            if not isinstance(value, list) or not value:
                findings.append(f"project_state_invalid_list:{list_field}")

        legacy_compatibility = project_state.get("legacy_compatibility")
        if not isinstance(legacy_compatibility, dict):
            findings.append("project_state_invalid_legacy_compatibility")

        _validate_model_routing_rules(root, findings)
        _validate_mcp_profiles(root, findings)
        _validate_docs_search_catalog(root, findings)
        _validate_phase_playbook(root, findings)
        _validate_skill_catalog(root, findings)
        _check_legacy_mirror(_primary_registry_path(root), _legacy_registry_path(root), "atomic_command_registry", findings)
        _check_legacy_mirror(_primary_mcp_policy_path(root), _legacy_mcp_policy_path(root), "mcp_connector_policy", findings)
        _check_legacy_mirror(_primary_context_protocol_path(root), _legacy_context_protocol_path(root), "context_refresh_protocol", findings)

    atlas_result = {"ok": not findings, "findings": findings, "profile": "canonical" if is_canonical_root else "adapter"}
    if project is None:
        return _finalize_governance_result(root, None, atlas_result)

    project_root = project.resolve()
    project_result = _validate_derived_project(project_root)
    combined_result = {
        "ok": bool(atlas_result["ok"]) and bool(project_result["ok"]),
        "findings": list(atlas_result["findings"]) + list(project_result["findings"]),
        "profile": "canonical+derived_project" if is_canonical_root else "adapter+derived_project",
        "atlas": atlas_result,
        "project": project_result,
    }
    return _finalize_governance_result(root, project_root, combined_result)


def format_report(result: Dict[str, object]) -> str:
    ok = bool(result["ok"])
    findings = list(result["findings"])
    profile = str(result.get("profile", "unknown")).upper()
    lines = ["ATLAS GOVERNANCE CHECK"]
    lines.append(f"PROFILE: {profile}")
    lines.append("OK" if ok else "FAILED")
    if findings:
        lines.append("Findings:")
        lines.extend(f"- {item}" for item in findings)
    else:
        lines.append("- root-first bootstrap structure, registry, policy and context protocol are consistent")
    return "\n".join(lines)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(add_help=True)
    parser.add_argument("--root", default=None, help="Workspace root to validate (defaults to this repo root).")
    parser.add_argument("--project", default=None, help="Derived project root to validate from Atlas.")
    args = parser.parse_args()
    root = Path(args.root).resolve() if args.root else None
    project = Path(args.project).resolve() if args.project else None
    print(format_report(run_check(root=root, project=project)))
