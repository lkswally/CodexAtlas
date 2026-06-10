import json

from tools.evidence_quality_report_cli import main
from tools.evidence_session import build_evidence_bundle, write_evidence_bundle


REPORT_FIELDS = {
    "report_name",
    "mode",
    "gate",
    "result",
    "blocking",
    "recommendation",
    "generated_at",
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
    report = _stdout_json(capsys)

    assert exit_code == 0
    assert report["result"] == "PASS"
    assert set(report.keys()) == REPORT_FIELDS


def test_cli_warn_bundle_returns_zero_and_valid_json(tmp_path, capsys):
    contract = _valid_contract()
    contract["screenshots"] = []
    output_path = _write_bundle(tmp_path, contract)

    exit_code = main([str(output_path)])
    report = _stdout_json(capsys)

    assert exit_code == 0
    assert report["result"] == "WARN"
    assert set(report.keys()) == REPORT_FIELDS


def test_cli_missing_bundle_returns_one_and_valid_json(tmp_path, capsys):
    exit_code = main([str(tmp_path / "missing.json")])
    report = _stdout_json(capsys)

    assert exit_code == 1
    assert report["result"] == "FAIL"
    assert set(report.keys()) == REPORT_FIELDS


def test_cli_without_arguments_returns_one(capsys):
    exit_code = main([])
    captured = capsys.readouterr()

    assert exit_code == 1
    assert "Usage:" in captured.err
    assert captured.out == ""


def test_cli_report_is_non_blocking(tmp_path, capsys):
    output_path = _write_bundle(tmp_path, _valid_contract())

    exit_code = main([str(output_path)])
    report = _stdout_json(capsys)

    assert exit_code == 0
    assert report["blocking"] is False


def test_cli_report_mode_is_opt_in_non_blocking(tmp_path, capsys):
    output_path = _write_bundle(tmp_path, _valid_contract())

    exit_code = main([str(output_path)])
    report = _stdout_json(capsys)

    assert exit_code == 0
    assert report["mode"] == "opt_in_non_blocking"


def test_cli_stdout_is_pretty_printed_json(tmp_path, capsys):
    output_path = _write_bundle(tmp_path, _valid_contract())

    exit_code = main([str(output_path)])
    captured = capsys.readouterr()

    assert exit_code == 0
    assert captured.out.startswith("{\n  \"report_name\"")
