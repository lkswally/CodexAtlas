from __future__ import annotations

import os
from pathlib import Path


RUNTIME_STATE_DIR = ".atlas_runtime"


def runtime_state_dir(root: Path) -> Path:
    override = os.environ.get("ATLAS_RUNTIME_STATE_DIR", "").strip()
    if override:
        configured = Path(override).expanduser()
        return configured if configured.is_absolute() else (root / configured)
    return root / RUNTIME_STATE_DIR


def runtime_state_file(root: Path, filename: str) -> Path:
    return runtime_state_dir(root.resolve()) / filename
