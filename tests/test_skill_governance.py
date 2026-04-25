import os
import json
from pathlib import Path
from unittest.mock import patch

os.environ["ATLAS_DISABLE_EVENT_LOGS"] = "1"

from tools.atlas_governance_check import (
    _find_forbidden_canonical_root_artifacts,
    _record_governance_event,
    _read_text,
    _validate_mcp_profiles,
    _validate_docs_search_catalog,
    _validate_bootstrap_contract,
    _validate_bootstrap_contract_consistency,
    _validate_bootstrap_templates,
    _validate_behavior_metadata,
    _validate_skill_behavior_consistency,
    _validate_skill_metadata,
    run_check,
)
from tools.atlas_orchestrator import get_project_bootstrap_contract, get_skill_execution_behavior_specs


ROOT = Path(r"C:\Proyectos\Codex-Atlas")


def test_current_skill_catalog_passes_governance():
    result = run_check(root=ROOT)
    assert result["ok"] is True


def test_skill_metadata_validation_rejects_invalid_contract_fields():
    findings = []
    skill_dir = ROOT / "skills" / "repo-audit"
    metadata = {
        "name": "repo-audit",
        "intent_keywords": ["audit repo"],
        "agent": "reality_checker",
        "workflow": "audit_project",
        "model_profile": "missing_profile",
        "risk_level": "severe",
        "requires_human_approval": "false",
        "supports_execution": "true",
        "expected_outputs": [],
        "validations": [],
        "required_inputs": [],
        "safety_limits": [],
        "rollback_manual": [],
        "execution_mode": "unsafe_write",
        "allowed_paths_policy": "all_paths",
        "forbidden_actions": [],
        "human_approval_triggers": [],
    }

    _validate_skill_metadata(ROOT, skill_dir, metadata, {"deep_reasoning", "creative_product"}, findings)

    assert "skill_repo-audit:missing_model_profile:missing_profile" in findings
    assert "skill_repo-audit:invalid_risk_level:severe" in findings
    assert "skill_repo-audit:requires_human_approval_not_boolean" in findings
    assert "skill_repo-audit:supports_execution_not_boolean" in findings
    assert "skill_repo-audit:invalid_expected_outputs" in findings
    assert "skill_repo-audit:invalid_validations" in findings
    assert "skill_repo-audit:invalid_required_inputs" in findings
    assert "skill_repo-audit:invalid_safety_limits" in findings
    assert "skill_repo-audit:invalid_rollback_manual" in findings
    assert "skill_repo-audit:invalid_execution_mode:unsafe_write" in findings
    assert "skill_repo-audit:invalid_allowed_paths_policy:all_paths" in findings
    assert "skill_repo-audit:invalid_forbidden_actions" in findings
    assert "skill_repo-audit:invalid_human_approval_triggers" in findings


def test_skill_metadata_validation_rejects_folder_name_mismatch():
    findings = []
    skill_dir = ROOT / "skills" / "product-branding-review"
    metadata = {
        "name": "brand-review",
        "intent_keywords": ["branding review"],
        "agent": "ux_brand",
        "workflow": "atlas_project_pipeline",
        "model_profile": "creative_product",
        "risk_level": "medium",
        "requires_human_approval": False,
        "supports_execution": True,
        "expected_outputs": ["branding review"],
        "validations": ["audience is explicit"],
        "required_inputs": ["product_context"],
        "safety_limits": ["do not write files"],
        "rollback_manual": ["no rollback needed because the skill is read-only"],
        "execution_mode": "read_only",
        "allowed_paths_policy": "no_filesystem_writes",
        "forbidden_actions": ["edit product runtime files automatically"],
        "human_approval_triggers": ["the task shifts from review to implementation"],
    }

    _validate_skill_metadata(ROOT, skill_dir, metadata, {"creative_product"}, findings)

    assert "skill_product-branding-review:name_mismatch:brand-review" in findings


def test_skill_behavior_consistency_rejects_declared_runtime_mismatch():
    findings = []
    metadata = {
        "name": "project-bootstrap",
        "execution_mode": "read_only",
        "allowed_paths_policy": "no_filesystem_writes",
        "supports_execution": True,
    }

    _validate_skill_behavior_consistency(
        "project-bootstrap",
        metadata,
        get_skill_execution_behavior_specs(),
        findings,
    )

    assert "skill_project-bootstrap:behavior_execution_mode_mismatch:read_only->write_docs" in findings
    assert "skill_project-bootstrap:behavior_allowed_paths_policy_mismatch:no_filesystem_writes->explicit_output_dir_only" in findings
    assert "skill_project-bootstrap:read_only_but_behavior_writes_files" in findings
    assert "skill_project-bootstrap:no_filesystem_writes_but_behavior_writes_files" in findings


def test_behavior_metadata_validation_rejects_invalid_behavior_contract():
    findings = []
    behavior = {
        "writes_files": "yes",
        "writes_code": False,
        "uses_output_dir": False,
        "read_only": True,
        "execution_helper": "",
        "side_effects": [],
        "requires_project_path": False,
        "requires_output_dir": False,
        "can_run_without_approval": "true",
        "notes": [],
    }

    _validate_behavior_metadata("repo-audit", behavior, findings)

    assert "skill_repo-audit:behavior_invalid_boolean:writes_files" in findings
    assert "skill_repo-audit:behavior_invalid_execution_helper" in findings
    assert "skill_repo-audit:behavior_invalid_side_effects" in findings
    assert "skill_repo-audit:behavior_invalid_boolean:can_run_without_approval" in findings
    assert "skill_repo-audit:behavior_invalid_notes" in findings


def test_bootstrap_contract_validation_rejects_invalid_contract():
    findings = []
    contract = {
        "required_inputs": [],
        "optional_inputs": "none",
        "supported_project_types": [],
        "default_project_type": "",
        "generated_structure": {"directories": []},
        "required_files": [],
        "optional_files": "none",
        "forbidden_outputs": [],
        "default_output_mode": "",
        "templates_by_type": {
            "backend_service": {
                "label": "",
                "description": "",
                "readme_template": "",
                "agents_template": "",
                "additional_directories": [],
                "readme_focus": [],
                "agents_focus": [],
                "example_usage": []
            }
        },
        "initial_content": {},
        "rollback_manual": [],
        "validation_steps": [],
        "safety_limits": [],
        "human_approval_triggers": [],
    }

    _validate_bootstrap_contract(ROOT, contract, findings)

    assert "skill_project-bootstrap:bootstrap_contract_invalid_required_inputs" in findings
    assert "skill_project-bootstrap:bootstrap_contract_invalid_optional_inputs" in findings
    assert "skill_project-bootstrap:bootstrap_contract_invalid_supported_project_types" in findings
    assert "skill_project-bootstrap:bootstrap_contract_invalid_default_project_type" in findings
    assert "skill_project-bootstrap:bootstrap_contract_invalid_generated_directories" in findings
    assert "skill_project-bootstrap:bootstrap_contract_invalid_required_files" in findings
    assert "skill_project-bootstrap:bootstrap_contract_invalid_optional_files" in findings
    assert "skill_project-bootstrap:bootstrap_contract_invalid_forbidden_outputs" in findings
    assert "skill_project-bootstrap:bootstrap_contract_invalid_default_output_mode" in findings
    assert "skill_project-bootstrap:bootstrap_contract_missing_template:frontend_app" in findings
    assert "skill_project-bootstrap:bootstrap_contract_invalid_readme_template:backend_service" in findings
    assert "skill_project-bootstrap:bootstrap_contract_invalid_agents_template:backend_service" in findings
    assert "skill_project-bootstrap:bootstrap_contract_invalid_initial_content_field:readme_sections" in findings
    assert "skill_project-bootstrap:bootstrap_contract_invalid_rollback_manual" in findings
    assert "skill_project-bootstrap:bootstrap_contract_invalid_validation_steps" in findings
    assert "skill_project-bootstrap:bootstrap_contract_invalid_safety_limits" in findings
    assert "skill_project-bootstrap:bootstrap_contract_invalid_human_approval_triggers" in findings


def test_bootstrap_contract_consistency_rejects_skill_mismatch():
    findings = []
    contract = get_project_bootstrap_contract()
    metadata = {
        "required_inputs": ["project_goal"],
        "rollback_manual": ["different rollback"],
        "safety_limits": ["different safety"],
        "human_approval_triggers": ["different trigger"],
        "validations": ["different validation"],
        "generated_structure": {"directories": ["docs"], "files": ["README.md"]},
        "allowed_paths_policy": "no_filesystem_writes",
    }
    behavior = get_skill_execution_behavior_specs()["project-bootstrap"]

    _validate_bootstrap_contract_consistency(metadata, behavior, contract, findings)

    assert "skill_project-bootstrap:bootstrap_contract_required_inputs_mismatch" in findings
    assert "skill_project-bootstrap:bootstrap_contract_rollback_mismatch" in findings
    assert "skill_project-bootstrap:bootstrap_contract_safety_limits_mismatch" in findings
    assert "skill_project-bootstrap:bootstrap_contract_approval_triggers_mismatch" in findings
    assert "skill_project-bootstrap:bootstrap_contract_validation_steps_mismatch" in findings
    assert "skill_project-bootstrap:bootstrap_contract_generated_directories_mismatch" in findings
    assert "skill_project-bootstrap:bootstrap_contract_required_files_mismatch" in findings
    assert "skill_project-bootstrap:bootstrap_contract_output_dir_policy_mismatch" in findings


def test_bootstrap_templates_render_cleanly_for_current_contract():
    findings = []
    _validate_bootstrap_templates(ROOT, get_project_bootstrap_contract(), findings)
    assert findings == []


def test_bootstrap_templates_reject_invalid_placeholders():
    invalid_templates = (
        ("README.invalid-double.template", "# {{project_name}}\n\nUnsupported {{profile_label}}\n", "{{profile_label}}"),
        ("README.invalid-single.template", "# {project_name}\n\nUnsupported {profile_label}\n", "{profile_label}"),
        ("README.invalid-dollar.template", "# ${project_name}\n\nUnsupported ${profile_label}\n", "${profile_label}"),
    )

    for template_name, template_text, expected_placeholder in invalid_templates:
        contract = get_project_bootstrap_contract()
        contract["templates_by_type"] = dict(contract["templates_by_type"])
        contract["templates_by_type"]["backend_service"] = dict(contract["templates_by_type"]["backend_service"])
        contract["templates_by_type"]["backend_service"]["readme_template"] = (
            f"templates/project_bootstrap/backend_service/{template_name}"
        )

        original_read_text = _read_text
        original_exists = Path.exists

        def fake_read_text(path, expected_name=template_name, supplied_text=template_text):
            if path.name == expected_name:
                return supplied_text
            return original_read_text(path)

        def fake_exists(self, expected_name=template_name):
            if self.name == expected_name:
                return True
            return original_exists(self)

        with patch("tools.atlas_governance_check._read_text", side_effect=fake_read_text):
            with patch.object(Path, "exists", new=fake_exists):
                findings = []
                _validate_bootstrap_templates(ROOT, contract, findings)

        assert any(
            finding
            == "skill_project-bootstrap:bootstrap_contract_invalid_template_placeholder:"
            "profile=backend_service:template=README:"
            f"file=templates/project_bootstrap/backend_service/{template_name}:"
            f"placeholder={expected_placeholder}:"
            "recommendation=replace_with_whitelisted_placeholder_or_static_text"
            for finding in findings
        )
        assert any(
            finding
            == "skill_project-bootstrap:bootstrap_contract_unresolved_template_placeholder:"
            "profile=backend_service:template=README:"
            f"file=templates/project_bootstrap/backend_service/{template_name}:"
            f"placeholder={expected_placeholder}:"
            "recommendation=ensure_the_placeholder_is_whitelisted_and_rendered_or_convert_it_to_static_text"
            for finding in findings
        )


def test_governance_detects_forbidden_canonical_root_artifacts():
    original_exists = Path.exists

    def fake_exists(path):
        if path in {ROOT / ".claude", ROOT / "CLAUDE.md"}:
            return True
        return original_exists(path)

    with patch("pathlib.Path.exists", new=fake_exists):
        findings = _find_forbidden_canonical_root_artifacts(ROOT)

    assert "forbidden_canonical_artifact:.claude" in findings
    assert "forbidden_canonical_artifact:CLAUDE.md" in findings


def test_governance_records_structured_event():
    captured = []

    def fake_append(path, record):
        captured.append((path, record))

    with patch("tools.atlas_governance_check._event_logging_enabled", return_value=True):
        with patch("tools.atlas_governance_check._append_jsonl_record", side_effect=fake_append):
            _record_governance_event(
                ROOT,
                None,
                {
                    "ok": True,
                    "findings": [],
                    "profile": "canonical",
                },
            )

    assert len(captured) == 1
    path, record = captured[0]
    assert path.name == "governance_events.jsonl"
    assert record["root"] == str(ROOT)
    assert record["project"] is None
    assert record["ok"] is True
    assert record["findings_count"] == 0


def test_mcp_profiles_reject_multiple_experimental_profiles():
    findings = []
    config_path = ROOT / "config" / "mcp_profiles.json"
    modified = json.loads(config_path.read_text(encoding="utf-8"))
    modified["profiles"]["docs_search"]["experimental_enabled"] = True
    modified["profiles"]["github"]["experimental_enabled"] = True
    modified["profiles"]["github"]["atlas_decision"] = "experimental_read_only"

    with patch("tools.atlas_governance_check._load_mcp_profiles", return_value=modified):
        _validate_mcp_profiles(ROOT, findings)

    assert any(finding.startswith("mcp_profiles_multiple_experimental:") for finding in findings)


def test_docs_search_catalog_rejects_duplicate_or_invalid_entries():
    findings = []
    invalid_catalog = {
        "schema_version": 1,
        "entries": [
            {
                "id": "docs_a",
                "title": "Docs A",
                "url": "https://example.com/docs",
                "source_type": "official_openai_docs",
                "topics": ["docs"],
                "description": "First entry.",
                "last_verified": "2026-04-24",
                "freshness_window_days": 120,
                "status": "active",
            },
            {
                "id": "docs_a",
                "title": "Docs B",
                "url": "https://example.com/docs",
                "source_type": "official_openai_docs",
                "topics": ["docs"],
                "description": "Second entry.",
                "last_verified": "invalid-date",
                "freshness_window_days": 0,
                "status": "unsupported",
            },
        ],
    }

    with patch("tools.atlas_governance_check._load_docs_search_catalog", return_value=invalid_catalog):
        _validate_docs_search_catalog(ROOT, findings)

    assert "docs_search_catalog_duplicate_id:docs_a" in findings
    assert "docs_search_catalog_duplicate_url:https://example.com/docs" in findings
    assert "docs_search_catalog_entry_2:invalid_last_verified:invalid-date" in findings
    assert "docs_search_catalog_entry_2:invalid_freshness_window_days:0" in findings
    assert "docs_search_catalog_entry_2:invalid_status:unsupported" in findings
