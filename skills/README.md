# Skills

Atlas-native skills are reusable operating guides for high-frequency Atlas work.

Structure:
- `skills/<skill_name>/skill.md`: documentary guidance for humans and reviews
- `skills/<skill_name>/skill.json`: structured metadata for routing and minimal execution
- `skills/<skill_name>/behavior.json`: canonical behavior spec for the real execution helper
- `skills/project-bootstrap/bootstrap_contract.json`: canonical scaffold contract for the factory bootstrap skill

Minimum `skill.json` contract:
- `name`: must match the folder name
- `intent_keywords`: non-empty list used for metadata-first routing
- `agent`: must point to an existing file in `agents/`
- `workflow`: must point to an existing file in `workflows/`
- `model_profile`: must exist in `config/model_profiles.json`
- `risk_level`: one of `low`, `medium`, `high`
- `requires_human_approval`: boolean
- `supports_execution`: boolean
- `expected_outputs`: non-empty list describing the intended deliverables
- `validations`: non-empty list describing the checks that define a good skill outcome

Advanced operational contract:
- `required_inputs`: non-empty list of required inputs or an explicit list such as `["none"]` when the skill can run without extra inputs
- `safety_limits`: non-empty list of execution boundaries
- `rollback_manual`: non-empty list of manual rollback steps or an explicit list such as `["no rollback needed because the skill is read-only"]`
- `execution_mode`: one of `read_only`, `write_docs`, `write_code`
- `allowed_paths_policy`: one of `atlas_root_or_derived_project_read_only`, `explicit_output_dir_only`, `no_filesystem_writes`
- `forbidden_actions`: non-empty list of actions the skill must never take
- `human_approval_triggers`: non-empty list of situations that should escalate to human approval

Interpretation:
- `requires_human_approval` tells whether the default path already requires approval
- `human_approval_triggers` lists the situations that force escalation even when the default path is normally safe
- `allowed_paths_policy` is documentary governance metadata, not a sandbox replacement
- `forbidden_actions` and `human_approval_triggers` are consumed by the orchestrator before allowing execution
- `behavior.json` is the source of truth for what the helper actually does; governance cross-checks `skill.json` against it
- `bootstrap_contract.json` is the source of truth for the scaffold layout and bootstrap-specific execution contract; governance cross-checks it against `skill.json` and `behavior.json`

`behavior.json` contract:
- `writes_files`
- `writes_code`
- `uses_output_dir`
- `read_only`
- `execution_helper`
- `side_effects`
- `requires_project_path`
- `requires_output_dir`
- `can_run_without_approval`
- `notes`

`bootstrap_contract.json` contract for `project-bootstrap`:
- `required_inputs`
- `optional_inputs`
- `supported_project_types`
- `default_project_type`
- `generated_structure`
- `required_files`
- `optional_files`
- `forbidden_outputs`
- `default_output_mode`
- `templates_by_type`
- `initial_content`
- `rollback_manual`
- `validation_steps`
- `safety_limits`
- `human_approval_triggers`

Rules:
- add a skill only when it solves repeated Atlas work
- define owner, scope, trigger and validation
- keep business-specific skills out of the Atlas core
- skills guide decisions and outputs; they do not create hidden automation
- lifecycle decisions are governed by `policies/skill_lifecycle_policy.md` and `config/skill_lifecycle_rules.json`
- catalog hygiene reviews are governed by `policies/skill_improvement_review_policy.md` and `config/skill_improvement_review_rules.json`
- a proposed skill may stay `candidate` or be rejected even if the idea sounds useful; Atlas should prefer catalog hygiene over skill sprawl
- `skill_improvement_review` is advisory-only: it may recommend `keep`, `improve`, `merge`, `deprecate`, `archive` or external `candidate_review`, but it does not auto-install or auto-modify skills
- when external skill references are reviewed, Atlas should classify them explicitly as `adapt_now`, `design_later`, `watchlist` or `discard` before any human chooses to implement them

Current skills:
- `project-bootstrap`: start a derived project safely from Atlas
- `repo-audit`: inspect a repo or derived project before bigger changes
- `product-branding-review`: review product direction without generic output
- `visual-direction-checkpoint`: turn a vague brief into explicit audience, mood and originality signals
- `anti-generic-ui-audit`: run a read-only design audit with evidence, warnings and next action
- `design-system-review`: review typography, spacing, hierarchy and layout coherence without changing files
- `market-research-benchmark`: benchmark Atlas against `_reference/claude-vibecoding` and documented radar repos without scraping, installing or mutating anything
- `ui_pre_return_audit` (tool-level advisory): cross-check final UI readiness against visual intent, brand profile, CTA clarity, anti-generic risk and evidence before stronger PASS claims
- `creative_pipeline_readiness` (tool-level advisory): report whether logo, image, video, component-inspiration or visual-brand-review paths look locally ready without generating assets or activating providers
- `component_inspiration_readiness` (tool-level advisory): report whether 21st/Context7-backed component inspiration looks locally ready without generating components, activating MCPs or bypassing local design direction
- `playwright_visual_qa_readiness` (tool-level advisory): report whether Playwright and browser binaries look locally ready for future screenshot-based visual QA without opening browsers, capturing screenshots or activating automation
- `design_quality_enforcement` (tool-level advisory): treat visually weak UI as not ready for handoff when border weight, shadows, hierarchy, palette, typography or overall polish still read as amateur or wireframe-like
- `intent_clarifier_contract` (tool-level advisory): require clearer upstream answers for audience, domain, goal, style and originality before stronger design or handoff claims
- `brand_json_v2_readiness` (tool-level advisory): require an explicit governed brand artifact posture instead of relying on inferred identity alone
- `frontend_auto_audit_rules` (tool-level advisory): aggregate intent, brand, pre-return and design-quality guardrails before Atlas should treat a frontend as strongly ready
- `atlas_error_learning_review` (tool-level advisory): turn repeated UI, landing and integration mistakes into explicit readiness blockers before Atlas treats a surface as ready again
- `model_cost_control_readiness` (tool-level advisory): recommend mini/medium/strong cost posture, context trimming and split-task strategy without auto-switching models
- `codex_runtime_compatibility_check` (tool-level advisory): report what the local Codex runtime can actually do on this machine without mutating configuration or activating MCPs
- `atlas_memory_readiness` (tool-level advisory): report whether Atlas local-first memory artifacts are strong enough for continuity without enabling plugin memory, hooks or hidden reinjection
- `evidence_collector_readiness` (tool-level advisory): report what proof Atlas still needs before making a strong PASS claim for frontend, backend, research, high-risk decisions or governance changes

Execution model:
- skills default to documentary guidance
- only explicitly marked skills may support minimal safe execution
- execution must remain local, reversible and non-destructive

Optional lifecycle metadata:
- `lifecycle_state`: one of `candidate`, `experimental`, `stable`, `deprecated`, `archived`, `rejected`
- Atlas governance validates `lifecycle_state` only when it is declared; skills are not auto-promoted
- design-facing skills should align with `policies/visual_intent_contract_policy.md` and `config/visual_intent_contract_rules.json` before stronger UX or branding claims
- upstream-facing design work should align with `policies/intent_clarifier_contract_policy.md` and `config/intent_clarifier_contract_rules.json` before Atlas trusts a brief as directionally complete
- stronger identity claims should align with `policies/brand_json_v2_readiness_policy.md` and `config/brand_json_v2_readiness_rules.json` before Atlas treats branding as explicit instead of inferred
- branding-facing skills should align with `policies/brand_profile_schema_policy.md` and `config/brand_profile_schema_rules.json` before stronger identity or differentiation claims
- final UI-facing reviews should also align with `policies/design_quality_enforcement_policy.md` and `config/design_quality_enforcement_rules.json` before Atlas calls a surface visually ready
- final frontend readiness claims should also align with `policies/frontend_auto_audit_rules_policy.md` and `config/frontend_auto_audit_rules.json` before Atlas calls the local guardrail chain complete

Design-intelligence conventions:
- design skills must return `status`, `warnings`, `evidence` and `next_action`
- if a check cannot run, prefer `status: skipped` over a false PASS
- anti-generic checks should be warning-first unless there is clear evidence of risk
- evidence should cite real files, styles, typography, layout structure or other observable signals
