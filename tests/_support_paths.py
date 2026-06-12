import json
import os
import shutil
import tempfile
from pathlib import Path


ATLAS_ROOT = Path(os.environ.get("ATLAS_ROOT", Path(__file__).resolve().parent.parent)).resolve()
FALLBACK_WEB_ROOT = ATLAS_ROOT / "tests" / "fixtures" / "codexatlas_web_stub"
WEB_ROOT = Path(os.environ.get("ATLAS_WEB_ROOT") or FALLBACK_WEB_ROOT).resolve()
REYESOFT_ROOT = Path(os.environ.get("ATLAS_REYESOFT_ROOT", ATLAS_ROOT.parent / "REYESOFT")).resolve()
TEMP_ROOT = Path(
    os.environ.get("ATLAS_TEST_TEMP_ROOT", Path(tempfile.gettempdir()) / "codex-atlas-tests")
).resolve()
PLAYWRIGHT_HOME_HINT = Path(
    os.environ.get("PLAYWRIGHT_BROWSERS_PATH", Path.home() / ".cache" / "ms-playwright")
)


def create_governed_web_fixture(destination: Path) -> Path:
    project_root = destination.resolve()
    shutil.copytree(FALLBACK_WEB_ROOT, project_root)
    metadata = {
        "schema_version": "1.0",
        "project_name": "CodexAtlas Web Stub",
        "project_type": "atlas-derived-project",
        "project_profile": "frontend_app",
        "bootstrap_template": "frontend_app",
        "generated_from_skill": "tests_fixture",
        "derived_from": "Codex-Atlas",
        "atlas_root": str(ATLAS_ROOT),
        "audit_paths": ["docs"],
        "status": "certified",
    }
    (project_root / ".atlas-project.json").write_text(
        json.dumps(metadata, indent=2) + "\n",
        encoding="utf-8",
    )
    return project_root
