from __future__ import annotations

import os
import sys
import threading
from contextlib import contextmanager
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Iterator

import pytest

from tests._support_paths import ATLAS_ROOT
from tools.evidence_contract_validator import validate_evidence_contract
from tools.evidence_quality_report import build_evidence_quality_report
from tools.evidence_runner import CONTRACT_KEYS, run_evidence
from tools.evidence_session import build_evidence_bundle, write_evidence_bundle


FIXTURE_ROOT = ATLAS_ROOT / "tests" / "fixtures" / "codexatlas_web_stub"


class _QuietHandler(SimpleHTTPRequestHandler):
    def log_message(self, format: str, *args: object) -> None:
        return None


@contextmanager
def _serve_fixture() -> Iterator[str]:
    handler = partial(_QuietHandler, directory=str(FIXTURE_ROOT))
    server = ThreadingHTTPServer(("127.0.0.1", 0), handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        host, port = server.server_address
        yield f"http://{host}:{port}/"
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=5)


def _windows_dll_directories() -> list[object]:
    if os.name != "nt" or not hasattr(os, "add_dll_directory"):
        return []
    candidates = (Path(sys.base_prefix), Path(sys.prefix) / "Scripts")
    return [os.add_dll_directory(str(path)) for path in candidates if path.is_dir()]


@pytest.mark.skipif(
    os.environ.get("ATLAS_RUN_REAL_BROWSER_SMOKE") != "1",
    reason="Real-browser smoke is opt-in and requires a provisioned local Chromium runtime.",
)
def test_evidence_runner_real_browser_smoke(tmp_path: Path) -> None:
    dll_handles = _windows_dll_directories()
    output_dir = tmp_path / "evidence"

    with _serve_fixture() as url:
        contract = run_evidence(url=url, output_dir=output_dir, root=ATLAS_ROOT)

    assert dll_handles or os.name != "nt"
    assert list(contract) == list(CONTRACT_KEYS)
    assert contract["source_commit"]
    assert contract["evidence_timestamp"]
    assert len(contract["screenshots"]) == 2
    assert {item["viewport"] for item in contract["screenshots"]} == {"desktop", "mobile"}
    assert all(item["valid"] for item in contract["screenshots"])
    assert all(Path(item["path"]).is_file() for item in contract["screenshots"])
    assert len(contract["viewport_reports"]) == 2
    assert contract["console_errors"] == []
    assert contract["network_errors"] == []

    validation = validate_evidence_contract(contract)
    assert validation["status"] == "PASS"
    assert validation["valid"] is True

    bundle = build_evidence_bundle(contract)
    bundle_path = write_evidence_bundle(bundle, tmp_path / "evidence-bundle.json")
    report = build_evidence_quality_report(bundle_path)

    assert bundle_path.is_file()
    assert report["result"] == "PASS"
    assert report["blocking"] is False
    assert report["gate"]["details"]["screenshots_count"] == 2
    assert report["gate"]["details"]["viewport_reports_count"] == 2
    assert report["gate"]["details"]["console_errors_count"] == 0
    assert report["gate"]["details"]["network_errors_count"] == 0
