import os
import tempfile
from pathlib import Path


ATLAS_ROOT = Path(os.environ.get("ATLAS_ROOT", Path(__file__).resolve().parent.parent)).resolve()
DEFAULT_WEB_ROOT = ATLAS_ROOT.parent / "CodexAtlas-Web"
FALLBACK_WEB_ROOT = ATLAS_ROOT / "tests" / "fixtures" / "codexatlas_web_stub"
WEB_ROOT = Path(os.environ.get("ATLAS_WEB_ROOT") or (DEFAULT_WEB_ROOT if DEFAULT_WEB_ROOT.exists() else FALLBACK_WEB_ROOT)).resolve()
REYESOFT_ROOT = Path(os.environ.get("ATLAS_REYESOFT_ROOT", ATLAS_ROOT.parent / "REYESOFT")).resolve()
TEMP_ROOT = Path(
    os.environ.get("ATLAS_TEST_TEMP_ROOT", Path(tempfile.gettempdir()) / "codex-atlas-tests")
).resolve()
PLAYWRIGHT_HOME_HINT = Path(
    os.environ.get("PLAYWRIGHT_BROWSERS_PATH", Path.home() / ".cache" / "ms-playwright")
)
