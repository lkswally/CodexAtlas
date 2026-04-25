from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple


DEFAULT_ROOT = Path(__file__).resolve().parents[1]
CONFIG_DIR = DEFAULT_ROOT / "config"
SKILLS_DIR = DEFAULT_ROOT / "skills"

MODEL_PROFILE_PATH = CONFIG_DIR / "model_profiles.json"
MCP_PROFILE_PATH = CONFIG_DIR / "mcp_profiles.json"
MEMORY_DIR_NAME = "memory"
DERIVED_PROJECTS_LOG = "derived_projects.json"
ROUTING_LOG = "routing_log.jsonl"


INTENT_ORDER = (
    "deployment_or_destructive_action",
    "security",
    "project_creation",
    "branding_ux",
    "code_review",
    "architecture",
    "planning",
    "research",
    "documentation",
    "code_execution",
    "unknown",
)

INTENT_KEYWORDS = {
    "deployment_or_destructive_action": (
        "deploy",
        "deployment",
        "hacer deploy",
        "desplegar",
        "desplegar a producción",
        "deploy production",
        "publicar en producción",
        "release production",
        "release",
        "production",
        "producción",
        "push to prod",
        "delete",
        "drop ",
        "destroy",
        "remove permanently",
        "rm ",
        "reset hard",
        "wipe",
    ),
    "security": (
        "security",
        "secret",
        "secrets",
        "token",
        "credential",
        "auth",
        "permission",
        "vulnerability",
        "owasp",
        "threat",
        "encryption",
    ),
    "project_creation": (
        "create project",
        "new project",
        "bootstrap",
        "bootstrap project",
        "start a project",
        "scaffold project",
        "project setup",
        "kick off project",
    ),
    "branding_ux": (
        "brand",
        "branding",
        "ux",
        "ui",
        "landing page",
        "visual direction",
        "design system",
        "copywriting",
        "positioning",
        "hero section",
        "audience",
    ),
    "code_review": (
        "review",
        "code review",
        "audit code",
        "find bugs",
        "regression",
        "pr review",
        "certify",
        "validate output",
    ),
    "architecture": (
        "architecture",
        "architect",
        "refactor architecture",
        "system design",
        "boundary",
        "module split",
        "separation",
        "contract design",
    ),
    "planning": (
        "plan",
        "planning",
        "roadmap",
        "break down",
        "phases",
        "estimate",
        "prioritize",
        "next steps",
    ),
    "research": (
        "research",
        "investigate",
        "look up",
        "compare",
        "latest",
        "docs",
        "documentation",
        "api reference",
        "database schema",
        "schema review",
    ),
    "documentation": (
        "document",
        "documentation",
        "readme",
        "status file",
        "next steps doc",
        "write docs",
        "update docs",
        "handoff",
    ),
    "code_execution": (
        "implement",
        "code",
        "fix",
        "bug",
        "write test",
        "refactor",
        "change file",
        "update function",
        "add endpoint",
        "build feature",
    ),
}
FALLBACK_SKILL_KEYWORDS = {
    "project-bootstrap": (
        "bootstrap",
        "create project",
        "new project",
        "bootstrap project",
        "scaffold project",
        "start a project",
        "kick off project",
    ),
    "repo-audit": (
        "audit repo",
        "audit repository",
        "repo audit",
        "workspace audit",
        "repository audit",
        "governance audit",
        "boundary review",
        "drift",
    ),
    "product-branding-review": (
        "branding review",
        "brand review",
        "ux review",
        "visual direction",
        "positioning",
        "audience",
        "landing page",
        "generic output",
    ),
}

SKILL_PRIORITY = (
    "project-bootstrap",
    "repo-audit",
    "product-branding-review",
)

AGENT_BY_INTENT = {
    "planning": "planner",
    "architecture": "architect",
    "code_execution": "implementer",
    "code_review": "reviewer",
    "branding_ux": "ux_brand",
    "security": "security_guard",
    "research": "reality_checker",
    "documentation": "implementer",
    "project_creation": "orchestrator",
    "deployment_or_destructive_action": "security_guard",
    "unknown": "orchestrator",
}

WORKFLOW_BY_INTENT = {
    "planning": "orchestrator_routing",
    "architecture": "atlas_project_pipeline",
    "code_execution": "atlas_project_pipeline",
    "code_review": "certify_output",
    "branding_ux": "atlas_project_pipeline",
    "security": "certify_output",
    "research": "audit_project",
    "documentation": "orchestrator_routing",
    "project_creation": "create_project",
    "deployment_or_destructive_action": "certify_output",
    "unknown": "orchestrator_routing",
}

MODEL_PROFILE_BY_INTENT = {
    "planning": "deep_reasoning",
    "architecture": "deep_reasoning",
    "code_execution": "code_execution",
    "code_review": "reviewer",
    "branding_ux": "creative_product",
    "security": "security",
    "research": "deep_reasoning",
    "documentation": "cost_saver",
    "project_creation": "deep_reasoning",
    "deployment_or_destructive_action": "security",
    "unknown": "cost_saver",
}

RISK_BY_INTENT = {
    "planning": "low",
    "architecture": "medium",
    "code_execution": "medium",
    "code_review": "medium",
    "branding_ux": "medium",
    "security": "high",
    "research": "medium",
    "documentation": "low",
    "project_creation": "medium",
    "deployment_or_destructive_action": "high",
    "unknown": "medium",
}

DEFAULT_SKILL_BY_INTENT = {
    "project_creation": "project-bootstrap",
    "branding_ux": "product-branding-review",
}
WORKFLOW_BY_SKILL = {
    "project-bootstrap": "create_project",
    "repo-audit": "audit_project",
    "product-branding-review": "atlas_project_pipeline",
}

DANGEROUS_APPROVAL_KEYWORDS = (
    "delete",
    "deploy",
    "hacer deploy",
    "desplegar",
    "desplegar a producción",
    "deploy production",
    "publicar en producción",
    "release production",
    "production",
    "producción",
    "deployment",
    "secret",
    "secrets",
    "credential",
    "credentials",
    "destructive action",
    "destroy",
    "drop",
    "wipe",
)
NEGATED_DANGEROUS_KEYWORD_PATTERNS = {
    "deploy": (
        "sin deploy",
        "no deploy",
        "no hacer deploy",
        "without deploy",
    ),
    "deployment": (
        "no deployment",
        "without deployment",
    ),
    "desplegar": (
        "no desplegar",
    ),
    "desplegar a producción": (
        "no desplegar a producción",
    ),
    "publicar en producción": (
        "no publicar en producción",
    ),
    "release production": (
        "no release production",
        "without release production",
    ),
}

POLICY_MATCH_STOPWORDS = {
    "the",
    "and",
    "or",
    "a",
    "an",
    "to",
    "of",
    "with",
    "without",
    "inside",
    "outside",
    "into",
    "only",
    "because",
    "that",
    "this",
    "is",
    "are",
    "be",
    "do",
    "not",
}

RISK_RANK = {
    "low": 1,
    "medium": 2,
    "high": 3,
}
REYESOFT_ROOT = DEFAULT_ROOT.parent / "REYESOFT"
PROJECT_BOOTSTRAP_PROJECT_MARKERS = (
    ".atlas-project.json",
    ".git",
    "pyproject.toml",
    "package.json",
    "README.md",
    "AGENTS.md",
    "core",
    "scripts",
    "src",
)
PROJECT_TYPE_KEYWORDS = {
    "backend_service": ("backend", "api", "service", "worker"),
    "frontend_app": ("frontend", "ui", "landing page", "web app", "dashboard"),
    "fullstack": ("fullstack", "full stack", "frontend and backend"),
    "internal_tool": ("internal tool", "operations", "ops", "admin", "backoffice"),
    "ai_agent_system": ("ai agent", "agent system", "multi-agent", "skill system", "orchestrator"),
}


def _load_json(path: Path) -> Dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _memory_dir(root: Path) -> Path:
    return root / MEMORY_DIR_NAME


def _event_logging_enabled(root: Path) -> bool:
    if os.environ.get("ATLAS_DISABLE_EVENT_LOGS", "").strip() == "1":
        return False
    return root.resolve() == DEFAULT_ROOT.resolve()


def _append_jsonl_record(path: Path, record: Dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(record, ensure_ascii=False) + "\n")


def _load_json_or_default(path: Path, default: Dict[str, Any]) -> Dict[str, Any]:
    if not path.exists():
        return dict(default)
    try:
        data = json.loads(path.read_text(encoding="utf-8-sig"))
    except Exception:
        return dict(default)
    return data if isinstance(data, dict) else dict(default)


def _write_json(path: Path, payload: Dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _task_fingerprint(task: str) -> str:
    return hashlib.sha256(task.strip().encode("utf-8")).hexdigest()[:16]


def _normalize(task: str) -> str:
    return " ".join(task.lower().split())


def _contains_any(text: str, keywords: List[str]) -> bool:
    return any(_keyword_matches(text, keyword) for keyword in keywords)


def _keyword_matches(text: str, keyword: str) -> bool:
    pattern = r"\b" + re.escape(keyword).replace(r"\ ", r"\s+") + r"\b"
    return re.search(pattern, text) is not None


def _dangerous_keyword_matches(text: str, keyword: str) -> bool:
    if not _keyword_matches(text, keyword):
        return False
    negated_patterns = NEGATED_DANGEROUS_KEYWORD_PATTERNS.get(keyword, ())
    return not any(_keyword_matches(text, pattern) for pattern in negated_patterns)


def _load_behavior_catalog(root: Path) -> Dict[str, Dict[str, Any]]:
    behavior_catalog: Dict[str, Dict[str, Any]] = {}
    skills_dir = root / "skills"
    if not skills_dir.exists():
        return behavior_catalog

    for skill_dir in sorted(path for path in skills_dir.iterdir() if path.is_dir() and not path.name.startswith("_")):
        behavior_path = skill_dir / "behavior.json"
        if not behavior_path.exists():
            continue
        behavior = _load_json(behavior_path)
        if not isinstance(behavior, dict):
            continue
        behavior["behavior_path"] = str(behavior_path)
        behavior_catalog[skill_dir.name] = behavior
    return behavior_catalog


def get_skill_execution_behavior_specs(root: Optional[Path] = None) -> Dict[str, Dict[str, Any]]:
    return _load_behavior_catalog((root or DEFAULT_ROOT).resolve())


def _project_bootstrap_contract_path(root: Path) -> Path:
    return root / "skills" / "project-bootstrap" / "bootstrap_contract.json"


def get_project_bootstrap_contract(root: Optional[Path] = None) -> Dict[str, Any]:
    return _load_json(_project_bootstrap_contract_path((root or DEFAULT_ROOT).resolve()))


def _resolve_project_type(task: str, contract: Dict[str, Any], explicit_project_type: Optional[str] = None) -> Dict[str, Any]:
    supported = list(contract.get("supported_project_types", []))
    default_project_type = str(contract.get("default_project_type", "internal_tool")).strip() or "internal_tool"

    if explicit_project_type:
        normalized = explicit_project_type.strip()
        if normalized in supported:
            return {
                "project_type": normalized,
                "valid": True,
                "source": "explicit",
                "reason": f"Explicit project_type `{normalized}` was provided.",
            }
        return {
            "project_type": normalized,
            "valid": False,
            "source": "explicit",
            "reason": f"Unsupported project_type `{normalized}`.",
        }

    normalized_task = _normalize(task)
    for project_type, keywords in PROJECT_TYPE_KEYWORDS.items():
        if project_type not in supported:
            continue
        if any(_keyword_matches(normalized_task, keyword) for keyword in keywords):
            return {
                "project_type": project_type,
                "valid": True,
                "source": "task_inference",
                "reason": f"Task wording matched the `{project_type}` bootstrap profile.",
            }

    return {
        "project_type": default_project_type,
        "valid": True,
        "source": "default",
        "reason": f"No stronger type signal was found; using default profile `{default_project_type}`.",
    }


def _project_bootstrap_type_template(contract: Dict[str, Any], project_type: str) -> Dict[str, Any]:
    return dict(contract.get("templates_by_type", {}).get(project_type, {}))


def _dedupe_preserve_order(items: List[str]) -> List[str]:
    seen: List[str] = []
    for item in items:
        if item not in seen:
            seen.append(item)
    return seen


def _format_bullet_list(items: List[str], code_wrap: bool = False) -> str:
    if not items:
        return "- none"
    if code_wrap:
        return "\n".join(f"- `{item}/`" for item in items)
    return "\n".join(f"- {item}" for item in items)


def _format_numbered_list(items: List[str]) -> str:
    if not items:
        return "1. No example usage defined yet."
    return "\n".join(f"{idx + 1}. {item}" for idx, item in enumerate(items))


def _load_template_text(root: Path, relative_path: str) -> str:
    return (root / relative_path).read_text(encoding="utf-8")


def _render_template_text(template_text: str, variables: Dict[str, str]) -> str:
    rendered = template_text
    for key, value in variables.items():
        rendered = rendered.replace(f"{{{{{key}}}}}", value)
        rendered = rendered.replace(f"${{{key}}}", value)
        rendered = rendered.replace(f"{{{key}}}", value)
    return rendered


def _policy_tokens(text: str) -> List[str]:
    return [
        token
        for token in re.findall(r"[a-z0-9]+", text.lower())
        if len(token) >= 4 and token not in POLICY_MATCH_STOPWORDS
    ]


def _matches_policy_phrase(task: str, phrase: str) -> bool:
    normalized_task = _normalize(task)
    normalized_phrase = _normalize(phrase)
    if normalized_phrase and normalized_phrase in normalized_task:
        return True

    task_tokens = set(_policy_tokens(normalized_task))
    phrase_tokens = set(_policy_tokens(normalized_phrase))
    if not task_tokens or not phrase_tokens:
        return False

    overlap = task_tokens & phrase_tokens
    return len(overlap) >= 2


def _matches_exact_phrase(task: str, phrase: str) -> bool:
    normalized_task = _normalize(task)
    normalized_phrase = _normalize(phrase)
    return bool(normalized_phrase) and normalized_phrase in normalized_task


def _is_relative_to(path: Path, base: Path) -> bool:
    try:
        path.resolve().relative_to(base.resolve())
        return True
    except ValueError:
        return False


def _project_bootstrap_preflight(output_dir: Optional[Path], root: Optional[Path] = None) -> Dict[str, Any]:
    resolved_root = (root or DEFAULT_ROOT).resolve()
    reyesoft_root = REYESOFT_ROOT.resolve()

    if output_dir is None:
        return {
            "output_dir": None,
            "exists": False,
            "is_empty": False,
            "contains_files": False,
            "seems_existing_project": False,
            "existing_project_markers": [],
            "inside_atlas_root": False,
            "inside_reyesoft": False,
            "matches_forbidden_path": False,
            "safe_to_execute": False,
            "approval_reasons": [],
            "blockers": ["project_bootstrap_missing_output_dir"],
        }

    target = output_dir.resolve()
    exists = target.exists()
    is_dir = target.is_dir() if exists else False
    entries = list(target.iterdir()) if exists and is_dir else []
    is_empty = exists and is_dir and not entries
    contains_files = any(entry.is_file() for entry in entries)
    markers = [marker for marker in PROJECT_BOOTSTRAP_PROJECT_MARKERS if (target / marker).exists()] if exists and is_dir else []
    seems_existing_project = bool(markers)
    inside_atlas_root = _is_relative_to(target, resolved_root)
    inside_reyesoft = _is_relative_to(target, reyesoft_root)
    matches_forbidden_path = target in {resolved_root, reyesoft_root}

    blockers: List[str] = []
    approval_reasons: List[str] = []

    if exists and not is_dir:
        blockers.append("project_bootstrap_output_dir_is_not_directory")
    if matches_forbidden_path:
        blockers.append("project_bootstrap_forbidden_output_dir")
    if inside_atlas_root:
        blockers.append("project_bootstrap_output_dir_inside_atlas_root")
    if inside_reyesoft:
        blockers.append("project_bootstrap_output_dir_inside_reyesoft")
    if exists and is_dir and entries:
        blockers.append("project_bootstrap_output_dir_not_empty")
        approval_reasons.append("project_bootstrap_preflight_existing_non_empty_output_dir")
    if seems_existing_project:
        approval_reasons.append("project_bootstrap_preflight_existing_project_detected")

    deduped_blockers: List[str] = []
    for blocker in blockers:
        if blocker not in deduped_blockers:
            deduped_blockers.append(blocker)

    deduped_approval_reasons: List[str] = []
    for reason in approval_reasons:
        if reason not in deduped_approval_reasons:
            deduped_approval_reasons.append(reason)

    safe_to_execute = output_dir is not None and not deduped_blockers
    return {
        "output_dir": str(target),
        "exists": exists,
        "is_empty": is_empty,
        "contains_files": contains_files,
        "seems_existing_project": seems_existing_project,
        "existing_project_markers": markers,
        "inside_atlas_root": inside_atlas_root,
        "inside_reyesoft": inside_reyesoft,
        "matches_forbidden_path": matches_forbidden_path,
        "safe_to_execute": safe_to_execute,
        "approval_reasons": deduped_approval_reasons,
        "blockers": deduped_blockers,
    }


def _load_skill_catalog(root: Path) -> Dict[str, Dict[str, Any]]:
    skill_catalog: Dict[str, Dict[str, Any]] = {}
    skills_dir = root / "skills"
    if not skills_dir.exists():
        return skill_catalog

    for skill_dir in sorted(path for path in skills_dir.iterdir() if path.is_dir()):
        metadata_path = skill_dir / "skill.json"
        doc_path = skill_dir / "skill.md"
        if not metadata_path.exists():
            continue
        metadata = _load_json(metadata_path)
        if not isinstance(metadata, dict):
            continue
        name = str(metadata.get("name", "")).strip()
        if not name:
            continue
        metadata["doc_path"] = str(doc_path)
        metadata["metadata_path"] = str(metadata_path)
        skill_catalog[name] = metadata
    return skill_catalog


def _classify_skill(task: str, intent: str, skill_catalog: Dict[str, Dict[str, Any]]) -> Tuple[Optional[str], Optional[Dict[str, Any]], str]:
    normalized = _normalize(task)
    scores: Dict[str, int] = {}

    for skill_name, metadata in skill_catalog.items():
        keywords = metadata.get("intent_keywords", [])
        if not isinstance(keywords, list):
            continue
        score = sum(1 for keyword in keywords if _keyword_matches(normalized, keyword))
        if score:
            scores[skill_name] = score

    if scores:
        best_score = max(scores.values())
        for skill_name in SKILL_PRIORITY:
            if scores.get(skill_name) == best_score:
                return (
                    skill_name,
                    skill_catalog.get(skill_name),
                    f"Structured skill metadata matched `{skill_name}` with the strongest keyword score.",
                )
        chosen_name = sorted(name for name, score in scores.items() if score == best_score)[0]
        return (
            chosen_name,
            skill_catalog.get(chosen_name),
            f"Structured skill metadata matched `{chosen_name}` with the strongest keyword score.",
        )

    fallback_scores: Dict[str, int] = {}
    for skill_name, keywords in FALLBACK_SKILL_KEYWORDS.items():
        score = sum(1 for keyword in keywords if _keyword_matches(normalized, keyword))
        if score:
            fallback_scores[skill_name] = score

    if fallback_scores:
        best_score = max(fallback_scores.values())
        for skill_name in SKILL_PRIORITY:
            if fallback_scores.get(skill_name) == best_score:
                if skill_name in skill_catalog:
                    return (
                        skill_name,
                        skill_catalog[skill_name],
                        f"Fallback heuristic matched `{skill_name}` because no structured skill keyword won clearly.",
                    )
                return (
                    skill_name,
                    None,
                    f"Fallback heuristic matched `{skill_name}`, but its structured metadata is missing.",
                )

    if intent in {"research", "code_review", "architecture"} and any(
        token in normalized for token in ("audit", "repo", "repository", "workspace", "boundary", "drift")
    ):
        skill_name = "repo-audit"
        return (
            skill_name,
            skill_catalog.get(skill_name),
            f"Fallback heuristic matched `{skill_name}` from audit and boundary signals.",
        )

    default_skill = DEFAULT_SKILL_BY_INTENT.get(intent)
    if default_skill and default_skill in skill_catalog:
        return (
            default_skill,
            skill_catalog[default_skill],
            f"Intent `{intent}` maps to the default Atlas-native skill `{default_skill}`.",
        )
    return None, None, "No Atlas-native skill is strongly indicated; proceed with workflow and agent guidance only."


def classify_intent(task: str) -> str:
    normalized = _normalize(task)
    scores: Dict[str, int] = {}
    for intent, keywords in INTENT_KEYWORDS.items():
        if intent == "deployment_or_destructive_action":
            score = sum(1 for keyword in keywords if _dangerous_keyword_matches(normalized, keyword))
        else:
            score = sum(1 for keyword in keywords if _keyword_matches(normalized, keyword))
        if score:
            scores[intent] = score

    if not scores:
        return "unknown"

    best_score = max(scores.values())
    for intent in INTENT_ORDER:
        if scores.get(intent) == best_score:
            return intent
    return "unknown"


def _suggest_mcp_ids(task: str, intent: str) -> List[str]:
    normalized = _normalize(task)
    suggestions: List[str] = []

    if any(
        token in normalized
        for token in (
            "latest",
            "look up",
            "current version",
            "current docs",
            "current release",
            "official docs",
            "api reference",
            "sdk docs",
            "documentation site",
        )
    ):
        suggestions.append("docs_search")

    if any(token in normalized for token in ("database", "schema", "table", "column", "sql")):
        suggestions.append("database_schema")

    if any(
        _keyword_matches(normalized, token)
        for token in ("github", "pull request", "pull requests", "github issue", "github issues", "pr")
    ):
        suggestions.append("github")

    if any(token in normalized for token in ("search the web",)):
        suggestions.append("web_search")

    if any(token in normalized for token in ("official product guidance", "library docs")):
        suggestions.append("docs")

    if any(token in normalized for token in ("analytics", "metric", "telemetry", "funnel", "dashboard metrics")):
        suggestions.append("analytics")

    if any(token in normalized for token in ("cross-workspace", "outside this repo", "other workspace", "external files")):
        suggestions.append("filesystem")

    if intent == "research" and not suggestions and "docs" in normalized:
        suggestions.append("docs_search")

    seen: List[str] = []
    for item in suggestions:
        if item not in seen:
            seen.append(item)
    return seen


def _build_model_reason(profile_name: str, profile: Dict[str, Any], intent: str, skill_name: Optional[str]) -> str:
    preferred = ", ".join(profile.get("preferred", []))
    fallback = ", ".join(profile.get("fallback", []))
    description = str(profile.get("description", "")).strip()
    prefix = f"Skill `{skill_name}` overrides the model route. " if skill_name else ""
    return (
        prefix
        + f"Intent `{intent}` routes to profile `{profile_name}`. "
        f"Configured preferred aliases: {preferred or 'none'}. "
        f"Fallback aliases: {fallback or 'none'}. "
        f"{description}"
    ).strip()


def _build_mcp_reason(suggested_ids: List[str], mcp_profiles: Dict[str, Any]) -> str:
    if not suggested_ids:
        return "Default deny: no MCP is suggested for this task. Use built-in repo context first."

    details: List[str] = []
    for mcp_id in suggested_ids:
        profile = mcp_profiles["profiles"][mcp_id]
        details.append(
            f"{mcp_id} ({profile['default_mode']}, approval={str(profile['requires_approval']).lower()}, risk={profile['risk_level']}, decision={profile.get('atlas_decision', 'unknown')})"
        )
    return (
        "Suggested MCPs remain advisory only and are not connected automatically. "
        "Recommended because the task implies external or structured context needs: "
        + "; ".join(details)
    )


def _mcp_lifecycle_state(profile: Dict[str, Any]) -> str:
    if not bool(profile.get("experimental_enabled")):
        return "blocked"
    if bool(profile.get("requires_approval")):
        return "approval_required"
    return "suggested"


def _global_approval_reasons(task: str) -> List[str]:
    normalized = _normalize(task)
    reasons: List[str] = []
    for keyword in DANGEROUS_APPROVAL_KEYWORDS:
        if _dangerous_keyword_matches(normalized, keyword):
            reasons.append(f"dangerous_task_keyword:{keyword}")
    return reasons


def _skill_trigger_matches(task: str, phrases: List[str], prefix: str) -> List[str]:
    if not isinstance(phrases, list):
        return []
    matches: List[str] = []
    for phrase in phrases:
        if isinstance(phrase, str) and phrase.strip() and _matches_policy_phrase(task, phrase):
            matches.append(f"{prefix}:{phrase}")
    return matches


def _next_action(
    intent: str,
    agent: str,
    workflow: str,
    approval: bool,
    suggested_mcps: List[Dict[str, Any]],
    skill_name: Optional[str],
    skill_metadata: Optional[Dict[str, Any]],
    preflight: Optional[Dict[str, Any]],
    execution_blockers: List[str],
) -> str:
    execution_note = ""
    if skill_name and skill_metadata and skill_metadata.get("supports_execution"):
        execution_note = f" Minimal safe execution exists for `{skill_name}`, but only when explicitly requested."

    if preflight and not bool(preflight.get("safe_to_execute")) and preflight.get("blockers"):
        return (
            f"Do not execute `{skill_name or 'the routed path'}` yet. "
            f"Preflight blockers were detected: {', '.join(preflight.get('blockers', []))}."
            + execution_note
        )
    if execution_blockers:
        return (
            f"Do not execute `{skill_name or 'the routed path'}` yet. "
            f"Execution blockers were detected: {', '.join(execution_blockers)}."
            + execution_note
        )
    if approval:
        return (
            f"Pause after routing. Review the `{agent}` recommendation, confirm the `{workflow}` path, "
            "and obtain explicit human approval before any destructive, deployment or MCP-enabled step."
            + execution_note
        )
    if suggested_mcps:
        return (
            f"Start with `{agent}` in `{workflow}` as a suggestion-only plan. "
            "If external context is still needed, request approval before activating any suggested MCP."
            + execution_note
        )
    return (
        f"Start with `{agent}` using `{workflow}` in read-only planning mode. "
        "Do not execute changes automatically."
        + execution_note
    )


def _skill_textual_trigger_matches(task: str, skill_name: Optional[str], phrases: List[str], prefix: str) -> List[str]:
    if not isinstance(phrases, list):
        return []
    matches: List[str] = []
    for phrase in phrases:
        if not isinstance(phrase, str) or not phrase.strip():
            continue
        if skill_name == "project-bootstrap":
            if _matches_exact_phrase(task, phrase):
                matches.append(f"{prefix}:{phrase}")
        elif _matches_policy_phrase(task, phrase):
            matches.append(f"{prefix}:{phrase}")
    return matches


def _approval_reasons(
    task: str,
    intent: str,
    suggested_mcps: List[Dict[str, Any]],
    skill_name: Optional[str],
    skill_metadata: Optional[Dict[str, Any]],
    preflight: Optional[Dict[str, Any]] = None,
) -> List[str]:
    reasons: List[str] = []
    if intent == "deployment_or_destructive_action":
        reasons.append("intent_requires_human_approval")
    if preflight:
        reasons.extend(list(preflight.get("approval_reasons", [])))
    if skill_metadata and bool(skill_metadata.get("requires_human_approval")):
        reasons.append("skill_default_requires_human_approval")
        reasons.extend(
            _skill_textual_trigger_matches(
                task,
                skill_name,
                list(skill_metadata.get("human_approval_triggers", [])),
                "skill_human_approval_trigger",
            )
        )
    elif skill_metadata:
        reasons.extend(
            _skill_textual_trigger_matches(
                task,
                skill_name,
                list(skill_metadata.get("human_approval_triggers", [])),
                "skill_human_approval_trigger",
            )
        )

    reasons.extend(_global_approval_reasons(task))

    for item in suggested_mcps:
        if bool(item.get("requires_approval")):
            reasons.append(f"mcp_requires_approval:{item.get('id')}")

    deduped: List[str] = []
    for reason in reasons:
        if reason not in deduped:
            deduped.append(reason)
    return deduped


def _execution_blockers(
    task: str,
    skill_name: Optional[str],
    skill_metadata: Optional[Dict[str, Any]],
    approval_reasons: List[str],
    preflight: Optional[Dict[str, Any]] = None,
) -> List[str]:
    blockers: List[str] = []
    if preflight:
        blockers.extend(list(preflight.get("blockers", [])))
    if skill_name and skill_metadata:
        blockers.extend(
            _skill_textual_trigger_matches(
                task,
                skill_name,
                list(skill_metadata.get("forbidden_actions", [])),
                "skill_forbidden_action",
            )
        )
        if approval_reasons:
            blockers.append("human_approval_required_before_execution")

    deduped: List[str] = []
    for blocker in blockers:
        if blocker not in deduped:
            deduped.append(blocker)
    return deduped


def _merge_risk(intent_risk: str, skill_metadata: Optional[Dict[str, Any]], requires_human_approval: bool) -> str:
    risk = intent_risk
    if skill_metadata:
        skill_risk = str(skill_metadata.get("risk_level", "")).strip()
        if RISK_RANK.get(skill_risk, 0) > RISK_RANK.get(risk, 0):
            risk = skill_risk
    if requires_human_approval and risk == "medium":
        return "high"
    return risk


def _structured_skill_metadata(metadata: Optional[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
    if not metadata:
        return None
    return {
        "name": metadata.get("name"),
        "intent_keywords": metadata.get("intent_keywords", []),
        "agent": metadata.get("agent"),
        "workflow": metadata.get("workflow"),
        "model_profile": metadata.get("model_profile"),
        "risk_level": metadata.get("risk_level"),
        "requires_human_approval": bool(metadata.get("requires_human_approval")),
        "supports_execution": bool(metadata.get("supports_execution")),
        "execution_mode": metadata.get("execution_mode"),
        "allowed_paths_policy": metadata.get("allowed_paths_policy"),
        "expected_outputs": metadata.get("expected_outputs", []),
        "validations": metadata.get("validations", []),
        "required_inputs": metadata.get("required_inputs", []),
        "safety_limits": metadata.get("safety_limits", []),
        "rollback_manual": metadata.get("rollback_manual", []),
        "forbidden_actions": metadata.get("forbidden_actions", []),
        "human_approval_triggers": metadata.get("human_approval_triggers", []),
        "doc_path": metadata.get("doc_path"),
        "metadata_path": metadata.get("metadata_path"),
    }


def _structured_behavior_metadata(behavior: Optional[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
    if not behavior:
        return None
    return {
        "writes_files": bool(behavior.get("writes_files")),
        "writes_code": bool(behavior.get("writes_code")),
        "uses_output_dir": bool(behavior.get("uses_output_dir")),
        "read_only": bool(behavior.get("read_only")),
        "execution_helper": behavior.get("execution_helper"),
        "side_effects": behavior.get("side_effects", []),
        "requires_project_path": bool(behavior.get("requires_project_path")),
        "requires_output_dir": bool(behavior.get("requires_output_dir")),
        "can_run_without_approval": bool(behavior.get("can_run_without_approval")),
        "notes": behavior.get("notes", []),
        "behavior_path": behavior.get("behavior_path"),
    }


def _record_routing_decision(root: Path, payload: Dict[str, Any]) -> None:
    if not _event_logging_enabled(root):
        return
    entry = {
        "timestamp": _utc_now_iso(),
        "task_fingerprint": _task_fingerprint(str(payload.get("task", ""))),
        "intent": payload.get("intent"),
        "recommended_agent": payload.get("recommended_agent"),
        "recommended_skill": payload.get("recommended_skill"),
        "recommended_workflow": payload.get("recommended_workflow"),
        "model_profile": payload.get("model_profile"),
        "suggested_mcp_ids": [item.get("id") for item in payload.get("suggested_mcps", []) if isinstance(item, dict)],
        "suggested_mcp_details": [
            {
                "id": item.get("id"),
                "atlas_decision": item.get("atlas_decision"),
                "experimental_enabled": item.get("experimental_enabled"),
                "lifecycle_state": item.get("lifecycle_state"),
            }
            for item in payload.get("suggested_mcps", [])
            if isinstance(item, dict)
        ],
        "requires_human_approval": bool(payload.get("requires_human_approval")),
        "risk_level": payload.get("risk_level"),
        "safe_to_execute": payload.get("safe_to_execute"),
        "execution_allowed": payload.get("execution_allowed"),
        "project_type": payload.get("project_type"),
    }
    _append_jsonl_record(_memory_dir(root) / ROUTING_LOG, entry)


def _record_derived_project_creation(root: Path, payload: Dict[str, Any]) -> None:
    if not _event_logging_enabled(root):
        return
    path = _memory_dir(root) / DERIVED_PROJECTS_LOG
    document = _load_json_or_default(path, {"schema_version": "1.0", "projects": []})
    projects = document.get("projects")
    if not isinstance(projects, list):
        projects = []
    projects.append(
        {
            "created_at": _utc_now_iso(),
            "project_name": payload.get("project_name"),
            "project_root": payload.get("project_root"),
            "project_profile": payload.get("project_profile"),
            "generated_from_skill": payload.get("generated_from_skill"),
            "atlas_root": payload.get("atlas_root"),
            "status": payload.get("status"),
        }
    )
    document["projects"] = projects
    _write_json(path, document)


def _build_project_bootstrap_scope(task: str) -> str:
    return "\n".join(
        [
            f"- Bootstrap request: {task}",
            "- Runtime and business logic are intentionally not generated at bootstrap time.",
        ]
    )


def _project_bootstrap_template_variables(
    project_name: str,
    project_type: str,
    type_template: Dict[str, Any],
    task: str,
    directories: List[str],
) -> Dict[str, str]:
    return {
        "project_name": project_name,
        "project_type": project_type,
        "project_goal": str(type_template.get("description", "")).strip() or task,
        "scope": _build_project_bootstrap_scope(task),
        "atlas_root": str(DEFAULT_ROOT),
        "generated_from_skill": "project-bootstrap",
    }


def _load_dispatcher_module():
    path = DEFAULT_ROOT / "tools" / "atlas_dispatcher.py"
    spec = importlib.util.spec_from_file_location("_atlas_dispatcher", str(path))
    if not spec or not spec.loader:
        raise RuntimeError("failed_to_load_dispatcher_spec")
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)
    return mod


def _project_bootstrap_contract(
    output_dir: Optional[Path],
    root: Optional[Path] = None,
    task: str = "",
    explicit_project_type: Optional[str] = None,
) -> Dict[str, Any]:
    resolved_root = (root or DEFAULT_ROOT).resolve()
    contract = get_project_bootstrap_contract(resolved_root)
    behavior = get_skill_execution_behavior_specs(resolved_root).get("project-bootstrap", {})
    skill_metadata = _load_skill_catalog(resolved_root).get("project-bootstrap", {})
    project_type_resolution = _resolve_project_type(task, contract, explicit_project_type)
    resolved_project_type = str(project_type_resolution.get("project_type", contract.get("default_project_type", "internal_tool")))
    type_template = _project_bootstrap_type_template(contract, resolved_project_type)
    execution_mode = "read_only" if bool(behavior.get("read_only")) else "write_docs"
    if bool(behavior.get("writes_code")):
        execution_mode = "write_code"
    allowed_paths_policy = "no_filesystem_writes"
    if bool(behavior.get("uses_output_dir")):
        allowed_paths_policy = "explicit_output_dir_only"
    elif bool(behavior.get("writes_files")) or bool(behavior.get("requires_project_path")):
        allowed_paths_policy = "atlas_root_or_derived_project_read_only"

    hydrated_contract = dict(contract)
    generated_structure = dict(hydrated_contract.get("generated_structure", {}))
    directories = _dedupe_preserve_order(
        list(generated_structure.get("directories", [])) + list(type_template.get("additional_directories", []))
    )
    generated_structure["directories"] = directories
    if "files" not in generated_structure:
        generated_structure["files"] = list(hydrated_contract.get("required_files", []))
    hydrated_contract["generated_structure"] = generated_structure
    hydrated_contract["execution_mode"] = execution_mode
    hydrated_contract["allowed_paths_policy"] = allowed_paths_policy
    hydrated_contract["forbidden_actions"] = list(skill_metadata.get("forbidden_actions", []))
    hydrated_contract["behavior"] = behavior
    hydrated_contract["resolved_project_type"] = resolved_project_type
    hydrated_contract["project_type_resolution"] = project_type_resolution
    hydrated_contract["type_template"] = type_template
    hydrated_contract["output_dir"] = str(output_dir.resolve()) if output_dir else None
    hydrated_contract["preflight"] = _project_bootstrap_preflight(output_dir, resolved_root)
    return hydrated_contract


def _execute_repo_audit(root: Path, project: Optional[Path]) -> Dict[str, Any]:
    dispatcher = _load_dispatcher_module()
    result = dispatcher.dispatch("audit-repo", root=root, project=project)
    return {
        "skill": "repo-audit",
        "mode": "dispatcher_audit_repo",
        "ok": bool(result.ok),
        "exit_code": int(result.exit_code),
        "output": result.output,
    }


def _write_file_if_missing(path: Path, content: str) -> None:
    if not path.exists():
        path.write_text(content, encoding="utf-8")


def _execute_project_bootstrap(
    task: str,
    output_dir: Optional[Path],
    root: Optional[Path] = None,
    project_type: Optional[str] = None,
) -> Dict[str, Any]:
    resolved_root = (root or DEFAULT_ROOT).resolve()
    contract = _project_bootstrap_contract(output_dir, resolved_root, task=task, explicit_project_type=project_type)
    preflight = contract.get("preflight", {})
    project_type_resolution = contract.get("project_type_resolution", {})
    if output_dir is None:
        return {
            "skill": "project-bootstrap",
            "mode": "scaffold",
            "ok": False,
            "error": "missing_output_dir",
            "preflight": preflight,
            "contract": contract,
        }

    if not bool(project_type_resolution.get("valid", True)):
        return {
            "skill": "project-bootstrap",
            "mode": "scaffold",
            "ok": False,
            "error": "invalid_project_type",
            "project_type_resolution": project_type_resolution,
            "preflight": preflight,
            "contract": contract,
        }

    target = output_dir.resolve()
    if not bool(preflight.get("safe_to_execute")):
        return {
            "skill": "project-bootstrap",
            "mode": "scaffold",
            "ok": False,
            "error": "unsafe_output_dir",
            "target": str(target),
            "preflight": preflight,
            "contract": contract,
        }

    target.mkdir(parents=True, exist_ok=True)
    directories = list(contract.get("generated_structure", {}).get("directories", []))
    required_files = list(contract.get("required_files", []))
    type_template = dict(contract.get("type_template", {}))
    resolved_project_type = str(contract.get("resolved_project_type", contract.get("default_project_type", "internal_tool")))
    template_variables = _project_bootstrap_template_variables(
        project_name=target.name,
        project_type=resolved_project_type,
        type_template=type_template,
        task=task,
        directories=directories,
    )
    for rel in directories:
        (target / rel).mkdir(parents=True, exist_ok=True)

    _write_file_if_missing(
        target / "README.md",
        _render_template_text(
            _load_template_text(resolved_root, str(type_template.get("readme_template", ""))),
            template_variables,
        ),
    )
    _write_file_if_missing(
        target / "AGENTS.md",
        _render_template_text(
            _load_template_text(resolved_root, str(type_template.get("agents_template", ""))),
            template_variables,
        ),
    )
    _write_file_if_missing(
        target / ".atlas-project.json",
        json.dumps(
            {
                "schema_version": "1.0",
                "project_name": target.name,
                "project_type": "atlas-derived-project",
                "project_profile": resolved_project_type,
                "bootstrap_template": resolved_project_type,
                "generated_from_skill": "project-bootstrap",
                "derived_from": "Codex-Atlas",
                "atlas_root": str(DEFAULT_ROOT),
                "audit_paths": directories,
                "status": "bootstrapped",
            },
            indent=2,
            ensure_ascii=False,
        )
        + "\n",
    )
    _record_derived_project_creation(
        resolved_root,
        {
            "project_name": target.name,
            "project_root": str(target),
            "project_profile": resolved_project_type,
            "generated_from_skill": "project-bootstrap",
            "atlas_root": str(DEFAULT_ROOT),
            "status": "bootstrapped",
        },
    )

    return {
        "skill": "project-bootstrap",
        "mode": "scaffold",
        "ok": True,
        "target": str(target),
        "created_directories": directories,
        "created_files": required_files,
        "project_type": resolved_project_type,
        "project_type_resolution": project_type_resolution,
        "preflight": preflight,
        "contract": contract,
        "summary": f"Created a minimal derived-project scaffold for task: {task}",
    }


def _execute_branding_review(task: str) -> Dict[str, Any]:
    checklist = [
        {"id": "audience", "question": "Is the target audience explicit and specific?", "status": "pending"},
        {"id": "value_proposition", "question": "Is the value proposition concrete and differentiated?", "status": "pending"},
        {"id": "visual_direction", "question": "Is there a clear visual direction beyond generic defaults?", "status": "pending"},
        {"id": "proof", "question": "Are claims supported by evidence, references or rationale?", "status": "pending"},
        {"id": "anti_generic", "question": "Does the proposal avoid generic branding and UX output?", "status": "pending"},
    ]
    return {
        "skill": "product-branding-review",
        "mode": "structured_checklist",
        "ok": True,
        "task": task,
        "checklist": checklist,
        "summary": "Returned a structured branding and UX review checklist without making changes.",
    }


def execute_skill(
    skill_name: str,
    task: str,
    root: Optional[Path] = None,
    project: Optional[Path] = None,
    output_dir: Optional[Path] = None,
    project_type: Optional[str] = None,
) -> Dict[str, Any]:
    root = (root or DEFAULT_ROOT).resolve()
    project = project.resolve() if project else None
    output_dir = output_dir.resolve() if output_dir else None

    if skill_name == "repo-audit":
        return _execute_repo_audit(root=root, project=project)
    if skill_name == "project-bootstrap":
        return _execute_project_bootstrap(task=task, output_dir=output_dir, root=root, project_type=project_type)
    if skill_name == "product-branding-review":
        return _execute_branding_review(task=task)
    return {"skill": skill_name, "ok": False, "error": "execution_not_supported"}


def orchestrate_task(
    task: str,
    root: Optional[Path] = None,
    output_dir: Optional[Path] = None,
    project_type: Optional[str] = None,
) -> Dict[str, Any]:
    root = (root or DEFAULT_ROOT).resolve()
    output_dir = output_dir.resolve() if output_dir else None
    if not task or not task.strip():
        raise ValueError("task_must_not_be_empty")

    model_profiles = _load_json(root / "config" / "model_profiles.json")
    mcp_profiles = _load_json(root / "config" / "mcp_profiles.json")
    skill_catalog = _load_skill_catalog(root)
    behavior_catalog = get_skill_execution_behavior_specs(root)
    bootstrap_contract = get_project_bootstrap_contract(root)

    intent = classify_intent(task)
    recommended_agent = AGENT_BY_INTENT[intent]
    recommended_workflow = WORKFLOW_BY_INTENT[intent]
    model_profile_name = MODEL_PROFILE_BY_INTENT[intent]
    recommended_skill, skill_metadata, skill_reason = _classify_skill(task, intent, skill_catalog)
    behavior_metadata = behavior_catalog.get(recommended_skill) if recommended_skill else None
    preflight = _project_bootstrap_preflight(output_dir, root) if recommended_skill == "project-bootstrap" else None
    project_type_resolution = (
        _resolve_project_type(task, bootstrap_contract, project_type) if recommended_skill == "project-bootstrap" else None
    )

    if skill_metadata:
        recommended_agent = str(skill_metadata.get("agent", recommended_agent)).strip() or recommended_agent
        recommended_workflow = str(skill_metadata.get("workflow", recommended_workflow)).strip() or recommended_workflow
        model_profile_name = str(skill_metadata.get("model_profile", model_profile_name)).strip() or model_profile_name
    elif recommended_skill in WORKFLOW_BY_SKILL:
        recommended_workflow = WORKFLOW_BY_SKILL[recommended_skill]

    model_profile = model_profiles["profiles"][model_profile_name]

    suggested_mcp_ids = _suggest_mcp_ids(task, intent)
    suggested_mcps = [
        {
            "id": mcp_id,
            "default_mode": mcp_profiles["profiles"][mcp_id]["default_mode"],
            "requires_approval": mcp_profiles["profiles"][mcp_id]["requires_approval"],
            "risk_level": mcp_profiles["profiles"][mcp_id]["risk_level"],
            "provider_kind": mcp_profiles["profiles"][mcp_id].get("provider_kind"),
            "atlas_decision": mcp_profiles["profiles"][mcp_id].get("atlas_decision"),
            "experimental_enabled": bool(mcp_profiles["profiles"][mcp_id].get("experimental_enabled")),
            "read_only_scope": mcp_profiles["profiles"][mcp_id].get("read_only_scope"),
            "lifecycle_state": _mcp_lifecycle_state(mcp_profiles["profiles"][mcp_id]),
        }
        for mcp_id in suggested_mcp_ids
    ]

    approval_reasons = _approval_reasons(task, intent, suggested_mcps, recommended_skill, skill_metadata, preflight)
    requires_human_approval = bool(approval_reasons)
    execution_blockers = _execution_blockers(task, recommended_skill, skill_metadata, approval_reasons, preflight)
    if project_type_resolution and not bool(project_type_resolution.get("valid", True)):
        execution_blockers = _dedupe_preserve_order(
            execution_blockers + [f"project_bootstrap_invalid_project_type:{project_type_resolution.get('project_type')}"]
        )
    safe_to_execute = bool(preflight.get("safe_to_execute")) if preflight is not None else bool(
        recommended_skill and skill_metadata and skill_metadata.get("supports_execution")
    )
    execution_allowed = bool(recommended_skill and skill_metadata and skill_metadata.get("supports_execution")) and safe_to_execute and not execution_blockers
    risk_level = _merge_risk(RISK_BY_INTENT[intent], skill_metadata, requires_human_approval)

    result = {
        "task": task,
        "intent": intent,
        "recommended_agent": recommended_agent,
        "recommended_skill": recommended_skill,
        "skill_reason": skill_reason,
        "project_type": project_type_resolution.get("project_type") if project_type_resolution else None,
        "project_type_reason": project_type_resolution.get("reason") if project_type_resolution else None,
        "skill_metadata": _structured_skill_metadata(skill_metadata),
        "behavior_metadata": _structured_behavior_metadata(behavior_metadata),
        "recommended_workflow": recommended_workflow,
        "model_profile": model_profile_name,
        "model_reason": _build_model_reason(model_profile_name, model_profile, intent, recommended_skill if skill_metadata else None),
        "suggested_mcps": suggested_mcps,
        "mcp_reason": _build_mcp_reason(suggested_mcp_ids, mcp_profiles),
        "preflight": preflight,
        "safe_to_execute": safe_to_execute,
        "requires_human_approval": requires_human_approval,
        "approval_reasons": approval_reasons,
        "risk_level": risk_level,
        "execution_allowed": execution_allowed,
        "execution_blockers": execution_blockers,
        "next_action": _next_action(
            intent,
            recommended_agent,
            recommended_workflow,
            requires_human_approval,
            suggested_mcps,
            recommended_skill,
            skill_metadata,
            preflight,
            execution_blockers,
        ),
    }
    _record_routing_decision(root, result)
    return result


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(add_help=True)
    parser.add_argument("--root", default=None, help="Atlas root to use for routing.")
    parser.add_argument("--project", default=None, help="Derived project root for supported skill execution.")
    parser.add_argument("--execute", action="store_true", help="Execute the recommended skill only if it supports safe minimal execution.")
    parser.add_argument("--output-dir", default=None, help="Output directory for project-bootstrap execution.")
    parser.add_argument("--project-type", default=None, help="Optional project profile for project-bootstrap.")
    parser.add_argument("task", nargs="+", help="Task description to route.")
    args = parser.parse_args(argv)

    root = Path(args.root).resolve() if args.root else DEFAULT_ROOT
    project = Path(args.project).resolve() if args.project else None
    output_dir = Path(args.output_dir).resolve() if args.output_dir else None

    result = orchestrate_task(" ".join(args.task), root=root, output_dir=output_dir, project_type=args.project_type)
    if args.execute and result.get("recommended_skill"):
        if not result.get("execution_allowed", False):
            result["execution"] = {
                "ok": False,
                "error": "execution_blocked",
                "blockers": result.get("execution_blockers", []),
                "approval_reasons": result.get("approval_reasons", []),
            }
        else:
            result["execution"] = execute_skill(
                str(result["recommended_skill"]),
                task=result["task"],
                root=root,
                project=project,
                output_dir=output_dir,
                project_type=args.project_type,
            )
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
