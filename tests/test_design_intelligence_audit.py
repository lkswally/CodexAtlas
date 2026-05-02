import os
from pathlib import Path
from unittest.mock import patch

os.environ["ATLAS_DISABLE_EVENT_LOGS"] = "1"

from tools.design_intelligence_audit import (
    _run_project_visual_analysis,
    anti_generic_ui_audit,
    design_system_review,
    visual_direction_checkpoint,
)


WEB_ROOT = Path(r"C:\Proyectos\CodexAtlas-Web")


def test_visual_direction_checkpoint_requires_missing_inputs_when_brief_is_vague():
    result = visual_direction_checkpoint("Create a site and make it look good.")
    assert result["status"] == "needs_input"
    assert "audience_missing_or_implicit" in result["warnings"]
    assert "mood_or_vibe_missing" in result["warnings"]


def test_visual_direction_checkpoint_detects_explicit_direction():
    result = visual_direction_checkpoint(
        "Create an internal tool landing page for developers with a premium editorial vibe and balanced originality."
    )
    assert result["status"] == "ready"
    assert result["checkpoint"]["audience"] is not None
    assert result["checkpoint"]["mood_or_vibe"] is not None


def test_anti_generic_ui_audit_returns_structured_output_for_codexatlas_web():
    result = anti_generic_ui_audit(WEB_ROOT)
    assert result["status"] in {"pass", "needs_attention"}
    assert result["public_readiness"] in {"ready", "needs_improvement", "not_ready"}
    assert isinstance(result["landing_score"], int)
    assert isinstance(result["blockers"], list)
    assert isinstance(result["warnings"], list)
    assert isinstance(result["evidence"], list)
    assert result["next_action"]
    assert isinstance(result["recommendation_sources"], list)
    if result["status"] == "pass":
        assert result["prioritized_problems"] == []
    else:
        assert result["prioritized_problems"]
    assert len(result["top_priorities"]) <= 3
    assert any(check["id"] == "cta_clarity" for check in result["checks"])


def test_design_system_review_returns_design_findings():
    result = design_system_review(WEB_ROOT)
    assert result["status"] in {"pass", "needs_attention"}
    assert isinstance(result["design_system_findings"], list)
    assert any(item["id"] == "typography_coherence" for item in result["design_system_findings"])


def test_anti_generic_ui_audit_does_not_emit_cta_fix_when_cta_check_passes():
    result = anti_generic_ui_audit(WEB_ROOT)
    cta_check = next(check for check in result["checks"] if check["id"] == "cta_clarity")
    assert cta_check["status"] == "pass"
    assert "recommendation" not in cta_check
    assert all(source["originating_check"] != "cta_clarity" for source in result["recommendation_sources"])
    assert "Add one clear primary CTA" not in result["next_action"]


def test_skipped_typography_check_includes_reason_without_failing_entire_audit():
    mocked_surface = {
        "index.html": """<!doctype html><html><head><meta name="viewport" content="width=device-width, initial-scale=1"></head>
        <body><header class="hero"><h1>Atlas Demo</h1></header></body></html>""",
        "styles.css": """:root { --bg: #ffffff; --ink: #111111; --accent: #333333; --accent-soft: #efefef; --max: 1080px; --line: #dddddd; }
        body { color: var(--ink); background: var(--bg); }
        @media (max-width: 760px) { body { padding: 1rem; } }""",
        "README.md": "",
        "AGENTS.md": "",
        "docs/architecture.md": "",
    }
    with patch("tools.design_intelligence_audit._load_project_surface", return_value=mocked_surface):
        result = _run_project_visual_analysis(Path("C:/fake-project"))
    typography_check = next(check for check in result["checks"] if check["id"] == "typography_coherence")
    assert typography_check["status"] == "skipped"
    assert typography_check["reason"]
    skipped_source = next(source for source in result["recommendation_sources"] if source["originating_check"] == "typography_coherence")
    assert skipped_source["status"] == "skipped"
    assert skipped_source["recommendation"] == typography_check["recommendation"]
    assert result["status"] in {"needs_attention", "skipped", "pass"}


def test_quick_wins_are_backed_by_recommendation_sources():
    result = anti_generic_ui_audit(WEB_ROOT)
    source_recommendations = {source["recommendation"] for source in result["recommendation_sources"]}
    for quick_win in result["quick_wins"]:
        assert quick_win in source_recommendations


def test_docs_heavy_surface_triggers_landing_balance_and_density_warnings():
    mocked_surface = {
        "index.html": """<!doctype html><html><head><meta name="viewport" content="width=device-width, initial-scale=1"></head>
        <body>
        <header class="hero"><h1>Codex-Atlas</h1><p>Codex-Atlas helps teams bootstrap and audit internal tools.</p><a href="#setup">Start setup</a></header>
        <main>
          <section class="panel"><h2>Installation guide</h2><ol><li>Step one</li><li>Step two</li><li>Step three</li><li>Step four</li><li>Step five</li></ol><p><code>python tools\\atlas_governance_check.py</code></p></section>
          <section class="panel"><h2>Configure</h2><ol><li>Alpha</li><li>Beta</li><li>Gamma</li><li>Delta</li><li>Epsilon</li></ol><p><code>python tools\\atlas_dispatcher.py audit-repo</code></p></section>
          <section class="panel"><h2>First project</h2><ol><li>Brief</li><li>Bootstrap</li><li>Audit</li><li>Certify</li><li>Repeat</li></ol><p><code>python tools\\atlas_dispatcher.py certify-project</code></p></section>
          <section class="panel"><h2>Example prompts</h2><ul><li>Prompt one</li><li>Prompt two</li><li>Prompt three</li><li>Prompt four</li><li>Prompt five</li></ul><p><code>prompt</code></p></section>
        </main></body></html>""",
        "styles.css": """:root { --bg: #f3ede2; --ink: #182126; --accent: #1f5a52; --accent-soft: #d7e7e2; --max: 1080px; --line: #d8cdbd; }
        body { font-family: 'Aptos', sans-serif; color: var(--ink); background: var(--bg); }
        h1, h2 { font-family: Georgia, serif; }
        p, li { font-family: 'Segoe UI', sans-serif; }
        @media (max-width: 760px) { body { padding: 1rem; } }""",
        "README.md": "",
        "AGENTS.md": "",
        "docs/architecture.md": "",
    }
    with patch("tools.design_intelligence_audit._load_project_surface", return_value=mocked_surface):
        result = _run_project_visual_analysis(Path("C:/fake-project"))
    by_id = {check["id"]: check for check in result["checks"]}
    assert by_id["landing_vs_documentation_balance"]["status"] == "warning"
    assert by_id["content_density"]["status"] == "warning"


def test_placeholder_cta_is_reported_as_evidence_based_integrity_warning():
    mocked_surface = {
        "index.html": """<!doctype html><html><head><meta name="viewport" content="width=device-width, initial-scale=1"></head>
        <body>
        <header class="hero"><h1>Codex-Atlas for teams</h1><p>Codex-Atlas is a factory that helps teams bootstrap structured projects.</p>
        <a href="#setup">Start setup</a><a href="PEGAR_ACA_MI_LINKEDIN_REAL">Contact Lucas</a></header>
        <section><h2>What is Codex-Atlas?</h2><p>Factory layer for auditable projects.</p></section>
        </body></html>""",
        "styles.css": """:root { --bg: #ffffff; --ink: #111111; --accent: #1f5a52; --accent-soft: #d7e7e2; --max: 1080px; --line: #d8cdbd; }
        body { font-family: 'Aptos', sans-serif; color: var(--ink); background: var(--bg); }
        h1, h2 { font-family: Georgia, serif; }
        p, li { font-family: 'Segoe UI', sans-serif; }
        @media (max-width: 760px) { body { padding: 1rem; } }""",
        "README.md": "",
        "AGENTS.md": "",
        "docs/architecture.md": "",
    }
    with patch("tools.design_intelligence_audit._load_project_surface", return_value=mocked_surface):
        result = _run_project_visual_analysis(Path("C:/fake-project"))
    cta_integrity = next(check for check in result["checks"] if check["id"] == "cta_integrity")
    assert cta_integrity["status"] == "warning"
    source = next(source for source in result["recommendation_sources"] if source["originating_check"] == "cta_integrity")
    assert any("PEGAR_ACA_MI_LINKEDIN_REAL" in item for item in source["evidence"])
