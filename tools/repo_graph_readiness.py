from __future__ import annotations

import argparse
import json
import os
import shutil
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional


DEFAULT_ROOT = Path(__file__).resolve().parents[1]
RULES_PATH = Path("config/repo_graph_readiness_rules.json")
SKIP_DIR_NAMES = {
    ".git",
    ".hg",
    ".svn",
    ".idea",
    ".vscode",
    "node_modules",
    ".venv",
    "venv",
    "__pycache__",
    "dist",
    "build",
    "coverage",
    ".next",
    ".turbo",
    ".pytest_cache",
}
SOURCE_SCAN_LIMIT_BYTES = 256_000


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _read_json(path: Path) -> Dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def load_repo_graph_readiness_rules(root: Path = DEFAULT_ROOT) -> Dict[str, Any]:
    return _read_json((root / RULES_PATH).resolve())


def _normalize(value: str) -> str:
    return " ".join(str(value or "").strip().lower().split())


def _safe_walk_files(root: Path) -> Iterable[Path]:
    for current_root, dirnames, filenames in os.walk(root, topdown=True, onerror=lambda exc: None):
        dirnames[:] = [
            dirname
            for dirname in dirnames
            if dirname not in SKIP_DIR_NAMES and not dirname.startswith("pytest-cache-files-")
        ]
        current = Path(current_root)
        for filename in filenames:
            yield current / filename


def _classify_project_size(file_count: int, thresholds: Dict[str, Any]) -> str:
    small_max = int(thresholds.get("small_max_files", 120))
    medium_max = int(thresholds.get("medium_max_files", 700))
    if file_count <= small_max:
        return "small"
    if file_count <= medium_max:
        return "medium"
    return "large"


def _detect_languages(files: List[Path], source_extensions: Dict[str, str]) -> List[str]:
    languages: List[str] = []
    seen: set[str] = set()
    for file_path in files:
        language = source_extensions.get(file_path.suffix.lower())
        if language and language not in seen:
            seen.add(language)
            languages.append(language)
    return languages


def _detect_route_signals(project: Path, files: List[Path], rules: Dict[str, Any]) -> List[str]:
    route_rules = rules.get("route_detection", {})
    path_signals = [str(item).strip().lower() for item in route_rules.get("path_signals", []) if str(item).strip()]
    file_signals = [str(item).strip().lower() for item in route_rules.get("file_signals", []) if str(item).strip()]
    content_signals = [str(item).strip().lower() for item in route_rules.get("content_signals", []) if str(item).strip()]

    hits: List[str] = []
    for file_path in files:
        relative = file_path.relative_to(project)
        relative_text = str(relative).replace("\\", "/").lower()
        path_parts = {part.lower() for part in relative.parts}
        if any(signal in path_parts for signal in path_signals):
            hits.append(f"path:{relative_text}")
            continue
        if file_path.name.lower() in file_signals:
            hits.append(f"file:{relative_text}")
            continue
        if any(part.lower().startswith("test") for part in relative.parts):
            continue
        if file_path.suffix.lower() not in {".py", ".js", ".jsx", ".ts", ".tsx", ".rb", ".php", ".java", ".go", ".rs"}:
            continue
        try:
            if file_path.stat().st_size > SOURCE_SCAN_LIMIT_BYTES:
                continue
            content = file_path.read_text(encoding="utf-8-sig", errors="ignore").lower()
        except OSError:
            continue
        if any(signal in content for signal in content_signals):
            hits.append(f"content:{relative_text}")
    return hits[:20]


def _detect_multi_module_signals(project: Path, files: List[Path], rules: Dict[str, Any]) -> List[str]:
    markers = [str(item).strip().lower() for item in rules.get("multi_module_markers", []) if str(item).strip()]
    top_level_dirs = {path.relative_to(project).parts[0].lower() for path in files if len(path.relative_to(project).parts) > 1}
    hits = [marker for marker in markers if marker in top_level_dirs]

    manifest_names = {
        "package.json",
        "pyproject.toml",
        "Cargo.toml",
        "go.mod",
        "pom.xml",
        "build.gradle",
        "build.gradle.kts",
    }
    manifest_count = sum(1 for path in files if path.name in manifest_names)
    if manifest_count > 1:
        hits.append(f"manifests:{manifest_count}")
    return hits


def _infer_task_fit(task: str, rules: Dict[str, Any]) -> tuple[str, List[str]]:
    normalized_task = _normalize(task)
    signals = rules.get("task_fit_signals", {})
    for band in ("high", "medium", "low"):
        hits = [term for term in signals.get(band, []) if _normalize(term) and _normalize(term) in normalized_task]
        if hits:
            return band, [f"{band}_task_fit_hits={hits}"]
    return "low", ["task_fit_not_explicit"]


def _detect_codegraph_installation(project: Path) -> Dict[str, Any]:
    reasons: List[str] = []
    detected = False

    binary_path = shutil.which("codegraph")
    if binary_path:
        detected = True
        reasons.append("codegraph_binary_on_path")

    for candidate in (
        project / "node_modules" / ".bin" / "codegraph",
        project / "node_modules" / ".bin" / "codegraph.cmd",
    ):
        if candidate.exists():
            detected = True
            reasons.append(f"local_binary:{candidate.name}")
            break

    return {"detected": detected, "reasons": reasons}


def assess_repo_graph_readiness(
    *,
    root: Path,
    project: Optional[Path] = None,
    task: str = "",
) -> Dict[str, Any]:
    root = root.resolve()
    project = (project or root).resolve()
    rules = load_repo_graph_readiness_rules(root)

    files = [path for path in _safe_walk_files(project) if path.is_file()]
    file_count = len(files)
    project_size = _classify_project_size(file_count, rules.get("size_thresholds", {}))
    languages = _detect_languages(files, rules.get("source_extensions", {}))
    route_signals = _detect_route_signals(project, files, rules)
    multi_module_signals = _detect_multi_module_signals(project, files, rules)
    task_fit, task_fit_evidence = _infer_task_fit(task, rules)

    codegraph_dir = project / ".codegraph"
    codegraph_initialized = codegraph_dir.exists() and codegraph_dir.is_dir()
    install_detection = _detect_codegraph_installation(project)
    codegraph_detected = bool(install_detection["detected"] or codegraph_initialized)

    blocked_reasons: List[str] = []
    watchlist: List[str] = []
    risks: List[str] = []
    why_parts: List[str] = []

    if project_size == "small":
        blocked_reasons.append("repo_small_enough_for_direct_exploration")
    if task_fit == "low":
        blocked_reasons.append("task_does_not_require_deep_navigation")

    normalized_task = _normalize(task)
    for term in rules.get("watchlist_terms", []):
        normalized_term = _normalize(str(term))
        if normalized_term and normalized_term in normalized_task:
            watchlist.append(f"runtime_term:{normalized_term}")

    if codegraph_initialized:
        why_parts.append("existing_.codegraph_detected")
    if install_detection["reasons"]:
        why_parts.extend(install_detection["reasons"])
    if route_signals:
        why_parts.append("framework_route_signals_present")
    if multi_module_signals:
        why_parts.append("multi_module_signals_present")
    why_parts.extend(task_fit_evidence)

    if not codegraph_initialized:
        watchlist.append("graph_not_initialized")
    if not codegraph_detected:
        watchlist.append("codegraph_not_detected_locally")
    if project_size in {"medium", "large"}:
        risks.append("brute_force_exploration_cost_risk")
    if multi_module_signals:
        risks.append("cross_module_navigation_risk")
    if route_signals:
        risks.append("route_trace_complexity_risk")
    if watchlist:
        risks.append("graph_runtime_not_approved")

    repo_graph_recommended = (
        project_size in {"medium", "large"}
        and task_fit in {"medium", "high"}
        and "repo_small_enough_for_direct_exploration" not in blocked_reasons
        and "task_does_not_require_deep_navigation" not in blocked_reasons
    )
    safe_to_initialize_manually = bool(repo_graph_recommended and "runtime_term:mcp" not in watchlist)

    if repo_graph_recommended:
        reason = "Repo structure and task shape suggest that graph-first exploration could reduce file-by-file discovery overhead."
    elif blocked_reasons:
        reason = "Direct local exploration remains cheaper and simpler than adding graph tooling for this repo/task."
    else:
        reason = "Current evidence does not justify graph initialization yet."

    manual_steps: List[str] = []
    if repo_graph_recommended:
        manual_steps.extend(rules.get("manual_steps", {}).get("recommended", []))
    if watchlist:
        manual_steps.extend(rules.get("manual_steps", {}).get("watchlist", []))
    manual_steps = list(dict.fromkeys(str(step).strip() for step in manual_steps if str(step).strip()))

    return {
        "status": "ok",
        "advisory_only": bool(rules.get("advisory_only", True)),
        "repo_graph_recommended": repo_graph_recommended,
        "reason": reason,
        "project_size": project_size,
        "file_count": file_count,
        "languages_detected": languages,
        "task_fit": task_fit,
        "route_signals": route_signals,
        "multi_module_signals": multi_module_signals,
        "codegraph_detected": codegraph_detected,
        "codegraph_initialized": codegraph_initialized,
        "safe_to_initialize_manually": safe_to_initialize_manually,
        "manual_steps": manual_steps,
        "blocked_reasons": list(dict.fromkeys(blocked_reasons)),
        "watchlist": list(dict.fromkeys(watchlist)),
        "risks": list(dict.fromkeys(risks)),
        "why": "; ".join(why_parts) or "repo_graph_not_needed_yet",
        "timestamp": _utc_now_iso(),
    }


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(add_help=True)
    parser.add_argument("--root", default=None, help="Atlas root to use.")
    parser.add_argument("--project", default=None, help="Target project path to assess.")
    parser.add_argument("--task", default="", help="Optional task text to estimate graph fit.")
    args = parser.parse_args(argv)

    root = Path(args.root).resolve() if args.root else DEFAULT_ROOT
    project = Path(args.project).resolve() if args.project else root
    result = assess_repo_graph_readiness(root=root, project=project, task=args.task)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
