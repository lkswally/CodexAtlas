import os
import shutil
import uuid
from pathlib import Path

os.environ["ATLAS_DISABLE_EVENT_LOGS"] = "1"

from tests._support_paths import ATLAS_ROOT
from tools.operational_parity_readiness import build_operational_parity_report


TMP_ROOT = ATLAS_ROOT / "tests" / "_tmp_operational_parity"


def _make_case_dir(name: str) -> Path:
    case_root = TMP_ROOT / f"{name}_{uuid.uuid4().hex}"
    case_root.mkdir(parents=True, exist_ok=True)
    return case_root


def test_operational_parity_report_is_ready_for_atlas_root():
    result = build_operational_parity_report(ATLAS_ROOT)
    assert result["status"] == "ready"
    assert result["adaptation_mode"] == "codex_native_advisory_readiness"
    assert result["advisory_only"] is True
    assert result["components"]["atlas_handoff_envelope"]["status"] == "ready"
    assert result["components"]["evidence_index"]["status"] == "ready"
    assert result["components"]["delegation_stop_rules"]["status"] == "ready"
    assert result["components"]["context_resume_protocol"]["status"] == "ready"
    assert result["components"]["manual_quality_hook_bundle"]["status"] == "ready"
    assert result["blockers"] == []
    assert "python tools\\atlas_dispatcher.py operational-parity-report" in result["manual_quality_hook_bundle"]


def test_operational_parity_blocks_claude_runtime_artifacts():
    case_root = _make_case_dir("claude_runtime")
    try:
        for relative in [
            "docs/operational_parity_codex_native.md",
            "policies/operational_parity_policy.md",
            "tools/atlas_dispatcher.py",
            "tools/operational_parity_readiness.py",
            "memory/context_refresh_protocol.md",
            "memory/breadcrumbs.md",
            "commands/atomic_command_registry.json",
        ]:
            path = case_root / relative
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text("placeholder", encoding="utf-8")
        (case_root / "CLAUDE.md").write_text("forbidden", encoding="utf-8")

        result = build_operational_parity_report(case_root)

        assert result["status"] == "blocked"
        assert result["blockers"][0]["code"] == "claude_runtime_artifacts_detected"
        assert "CLAUDE.md" in result["blockers"][0]["evidence"]
    finally:
        shutil.rmtree(case_root, ignore_errors=True)
