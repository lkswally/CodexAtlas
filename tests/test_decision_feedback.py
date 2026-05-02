import json
from io import StringIO
import tempfile
from contextlib import redirect_stdout
from pathlib import Path

from tools.decision_feedback import append_decision_feedback, find_relevant_feedback, main


ROOT = Path(r"C:\Proyectos\Codex-Atlas")
PROJECT = Path(r"C:\Proyectos\CodexAtlas-Web")


def test_append_decision_feedback_and_find_relevant_entries():
    with tempfile.TemporaryDirectory() as tmp_dir:
        log_path = Path(tmp_dir) / "decision_feedback.jsonl"
        append_decision_feedback(
            root=ROOT,
            project_path=PROJECT,
            recommendation_id="typography_coherence",
            action="Refine body typography",
            decision="accepted",
            reason="Approved for the next landing iteration.",
            source="quality_gate_report",
            log_path=log_path,
        )
        append_decision_feedback(
            root=ROOT,
            project_path=PROJECT,
            action="Start setup",
            decision="deferred",
            reason="Not relevant for the current iteration.",
            source="manual",
            log_path=log_path,
        )

        result = find_relevant_feedback(
            root=ROOT,
            project_path=PROJECT,
            recommendation_ids=["typography_coherence"],
            actions=["Refine body typography"],
            log_path=log_path,
        )

        assert result["status"] == "ok"
        assert result["has_relevant_feedback"] is True
        assert len(result["relevant_feedback"]) == 1
        entry = result["relevant_feedback"][0]
        assert entry["recommendation_id"] == "typography_coherence"
        assert entry["decision"] == "accepted"


def test_append_decision_feedback_requires_recommendation_or_action():
    with tempfile.TemporaryDirectory() as tmp_dir:
        log_path = Path(tmp_dir) / "decision_feedback.jsonl"
        try:
            append_decision_feedback(
                root=ROOT,
                project_path=PROJECT,
                decision="ignored",
                reason="No action selected.",
                source="manual",
                log_path=log_path,
            )
        except ValueError as exc:
            assert str(exc) == "recommendation_id_or_action_required"
        else:
            raise AssertionError("Expected ValueError when both recommendation_id and action are missing.")


def test_find_relevant_feedback_skips_blank_lines():
    with tempfile.TemporaryDirectory() as tmp_dir:
        log_path = Path(tmp_dir) / "decision_feedback.jsonl"
        log_path.write_text(
            "\n"
            + json.dumps(
                {
                    "project_path": str(PROJECT.resolve()),
                    "recommendation_id": "cta_integrity",
                    "action": None,
                    "decision": "replaced",
                    "reason": "Handled through a broader landing rewrite.",
                    "timestamp": "2026-05-01T00:00:00+00:00",
                    "source": "priority_engine",
                }
            )
            + "\n",
            encoding="utf-8",
        )

        result = find_relevant_feedback(
            root=ROOT,
            project_path=PROJECT,
            recommendation_ids=["cta_integrity"],
            log_path=log_path,
        )

        assert result["status"] == "ok"
        assert result["has_relevant_feedback"] is True
        assert result["relevant_feedback"][0]["decision"] == "replaced"


def test_decision_feedback_cli_add_writes_append_only_entry():
    with tempfile.TemporaryDirectory() as tmp_dir:
        root = Path(tmp_dir)
        buffer = StringIO()
        with redirect_stdout(buffer):
            exit_code = main(
                [
                    "add",
                    "--root",
                    str(root),
                    "--project",
                    str(PROJECT),
                    "--action",
                    "Refine CTA copy",
                    "--decision",
                    "accepted",
                    "--reason",
                    "Approved for the next pass.",
                ]
            )

        assert exit_code == 0
        payload = json.loads(buffer.getvalue())
        assert payload["status"] == "ok"
        log_path = root / "memory" / "decision_feedback.jsonl"
        lines = log_path.read_text(encoding="utf-8").splitlines()
        assert len(lines) == 1
        entry = json.loads(lines[0])
        assert entry["action"] == "Refine CTA copy"
        assert entry["decision"] == "accepted"


def test_decision_feedback_cli_list_returns_project_history_without_filters():
    with tempfile.TemporaryDirectory() as tmp_dir:
        root = Path(tmp_dir)
        log_path = root / "memory" / "decision_feedback.jsonl"
        log_path.parent.mkdir(parents=True, exist_ok=True)
        log_path.write_text(
            "\n".join(
                [
                    json.dumps(
                        {
                            "project_path": str(PROJECT.resolve()),
                            "recommendation_id": None,
                            "action": "Refine CTA copy",
                            "decision": "accepted",
                            "reason": "Approved.",
                            "timestamp": "2026-05-01T00:00:00+00:00",
                            "source": "manual",
                        }
                    ),
                    json.dumps(
                        {
                            "project_path": str(PROJECT.resolve()),
                            "recommendation_id": None,
                            "action": "Trim dense sections",
                            "decision": "deferred",
                            "reason": "Later.",
                            "timestamp": "2026-05-02T00:00:00+00:00",
                            "source": "quality_gate_report",
                        }
                    ),
                ]
            )
            + "\n",
            encoding="utf-8",
        )

        buffer = StringIO()
        with redirect_stdout(buffer):
            exit_code = main(
                [
                    "list",
                    "--root",
                    str(root),
                    "--project",
                    str(PROJECT),
                ]
            )

        assert exit_code == 0
        payload = json.loads(buffer.getvalue())
        assert payload["status"] == "ok"
        assert payload["has_relevant_feedback"] is True
        assert len(payload["relevant_feedback"]) == 2
