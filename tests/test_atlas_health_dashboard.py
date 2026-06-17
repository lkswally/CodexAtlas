import pytest

from tools.atlas_health_dashboard import (
    AtlasHealthDashboardValidationError,
    build_health_dashboard,
    render_health_markdown,
    validate_health_dashboard,
)


WORKFLOW_PASS = {
    "Atlas CI": "PASS",
    "Atlas Global Test": "PASS",
    "Evidence Quality Report": "PASS",
    "Evidence Browser Smoke": "PASS",
}
CORE_PASS = {
    "evidence_pipeline": "PASS",
    "model_routing": "PASS",
    "failure_registry": "PASS",
    "governance": "PASS",
}


def _dashboard(**overrides):
    params = {
        "workflow_statuses": WORKFLOW_PASS,
        "core_statuses": CORE_PASS,
        "generated_at": "2026-06-17T00:00:00+00:00",
    }
    params.update(overrides)
    return build_health_dashboard(**params)


def test_dashboard_is_valid():
    report = _dashboard()

    assert validate_health_dashboard(report) == {"status": "PASS", "valid": True, "findings": []}
    assert report["dashboard_name"] == "atlas_health_dashboard"
    assert report["version"] == "v1"


def test_status_pass_if_all_core_is_pass():
    report = _dashboard()

    assert report["overall_status"] == "PASS"


def test_status_warn_if_any_section_is_unknown():
    workflows = dict(WORKFLOW_PASS)
    del workflows["Atlas Global Test"]

    report = _dashboard(workflow_statuses=workflows)

    assert report["overall_status"] == "WARN"
    assert report["sections"]["ci"]["status"] == "UNKNOWN"


def test_status_fail_if_critical_block_fails():
    core = dict(CORE_PASS)
    core["evidence_pipeline"] = "FAIL"

    report = _dashboard(core_statuses=core)

    assert report["overall_status"] == "FAIL"
    assert report["sections"]["evidence"]["status"] == "FAIL"


def test_render_markdown_includes_main_sections():
    markdown = render_health_markdown(_dashboard())

    for heading in (
        "## CI",
        "## Evidence",
        "## Browser Smoke",
        "## Model Routing",
        "## Failure Registry",
        "## Integrations",
    ):
        assert heading in markdown


def test_validate_rejects_missing_fields():
    report = _dashboard()
    del report["sections"]

    with pytest.raises(AtlasHealthDashboardValidationError):
        validate_health_dashboard(report)


def test_build_does_not_require_gh():
    report = build_health_dashboard(
        core_statuses=CORE_PASS,
        generated_at="2026-06-17T00:00:00+00:00",
    )

    assert report["overall_status"] == "WARN"
    assert all(
        workflow["status"] == "UNKNOWN"
        for workflow in report["sections"]["ci"]["workflows"]
    )


def test_build_does_not_call_external_apis(monkeypatch):
    def forbidden(*args, **kwargs):
        raise AssertionError("external command should not be called")

    monkeypatch.setattr("subprocess.run", forbidden, raising=False)

    report = _dashboard()

    assert report["overall_status"] == "PASS"
