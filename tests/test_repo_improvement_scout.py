import os
import shutil
from pathlib import Path
from uuid import uuid4

os.environ["ATLAS_DISABLE_EVENT_LOGS"] = "1"

from tools.repo_improvement_scout import scout_reference_repo


def test_repo_improvement_scout_requires_reference_when_missing():
    result = scout_reference_repo(source=Path(r"C:\missing\claude-vibecoding"))
    assert result["status"] == "needs_reference"


def test_repo_improvement_scout_returns_matrix_for_valid_local_reference():
    root = Path(__file__).resolve().parent / f"_tmp_repo_scout_case_{uuid4().hex}"
    shutil.rmtree(root, ignore_errors=True)
    root.mkdir(parents=True, exist_ok=True)
    try:
        for name in ("README.md", "CLAUDE.md", "UPGRADE_LOG.md"):
            (root / name).write_text("placeholder", encoding="utf-8")
        for name in ("agents", "docs"):
            (root / name).mkdir(exist_ok=True)
        result = scout_reference_repo(source=root)
    finally:
        shutil.rmtree(root, ignore_errors=True)

    assert result["status"] == "ok"
    assert result["patterns"]
    assert result["summary"]["adaptar_ahora"] >= 1
