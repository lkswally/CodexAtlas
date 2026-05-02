from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple


DEFAULT_ROOT = Path(__file__).resolve().parents[1]
PHASE_PLAYBOOK_PATH = Path("config") / "phase_playbook.json"
PHASES = ("idea", "planning", "bootstrap", "build", "audit", "certified")
PHASE_INDEX = {phase: index for index, phase in enumerate(PHASES)}
BOOTSTRAP_DIRS = {"docs", "memory", "workflows", "policies", "tools"}
BOOTSTRAP_FILES = {".atlas-project.json", "README.md", "AGENTS.md"}
DISPATCH_EVENT_TYPE = "dispatcher_command"
ROUTING_LOG_PATH = Path("memory") / "routing_log.jsonl"
GOVERNANCE_EVENTS_PATH = Path("memory") / "governance_events.jsonl"


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _read_json(path: Path) -> Dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def _load_phase_playbook(root: Path) -> Dict[str, Dict[str, List[str]]]:
    path = root / PHASE_PLAYBOOK_PATH
    data = _read_json(path)
    if not isinstance(data, dict):
        return {}
    normalized: Dict[str, Dict[str, List[str]]] = {}
    for phase, item in data.items():
        if not isinstance(item, dict):
            continue
        normalized[str(phase).strip()] = {
            "allowed_commands": [str(value).strip() for value in item.get("allowed_commands", []) if str(value).strip()],
            "recommended_actions": [str(value).strip() for value in item.get("recommended_actions", []) if str(value).strip()],
            "common_mistakes": [str(value).strip() for value in item.get("common_mistakes", []) if str(value).strip()],
        }
    return normalized


def _iter_jsonl(path: Path) -> Iterable[Dict[str, Any]]:
    if not path.exists():
        return []

    def _generator() -> Iterable[Dict[str, Any]]:
        for raw_line in path.read_text(encoding="utf-8-sig").splitlines():
            line = raw_line.strip()
            if not line:
                continue
            try:
                record = json.loads(line)
            except Exception:
                continue
            if isinstance(record, dict):
                yield record

    return _generator()


def _metadata_path(project: Path) -> Path:
    return project / ".atlas-project.json"


def _load_metadata(project: Path) -> Tuple[Optional[Dict[str, Any]], Optional[str]]:
    path = _metadata_path(project)
    if not path.exists():
        return None, "missing_project_metadata"
    try:
        data = _read_json(path)
    except Exception as exc:
        return None, f"invalid_project_metadata:{exc}"
    if not isinstance(data, dict):
        return None, "project_metadata_not_object"
    return data, None


def _has_bootstrap_scaffold(project: Path) -> Tuple[bool, List[str]]:
    missing: List[str] = []
    for rel in sorted(BOOTSTRAP_FILES):
        if not (project / rel).exists():
            missing.append(rel)
    for rel in sorted(BOOTSTRAP_DIRS):
        path = project / rel
        if not path.exists() or not path.is_dir():
            missing.append(f"{rel}/")
    return (not missing), missing


def _runtime_surface_signals(project: Path) -> List[str]:
    signals: List[str] = []
    if not project.exists() or not project.is_dir():
        return signals

    reserved_files = BOOTSTRAP_FILES | {".gitignore"}
    reserved_dirs = BOOTSTRAP_DIRS | {".git", "__pycache__"}
    runtime_suffixes = {".html", ".css", ".js", ".jsx", ".ts", ".tsx", ".json", ".md"}

    for path in sorted(project.iterdir(), key=lambda item: item.name.lower()):
        if path.name in reserved_files or path.name in reserved_dirs:
            continue
        if path.is_file() and path.suffix.lower() in runtime_suffixes:
            signals.append(f"runtime_file:{path.name}")
        elif path.is_dir():
            signals.append(f"runtime_dir:{path.name}")
    return signals


def _phase_from_metadata_status(metadata: Dict[str, Any]) -> Optional[str]:
    status = str(metadata.get("status", "")).strip().lower()
    mapping = {
        "idea": "idea",
        "planning": "planning",
        "bootstrapped": "bootstrap",
        "bootstrap": "bootstrap",
        "build": "build",
        "built": "build",
        "audited": "audit",
        "audit": "audit",
        "certified": "certified",
    }
    return mapping.get(status)


def _dispatcher_command_events(root: Path, project: Path) -> List[Dict[str, Any]]:
    project_s = str(project.resolve())
    entries: List[Dict[str, Any]] = []
    for record in _iter_jsonl(root / ROUTING_LOG_PATH):
        if str(record.get("event_type", "")).strip() != DISPATCH_EVENT_TYPE:
            continue
        if str(record.get("project", "")).strip() != project_s:
            continue
        entries.append(record)
    return entries


def _governance_project_events(root: Path, project: Path) -> List[Dict[str, Any]]:
    project_s = str(project.resolve())
    entries: List[Dict[str, Any]] = []
    for record in _iter_jsonl(root / GOVERNANCE_EVENTS_PATH):
        if str(record.get("project", "")).strip() != project_s:
            continue
        entries.append(record)
    return entries


def _evidence_for_phase_from_logs(root: Path, project: Path) -> Tuple[Optional[str], List[str], str]:
    evidence: List[str] = []
    dispatcher_events = _dispatcher_command_events(root, project)
    governance_events = _governance_project_events(root, project)

    successful_certify = [
        item for item in dispatcher_events
        if item.get("command_id") == "certify-project" and bool(item.get("ok"))
    ]
    if successful_certify:
        latest = successful_certify[-1]
        evidence.append(f"dispatcher_command:certify-project:{latest.get('timestamp')}")
        return "certified", evidence, "high"

    successful_audit = [
        item for item in dispatcher_events
        if item.get("command_id") == "audit-repo" and bool(item.get("ok"))
    ]
    if successful_audit:
        latest = successful_audit[-1]
        evidence.append(f"dispatcher_command:audit-repo:{latest.get('timestamp')}")
        return "audit", evidence, "high"

    successful_governance = [item for item in governance_events if bool(item.get("ok"))]
    if successful_governance:
        latest = successful_governance[-1]
        evidence.append(f"governance_project_event:{latest.get('timestamp')}")
        return "audit", evidence, "medium"

    return None, evidence, "low"


def _max_phase(*phases: Optional[str]) -> Optional[str]:
    valid = [phase for phase in phases if phase in PHASE_INDEX]
    if not valid:
        return None
    return max(valid, key=lambda phase: PHASE_INDEX[phase])


def _next_valid_phases(current_phase: str) -> List[str]:
    transitions = {
        "idea": ["planning", "bootstrap"],
        "planning": ["bootstrap"],
        "bootstrap": ["build", "audit"],
        "build": ["audit"],
        "audit": ["certified", "build"],
        "certified": ["build", "audit"],
    }
    return transitions.get(current_phase, [])


def _command_allowed(current_phase: str, command_id: str) -> bool:
    if command_id == "project-bootstrap":
        return current_phase in {"idea", "planning"}
    if command_id == "audit-repo":
        return PHASE_INDEX[current_phase] >= PHASE_INDEX["bootstrap"]
    if command_id == "certify-project":
        return PHASE_INDEX[current_phase] >= PHASE_INDEX["audit"]
    return True


def _blocked_actions(current_phase: str) -> List[str]:
    commands = ("project-bootstrap", "audit-repo", "certify-project")
    return [command_id for command_id in commands if not _command_allowed(current_phase, command_id)]


def _fallback_recommended_actions(current_phase: str) -> List[str]:
    mapping = {
        "idea": [
            "Define the project goal, output_dir and safety boundaries before bootstrapping.",
            "Move to planning with an explicit brief and project type.",
        ],
        "planning": [
            "Run project-bootstrap with an explicit output_dir once the brief is stable.",
            "Keep the factory and derived project separated from the start.",
        ],
        "bootstrap": [
            "Implement the first runtime surface or public entrypoint before broader review.",
            "Run audit-repo when the scaffold and metadata are in place.",
        ],
        "build": [
            "Run audit-repo to validate structure and boundaries before certification.",
            "Reduce drift before calling the project ready for handoff.",
        ],
        "audit": [
            "Run certify-project once audit findings are resolved.",
            "Use quality-gate-report for a single readiness view before handoff.",
        ],
        "certified": [
            "Keep changes scoped and rerun audit/certify after material edits.",
            "Use quality-gate-report before public handoff or broader review.",
        ],
    }
    return mapping.get(current_phase, ["Review the project state before taking the next action."])


def _phase_guidance(root: Path, current_phase: str) -> Dict[str, List[str]]:
    playbook = _load_phase_playbook(root)
    phase_data = playbook.get(current_phase, {})
    allowed_commands = list(phase_data.get("allowed_commands", []))
    recommended_actions = list(phase_data.get("recommended_actions", []))
    common_mistakes = list(phase_data.get("common_mistakes", []))
    if not recommended_actions:
        recommended_actions = _fallback_recommended_actions(current_phase)
    return {
        "allowed_commands": allowed_commands,
        "recommended_actions": recommended_actions,
        "common_mistakes": common_mistakes,
    }


def resolve_project_phase(root: Path, project: Path) -> Dict[str, Any]:
    root = root.resolve()
    project = project.resolve()
    evidence: List[str] = []

    if not project.exists():
        current_phase = "idea"
        confidence = "high"
        evidence.append("project_root_missing")
    elif not project.is_dir():
        current_phase = "planning"
        confidence = "high"
        evidence.append("project_root_not_directory")
    else:
        metadata, metadata_error = _load_metadata(project)
        if metadata_error:
            current_phase = "planning"
            confidence = "medium"
            evidence.append(metadata_error)
        else:
            scaffold_ok, missing_scaffold = _has_bootstrap_scaffold(project)
            metadata_phase = _phase_from_metadata_status(metadata or {})
            log_phase, log_evidence, log_confidence = _evidence_for_phase_from_logs(root, project)
            evidence.extend(log_evidence)

            if not scaffold_ok:
                current_phase = "planning"
                confidence = "medium"
                evidence.append(f"incomplete_bootstrap_scaffold:{','.join(missing_scaffold)}")
            else:
                runtime_signals = _runtime_surface_signals(project)
                heuristic_phase = "build" if runtime_signals else "bootstrap"
                evidence.append(f"bootstrap_scaffold_ok:{','.join(sorted(BOOTSTRAP_DIRS))}")
                if runtime_signals:
                    evidence.extend(runtime_signals[:5])

                current_phase = _max_phase(metadata_phase, log_phase, heuristic_phase) or heuristic_phase
                if log_phase:
                    confidence = log_confidence
                elif metadata_phase:
                    confidence = "high"
                elif runtime_signals:
                    confidence = "medium"
                else:
                    confidence = "high"

    guidance = _phase_guidance(root, current_phase)
    return {
        "status": "ok",
        "project_path": str(project),
        "current_phase": current_phase,
        "confidence": confidence,
        "allowed_commands": guidance["allowed_commands"],
        "next_valid_phases": _next_valid_phases(current_phase),
        "recommended_actions": guidance["recommended_actions"],
        "recommended_next_steps": guidance["recommended_actions"],
        "common_mistakes": guidance["common_mistakes"],
        "blocked_actions": _blocked_actions(current_phase),
        "evidence": evidence,
        "timestamp": _utc_now_iso(),
    }


def build_project_phase_report(root: Path, project: Path) -> Dict[str, Any]:
    return resolve_project_phase(root, project)


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(add_help=True)
    parser.add_argument("--root", default=None, help="Atlas root to use. Defaults to this repository root.")
    parser.add_argument("--project", required=True, help="Derived project path to inspect.")
    args = parser.parse_args(argv)

    root = Path(args.root).resolve() if args.root else DEFAULT_ROOT
    project = Path(args.project).resolve()
    report = build_project_phase_report(root, project)
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
