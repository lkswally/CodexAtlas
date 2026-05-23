# Templates

This directory is reserved for reusable Atlas templates.

Level 1 rule:
- keep the directory present but empty of heavy scaffolds
- add templates only after the workflow and adapter contract are stable

Current lightweight assets:
- `project/AGENTS.md.template`: global governance bootstrap template for local AGENTS files
- `project/.atlas-project.json.template`: global governance bootstrap template for derived-project metadata
- `project/SPRINT_STATUS.md.template`: global governance bootstrap template for minimum sprint/status tracking
- `project_bootstrap_profiles.md`: reference for type-aware project-bootstrap scaffolds
- `project_bootstrap/<profile>/README.md.template`: README template per bootstrap profile
- `project_bootstrap/<profile>/AGENTS.md.template`: AGENTS template per bootstrap profile
- `project_bootstrap/PROJECT_STATUS.md.template`: shared project status template for derived-project governance bootstrap

Template quality rules:
- only these placeholders are allowed in Atlas templates: `project_name`, `project_type`, `project_goal`, `scope`, `atlas_root`, `generated_from_skill`
- governance must fail if a referenced template uses any other placeholder, whether it appears as `{placeholder}`, `{{placeholder}}` or `${placeholder}`
- governance must fail if a rendered template still leaves unresolved placeholders in any of those common formats
- governance must fail if a profile template misses the minimum expected README or AGENTS sections declared by `bootstrap_contract.json`
