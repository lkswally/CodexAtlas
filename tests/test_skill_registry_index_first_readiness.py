import json
import shutil
import uuid
from contextlib import contextmanager
from pathlib import Path

from tests._support_paths import ATLAS_ROOT
from tools.skill_registry_index_first_readiness import assess_skill_registry_index_first_readiness


def _write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def _write_json(path: Path, payload: dict) -> None:
    _write(path, json.dumps(payload, ensure_ascii=False, indent=2) + "\n")


def _seed_rules(root: Path) -> None:
    config_dir = root / "config"
    config_dir.mkdir(parents=True, exist_ok=True)
    source_rules = Path(__file__).resolve().parents[1] / "config" / "skill_registry_index_first_rules.json"
    _write(config_dir / "skill_registry_index_first_rules.json", source_rules.read_text(encoding="utf-8"))


def _make_skill(
    root: Path,
    skill_id: str,
    *,
    skill_name: str = "",
    markdown: str = "",
    behavior: dict | None = None,
) -> None:
    skill_dir = root / "skills" / skill_id
    skill_dir.mkdir(parents=True, exist_ok=True)
    _write_json(
        skill_dir / "skill.json",
        {
            "name": skill_name or skill_id,
            "intent_keywords": ["repo audit", "boundary review"],
            "agent": "reviewer",
            "workflow": "audit_project",
            "risk_level": "medium",
        },
    )
    _write(
        skill_dir / "skill.md",
        markdown
        or "# Skill\n\n## Purpose\nAudit a repository carefully before making larger changes.\n",
    )
    _write_json(
        skill_dir / "behavior.json",
        behavior
        or {
            "writes_files": False,
            "writes_code": False,
            "uses_output_dir": False,
            "read_only": True,
            "execution_helper": "none",
            "side_effects": [],
            "requires_project_path": True,
            "requires_output_dir": False,
            "can_run_without_approval": True,
            "notes": ["read only"],
        },
    )


@contextmanager
def _workspace_root() -> Path:
    root = ATLAS_ROOT / "tests" / f"_tmp_skill_registry_index_first_{uuid.uuid4().hex[:8]}"
    if root.exists():
        shutil.rmtree(root, ignore_errors=True)
    root.mkdir(parents=True, exist_ok=True)
    try:
        yield root
    finally:
        shutil.rmtree(root, ignore_errors=True)


def test_index_first_ready_with_multiline_frontmatter_description():
    with _workspace_root() as root:
        _seed_rules(root)
        _make_skill(
            root,
            "repo-audit",
            markdown="---\nname: repo-audit\ndescription: >\n  Audit repositories with explicit boundary checks and\n  evidence-backed findings before implementation starts.\nscope: atlas repo analysis\n---\n\n# Skill\n",
        )

        result = assess_skill_registry_index_first_readiness(root=root)
        assert result["readiness_state"] == "ready"
        assert result["index_first_safe_to_use"] is True
        assert result["skills_indexed"] == 1
        assert result["skills_index"][0]["description"].startswith("Audit repositories")


def test_index_first_blocks_missing_behavior_json():
    with _workspace_root() as root:
        _seed_rules(root)
        skill_dir = root / "skills" / "repo-audit"
        skill_dir.mkdir(parents=True, exist_ok=True)
        _write_json(
            skill_dir / "skill.json",
            {
                "name": "repo-audit",
                "intent_keywords": ["repo audit"],
                "agent": "reviewer",
                "workflow": "audit_project",
                "risk_level": "medium",
            },
        )
        _write(
            skill_dir / "skill.md",
            "# Skill\n\n## Purpose\nAudit repositories with explicit evidence before implementation starts.\n",
        )

        result = assess_skill_registry_index_first_readiness(root=root)
        assert result["readiness_state"] == "blocked"
        assert "repo-audit:missing_behavior_json" in result["broken_skill_paths"]


def test_index_first_blocks_invalid_frontmatter():
    with _workspace_root() as root:
        _seed_rules(root)
        _make_skill(
            root,
            "repo-audit",
            markdown="---\nname repo-audit\ndescription: broken frontmatter\n---\n\n# Skill\n",
        )

        result = assess_skill_registry_index_first_readiness(root=root)
        assert result["readiness_state"] == "blocked"
        assert any(item.startswith("repo-audit:frontmatter_invalid_line") for item in result["invalid_frontmatter"])


def test_index_first_detects_duplicate_names():
    with _workspace_root() as root:
        _seed_rules(root)
        _make_skill(root, "repo-audit-a", skill_name="repo-audit")
        _make_skill(root, "repo-audit-b", skill_name="repo-audit")

        result = assess_skill_registry_index_first_readiness(root=root)
        assert result["readiness_state"] == "blocked"
        assert "repo-audit" in result["duplicate_names"]


def test_index_first_marks_missing_description_as_partial():
    with _workspace_root() as root:
        _seed_rules(root)
        _make_skill(
            root,
            "repo-audit",
            markdown="# Skill\n\nShort.\n",
        )

        result = assess_skill_registry_index_first_readiness(root=root)
        assert result["readiness_state"] == "partial"
        assert "repo-audit" in result["missing_descriptions"]
