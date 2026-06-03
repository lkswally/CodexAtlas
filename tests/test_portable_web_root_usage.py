from pathlib import Path

from tests._support_paths import ATLAS_ROOT


TARGET_FILES = [
    "tests/test_project_intent.py",
    "tests/test_design_intelligence_audit.py",
    "tests/test_skill_execution.py",
    "tests/test_repo_graph_readiness.py",
]


def test_web_root_related_tests_do_not_hardcode_local_codexatlas_web_paths():
    forbidden_patterns = [
        "C:" + "\\Proyectos\\CodexAtlas-Web",
        "C:/Proyectos/CodexAtlas-Web",
        'ROOT.parent / "CodexAtlas-Web"',
    ]
    offenders: dict[str, list[str]] = {}

    for relative_path in TARGET_FILES:
        content = (ATLAS_ROOT / relative_path).read_text(encoding="utf-8")
        matches = [pattern for pattern in forbidden_patterns if pattern in content]
        if matches:
            offenders[relative_path] = matches

    assert offenders == {}
