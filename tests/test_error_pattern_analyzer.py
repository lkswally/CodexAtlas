import json
import os
import shutil
from pathlib import Path
from uuid import uuid4

os.environ["ATLAS_DISABLE_EVENT_LOGS"] = "1"

from tools.error_pattern_analyzer import analyze_error_patterns


def _write_jsonl(path: Path, records):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for record in records:
            handle.write(json.dumps(record) + "\n")


def test_error_pattern_analyzer_detects_repeated_ignored_actions_and_mcp_blockers():
    root = Path(__file__).resolve().parent / f"_tmp_error_patterns_case_{uuid4().hex}"
    shutil.rmtree(root, ignore_errors=True)
    root.mkdir(parents=True, exist_ok=True)
    try:
        _write_jsonl(
            root / "memory" / "decision_feedback.jsonl",
            [
                {"project_path": "C:/fake", "action": "Trim dense sections", "decision": "ignored"},
                {"project_path": "C:/fake", "action": "Trim dense sections", "decision": "ignored"},
            ],
        )
        _write_jsonl(
            root / "memory" / "mcp_events.jsonl",
            [
                {"state": "blocked", "cli_error": "[WinError 5] Access is denied"},
                {"state": "blocked", "cli_error": "[WinError 5] Access is denied"},
            ],
        )
        _write_jsonl(root / "memory" / "routing_log.jsonl", [])
        _write_jsonl(root / "memory" / "governance_events.jsonl", [])
        result = analyze_error_patterns(root=root)
    finally:
        shutil.rmtree(root, ignore_errors=True)

    assert result["status"] == "ok"
    assert result["patterns"]
    assert any("repeatedly ignored" in item["pattern"].lower() for item in result["patterns"])
    assert any("access is denied" in " ".join(item["evidence"]).lower() for item in result["patterns"])


def test_error_pattern_analyzer_reports_no_recurrent_pattern_when_logs_are_clean():
    root = Path(__file__).resolve().parent / f"_tmp_error_patterns_clean_case_{uuid4().hex}"
    shutil.rmtree(root, ignore_errors=True)
    root.mkdir(parents=True, exist_ok=True)
    try:
        _write_jsonl(root / "memory" / "decision_feedback.jsonl", [])
        _write_jsonl(root / "memory" / "mcp_events.jsonl", [])
        _write_jsonl(root / "memory" / "routing_log.jsonl", [])
        _write_jsonl(root / "memory" / "governance_events.jsonl", [])
        result = analyze_error_patterns(root=root)
    finally:
        shutil.rmtree(root, ignore_errors=True)

    assert result["status"] == "ok"
    assert result["patterns"] == []
    assert result["should_create_issue"] is False
