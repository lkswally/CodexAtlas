import os
from pathlib import Path

os.environ["ATLAS_DISABLE_EVENT_LOGS"] = "1"

from tests._support_paths import TEMP_ROOT
from tools import evidence_runner


PNG_1X1 = (
    b"\x89PNG\r\n\x1a\n"
    b"\x00\x00\x00\rIHDR"
    b"\x00\x00\x00\x01\x00\x00\x00\x01"
    b"\x08\x02\x00\x00\x00"
    b"\x90wS\xde"
    b"\x00\x00\x00\x00IEND\xaeB`\x82"
)


class FakeConsoleMessage:
    type = "error"
    text = "boom"
    location = {"url": "http://local.test/app.js", "lineNumber": 3, "columnNumber": 9}


class FakeRequest:
    url = "http://local.test/missing.js"
    method = "GET"

    def failure(self):
        return {"errorText": "net::ERR_FAILED"}


class FakeResponse:
    url = "http://local.test/broken.png"
    status = 404
    request = FakeRequest()


class FakePage:
    def __init__(self, browser, viewport):
        self.browser = browser
        self.viewport = viewport
        self.url = ""
        self.handlers = {}

    def on(self, event, handler):
        self.handlers[event] = handler

    def goto(self, url, wait_until):
        self.url = url
        self.browser.opened_urls.append((url, wait_until, self.viewport))
        self.handlers["console"](FakeConsoleMessage())
        self.handlers["requestfailed"](FakeRequest())
        self.handlers["response"](FakeResponse())

    def screenshot(self, path, full_page):
        self.browser.screenshots.append((Path(path).name, full_page))
        Path(path).write_bytes(PNG_1X1)

    def title(self):
        return "Evidence Test"

    def close(self):
        self.browser.closed_pages += 1


class FakeBrowser:
    def __init__(self):
        self.opened_urls = []
        self.screenshots = []
        self.closed_pages = 0
        self.closed = False

    def new_page(self, viewport):
        return FakePage(self, viewport)

    def close(self):
        self.closed = True


class FakeChromium:
    def __init__(self, browser):
        self.browser = browser

    def launch(self):
        return self.browser


class FakePlaywright:
    def __init__(self, browser):
        self.chromium = FakeChromium(browser)


class FakePlaywrightContext:
    def __init__(self, browser):
        self.browser = browser

    def __enter__(self):
        return FakePlaywright(self.browser)

    def __exit__(self, exc_type, exc, tb):
        return False


def _output_dir(name: str) -> Path:
    path = TEMP_ROOT / name
    path.mkdir(parents=True, exist_ok=True)
    return path


def test_evidence_runner_emits_contract_and_opens_url(monkeypatch):
    browser = FakeBrowser()
    monkeypatch.setattr(evidence_runner, "_source_commit", lambda root: "abc123")
    monkeypatch.setattr(
        evidence_runner,
        "_run_build_command",
        lambda command, cwd: {"status": "skipped", "command": None, "returncode": None, "stdout": "", "stderr": ""},
    )

    contract = evidence_runner.run_evidence(
        url="http://local.test",
        output_dir=_output_dir("evidence_runner_valid"),
        playwright_context_factory=lambda: FakePlaywrightContext(browser),
    )

    assert list(contract.keys()) == list(evidence_runner.CONTRACT_KEYS)
    assert contract["source_commit"] == "abc123"
    assert contract["build_report"]["status"] == "skipped"
    assert [item["viewport"] for item in contract["screenshots"]] == ["desktop", "mobile"]
    assert [item["viewport"] for item in contract["viewport_reports"]] == ["desktop", "mobile"]
    assert {name for name, _ in browser.screenshots} == {"desktop.png", "mobile.png"}
    assert len(browser.opened_urls) == 2
    assert all(url == "http://local.test" for url, _, _ in browser.opened_urls)
    assert contract["console_errors"][0]["text"] == "boom"
    assert any(item.get("failure") == "net::ERR_FAILED" for item in contract["network_errors"])
    assert any(item.get("status") == 404 for item in contract["network_errors"])


def test_evidence_runner_marks_empty_screenshot_invalid(tmp_path):
    screenshot = tmp_path / "desktop.png"
    screenshot.write_bytes(b"")

    report = evidence_runner._screenshot_report(
        screenshot,
        "desktop",
        evidence_runner.DEFAULT_DESKTOP_VIEWPORT,
    )

    assert report["exists"] is True
    assert report["byte_size"] == 0
    assert report["valid"] is False


def test_evidence_runner_preserves_failed_build_report(monkeypatch):
    browser = FakeBrowser()
    failed_build = {
        "status": "failed",
        "command": "npm run build",
        "returncode": 1,
        "stdout": "",
        "stderr": "build failed",
    }
    monkeypatch.setattr(evidence_runner, "_source_commit", lambda root: "abc123")
    monkeypatch.setattr(evidence_runner, "_run_build_command", lambda command, cwd: failed_build)

    contract = evidence_runner.run_evidence(
        url="http://local.test",
        output_dir=_output_dir("evidence_runner_failed_build"),
        build_command="npm run build",
        playwright_context_factory=lambda: FakePlaywrightContext(browser),
    )

    assert contract["build_report"] == failed_build
    assert contract["screenshots"][0]["valid"] is True
