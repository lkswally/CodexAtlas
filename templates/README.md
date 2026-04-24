# Templates

This directory is reserved for reusable Atlas templates.

Level 1 rule:
- keep the directory present but empty of heavy scaffolds
- add templates only after the workflow and adapter contract are stable

Current lightweight assets:
- `project_bootstrap_profiles.md`: reference for type-aware project-bootstrap scaffolds
- `project_bootstrap/<profile>/README.md.template`: README template per bootstrap profile
- `project_bootstrap/<profile>/AGENTS.md.template`: AGENTS template per bootstrap profile

Template quality rules:
- only these placeholders are allowed in bootstrap templates: `project_name`, `project_type`, `project_goal`, `scope`, `atlas_root`, `generated_from_skill`
- governance must fail if a referenced template uses any other placeholder, whether it appears as `{placeholder}`, `{{placeholder}}` or `${placeholder}`
- governance must fail if a rendered template still leaves unresolved placeholders in any of those common formats
- governance must fail if a profile template misses the minimum expected README or AGENTS sections declared by `bootstrap_contract.json`
