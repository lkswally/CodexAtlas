from __future__ import annotations

import argparse
import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Tuple


DEFAULT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DESKTOP_VIEWPORT = {"width": 1440, "height": 1000}
DEFAULT_MOBILE_VIEWPORT = {"width": 390, "height": 844}
CONTRACT_KEYS = (
    "screenshots",
    "viewport_reports",
    "build_report",
    "console_errors",
    "network_errors",
    "evidence_timestamp",
    "source_commit",
)


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _empty_contract(*, timestamp: Optional[str] = None, source_commit: str = "") -> Dict[str, Any]:
    return {
        "screenshots": [],
        "viewport_reports": [],
        "build_report": {},
        "console_errors": [],
        "network_errors": [],
        "evidence_timestamp": timestamp or _utc_now_iso(),
        "source_commit": source_commit,
    }


def _source_commit(root: Path) -> str:
    try:
        result = subprocess.run(
            ["git", "-C", str(root), "-c", f"safe.directory={root.as_posix()}", "rev-parse", "HEAD"],
            capture_output=True,
            text=True,
            timeout=10,
            check=False,
        )
    except Exception:
        return ""
    if result.returncode != 0:
        return ""
    return (result.stdout or "").strip()


def _run_build_command(command: Optional[str], cwd: Path) -> Dict[str, Any]:
    if not command:
        return {"status": "skipped", "command": None, "returncode": None, "stdout": "", "stderr": ""}
    try:
        result = subprocess.run(
            command,
            cwd=str(cwd),
            shell=True,
            capture_output=True,
            text=True,
            timeout=120,
            check=False,
        )
    except Exception as exc:
        return {
            "status": "failed",
            "command": command,
            "returncode": None,
            "stdout": "",
            "stderr": str(exc),
        }
    return {
        "status": "passed" if result.returncode == 0 else "failed",
        "command": command,
        "returncode": result.returncode,
        "stdout": (result.stdout or "").strip(),
        "stderr": (result.stderr or "").strip(),
    }


def _png_dimensions(path: Path) -> Tuple[Optional[int], Optional[int]]:
    try:
        with path.open("rb") as handle:
            header = handle.read(24)
    except OSError:
        return None, None
    if len(header) < 24 or header[:8] != b"\x89PNG\r\n\x1a\n":
        return None, None
    return int.from_bytes(header[16:20], "big"), int.from_bytes(header[20:24], "big")


def _screenshot_report(path: Path, viewport_name: str, viewport: Dict[str, int]) -> Dict[str, Any]:
    exists = path.exists()
    byte_size = path.stat().st_size if exists else 0
    image_width, image_height = _png_dimensions(path)
    return {
        "viewport": viewport_name,
        "path": str(path),
        "exists": exists,
        "byte_size": byte_size,
        "width": image_width or int(viewport["width"]),
        "height": image_height or int(viewport["height"]),
        "valid": bool(exists and byte_size > 0 and image_width is not None and image_height is not None),
    }


def _console_error(message: Any) -> Dict[str, Any]:
    location = message.location if isinstance(getattr(message, "location", None), dict) else {}
    return {
        "type": str(getattr(message, "type", "")),
        "text": str(getattr(message, "text", "")),
        "url": str(location.get("url", "")),
        "line": location.get("lineNumber"),
        "column": location.get("columnNumber"),
    }


def _request_failure(request: Any) -> Dict[str, Any]:
    failure = request.failure() if callable(getattr(request, "failure", None)) else None
    return {
        "url": str(getattr(request, "url", "")),
        "method": str(getattr(request, "method", "")),
        "failure": str((failure or {}).get("errorText", "")) if isinstance(failure, dict) else str(failure or ""),
    }


def _response_failure(response: Any) -> Optional[Dict[str, Any]]:
    status = int(getattr(response, "status", 0) or 0)
    if status < 400:
        return None
    request = response.request if getattr(response, "request", None) is not None else None
    return {
        "url": str(getattr(response, "url", "")),
        "method": str(getattr(request, "method", "")),
        "status": status,
    }


def _append_response_failure(network_errors: List[Dict[str, Any]], response: Any) -> None:
    failure = _response_failure(response)
    if failure is not None:
        network_errors.append(failure)


def _viewport_report(page: Any, viewport_name: str, viewport: Dict[str, int], timestamp: str) -> Dict[str, Any]:
    title = page.title() if callable(getattr(page, "title", None)) else ""
    return {
        "viewport": viewport_name,
        "url": str(getattr(page, "url", "")),
        "width": int(viewport["width"]),
        "height": int(viewport["height"]),
        "title": str(title),
        "timestamp": timestamp,
    }


def _sync_playwright_context() -> Any:
    from playwright.sync_api import sync_playwright

    return sync_playwright()


def run_evidence(
    *,
    url: str,
    output_dir: Path,
    root: Path = DEFAULT_ROOT,
    build_command: Optional[str] = None,
    playwright_context_factory: Optional[Callable[[], Any]] = None,
) -> Dict[str, Any]:
    root = root.resolve()
    output_dir = output_dir.resolve()
    output_dir.mkdir(parents=True, exist_ok=True)
    timestamp = _utc_now_iso()
    contract = _empty_contract(timestamp=timestamp, source_commit=_source_commit(root))
    contract["build_report"] = _run_build_command(build_command, root)

    console_errors: List[Dict[str, Any]] = []
    network_errors: List[Dict[str, Any]] = []
    factory = playwright_context_factory or _sync_playwright_context

    with factory() as playwright:
        browser = playwright.chromium.launch()
        try:
            for viewport_name, viewport in (
                ("desktop", DEFAULT_DESKTOP_VIEWPORT),
                ("mobile", DEFAULT_MOBILE_VIEWPORT),
            ):
                page = browser.new_page(viewport=viewport)
                page.on("console", lambda message: console_errors.append(_console_error(message)) if getattr(message, "type", "") == "error" else None)
                page.on("requestfailed", lambda request: network_errors.append(_request_failure(request)))
                page.on("response", lambda response: _append_response_failure(network_errors, response))
                page.goto(url, wait_until="networkidle")
                screenshot_path = output_dir / f"{viewport_name}.png"
                page.screenshot(path=str(screenshot_path), full_page=True)
                contract["screenshots"].append(_screenshot_report(screenshot_path, viewport_name, viewport))
                contract["viewport_reports"].append(_viewport_report(page, viewport_name, viewport, timestamp))
                if callable(getattr(page, "close", None)):
                    page.close()
        finally:
            browser.close()

    contract["console_errors"] = console_errors
    contract["network_errors"] = [item for item in network_errors if item]
    return {key: contract[key] for key in CONTRACT_KEYS}


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(add_help=True)
    parser.add_argument("--url", required=True)
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--root", default=None)
    parser.add_argument("--build-command", default=None)
    parser.add_argument("--contract-out", default=None)
    args = parser.parse_args(argv)

    root = Path(args.root).resolve() if args.root else DEFAULT_ROOT
    contract = run_evidence(
        url=args.url,
        output_dir=Path(args.output_dir),
        root=root,
        build_command=args.build_command,
    )
    rendered = json.dumps(contract, ensure_ascii=False, indent=2)
    if args.contract_out:
        Path(args.contract_out).resolve().write_text(rendered + "\n", encoding="utf-8")
    print(rendered)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
