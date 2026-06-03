from __future__ import annotations

from typing import Dict, Tuple


SEVERITY_RANK: Dict[str, int] = {
    "blocker": 4,
    "high": 3,
    "medium": 2,
    "low": 1,
}

CORE_REPORTS: Tuple[str, ...] = (
    "project-phase-report",
    "audit-repo",
    "certify-project",
    "design_intelligence_audit",
    "surface-audit",
)

QUALITY_GATE_MINIMUM_TOP_LEVEL_KEY_ALIASES = {
    "status": ("status",),
    "project": ("project", "project_path"),
    "overall_status": ("overall_status",),
    "confidence": ("confidence", "confidence_level"),
    "summary_for_human": ("summary_for_human",),
    "recommended_next_action": ("recommended_next_action",),
    "source_reports": ("source_reports",),
    "warnings": ("warnings",),
    "blockers": ("blockers",),
}

QUALITY_GATE_CORE_POSTURE_KEYS: Tuple[str, ...] = (
    "visual_intent_posture",
    "brand_profile_posture",
    "brand_strategy_posture",
    "ui_ux_design_system_posture",
    "visual_fidelity_posture",
    "chrome_devtools_mcp_posture",
    "mcp_permission_posture",
    "model_cost_control_posture",
    "n8n_automation_posture",
    "department_registry_posture",
    "repo_graph_posture",
    "business_idea_simulation_posture",
)

QUALITY_GATE_SOURCE_REPORT_IDS: Tuple[str, ...] = (
    "project-phase-report",
    "audit-repo",
    "certify-project",
    "design_intelligence_audit",
    "surface-audit",
    "project_intent_analyzer",
    "intent_clarifier_contract",
    "brand_json_v2_readiness",
    "frontend_auto_audit_rules",
    "playwright_visual_qa_readiness",
    "codex_runtime_compatibility_check",
    "atlas_memory_readiness",
    "skill_registry_index_first_readiness",
    "ui_ux_design_system_readiness",
    "atlas_error_learning_review",
    "evidence_collector_readiness",
    "visual_fidelity_judge",
    "chrome_devtools_mcp_readiness",
    "mcp_permission_matrix_readiness",
    "copywriting_conversion_readiness",
    "brand_strategy_readiness",
    "n8n_automation_readiness",
    "change_proposal_readiness",
    "file_change_declaration_verification",
    "prompt_builder",
    "skill_evaluator",
    "skill_improvement_review",
    "feedback_analyzer",
    "model_router",
    "error_pattern_analyzer",
    "creative_pipeline_readiness",
    "component_inspiration_readiness",
    "model_cost_control_readiness",
    "business_idea_simulation_readiness",
    "department_registry_readiness",
    "repo_graph_readiness",
)

QUALITY_GATE_CORE_SOURCE_REPORT_KEYS: Tuple[str, ...] = (
    "project-phase-report",
    "audit-repo",
    "certify-project",
    "surface-audit",
    "project_intent_analyzer",
    "design_intelligence_audit",
    "model_router",
    "model_cost_control_readiness",
    "chrome_devtools_mcp_readiness",
    "mcp_permission_matrix_readiness",
    "brand_strategy_readiness",
    "copywriting_conversion_readiness",
    "n8n_automation_readiness",
    "department_registry_readiness",
    "repo_graph_readiness",
    "business_idea_simulation_readiness",
)

WARNING_FIELD_ALIASES = {
    "identifier": ("id", "code", "check"),
    "message": ("message", "reason"),
    "severity": ("severity",),
    "source": ("source",),
}


def expected_posture_keys() -> Tuple[str, ...]:
    return QUALITY_GATE_CORE_POSTURE_KEYS


def expected_source_report_ids() -> Tuple[str, ...]:
    return QUALITY_GATE_SOURCE_REPORT_IDS
