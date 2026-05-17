from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple


DEFAULT_ROOT = Path(__file__).resolve().parents[1]
RULES_PATH = Path("config/skill_registry_index_first_rules.json")


def load_skill_registry_index_first_rules(root: Path = DEFAULT_ROOT) -> Dict[str, Any]:
    return json.loads((root / RULES_PATH).read_text(encoding="utf-8-sig"))


def _read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8-sig")


def _read_json(path: Path) -> Dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def _normalize_list(items: Any) -> List[str]:
    if not isinstance(items, list):
        return []
    output: List[str] = []
    for item in items:
        value = str(item).strip()
        if value and value not in output:
            output.append(value)
    return output


def _word_count(text: str) -> int:
    return len(re.findall(r"[A-Za-z0-9]+", str(text)))


def _skill_dirs(root: Path) -> List[Path]:
    skills_dir = root / "skills"
    if not skills_dir.exists():
        return []
    return sorted(path for path in skills_dir.iterdir() if path.is_dir() and not path.name.startswith("_"))


def _resolve_doc_path(skill_dir: Path, accepted_names: List[str]) -> Optional[Path]:
    for name in accepted_names:
        candidate = skill_dir / name
        if candidate.exists():
            return candidate
    return None


def _extract_section_text(markdown: str, heading: str) -> str:
    pattern = re.compile(
        rf"^##\s+{re.escape(heading)}\s*$([\s\S]*?)(?=^##\s+|\Z)",
        re.MULTILINE,
    )
    match = pattern.search(markdown)
    if not match:
        return ""
    return re.sub(r"\s+", " ", match.group(1)).strip(" -\n\t")


def _parse_frontmatter(markdown: str) -> Tuple[Optional[Dict[str, str]], Optional[str], str]:
    if not markdown.startswith("---\n") and not markdown.startswith("---\r\n"):
        return None, None, markdown

    lines = markdown.splitlines()
    if not lines or lines[0].strip() != "---":
        return None, "frontmatter_start_invalid", markdown

    closing_index: Optional[int] = None
    for index in range(1, len(lines)):
        if lines[index].strip() == "---":
            closing_index = index
            break
    if closing_index is None:
        return None, "frontmatter_not_closed", markdown

    raw_lines = lines[1:closing_index]
    body = "\n".join(lines[closing_index + 1 :])
    data: Dict[str, str] = {}
    pointer = 0

    while pointer < len(raw_lines):
        line = raw_lines[pointer]
        stripped = line.strip()
        pointer += 1

        if not stripped or stripped.startswith("#"):
            continue
        if ":" not in line:
            return None, "frontmatter_invalid_line", body

        key, raw_value = line.split(":", 1)
        key = key.strip()
        value = raw_value.strip()
        if not key:
            return None, "frontmatter_empty_key", body

        if value in {">", "|"}:
            multiline_mode = value
            chunks: List[str] = []
            while pointer < len(raw_lines):
                next_line = raw_lines[pointer]
                if next_line.startswith(" ") or next_line.startswith("\t"):
                    chunks.append(next_line.strip())
                    pointer += 1
                    continue
                break
            if not chunks:
                return None, f"frontmatter_empty_multiline:{key}", body
            data[key] = " ".join(chunks) if multiline_mode == ">" else "\n".join(chunks)
            continue

        data[key] = value.strip("\"'")

    return data, None, body


def _derive_description(frontmatter: Optional[Dict[str, str]], metadata: Dict[str, Any], markdown: str) -> str:
    if isinstance(frontmatter, dict):
        description = str(frontmatter.get("description", "")).strip()
        if description:
            return description

    purpose = _extract_section_text(markdown, "Purpose")
    if purpose:
        return purpose

    when_to_use = _extract_section_text(markdown, "When to use")
    if when_to_use:
        return when_to_use

    outputs = _normalize_list(metadata.get("expected_outputs"))
    if outputs:
        return f"Provides {', '.join(outputs[:3])}."

    return ""


def _derive_scope(frontmatter: Optional[Dict[str, str]], metadata: Dict[str, Any]) -> str:
    if isinstance(frontmatter, dict):
        scope = str(frontmatter.get("scope", "")).strip()
        if scope:
            return scope

    intent_keywords = _normalize_list(metadata.get("intent_keywords"))
    if intent_keywords:
        return ", ".join(intent_keywords[:3])

    workflow = str(metadata.get("workflow", "")).strip()
    agent = str(metadata.get("agent", "")).strip()
    if workflow and agent:
        return f"{workflow} via {agent}"
    if workflow:
        return workflow
    if agent:
        return agent
    return "atlas_skill"


def assess_skill_registry_index_first_readiness(
    *,
    root: Path = DEFAULT_ROOT,
) -> Dict[str, Any]:
    rules = load_skill_registry_index_first_rules(root)
    accepted_doc_names = _normalize_list(rules.get("accepted_skill_doc_names"))
    valid_lifecycle_states = set(_normalize_list(rules.get("valid_lifecycle_states")))
    minimum_words = int((rules.get("description_rules") or {}).get("minimum_words", 8))

    broken_skill_paths: List[str] = []
    invalid_frontmatter: List[str] = []
    duplicate_names: List[str] = []
    missing_descriptions: List[str] = []
    invalid_lifecycle_states: List[str] = []
    skills_index: List[Dict[str, Any]] = []
    seen_names: Dict[str, str] = {}

    for skill_dir in _skill_dirs(root):
        doc_path = _resolve_doc_path(skill_dir, accepted_doc_names)
        metadata_path = skill_dir / "skill.json"
        behavior_path = skill_dir / "behavior.json"

        if doc_path is None:
            broken_skill_paths.append(f"{skill_dir.name}:missing_skill_doc")
            continue
        if not metadata_path.exists():
            broken_skill_paths.append(f"{skill_dir.name}:missing_skill_json")
            continue
        if not behavior_path.exists():
            broken_skill_paths.append(f"{skill_dir.name}:missing_behavior_json")
            continue

        try:
            markdown = _read_text(doc_path)
            metadata = _read_json(metadata_path)
        except Exception:
            broken_skill_paths.append(f"{skill_dir.name}:unreadable_metadata_or_doc")
            continue

        frontmatter, frontmatter_error, body_markdown = _parse_frontmatter(markdown)
        if frontmatter_error:
            invalid_frontmatter.append(f"{skill_dir.name}:{frontmatter_error}")

        name = str(metadata.get("name", "")).strip() or skill_dir.name
        description = _derive_description(frontmatter, metadata, body_markdown)
        scope = _derive_scope(frontmatter, metadata)
        lifecycle_state = str(metadata.get("lifecycle_state", "")).strip()
        if lifecycle_state and lifecycle_state not in valid_lifecycle_states:
            invalid_lifecycle_states.append(f"{skill_dir.name}:{lifecycle_state}")

        if _word_count(description) < minimum_words:
            missing_descriptions.append(skill_dir.name)

        lowered_name = name.lower()
        previous_owner = seen_names.get(lowered_name)
        if previous_owner and previous_owner != skill_dir.name:
            duplicate_names.append(name)
        else:
            seen_names[lowered_name] = skill_dir.name

        skills_index.append(
            {
                "name": name,
                "description": description,
                "scope": scope,
                "path": str(doc_path),
                "lifecycle_state": lifecycle_state or "undeclared",
                "risk_level": str(metadata.get("risk_level", "")).strip() or "unknown",
                "agent": str(metadata.get("agent", "")).strip() or "unknown",
                "workflow": str(metadata.get("workflow", "")).strip() or "unknown",
            }
        )

    duplicate_names = sorted(set(duplicate_names))
    missing_descriptions = sorted(set(missing_descriptions))
    invalid_frontmatter = sorted(set(invalid_frontmatter))
    broken_skill_paths = sorted(set(broken_skill_paths))
    invalid_lifecycle_states = sorted(set(invalid_lifecycle_states))

    if broken_skill_paths or duplicate_names or invalid_frontmatter:
        readiness_state = "blocked"
        status = "needs_attention"
    elif missing_descriptions or invalid_lifecycle_states:
        readiness_state = "partial"
        status = "needs_attention"
    else:
        readiness_state = "ready"
        status = "ok"

    why = (
        "Atlas can use an index-first registry safely only when skill files are resolvable, descriptions are strong enough for metadata-first routing, and the registry can point to the canonical markdown instructions without carrying their full body by default."
    )

    return {
        "status": status,
        "readiness_state": readiness_state,
        "skills_indexed": len(skills_index),
        "broken_skill_paths": broken_skill_paths,
        "invalid_frontmatter": invalid_frontmatter,
        "duplicate_names": duplicate_names,
        "missing_descriptions": missing_descriptions,
        "invalid_lifecycle_states": invalid_lifecycle_states,
        "skills_index": skills_index,
        "index_first_safe_to_use": readiness_state != "blocked",
        "why": why,
        "advisory_only": bool(rules.get("advisory_only", True)),
    }


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(add_help=True)
    args = parser.parse_args(argv)
    result = assess_skill_registry_index_first_readiness(root=DEFAULT_ROOT)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
