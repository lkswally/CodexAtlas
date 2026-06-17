import json

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


def _write_observations(tmp_path, workflows):
    path = tmp_path / "workflow_observations.json"
    path.write_text(
        json.dumps(
            {
                "observations_version": "v1",
                "updated_at": "2026-06-17T00:00:00+00:00",
                "workflows": workflows,
            }
        ),
        encoding="utf-8",
    )
    return path


def _valid_cached_workflows():
    return {
        "atlas_ci": {
            "status": "PASS",
            "run_id": "27725625470",
            "observed_at": "2026-06-17T23:11:12+00:00",
            "notes": "Atlas CI success after dashboard v1",
        },
        "atlas_global_test": {
            "status": "PASS",
            "run_id": "27414397174",
            "observed_at": "2026-06-17T00:00:00+00:00",
            "notes": "Manual global suite passed",
        },
        "evidence_quality_report": {
            "status": "PASS",
            "run_id": "27390064634",
            "artifact_id": "7581555415",
            "observed_at": "2026-06-17T00:00:00+00:00",
            "notes": "Manual opt-in evidence report PASS",
        },
        "evidence_browser_smoke": {
            "status": "PASS",
            "run_id": "27724893071",
            "artifact_id": "7709863742",
            "observed_at": "2026-06-17T22:53:00+00:00",
            "notes": "Manual browser smoke PASS",
        },
    }


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

    report = _dashboard(workflow_statuses=workflows, workflow_observations_path="missing.json")

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
        workflow_observations_path="missing.json",
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


def test_dashboard_uses_valid_workflow_observations(tmp_path):
    path = _write_observations(tmp_path, _valid_cached_workflows())

    report = build_health_dashboard(
        core_statuses=CORE_PASS,
        workflow_observations_path=path,
        generated_at="2026-06-17T00:00:00+00:00",
    )

    assert report["overall_status"] == "PASS"
    assert report["sections"]["ci"]["status"] == "PASS"
    assert report["sections"]["ci"]["workflows"][0]["run_id"] == "27725625470"


def test_missing_workflow_observation_stays_unknown(tmp_path):
    workflows = _valid_cached_workflows()
    del workflows["atlas_global_test"]
    path = _write_observations(tmp_path, workflows)

    report = build_health_dashboard(
        core_statuses=CORE_PASS,
        workflow_observations_path=path,
        generated_at="2026-06-17T00:00:00+00:00",
    )

    atlas_global = report["sections"]["ci"]["workflows"][1]
    assert atlas_global["name"] == "Atlas Global Test"
    assert atlas_global["status"] == "UNKNOWN"
    assert report["overall_status"] == "WARN"


def test_invalid_observations_file_generates_controlled_warn(tmp_path):
    path = tmp_path / "workflow_observations.json"
    path.write_text("{not-json", encoding="utf-8")

    report = build_health_dashboard(
        core_statuses=CORE_PASS,
        workflow_observations_path=path,
        generated_at="2026-06-17T00:00:00+00:00",
    )

    assert report["overall_status"] == "WARN"
    assert report["sections"]["ci"]["observations_cache"]["status"] == "WARN"
    assert report["sections"]["ci"]["observations_cache"]["findings"]


def test_invalid_workflow_status_generates_warn(tmp_path):
    workflows = _valid_cached_workflows()
    workflows["atlas_ci"]["status"] = "GREEN"
    path = _write_observations(tmp_path, workflows)

    report = build_health_dashboard(
        core_statuses=CORE_PASS,
        workflow_observations_path=path,
        generated_at="2026-06-17T00:00:00+00:00",
    )

    assert report["overall_status"] == "WARN"
    assert report["sections"]["ci"]["workflows"][0]["status"] == "WARN"
    assert "invalid_workflow_status:atlas_ci" in report["sections"]["ci"]["observations_cache"]["findings"]


def test_markdown_shows_run_id_and_optional_artifact_id(tmp_path):
    path = _write_observations(tmp_path, _valid_cached_workflows())
    report = build_health_dashboard(
        core_statuses=CORE_PASS,
        workflow_observations_path=path,
        generated_at="2026-06-17T00:00:00+00:00",
    )

    markdown = render_health_markdown(report)

    assert "run_id: 27725625470" in markdown
    assert "artifact_id: 7709863742" in markdown


def test_artifact_id_is_optional(tmp_path):
    workflows = _valid_cached_workflows()
    path = _write_observations(tmp_path, workflows)

    report = build_health_dashboard(
        core_statuses=CORE_PASS,
        workflow_observations_path=path,
        generated_at="2026-06-17T00:00:00+00:00",
    )

    atlas_ci = report["sections"]["ci"]["workflows"][0]
    assert atlas_ci["status"] == "PASS"
    assert atlas_ci["run_id"] == "27725625470"
    assert "artifact_id" not in atlas_ci


def test_cached_workflows_do_not_degrade_local_core_pass(tmp_path):
    path = _write_observations(tmp_path, _valid_cached_workflows())

    report = build_health_dashboard(
        core_statuses=CORE_PASS,
        workflow_observations_path=path,
        generated_at="2026-06-17T00:00:00+00:00",
    )

    assert report["sections"]["evidence"]["components"][0]["status"] == "PASS"
    assert report["sections"]["model_routing"]["status"] == "PASS"
    assert report["sections"]["failure_registry"]["status"] == "PASS"
    assert report["sections"]["integrations"]["governance"]["status"] == "PASS"


def test_overall_warn_if_any_workflow_unknown(tmp_path):
    path = _write_observations(tmp_path, {})

    report = build_health_dashboard(
        core_statuses=CORE_PASS,
        workflow_observations_path=path,
        generated_at="2026-06-17T00:00:00+00:00",
    )

    assert report["overall_status"] == "WARN"
    assert report["sections"]["ci"]["status"] == "UNKNOWN"


def test_overall_pass_if_core_and_observed_workflows_pass(tmp_path):
    path = _write_observations(tmp_path, _valid_cached_workflows())

    report = build_health_dashboard(
        core_statuses=CORE_PASS,
        workflow_observations_path=path,
        generated_at="2026-06-17T00:00:00+00:00",
    )

    assert report["overall_status"] == "PASS"
