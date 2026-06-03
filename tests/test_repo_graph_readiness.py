from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

from tests._support_paths import ATLAS_ROOT, WEB_ROOT
from tools.repo_graph_readiness import assess_repo_graph_readiness


ROOT = ATLAS_ROOT
FIXTURE_ROOT = ROOT / "tests" / "fixtures" / "repo_graph"
SMALL_REPO = FIXTURE_ROOT / "small_repo"
MEDIUM_REPO = FIXTURE_ROOT / "medium_repo"


def _rules_with_thresholds(*, small_max: int, medium_max: int) -> dict:
    from tools.repo_graph_readiness import load_repo_graph_readiness_rules

    rules = load_repo_graph_readiness_rules(ROOT)
    rules["size_thresholds"] = {
        "small_max_files": small_max,
        "medium_max_files": medium_max,
    }
    return rules


def test_repo_graph_readiness_keeps_small_repo_low_value():
    result = assess_repo_graph_readiness(root=ROOT, project=SMALL_REPO, task="small fix in one file")

    assert result["status"] == "ok"
    assert result["project_size"] == "small"
    assert result["repo_graph_recommended"] is False
    assert "repo_small_enough_for_direct_exploration" in result["blocked_reasons"]


def test_repo_graph_readiness_recommends_graph_for_larger_refactor_repo():
    with patch(
        "tools.repo_graph_readiness.load_repo_graph_readiness_rules",
        return_value=_rules_with_thresholds(small_max=2, medium_max=4),
    ):
        result = assess_repo_graph_readiness(
            root=ROOT,
            project=MEDIUM_REPO,
            task="Trace callers, callees and impact analysis before a refactor across modules",
        )

    assert result["repo_graph_recommended"] is True
    assert result["project_size"] in {"medium", "large"}
    assert result["task_fit"] == "high"
    assert result["safe_to_initialize_manually"] is True
    assert result["route_signals"]
    assert result["multi_module_signals"]


def test_repo_graph_readiness_detects_initialized_codegraph_directory():
    original_exists = Path.exists
    original_is_dir = Path.is_dir

    def fake_exists(path: Path) -> bool:
        if path == MEDIUM_REPO / ".codegraph":
            return True
        return original_exists(path)

    def fake_is_dir(path: Path) -> bool:
        if path == MEDIUM_REPO / ".codegraph":
            return True
        return original_is_dir(path)

    with patch("pathlib.Path.exists", fake_exists), patch("pathlib.Path.is_dir", fake_is_dir):
        result = assess_repo_graph_readiness(root=ROOT, project=MEDIUM_REPO, task="understand routes")

    assert result["codegraph_initialized"] is True
    assert result["codegraph_detected"] is True


def test_repo_graph_readiness_detects_local_codegraph_binary_without_running_it():
    with patch("tools.repo_graph_readiness.shutil.which", return_value="C:/fake/codegraph.cmd"):
        result = assess_repo_graph_readiness(root=ROOT, project=MEDIUM_REPO, task="explore module boundaries")

    assert result["codegraph_detected"] is True
    assert "codegraph_binary_on_path" in result["why"]


def test_quality_gate_report_exposes_repo_graph_posture():
    from tools.quality_gate_report import build_quality_gate_report

    result = build_quality_gate_report(ROOT, WEB_ROOT)
    assert isinstance(result["repo_graph_posture"], dict)
    assert result["repo_graph_posture"]["advisory_only"] is True
    assert "repo_graph_recommended" in result["repo_graph_posture"]
    assert "codegraph_detected" in result["repo_graph_posture"]
