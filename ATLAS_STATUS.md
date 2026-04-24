# ATLAS Status

As of 2026-04-24, `C:\Proyectos\Codex-Atlas` is the canonical Codex-native base of ATLAS.

## Current capabilities

- Canonical root-first governance metadata under `commands/`, `policies/` and `memory/`
- Executable governance validator via `tools/atlas_governance_check.py`
- Executable minimal dispatcher via `tools/atlas_dispatcher.py`
- Executable suggestive orchestrator via `tools/atlas_orchestrator.py`
- First Atlas-native skills now exist in a structured format with `skill.md` and `skill.json`
- Governance now validates the minimum contract of each canonical `skill.json`
- Governance now validates the advanced operational contract of each canonical `skill.json`
- Governance now cross-checks declared skill behavior against the execution helper behavior spec
- Canonical behavior specs now live in `skills/<skill>/behavior.json`
- `project-bootstrap` now has a canonical external scaffold contract in `skills/project-bootstrap/bootstrap_contract.json`
- `project-bootstrap` now supports type-aware scaffolds for `backend_service`, `frontend_app`, `fullstack`, `internal_tool` and `ai_agent_system`
- `project-bootstrap` now renders README and AGENTS from external templates under `templates/project_bootstrap/`
- Governance now validates bootstrap templates for allowed placeholders, clean rendering and minimum section content
- Governance now scans bootstrap templates for unresolved or non-whitelisted placeholders in `{x}`, `{{x}}` and `${x}` formats
- One complete minimal workflow implemented: `audit-repo`
- Dedicated execution tests now cover `repo-audit`, `project-bootstrap` and `product-branding-review`
- Codex-native documentary base for agents, workflows, policies, commands, validators, memory and adapters
- Clear separation rule: ATLAS is the parent factory, REYESOFT is a derived runtime

## Closed blocks

- Canonical source of truth moved out of REYESOFT and established in `C:\Proyectos\Codex-Atlas`
- Minimal governance seed defined
- Minimal dispatcher defined
- First suggestive orchestration layer defined with configurable model and MCP profiles
- Structured skill system added with metadata-first routing and safe execution boundaries
- `project-bootstrap` contract formalized in documentation, metadata and execution output
- Skill metadata governance added for name, routing references, model profile, risk and output contract checks
- Advanced skill contract added for required inputs, safety limits, rollback, execution mode and approval triggers
- Orchestrator now considers forbidden actions and human approval triggers before allowing execution
- Behavior spec source of truth extracted from the orchestrator into per-skill canonical files
- `project-bootstrap` scaffold contract extracted into canonical metadata and removed from hardcoded execution rules
- REYESOFT no longer carries active Atlas core files and is handled externally through `.atlas-project.json`
- Root-level Atlas structure established as the primary home of mother configuration
- MCP integration explicitly blocked by policy for this stage
- Hook automation explicitly out of scope

## New skills already present

- `project-bootstrap`
- `repo-audit`
- `product-branding-review`
- The orchestrator now prioritizes `skill.json` metadata and can recommend these skills with structured output

## Role vs REYESOFT

- ATLAS defines reusable structure, governance and standards
- REYESOFT remains the derived product/runtime
- REYESOFT exposes only derived-project metadata and legacy artifacts marked for retirement
- Atlas operates on REYESOFT from outside using `--project`

## Governance status

- Status: active bootstrap
- Canonical registry exists and is validated
- Safe execution and approval policies are documented
- Model routing, MCP routing and cost control policies are documented
- Decision log, breadcrumbs and session summaries exist for continuity
- Governance check validates the root-first canonical structure, legacy compatibility mirrors and skill metadata contract
- Governance check validates advanced skill metadata including operational limits and approval escalation triggers
- Governance check also validates consistency between declared execution behavior and the helper behavior spec
- Governance check also validates the canonical bootstrap scaffold contract for `project-bootstrap`
- Governance check now validates that bootstrap templates only use the approved placeholder set and render without unresolved placeholders
- Orchestrator reads `behavior.json` per skill instead of keeping the behavior spec inline
- Orchestrator reads `bootstrap_contract.json` for `project-bootstrap` instead of reconstructing the scaffold contract inline

## Workflows status

- `audit-repo`: documented and executable
- `atlas_project_pipeline`: documented only
- `create_project`: documented with minimal scaffold execution through `project-bootstrap`
- `audit_project`: documented with minimal execution through `repo-audit`
- `certify_output`: documented only
- `orchestrator_routing`: documented and executable through the suggestive router

## Skill status

- Skills live under `skills/<skill_name>/skill.md` and `skills/<skill_name>/skill.json`
- `repo-audit` executes safely through the dispatcher
- `project-bootstrap` can create a minimal derived-project scaffold outside REYESOFT
- `project-bootstrap` now generates richer README and AGENTS templates plus profile-specific directories
- The README and AGENTS content no longer lives inline in the orchestrator; it is rendered from per-profile template files
- `project-bootstrap` now performs a real filesystem preflight for `output_dir` before allowing execution
- `product-branding-review` can return a structured checklist without touching files
- No skill introduces automatic execution, hooks or MCP activation
- Skill execution now has dedicated tests without creating new filesystem residue
- Skill governance now verifies `expected_outputs` and `validations` for every structured skill
- Skill governance now verifies `required_inputs`, `safety_limits`, `rollback_manual`, `execution_mode`, `allowed_paths_policy`, `forbidden_actions` and `human_approval_triggers`
- Skill governance now validates `bootstrap_contract.json` and its consistency with `skill.json` and `behavior.json`
- Skill governance now validates supported bootstrap project types and template metadata
- Skill governance now validates that each bootstrap profile points to real external template files
- Skill governance now validates rendered README and AGENTS template quality for every bootstrap profile
- Orchestrator output now reflects approval reasons and execution blockers derived from skill metadata and task wording
- Orchestrator output now includes bootstrap preflight status and `safe_to_execute` based on the real target path

## GitHub block status

- No GitHub-specific integration is active in this repo
- No deploy automation or external connector has been introduced
- `C:\Proyectos\Codex-Atlas` still lacks its own `.git` repository, which is an operational gap but not a runtime blocker

## Product context status

- Atlas is intentionally not a product app
- Product-specific context must stay in derived repos such as REYESOFT
- Atlas currently holds generic operating context, not business-domain runtime logic

## Legacy status

- `00_SISTEMA/_meta/atlas/` remains present only as a compatibility mirror
- Root-level directories are now the primary Atlas surface
- REYESOFT legacy Atlas artifacts were moved under `00_SISTEMA/_legacy/atlas_deprecated_2026-04-23/`
- Flat skill markdown files remain only as deprecated compatibility pointers because the environment denied file removal
- `skills/_legacy_flat/` exists as an empty blocked cleanup directory after a failed move attempt
- Existing blocked test residues remain under `tests/tmpik5_anpo`, `tests/_tmp_bootstrap_case`, `tests/_tmp_bootstrap_tests` and `tests/_tmp_template_validation` because the environment denied deletion
