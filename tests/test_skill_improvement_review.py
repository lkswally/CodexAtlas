import json
import os
import shutil
from pathlib import Path
from uuid import uuid4

os.environ["ATLAS_DISABLE_EVENT_LOGS"] = "1"

from tests._support_paths import ATLAS_ROOT, TEMP_ROOT
from tools.skill_improvement_review import review_skill_catalog




def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def _write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def _make_root(root: Path) -> Path:
    config_dir = root / "config"
    skills_dir = root / "skills"
    tests_dir = root / "tests"
    config_dir.mkdir(parents=True, exist_ok=True)
    skills_dir.mkdir(parents=True, exist_ok=True)
    tests_dir.mkdir(parents=True, exist_ok=True)
    for config_name in ("skill_lifecycle_rules.json", "skill_improvement_review_rules.json"):
        source = ATLAS_ROOT / "config" / config_name
        _write_text(config_dir / config_name, source.read_text(encoding="utf-8"))
    return root


def _make_workspace_root() -> Path:
    root = TEMP_ROOT / f"skill_improvement_{uuid4().hex}" / "atlas"
    if root.exists():
        shutil.rmtree(root.parent.parent, ignore_errors=True)
    return _make_root(root)


def _make_skill(
    root: Path,
    skill_id: str,
    *,
    intent_keywords: list[str],
    workflow: str = "atlas_project_pipeline",
    risk_level: str = "low",
    skill_md: str | None = None,
    include_behavior: bool = True,
) -> None:
    skill_dir = root / "skills" / skill_id
    metadata = {
        "name": skill_id,
        "intent_keywords": intent_keywords,
        "agent": "planner",
        "workflow": workflow,
        "model_profile": "deep_reasoning",
        "risk_level": risk_level,
        "requires_human_approval": False,
        "supports_execution": False,
        "required_inputs": ["none"],
        "execution_mode": "read_only",
        "allowed_paths_policy": "no_filesystem_writes",
        "expected_outputs": ["review"],
        "safety_limits": ["do not write files"],
        "forbidden_actions": ["do not auto-modify skills"],
        "human_approval_triggers": ["the task becomes write-capable"],
        "rollback_manual": ["no rollback needed because this review is read-only"],
        "validations": ["returns a structured recommendation"],
    }
    _write_json(skill_dir / "skill.json", metadata)
    if skill_md is not None:
        _write_text(skill_dir / "skill.md", skill_md)
    if include_behavior:
        _write_json(
            skill_dir / "behavior.json",
            {
                "writes_files": False,
                "writes_code": False,
                "uses_output_dir": False,
                "read_only": True,
                "execution_helper": "none",
                "side_effects": [],
                "requires_project_path": False,
                "requires_output_dir": False,
                "can_run_without_approval": True,
                "notes": ["test helper"],
            },
        )


def _add_test_reference(root: Path, skill_id: str) -> None:
    _write_text(root / "tests" / f"test_{skill_id.replace('-', '_')}.py", f"def test_ref():\n    assert '{skill_id}'\n")


def test_skill_improvement_review_marks_healthy_skill_as_keep():
    root = _make_workspace_root()
    try:
        _make_skill(
            root,
            "design-system-review",
            intent_keywords=["design system", "typography", "layout"],
            skill_md="# Design\n\n## When to Use\nUse it.\n\n## Steps\n1. Review.\n\n## Outputs\nStructured review.\n",
        )
        _add_test_reference(root, "design-system-review")

        result = review_skill_catalog(root=root)

        assert result["status"] == "ok"
        review = result["reviewed_skills"][0]
        assert review["recommendation"] == "keep"
        assert review["recommended_state"] == "stable"
    finally:
        shutil.rmtree(root.parent, ignore_errors=True)


def test_skill_improvement_review_flags_skill_without_tests():
    root = _make_workspace_root()
    try:
        _make_skill(
            root,
            "visual-direction-checkpoint",
            intent_keywords=["visual direction", "mood", "audience"],
            skill_md="# Visual Direction\n\n## When to Use\nUse it.\n\n## Steps\n1. Clarify.\n\n## Outputs\nCheckpoint.\n",
        )

        result = review_skill_catalog(root=root)

        review = result["reviewed_skills"][0]
        assert review["recommendation"] == "improve"
        assert "no_skill_specific_test_reference" in review["missing_tests"]
        assert result["weak_skills"]
    finally:
        shutil.rmtree(root.parent, ignore_errors=True)


def test_skill_improvement_review_flags_skill_without_docs():
    root = _make_workspace_root()
    try:
        _make_skill(
            root,
            "repo-audit",
            intent_keywords=["repo audit", "surface review"],
            skill_md=None,
        )
        _add_test_reference(root, "repo-audit")

        result = review_skill_catalog(root=root)

        review = result["reviewed_skills"][0]
        assert review["recommendation"] == "improve"
        assert "missing_skill_md" in review["missing_docs"]
    finally:
        shutil.rmtree(root.parent, ignore_errors=True)


def test_skill_improvement_review_detects_duplicate_skills_and_recommends_deprecate():
    root = _make_workspace_root()
    try:
        doc = "# Skill\n\n## When to Use\nUse it.\n\n## Steps\n1. Review.\n\n## Outputs\nReview.\n"
        _make_skill(root, "repo-audit", intent_keywords=["repo audit", "surface review", "structure"], skill_md=doc)
        _make_skill(root, "repo-audit-plus", intent_keywords=["repo audit", "surface review", "structure"], skill_md=doc)
        _add_test_reference(root, "repo-audit")
        _add_test_reference(root, "repo-audit-plus")

        result = review_skill_catalog(root=root)

        assert result["duplicate_risks"]
        assert any(item["recommendation"] == "deprecate" for item in result["reviewed_skills"])
    finally:
        shutil.rmtree(root.parent, ignore_errors=True)


def test_skill_improvement_review_external_candidate_can_require_human_approval():
    root = _make_workspace_root()
    try:
        _make_skill(root, "repo-audit", intent_keywords=["repo audit", "surface review"], skill_md="# Skill\n\n## When to Use\nUse it.\n\n## Steps\n1. Review.\n")
        _add_test_reference(root, "repo-audit")

        result = review_skill_catalog(
            root=root,
            external_candidates=[
                {
                    "candidate_name": "skill-catalog-hygiene",
                    "problem_statement": "Need a reusable factory-wide governance workflow skill for an AI agent system with repeatable cross-project catalog hygiene review and skill lifecycle guidance.",
                    "source": "claude-auto-tune",
                    "clear_gap": True,
                    "improves_existing_layer": True,
                    "provenance": "documented_repo",
                }
            ],
        )

        assert result["candidate_opportunities"]
        assert result["requires_human_approval"] is True
        assert result["candidate_opportunities"][0]["atlas_fit_decision"] == "adapt_later"
        assert result["candidate_opportunities"][0]["utility_score"] >= 70
    finally:
        shutil.rmtree(root.parent.parent, ignore_errors=True)


def test_skill_improvement_review_watchlists_candidate_with_install_mcp_and_global_config_risk():
    root = _make_workspace_root()
    try:
        _make_skill(root, "repo-audit", intent_keywords=["repo audit", "surface review"], skill_md="# Skill\n\n## When to Use\nUse it.\n\n## Steps\n1. Review.\n")
        _add_test_reference(root, "repo-audit")

        result = review_skill_catalog(
            root=root,
            external_candidates=[
                {
                    "candidate_name": "playwright-runtime-sync",
                    "problem_statement": "Need an autonomous MCP Playwright runtime install and sync skill with browser automation and provider token setup.",
                    "source": "external-radar",
                    "requires_mcp": True,
                    "install_script": True,
                    "requires_config_global": True,
                }
            ],
        )

        assert result["blocked_candidates"]
        assert result["requires_decision_council"] is True
        assert result["blocked_candidates"][0]["recommendation"] == "decision_council_required"
        assert result["blocked_candidates"][0]["atlas_fit_decision"] == "watchlist"
        assert result["blocked_candidates"][0]["mcp_risk"] == "high"
        assert result["blocked_candidates"][0]["install_risk"] == "high"
    finally:
        shutil.rmtree(root.parent.parent, ignore_errors=True)


def test_skill_improvement_review_watchlists_candidate_with_provider_keys():
    root = _make_workspace_root()
    try:
        _make_skill(root, "repo-audit", intent_keywords=["repo audit", "surface review"], skill_md="# Skill\n\n## When to Use\nUse it.\n\n## Steps\n1. Review.\n")
        _add_test_reference(root, "repo-audit")

        result = review_skill_catalog(
            root=root,
            external_candidates=[
                {
                    "candidate_name": "provider-fallback-runtime",
                    "problem_statement": "Need provider key handling and external provider runtime for fallback summaries and remote execution.",
                    "source": "provider-radar",
                    "requires_secrets": True,
                    "requires_provider": True,
                    "provenance": "community",
                }
            ],
        )

        assert result["blocked_candidates"]
        assert result["blocked_candidates"][0]["atlas_fit_decision"] == "watchlist"
        assert result["blocked_candidates"][0]["secret_risk"] == "high"
    finally:
        shutil.rmtree(root.parent.parent, ignore_errors=True)


def test_skill_improvement_review_marks_already_covered_candidate_explicitly():
    root = _make_workspace_root()
    try:
        _make_skill(
            root,
            "repo-graph-readiness",
            intent_keywords=["repo graph", "code intelligence", "impact analysis"],
            skill_md="# Skill\n\n## When to Use\nUse it.\n\n## Steps\n1. Review.\n",
        )
        _add_test_reference(root, "repo-graph-readiness")

        result = review_skill_catalog(
            root=root,
            external_candidates=[
                {
                    "candidate_name": "repo-graph-readiness",
                    "problem_statement": "Already covered by the same capability overlap in Atlas for repo graph readiness and impact analysis.",
                    "source": "trending-radar",
                    "already_covered": True,
                }
            ],
        )

        assert result["blocked_candidates"]
        assert result["blocked_candidates"][0]["atlas_fit_decision"] == "already_covered"
        assert result["blocked_candidates"][0]["duplication_risk"] == "high"
    finally:
        shutil.rmtree(root.parent.parent, ignore_errors=True)


def test_skill_improvement_review_discards_popular_repo_without_real_gap():
    root = _make_workspace_root()
    try:
        _make_skill(root, "repo-audit", intent_keywords=["repo audit", "surface review"], skill_md="# Skill\n\n## When to Use\nUse it.\n\n## Steps\n1. Review.\n")
        _add_test_reference(root, "repo-audit")

        result = review_skill_catalog(
            root=root,
            external_candidates=[
                {
                    "candidate_name": "trending-ui-starter",
                    "problem_statement": "Popular starter template for marketing themes and boilerplate without a real Atlas gap.",
                    "source": "github-trending",
                    "popular_only": True,
                    "provenance": "community",
                }
            ],
        )

        assert result["blocked_candidates"]
        assert result["blocked_candidates"][0]["atlas_fit_decision"] == "discard"
        assert result["blocked_candidates"][0]["utility_score"] < 50
    finally:
        shutil.rmtree(root.parent.parent, ignore_errors=True)


def test_skill_improvement_review_deduplicates_external_references():
    root = _make_workspace_root()
    try:
        _make_skill(root, "repo-audit", intent_keywords=["repo audit", "surface review"], skill_md="# Skill\n\n## When to Use\nUse it.\n\n## Steps\n1. Review.\n")
        _add_test_reference(root, "repo-audit")

        result = review_skill_catalog(
            root=root,
            external_candidates=[
                {
                    "candidate_name": "safe-skill-registry",
                    "problem_statement": "Need stronger skill provenance and registry scoring for Atlas without runtime install.",
                    "source": "github-trending",
                    "repo": "tech-leads-club/agent-skills",
                    "clear_gap": True,
                    "improves_existing_layer": True,
                },
                {
                    "candidate_name": "safe-skill-registry",
                    "problem_statement": "Need stronger skill provenance and registry scoring for Atlas without runtime install.",
                    "source": "market-radar",
                    "repo": "tech-leads-club/agent-skills",
                    "clear_gap": True,
                    "improves_existing_layer": True,
                },
            ],
        )

        assert len(result["external_reference_reviews"]) == 1
    finally:
        shutil.rmtree(root.parent.parent, ignore_errors=True)


def test_skill_improvement_review_discards_claude_only_candidate():
    root = _make_workspace_root()
    try:
        _make_skill(root, "repo-audit", intent_keywords=["repo audit", "surface review"], skill_md="# Skill\n\n## When to Use\nUse it.\n\n## Steps\n1. Review.\n")
        _add_test_reference(root, "repo-audit")

        result = review_skill_catalog(
            root=root,
            external_candidates=[
                {
                    "candidate_name": "claude-hook-sync",
                    "problem_statement": "Need Claude-specific hooks and CLAUDE.md runtime glue for automatic workflow injection.",
                    "source": "claude-only-radar",
                    "claude_only": True,
                }
            ],
        )

        assert result["blocked_candidates"]
        assert result["blocked_candidates"][0]["atlas_fit_decision"] == "discard"
        assert result["blocked_candidates"][0]["recommendation"] == "reject"
    finally:
        shutil.rmtree(root.parent.parent, ignore_errors=True)
