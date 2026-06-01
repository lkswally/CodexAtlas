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
    "config/model_cost_control_profiles.json",
    "config/mcp_profiles.json",
    "config/docs_search_catalog.json",
    "config/phase_playbook.json",
    "config/external_tool_policy.json",
    "config/skill_lifecycle_rules.json",
    "config/skill_improvement_review_rules.json",
    "config/market_research_benchmark_rules.json",
    "config/intent_clarifier_contract_rules.json",
    "config/visual_intent_contract_rules.json",
    "config/brand_json_v2_readiness_rules.json",
    "config/brand_profile_schema_rules.json",
    "config/frontend_auto_audit_rules.json",
    "config/ui_pre_return_audit_rules.json",
    "config/creative_pipeline_profiles.json",
    "config/component_inspiration_profiles.json",
    "config/playwright_visual_qa_profiles.json",
    "config/visual_fidelity_judge_rules.json",
    "config/chrome_devtools_mcp_rules.json",
    "config/design_quality_enforcement_rules.json",
    "config/atlas_error_learning_rules.json",
    "config/codex_runtime_compatibility_rules.json",
    "config/atlas_memory_readiness_profiles.json",
    "config/evidence_collector_readiness_rules.json",
    "config/change_proposal_rules.json",
    "config/skill_registry_index_first_rules.json",
    "config/ui_ux_design_system_rules.json",
    "config/repo_graph_readiness_rules.json",
    "config/business_idea_simulation_rules.json",
    "config/copywriting_conversion_rules.json",
    "config/brand_strategy_rules.json",
    "config/n8n_automation_readiness_rules.json",
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
    "workflows/change_proposal_workflow.md",
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
    "policies/model_cost_control_policy.md",
    "policies/mcp_routing_policy.md",
    "policies/cost_control_policy.md",
    "policies/external_tool_policy.md",
    "policies/skill_lifecycle_policy.md",
    "policies/skill_improvement_review_policy.md",
    "policies/market_research_benchmark_policy.md",
    "policies/intent_clarifier_contract_policy.md",
    "policies/visual_intent_contract_policy.md",
    "policies/brand_json_v2_readiness_policy.md",
    "policies/brand_profile_schema_policy.md",
    "policies/frontend_auto_audit_rules_policy.md",
    "policies/ui_pre_return_audit_policy.md",
    "policies/creative_pipeline_readiness_policy.md",
    "policies/component_inspiration_readiness_policy.md",
    "policies/playwright_visual_qa_readiness_policy.md",
    "policies/visual_fidelity_judge_policy.md",
    "policies/chrome_devtools_mcp_policy.md",
    "policies/design_quality_enforcement_policy.md",
    "policies/atlas_error_learning_policy.md",
    "policies/codex_runtime_compatibility_policy.md",
    "policies/atlas_memory_readiness_policy.md",
    "policies/evidence_collector_readiness_policy.md",
    "policies/change_proposal_policy.md",
    "policies/skill_registry_index_first_policy.md",
    "policies/ui_ux_design_system_policy.md",
    "policies/repo_graph_readiness_policy.md",
    "policies/business_idea_simulation_policy.md",
    "policies/copywriting_conversion_policy.md",
    "policies/brand_strategy_policy.md",
    "policies/n8n_automation_readiness_policy.md",
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
    "skills/market-research-benchmark/skill.md",
    "skills/market-research-benchmark/skill.json",
    "skills/market-research-benchmark/behavior.json",
    "skills/design-system-review/skill.md",
    "skills/design-system-review/skill.json",
    "skills/design-system-review/behavior.json",
    "skills/business-idea-evaluator/skill.md",
    "skills/business-idea-evaluator/skill.json",
    "skills/business-idea-evaluator/behavior.json",
    "skills/conversion-copywriter/skill.md",
    "skills/conversion-copywriter/skill.json",
    "skills/conversion-copywriter/behavior.json",
    "workflows/orchestrator_routing.md",
    "tools/atlas_orchestrator.py",
    "tools/design_intelligence_audit.py",
    "tools/atlas_mcp_manager.py",
    "tools/atlas_surface_audit.py",
    "tools/docs_search_adapter.py",
    "tools/docs_catalog_report.py",
    "tools/project_phase_resolver.py",
    "tools/project_intent_analyzer.py",
    "tools/intent_clarifier_contract.py",
    "tools/priority_engine.py",
    "tools/decision_feedback.py",
    "tools/feedback_analyzer.py",
    "tools/model_router.py",
    "tools/model_router_core.py",
    "tools/model_cost_control_readiness.py",
    "tools/error_pattern_analyzer.py",
    "tools/repo_improvement_scout.py",
    "tools/mcp_readiness_check.py",
    "tools/prompt_builder.py",
    "tools/quality_gate_report.py",
    "tools/skill_evaluator.py",
    "tools/skill_improvement_review.py",
    "tools/market_research_benchmark.py",
    "tools/brand_profile_schema.py",
    "tools/brand_json_v2_readiness.py",
    "tools/frontend_auto_audit_rules.py",
    "tools/ui_pre_return_audit.py",
    "tools/creative_pipeline_readiness.py",
    "tools/component_inspiration_readiness.py",
    "tools/playwright_visual_qa_readiness.py",
    "tools/visual_fidelity_judge.py",
    "tools/chrome_devtools_mcp_readiness.py",
    "tools/design_quality_enforcement.py",
    "tools/atlas_error_learning_review.py",
    "tools/codex_runtime_compatibility_check.py",
    "tools/atlas_memory_readiness.py",
    "tools/evidence_collector_readiness.py",
    "tools/change_proposal_readiness.py",
    "tools/skill_registry_index_first_readiness.py",
    "tools/ui_ux_design_system_readiness.py",
    "tools/repo_graph_readiness.py",
    "tools/business_idea_simulation_readiness.py",
    "tools/copywriting_conversion_readiness.py",
    "tools/brand_strategy_readiness.py",
    "tools/n8n_automation_readiness.py",
    "tests/test_atlas_orchestrator.py",
    "tests/test_certify_project.py",
    "tests/test_docs_catalog_report.py",
    "tests/test_design_intelligence_audit.py",
    "tests/test_mcp_manager.py",
    "tests/test_project_intent.py",
    "tests/test_intent_clarifier_contract.py",
    "tests/test_project_phase.py",
    "tests/test_priority_engine.py",
    "tests/test_decision_feedback.py",
    "tests/test_feedback_analyzer.py",
    "tests/test_model_router.py",
    "tests/test_model_cost_control_readiness.py",
    "tests/test_error_pattern_analyzer.py",
    "tests/test_repo_improvement_scout.py",
    "tests/test_mcp_readiness_check.py",
    "tests/test_prompt_builder.py",
    "tests/test_quality_gate_report.py",
    "tests/test_skill_evaluator.py",
    "tests/test_skill_improvement_review.py",
    "tests/test_market_research_benchmark.py",
    "tests/test_skill_execution.py",
    "tests/test_skill_governance.py",
    "tests/test_brand_profile_schema.py",
    "tests/test_brand_json_v2_readiness.py",
    "tests/test_frontend_auto_audit_rules.py",
    "tests/test_ui_pre_return_audit.py",
    "tests/test_creative_pipeline_readiness.py",
    "tests/test_component_inspiration_readiness.py",
    "tests/test_playwright_visual_qa_readiness.py",
    "tests/test_visual_fidelity_judge.py",
    "tests/test_chrome_devtools_mcp_readiness.py",
    "tests/test_design_quality_enforcement.py",
    "tests/test_atlas_error_learning_review.py",
    "tests/test_codex_runtime_compatibility_check.py",
    "tests/test_atlas_memory_readiness.py",
    "tests/test_evidence_collector_readiness.py",
    "tests/test_change_proposal_readiness.py",
    "tests/test_skill_registry_index_first_readiness.py",
    "tests/test_ui_ux_design_system_readiness.py",
    "tests/test_repo_graph_readiness.py",
    "tests/test_business_idea_simulation_readiness.py",
    "tests/test_copywriting_conversion_readiness.py",
    "tests/test_brand_strategy_readiness.py",
    "tests/test_n8n_automation_readiness.py",
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
EXPECTED_CODEX_ROUTING_MODELS = {
    "GPT-5.4",
    "GPT-5.2-Codex",
    "GPT-5.1-Codex-Max",
    "GPT-5.4-Mini",
    "GPT-5.3-Codex",
    "GPT-5.2",
    "GPT-5.1-Codex-Mini",
}
MODEL_ROUTING_RULE_REQUIRED_FIELDS = {
    "id",
    "task_type",
    "phase",
    "complexity",
    "risk_level",
    "cost_sensitivity",
    "recommended_model",
    "fallback_model",
    "avoid_models",
    "reason",
    "requires_confirmation_when_ambiguous",
}
EXTERNAL_TOOL_POLICY_REQUIRED_FIELDS = {
    "version",
    "mode",
    "layers",
    "source_priority",
    "default_stance",
    "prefer_cli_over_mcp_when",
    "do_not_use_external_tools_when",
    "risk_axes",
    "integration_hints",
}
EXTERNAL_TOOL_POLICY_REQUIRED_LAYERS = {"knowledge", "control", "execution", "context"}
REQUIRED_SKILL_LIFECYCLE_STATES = {
    "candidate",
    "experimental",
    "stable",
    "deprecated",
    "archived",
    "rejected",
}
SKILL_LIFECYCLE_RULES_REQUIRED_FIELDS = {
    "version",
    "states",
    "allowed_transitions",
    "required_fields_by_state",
    "test_requirements_by_state",
    "documentation_requirements_by_state",
    "human_approval_required_by_state",
    "allowed_risk_by_state",
}
SKILL_IMPROVEMENT_REVIEW_REQUIRED_FIELDS = {
    "version",
    "advisory_only",
    "scoring_rules",
    "maturity_signals",
    "duplication_signals",
    "stale_skill_signals",
    "missing_test_signals",
    "missing_docs_signals",
    "external_dependency_signals",
    "risk_scoring",
    "recommendation_types",
}
REQUIRED_SKILL_IMPROVEMENT_RECOMMENDATIONS = {
    "keep",
    "improve",
    "merge",
    "split",
    "deprecate",
    "archive",
    "reject",
    "candidate_review",
    "decision_council_required",
}
MARKET_RESEARCH_BENCHMARK_REQUIRED_FIELDS = {
    "version",
    "advisory_only",
    "primary_reference_repo",
    "allowed_source_types",
    "benchmark_axes",
    "recommendation_types",
    "required_output_sections",
    "high_risk_signals",
    "requires_decision_council_signals",
    "reference_catalog",
}
REQUIRED_MARKET_RESEARCH_RECOMMENDATIONS = {
    "adapt_now",
    "design_later",
    "watchlist",
    "discard",
}
REQUIRED_MARKET_RESEARCH_SOURCE_TYPES = {
    "local_reference_clone",
    "documented_repo",
    "explicit_payload",
}
INTENT_CLARIFIER_REQUIRED_FIELDS = {
    "version",
    "advisory_only",
    "required_fields",
    "ui_required_fields",
    "recommended_fields",
    "required_for_project_types",
    "backend_exempt_project_types",
    "minimum_ready_fields",
    "weak_answer_patterns",
    "approval_triggers",
    "domain_signals",
}
REQUIRED_INTENT_CLARIFIER_FIELDS = {
    "project_type",
    "domain_context",
    "target_audience",
    "primary_goal",
}
REQUIRED_INTENT_CLARIFIER_UI_FIELDS = {
    "style_direction",
    "originality_level",
}
VISUAL_INTENT_CONTRACT_REQUIRED_FIELDS = {
    "version",
    "advisory_only",
    "required_fields",
    "required_for_project_types",
    "ui_surface_signals",
    "backend_exempt_project_types",
    "allowed_originality_levels",
    "allowed_motion_intensity",
    "allowed_visual_density",
    "minimum_evidence_expectations",
    "weak_field_rules",
}
REQUIRED_VISUAL_INTENT_FIELDS = {
    "audience",
    "project_type",
    "problem_or_promise",
    "mood_or_vibe",
    "originality_level",
    "hero_direction",
    "primary_cta_intent",
    "visual_density",
    "motion_intensity",
    "typography_intent",
    "color_strategy",
    "anti_patterns_to_avoid",
    "evidence_expectations",
}
BRAND_PROFILE_SCHEMA_REQUIRED_FIELDS = {
    "version",
    "advisory_only",
    "required_fields",
    "recommended_fields",
    "required_for_project_types",
    "ui_surface_signals",
    "backend_exempt_project_types",
    "allowed_originality_levels",
    "allowed_visual_density",
    "mood_vector_dimensions",
    "mood_vector_range",
    "required_color_strategy_fields",
    "required_typography_strategy_fields",
    "minimum_quality_rules",
    "anti_generic_criteria",
    "forbidden_font_patterns",
    "derivative_reference_signals",
    "minimum_evidence_expectations",
}
REQUIRED_BRAND_PROFILE_FIELDS = {
    "brand_name",
    "audience",
    "project_type",
    "personality_traits",
    "mood_vector",
    "color_strategy",
    "typography_strategy",
    "layout_principles",
    "motion_principles",
    "visual_density",
    "originality_level",
    "anti_patterns_to_avoid",
    "inspiration_references",
    "differentiation_notes",
    "accessibility_notes",
    "evidence_expectations",
}
REQUIRED_BRAND_MOOD_VECTOR_DIMENSIONS = {
    "premium",
    "playful",
    "technical",
    "editorial",
    "minimalist",
    "bold",
    "warm",
    "futuristic",
}
REQUIRED_BRAND_COLOR_STRATEGY_FIELDS = {
    "primary",
    "secondary",
    "accent",
    "background",
    "contrast_notes",
    "forbidden_color_patterns",
}
REQUIRED_BRAND_TYPOGRAPHY_FIELDS = {
    "heading_style",
    "body_style",
    "contrast_rationale",
    "forbidden_font_patterns",
}
BRAND_JSON_V2_REQUIRED_FIELDS = {
    "version",
    "advisory_only",
    "required_sections",
    "recommended_sections",
    "required_for_project_types",
    "backend_exempt_project_types",
    "mood_vector_dimensions",
    "explicit_profile_required_for_ready",
    "minimum_evidence_expectations",
}
CHROME_DEVTOOLS_MCP_RULES_REQUIRED_FIELDS = {
    "version",
    "advisory_only",
    "frontend_project_types",
    "layout_debug_signals",
    "console_debug_signals",
    "network_debug_signals",
    "performance_debug_signals",
    "drift_trigger_states",
    "screenshot_gap_signals",
    "configured_server_aliases",
    "best_for",
    "recommended_flags",
    "manual_setup_steps",
    "risks",
    "recommendation_thresholds",
}
REQUIRED_CHROME_DEVTOOLS_MCP_BEST_FOR = {
    "layout_debugging",
    "css_inspection",
    "console_errors",
    "network",
    "performance",
}
COPYWRITING_CONVERSION_REQUIRED_FIELDS = {
    "version",
    "advisory_only",
    "applicable_project_types",
    "input_aliases",
    "project_scan_files",
    "blocked_claim_terms",
    "instant_diagnosis_terms",
    "generic_ai_phrases",
    "aggressive_sales_phrases",
    "strong_cta_terms",
    "weak_cta_terms",
    "audience_keywords",
    "problem_keywords",
    "value_keywords",
    "form_follow_up_terms",
    "consent_terms",
    "trust_terms",
    "ready_thresholds",
}
COPYWRITING_CONVERSION_REQUIRED_THRESHOLDS = {
    "clarity_score",
    "conversion_score",
    "trust_score",
    "tone_consistency_score",
}
BRAND_STRATEGY_REQUIRED_FIELDS = {
    "version",
    "advisory_only",
    "applicable_project_types",
    "input_aliases",
    "generic_category_terms",
    "generic_palette_terms",
    "generic_brand_phrases",
    "template_risk_signals",
    "inconsistent_tone_signals",
    "claims_without_evidence_terms",
    "audience_mismatch_signals",
    "required_color_roles",
    "required_typography_fields",
    "ready_thresholds",
}
BRAND_STRATEGY_REQUIRED_THRESHOLDS = {
    "positioning_score",
    "differentiation_score",
    "trust_score",
    "visual_consistency_score",
    "tone_consistency_score",
    "audience_fit_score",
}
REQUIRED_BRAND_JSON_V2_SECTIONS = {
    "brand_name",
    "audience",
    "project_type",
    "mood_vector",
    "color_strategy",
    "typography_strategy",
    "layout_principles",
    "motion_principles",
    "visual_density",
    "originality_level",
    "anti_patterns_to_avoid",
    "differentiation_notes",
    "accessibility_notes",
    "evidence_expectations",
}
UI_PRE_RETURN_AUDIT_REQUIRED_FIELDS = {
    "version",
    "advisory_only",
    "required_inputs",
    "required_for_project_types",
    "backend_exempt_project_types",
    "checks",
    "severity",
    "evidence_required",
    "warning_codes",
    "pass_conditions",
    "anti_generic_patterns",
    "brand_alignment_checks",
    "accessibility_basics",
    "responsive_expectations",
}
REQUIRED_UI_PRE_RETURN_CHECKS = {
    "visual_intent_contract_present",
    "visual_intent_contract_sufficient",
    "brand_profile_present",
    "brand_profile_sufficient",
    "cta_clarity",
    "above_the_fold_clarity",
    "typography_coherence",
    "color_strategy_coherence",
    "layout_hierarchy",
    "visual_density_alignment",
    "motion_alignment",
    "anti_generic_patterns",
    "responsive_expectations",
    "accessibility_basics",
    "evidence_expectations",
    "final_claim_supported_by_evidence",
}
REQUIRED_UI_PRE_RETURN_WARNING_CODES = {
    "ui_pre_return_audit_missing",
    "ui_pre_return_missing_visual_intent",
    "ui_pre_return_missing_brand_profile",
    "ui_pre_return_missing_evidence",
    "ui_pre_return_generic_risk",
    "ui_pre_return_brand_mismatch",
    "ui_pre_return_cta_weak",
    "ui_pre_return_hierarchy_weak",
    "ui_pre_return_accessibility_weak",
    "ui_pre_return_responsive_unknown",
    "ui_pre_return_not_ready",
}
FRONTEND_AUTO_AUDIT_REQUIRED_FIELDS = {
    "version",
    "advisory_only",
    "required_for_project_types",
    "backend_exempt_project_types",
    "required_inputs",
    "checks",
    "warning_codes",
    "watchlist_dependencies",
}
REQUIRED_FRONTEND_AUTO_AUDIT_INPUTS = {
    "intent_clarifier_contract",
    "visual_intent_contract_review",
    "brand_json_v2_readiness",
    "brand_profile_review",
    "ui_pre_return_review",
    "design_quality_review",
    "design_checks",
}
REQUIRED_FRONTEND_AUTO_AUDIT_CHECKS = {
    "intent_clarifier_ready",
    "visual_intent_contract_ready",
    "brand_json_v2_ready",
    "ui_pre_return_ready",
    "design_quality_ready",
    "responsive_baseline_present",
    "evidence_expectations_defined",
}
REQUIRED_FRONTEND_AUTO_AUDIT_WARNING_CODES = {
    "frontend_auto_audit_missing",
    "frontend_auto_audit_missing_intent_clarifier",
    "frontend_auto_audit_missing_brand_json_v2",
    "frontend_auto_audit_missing_evidence",
    "frontend_auto_audit_not_ready",
    "frontend_auto_audit_watchlist_screenshots",
    "frontend_auto_audit_watchlist_visual_fidelity",
    "frontend_auto_audit_watchlist_reality_check",
}
CREATIVE_PIPELINE_REQUIRED_PROFILES = {
    "logo_generation",
    "image_generation",
    "video_generation",
    "brand_visual_review",
    "component_inspiration",
    "visual_qa_watchlist",
}
CREATIVE_PIPELINE_REQUIRED_SERVICES = {
    "gemini",
    "huggingface",
    "replicate",
    "twentyfirst_magic",
    "context7",
    "playwright_visual_qa",
}
CREATIVE_PIPELINE_PROFILE_REQUIRED_FIELDS = {
    "suggested_services",
    "requirements",
    "expected_env_vars",
    "risk_level",
    "initial_state",
    "requires_human_approval",
}
CREATIVE_PIPELINE_SERVICE_REQUIRED_FIELDS = {
    "display_name",
    "expected_env_vars",
    "related_mcp_servers",
    "atlas_mcp_profiles",
    "purpose",
    "risk_level",
}
VALID_CREATIVE_PIPELINE_STATES = {"advisory", "approval_required", "watchlist", "blocked"}
COMPONENT_INSPIRATION_REQUIRED_PROFILES = {
    "ui_component_inspiration",
    "design_system_reference",
    "landing_section_patterns",
    "dashboard_patterns",
    "form_flow_patterns",
    "empty_error_loading_states",
    "component_generation_watchlist",
}
COMPONENT_INSPIRATION_REQUIRED_SERVICES = {
    "twentyfirst_magic",
    "context7",
}
COMPONENT_INSPIRATION_PROFILE_REQUIRED_FIELDS = {
    "suggested_services",
    "requirements",
    "expected_env_vars",
    "risk_level",
    "initial_state",
    "requires_human_approval",
    "fallback",
}
COMPONENT_INSPIRATION_SERVICE_REQUIRED_FIELDS = {
    "display_name",
    "expected_env_vars",
    "related_mcp_servers",
    "purpose",
    "risk_level",
}
VALID_COMPONENT_INSPIRATION_STATES = {"advisory", "approval_required", "watchlist", "blocked"}
PLAYWRIGHT_VISUAL_QA_REQUIRED_PROFILES = {
    "landing_visual_qa",
    "dashboard_visual_qa",
    "form_flow_visual_qa",
    "responsive_visual_qa",
    "regression_screenshot_watchlist",
}
PLAYWRIGHT_VISUAL_QA_PROFILE_REQUIRED_FIELDS = {
    "requirements",
    "risk_level",
    "initial_state",
    "requires_human_approval",
    "fallback",
}
VALID_PLAYWRIGHT_VISUAL_QA_STATES = {"advisory", "approval_required", "watchlist", "blocked"}
DESIGN_QUALITY_ENFORCEMENT_REQUIRED_FIELDS = {
    "version",
    "advisory_only",
    "required_inputs",
    "required_for_project_types",
    "backend_exempt_project_types",
    "warning_codes",
    "redesign_levels",
    "checks",
}
REQUIRED_DESIGN_QUALITY_CHECKS = {
    "border_weight_excessive",
    "shadow_style_heavy",
    "card_repetition",
    "weak_visual_hierarchy",
    "weak_button_hierarchy",
    "poor_spacing",
    "weak_color_system",
    "typography_without_intent",
    "wireframe_look",
    "amateur_internal_tool_look",
    "excessive_horizontal_spread",
    "unclear_state_feedback",
    "generic_dashboard_pattern",
    "brutalism_misapplied",
}
DESIGN_QUALITY_RULE_REQUIRED_FIELDS = {
    "severity",
    "signal",
    "why_it_matters",
    "recommended_fix",
    "blocks_ready_if_present",
}
REQUIRED_DESIGN_QUALITY_WARNING_CODES = {
    "design_quality_not_ready",
    "visual_system_weak",
    "hierarchy_weak",
    "amateur_ui_risk",
    "brutalism_misapplied",
    "excessive_visual_weight",
}
VALID_DESIGN_QUALITY_REDESIGN_LEVELS = {
    "none",
    "minor_polish",
    "layout_refactor",
    "visual_system_refactor",
    "full_redesign",
}
ATLAS_ERROR_LEARNING_REQUIRED_FIELDS = {
    "version",
    "advisory_only",
    "ui_project_types",
    "checks",
    "warning_codes",
}
ATLAS_ERROR_LEARNING_REQUIRED_CHECKS = {
    "hero_overflow_or_mobile_header_failure",
    "font_loading_or_typography_failure",
    "cta_or_onboarding_failure",
    "touch_accessibility_failure",
    "seo_or_security_baseline_missing",
    "visual_evidence_missing",
    "landing_reads_like_readme",
    "landing_copy_or_onboarding_weak",
    "integration_claims_ahead_of_readiness",
    "integration_missing_tests_or_labels",
}
ATLAS_ERROR_LEARNING_REQUIRED_WARNING_CODES = {
    "error_learning_ui_not_ready",
    "error_learning_landing_not_ready",
    "error_learning_integration_not_ready",
    "error_learning_visual_evidence_missing",
    "error_learning_readiness_label_mismatch",
}
ATLAS_ERROR_LEARNING_REQUIRED_CHECK_FIELDS = {
    "category",
    "severity",
    "signal",
    "why_it_matters",
    "recommended_fix",
    "blocks_ready_if_present",
}
CODEX_RUNTIME_COMPATIBILITY_REQUIRED_FIELDS = {
    "version",
    "advisory_only",
    "required_checks",
    "known_limitations",
    "manual_step_templates",
}
CODEX_RUNTIME_COMPATIBILITY_REQUIRED_CHECKS = {
    "codex_cli_available",
    "codex_version_visible",
    "mcp_cli_functional",
    "configured_mcp_servers_visible",
    "runtime_model_visibility",
    "atlas_compatibility",
}
CODEX_RUNTIME_COMPATIBILITY_REQUIRED_LIMITATIONS = {
    "manual_model_switch_only",
    "no_mcp_auto_activation",
    "config_visibility_can_be_partial",
    "runtime_probe_is_not_execution_proof",
}
ATLAS_MEMORY_READINESS_REQUIRED_FIELDS = {
    "version",
    "advisory_only",
    "risk_categories",
    "local_sources",
    "profiles",
}
ATLAS_MEMORY_READINESS_REQUIRED_PROFILES = {
    "local_session_summary",
    "cross_session_factory_memory",
    "derived_project_memory",
    "plugin_memory_watchlist",
    "auto_injection_watchlist",
    "cross_machine_sync_watchlist",
}
ATLAS_MEMORY_READINESS_REQUIRED_PROFILE_FIELDS = {
    "description",
    "required_sources",
    "risk_level",
    "initial_state",
    "requires_human_approval",
    "fallback",
}
ATLAS_MEMORY_READINESS_VALID_STATES = {"advisory", "approval_required", "watchlist"}
EVIDENCE_COLLECTOR_READINESS_REQUIRED_FIELDS = {
    "version",
    "advisory_only",
    "task_types",
    "project_type_map",
    "warning_codes",
}
EVIDENCE_COLLECTOR_REQUIRED_TASK_TYPES = {
    "frontend_ui_landing",
    "backend_api",
    "research_benchmark",
    "high_risk_decision",
    "skill_governance_change",
}
EVIDENCE_COLLECTOR_REQUIRED_TASK_FIELDS = {
    "required_evidence",
    "blocking_evidence",
    "advisory_evidence",
    "can_pass_with_caution_when_missing_only",
}
EVIDENCE_COLLECTOR_REQUIRED_WARNING_CODES = {
    "evidence_collector_missing",
    "evidence_collector_partial",
    "evidence_collector_not_ready",
    "evidence_collector_frontend_visual_gap",
    "evidence_collector_high_risk_gap",
}
CHANGE_PROPOSAL_REQUIRED_FIELDS = {
    "version",
    "advisory_only",
    "required_when",
    "required_artifacts",
    "artifact_requirements",
}
CHANGE_PROPOSAL_REQUIRED_ARTIFACTS = {
    "proposal",
    "specs",
    "design",
    "tasks",
    "verify",
    "archive",
}
CHANGE_PROPOSAL_REQUIRED_ARTIFACT_FIELDS = {
    "required_fields",
    "why_it_matters",
}
SKILL_REGISTRY_INDEX_FIRST_REQUIRED_FIELDS = {
    "version",
    "advisory_only",
    "accepted_skill_doc_names",
    "required_registry_fields",
    "required_companion_files",
    "optional_frontmatter_fields",
    "description_rules",
    "valid_lifecycle_states",
}
SKILL_REGISTRY_INDEX_FIRST_REQUIRED_REGISTRY_FIELDS = {
    "name",
    "description",
    "scope",
    "path",
    "lifecycle_state",
    "risk_level",
    "agent",
    "workflow",
}
SKILL_REGISTRY_INDEX_FIRST_REQUIRED_COMPANION_FILES = {
    "skill.json",
    "behavior.json",
}
UI_UX_DESIGN_SYSTEM_REQUIRED_FIELDS = {
    "version",
    "advisory_only",
    "required_inputs",
    "frontend_project_types",
    "product_profiles",
    "audience_modifiers",
    "motion_library_posture",
    "component_library_posture",
    "pre_delivery_checklist",
    "accessibility_baseline",
}
UI_UX_DESIGN_SYSTEM_REQUIRED_PRODUCT_FIELDS = {
    "id",
    "match_terms",
    "recommended_pattern",
    "recommended_style",
    "recommended_palette",
    "recommended_typography",
    "recommended_motion",
    "anti_patterns",
    "stack_recommendation",
    "style_priority",
}
UI_UX_DESIGN_SYSTEM_REQUIRED_MOTION_FIELDS = {
    "react_eligible_stacks",
    "css_first_stacks",
    "triggers_for_recommended_for_react",
    "reduced_motion_policy",
}
UI_UX_DESIGN_SYSTEM_REQUIRED_COMPONENT_LIBRARY_FIELDS = {
    "decision_types",
    "react_eligible_stacks",
    "static_or_css_first_stacks",
    "tailwind_signals",
    "high_fit_project_types",
    "best_for",
    "custom_identity_signals",
    "generic_design_blockers",
    "risks",
    "manual_install_required",
    "should_auto_install",
}
REPO_GRAPH_READINESS_REQUIRED_FIELDS = {
    "version",
    "advisory_only",
    "size_thresholds",
    "source_extensions",
    "route_detection",
    "multi_module_markers",
    "task_fit_signals",
    "blocked_task_types",
    "watchlist_terms",
    "manual_steps",
}
REPO_GRAPH_READINESS_REQUIRED_ROUTE_FIELDS = {
    "path_signals",
    "file_signals",
    "content_signals",
}
REPO_GRAPH_READINESS_REQUIRED_MANUAL_STEP_FIELDS = {
    "recommended",
    "watchlist",
}
BUSINESS_IDEA_SIMULATION_REQUIRED_FIELDS = {
    "version",
    "advisory_only",
    "required_inputs",
    "input_aliases",
    "core_inputs",
    "scenario_ready_inputs",
    "profitability_inputs",
    "blocked_prediction_terms",
    "research_required_inputs",
    "risk_categories",
    "risk_signals",
    "signal_thresholds",
    "experiment_catalog",
}
BUSINESS_IDEA_SIMULATION_REQUIRED_INPUTS = {
    "problem",
    "customer",
    "value_proposition",
    "competition",
    "pricing",
    "costs",
    "channels",
    "acquisition",
    "retention",
}
BUSINESS_IDEA_SIMULATION_REQUIRED_RISK_CATEGORIES = {
    "legal",
    "technical",
    "commercial",
}
BUSINESS_IDEA_SIMULATION_REQUIRED_THRESHOLDS = {
    "promising_min_present",
    "incomplete_min_present",
}
BUSINESS_IDEA_SIMULATION_REQUIRED_EXPERIMENT_FIELDS = {
    "id",
    "objective",
    "time_estimate",
    "success_signal",
}
VISUAL_FIDELITY_JUDGE_REQUIRED_FIELDS = {
    "version",
    "advisory_only",
    "frontend_project_types",
    "candidate_report_paths",
    "candidate_screenshot_dirs",
    "required_viewports",
    "viewport_filename_tokens",
    "core_compared_layers",
    "supporting_compared_layers",
    "minimum_signal_count",
    "warning_codes",
}
VISUAL_FIDELITY_JUDGE_REQUIRED_VIEWPORTS = {
    "desktop",
    "mobile",
}
VISUAL_FIDELITY_JUDGE_REQUIRED_CORE_LAYERS = {
    "visual_intent_contract",
    "brand_profile",
}
MODEL_COST_CONTROL_REQUIRED_FIELDS = {
    "version",
    "advisory_only",
    "tiers",
    "context_thresholds",
    "split_task_rules",
    "confirmation_triggers",
    "task_type_hints",
    "risk_signals",
}
MODEL_COST_CONTROL_REQUIRED_TIERS = {"strong", "medium", "mini"}
MODEL_COST_CONTROL_TIER_REQUIRED_FIELDS = {
    "description",
    "preferred_for_task_types",
    "preferred_for_risk_levels",
    "preferred_for_complexity_levels",
    "default_cost_saver_strategy",
    "default_context_reduction_strategy",
}
MODEL_COST_CONTROL_REQUIRED_CONTEXT_THRESHOLDS = {"small_chars", "medium_chars", "large_chars"}
MODEL_COST_CONTROL_REQUIRED_SPLIT_RULES = {
    "large_context_requires_split",
    "mixed_planning_and_execution_requires_split",
    "high_risk_plus_high_complexity_requires_split",
}
MODEL_COST_CONTROL_REQUIRED_CONFIRMATION_TRIGGERS = {
    "strong_tier_requires_confirmation",
    "ambiguous_task_type_requires_confirmation",
    "large_context_requires_confirmation",
    "cost_vs_quality_unclear_requires_confirmation",
}


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


def _load_model_cost_control_profiles(root: Path) -> Dict[str, Any]:
    return json.loads((root / "config" / "model_cost_control_profiles.json").read_text(encoding="utf-8"))


def _load_mcp_profiles(root: Path) -> Dict[str, Any]:
    return json.loads((root / "config" / "mcp_profiles.json").read_text(encoding="utf-8"))


def _load_external_tool_policy(root: Path) -> Dict[str, Any]:
    return json.loads((root / "config" / "external_tool_policy.json").read_text(encoding="utf-8"))


def _load_skill_lifecycle_rules(root: Path) -> Dict[str, Any]:
    return json.loads((root / "config" / "skill_lifecycle_rules.json").read_text(encoding="utf-8"))


def _load_skill_improvement_review_rules(root: Path) -> Dict[str, Any]:
    return json.loads((root / "config" / "skill_improvement_review_rules.json").read_text(encoding="utf-8"))


def _load_market_research_benchmark_rules(root: Path) -> Dict[str, Any]:
    return json.loads((root / "config" / "market_research_benchmark_rules.json").read_text(encoding="utf-8"))


def _load_intent_clarifier_contract_rules(root: Path) -> Dict[str, Any]:
    return json.loads((root / "config" / "intent_clarifier_contract_rules.json").read_text(encoding="utf-8"))


def _load_visual_intent_contract(root: Path) -> Dict[str, Any]:
    return json.loads((root / "config" / "visual_intent_contract_rules.json").read_text(encoding="utf-8"))


def _load_brand_json_v2_readiness_rules(root: Path) -> Dict[str, Any]:
    return json.loads((root / "config" / "brand_json_v2_readiness_rules.json").read_text(encoding="utf-8"))


def _load_brand_profile_schema(root: Path) -> Dict[str, Any]:
    return json.loads((root / "config" / "brand_profile_schema_rules.json").read_text(encoding="utf-8"))


def _load_frontend_auto_audit_rules(root: Path) -> Dict[str, Any]:
    return json.loads((root / "config" / "frontend_auto_audit_rules.json").read_text(encoding="utf-8"))


def _load_ui_pre_return_audit_rules(root: Path) -> Dict[str, Any]:
    return json.loads((root / "config" / "ui_pre_return_audit_rules.json").read_text(encoding="utf-8"))


def _load_creative_pipeline_profiles(root: Path) -> Dict[str, Any]:
    return json.loads((root / "config" / "creative_pipeline_profiles.json").read_text(encoding="utf-8"))


def _load_component_inspiration_profiles(root: Path) -> Dict[str, Any]:
    return json.loads((root / "config" / "component_inspiration_profiles.json").read_text(encoding="utf-8"))


def _load_playwright_visual_qa_profiles(root: Path) -> Dict[str, Any]:
    return json.loads((root / "config" / "playwright_visual_qa_profiles.json").read_text(encoding="utf-8"))


def _load_design_quality_enforcement_rules(root: Path) -> Dict[str, Any]:
    return json.loads((root / "config" / "design_quality_enforcement_rules.json").read_text(encoding="utf-8"))


def _load_atlas_error_learning_rules(root: Path) -> Dict[str, Any]:
    return json.loads((root / "config" / "atlas_error_learning_rules.json").read_text(encoding="utf-8"))


def _load_codex_runtime_compatibility_rules(root: Path) -> Dict[str, Any]:
    return json.loads((root / "config" / "codex_runtime_compatibility_rules.json").read_text(encoding="utf-8"))


def _load_atlas_memory_readiness_profiles(root: Path) -> Dict[str, Any]:
    return json.loads((root / "config" / "atlas_memory_readiness_profiles.json").read_text(encoding="utf-8"))


def _load_evidence_collector_readiness_rules(root: Path) -> Dict[str, Any]:
    return json.loads((root / "config" / "evidence_collector_readiness_rules.json").read_text(encoding="utf-8"))


def _load_change_proposal_rules(root: Path) -> Dict[str, Any]:
    return json.loads((root / "config" / "change_proposal_rules.json").read_text(encoding="utf-8"))


def _load_skill_registry_index_first_rules(root: Path) -> Dict[str, Any]:
    return json.loads((root / "config" / "skill_registry_index_first_rules.json").read_text(encoding="utf-8"))


def _load_ui_ux_design_system_rules(root: Path) -> Dict[str, Any]:
    return json.loads((root / "config" / "ui_ux_design_system_rules.json").read_text(encoding="utf-8"))


def _load_repo_graph_readiness_rules(root: Path) -> Dict[str, Any]:
    return json.loads((root / "config" / "repo_graph_readiness_rules.json").read_text(encoding="utf-8"))


def _load_business_idea_simulation_rules(root: Path) -> Dict[str, Any]:
    return json.loads((root / "config" / "business_idea_simulation_rules.json").read_text(encoding="utf-8"))


def _load_visual_fidelity_judge_rules(root: Path) -> Dict[str, Any]:
    return json.loads((root / "config" / "visual_fidelity_judge_rules.json").read_text(encoding="utf-8"))


def _load_chrome_devtools_mcp_rules(root: Path) -> Dict[str, Any]:
    return json.loads((root / "config" / "chrome_devtools_mcp_rules.json").read_text(encoding="utf-8"))


def _load_copywriting_conversion_rules(root: Path) -> Dict[str, Any]:
    return json.loads((root / "config" / "copywriting_conversion_rules.json").read_text(encoding="utf-8"))


def _load_brand_strategy_rules(root: Path) -> Dict[str, Any]:
    return json.loads((root / "config" / "brand_strategy_rules.json").read_text(encoding="utf-8"))


def _load_n8n_automation_readiness_rules(root: Path) -> Dict[str, Any]:
    return json.loads((root / "config" / "n8n_automation_readiness_rules.json").read_text(encoding="utf-8"))


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
    available_models = rules.get("available_models")
    if not isinstance(available_models, list) or not available_models:
        findings.append("model_routing_rules_missing_available_models")
        return
    available_model_set = {str(item).strip() for item in available_models if str(item).strip()}
    if available_model_set != EXPECTED_CODEX_ROUTING_MODELS:
        findings.append("model_routing_rules_available_models_mismatch")

    default_rule = rules.get("default_rule")
    if not isinstance(default_rule, dict):
        findings.append("model_routing_rules_missing_default_rule")
    else:
        recommended_model = str(default_rule.get("recommended_model", "")).strip()
        fallback_model = str(default_rule.get("fallback_model", "")).strip()
        recommended_profile = str(default_rule.get("recommended_model_profile", "")).strip()
        cost_saver_model = str(default_rule.get("cost_saver_model", "")).strip()
        if recommended_model not in available_model_set:
            findings.append(f"model_routing_rules_unknown_default_model:{recommended_model}")
        if fallback_model not in available_model_set:
            findings.append(f"model_routing_rules_unknown_default_fallback:{fallback_model}")
        if cost_saver_model and cost_saver_model not in available_model_set:
            findings.append(f"model_routing_rules_unknown_default_cost_saver:{cost_saver_model}")
        if recommended_profile and recommended_profile not in profile_names:
            findings.append(f"model_routing_rules_unknown_default_profile:{recommended_profile}")

    ambiguity_policy = rules.get("ambiguity_policy")
    if not isinstance(ambiguity_policy, dict) or not ambiguity_policy:
        findings.append("model_routing_rules_invalid_ambiguity_policy")

    auto_switch_policy = rules.get("auto_switch_policy")
    if not isinstance(auto_switch_policy, dict) or not auto_switch_policy:
        findings.append("model_routing_rules_invalid_auto_switch_policy")

    routing_rules = rules.get("routing_rules")
    if not isinstance(routing_rules, list) or not routing_rules:
        findings.append("model_routing_rules_missing_routing_rules")
        return

    for index, rule in enumerate(routing_rules, start=1):
        if not isinstance(rule, dict):
            findings.append(f"model_routing_rule_not_object:{index}")
            continue
        missing_fields = MODEL_ROUTING_RULE_REQUIRED_FIELDS - set(rule.keys())
        if missing_fields:
            findings.append(f"model_routing_rule_missing_fields:{index}:{','.join(sorted(missing_fields))}")

        recommended_model = str(rule.get("recommended_model", "")).strip()
        fallback_model = str(rule.get("fallback_model", "")).strip()
        recommended_profile = str(rule.get("recommended_model_profile", "")).strip()
        cost_saver_model = str(rule.get("cost_saver_model", "")).strip()
        if recommended_model not in available_model_set:
            findings.append(f"model_routing_rule_unknown_recommended_model:{index}:{recommended_model}")
        if fallback_model not in available_model_set:
            findings.append(f"model_routing_rule_unknown_fallback_model:{index}:{fallback_model}")
        if cost_saver_model and cost_saver_model not in available_model_set:
            findings.append(f"model_routing_rule_unknown_cost_saver_model:{index}:{cost_saver_model}")
        if recommended_profile and recommended_profile not in profile_names:
            findings.append(f"model_routing_rule_unknown_profile:{index}:{recommended_profile}")

        avoid_models = rule.get("avoid_models")
        if not isinstance(avoid_models, list):
            findings.append(f"model_routing_rule_invalid_avoid_models:{index}")
        else:
            for model_name in avoid_models:
                if str(model_name).strip() not in available_model_set:
                    findings.append(f"model_routing_rule_unknown_avoid_model:{index}:{model_name}")

        for field in ("task_type", "phase", "complexity", "risk_level", "cost_sensitivity"):
            value = rule.get(field)
            if not isinstance(value, list) or not value or not all(isinstance(item, str) and item.strip() for item in value):
                findings.append(f"model_routing_rule_invalid_selector:{index}:{field}")

        if not isinstance(rule.get("requires_confirmation_when_ambiguous"), bool):
            findings.append(f"model_routing_rule_invalid_confirmation_flag:{index}")


def _validate_model_cost_control_profiles(root: Path, findings: List[str]) -> None:
    try:
        config = _load_model_cost_control_profiles(root)
    except Exception as exc:
        findings.append(f"invalid_model_cost_control_profiles_json:{exc}")
        return

    if not isinstance(config, dict):
        findings.append("model_cost_control_profiles_not_object")
        return

    missing_fields = MODEL_COST_CONTROL_REQUIRED_FIELDS - set(config.keys())
    if missing_fields:
        findings.append(f"model_cost_control_profiles_missing_fields:{','.join(sorted(missing_fields))}")

    tiers = config.get("tiers")
    if not isinstance(tiers, dict) or not tiers:
        findings.append("model_cost_control_profiles_invalid_tiers")
    else:
        missing_tiers = MODEL_COST_CONTROL_REQUIRED_TIERS - set(tiers.keys())
        if missing_tiers:
            findings.append(f"model_cost_control_profiles_missing_tiers:{','.join(sorted(missing_tiers))}")
        for tier_name, tier in tiers.items():
            if not isinstance(tier, dict):
                findings.append(f"model_cost_control_profiles_invalid_tier:{tier_name}")
                continue
            missing_tier_fields = MODEL_COST_CONTROL_TIER_REQUIRED_FIELDS - set(tier.keys())
            if missing_tier_fields:
                findings.append(
                    f"model_cost_control_profiles_missing_tier_fields:{tier_name}:{','.join(sorted(missing_tier_fields))}"
                )
            for field_name in (
                "preferred_for_task_types",
                "preferred_for_risk_levels",
                "preferred_for_complexity_levels",
            ):
                value = tier.get(field_name)
                if not isinstance(value, list) or not value:
                    findings.append(f"model_cost_control_profiles_invalid_tier_list:{tier_name}:{field_name}")

    context_thresholds = config.get("context_thresholds")
    if not isinstance(context_thresholds, dict) or not context_thresholds:
        findings.append("model_cost_control_profiles_invalid_context_thresholds")
    else:
        missing_thresholds = MODEL_COST_CONTROL_REQUIRED_CONTEXT_THRESHOLDS - set(context_thresholds.keys())
        if missing_thresholds:
            findings.append(
                f"model_cost_control_profiles_missing_context_thresholds:{','.join(sorted(missing_thresholds))}"
            )

    split_task_rules = config.get("split_task_rules")
    if not isinstance(split_task_rules, dict) or not split_task_rules:
        findings.append("model_cost_control_profiles_invalid_split_task_rules")
    else:
        missing_split_rules = MODEL_COST_CONTROL_REQUIRED_SPLIT_RULES - set(split_task_rules.keys())
        if missing_split_rules:
            findings.append(
                f"model_cost_control_profiles_missing_split_task_rules:{','.join(sorted(missing_split_rules))}"
            )

    confirmation_triggers = config.get("confirmation_triggers")
    if not isinstance(confirmation_triggers, dict) or not confirmation_triggers:
        findings.append("model_cost_control_profiles_invalid_confirmation_triggers")
    else:
        missing_confirmation = MODEL_COST_CONTROL_REQUIRED_CONFIRMATION_TRIGGERS - set(confirmation_triggers.keys())
        if missing_confirmation:
            findings.append(
                f"model_cost_control_profiles_missing_confirmation_triggers:{','.join(sorted(missing_confirmation))}"
            )

    for field_name in ("task_type_hints", "risk_signals"):
        value = config.get(field_name)
        if not isinstance(value, dict) or not value:
            findings.append(f"model_cost_control_profiles_invalid_dict:{field_name}")


def _validate_atlas_memory_readiness_profiles(root: Path, findings: List[str]) -> None:
    try:
        rules = _load_atlas_memory_readiness_profiles(root)
    except Exception as exc:
        findings.append(f"invalid_atlas_memory_readiness_profiles_json:{exc}")
        return

    if not isinstance(rules, dict):
        findings.append("atlas_memory_readiness_profiles_not_object")
        return

    missing_fields = ATLAS_MEMORY_READINESS_REQUIRED_FIELDS - set(rules.keys())
    if missing_fields:
        findings.append(
            f"atlas_memory_readiness_profiles_missing_fields:{','.join(sorted(missing_fields))}"
        )

    local_sources = rules.get("local_sources")
    if not isinstance(local_sources, dict) or not local_sources:
        findings.append("atlas_memory_readiness_profiles_invalid_local_sources")
    else:
        for source_name, source in local_sources.items():
            if not isinstance(source, dict):
                findings.append(f"atlas_memory_readiness_profiles_invalid_source:{source_name}")
                continue
            for field_name in ("path", "requires_content", "purpose"):
                if field_name not in source:
                    findings.append(
                        f"atlas_memory_readiness_profiles_missing_source_field:{source_name}:{field_name}"
                    )
            if not isinstance(source.get("requires_content"), bool):
                findings.append(
                    f"atlas_memory_readiness_profiles_invalid_source_requires_content:{source_name}"
                )

    profiles = rules.get("profiles")
    if not isinstance(profiles, dict) or not profiles:
        findings.append("atlas_memory_readiness_profiles_invalid_profiles")
    else:
        missing_profiles = ATLAS_MEMORY_READINESS_REQUIRED_PROFILES - set(profiles.keys())
        if missing_profiles:
            findings.append(
                f"atlas_memory_readiness_profiles_missing_profiles:{','.join(sorted(missing_profiles))}"
            )
        for profile_name, profile in profiles.items():
            if not isinstance(profile, dict):
                findings.append(f"atlas_memory_readiness_profiles_invalid_profile:{profile_name}")
                continue
            missing_profile_fields = ATLAS_MEMORY_READINESS_REQUIRED_PROFILE_FIELDS - set(profile.keys())
            if missing_profile_fields:
                findings.append(
                    f"atlas_memory_readiness_profiles_missing_profile_fields:{profile_name}:{','.join(sorted(missing_profile_fields))}"
                )
            if not isinstance(profile.get("required_sources"), list):
                findings.append(
                    f"atlas_memory_readiness_profiles_invalid_required_sources:{profile_name}"
                )
            initial_state = str(profile.get("initial_state", "")).strip()
            if initial_state not in ATLAS_MEMORY_READINESS_VALID_STATES:
                findings.append(
                    f"atlas_memory_readiness_profiles_invalid_initial_state:{profile_name}:{initial_state}"
                )
            if not isinstance(profile.get("requires_human_approval"), bool):
                findings.append(
                    f"atlas_memory_readiness_profiles_invalid_approval_flag:{profile_name}"
                )

    risk_categories = rules.get("risk_categories")
    if not isinstance(risk_categories, list) or not risk_categories:
        findings.append("atlas_memory_readiness_profiles_invalid_risk_categories")


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


def _validate_external_tool_policy(root: Path, findings: List[str]) -> None:
    try:
        policy = _load_external_tool_policy(root)
    except Exception as exc:
        findings.append(f"invalid_external_tool_policy_json:{exc}")
        return

    if not isinstance(policy, dict):
        findings.append("external_tool_policy_not_object")
        return

    missing = EXTERNAL_TOOL_POLICY_REQUIRED_FIELDS - set(policy.keys())
    if missing:
        findings.append(f"external_tool_policy_missing_fields:{','.join(sorted(missing))}")

    if str(policy.get("mode", "")).strip() != "advisory_only":
        findings.append("external_tool_policy_invalid_mode")

    layers = policy.get("layers")
    layer_names = {str(item).strip() for item in layers} if isinstance(layers, list) else set()
    if not isinstance(layers, list) or not EXTERNAL_TOOL_POLICY_REQUIRED_LAYERS.issubset(layer_names):
        findings.append("external_tool_policy_invalid_layers")

    source_priority = policy.get("source_priority")
    if not isinstance(source_priority, list) or len(source_priority) < 5:
        findings.append("external_tool_policy_invalid_source_priority")

    default_stance = policy.get("default_stance")
    if not isinstance(default_stance, dict):
        findings.append("external_tool_policy_invalid_default_stance")
    else:
        if str(default_stance.get("mcp", "")).strip() != "blocked_until_readiness_verified":
            findings.append("external_tool_policy_invalid_mcp_stance")
        if str(default_stance.get("preferred_mode", "")).strip() != "read_only":
            findings.append("external_tool_policy_invalid_preferred_mode")

    for field in ("prefer_cli_over_mcp_when", "do_not_use_external_tools_when", "risk_axes"):
        value = policy.get(field)
        if not isinstance(value, list) or not value:
            findings.append(f"external_tool_policy_invalid_list:{field}")

    if not isinstance(policy.get("integration_hints"), dict) or not policy.get("integration_hints"):
        findings.append("external_tool_policy_invalid_integration_hints")


def _validate_skill_lifecycle_rules(root: Path, findings: List[str]) -> None:
    try:
        rules = _load_skill_lifecycle_rules(root)
    except Exception as exc:
        findings.append(f"invalid_skill_lifecycle_rules_json:{exc}")
        return

    if not isinstance(rules, dict):
        findings.append("skill_lifecycle_rules_not_object")
        return

    missing_fields = SKILL_LIFECYCLE_RULES_REQUIRED_FIELDS - set(rules.keys())
    if missing_fields:
        findings.append(f"skill_lifecycle_rules_missing_fields:{','.join(sorted(missing_fields))}")

    states = rules.get("states")
    if not isinstance(states, list) or not states or not all(isinstance(item, str) and item.strip() for item in states):
        findings.append("skill_lifecycle_rules_invalid_states")
        return

    state_set = {str(item).strip() for item in states}
    missing_states = REQUIRED_SKILL_LIFECYCLE_STATES - state_set
    unknown_states = state_set - REQUIRED_SKILL_LIFECYCLE_STATES
    if missing_states:
        findings.append(f"skill_lifecycle_rules_missing_states:{','.join(sorted(missing_states))}")
    if unknown_states:
        findings.append(f"skill_lifecycle_rules_unknown_states:{','.join(sorted(unknown_states))}")

    allowed_transitions = rules.get("allowed_transitions")
    if not isinstance(allowed_transitions, dict):
        findings.append("skill_lifecycle_rules_invalid_allowed_transitions")
    else:
        for state in REQUIRED_SKILL_LIFECYCLE_STATES:
            transitions = allowed_transitions.get(state)
            if not isinstance(transitions, list):
                findings.append(f"skill_lifecycle_rules_invalid_transitions:{state}")
                continue
            for transition in transitions:
                if str(transition).strip() not in REQUIRED_SKILL_LIFECYCLE_STATES:
                    findings.append(f"skill_lifecycle_rules_unknown_transition:{state}:{transition}")

    for field_name in (
        "required_fields_by_state",
        "test_requirements_by_state",
        "documentation_requirements_by_state",
        "human_approval_required_by_state",
        "allowed_risk_by_state",
    ):
        value = rules.get(field_name)
        if not isinstance(value, dict):
            findings.append(f"skill_lifecycle_rules_invalid_section:{field_name}")
            continue
        missing_state_keys = REQUIRED_SKILL_LIFECYCLE_STATES - set(value.keys())
        if missing_state_keys:
            findings.append(
                f"skill_lifecycle_rules_missing_section_states:{field_name}:{','.join(sorted(missing_state_keys))}"
            )

    allowed_risk_by_state = rules.get("allowed_risk_by_state", {})
    if isinstance(allowed_risk_by_state, dict):
        for state, risks in allowed_risk_by_state.items():
            if not isinstance(risks, list) or not risks:
                findings.append(f"skill_lifecycle_rules_invalid_risk_list:{state}")
                continue
            for risk in risks:
                if str(risk).strip() not in VALID_SKILL_RISK_LEVELS:
                    findings.append(f"skill_lifecycle_rules_unknown_risk_level:{state}:{risk}")

    human_approval_by_state = rules.get("human_approval_required_by_state", {})
    if isinstance(human_approval_by_state, dict):
        for state, value in human_approval_by_state.items():
            if not isinstance(value, bool):
                findings.append(f"skill_lifecycle_rules_invalid_approval_flag:{state}")


def _validate_skill_improvement_review_rules(root: Path, findings: List[str]) -> None:
    try:
        rules = _load_skill_improvement_review_rules(root)
    except Exception as exc:
        findings.append(f"invalid_skill_improvement_review_rules_json:{exc}")
        return

    if not isinstance(rules, dict):
        findings.append("skill_improvement_review_rules_not_object")
        return

    missing_fields = SKILL_IMPROVEMENT_REVIEW_REQUIRED_FIELDS - set(rules.keys())
    if missing_fields:
        findings.append(
            "skill_improvement_review_rules_missing_fields:" + ",".join(sorted(missing_fields))
        )

    scoring_rules = rules.get("scoring_rules")
    if not isinstance(scoring_rules, dict) or not scoring_rules:
        findings.append("skill_improvement_review_rules_invalid_scoring_rules")
    else:
        required_scoring_fields = {
            "base_score",
            "missing_tests_penalty",
            "missing_docs_penalty",
            "missing_behavior_penalty",
            "missing_skill_json_penalty",
            "duplicate_penalty_medium",
            "duplicate_penalty_high",
            "external_dependency_penalty_medium",
            "external_dependency_penalty_high",
            "stale_state_penalty",
            "minimum_score_for_keep",
            "minimum_score_for_improve",
        }
        missing_scoring = required_scoring_fields - set(scoring_rules.keys())
        if missing_scoring:
            findings.append(
                "skill_improvement_review_rules_missing_scoring_fields:"
                + ",".join(sorted(missing_scoring))
            )

    recommendation_types = rules.get("recommendation_types")
    if not isinstance(recommendation_types, list) or not recommendation_types:
        findings.append("skill_improvement_review_rules_invalid_recommendation_types")
    else:
        recommendation_set = {str(item).strip() for item in recommendation_types if str(item).strip()}
        missing_recommendations = REQUIRED_SKILL_IMPROVEMENT_RECOMMENDATIONS - recommendation_set
        if missing_recommendations:
            findings.append(
                "skill_improvement_review_rules_missing_recommendation_types:"
                + ",".join(sorted(missing_recommendations))
            )

    for field_name in (
        "maturity_signals",
        "duplication_signals",
        "external_dependency_signals",
        "risk_scoring",
    ):
        value = rules.get(field_name)
        if not isinstance(value, dict) or not value:
            findings.append(f"skill_improvement_review_rules_invalid_object:{field_name}")

    for field_name in ("stale_skill_signals", "missing_test_signals", "missing_docs_signals"):
        value = rules.get(field_name)
        if not isinstance(value, list) or not value:
            findings.append(f"skill_improvement_review_rules_invalid_list:{field_name}")


def _validate_market_research_benchmark_rules(root: Path, findings: List[str]) -> None:
    try:
        rules = _load_market_research_benchmark_rules(root)
    except Exception as exc:
        findings.append(f"invalid_market_research_benchmark_rules_json:{exc}")
        return

    if not isinstance(rules, dict):
        findings.append("market_research_benchmark_rules_not_object")
        return

    missing_fields = MARKET_RESEARCH_BENCHMARK_REQUIRED_FIELDS - set(rules.keys())
    if missing_fields:
        findings.append(
            "market_research_benchmark_rules_missing_fields:" + ",".join(sorted(missing_fields))
        )

    primary_reference = rules.get("primary_reference_repo")
    if not isinstance(primary_reference, dict) or not primary_reference:
        findings.append("market_research_benchmark_rules_invalid_primary_reference_repo")
    else:
        for field_name in ("id", "source_type", "path"):
            if not str(primary_reference.get(field_name, "")).strip():
                findings.append(f"market_research_benchmark_rules_missing_primary_reference_field:{field_name}")

    for field_name in (
        "allowed_source_types",
        "benchmark_axes",
        "recommendation_types",
        "required_output_sections",
        "high_risk_signals",
        "requires_decision_council_signals",
    ):
        value = rules.get(field_name)
        if not isinstance(value, list) or not value:
            findings.append(f"market_research_benchmark_rules_invalid_list:{field_name}")

    source_types = {str(item).strip() for item in rules.get("allowed_source_types", []) if str(item).strip()}
    missing_source_types = REQUIRED_MARKET_RESEARCH_SOURCE_TYPES - source_types
    if missing_source_types:
        findings.append(
            "market_research_benchmark_rules_missing_source_types:" + ",".join(sorted(missing_source_types))
        )

    recommendation_types = {str(item).strip() for item in rules.get("recommendation_types", []) if str(item).strip()}
    missing_recommendations = REQUIRED_MARKET_RESEARCH_RECOMMENDATIONS - recommendation_types
    if missing_recommendations:
        findings.append(
            "market_research_benchmark_rules_missing_recommendations:" + ",".join(sorted(missing_recommendations))
        )

    reference_catalog = rules.get("reference_catalog")
    if not isinstance(reference_catalog, list) or not reference_catalog:
        findings.append("market_research_benchmark_rules_invalid_reference_catalog")
    else:
        seen_ids: Set[str] = set()
        for index, item in enumerate(reference_catalog, start=1):
            if not isinstance(item, dict):
                findings.append(f"market_research_benchmark_reference_{index}:not_object")
                continue
            reference_id = str(item.get("id", "")).strip()
            if not reference_id:
                findings.append(f"market_research_benchmark_reference_{index}:missing_id")
            elif reference_id in seen_ids:
                findings.append(f"market_research_benchmark_duplicate_reference_id:{reference_id}")
            else:
                seen_ids.add(reference_id)
            if str(item.get("source_type", "")).strip() not in source_types:
                findings.append(f"market_research_benchmark_reference_{index}:invalid_source_type")
            for field_name in ("source", "benefit", "risk", "fit", "default_recommendation"):
                if not str(item.get(field_name, "")).strip():
                    findings.append(f"market_research_benchmark_reference_{index}:missing_field:{field_name}")
            if not isinstance(item.get("focus_areas"), list) or not item.get("focus_areas"):
                findings.append(f"market_research_benchmark_reference_{index}:invalid_focus_areas")
            if not isinstance(item.get("notes"), list) or not item.get("notes"):
                findings.append(f"market_research_benchmark_reference_{index}:invalid_notes")
            if not isinstance(item.get("risk_signals"), list):
                findings.append(f"market_research_benchmark_reference_{index}:invalid_risk_signals")
            if str(item.get("default_recommendation", "")).strip() not in recommendation_types:
                findings.append(f"market_research_benchmark_reference_{index}:invalid_default_recommendation")


def _validate_intent_clarifier_contract_rules(root: Path, findings: List[str]) -> None:
    try:
        rules = _load_intent_clarifier_contract_rules(root)
    except Exception as exc:
        findings.append(f"invalid_intent_clarifier_contract_rules_json:{exc}")
        return

    if not isinstance(rules, dict):
        findings.append("intent_clarifier_contract_rules_not_object")
        return

    missing_fields = INTENT_CLARIFIER_REQUIRED_FIELDS - set(rules.keys())
    if missing_fields:
        findings.append(f"intent_clarifier_contract_rules_missing_fields:{','.join(sorted(missing_fields))}")

    for field_name in (
        "required_fields",
        "ui_required_fields",
        "recommended_fields",
        "required_for_project_types",
        "backend_exempt_project_types",
        "weak_answer_patterns",
        "approval_triggers",
    ):
        value = rules.get(field_name)
        if not isinstance(value, list) or not value:
            findings.append(f"intent_clarifier_contract_rules_invalid_list:{field_name}")

    if not isinstance(rules.get("domain_signals"), dict) or not rules.get("domain_signals"):
        findings.append("intent_clarifier_contract_rules_invalid_domain_signals")

    required_fields = {str(item).strip() for item in rules.get("required_fields", []) if str(item).strip()}
    missing_required = REQUIRED_INTENT_CLARIFIER_FIELDS - required_fields
    if missing_required:
        findings.append(
            f"intent_clarifier_contract_rules_missing_required_fields:{','.join(sorted(missing_required))}"
        )

    ui_required_fields = {str(item).strip() for item in rules.get("ui_required_fields", []) if str(item).strip()}
    missing_ui_required = REQUIRED_INTENT_CLARIFIER_UI_FIELDS - ui_required_fields
    if missing_ui_required:
        findings.append(
            f"intent_clarifier_contract_rules_missing_ui_required_fields:{','.join(sorted(missing_ui_required))}"
        )

    if not isinstance(rules.get("advisory_only"), bool):
        findings.append("intent_clarifier_contract_rules_invalid_advisory_only")
    if not isinstance(rules.get("minimum_ready_fields"), int):
        findings.append("intent_clarifier_contract_rules_invalid_minimum_ready_fields")


def _validate_visual_intent_contract(root: Path, findings: List[str]) -> None:
    try:
        contract = _load_visual_intent_contract(root)
    except Exception as exc:
        findings.append(f"invalid_visual_intent_contract_json:{exc}")
        return

    if not isinstance(contract, dict):
        findings.append("visual_intent_contract_not_object")
        return

    missing_fields = VISUAL_INTENT_CONTRACT_REQUIRED_FIELDS - set(contract.keys())
    if missing_fields:
        findings.append(f"visual_intent_contract_missing_fields:{','.join(sorted(missing_fields))}")

    required_fields = contract.get("required_fields")
    if not isinstance(required_fields, list) or not required_fields:
        findings.append("visual_intent_contract_invalid_required_fields")
    else:
        required_set = {str(item).strip() for item in required_fields if str(item).strip()}
        missing_required = REQUIRED_VISUAL_INTENT_FIELDS - required_set
        unknown_required = required_set - REQUIRED_VISUAL_INTENT_FIELDS
        if missing_required:
            findings.append(f"visual_intent_contract_missing_required_fields:{','.join(sorted(missing_required))}")
        if unknown_required:
            findings.append(f"visual_intent_contract_unknown_required_fields:{','.join(sorted(unknown_required))}")

    if not isinstance(contract.get("advisory_only"), bool):
        findings.append("visual_intent_contract_invalid_advisory_only")

    originality_levels = contract.get("allowed_originality_levels")
    if not isinstance(originality_levels, list) or set(originality_levels) != {
        "conservative",
        "balanced",
        "distinctive",
        "experimental",
    }:
        findings.append("visual_intent_contract_invalid_originality_levels")

    motion_levels = contract.get("allowed_motion_intensity")
    if not isinstance(motion_levels, list) or set(motion_levels) != {"low", "medium", "high"}:
        findings.append("visual_intent_contract_invalid_motion_intensity_levels")

    density_levels = contract.get("allowed_visual_density")
    if not isinstance(density_levels, list) or set(density_levels) != {"low", "medium", "high"}:
        findings.append("visual_intent_contract_invalid_visual_density_levels")

    minimum_evidence = contract.get("minimum_evidence_expectations")
    if not isinstance(minimum_evidence, list) or not minimum_evidence:
        findings.append("visual_intent_contract_invalid_minimum_evidence_expectations")

    for field_name in ("required_for_project_types", "ui_surface_signals", "backend_exempt_project_types"):
        value = contract.get(field_name)
        if not isinstance(value, list) or not value:
            findings.append(f"visual_intent_contract_invalid_list:{field_name}")

    weak_rules = contract.get("weak_field_rules")
    if not isinstance(weak_rules, dict) or not weak_rules:
        findings.append("visual_intent_contract_invalid_weak_field_rules")


def _validate_brand_profile_schema(root: Path, findings: List[str]) -> None:
    try:
        schema = _load_brand_profile_schema(root)
    except Exception as exc:
        findings.append(f"invalid_brand_profile_schema_json:{exc}")
        return

    if not isinstance(schema, dict):
        findings.append("brand_profile_schema_not_object")
        return

    missing_fields = BRAND_PROFILE_SCHEMA_REQUIRED_FIELDS - set(schema.keys())
    if missing_fields:
        findings.append(f"brand_profile_schema_missing_fields:{','.join(sorted(missing_fields))}")

    required_fields = schema.get("required_fields")
    if not isinstance(required_fields, list) or not required_fields:
        findings.append("brand_profile_schema_invalid_required_fields")
    else:
        required_set = {str(item).strip() for item in required_fields if str(item).strip()}
        missing_required = REQUIRED_BRAND_PROFILE_FIELDS - required_set
        unknown_required = required_set - REQUIRED_BRAND_PROFILE_FIELDS
        if missing_required:
            findings.append(f"brand_profile_schema_missing_required_fields:{','.join(sorted(missing_required))}")
        if unknown_required:
            findings.append(f"brand_profile_schema_unknown_required_fields:{','.join(sorted(unknown_required))}")

    recommended_fields = schema.get("recommended_fields")
    if not isinstance(recommended_fields, list) or not recommended_fields:
        findings.append("brand_profile_schema_invalid_recommended_fields")

    if not isinstance(schema.get("advisory_only"), bool):
        findings.append("brand_profile_schema_invalid_advisory_only")

    originality_levels = schema.get("allowed_originality_levels")
    if not isinstance(originality_levels, list) or set(originality_levels) != {
        "conservative",
        "balanced",
        "distinctive",
        "experimental",
    }:
        findings.append("brand_profile_schema_invalid_originality_levels")

    density_levels = schema.get("allowed_visual_density")
    if not isinstance(density_levels, list) or set(density_levels) != {"low", "medium", "high"}:
        findings.append("brand_profile_schema_invalid_visual_density_levels")

    mood_dimensions = schema.get("mood_vector_dimensions")
    if not isinstance(mood_dimensions, list) or set(mood_dimensions) != REQUIRED_BRAND_MOOD_VECTOR_DIMENSIONS:
        findings.append("brand_profile_schema_invalid_mood_vector_dimensions")

    mood_range = schema.get("mood_vector_range")
    if not isinstance(mood_range, dict):
        findings.append("brand_profile_schema_invalid_mood_vector_range")
    else:
        if mood_range.get("min") != 0 or mood_range.get("max") != 10:
            findings.append("brand_profile_schema_invalid_mood_vector_bounds")

    color_fields = schema.get("required_color_strategy_fields")
    if not isinstance(color_fields, list) or set(color_fields) != REQUIRED_BRAND_COLOR_STRATEGY_FIELDS:
        findings.append("brand_profile_schema_invalid_color_strategy_fields")

    typography_fields = schema.get("required_typography_strategy_fields")
    if not isinstance(typography_fields, list) or set(typography_fields) != REQUIRED_BRAND_TYPOGRAPHY_FIELDS:
        findings.append("brand_profile_schema_invalid_typography_strategy_fields")

    for field_name in (
        "required_for_project_types",
        "ui_surface_signals",
        "backend_exempt_project_types",
        "anti_generic_criteria",
        "forbidden_font_patterns",
        "derivative_reference_signals",
        "minimum_evidence_expectations",
    ):
        value = schema.get(field_name)
        if not isinstance(value, list) or not value:
            findings.append(f"brand_profile_schema_invalid_list:{field_name}")

    quality_rules = schema.get("minimum_quality_rules")
    if not isinstance(quality_rules, dict) or not quality_rules:
        findings.append("brand_profile_schema_invalid_minimum_quality_rules")
    else:
        required_quality_keys = {
            "personality_traits_min_items",
            "layout_principles_min_items",
            "motion_principles_min_items",
            "anti_patterns_min_items",
            "evidence_expectations_min_items",
            "differentiation_notes_min_words",
        }
        missing_quality = required_quality_keys - set(quality_rules.keys())
        if missing_quality:
            findings.append(f"brand_profile_schema_missing_quality_rules:{','.join(sorted(missing_quality))}")


def _validate_ui_pre_return_audit_rules(root: Path, findings: List[str]) -> None:
    try:
        rules = _load_ui_pre_return_audit_rules(root)
    except Exception as exc:
        findings.append(f"invalid_ui_pre_return_audit_rules_json:{exc}")
        return

    if not isinstance(rules, dict):
        findings.append("ui_pre_return_audit_rules_not_object")
        return

    missing_fields = UI_PRE_RETURN_AUDIT_REQUIRED_FIELDS - set(rules.keys())
    if missing_fields:
        findings.append(f"ui_pre_return_audit_rules_missing_fields:{','.join(sorted(missing_fields))}")

    for field_name in ("required_inputs", "required_for_project_types", "backend_exempt_project_types"):
        value = rules.get(field_name)
        if not isinstance(value, list) or not value:
            findings.append(f"ui_pre_return_audit_rules_invalid_list:{field_name}")

    checks = rules.get("checks")
    if not isinstance(checks, list) or not checks:
        findings.append("ui_pre_return_audit_rules_invalid_checks")
    else:
        check_set = {str(item).strip() for item in checks if str(item).strip()}
        missing_checks = REQUIRED_UI_PRE_RETURN_CHECKS - check_set
        unknown_checks = check_set - REQUIRED_UI_PRE_RETURN_CHECKS
        if missing_checks:
            findings.append(f"ui_pre_return_audit_rules_missing_checks:{','.join(sorted(missing_checks))}")
        if unknown_checks:
            findings.append(f"ui_pre_return_audit_rules_unknown_checks:{','.join(sorted(unknown_checks))}")

    severity = rules.get("severity")
    if not isinstance(severity, dict) or not severity:
        findings.append("ui_pre_return_audit_rules_invalid_severity")
    else:
        missing_severity = REQUIRED_UI_PRE_RETURN_CHECKS - {str(key).strip() for key in severity.keys()}
        if missing_severity:
            findings.append(f"ui_pre_return_audit_rules_missing_severity:{','.join(sorted(missing_severity))}")

    warning_codes = rules.get("warning_codes")
    if not isinstance(warning_codes, list) or not warning_codes:
        findings.append("ui_pre_return_audit_rules_invalid_warning_codes")
    else:
        warning_set = {str(item).strip() for item in warning_codes if str(item).strip()}
        missing_warnings = REQUIRED_UI_PRE_RETURN_WARNING_CODES - warning_set
        unknown_warnings = warning_set - REQUIRED_UI_PRE_RETURN_WARNING_CODES
        if missing_warnings:
            findings.append(f"ui_pre_return_audit_rules_missing_warning_codes:{','.join(sorted(missing_warnings))}")
        if unknown_warnings:
            findings.append(f"ui_pre_return_audit_rules_unknown_warning_codes:{','.join(sorted(unknown_warnings))}")

    evidence_required = rules.get("evidence_required")
    if not isinstance(evidence_required, dict) or not evidence_required:
        findings.append("ui_pre_return_audit_rules_invalid_evidence_required")
    else:
        missing_evidence_rules = REQUIRED_UI_PRE_RETURN_CHECKS - {str(key).strip() for key in evidence_required.keys()}
        if missing_evidence_rules:
            findings.append(
                f"ui_pre_return_audit_rules_missing_evidence_required:{','.join(sorted(missing_evidence_rules))}"
            )

    for field_name in (
        "pass_conditions",
        "anti_generic_patterns",
        "brand_alignment_checks",
        "accessibility_basics",
        "responsive_expectations",
    ):
        value = rules.get(field_name)
        if not isinstance(value, list) or not value:
            findings.append(f"ui_pre_return_audit_rules_invalid_list:{field_name}")


def _validate_creative_pipeline_profiles(root: Path, findings: List[str]) -> None:
    try:
        rules = _load_creative_pipeline_profiles(root)
    except Exception as exc:
        findings.append(f"invalid_creative_pipeline_profiles_json:{exc}")
        return

    if not isinstance(rules, dict):
        findings.append("creative_pipeline_profiles_not_object")
        return

    services = rules.get("services")
    profiles = rules.get("profiles")
    if not isinstance(services, dict) or not services:
        findings.append("creative_pipeline_profiles_invalid_services")
        return
    if not isinstance(profiles, dict) or not profiles:
        findings.append("creative_pipeline_profiles_invalid_profiles")
        return

    missing_services = CREATIVE_PIPELINE_REQUIRED_SERVICES - set(services.keys())
    if missing_services:
        findings.append(f"creative_pipeline_profiles_missing_services:{','.join(sorted(missing_services))}")
    missing_profiles = CREATIVE_PIPELINE_REQUIRED_PROFILES - set(profiles.keys())
    if missing_profiles:
        findings.append(f"creative_pipeline_profiles_missing_profiles:{','.join(sorted(missing_profiles))}")

    for service_name, service in services.items():
        if not isinstance(service, dict):
            findings.append(f"creative_pipeline_profiles_invalid_service:{service_name}")
            continue
        missing_fields = CREATIVE_PIPELINE_SERVICE_REQUIRED_FIELDS - set(service.keys())
        if missing_fields:
            findings.append(
                f"creative_pipeline_profiles_missing_service_fields:{service_name}:{','.join(sorted(missing_fields))}"
            )
        for field_name in ("expected_env_vars", "related_mcp_servers", "atlas_mcp_profiles"):
            value = service.get(field_name)
            if not isinstance(value, list):
                findings.append(f"creative_pipeline_profiles_invalid_service_list:{service_name}:{field_name}")
        if str(service.get("risk_level", "")).strip() not in VALID_SKILL_RISK_LEVELS:
            findings.append(f"creative_pipeline_profiles_invalid_service_risk:{service_name}")

    for profile_name, profile in profiles.items():
        if not isinstance(profile, dict):
            findings.append(f"creative_pipeline_profiles_invalid_profile:{profile_name}")
            continue
        missing_fields = CREATIVE_PIPELINE_PROFILE_REQUIRED_FIELDS - set(profile.keys())
        if missing_fields:
            findings.append(
                f"creative_pipeline_profiles_missing_profile_fields:{profile_name}:{','.join(sorted(missing_fields))}"
            )
        for field_name in ("suggested_services", "requirements", "expected_env_vars"):
            value = profile.get(field_name)
            if not isinstance(value, list):
                findings.append(f"creative_pipeline_profiles_invalid_profile_list:{profile_name}:{field_name}")
        if str(profile.get("risk_level", "")).strip() not in VALID_SKILL_RISK_LEVELS:
            findings.append(f"creative_pipeline_profiles_invalid_profile_risk:{profile_name}")
        if str(profile.get("initial_state", "")).strip() not in VALID_CREATIVE_PIPELINE_STATES:
            findings.append(f"creative_pipeline_profiles_invalid_profile_state:{profile_name}")
        if not isinstance(profile.get("requires_human_approval"), bool):
            findings.append(f"creative_pipeline_profiles_invalid_profile_approval:{profile_name}")


def _validate_component_inspiration_profiles(root: Path, findings: List[str]) -> None:
    try:
        rules = _load_component_inspiration_profiles(root)
    except Exception as exc:
        findings.append(f"invalid_component_inspiration_profiles_json:{exc}")
        return

    if not isinstance(rules, dict):
        findings.append("component_inspiration_profiles_not_object")
        return

    services = rules.get("services")
    profiles = rules.get("profiles")
    if not isinstance(services, dict) or not services:
        findings.append("component_inspiration_profiles_invalid_services")
        return
    if not isinstance(profiles, dict) or not profiles:
        findings.append("component_inspiration_profiles_invalid_profiles")
        return

    missing_services = COMPONENT_INSPIRATION_REQUIRED_SERVICES - set(services.keys())
    if missing_services:
        findings.append(
            f"component_inspiration_profiles_missing_services:{','.join(sorted(missing_services))}"
        )
    missing_profiles = COMPONENT_INSPIRATION_REQUIRED_PROFILES - set(profiles.keys())
    if missing_profiles:
        findings.append(
            f"component_inspiration_profiles_missing_profiles:{','.join(sorted(missing_profiles))}"
        )

    for service_name, service in services.items():
        if not isinstance(service, dict):
            findings.append(f"component_inspiration_profiles_invalid_service:{service_name}")
            continue
        missing_fields = COMPONENT_INSPIRATION_SERVICE_REQUIRED_FIELDS - set(service.keys())
        if missing_fields:
            findings.append(
                "component_inspiration_profiles_missing_service_fields:"
                f"{service_name}:{','.join(sorted(missing_fields))}"
            )
        for field_name in ("expected_env_vars", "related_mcp_servers"):
            value = service.get(field_name)
            if not isinstance(value, list):
                findings.append(
                    f"component_inspiration_profiles_invalid_service_list:{service_name}:{field_name}"
                )
        if str(service.get("risk_level", "")).strip() not in VALID_SKILL_RISK_LEVELS:
            findings.append(f"component_inspiration_profiles_invalid_service_risk:{service_name}")

    for profile_name, profile in profiles.items():
        if not isinstance(profile, dict):
            findings.append(f"component_inspiration_profiles_invalid_profile:{profile_name}")
            continue
        missing_fields = COMPONENT_INSPIRATION_PROFILE_REQUIRED_FIELDS - set(profile.keys())
        if missing_fields:
            findings.append(
                "component_inspiration_profiles_missing_profile_fields:"
                f"{profile_name}:{','.join(sorted(missing_fields))}"
            )
        for field_name in ("suggested_services", "requirements", "expected_env_vars"):
            value = profile.get(field_name)
            if not isinstance(value, list):
                findings.append(
                    f"component_inspiration_profiles_invalid_profile_list:{profile_name}:{field_name}"
                )
        if str(profile.get("risk_level", "")).strip() not in VALID_SKILL_RISK_LEVELS:
            findings.append(f"component_inspiration_profiles_invalid_profile_risk:{profile_name}")
        if str(profile.get("initial_state", "")).strip() not in VALID_COMPONENT_INSPIRATION_STATES:
            findings.append(f"component_inspiration_profiles_invalid_profile_state:{profile_name}")
        if not isinstance(profile.get("requires_human_approval"), bool):
            findings.append(
                f"component_inspiration_profiles_invalid_profile_approval:{profile_name}"
            )
        if not str(profile.get("fallback", "")).strip():
            findings.append(f"component_inspiration_profiles_invalid_profile_fallback:{profile_name}")


def _validate_playwright_visual_qa_profiles(root: Path, findings: List[str]) -> None:
    try:
        rules = _load_playwright_visual_qa_profiles(root)
    except Exception as exc:
        findings.append(f"invalid_playwright_visual_qa_profiles_json:{exc}")
        return

    if not isinstance(rules, dict):
        findings.append("playwright_visual_qa_profiles_not_object")
        return

    profiles = rules.get("profiles")
    if not isinstance(profiles, dict) or not profiles:
        findings.append("playwright_visual_qa_profiles_invalid_profiles")
        return

    missing_profiles = PLAYWRIGHT_VISUAL_QA_REQUIRED_PROFILES - set(profiles.keys())
    if missing_profiles:
        findings.append(
            f"playwright_visual_qa_profiles_missing_profiles:{','.join(sorted(missing_profiles))}"
        )

    for profile_name, profile in profiles.items():
        if not isinstance(profile, dict):
            findings.append(f"playwright_visual_qa_profiles_invalid_profile:{profile_name}")
            continue
        missing_fields = PLAYWRIGHT_VISUAL_QA_PROFILE_REQUIRED_FIELDS - set(profile.keys())
        if missing_fields:
            findings.append(
                "playwright_visual_qa_profiles_missing_profile_fields:"
                f"{profile_name}:{','.join(sorted(missing_fields))}"
            )
        requirements = profile.get("requirements")
        if not isinstance(requirements, list):
            findings.append(
                f"playwright_visual_qa_profiles_invalid_profile_list:{profile_name}:requirements"
            )
        if str(profile.get("risk_level", "")).strip() not in VALID_SKILL_RISK_LEVELS:
            findings.append(f"playwright_visual_qa_profiles_invalid_profile_risk:{profile_name}")
        if str(profile.get("initial_state", "")).strip() not in VALID_PLAYWRIGHT_VISUAL_QA_STATES:
            findings.append(f"playwright_visual_qa_profiles_invalid_profile_state:{profile_name}")
        if not isinstance(profile.get("requires_human_approval"), bool):
            findings.append(
                f"playwright_visual_qa_profiles_invalid_profile_approval:{profile_name}"
            )
        if not str(profile.get("fallback", "")).strip():
            findings.append(f"playwright_visual_qa_profiles_invalid_profile_fallback:{profile_name}")


def _validate_brand_json_v2_readiness_rules(root: Path, findings: List[str]) -> None:
    try:
        rules = _load_brand_json_v2_readiness_rules(root)
    except Exception as exc:
        findings.append(f"invalid_brand_json_v2_readiness_rules_json:{exc}")
        return

    if not isinstance(rules, dict):
        findings.append("brand_json_v2_readiness_rules_not_object")
        return

    missing_fields = BRAND_JSON_V2_REQUIRED_FIELDS - set(rules.keys())
    if missing_fields:
        findings.append(f"brand_json_v2_readiness_rules_missing_fields:{','.join(sorted(missing_fields))}")

    for field_name in (
        "required_sections",
        "recommended_sections",
        "required_for_project_types",
        "backend_exempt_project_types",
        "mood_vector_dimensions",
        "minimum_evidence_expectations",
    ):
        value = rules.get(field_name)
        if not isinstance(value, list) or not value:
            findings.append(f"brand_json_v2_readiness_rules_invalid_list:{field_name}")

    required_sections = {str(item).strip() for item in rules.get("required_sections", []) if str(item).strip()}
    missing_sections = REQUIRED_BRAND_JSON_V2_SECTIONS - required_sections
    if missing_sections:
        findings.append(
            f"brand_json_v2_readiness_rules_missing_required_sections:{','.join(sorted(missing_sections))}"
        )

    mood_dimensions = {str(item).strip() for item in rules.get("mood_vector_dimensions", []) if str(item).strip()}
    missing_dimensions = REQUIRED_BRAND_MOOD_VECTOR_DIMENSIONS - mood_dimensions
    if missing_dimensions:
        findings.append(
            f"brand_json_v2_readiness_rules_missing_mood_vector_dimensions:{','.join(sorted(missing_dimensions))}"
        )

    if not isinstance(rules.get("advisory_only"), bool):
        findings.append("brand_json_v2_readiness_rules_invalid_advisory_only")
    if not isinstance(rules.get("explicit_profile_required_for_ready"), bool):
        findings.append("brand_json_v2_readiness_rules_invalid_explicit_profile_required_for_ready")


def _validate_frontend_auto_audit_rules(root: Path, findings: List[str]) -> None:
    try:
        rules = _load_frontend_auto_audit_rules(root)
    except Exception as exc:
        findings.append(f"invalid_frontend_auto_audit_rules_json:{exc}")
        return

    if not isinstance(rules, dict):
        findings.append("frontend_auto_audit_rules_not_object")
        return

    missing_fields = FRONTEND_AUTO_AUDIT_REQUIRED_FIELDS - set(rules.keys())
    if missing_fields:
        findings.append(f"frontend_auto_audit_rules_missing_fields:{','.join(sorted(missing_fields))}")

    for field_name in (
        "required_for_project_types",
        "backend_exempt_project_types",
        "required_inputs",
        "warning_codes",
        "watchlist_dependencies",
    ):
        value = rules.get(field_name)
        if not isinstance(value, list) or not value:
            findings.append(f"frontend_auto_audit_rules_invalid_list:{field_name}")

    required_inputs = {str(item).strip() for item in rules.get("required_inputs", []) if str(item).strip()}
    missing_inputs = REQUIRED_FRONTEND_AUTO_AUDIT_INPUTS - required_inputs
    if missing_inputs:
        findings.append(
            f"frontend_auto_audit_rules_missing_required_inputs:{','.join(sorted(missing_inputs))}"
        )

    checks = rules.get("checks")
    if not isinstance(checks, dict) or not checks:
        findings.append("frontend_auto_audit_rules_invalid_checks")
    else:
        missing_checks = REQUIRED_FRONTEND_AUTO_AUDIT_CHECKS - set(checks.keys())
        if missing_checks:
            findings.append(f"frontend_auto_audit_rules_missing_checks:{','.join(sorted(missing_checks))}")
        for check_id, rule in checks.items():
            if not isinstance(rule, dict):
                findings.append(f"frontend_auto_audit_rules_invalid_check:{check_id}")
                continue
            missing_rule_fields = {"severity", "signal", "why_it_matters", "recommended_fix", "blocks_ready_if_present"} - set(rule.keys())
            if missing_rule_fields:
                findings.append(
                    f"frontend_auto_audit_rules_missing_check_fields:{check_id}:{','.join(sorted(missing_rule_fields))}"
                )
            if str(rule.get("severity", "")).strip() not in VALID_SKILL_RISK_LEVELS:
                findings.append(f"frontend_auto_audit_rules_invalid_check_severity:{check_id}")
            if not isinstance(rule.get("blocks_ready_if_present"), bool):
                findings.append(f"frontend_auto_audit_rules_invalid_check_blocking:{check_id}")

    warning_codes = {str(item).strip() for item in rules.get("warning_codes", []) if str(item).strip()}
    missing_warning_codes = REQUIRED_FRONTEND_AUTO_AUDIT_WARNING_CODES - warning_codes
    if missing_warning_codes:
        findings.append(
            f"frontend_auto_audit_rules_missing_warning_codes:{','.join(sorted(missing_warning_codes))}"
        )

    if not isinstance(rules.get("advisory_only"), bool):
        findings.append("frontend_auto_audit_rules_invalid_advisory_only")


def _validate_design_quality_enforcement_rules(root: Path, findings: List[str]) -> None:
    try:
        rules = _load_design_quality_enforcement_rules(root)
    except Exception as exc:
        findings.append(f"invalid_design_quality_enforcement_rules_json:{exc}")
        return

    if not isinstance(rules, dict):
        findings.append("design_quality_enforcement_rules_not_object")
        return

    missing_fields = DESIGN_QUALITY_ENFORCEMENT_REQUIRED_FIELDS - set(rules.keys())
    if missing_fields:
        findings.append(f"design_quality_enforcement_rules_missing_fields:{','.join(sorted(missing_fields))}")

    for field_name in ("required_inputs", "required_for_project_types", "backend_exempt_project_types"):
        value = rules.get(field_name)
        if not isinstance(value, list) or not value:
            findings.append(f"design_quality_enforcement_rules_invalid_list:{field_name}")

    warning_codes = rules.get("warning_codes")
    if not isinstance(warning_codes, list) or not warning_codes:
        findings.append("design_quality_enforcement_rules_invalid_warning_codes")
    else:
        warning_set = {str(item).strip() for item in warning_codes if str(item).strip()}
        missing_warnings = REQUIRED_DESIGN_QUALITY_WARNING_CODES - warning_set
        unknown_warnings = warning_set - REQUIRED_DESIGN_QUALITY_WARNING_CODES
        if missing_warnings:
            findings.append(
                f"design_quality_enforcement_rules_missing_warning_codes:{','.join(sorted(missing_warnings))}"
            )
        if unknown_warnings:
            findings.append(
                f"design_quality_enforcement_rules_unknown_warning_codes:{','.join(sorted(unknown_warnings))}"
            )

    redesign_levels = rules.get("redesign_levels")
    if not isinstance(redesign_levels, list) or not redesign_levels:
        findings.append("design_quality_enforcement_rules_invalid_redesign_levels")
    else:
        redesign_set = {str(item).strip() for item in redesign_levels if str(item).strip()}
        missing_levels = VALID_DESIGN_QUALITY_REDESIGN_LEVELS - redesign_set
        unknown_levels = redesign_set - VALID_DESIGN_QUALITY_REDESIGN_LEVELS
        if missing_levels:
            findings.append(
                f"design_quality_enforcement_rules_missing_redesign_levels:{','.join(sorted(missing_levels))}"
            )
        if unknown_levels:
            findings.append(
                f"design_quality_enforcement_rules_unknown_redesign_levels:{','.join(sorted(unknown_levels))}"
            )

    checks = rules.get("checks")
    if not isinstance(checks, dict) or not checks:
        findings.append("design_quality_enforcement_rules_invalid_checks")
        return

    missing_checks = REQUIRED_DESIGN_QUALITY_CHECKS - set(checks.keys())
    if missing_checks:
        findings.append(
            f"design_quality_enforcement_rules_missing_checks:{','.join(sorted(missing_checks))}"
        )

    for check_name, rule in checks.items():
        if not isinstance(rule, dict):
            findings.append(f"design_quality_enforcement_rules_invalid_check:{check_name}")
            continue
        missing_rule_fields = DESIGN_QUALITY_RULE_REQUIRED_FIELDS - set(rule.keys())
        if missing_rule_fields:
            findings.append(
                "design_quality_enforcement_rules_missing_check_fields:"
                f"{check_name}:{','.join(sorted(missing_rule_fields))}"
            )
        if str(rule.get("severity", "")).strip() not in VALID_SKILL_RISK_LEVELS:
            findings.append(f"design_quality_enforcement_rules_invalid_check_severity:{check_name}")
        if not isinstance(rule.get("blocks_ready_if_present"), bool):
            findings.append(f"design_quality_enforcement_rules_invalid_check_blocker_flag:{check_name}")


def _validate_atlas_error_learning_rules(root: Path, findings: List[str]) -> None:
    try:
        rules = _load_atlas_error_learning_rules(root)
    except Exception as exc:
        findings.append(f"invalid_atlas_error_learning_rules_json:{exc}")
        return

    if not isinstance(rules, dict):
        findings.append("atlas_error_learning_rules_not_object")
        return

    missing_fields = ATLAS_ERROR_LEARNING_REQUIRED_FIELDS - set(rules.keys())
    if missing_fields:
        findings.append(f"atlas_error_learning_rules_missing_fields:{','.join(sorted(missing_fields))}")

    ui_project_types = rules.get("ui_project_types")
    if not isinstance(ui_project_types, list) or not ui_project_types:
        findings.append("atlas_error_learning_rules_invalid_ui_project_types")

    checks = rules.get("checks")
    if not isinstance(checks, dict) or not checks:
        findings.append("atlas_error_learning_rules_invalid_checks")
    else:
        missing_checks = ATLAS_ERROR_LEARNING_REQUIRED_CHECKS - set(checks.keys())
        if missing_checks:
            findings.append(f"atlas_error_learning_rules_missing_checks:{','.join(sorted(missing_checks))}")
        for check_name, check in checks.items():
            if not isinstance(check, dict):
                findings.append(f"atlas_error_learning_rules_invalid_check:{check_name}")
                continue
            missing_rule_fields = ATLAS_ERROR_LEARNING_REQUIRED_CHECK_FIELDS - set(check.keys())
            if missing_rule_fields:
                findings.append(
                    f"atlas_error_learning_rules_missing_check_fields:{check_name}:{','.join(sorted(missing_rule_fields))}"
                )
            if str(check.get("severity", "")).strip() not in VALID_SKILL_RISK_LEVELS:
                findings.append(f"atlas_error_learning_rules_invalid_check_severity:{check_name}")
            if not isinstance(check.get("blocks_ready_if_present"), bool):
                findings.append(f"atlas_error_learning_rules_invalid_check_blocking:{check_name}")

    warning_codes = rules.get("warning_codes")
    if not isinstance(warning_codes, list) or not warning_codes:
        findings.append("atlas_error_learning_rules_invalid_warning_codes")
    else:
        warning_set = {str(item).strip() for item in warning_codes if str(item).strip()}
        missing_warning_codes = ATLAS_ERROR_LEARNING_REQUIRED_WARNING_CODES - warning_set
        if missing_warning_codes:
            findings.append(
                f"atlas_error_learning_rules_missing_warning_codes:{','.join(sorted(missing_warning_codes))}"
            )


def _validate_codex_runtime_compatibility_rules(root: Path, findings: List[str]) -> None:
    try:
        rules = _load_codex_runtime_compatibility_rules(root)
    except Exception as exc:
        findings.append(f"invalid_codex_runtime_compatibility_rules_json:{exc}")
        return

    if not isinstance(rules, dict):
        findings.append("codex_runtime_compatibility_rules_not_object")
        return

    missing_fields = CODEX_RUNTIME_COMPATIBILITY_REQUIRED_FIELDS - set(rules.keys())
    if missing_fields:
        findings.append(
            f"codex_runtime_compatibility_rules_missing_fields:{','.join(sorted(missing_fields))}"
        )

    required_checks = rules.get("required_checks")
    if not isinstance(required_checks, list) or not required_checks:
        findings.append("codex_runtime_compatibility_rules_invalid_required_checks")
    else:
        check_set = {str(item).strip() for item in required_checks if str(item).strip()}
        missing_checks = CODEX_RUNTIME_COMPATIBILITY_REQUIRED_CHECKS - check_set
        if missing_checks:
            findings.append(
                f"codex_runtime_compatibility_rules_missing_required_checks:{','.join(sorted(missing_checks))}"
            )

    limitations = rules.get("known_limitations")
    if not isinstance(limitations, list) or not limitations:
        findings.append("codex_runtime_compatibility_rules_invalid_known_limitations")
    else:
        limitation_set = {str(item).strip() for item in limitations if str(item).strip()}
        missing_limitations = CODEX_RUNTIME_COMPATIBILITY_REQUIRED_LIMITATIONS - limitation_set
        if missing_limitations:
            findings.append(
                f"codex_runtime_compatibility_rules_missing_known_limitations:{','.join(sorted(missing_limitations))}"
            )

    manual_steps = rules.get("manual_step_templates")
    if not isinstance(manual_steps, list) or not manual_steps:
        findings.append("codex_runtime_compatibility_rules_invalid_manual_steps")


def _validate_evidence_collector_readiness_rules(root: Path, findings: List[str]) -> None:
    try:
        rules = _load_evidence_collector_readiness_rules(root)
    except Exception as exc:
        findings.append(f"invalid_evidence_collector_readiness_rules_json:{exc}")
        return

    if not isinstance(rules, dict):
        findings.append("evidence_collector_readiness_rules_not_object")
        return

    missing_fields = EVIDENCE_COLLECTOR_READINESS_REQUIRED_FIELDS - set(rules.keys())
    if missing_fields:
        findings.append(
            f"evidence_collector_readiness_rules_missing_fields:{','.join(sorted(missing_fields))}"
        )

    task_types = rules.get("task_types")
    if not isinstance(task_types, dict) or not task_types:
        findings.append("evidence_collector_readiness_rules_invalid_task_types")
    else:
        missing_task_types = EVIDENCE_COLLECTOR_REQUIRED_TASK_TYPES - set(task_types.keys())
        if missing_task_types:
            findings.append(
                f"evidence_collector_readiness_rules_missing_task_types:{','.join(sorted(missing_task_types))}"
            )
        for task_type, task_rules in task_types.items():
            if not isinstance(task_rules, dict):
                findings.append(f"evidence_collector_readiness_rules_invalid_task:{task_type}")
                continue
            missing_task_fields = EVIDENCE_COLLECTOR_REQUIRED_TASK_FIELDS - set(task_rules.keys())
            if missing_task_fields:
                findings.append(
                    f"evidence_collector_readiness_rules_missing_task_fields:{task_type}:{','.join(sorted(missing_task_fields))}"
                )
            for field_name in EVIDENCE_COLLECTOR_REQUIRED_TASK_FIELDS:
                value = task_rules.get(field_name)
                if not isinstance(value, list):
                    findings.append(
                        f"evidence_collector_readiness_rules_invalid_task_list:{task_type}:{field_name}"
                    )

    project_type_map = rules.get("project_type_map")
    if not isinstance(project_type_map, dict) or not project_type_map:
        findings.append("evidence_collector_readiness_rules_invalid_project_type_map")

    warning_codes = rules.get("warning_codes")
    if not isinstance(warning_codes, list) or not warning_codes:
        findings.append("evidence_collector_readiness_rules_invalid_warning_codes")
    else:
        warning_set = {str(item).strip() for item in warning_codes if str(item).strip()}
        missing_warning_codes = EVIDENCE_COLLECTOR_REQUIRED_WARNING_CODES - warning_set
        if missing_warning_codes:
            findings.append(
                f"evidence_collector_readiness_rules_missing_warning_codes:{','.join(sorted(missing_warning_codes))}"
            )


def _validate_change_proposal_rules(root: Path, findings: List[str]) -> None:
    try:
        rules = _load_change_proposal_rules(root)
    except Exception as exc:
        findings.append(f"invalid_change_proposal_rules_json:{exc}")
        return

    if not isinstance(rules, dict):
        findings.append("change_proposal_rules_not_object")
        return

    missing_fields = CHANGE_PROPOSAL_REQUIRED_FIELDS - set(rules.keys())
    if missing_fields:
        findings.append(
            f"change_proposal_rules_missing_fields:{','.join(sorted(missing_fields))}"
        )

    required_when = rules.get("required_when")
    if not isinstance(required_when, dict) or not required_when:
        findings.append("change_proposal_rules_invalid_required_when")

    required_artifacts = rules.get("required_artifacts")
    if not isinstance(required_artifacts, list) or not required_artifacts:
        findings.append("change_proposal_rules_invalid_required_artifacts")
    else:
        artifact_set = {str(item).strip() for item in required_artifacts if str(item).strip()}
        missing_artifacts = CHANGE_PROPOSAL_REQUIRED_ARTIFACTS - artifact_set
        if missing_artifacts:
            findings.append(
                f"change_proposal_rules_missing_required_artifacts:{','.join(sorted(missing_artifacts))}"
            )

    artifact_requirements = rules.get("artifact_requirements")
    if not isinstance(artifact_requirements, dict) or not artifact_requirements:
        findings.append("change_proposal_rules_invalid_artifact_requirements")
    else:
        missing_requirement_artifacts = CHANGE_PROPOSAL_REQUIRED_ARTIFACTS - set(artifact_requirements.keys())
        if missing_requirement_artifacts:
            findings.append(
                f"change_proposal_rules_missing_artifact_requirements:{','.join(sorted(missing_requirement_artifacts))}"
            )
        for artifact_name, artifact_rules in artifact_requirements.items():
            if not isinstance(artifact_rules, dict):
                findings.append(f"change_proposal_rules_invalid_artifact:{artifact_name}")
                continue
            missing_artifact_fields = CHANGE_PROPOSAL_REQUIRED_ARTIFACT_FIELDS - set(artifact_rules.keys())
            if missing_artifact_fields:
                findings.append(
                    f"change_proposal_rules_missing_artifact_fields:{artifact_name}:{','.join(sorted(missing_artifact_fields))}"
                )
            required_fields = artifact_rules.get("required_fields")
            if not isinstance(required_fields, list) or not required_fields:
                findings.append(
                    f"change_proposal_rules_invalid_artifact_required_fields:{artifact_name}"
                )


def _validate_skill_registry_index_first_rules(root: Path, findings: List[str]) -> None:
    try:
        rules = _load_skill_registry_index_first_rules(root)
    except Exception as exc:
        findings.append(f"invalid_skill_registry_index_first_rules_json:{exc}")
        return

    if not isinstance(rules, dict):
        findings.append("skill_registry_index_first_rules_not_object")
        return

    missing_fields = SKILL_REGISTRY_INDEX_FIRST_REQUIRED_FIELDS - set(rules.keys())
    if missing_fields:
        findings.append(
            f"skill_registry_index_first_rules_missing_fields:{','.join(sorted(missing_fields))}"
        )

    accepted_doc_names = rules.get("accepted_skill_doc_names")
    if not isinstance(accepted_doc_names, list) or not accepted_doc_names:
        findings.append("skill_registry_index_first_rules_invalid_accepted_skill_doc_names")

    registry_fields = rules.get("required_registry_fields")
    if not isinstance(registry_fields, list) or not registry_fields:
        findings.append("skill_registry_index_first_rules_invalid_required_registry_fields")
    else:
        registry_field_set = {str(item).strip() for item in registry_fields if str(item).strip()}
        missing_registry_fields = SKILL_REGISTRY_INDEX_FIRST_REQUIRED_REGISTRY_FIELDS - registry_field_set
        if missing_registry_fields:
            findings.append(
                f"skill_registry_index_first_rules_missing_required_registry_fields:{','.join(sorted(missing_registry_fields))}"
            )

    companion_files = rules.get("required_companion_files")
    if not isinstance(companion_files, list) or not companion_files:
        findings.append("skill_registry_index_first_rules_invalid_required_companion_files")
    else:
        companion_set = {str(item).strip() for item in companion_files if str(item).strip()}
        missing_companion = SKILL_REGISTRY_INDEX_FIRST_REQUIRED_COMPANION_FILES - companion_set
        if missing_companion:
            findings.append(
                f"skill_registry_index_first_rules_missing_required_companion_files:{','.join(sorted(missing_companion))}"
            )

    description_rules = rules.get("description_rules")
    if not isinstance(description_rules, dict) or not description_rules:
        findings.append("skill_registry_index_first_rules_invalid_description_rules")
    else:
        if "minimum_words" not in description_rules:
            findings.append("skill_registry_index_first_rules_missing_minimum_words")

    valid_lifecycle_states = rules.get("valid_lifecycle_states")
    if not isinstance(valid_lifecycle_states, list) or not valid_lifecycle_states:
        findings.append("skill_registry_index_first_rules_invalid_valid_lifecycle_states")


def _validate_ui_ux_design_system_rules(root: Path, findings: List[str]) -> None:
    try:
        rules = _load_ui_ux_design_system_rules(root)
    except Exception as exc:
        findings.append(f"invalid_ui_ux_design_system_rules_json:{exc}")
        return

    if not isinstance(rules, dict):
        findings.append("ui_ux_design_system_rules_not_object")
        return

    missing_fields = UI_UX_DESIGN_SYSTEM_REQUIRED_FIELDS - set(rules.keys())
    if missing_fields:
        findings.append(
            f"ui_ux_design_system_rules_missing_fields:{','.join(sorted(missing_fields))}"
        )

    required_inputs = rules.get("required_inputs")
    if not isinstance(required_inputs, list) or not required_inputs:
        findings.append("ui_ux_design_system_rules_invalid_required_inputs")

    frontend_project_types = rules.get("frontend_project_types")
    if not isinstance(frontend_project_types, list) or not frontend_project_types:
        findings.append("ui_ux_design_system_rules_invalid_frontend_project_types")

    product_profiles = rules.get("product_profiles")
    if not isinstance(product_profiles, list) or not product_profiles:
        findings.append("ui_ux_design_system_rules_invalid_product_profiles")
    else:
        for profile in product_profiles:
            if not isinstance(profile, dict):
                findings.append("ui_ux_design_system_rules_invalid_product_profile")
                continue
            missing_profile_fields = UI_UX_DESIGN_SYSTEM_REQUIRED_PRODUCT_FIELDS - set(profile.keys())
            if missing_profile_fields:
                findings.append(
                    "ui_ux_design_system_rules_missing_product_profile_fields:"
                    f"{profile.get('id', 'unknown')}:{','.join(sorted(missing_profile_fields))}"
                )

    audience_modifiers = rules.get("audience_modifiers")
    if not isinstance(audience_modifiers, dict) or not audience_modifiers:
        findings.append("ui_ux_design_system_rules_invalid_audience_modifiers")

    motion_library_posture = rules.get("motion_library_posture")
    if not isinstance(motion_library_posture, dict) or not motion_library_posture:
        findings.append("ui_ux_design_system_rules_invalid_motion_library_posture")
    else:
        missing_motion_fields = UI_UX_DESIGN_SYSTEM_REQUIRED_MOTION_FIELDS - set(motion_library_posture.keys())
        if missing_motion_fields:
            findings.append(
                f"ui_ux_design_system_rules_missing_motion_library_fields:{','.join(sorted(missing_motion_fields))}"
            )

    component_library_posture = rules.get("component_library_posture")
    if not isinstance(component_library_posture, dict) or not component_library_posture:
        findings.append("ui_ux_design_system_rules_invalid_component_library_posture")
    else:
        missing_component_library_fields = UI_UX_DESIGN_SYSTEM_REQUIRED_COMPONENT_LIBRARY_FIELDS - set(
            component_library_posture.keys()
        )
        if missing_component_library_fields:
            findings.append(
                "ui_ux_design_system_rules_missing_component_library_fields:"
                f"{','.join(sorted(missing_component_library_fields))}"
            )

    pre_delivery_checklist = rules.get("pre_delivery_checklist")
    if not isinstance(pre_delivery_checklist, list) or not pre_delivery_checklist:
        findings.append("ui_ux_design_system_rules_invalid_pre_delivery_checklist")

    accessibility_baseline = rules.get("accessibility_baseline")
    if not isinstance(accessibility_baseline, list) or not accessibility_baseline:
        findings.append("ui_ux_design_system_rules_invalid_accessibility_baseline")


def _validate_repo_graph_readiness_rules(root: Path, findings: List[str]) -> None:
    try:
        rules = _load_repo_graph_readiness_rules(root)
    except Exception as exc:
        findings.append(f"invalid_repo_graph_readiness_rules_json:{exc}")
        return

    if not isinstance(rules, dict):
        findings.append("repo_graph_readiness_rules_not_object")
        return

    missing_fields = REPO_GRAPH_READINESS_REQUIRED_FIELDS - set(rules.keys())
    if missing_fields:
        findings.append(f"repo_graph_readiness_rules_missing_fields:{','.join(sorted(missing_fields))}")

    size_thresholds = rules.get("size_thresholds")
    if not isinstance(size_thresholds, dict) or not size_thresholds:
        findings.append("repo_graph_readiness_rules_invalid_size_thresholds")
    else:
        for field_name in ("small_max_files", "medium_max_files"):
            if field_name not in size_thresholds:
                findings.append(f"repo_graph_readiness_rules_missing_size_threshold:{field_name}")

    source_extensions = rules.get("source_extensions")
    if not isinstance(source_extensions, dict) or not source_extensions:
        findings.append("repo_graph_readiness_rules_invalid_source_extensions")

    route_detection = rules.get("route_detection")
    if not isinstance(route_detection, dict) or not route_detection:
        findings.append("repo_graph_readiness_rules_invalid_route_detection")
    else:
        missing_route_fields = REPO_GRAPH_READINESS_REQUIRED_ROUTE_FIELDS - set(route_detection.keys())
        if missing_route_fields:
            findings.append(
                f"repo_graph_readiness_rules_missing_route_detection_fields:{','.join(sorted(missing_route_fields))}"
            )

    for field_name in ("multi_module_markers", "blocked_task_types", "watchlist_terms"):
        value = rules.get(field_name)
        if not isinstance(value, list) or not value:
            findings.append(f"repo_graph_readiness_rules_invalid_{field_name}")

    task_fit_signals = rules.get("task_fit_signals")
    if not isinstance(task_fit_signals, dict) or not task_fit_signals:
        findings.append("repo_graph_readiness_rules_invalid_task_fit_signals")
    else:
        for field_name in ("high", "medium", "low"):
            value = task_fit_signals.get(field_name)
            if not isinstance(value, list) or not value:
                findings.append(f"repo_graph_readiness_rules_invalid_task_fit_band:{field_name}")

    manual_steps = rules.get("manual_steps")
    if not isinstance(manual_steps, dict) or not manual_steps:
        findings.append("repo_graph_readiness_rules_invalid_manual_steps")
    else:
        missing_manual_fields = REPO_GRAPH_READINESS_REQUIRED_MANUAL_STEP_FIELDS - set(manual_steps.keys())
        if missing_manual_fields:
            findings.append(
                f"repo_graph_readiness_rules_missing_manual_step_fields:{','.join(sorted(missing_manual_fields))}"
            )
        for field_name in REPO_GRAPH_READINESS_REQUIRED_MANUAL_STEP_FIELDS:
            if field_name in manual_steps:
                value = manual_steps.get(field_name)
                if not isinstance(value, list) or not value:
                    findings.append(f"repo_graph_readiness_rules_invalid_manual_step_list:{field_name}")


def _validate_business_idea_simulation_rules(root: Path, findings: List[str]) -> None:
    try:
        rules = _load_business_idea_simulation_rules(root)
    except Exception as exc:
        findings.append(f"invalid_business_idea_simulation_rules_json:{exc}")
        return

    if not isinstance(rules, dict):
        findings.append("business_idea_simulation_rules_not_object")
        return

    missing_fields = BUSINESS_IDEA_SIMULATION_REQUIRED_FIELDS - set(rules.keys())
    if missing_fields:
        findings.append(f"business_idea_simulation_rules_missing_fields:{','.join(sorted(missing_fields))}")

    required_inputs = rules.get("required_inputs")
    if not isinstance(required_inputs, list) or not required_inputs:
        findings.append("business_idea_simulation_rules_invalid_required_inputs")
    else:
        required_input_set = {str(item).strip() for item in required_inputs if str(item).strip()}
        missing_required_inputs = BUSINESS_IDEA_SIMULATION_REQUIRED_INPUTS - required_input_set
        if missing_required_inputs:
            findings.append(
                f"business_idea_simulation_rules_missing_required_inputs:{','.join(sorted(missing_required_inputs))}"
            )

    input_aliases = rules.get("input_aliases")
    if not isinstance(input_aliases, dict) or not input_aliases:
        findings.append("business_idea_simulation_rules_invalid_input_aliases")

    for field_name in (
        "core_inputs",
        "scenario_ready_inputs",
        "profitability_inputs",
        "blocked_prediction_terms",
        "research_required_inputs",
    ):
        value = rules.get(field_name)
        if not isinstance(value, list) or not value:
            findings.append(f"business_idea_simulation_rules_invalid_{field_name}")

    risk_categories = rules.get("risk_categories")
    if not isinstance(risk_categories, list) or not risk_categories:
        findings.append("business_idea_simulation_rules_invalid_risk_categories")
    else:
        risk_category_set = {str(item).strip() for item in risk_categories if str(item).strip()}
        missing_risk_categories = BUSINESS_IDEA_SIMULATION_REQUIRED_RISK_CATEGORIES - risk_category_set
        if missing_risk_categories:
            findings.append(
                f"business_idea_simulation_rules_missing_risk_categories:{','.join(sorted(missing_risk_categories))}"
            )

    risk_signals = rules.get("risk_signals")
    if not isinstance(risk_signals, dict) or not risk_signals:
        findings.append("business_idea_simulation_rules_invalid_risk_signals")

    signal_thresholds = rules.get("signal_thresholds")
    if not isinstance(signal_thresholds, dict) or not signal_thresholds:
        findings.append("business_idea_simulation_rules_invalid_signal_thresholds")
    else:
        missing_thresholds = BUSINESS_IDEA_SIMULATION_REQUIRED_THRESHOLDS - set(signal_thresholds.keys())
        if missing_thresholds:
            findings.append(
                f"business_idea_simulation_rules_missing_signal_thresholds:{','.join(sorted(missing_thresholds))}"
            )

    experiment_catalog = rules.get("experiment_catalog")
    if not isinstance(experiment_catalog, list) or not experiment_catalog:
        findings.append("business_idea_simulation_rules_invalid_experiment_catalog")
    else:
        for idx, experiment in enumerate(experiment_catalog, start=1):
            if not isinstance(experiment, dict):
                findings.append(f"business_idea_simulation_rules_invalid_experiment:{idx}")
                continue
            missing_experiment_fields = BUSINESS_IDEA_SIMULATION_REQUIRED_EXPERIMENT_FIELDS - set(experiment.keys())
            if missing_experiment_fields:
                findings.append(
                    "business_idea_simulation_rules_missing_experiment_fields:"
                    f"{idx}:{','.join(sorted(missing_experiment_fields))}"
                )


def _validate_chrome_devtools_mcp_rules(root: Path, findings: List[str]) -> None:
    try:
        rules = _load_chrome_devtools_mcp_rules(root)
    except Exception as exc:
        findings.append(f"invalid_chrome_devtools_mcp_rules_json:{exc}")
        return

    if not isinstance(rules, dict):
        findings.append("chrome_devtools_mcp_rules_not_object")
        return

    missing_fields = CHROME_DEVTOOLS_MCP_RULES_REQUIRED_FIELDS - set(rules.keys())
    if missing_fields:
        findings.append(f"chrome_devtools_mcp_rules_missing_fields:{','.join(sorted(missing_fields))}")

    for field_name in (
        "frontend_project_types",
        "layout_debug_signals",
        "console_debug_signals",
        "network_debug_signals",
        "performance_debug_signals",
        "drift_trigger_states",
        "screenshot_gap_signals",
        "configured_server_aliases",
        "best_for",
        "recommended_flags",
        "manual_setup_steps",
    ):
        value = rules.get(field_name)
        if not isinstance(value, list) or not value:
            findings.append(f"chrome_devtools_mcp_rules_invalid_{field_name}")

    best_for = {str(item).strip() for item in rules.get("best_for", []) if str(item).strip()}
    missing_best_for = REQUIRED_CHROME_DEVTOOLS_MCP_BEST_FOR - best_for
    if missing_best_for:
        findings.append(
            f"chrome_devtools_mcp_rules_missing_best_for:{','.join(sorted(missing_best_for))}"
        )

    recommended_flags = {str(item).strip() for item in rules.get("recommended_flags", []) if str(item).strip()}
    if "--no-usage-statistics" not in recommended_flags:
        findings.append("chrome_devtools_mcp_rules_missing_no_usage_statistics_flag")

    risks = rules.get("risks")
    if not isinstance(risks, dict) or not risks:
        findings.append("chrome_devtools_mcp_rules_invalid_risks")
    else:
        for field_name in ("telemetry_risk", "browser_profile_risk", "privacy_risk"):
            value = str(risks.get(field_name, "")).strip()
            if value not in {"low", "medium", "high"}:
                findings.append(f"chrome_devtools_mcp_rules_invalid_risk:{field_name}")

    thresholds = rules.get("recommendation_thresholds")
    if not isinstance(thresholds, dict) or not thresholds:
        findings.append("chrome_devtools_mcp_rules_invalid_recommendation_thresholds")
    else:
        minimum_symptom_count = thresholds.get("minimum_symptom_count")
        if not isinstance(minimum_symptom_count, int) or minimum_symptom_count < 1:
            findings.append("chrome_devtools_mcp_rules_invalid_minimum_symptom_count")


def _validate_copywriting_conversion_rules(root: Path, findings: List[str]) -> None:
    try:
        rules = _load_copywriting_conversion_rules(root)
    except Exception as exc:
        findings.append(f"invalid_copywriting_conversion_rules_json:{exc}")
        return

    if not isinstance(rules, dict):
        findings.append("copywriting_conversion_rules_not_object")
        return

    missing_fields = COPYWRITING_CONVERSION_REQUIRED_FIELDS - set(rules.keys())
    if missing_fields:
        findings.append(f"copywriting_conversion_rules_missing_fields:{','.join(sorted(missing_fields))}")

    for field_name in (
        "applicable_project_types",
        "project_scan_files",
        "blocked_claim_terms",
        "instant_diagnosis_terms",
        "generic_ai_phrases",
        "aggressive_sales_phrases",
        "strong_cta_terms",
        "weak_cta_terms",
        "audience_keywords",
        "problem_keywords",
        "value_keywords",
        "form_follow_up_terms",
        "consent_terms",
        "trust_terms",
    ):
        value = rules.get(field_name)
        if not isinstance(value, list) or not value:
            findings.append(f"copywriting_conversion_rules_invalid_{field_name}")

    input_aliases = rules.get("input_aliases")
    if not isinstance(input_aliases, dict) or not input_aliases:
        findings.append("copywriting_conversion_rules_invalid_input_aliases")

    thresholds = rules.get("ready_thresholds")
    if not isinstance(thresholds, dict) or not thresholds:
        findings.append("copywriting_conversion_rules_invalid_ready_thresholds")
    else:
        missing_thresholds = COPYWRITING_CONVERSION_REQUIRED_THRESHOLDS - set(thresholds.keys())
        if missing_thresholds:
            findings.append(
                f"copywriting_conversion_rules_missing_ready_thresholds:{','.join(sorted(missing_thresholds))}"
            )
        for field_name in COPYWRITING_CONVERSION_REQUIRED_THRESHOLDS:
            if field_name not in thresholds:
                continue
            value = thresholds.get(field_name)
            if not isinstance(value, int) or value < 0 or value > 100:
                findings.append(f"copywriting_conversion_rules_invalid_threshold:{field_name}")


def _validate_brand_strategy_rules(root: Path, findings: List[str]) -> None:
    try:
        rules = _load_brand_strategy_rules(root)
    except Exception as exc:
        findings.append(f"invalid_brand_strategy_rules_json:{exc}")
        return

    if not isinstance(rules, dict):
        findings.append("brand_strategy_rules_not_object")
        return

    missing_fields = BRAND_STRATEGY_REQUIRED_FIELDS - set(rules.keys())
    if missing_fields:
        findings.append(f"brand_strategy_rules_missing_fields:{','.join(sorted(missing_fields))}")

    for field_name in (
        "applicable_project_types",
        "generic_category_terms",
        "generic_palette_terms",
        "generic_brand_phrases",
        "template_risk_signals",
        "inconsistent_tone_signals",
        "claims_without_evidence_terms",
        "audience_mismatch_signals",
        "required_color_roles",
        "required_typography_fields",
    ):
        value = rules.get(field_name)
        if not isinstance(value, list) or not value:
            findings.append(f"brand_strategy_rules_invalid_{field_name}")

    input_aliases = rules.get("input_aliases")
    if not isinstance(input_aliases, dict) or not input_aliases:
        findings.append("brand_strategy_rules_invalid_input_aliases")

    thresholds = rules.get("ready_thresholds")
    if not isinstance(thresholds, dict) or not thresholds:
        findings.append("brand_strategy_rules_invalid_ready_thresholds")
    else:
        missing_thresholds = BRAND_STRATEGY_REQUIRED_THRESHOLDS - set(thresholds.keys())
        if missing_thresholds:
            findings.append(
                f"brand_strategy_rules_missing_ready_thresholds:{','.join(sorted(missing_thresholds))}"
            )
        for field_name in BRAND_STRATEGY_REQUIRED_THRESHOLDS:
            if field_name not in thresholds:
                continue
            value = thresholds.get(field_name)
            if not isinstance(value, int) or value < 0 or value > 100:
                findings.append(f"brand_strategy_rules_invalid_threshold:{field_name}")


def _validate_n8n_automation_readiness_rules(root: Path, findings: List[str]) -> None:
    try:
        rules = _load_n8n_automation_readiness_rules(root)
    except Exception as exc:
        findings.append(f"invalid_n8n_automation_readiness_rules_json:{exc}")
        return

    if not isinstance(rules, dict):
        findings.append("n8n_automation_readiness_rules_not_object")
        return

    required_fields = {
        "version",
        "advisory_only",
        "applicable_project_types",
        "input_aliases",
        "node_type_signals",
        "sensitive_data_signals",
        "risk_triggers",
        "required_safety_fields",
        "allow_advisory_without_side_effects",
    }
    missing_fields = required_fields - set(rules.keys())
    if missing_fields:
        findings.append(f"n8n_automation_readiness_rules_missing_fields:{','.join(sorted(missing_fields))}")

    if not isinstance(rules.get("input_aliases"), dict):
        findings.append("n8n_automation_readiness_rules_invalid_input_aliases")

    node_type_signals = rules.get("node_type_signals")
    if not isinstance(node_type_signals, dict):
        findings.append("n8n_automation_readiness_rules_invalid_node_type_signals")
    else:
        required_node_types = {"send_email", "sheets_write", "db_write", "webhook", "scraping", "llm"}
        missing_node_types = required_node_types - set(node_type_signals.keys())
        if missing_node_types:
            findings.append(
                f"n8n_automation_readiness_rules_missing_node_type_signals:{','.join(sorted(missing_node_types))}"
            )

    for field_name in ("applicable_project_types", "sensitive_data_signals", "required_safety_fields"):
        value = rules.get(field_name)
        if not isinstance(value, list) or not all(str(item).strip() for item in value):
            findings.append(f"n8n_automation_readiness_rules_invalid_{field_name}")

    risk_triggers = rules.get("risk_triggers")
    if not isinstance(risk_triggers, dict):
        findings.append("n8n_automation_readiness_rules_invalid_risk_triggers")
    else:
        for bucket in ("high", "medium"):
            value = risk_triggers.get(bucket)
            if not isinstance(value, list) or not all(str(item).strip() for item in value):
                findings.append(f"n8n_automation_readiness_rules_invalid_risk_triggers_{bucket}")


def _validate_visual_fidelity_judge_rules(root: Path, findings: List[str]) -> None:
    try:
        rules = _load_visual_fidelity_judge_rules(root)
    except Exception as exc:
        findings.append(f"invalid_visual_fidelity_judge_rules_json:{exc}")
        return

    if not isinstance(rules, dict):
        findings.append("visual_fidelity_judge_rules_not_object")
        return

    missing_fields = VISUAL_FIDELITY_JUDGE_REQUIRED_FIELDS - set(rules.keys())
    if missing_fields:
        findings.append(f"visual_fidelity_judge_rules_missing_fields:{','.join(sorted(missing_fields))}")

    for field_name in (
        "frontend_project_types",
        "candidate_report_paths",
        "candidate_screenshot_dirs",
        "required_viewports",
        "core_compared_layers",
        "supporting_compared_layers",
        "warning_codes",
    ):
        value = rules.get(field_name)
        if not isinstance(value, list) or not value:
            findings.append(f"visual_fidelity_judge_rules_invalid_{field_name}")

    required_viewports = {
        str(item).strip()
        for item in rules.get("required_viewports", [])
        if str(item).strip()
    }
    missing_viewports = VISUAL_FIDELITY_JUDGE_REQUIRED_VIEWPORTS - required_viewports
    if missing_viewports:
        findings.append(
            f"visual_fidelity_judge_rules_missing_required_viewports:{','.join(sorted(missing_viewports))}"
        )

    core_layers = {
        str(item).strip()
        for item in rules.get("core_compared_layers", [])
        if str(item).strip()
    }
    missing_core_layers = VISUAL_FIDELITY_JUDGE_REQUIRED_CORE_LAYERS - core_layers
    if missing_core_layers:
        findings.append(
            f"visual_fidelity_judge_rules_missing_core_layers:{','.join(sorted(missing_core_layers))}"
        )

    viewport_filename_tokens = rules.get("viewport_filename_tokens")
    if not isinstance(viewport_filename_tokens, dict) or not viewport_filename_tokens:
        findings.append("visual_fidelity_judge_rules_invalid_viewport_filename_tokens")
    else:
        for viewport in VISUAL_FIDELITY_JUDGE_REQUIRED_VIEWPORTS:
            value = viewport_filename_tokens.get(viewport)
            if not isinstance(value, list) or not value:
                findings.append(f"visual_fidelity_judge_rules_missing_viewport_tokens:{viewport}")

    minimum_signal_count = rules.get("minimum_signal_count")
    if not isinstance(minimum_signal_count, int) or minimum_signal_count < 1:
        findings.append("visual_fidelity_judge_rules_invalid_minimum_signal_count")


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

    lifecycle_state = metadata.get("lifecycle_state")
    if lifecycle_state is not None:
        lifecycle_state_value = str(lifecycle_state).strip()
        if lifecycle_state_value not in REQUIRED_SKILL_LIFECYCLE_STATES:
            findings.append(f"skill_{skill_name}:unknown_lifecycle_state:{lifecycle_state_value or 'empty'}")


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


def _validate_global_project_templates(root: Path, findings: List[str]) -> None:
    sample_values = _sample_bootstrap_template_values("frontend_app")
    template_specs = (
        ("templates/project/AGENTS.md.template", "AGENTS"),
        ("templates/project/.atlas-project.json.template", "PROJECT_METADATA"),
        ("templates/project/SPRINT_STATUS.md.template", "SPRINT_STATUS"),
    )

    for relative_path, template_label in template_specs:
        template_path = root / relative_path
        if not template_path.exists():
            findings.append(f"atlas_project_bootstrap:missing_template_file:{relative_path}")
            continue

        template_text = _read_text(template_path)
        placeholders = _extract_template_placeholders(template_text)
        for raw_placeholder, placeholder_name in placeholders:
            if placeholder_name not in ALLOWED_BOOTSTRAP_TEMPLATE_PLACEHOLDERS:
                findings.append(
                    "atlas_project_bootstrap:"
                    "invalid_template_placeholder:"
                    "profile=global_project_governance:"
                    f"template={template_label}:file={relative_path}:"
                    f"placeholder={raw_placeholder}:"
                    "recommendation=replace_with_whitelisted_placeholder_or_static_text"
                )

        rendered = _render_template_with_sample_values(template_text, sample_values)
        unresolved = _extract_template_placeholders(rendered)
        for raw_placeholder, _placeholder_name in unresolved:
            findings.append(
                "atlas_project_bootstrap:"
                "unresolved_template_placeholder:"
                "profile=global_project_governance:"
                f"template={template_label}:file={relative_path}:"
                f"placeholder={raw_placeholder}:"
                "recommendation=ensure_the_placeholder_is_whitelisted_and_rendered_or_convert_it_to_static_text"
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
        _validate_model_cost_control_profiles(root, findings)
        _validate_mcp_profiles(root, findings)
        _validate_external_tool_policy(root, findings)
        _validate_skill_lifecycle_rules(root, findings)
        _validate_skill_improvement_review_rules(root, findings)
        _validate_market_research_benchmark_rules(root, findings)
        _validate_intent_clarifier_contract_rules(root, findings)
        _validate_visual_intent_contract(root, findings)
        _validate_brand_json_v2_readiness_rules(root, findings)
        _validate_brand_profile_schema(root, findings)
        _validate_frontend_auto_audit_rules(root, findings)
        _validate_ui_pre_return_audit_rules(root, findings)
        _validate_creative_pipeline_profiles(root, findings)
        _validate_component_inspiration_profiles(root, findings)
        _validate_playwright_visual_qa_profiles(root, findings)
        _validate_design_quality_enforcement_rules(root, findings)
        _validate_atlas_error_learning_rules(root, findings)
        _validate_codex_runtime_compatibility_rules(root, findings)
        _validate_atlas_memory_readiness_profiles(root, findings)
        _validate_evidence_collector_readiness_rules(root, findings)
        _validate_change_proposal_rules(root, findings)
        _validate_skill_registry_index_first_rules(root, findings)
        _validate_ui_ux_design_system_rules(root, findings)
        _validate_repo_graph_readiness_rules(root, findings)
        _validate_business_idea_simulation_rules(root, findings)
        _validate_visual_fidelity_judge_rules(root, findings)
        _validate_chrome_devtools_mcp_rules(root, findings)
        _validate_copywriting_conversion_rules(root, findings)
        _validate_brand_strategy_rules(root, findings)
        _validate_n8n_automation_readiness_rules(root, findings)
        _validate_docs_search_catalog(root, findings)
        _validate_phase_playbook(root, findings)
        _validate_skill_catalog(root, findings)
        _validate_global_project_templates(root, findings)
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
