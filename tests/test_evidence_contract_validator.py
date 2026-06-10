from tools.evidence_contract_validator import validate_evidence_contract


def _valid_contract():
    return {
        "screenshots": [
            {
                "path": "evidence/screenshots/desktop.png",
                "viewport": "desktop",
            }
        ],
        "viewport_reports": [],
        "build_report": {},
        "console_errors": [],
        "network_errors": [],
        "evidence_timestamp": "2026-06-10T00:00:00+00:00",
        "source_commit": "abc123",
    }


def _codes(result):
    return {item["code"] for item in result["findings"]}


def test_valid_contract_passes():
    result = validate_evidence_contract(_valid_contract())

    assert result["status"] == "PASS"
    assert result["valid"] is True
    assert result["findings"] == []


def test_missing_required_field_fails():
    contract = _valid_contract()
    del contract["screenshots"]

    result = validate_evidence_contract(contract)

    assert result["status"] == "FAIL"
    assert result["valid"] is False
    assert "missing_required_field" in _codes(result)


def test_extra_field_fails():
    contract = _valid_contract()
    contract["score"] = 100

    result = validate_evidence_contract(contract)

    assert result["status"] == "FAIL"
    assert result["valid"] is False
    assert "unexpected_field" in _codes(result)


def test_wrong_type_fails():
    contract = _valid_contract()
    contract["console_errors"] = {}

    result = validate_evidence_contract(contract)

    assert result["status"] == "FAIL"
    assert result["valid"] is False
    assert "invalid_field_type" in _codes(result)


def test_empty_timestamp_fails():
    contract = _valid_contract()
    contract["evidence_timestamp"] = " "

    result = validate_evidence_contract(contract)

    assert result["status"] == "FAIL"
    assert result["valid"] is False
    assert "empty_required_string" in _codes(result)


def test_empty_source_commit_fails():
    contract = _valid_contract()
    contract["source_commit"] = ""

    result = validate_evidence_contract(contract)

    assert result["status"] == "FAIL"
    assert result["valid"] is False
    assert "empty_required_string" in _codes(result)


def test_invalid_screenshot_item_fails():
    contract = _valid_contract()
    contract["screenshots"] = [{"path": "desktop.png"}]

    result = validate_evidence_contract(contract)

    assert result["status"] == "FAIL"
    assert result["valid"] is False
    assert "invalid_screenshot_item" in _codes(result)


def test_contract_must_be_object():
    result = validate_evidence_contract([])

    assert result["status"] == "FAIL"
    assert result["valid"] is False
    assert "contract_not_object" in _codes(result)
