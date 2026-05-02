from __future__ import annotations

import argparse
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple


DEFAULT_ROOT = Path(__file__).resolve().parents[1]
SURFACE_FILES = ("README.md", "AGENTS.md", "index.html", "docs/architecture.md")
PROJECT_TYPE_KEYWORDS = {
    "internal_tool": ("internal tool", "operations", "ops", "admin", "dashboard", "workflow", "backoffice"),
    "frontend_app": ("landing", "website", "frontend", "marketing", "site", "static web"),
    "backend_service": ("api", "backend", "service", "webhook", "worker", "jobs"),
    "fullstack": ("fullstack", "full-stack", "auth", "database", "dashboard", "backend and frontend"),
    "ai_agent_system": ("ai system", "agent system", "multi-agent", "orchestrator", "routing", "governance"),
}
AUDIENCE_TERMS = (
    "for developers",
    "for teams",
    "for operators",
    "for founders",
    "for internal teams",
    "for product teams",
    "for technical teams",
    "audience",
)
SCOPE_TERMS = ("scope", "constraints", "restrictions", "no deploy", "no backend", "no mcp", "read-only")
HIGH_RISK_TERMS = (
    "production",
    "deploy",
    "payments",
    "auth",
    "authentication",
    "security",
    "credentials",
    "tokens",
    "customer data",
    "api",
    "database",
)
MEDIUM_RISK_TERMS = ("public", "landing", "signup", "integration", "webapp", "workflow")
HIGH_COMPLEXITY_TYPES = {"fullstack", "backend_service", "ai_agent_system"}
MEDIUM_COMPLEXITY_TYPES = {"frontend_app", "internal_tool"}
NEGATED_RISK_PATTERNS = (
    "no deploy",
    "without deploy",
    "sin deploy",
    "no production deploy",
    "no backend",
    "no mcp",
)


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _normalize(text: str) -> str:
    return re.sub(r"\s+", " ", text.lower()).strip()


def _read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8-sig")


def _read_json(path: Path) -> Dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def _strip_html(text: str) -> str:
    text = re.sub(r"<[^>]+>", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def _extract_first_meaningful_sentence(text: str) -> Optional[str]:
    cleaned = _strip_html(text)
    if not cleaned:
        return None
    parts = re.split(r"(?<=[.!?])\s+", cleaned)
    for part in parts:
        candidate = part.strip()
        if len(candidate.split()) >= 5:
            return candidate
    return cleaned[:180].strip() if cleaned else None


def _extract_first_heading(text: str) -> Optional[str]:
    for pattern in (
        r"<h1\b[^>]*>(.*?)</h1>",
        r"^#\s+(.+)$",
        r"^##\s+(.+)$",
    ):
        match = re.search(pattern, text, flags=re.IGNORECASE | re.MULTILINE | re.DOTALL)
        if match:
            heading = _strip_html(match.group(1)).strip()
            if heading:
                return heading
    return None


def _collect_project_text(project: Path) -> Dict[str, str]:
    surface: Dict[str, str] = {}
    for rel in SURFACE_FILES:
        path = project / rel
        if path.exists():
            surface[rel] = _read_text(path)
    return surface


def _load_project_metadata(project: Path) -> Tuple[Optional[Dict[str, Any]], Optional[str]]:
    path = project / ".atlas-project.json"
    if not path.exists():
        return None, "missing_project_metadata"
    try:
        data = _read_json(path)
    except Exception as exc:
        return None, f"invalid_project_metadata:{exc}"
    if not isinstance(data, dict):
        return None, "project_metadata_not_object"
    return data, None


def _keyword_hits(normalized_text: str, terms: Tuple[str, ...]) -> List[str]:
    hits: List[str] = []
    for term in terms:
        if term in normalized_text:
            hits.append(term)
    return hits


def _risk_hits(normalized_text: str, terms: Tuple[str, ...]) -> List[str]:
    hits: List[str] = []
    for term in terms:
        if term not in normalized_text:
            continue
        if term == "deploy" and any(pattern in normalized_text for pattern in NEGATED_RISK_PATTERNS):
            continue
        hits.append(term)
    return hits


def _detect_project_type(normalized_text: str, metadata: Optional[Dict[str, Any]]) -> Tuple[str, List[str]]:
    evidence: List[str] = []
    if metadata:
        for key in ("project_profile", "bootstrap_template"):
            value = str(metadata.get(key, "")).strip()
            if value in PROJECT_TYPE_KEYWORDS:
                evidence.append(f"{key}={value}")
                return value, evidence

    scores: Dict[str, int] = {}
    for project_type, keywords in PROJECT_TYPE_KEYWORDS.items():
        hits = [term for term in keywords if term in normalized_text]
        if hits:
            scores[project_type] = len(hits)
            evidence.append(f"{project_type}_hits={hits}")

    if not scores:
        return "unknown", ["no_project_type_signal"]
    best = max(scores, key=scores.get)
    return best, evidence


def _detect_objective(metadata: Optional[Dict[str, Any]], surface: Dict[str, str]) -> Tuple[Optional[str], List[str]]:
    evidence: List[str] = []
    if metadata:
        goal = str(metadata.get("project_goal", "")).strip()
        if goal:
            evidence.append("metadata.project_goal")
            return goal, evidence

    for rel in ("index.html", "README.md", "docs/architecture.md", "AGENTS.md"):
        text = surface.get(rel, "")
        heading = _extract_first_heading(text)
        sentence = _extract_first_meaningful_sentence(text)
        if heading and sentence:
            heading_n = heading.lower().strip(" .:")
            sentence_n = sentence.lower().strip(" .:")
            objective = sentence if heading_n in sentence_n else f"{heading}: {sentence}"
            evidence.append(f"{rel}:heading+sentence")
            return objective[:240], evidence
        if sentence:
            evidence.append(f"{rel}:sentence")
            return sentence[:240], evidence
    return None, ["no_objective_signal"]


def _detect_risk_level(project_type: str, normalized_text: str) -> Tuple[str, List[str]]:
    evidence: List[str] = []
    high_hits = _risk_hits(normalized_text, HIGH_RISK_TERMS)
    medium_hits = _risk_hits(normalized_text, MEDIUM_RISK_TERMS)

    if project_type in HIGH_COMPLEXITY_TYPES:
        evidence.append(f"type_high_risk={project_type}")
    if high_hits:
        evidence.append(f"high_risk_terms={high_hits}")
    if project_type == "internal_tool" and high_hits and set(high_hits).issubset({"production"}):
        return "medium", evidence + ["internal_tool_production_only"]
    if project_type in HIGH_COMPLEXITY_TYPES or high_hits:
        return "high", evidence or ["high_risk_by_type"]

    if project_type in MEDIUM_COMPLEXITY_TYPES:
        evidence.append(f"type_medium_risk={project_type}")
    if medium_hits:
        evidence.append(f"medium_risk_terms={medium_hits}")
    if project_type in MEDIUM_COMPLEXITY_TYPES or medium_hits:
        return "medium", evidence or ["medium_risk_by_type"]
    return "low", evidence or ["low_risk_surface"]


def _detect_complexity(project_type: str, surface: Dict[str, str], normalized_text: str) -> Tuple[str, List[str]]:
    evidence: List[str] = []
    surface_count = len([value for value in surface.values() if value.strip()])
    if project_type in HIGH_COMPLEXITY_TYPES:
        evidence.append(f"type_high_complexity={project_type}")
        return "high", evidence
    if project_type in MEDIUM_COMPLEXITY_TYPES:
        evidence.append(f"type_medium_complexity={project_type}")
    if surface_count >= 3:
        evidence.append(f"surface_files={surface_count}")
    if any(term in normalized_text for term in ("workflow", "governance", "certify", "audit")):
        evidence.append("workflow_governance_signals")
    if project_type in MEDIUM_COMPLEXITY_TYPES or surface_count >= 3:
        return "medium", evidence or ["medium_complexity_surface"]
    return "low", evidence or ["low_complexity_surface"]


def _detect_missing_definition(normalized_text: str, objective: Optional[str], project_type: str) -> List[str]:
    missing: List[str] = []
    if project_type == "unknown":
        missing.append("project_type_unclear")
    if not objective:
        missing.append("objective_missing")
    if not _keyword_hits(normalized_text, AUDIENCE_TERMS):
        missing.append("audience_missing_or_implicit")
    if not _keyword_hits(normalized_text, SCOPE_TERMS):
        missing.append("scope_or_constraints_missing")
    return missing


def _clarity_score(project_type: str, objective: Optional[str], missing_definition: List[str]) -> int:
    score = 4
    if project_type != "unknown":
        score += 2
    if objective:
        score += 2
    score -= min(len(missing_definition), 3)
    return max(0, min(score, 10))


def analyze_project_intent(
    *,
    project: Optional[Path] = None,
    brief: Optional[str] = None,
) -> Dict[str, Any]:
    metadata: Optional[Dict[str, Any]] = None
    surface: Dict[str, str] = {}
    evidence: List[str] = []

    if project is None and not brief:
        return {
            "status": "skipped",
            "reason": "missing_project_or_brief",
            "timestamp": _utc_now_iso(),
        }

    project_path = None
    raw_text = ""
    if project is not None:
        project = project.resolve()
        project_path = str(project)
        metadata, metadata_error = _load_project_metadata(project)
        surface = _collect_project_text(project)
        if metadata_error:
            evidence.append(metadata_error)
        raw_text = "\n".join(surface.values())
        if metadata:
            raw_text += "\n" + json.dumps(metadata, ensure_ascii=False)
    else:
        raw_text = brief or ""

    normalized_text = _normalize(raw_text)
    project_type, type_evidence = _detect_project_type(normalized_text, metadata)
    objective, objective_evidence = _detect_objective(metadata, surface) if project is not None else (_extract_first_meaningful_sentence(brief or ""), ["brief_sentence"] if brief else ["no_brief"])
    risk_level, risk_evidence = _detect_risk_level(project_type, normalized_text)
    complexity, complexity_evidence = _detect_complexity(project_type, surface, normalized_text)
    missing_definition = _detect_missing_definition(normalized_text, objective, project_type)
    clarity_score = _clarity_score(project_type, objective, missing_definition)

    evidence.extend(type_evidence)
    evidence.extend(objective_evidence)
    evidence.extend(risk_evidence)
    evidence.extend(complexity_evidence)

    reasoning: List[str] = []
    if project_type != "unknown":
        reasoning.append(f"Project type resolves as `{project_type}` from metadata or repeated surface keywords.")
    else:
        reasoning.append("Project type remains unclear because the current brief or surface does not expose stable type signals.")
    if objective:
        reasoning.append("A concrete project objective could be extracted from the current brief or project surface.")
    else:
        reasoning.append("The current brief or project surface does not state a concrete project objective yet.")
    reasoning.append(f"Risk is `{risk_level}` and complexity is `{complexity}` using project-type and surface-signal heuristics, not hidden runtime behavior.")

    return {
        "status": "ready" if not missing_definition else "needs_input",
        "project_path": project_path,
        "project_type": project_type,
        "objective": objective,
        "risk_level": risk_level,
        "complexity": complexity,
        "clarity_score": clarity_score,
        "missing_definition": missing_definition,
        "evidence": evidence[:12],
        "reasoning": reasoning,
        "timestamp": _utc_now_iso(),
    }


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(add_help=True)
    parser.add_argument("--project", default=None, help="Derived project path to inspect.")
    parser.add_argument("--brief", default=None, help="Free-text brief to analyze when no project path is available.")
    args = parser.parse_args(argv)

    project = Path(args.project).resolve() if args.project else None
    result = analyze_project_intent(project=project, brief=args.brief)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
