import json
import shutil
from pathlib import Path
from uuid import uuid4

from tools.feedback_analyzer import analyze_feedback


ROOT = Path(r"C:\Proyectos\Codex-Atlas")
PROJECT = Path(r"C:\Proyectos\CodexAtlas-Web")
TESTS_DIR = Path(__file__).resolve().parent


def test_feedback_analyzer_calculates_rates_and_last_decision():
    tmp_dir = TESTS_DIR / f"_tmp_feedback_analyzer_case_1_{uuid4().hex}"
    shutil.rmtree(tmp_dir, ignore_errors=True)
    tmp_dir.mkdir(parents=True, exist_ok=True)
    try:
        log_path = tmp_dir / "decision_feedback.jsonl"
        entries = [
            {
                "project_path": str(PROJECT.resolve()),
                "recommendation_id": "hero_copy",
                "action": "Tighten hero copy",
                "decision": "accepted",
                "reason": "Approved.",
                "timestamp": "2026-05-01T00:00:00+00:00",
                "source": "quality_gate_report",
            },
            {
                "project_path": str(PROJECT.resolve()),
                "recommendation_id": "hero_copy",
                "action": "Tighten hero copy",
                "decision": "ignored",
                "reason": "Skipped.",
                "timestamp": "2026-05-02T00:00:00+00:00",
                "source": "manual",
            },
        ]
        log_path.write_text("\n".join(json.dumps(item) for item in entries) + "\n", encoding="utf-8")

        result = analyze_feedback(root=ROOT, project_path=PROJECT, log_path=log_path)

        assert result["status"] == "ok"
        assert result["analyzed_entries"] == 2
        feedback = result["action_feedback"][0]
        assert feedback["action"] == "Tighten hero copy"
        assert feedback["acceptance_rate"] == 0.5
        assert feedback["ignore_rate"] == 0.5
        assert feedback["last_decision"] == "ignored"
    finally:
        shutil.rmtree(tmp_dir, ignore_errors=True)


def test_feedback_analyzer_detects_repeated_ignore_pattern():
    tmp_dir = TESTS_DIR / f"_tmp_feedback_analyzer_case_2_{uuid4().hex}"
    shutil.rmtree(tmp_dir, ignore_errors=True)
    tmp_dir.mkdir(parents=True, exist_ok=True)
    try:
        log_path = tmp_dir / "decision_feedback.jsonl"
        entries = [
            {
                "project_path": str(PROJECT.resolve()),
                "recommendation_id": "layout_density",
                "action": "Trim dense sections",
                "decision": "ignored",
                "reason": "Not now.",
                "timestamp": "2026-05-01T00:00:00+00:00",
                "source": "quality_gate_report",
            },
            {
                "project_path": str(PROJECT.resolve()),
                "recommendation_id": "layout_density",
                "action": "Trim dense sections",
                "decision": "ignored",
                "reason": "Still not now.",
                "timestamp": "2026-05-02T00:00:00+00:00",
                "source": "priority_engine",
            },
        ]
        log_path.write_text("\n".join(json.dumps(item) for item in entries) + "\n", encoding="utf-8")

        result = analyze_feedback(root=ROOT, project_path=PROJECT, log_path=log_path)

        assert result["detected_patterns"]
        assert "repeatedly ignored" in result["detected_patterns"][0]["pattern"]
    finally:
        shutil.rmtree(tmp_dir, ignore_errors=True)
