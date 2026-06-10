import json

from tools.evidence_bundle_summary_cli import main
from tools.evidence_session import build_evidence_bundle, write_evidence_bundle


SUMMARY_FIELDS = {
    "status",
    "contract_version",
    "source_commit",
    "evidence_timestamp",
    "screenshots_count",
    "viewport_reports_count",
    "console_errors_count",
    "network_errors_count",
    "has_build_report",
    "warnings",
    "failures",
}


def _valid_contract():
    return {
        "screenshots": [
            {
                "path": "evidence/screenshots/desktop.png",
                "viewport": "desktop",
            }
        ],
        "viewport_reports": [
            {
                "viewport": "desktop",
                "url": "http://localhost:3000",
                "width": 1440,
                "height": 1000,
            }
        ],
        "build_report": {},
        "console_errors": [],
        "network_errors": [],
        "evidence_timestamp": "2026-06-10T00:00:00+00:00",
        "source_commit": "abc123",
    }


def _write_bundle(tmp_path, contract):
    bundle = build_evidence_bundle(contract)
    output_path = tmp_path / "bundle.json"
    write_evidence_bundle(bundle, output_path)
    return output_path


def _stdout_json(capsys):
    captured = capsys.readouterr()
    return json.loads(captured.out)


def test_cli_pass_bundle_returns_zero_and_valid_json(tmp_path, capsys):
    output_path = _write_bundle(tmp_path, _valid_contract())

    exit_code = main([str(output_path)])
    summary = _stdout_json(capsys)

    assert exit_code == 0
    assert summary["status"] == "PASS"
    assert set(summary.keys()) == SUMMARY_FIELDS


def test_cli_warn_bundle_returns_zero_and_valid_json(tmp_path, capsys):
    contract = _valid_contract()
    contract["screenshots"] = []
    output_path = _write_bundle(tmp_path, contract)

    exit_code = main([str(output_path)])
    summary = _stdout_json(capsys)

    assert exit_code == 0
    assert summary["status"] == "WARN"
    assert set(summary.keys()) == SUMMARY_FIELDS


def test_cli_missing_bundle_returns_one(tmp_path, capsys):
    exit_code = main([str(tmp_path / "missing.json")])
    summary = _stdout_json(capsys)

    assert exit_code == 1
    assert summary["status"] == "FAIL"
    assert summary["failures"]


def test_cli_without_arguments_returns_one(capsys):
    exit_code = main([])
    captured = capsys.readouterr()

    assert exit_code == 1
    assert "Usage:" in captured.err
    assert captured.out == ""


def test_cli_stdout_is_pretty_printed_json(tmp_path, capsys):
    output_path = _write_bundle(tmp_path, _valid_contract())

    exit_code = main([str(output_path)])
    captured = capsys.readouterr()

    assert exit_code == 0
    assert captured.out.startswith("{\n  \"status\"")
