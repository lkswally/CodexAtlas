import os
import json
from pathlib import Path
from unittest.mock import patch

os.environ["ATLAS_DISABLE_EVENT_LOGS"] = "1"

from tests._support_paths import ATLAS_ROOT
from tools.atlas_governance_check import (
    _find_forbidden_canonical_root_artifacts,
    _record_governance_event,
    _read_text,
    _load_skill_lifecycle_rules,
    _load_skill_improvement_review_rules,
    _load_market_research_benchmark_rules,
    _load_intent_clarifier_contract_rules,
    _load_visual_intent_contract,
    _load_brand_json_v2_readiness_rules,
    _load_brand_profile_schema,
    _load_frontend_auto_audit_rules,
    _load_ui_pre_return_audit_rules,
    _load_creative_pipeline_profiles,
    _load_component_inspiration_profiles,
    _load_playwright_visual_qa_profiles,
    _load_design_quality_enforcement_rules,
    _load_atlas_error_learning_rules,
    _load_codex_runtime_compatibility_rules,
    _load_atlas_memory_readiness_profiles,
    _load_evidence_collector_readiness_rules,
    _load_change_proposal_rules,
    _load_skill_registry_index_first_rules,
    _load_ui_ux_design_system_rules,
    _load_business_idea_simulation_rules,
    _load_visual_fidelity_judge_rules,
    _load_chrome_devtools_mcp_rules,
    _load_copywriting_conversion_rules,
    _load_brand_strategy_rules,
    _load_mcp_permission_matrix_rules,
    _load_github_connector_rules,
    _load_department_registry,
    _load_n8n_automation_readiness_rules,
    _load_n8n_workflow_generation_rules,
    _validate_external_tool_policy,
    _validate_mcp_profiles,
    _validate_docs_search_catalog,
    _validate_skill_lifecycle_rules,
    _validate_skill_improvement_review_rules,
    _validate_market_research_benchmark_rules,
    _validate_intent_clarifier_contract_rules,
    _validate_visual_intent_contract,
    _validate_brand_json_v2_readiness_rules,
    _validate_brand_profile_schema,
    _validate_frontend_auto_audit_rules,
    _validate_ui_pre_return_audit_rules,
    _validate_creative_pipeline_profiles,
    _validate_component_inspiration_profiles,
    _validate_playwright_visual_qa_profiles,
    _validate_design_quality_enforcement_rules,
    _validate_atlas_error_learning_rules,
    _validate_codex_runtime_compatibility_rules,
    _validate_atlas_memory_readiness_profiles,
    _validate_evidence_collector_readiness_rules,
    _validate_change_proposal_rules,
    _validate_skill_registry_index_first_rules,
    _validate_ui_ux_design_system_rules,
    _validate_business_idea_simulation_rules,
    _validate_visual_fidelity_judge_rules,
    _validate_chrome_devtools_mcp_rules,
    _validate_copywriting_conversion_rules,
    _validate_brand_strategy_rules,
    _validate_mcp_permission_matrix_rules,
    _validate_github_connector_rules,
    _validate_department_registry,
    _validate_n8n_automation_readiness_rules,
    _validate_n8n_workflow_generation_rules,
    _validate_bootstrap_contract,
    _validate_bootstrap_contract_consistency,
    _validate_bootstrap_templates,
    _validate_global_project_templates,
    _validate_behavior_metadata,
    _validate_skill_behavior_consistency,
    _validate_skill_metadata,
    run_check,
)
from tools.atlas_orchestrator import get_project_bootstrap_contract, get_skill_execution_behavior_specs


ROOT = ATLAS_ROOT


def test_current_skill_catalog_passes_governance():
    result = run_check(root=ROOT)
    assert result["ok"] is True


def test_skill_lifecycle_rules_allow_expected_transitions():
    rules = _load_skill_lifecycle_rules(ROOT)
    assert "experimental" in rules["allowed_transitions"]["candidate"]
    assert "stable" in rules["allowed_transitions"]["experimental"]
    assert "deprecated" in rules["allowed_transitions"]["stable"]


def test_skill_lifecycle_rules_reject_missing_states():
    findings = []
    invalid_rules = _load_skill_lifecycle_rules(ROOT)
    invalid_rules["states"] = ["candidate", "experimental"]

    with patch("tools.atlas_governance_check._load_skill_lifecycle_rules", return_value=invalid_rules):
        _validate_skill_lifecycle_rules(ROOT, findings)

    assert any(finding.startswith("skill_lifecycle_rules_missing_states:") for finding in findings)


def test_skill_improvement_review_rules_require_expected_recommendations():
    findings = []
    invalid_rules = _load_skill_improvement_review_rules(ROOT)
    invalid_rules["recommendation_types"] = ["keep", "improve"]

    with patch(
        "tools.atlas_governance_check._load_skill_improvement_review_rules",
        return_value=invalid_rules,
    ):
        _validate_skill_improvement_review_rules(ROOT, findings)

    assert any(
        finding.startswith("skill_improvement_review_rules_missing_recommendation_types:")
        for finding in findings
    )


def test_skill_improvement_review_rules_require_scoring_fields():
    findings = []
    invalid_rules = _load_skill_improvement_review_rules(ROOT)
    invalid_rules["scoring_rules"] = {"base_score": 100}

    with patch(
        "tools.atlas_governance_check._load_skill_improvement_review_rules",
        return_value=invalid_rules,
    ):
        _validate_skill_improvement_review_rules(ROOT, findings)

    assert any(
        finding.startswith("skill_improvement_review_rules_missing_scoring_fields:")
        for finding in findings
    )


def test_market_research_benchmark_rules_require_recommendations_and_sources():
    findings = []
    invalid_rules = _load_market_research_benchmark_rules(ROOT)
    invalid_rules["recommendation_types"] = ["adapt_now"]
    invalid_rules["allowed_source_types"] = ["local_reference_clone"]

    with patch(
        "tools.atlas_governance_check._load_market_research_benchmark_rules",
        return_value=invalid_rules,
    ):
        _validate_market_research_benchmark_rules(ROOT, findings)

    assert any(
        finding.startswith("market_research_benchmark_rules_missing_recommendations:")
        for finding in findings
    )
    assert any(
        finding.startswith("market_research_benchmark_rules_missing_source_types:")
        for finding in findings
    )


def test_atlas_memory_readiness_profiles_require_expected_profiles():
    findings = []
    invalid_rules = _load_atlas_memory_readiness_profiles(ROOT)
    invalid_rules["profiles"] = {
        "local_session_summary": invalid_rules["profiles"]["local_session_summary"]
    }

    with patch(
        "tools.atlas_governance_check._load_atlas_memory_readiness_profiles",
        return_value=invalid_rules,
    ):
        _validate_atlas_memory_readiness_profiles(ROOT, findings)

    assert any(
        finding.startswith("atlas_memory_readiness_profiles_missing_profiles:")
        for finding in findings
    )


def test_evidence_collector_readiness_rules_require_expected_task_types():
    findings = []
    invalid_rules = _load_evidence_collector_readiness_rules(ROOT)
    invalid_rules["task_types"] = {
        "frontend_ui_landing": invalid_rules["task_types"]["frontend_ui_landing"]
    }

    with patch(
        "tools.atlas_governance_check._load_evidence_collector_readiness_rules",
        return_value=invalid_rules,
    ):
        _validate_evidence_collector_readiness_rules(ROOT, findings)

    assert any(
        finding.startswith("evidence_collector_readiness_rules_missing_task_types:")
        for finding in findings
    )


def test_change_proposal_rules_require_expected_artifacts():
    findings = []
    invalid_rules = _load_change_proposal_rules(ROOT)
    invalid_rules["required_artifacts"] = ["proposal", "specs"]

    with patch(
        "tools.atlas_governance_check._load_change_proposal_rules",
        return_value=invalid_rules,
    ):
        _validate_change_proposal_rules(ROOT, findings)

    assert any(
        finding.startswith("change_proposal_rules_missing_required_artifacts:")
        for finding in findings
    )


def test_skill_registry_index_first_rules_require_expected_registry_fields():
    findings = []
    invalid_rules = _load_skill_registry_index_first_rules(ROOT)
    invalid_rules["required_registry_fields"] = ["name", "description"]

    with patch(
        "tools.atlas_governance_check._load_skill_registry_index_first_rules",
        return_value=invalid_rules,
    ):
        _validate_skill_registry_index_first_rules(ROOT, findings)

    assert any(
        finding.startswith("skill_registry_index_first_rules_missing_required_registry_fields:")
        for finding in findings
    )


def test_ui_ux_design_system_rules_require_motion_library_fields():
    findings = []
    invalid_rules = _load_ui_ux_design_system_rules(ROOT)
    invalid_rules["motion_library_posture"] = {
        "react_eligible_stacks": ["react"]
    }

    with patch(
        "tools.atlas_governance_check._load_ui_ux_design_system_rules",
        return_value=invalid_rules,
    ):
        _validate_ui_ux_design_system_rules(ROOT, findings)

    assert any(
        finding.startswith("ui_ux_design_system_rules_missing_motion_library_fields:")
        for finding in findings
    )


def test_ui_ux_design_system_rules_require_component_library_fields():
    findings = []
    invalid_rules = _load_ui_ux_design_system_rules(ROOT)
    invalid_rules["component_library_posture"] = {
        "decision_types": ["manual_install_with_approval"]
    }

    with patch(
        "tools.atlas_governance_check._load_ui_ux_design_system_rules",
        return_value=invalid_rules,
    ):
        _validate_ui_ux_design_system_rules(ROOT, findings)

    assert any(
        finding.startswith("ui_ux_design_system_rules_missing_component_library_fields:")
        for finding in findings
    )


def test_business_idea_simulation_rules_require_core_inputs():
    findings = []
    invalid_rules = _load_business_idea_simulation_rules(ROOT)
    invalid_rules["required_inputs"] = ["problem", "customer"]

    with patch(
        "tools.atlas_governance_check._load_business_idea_simulation_rules",
        return_value=invalid_rules,
    ):
        _validate_business_idea_simulation_rules(ROOT, findings)

    assert any(
        finding.startswith("business_idea_simulation_rules_missing_required_inputs:")
        for finding in findings
    )


def test_visual_fidelity_judge_rules_require_core_layers_and_viewports():
    findings = []
    invalid_rules = _load_visual_fidelity_judge_rules(ROOT)
    invalid_rules["required_viewports"] = ["desktop"]
    invalid_rules["core_compared_layers"] = ["visual_intent_contract"]

    with patch(
        "tools.atlas_governance_check._load_visual_fidelity_judge_rules",
        return_value=invalid_rules,
    ):
        _validate_visual_fidelity_judge_rules(ROOT, findings)

    assert any(
        finding.startswith("visual_fidelity_judge_rules_missing_required_viewports:")
        for finding in findings
    )
    assert any(
        finding.startswith("visual_fidelity_judge_rules_missing_core_layers:")
        for finding in findings
    )


def test_chrome_devtools_mcp_rules_require_core_fields_and_flag():
    findings = []
    invalid_rules = _load_chrome_devtools_mcp_rules(ROOT)
    invalid_rules["best_for"] = ["layout_debugging"]
    invalid_rules["recommended_flags"] = []

    with patch(
        "tools.atlas_governance_check._load_chrome_devtools_mcp_rules",
        return_value=invalid_rules,
    ):
        _validate_chrome_devtools_mcp_rules(ROOT, findings)

    assert any(
        finding.startswith("chrome_devtools_mcp_rules_missing_best_for:")
        for finding in findings
    )
    assert "chrome_devtools_mcp_rules_missing_no_usage_statistics_flag" in findings


def test_copywriting_conversion_rules_require_core_fields_and_thresholds():
    findings = []
    invalid_rules = _load_copywriting_conversion_rules(ROOT)
    invalid_rules["blocked_claim_terms"] = []
    invalid_rules["ready_thresholds"] = {"clarity_score": 70}

    with patch(
        "tools.atlas_governance_check._load_copywriting_conversion_rules",
        return_value=invalid_rules,
    ):
        _validate_copywriting_conversion_rules(ROOT, findings)

    assert "copywriting_conversion_rules_invalid_blocked_claim_terms" in findings
    assert any(
        finding.startswith("copywriting_conversion_rules_missing_ready_thresholds:")
        for finding in findings
    )


def test_brand_strategy_rules_require_core_fields_and_thresholds():
    findings = []
    invalid_rules = _load_brand_strategy_rules(ROOT)
    invalid_rules["generic_palette_terms"] = []
    invalid_rules["ready_thresholds"] = {"positioning_score": 70}

    with patch(
        "tools.atlas_governance_check._load_brand_strategy_rules",
        return_value=invalid_rules,
    ):
        _validate_brand_strategy_rules(ROOT, findings)

    assert "brand_strategy_rules_invalid_generic_palette_terms" in findings
    assert any(
        finding.startswith("brand_strategy_rules_missing_ready_thresholds:")
        for finding in findings
    )


def test_department_registry_requires_expected_departments_and_watchlist_boundary():
    findings = []
    invalid_registry = _load_department_registry(ROOT)
    invalid_registry["department_activation_order"] = ["product", "qa_governance"]
    invalid_registry["departments"] = dict(invalid_registry["departments"])
    invalid_registry["departments"].pop("research", None)
    invalid_registry["departments"]["operations_finance"] = dict(
        invalid_registry["departments"]["operations_finance"]
    )
    invalid_registry["departments"]["operations_finance"]["status"] = "active"

    with patch(
        "tools.atlas_governance_check._load_department_registry",
        return_value=invalid_registry,
    ):
        _validate_department_registry(ROOT, findings)

    assert any(
        finding.startswith("department_registry_missing_departments:")
        for finding in findings
    )
    assert "department_registry_activation_order_incomplete" in findings
    assert "department_registry_operations_finance_must_be_watchlist" in findings


def test_mcp_permission_matrix_rules_require_platforms_capabilities_and_defaults():
    findings = []
    invalid_rules = _load_mcp_permission_matrix_rules(ROOT)
    invalid_rules["supported_platforms"] = ["github", "gmail"]
    invalid_rules["platform_defaults"] = {
        "github": invalid_rules["platform_defaults"]["github"]
    }

    with patch(
        "tools.atlas_governance_check._load_mcp_permission_matrix_rules",
        return_value=invalid_rules,
    ):
        _validate_mcp_permission_matrix_rules(ROOT, findings)

    assert any(
        finding.startswith("mcp_permission_matrix_rules_missing_supported_platforms:")
        for finding in findings
    )
    assert any(
        finding.startswith("mcp_permission_matrix_rules_missing_platform_defaults:")
        for finding in findings
    )


def test_github_connector_rules_require_capabilities_and_blocked_actions():
    findings = []
    invalid_rules = _load_github_connector_rules(ROOT)
    invalid_rules["blocked_capabilities"] = ["merge"]
    invalid_rules["capability_levels"] = {
        "repo_status": "read_only",
        "pr_draft": "draft_only",
    }
    invalid_rules["runtime_read_checks"] = ["repo_accessible"]
    invalid_rules["pr_draft_plan_defaults"] = {"base_branch": "main"}
    invalid_rules["pr_draft_create_guard_defaults"] = {"requested_action": "create_draft_pr"}

    with patch(
        "tools.atlas_governance_check._load_github_connector_rules",
        return_value=invalid_rules,
    ):
        _validate_github_connector_rules(ROOT, findings)

    assert any(
        finding.startswith("github_connector_rules_missing_capabilities:")
        for finding in findings
    )
    assert any(
        finding.startswith("github_connector_rules_missing_runtime_read_checks:")
        for finding in findings
    )
    assert any(
        finding.startswith("github_connector_rules_missing_pr_draft_plan_field:")
        for finding in findings
    )
    assert any(
        finding.startswith("github_connector_rules_missing_pr_draft_create_guard_field:")
        for finding in findings
    )
    assert "github_connector_rules_workflow_dispatch_must_be_blocked" in findings
    assert "github_connector_rules_secrets_access_must_be_blocked" in findings


def test_n8n_automation_readiness_rules_require_core_fields_and_node_signals():
    findings = []
    invalid_rules = _load_n8n_automation_readiness_rules(ROOT)
    invalid_rules["node_type_signals"] = {
        "send_email": ["send email"]
    }
    invalid_rules["risk_triggers"] = {"high": ["send_email_real"]}

    with patch(
        "tools.atlas_governance_check._load_n8n_automation_readiness_rules",
        return_value=invalid_rules,
    ):
        _validate_n8n_automation_readiness_rules(ROOT, findings)

    assert any(
        finding.startswith("n8n_automation_readiness_rules_missing_node_type_signals:")
        for finding in findings
    )
    assert "n8n_automation_readiness_rules_invalid_risk_triggers_medium" in findings


def test_n8n_workflow_generation_rules_require_core_templates_and_placeholders():
    findings = []
    invalid_rules = _load_n8n_workflow_generation_rules(ROOT)
    invalid_rules["trigger_templates"] = {
        "manual": invalid_rules["trigger_templates"]["manual"]
    }
    invalid_rules["safe_placeholder_values"] = {
        "credential_binding": "MANUAL_BIND_REQUIRED"
    }

    with patch(
        "tools.atlas_governance_check._load_n8n_workflow_generation_rules",
        return_value=invalid_rules,
    ):
        _validate_n8n_workflow_generation_rules(ROOT, findings)

    assert any(
        finding.startswith("n8n_workflow_generation_rules_missing_trigger_templates:")
        for finding in findings
    )
    assert any(
        finding.startswith("n8n_workflow_generation_rules_missing_safe_placeholder_values:")
        for finding in findings
    )


def test_intent_clarifier_contract_rules_require_core_fields():
    findings = []
    invalid_rules = _load_intent_clarifier_contract_rules(ROOT)
    invalid_rules["required_fields"] = ["project_type", "primary_goal"]

    with patch(
        "tools.atlas_governance_check._load_intent_clarifier_contract_rules",
        return_value=invalid_rules,
    ):
        _validate_intent_clarifier_contract_rules(ROOT, findings)

    assert any(
        finding.startswith("intent_clarifier_contract_rules_missing_required_fields:")
        for finding in findings
    )


def test_visual_intent_contract_rejects_missing_required_fields():
    findings = []
    invalid_contract = _load_visual_intent_contract(ROOT)
    invalid_contract["required_fields"] = ["audience", "mood_vibe"]

    with patch("tools.atlas_governance_check._load_visual_intent_contract", return_value=invalid_contract):
        _validate_visual_intent_contract(ROOT, findings)

    assert any(finding.startswith("visual_intent_contract_missing_required_fields:") for finding in findings)


def test_brand_profile_schema_rejects_missing_required_fields():
    findings = []
    invalid_schema = _load_brand_profile_schema(ROOT)
    invalid_schema["required_fields"] = ["brand_name", "audience"]

    with patch("tools.atlas_governance_check._load_brand_profile_schema", return_value=invalid_schema):
        _validate_brand_profile_schema(ROOT, findings)

    assert any(finding.startswith("brand_profile_schema_missing_required_fields:") for finding in findings)


def test_brand_json_v2_rules_require_core_sections():
    findings = []
    invalid_rules = _load_brand_json_v2_readiness_rules(ROOT)
    invalid_rules["required_sections"] = ["brand_name", "audience"]

    with patch(
        "tools.atlas_governance_check._load_brand_json_v2_readiness_rules",
        return_value=invalid_rules,
    ):
        _validate_brand_json_v2_readiness_rules(ROOT, findings)

    assert any(
        finding.startswith("brand_json_v2_readiness_rules_missing_required_sections:")
        for finding in findings
    )


def test_ui_pre_return_rules_reject_missing_checks():
    findings = []
    invalid_rules = _load_ui_pre_return_audit_rules(ROOT)
    invalid_rules["checks"] = ["cta_clarity", "above_the_fold_clarity"]

    with patch("tools.atlas_governance_check._load_ui_pre_return_audit_rules", return_value=invalid_rules):
        _validate_ui_pre_return_audit_rules(ROOT, findings)

    assert any(finding.startswith("ui_pre_return_audit_rules_missing_checks:") for finding in findings)


def test_ui_pre_return_rules_reject_missing_warning_codes():
    findings = []
    invalid_rules = _load_ui_pre_return_audit_rules(ROOT)
    invalid_rules["warning_codes"] = ["ui_pre_return_cta_weak"]

    with patch("tools.atlas_governance_check._load_ui_pre_return_audit_rules", return_value=invalid_rules):
        _validate_ui_pre_return_audit_rules(ROOT, findings)

    assert any(finding.startswith("ui_pre_return_audit_rules_missing_warning_codes:") for finding in findings)


def test_frontend_auto_audit_rules_require_expected_checks():
    findings = []
    invalid_rules = _load_frontend_auto_audit_rules(ROOT)
    invalid_rules["checks"] = {
        "intent_clarifier_ready": invalid_rules["checks"]["intent_clarifier_ready"]
    }
    invalid_rules["warning_codes"] = ["frontend_auto_audit_not_ready"]

    with patch(
        "tools.atlas_governance_check._load_frontend_auto_audit_rules",
        return_value=invalid_rules,
    ):
        _validate_frontend_auto_audit_rules(ROOT, findings)

    assert any(
        finding.startswith("frontend_auto_audit_rules_missing_checks:")
        for finding in findings
    )
    assert any(
        finding.startswith("frontend_auto_audit_rules_missing_warning_codes:")
        for finding in findings
    )


def test_creative_pipeline_profiles_require_expected_profiles_and_services():
    findings = []
    invalid_rules = _load_creative_pipeline_profiles(ROOT)
    invalid_rules["profiles"] = {"brand_visual_review": invalid_rules["profiles"]["brand_visual_review"]}
    invalid_rules["services"] = {"gemini": invalid_rules["services"]["gemini"]}

    with patch("tools.atlas_governance_check._load_creative_pipeline_profiles", return_value=invalid_rules):
        _validate_creative_pipeline_profiles(ROOT, findings)

    assert any(finding.startswith("creative_pipeline_profiles_missing_profiles:") for finding in findings)
    assert any(finding.startswith("creative_pipeline_profiles_missing_services:") for finding in findings)


def test_component_inspiration_profiles_require_expected_profiles_and_services():
    findings = []
    invalid_rules = _load_component_inspiration_profiles(ROOT)
    invalid_rules["profiles"] = {
        "ui_component_inspiration": invalid_rules["profiles"]["ui_component_inspiration"]
    }
    invalid_rules["services"] = {"twentyfirst_magic": invalid_rules["services"]["twentyfirst_magic"]}

    with patch(
        "tools.atlas_governance_check._load_component_inspiration_profiles",
        return_value=invalid_rules,
    ):
        _validate_component_inspiration_profiles(ROOT, findings)

    assert any(
        finding.startswith("component_inspiration_profiles_missing_profiles:")
        for finding in findings
    )
    assert any(
        finding.startswith("component_inspiration_profiles_missing_services:")
        for finding in findings
    )


def test_playwright_visual_qa_profiles_require_expected_profiles():
    findings = []
    invalid_rules = _load_playwright_visual_qa_profiles(ROOT)
    invalid_rules["profiles"] = {
        "landing_visual_qa": invalid_rules["profiles"]["landing_visual_qa"]
    }

    with patch(
        "tools.atlas_governance_check._load_playwright_visual_qa_profiles",
        return_value=invalid_rules,
    ):
        _validate_playwright_visual_qa_profiles(ROOT, findings)

    assert any(
        finding.startswith("playwright_visual_qa_profiles_missing_profiles:")
        for finding in findings
    )


def test_design_quality_enforcement_rules_require_expected_checks():
    findings = []
    invalid_rules = _load_design_quality_enforcement_rules(ROOT)
    invalid_rules["checks"] = {
        "border_weight_excessive": invalid_rules["checks"]["border_weight_excessive"]
    }
    invalid_rules["warning_codes"] = ["design_quality_not_ready"]

    with patch(
        "tools.atlas_governance_check._load_design_quality_enforcement_rules",
        return_value=invalid_rules,
    ):
        _validate_design_quality_enforcement_rules(ROOT, findings)

    assert any(
        finding.startswith("design_quality_enforcement_rules_missing_checks:")
        for finding in findings
    )
    assert any(
        finding.startswith("design_quality_enforcement_rules_missing_warning_codes:")
        for finding in findings
    )


def test_atlas_error_learning_rules_require_expected_checks_and_warning_codes():
    findings = []
    invalid_rules = _load_atlas_error_learning_rules(ROOT)
    invalid_rules["checks"] = {
        "hero_overflow_or_mobile_header_failure": invalid_rules["checks"]["hero_overflow_or_mobile_header_failure"]
    }
    invalid_rules["warning_codes"] = ["error_learning_ui_not_ready"]

    with patch(
        "tools.atlas_governance_check._load_atlas_error_learning_rules",
        return_value=invalid_rules,
    ):
        _validate_atlas_error_learning_rules(ROOT, findings)

    assert any(
        finding.startswith("atlas_error_learning_rules_missing_checks:")
        for finding in findings
    )
    assert any(
        finding.startswith("atlas_error_learning_rules_missing_warning_codes:")
        for finding in findings
    )


def test_codex_runtime_compatibility_rules_require_expected_checks_and_limitations():
    findings = []
    invalid_rules = _load_codex_runtime_compatibility_rules(ROOT)
    invalid_rules["required_checks"] = ["codex_cli_available"]
    invalid_rules["known_limitations"] = ["manual_model_switch_only"]

    with patch(
        "tools.atlas_governance_check._load_codex_runtime_compatibility_rules",
        return_value=invalid_rules,
    ):
        _validate_codex_runtime_compatibility_rules(ROOT, findings)

    assert any(
        finding.startswith("codex_runtime_compatibility_rules_missing_required_checks:")
        for finding in findings
    )
    assert any(
        finding.startswith("codex_runtime_compatibility_rules_missing_known_limitations:")
        for finding in findings
    )


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


def test_global_project_templates_render_cleanly():
    findings = []
    _validate_global_project_templates(ROOT, findings)
    assert findings == []


def test_global_project_templates_reject_invalid_placeholders():
    template_name = "AGENTS.md.template"
    relative_path = "templates/project/AGENTS.md.template"
    template_text = "# {project_name}\n\nUnsupported {project_profile}\n"

    original_read_text = _read_text
    original_exists = Path.exists

    def fake_read_text(path, supplied_text=template_text):
        if str(path).endswith(relative_path.replace("/", "\\")):
            return supplied_text
        return original_read_text(path)

    def fake_exists(self):
        if str(self).endswith(relative_path.replace("/", "\\")):
            return True
        return original_exists(self)

    with patch("tools.atlas_governance_check._read_text", side_effect=fake_read_text):
        with patch.object(Path, "exists", new=fake_exists):
            findings = []
            _validate_global_project_templates(ROOT, findings)

    assert any(
        finding
        == "atlas_project_bootstrap:invalid_template_placeholder:"
        "profile=global_project_governance:template=AGENTS:"
        "file=templates/project/AGENTS.md.template:"
        "placeholder={project_profile}:"
        "recommendation=replace_with_whitelisted_placeholder_or_static_text"
        for finding in findings
    )
    assert any(
        finding
        == "atlas_project_bootstrap:unresolved_template_placeholder:"
        "profile=global_project_governance:template=AGENTS:"
        "file=templates/project/AGENTS.md.template:"
        "placeholder={project_profile}:"
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


def test_external_tool_policy_rejects_invalid_structure():
    findings = []
    invalid_policy = {
        "version": "1.0",
        "mode": "automatic",
        "layers": ["knowledge"],
        "source_priority": ["local_repo"],
        "default_stance": {"mcp": "enabled", "preferred_mode": "write"},
        "prefer_cli_over_mcp_when": [],
        "do_not_use_external_tools_when": [],
        "risk_axes": [],
        "integration_hints": {},
    }

    with patch("tools.atlas_governance_check._load_external_tool_policy", return_value=invalid_policy):
        _validate_external_tool_policy(ROOT, findings)

    assert "external_tool_policy_invalid_mode" in findings
    assert "external_tool_policy_invalid_layers" in findings
    assert "external_tool_policy_invalid_source_priority" in findings
    assert "external_tool_policy_invalid_mcp_stance" in findings
    assert "external_tool_policy_invalid_preferred_mode" in findings
    assert "external_tool_policy_invalid_list:prefer_cli_over_mcp_when" in findings
    assert "external_tool_policy_invalid_list:do_not_use_external_tools_when" in findings
    assert "external_tool_policy_invalid_list:risk_axes" in findings
    assert "external_tool_policy_invalid_integration_hints" in findings
