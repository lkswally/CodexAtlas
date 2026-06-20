from __future__ import annotations

from typing import Any, Dict, Iterable, Mapping, Optional, Sequence

from tools.architecture_state_model import validate_architecture_state
from tools.dangerous_command_policy import classify_command


MODEL_CLASSES = {
    "cheap_fast",
    "balanced",
    "premium_reasoning",
    "code_specialist",
    "verifier",
    "summarizer",
}
ROLES = {
    "Planner",
    "Executor",
    "Verifier",
    "Evidence Reporter",
    "Security Reviewer",
    "MCP Specialist",
    "Documentation Specialist",
    "Release Reviewer",
    "Failure Recorder",
    "Orchestrator",
}
RETURN_STATUSES = {"PASS", "WARN", "FAIL", "BLOCKED"}
RETURN_FIELDS = {
    "agent",
    "status",
    "summary",
    "evidence",
    "changes",
    "risks",
    "recommendation",
    "needs_followup",
}
MAX_AGENT_COUNT = 3
MAX_CONTEXT_FILES = 4


TASK_KEYWORDS = {
    "architecture": ("architecture", "arquitectura", "design system", "redesign"),
    "security": ("security", "seguridad", "secret", "credential", "vulnerability"),
    "mcp": ("mcp", "model context protocol", "engram"),
    "release": ("release", "tag", "release candidate", "rc1"),
    "verification": ("verify", "verification", "validar", "audit", "review"),
    "documentation": ("documentation", "documentacion", "docs", "readme"),
    "summary": ("summarize", "summary", "resumir", "resumen"),
    "failure": ("failure registry", "record failure", "registrar fallo"),
    "code": ("code", "codigo", "implement", "fix", "refactor", "test"),
}
HIGH_RISK_KEYWORDS = (
    "production",
    "produccion",
    "deploy",
    "delete",
    "borrar",
    "credential",
    "secret",
    "database",
    "release",
    "critical",
    "critico",
)
DESTRUCTIVE_INTENT_KEYWORDS = (
    "delete",
    "remove",
    "clean",
    "reset",
    "purge",
    "destroy",
    "wipe",
    "eliminar",
    "borrar",
    "limpiar",
    "purgar",
    "git reset",
    "git clean",
    "drop database",
    "drop table",
    "truncate table",
    "drop schema",
    "delete from",
    "force push",
    "git checkout --",
    "git restore",
)
RUNTIME_ARCHITECTURE_KEYWORDS = (
    "runtime",
    "runtime architecture",
    "architecture runtime",
    "runtime integration",
    "integration runtime",
    "autonomous runtime",
    "runtime autonomo",
    "runtime aut\u00f3nomo",
    "integracion runtime",
    "integraci\u00f3n runtime",
    "disenar runtime",
    "dise\u00f1ar runtime",
    "design runtime",
)
MCP_SIDE_EFFECT_KEYWORDS = (
    "mcp write",
    "mcp save",
    "mcp update",
    "mcp delete",
    "mcp mutate",
    "write tool",
    "tool write",
    "non-read-only",
    "not read-only",
    "con side effects",
    "with side effects",
)
COMPLEXITY_KEYWORDS = (
    "architecture",
    "arquitectura",
    "cross-module",
    "multiple modules",
    "end-to-end",
    "migration",
    "redesign",
    "complex",
    "complejo",
)
VAGUE_PROMPTS = {"help", "ayuda", "do it", "hazlo", "fix it", "arreglalo"}


class OrchestratorContractError(ValueError):
    """Raised when advisory orchestration inputs or envelopes are invalid."""


def _dedupe(items: Iterable[Any]) -> list[Any]:
    result: list[Any] = []
    for item in items:
        if item not in result:
            result.append(item)
    return result


def analyze_intake(prompt: str, proposed_commands: Sequence[str] = ()) -> Dict[str, Any]:
    text = str(prompt or "").strip()
    lowered = text.lower()
    words = text.split()
    clear = len(words) >= 3 and lowered not in VAGUE_PROMPTS

    destructive_intent = any(item in lowered for item in DESTRUCTIVE_INTENT_KEYWORDS)
    runtime_architecture = any(item in lowered for item in RUNTIME_ARCHITECTURE_KEYWORDS)
    mcp_side_effects = "mcp" in lowered and any(
        item in lowered for item in MCP_SIDE_EFFECT_KEYWORDS
    )

    if destructive_intent:
        task_type = "destructive_operation"
    elif runtime_architecture:
        task_type = "architecture"
    else:
        task_type = "general"
        for candidate, keywords in TASK_KEYWORDS.items():
            if any(keyword in lowered for keyword in keywords):
                task_type = candidate
                break

    risk_level = "high" if any(item in lowered for item in HIGH_RISK_KEYWORDS) else "low"
    risk_reasons = []
    if destructive_intent:
        risk_level = "high"
        risk_reasons.append("destructive_intent")
    if runtime_architecture:
        risk_level = "high"
        risk_reasons.append("runtime_architecture")
    if task_type == "security":
        risk_level = "high"
        risk_reasons.append("security_sensitive")
    if mcp_side_effects:
        risk_level = "high"
        risk_reasons.append("mcp_side_effects")
    if risk_level == "low" and task_type in {"code", "mcp", "release", "security"}:
        risk_level = "medium"

    if (
        runtime_architecture
        or any(item in lowered for item in COMPLEXITY_KEYWORDS)
        or len(words) > 50
    ):
        complexity = "complex"
    elif len(words) <= 12:
        complexity = "simple"
    else:
        complexity = "moderate"

    impact = "high" if risk_level == "high" else ("medium" if complexity != "simple" else "low")
    tool_needs = []
    if proposed_commands:
        tool_needs.append("local_commands")
    if task_type == "mcp":
        tool_needs.append("mcp_diagnostics")
    if task_type in {"verification", "release"}:
        tool_needs.append("verification_tools")

    evidence_required = task_type not in {"summary", "general"} or risk_level != "low"
    return {
        "task_type": task_type,
        "risk_level": risk_level,
        "complexity": complexity,
        "impact": impact,
        "tool_needs": tool_needs,
        "multiple_agents_useful": complexity == "complex" or risk_level == "high",
        "evidence_required": evidence_required,
        "expected_cost": "low" if complexity == "simple" and risk_level == "low" else ("high" if risk_level == "high" else "medium"),
        "clear": clear,
        "risk_reasons": risk_reasons,
        "mcp_side_effects": mcp_side_effects,
    }


def select_model_class(intake: Mapping[str, Any]) -> Dict[str, str]:
    task_type = str(intake["task_type"])
    risk_level = str(intake["risk_level"])
    complexity = str(intake["complexity"])
    if task_type == "verification":
        selected = "verifier"
        reason = "Verification work uses the verifier class."
    elif task_type == "summary":
        selected = "summarizer"
        reason = "Pure consolidation uses the summarizer class."
    elif risk_level in {"high", "critical"} or task_type in {
        "architecture",
        "security",
        "destructive_operation",
    }:
        selected = "premium_reasoning"
        reason = "Sensitive, high-risk, or architecture work requires premium reasoning."
    elif task_type == "code" and complexity == "complex":
        selected = "code_specialist"
        reason = "Complex code work benefits from a code-specialist class."
    elif complexity == "simple" and risk_level == "low":
        selected = "cheap_fast"
        reason = "A cheap, fast class is sufficient for this bounded low-risk task."
    else:
        selected = "balanced"
        reason = "Moderate work uses the balanced class."

    return {
        "selected_model_class": selected,
        "reason": reason,
        "cost_sensitivity": "high" if intake["expected_cost"] == "low" else "medium",
        "risk_level": risk_level,
    }


def _primary_role(task_type: str) -> str:
    return {
        "architecture": "Planner",
        "security": "Security Reviewer",
        "mcp": "MCP Specialist",
        "release": "Release Reviewer",
        "verification": "Verifier",
        "documentation": "Documentation Specialist",
        "summary": "Documentation Specialist",
        "failure": "Failure Recorder",
        "code": "Executor",
        "destructive_operation": "Security Reviewer",
    }.get(task_type, "Orchestrator")


def _route_roles(intake: Mapping[str, Any]) -> list[str]:
    primary = _primary_role(str(intake["task_type"]))
    if not intake["multiple_agents_useful"]:
        return [primary]

    if intake["risk_level"] in {"high", "critical"}:
        roles = [primary]
        if primary != "Security Reviewer":
            roles.append("Security Reviewer")
    else:
        roles = ["Planner"] if primary != "Planner" else [primary]
        if primary not in roles:
            roles.append(primary)
        elif primary == "Planner":
            roles.append("Executor")
    if "Verifier" not in roles:
        roles.append("Verifier")
    return _dedupe(roles)[:MAX_AGENT_COUNT]


def _relevant_domains(task_type: str) -> list[str]:
    shared = ["governance", "security"]
    specific = {
        "architecture": ["docs", "tests"],
        "security": ["security", "governance"],
        "mcp": ["mcp", "security"],
        "release": ["release", "workflows", "tests"],
        "verification": ["evidence", "tests"],
        "documentation": ["docs", "governance"],
        "summary": ["docs"],
        "failure": ["failure_registry", "evidence"],
        "code": ["tests", "governance"],
        "destructive_operation": ["security", "governance"],
    }.get(task_type, [])
    return _dedupe(specific + shared)[:4]


def _select_files(role: str, relevant_files: Sequence[str]) -> list[str]:
    files = _dedupe(str(item) for item in relevant_files if str(item).strip())
    preferences = {
        "Verifier": ("test", "config", "workflow"),
        "Evidence Reporter": ("evidence", "report", "test"),
        "Security Reviewer": ("security", "policy", "config"),
        "MCP Specialist": ("mcp", "config", "policy"),
        "Documentation Specialist": (".md", "docs", "readme"),
        "Release Reviewer": ("release", "workflow", "changelog"),
    }.get(role, ())
    preferred = [item for item in files if any(token in item.lower() for token in preferences)]
    fallback = [item for item in files if item not in preferred]
    return (preferred + fallback)[:MAX_CONTEXT_FILES]


def _architecture_context(
    state: Optional[Mapping[str, Any]], task_type: str
) -> Dict[str, str]:
    if state is None:
        return {}
    validate_architecture_state(state)
    domains = state["domains"]
    return {
        name: str(domains[name]["status"])
        for name in _relevant_domains(task_type)
    }


def _assignment(
    role: str,
    prompt: str,
    relevant_files: Sequence[str],
    architecture_context: Mapping[str, str],
) -> Dict[str, Any]:
    return {
        "agent": role,
        "objective": f"Handle the {role} responsibility for: {prompt.strip()}",
        "context": {
            "relevant_files": _select_files(role, relevant_files),
            "architecture_domains": dict(architecture_context),
            "constraints": [
                "advisory_simulation_only",
                "no_runtime_execution",
                "return_evidence_for_claims",
            ],
        },
        "expected_output": sorted(RETURN_FIELDS),
    }


def validate_return_envelope(envelope: Any) -> bool:
    if not isinstance(envelope, Mapping) or set(envelope) != RETURN_FIELDS:
        raise OrchestratorContractError("Return envelope violates the exact field contract.")
    if envelope["agent"] not in ROLES:
        raise OrchestratorContractError("Return envelope agent is not an allowed role.")
    if envelope["status"] not in RETURN_STATUSES:
        raise OrchestratorContractError("Return envelope status is invalid.")
    for field in ("evidence", "changes", "risks"):
        if not isinstance(envelope[field], list):
            raise OrchestratorContractError(f"Return envelope `{field}` must be a list.")
    if not isinstance(envelope["needs_followup"], bool):
        raise OrchestratorContractError("Return envelope needs_followup must be boolean.")
    for field in ("summary", "recommendation"):
        if not isinstance(envelope[field], str):
            raise OrchestratorContractError(f"Return envelope `{field}` must be text.")
    if envelope["status"] == "PASS" and not envelope["evidence"]:
        raise OrchestratorContractError("PASS return envelopes require evidence.")
    return True


def consolidate_return_envelopes(envelopes: Sequence[Mapping[str, Any]]) -> Dict[str, Any]:
    if not envelopes:
        raise OrchestratorContractError("At least one return envelope is required.")
    for envelope in envelopes:
        validate_return_envelope(envelope)

    statuses = [str(item["status"]) for item in envelopes]
    status = next(
        candidate
        for candidate in ("FAIL", "BLOCKED", "WARN", "PASS")
        if candidate in statuses
    )
    recommendations = [
        str(item["recommendation"]).strip()
        for item in envelopes
        if str(item["recommendation"]).strip()
    ]
    result = {
        "agent": "Orchestrator",
        "status": status,
        "summary": " | ".join(str(item["summary"]) for item in envelopes),
        "evidence": _dedupe(evidence for item in envelopes for evidence in item["evidence"]),
        "changes": _dedupe(change for item in envelopes for change in item["changes"]),
        "risks": _dedupe(risk for item in envelopes for risk in item["risks"]),
        "recommendation": recommendations[0] if recommendations else "",
        "needs_followup": any(bool(item["needs_followup"]) for item in envelopes)
        or status != "PASS",
    }
    validate_return_envelope(result)
    return result


def simulate_orchestration(
    prompt: str,
    *,
    relevant_files: Sequence[str] = (),
    proposed_commands: Sequence[str] = (),
    architecture_state: Optional[Mapping[str, Any]] = None,
    agent_results: Optional[Sequence[Mapping[str, Any]]] = None,
) -> Dict[str, Any]:
    """Produce one advisory orchestration plan without executing tools or agents."""
    intake = analyze_intake(prompt, proposed_commands)
    command_assessments = [classify_command(command) for command in proposed_commands]
    denied = [item for item in command_assessments if item["status"] == "DENY"]
    warned = [item for item in command_assessments if item["status"] in {"WARN", "UNKNOWN"}]

    if denied:
        intake["risk_level"] = "critical"
        intake["impact"] = "high"
        intake["expected_cost"] = "high"
        intake["multiple_agents_useful"] = True
        intake["risk_reasons"] = _dedupe(
            intake["risk_reasons"] + ["dangerous_policy_deny"]
        )
    elif warned and (
        intake["risk_level"] == "high"
        or intake["task_type"]
        in {"mcp", "security", "destructive_operation", "architecture"}
    ):
        intake["risk_level"] = "high"
        intake["impact"] = "high"
        intake["expected_cost"] = "high"
        intake["multiple_agents_useful"] = True
        intake["risk_reasons"] = _dedupe(
            intake["risk_reasons"] + ["sensitive_policy_warning"]
        )

    routing = select_model_class(intake)

    if architecture_state is not None:
        validate_architecture_state(architecture_state)
    state_blockers = []
    state_warnings = []
    if architecture_state is not None:
        for name in ("governance", "security"):
            if architecture_state["domains"][name]["status"] == "FAIL":
                state_blockers.append(f"architecture_domain_failed:{name}")
        for name in _relevant_domains(str(intake["task_type"])):
            domain_status = architecture_state["domains"][name]["status"]
            if domain_status in {"WARN", "UNKNOWN"}:
                state_warnings.append(
                    f"architecture_domain_{domain_status.lower()}:{name}"
                )

    if not intake["clear"]:
        status = "NEEDS_CLARIFICATION"
        question = "What concrete outcome and scope should Atlas evaluate?"
        roles: list[str] = []
    elif denied or state_blockers:
        status = "BLOCKED"
        question = ""
        roles = []
    else:
        status = "READY"
        question = ""
        roles = _route_roles(intake)

    architecture_context = _architecture_context(architecture_state, str(intake["task_type"]))
    assignments = [
        _assignment(role, prompt, relevant_files, architecture_context)
        for role in roles
    ]
    consolidated = consolidate_return_envelopes(agent_results) if agent_results else None
    approval_reasons = []
    if intake["risk_level"] in {"high", "critical"} or intake["impact"] == "high":
        approval_reasons.append("elevated_risk")
    if warned:
        approval_reasons.append("dangerous_policy_warning_or_unknown")
    if denied:
        approval_reasons.append("dangerous_policy_deny")
    approval_reasons.extend(state_warnings)
    approval_reasons = _dedupe(approval_reasons)
    requires_approval = bool(approval_reasons)
    blockers = state_blockers + [
        f"dangerous_command:{item['matched_pattern']}" for item in denied
    ]
    failure_registry_review_required = bool(
        blockers
        or (consolidated and consolidated["status"] in {"FAIL", "BLOCKED"})
    )
    if status == "NEEDS_CLARIFICATION":
        final_decision = "ASK_ONE_QUESTION"
    elif status == "BLOCKED":
        final_decision = "BLOCK"
    elif requires_approval:
        final_decision = "NEEDS_APPROVAL"
    elif status == "READY":
        final_decision = "EXECUTE_SIMULATED"
    else:
        final_decision = "REJECT"
    return {
        "orchestrator": "atlas_intelligent_orchestrator",
        "version": "v1",
        "mode": "advisory_simulation",
        "status": status,
        "final_decision": final_decision,
        "intake": intake,
        "decision_gate": {
            "task_is_clear": intake["clear"],
            "safe_to_proceed": not denied and not state_blockers,
            "requires_human_approval": requires_approval,
            "single_agent_sufficient": not intake["multiple_agents_useful"],
            "split_task": len(assignments) > 1,
            "evidence_required": intake["evidence_required"],
            "blockers": blockers,
            "approval_reasons": approval_reasons,
        },
        "model_routing": routing,
        "agent_assignments": assignments,
        "command_assessments": command_assessments,
        "clarification": {
            "required": status == "NEEDS_CLARIFICATION",
            "question_count": 1 if status == "NEEDS_CLARIFICATION" else 0,
            "question": question,
        },
        "loop_control": {
            "max_decision_rounds": 1,
            "max_agents": MAX_AGENT_COUNT,
            "planned_agents": len(assignments),
            "agents_may_converse": False,
        },
        "verification_plan": {
            "review_evidence": True,
            "review_risks": True,
            "review_tests_and_checks": True,
            "review_changes": True,
            "review_docs_consistency": True,
            "failure_registry_review_required": failure_registry_review_required,
        },
        "consolidated_result": consolidated,
        "runtime_execution": False,
    }
