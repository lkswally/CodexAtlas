# Decision Log

## 2026-04-23
- Decision: establish a Codex-native Level 1 bootstrap inside the canonical Atlas repo
- Reason: reduce drift, improve handoff between sessions and avoid depending on long chat context
- Impact: Atlas now has a stable documentary surface around the existing executable core
- Risk: the new structure can become stale if not reviewed alongside real changes
- Rollback: remove the new documentary directories and revert the governance checks that require them

## 2026-04-23
- Decision: move the mother configuration to root-level directories and keep `00_SISTEMA/_meta/atlas/` as a legacy mirror
- Reason: Atlas should feel Codex-native and should not hide its canonical configuration in a legacy seed path
- Impact: commands, policies and memory now have a primary home in the root structure
- Risk: temporary drift between the root-first canonical files and the legacy mirror
- Rollback: point the tooling back to the legacy seed as the primary path

## 2026-04-23
- Decision: create the first Atlas-native skills and connect them to the suggestive orchestrator
- Reason: Atlas needed real reusable guidance instead of an empty skills directory
- Impact: the router can now recommend `project-bootstrap`, `repo-audit` and `product-branding-review`
- Risk: skill routing is still heuristic and may need refinement as usage patterns become clearer
- Rollback: remove the skill markdown files and the skill recommendation layer from the orchestrator

## 2026-04-23
- Decision: evolve the first Atlas-native skills to a structured `skill.md` + `skill.json` format with minimal execution support
- Reason: Atlas needed a stronger contract between documentation, routing and safe execution without adding dangerous autonomy
- Impact: the orchestrator now prioritizes structured skill metadata, `repo-audit` can execute through the dispatcher, `project-bootstrap` can scaffold a safe minimal project, and `product-branding-review` can return a structured checklist
- Risk: duplicate legacy flat skill files can still confuse humans until they are removed cleanly
- Rollback: point the orchestrator back to heuristic-only routing and treat the new skill folders as documentary only

## 2026-04-24
- Decision: stabilize the Level 3B skill system before adding more capabilities
- Reason: Atlas needed cleanup, a formal `project-bootstrap` contract and side-effect-safe execution tests to avoid compounding fragility
- Impact: `project-bootstrap` now exposes a concrete contract, execution tests live in a dedicated file, and the test suite no longer creates new bootstrap residue
- Risk: the environment still blocks deletion of legacy flat skill files and old test residue folders
- Rollback: revert the contract additions and move execution assertions back into the general orchestrator tests

## 2026-04-24
- Decision: add governance validation for the minimum `skill.json` contract
- Reason: Atlas needed to guarantee that structured skills remain consistent with folders, agents, workflows, model profiles and expected outputs before adding more capabilities
- Impact: the governance check now validates each canonical skill metadata file and dedicated tests cover the skill governance layer
- Risk: future skill changes now have a stricter contract and will fail governance if docs and metadata drift
- Rollback: remove the skill metadata validation from the governance check and treat `skill.json` as advisory only

## 2026-04-24
- Decision: extend the skill metadata contract with advanced operational fields
- Reason: Atlas needed to make execution boundaries, forbidden actions and approval triggers explicit before adding more skills or autonomy
- Impact: each canonical skill now declares required inputs, safety limits, rollback guidance, execution mode, allowed path policy, forbidden actions and approval triggers, and governance validates them
- Risk: the contract is stricter and any future drift between metadata and actual execution helpers will fail governance
- Rollback: remove the advanced field checks and fall back to the previous minimum skill contract

## 2026-04-24
- Decision: validate consistency between declared skill behavior and real helper behavior, and surface approval logic in the orchestrator output
- Reason: Atlas needed to detect contradictions between metadata and execution before adding more capability or autonomy
- Impact: governance now cross-checks execution behavior specs, and the orchestrator exposes approval reasons, forbidden-action blockers and execution eligibility
- Risk: the inline behavior spec can drift if helpers change without updating the spec
- Rollback: remove the behavior-consistency check and revert the orchestrator to approval logic based only on intent and MCP requirements

## 2026-04-24
- Decision: move skill behavior specs out of the orchestrator and into per-skill `behavior.json` files
- Reason: Atlas needed a canonical external source of truth for helper behavior before the inline spec became hard to maintain
- Impact: the orchestrator now reads behavior metadata from `skills/<skill>/behavior.json`, and governance validates `skill.json` against those files
- Risk: there is now one more file per skill to keep aligned with the helper implementation
- Rollback: move the behavior spec back into the orchestrator and treat `behavior.json` as optional documentation only

## 2026-04-24
- Decision: externalize the `project-bootstrap` scaffold contract into `skills/project-bootstrap/bootstrap_contract.json`
- Reason: Atlas needed the factory bootstrap contract to be canonical metadata instead of logic reconstructed inside the orchestrator helper
- Impact: `project-bootstrap` execution now consumes a file-backed contract, and governance validates its consistency against `skill.json` and `behavior.json`
- Risk: the bootstrap contract can now drift as a third metadata layer if future scaffold changes skip governance
- Rollback: rebuild the contract inline in the orchestrator and treat `bootstrap_contract.json` as documentary only

## 2026-04-24
- Decision: move `project-bootstrap` execution preflight from fuzzy text triggers to real filesystem checks on `output_dir`
- Reason: the first factory test with `ATLAS_SANDBOX_DEMO` exposed false positives that blocked a legitimate scaffold request
- Impact: Atlas now separates textual forbidden actions from path safety checks and can decide `safe_to_execute` from the real target directory state
- Risk: path-based preflight still needs periodic review if Atlas starts supporting more derived-project layouts
- Rollback: revert to the previous orchestrator matching model and treat output directory safety as manual review only

## 2026-04-24
- Decision: upgrade `project-bootstrap` from a bare scaffold to a type-aware starter with richer templates
- Reason: the factory needed outputs that are useful enough to continue work without turning bootstrap into a runtime generator
- Impact: bootstrap now supports project profiles, richer README and AGENTS content, and profile-specific directories while preserving the same safety boundaries
- Risk: template quality can drift toward generic boilerplate if new profiles are added without review
- Rollback: revert to the previous minimal scaffold and remove project-type template hydration from the helper

## 2026-04-24
- Decision: externalize `project-bootstrap` README and AGENTS templates into per-profile files under `templates/project_bootstrap/`
- Reason: template text should not keep growing inside `atlas_orchestrator.py` now that profile-aware scaffolds exist
- Impact: the contract now references template files, the orchestrator renders them with simple variables, and governance validates that referenced template files exist
- Risk: template files can drift from the expected variable set if they evolve without tests
- Rollback: move the text rendering back into the helper and treat template files as documentation only

## 2026-04-24
- Decision: add governance validation for bootstrap template quality and reduce templates to an approved placeholder set
- Reason: Atlas needed to guarantee that profile templates render cleanly and do not drift into uncontrolled variable usage
- Impact: governance now checks placeholder allowlists, unresolved placeholders and minimum rendered section content for every bootstrap profile
- Risk: template edits are now stricter and will fail fast if someone adds undocumented render variables
- Rollback: remove the template-quality checks and allow free-form template variables again

## 2026-04-24
- Decision: keep the new invalid-template governance test side-effect free and document the first blocked cleanup residue instead of forcing deletion
- Reason: a first filesystem-backed version of the test left `tests/_tmp_template_validation` locked on Windows and Atlas should prefer auditable cleanup notes over risky force-removal
- Impact: the current governance test no longer writes temporary template files, and the blocked residue is now tracked explicitly in status/next-steps
- Risk: the locked residue still needs a later manual cleanup when the filesystem allows it
- Rollback: reintroduce filesystem-backed temp templates for the test and stop tracking the blocked residue

## 2026-04-24
- Decision: expand bootstrap template validation to catch placeholder drift across `{x}`, `{{x}}` and `${x}` formats
- Reason: Atlas needed to fail fast on unresolved or non-whitelisted placeholders even when someone uses a different common placeholder style by mistake
- Impact: governance findings now identify the affected template, profile, raw placeholder and a direct correction recommendation
- Risk: template validation is stricter and may surface legacy formatting mistakes immediately
- Rollback: narrow placeholder detection back to the previous `{{x}}`-only behavior

## 2026-04-24
- Decision: add `certify-project` as a read-only Atlas-native certification command for derived projects
- Reason: Atlas needed a Codex-native adaptation of the certification phase that validates derivative integrity without copying Claude-only infrastructure or touching runtime
- Impact: the dispatcher can now certify derived projects by checking metadata, minimum directories, profile-specific structure and absence of embedded Atlas core
- Risk: the certification checklist can drift if future bootstrap profiles evolve without updating the command
- Rollback: remove `certify-project` from the registry and treat certification as documentary only again

## 2026-04-24
- Decision: capture the deep `claude-vibecoding` assessment as Codex-native docs and policies instead of importing Claude runtime files
- Reason: Atlas needed to preserve the useful patterns from the reference repo without turning them into `.claude`, `CLAUDE.md`, hook or MCP dependencies
- Impact: Atlas now has an explicit `docs/codex_system_prompt.md`, a canonical reference assessment, stronger quality-gate policies and a clearer seven-phase pipeline
- Risk: the documentary layer can drift if future Atlas changes update workflows or policies without updating the assessment
- Rollback: remove the new docs and policies and fall back to the previous lighter guidance surface

## 2026-04-24
- Decision: add append-only observability logs for routing, governance and derived-project creation
- Reason: Atlas needed lightweight system visibility over time without introducing MCPs, hooks, external dependencies or runtime risk
- Impact: the orchestrator now logs structured decisions, `project-bootstrap` records created derivatives, and governance check records validation events under `memory/`
- Risk: observability can become noisy if future changes log too much detail or allow sensitive payloads into persistent files
- Rollback: remove the logging helpers, delete the new memory files and return to purely ad-hoc inspection

## 2026-04-24
- Decision: approve only `docs_search` as the first experimental read-only MCP and keep the rest denied or deferred
- Reason: Atlas needed one low-risk external context path for unstable docs and version checks, while GitHub, filesystem and Engram still carry either insufficient current value or broader risk
- Impact: MCP metadata, routing and governance now expose a single experimental read-only profile, and governance logs which experimental MCPs are active
- Risk: the experimental profile could expand informally if future edits ignore the one-experiment-at-a-time rule
- Rollback: set `experimental_enabled` to `false` for `docs_search`, keep all MCPs advisory-only, and re-run governance

## 2026-04-24
- Decision: add a governed MCP lifecycle manager before enabling any real connector
- Reason: Atlas needed explicit states and auditable transitions for MCP suggestions, approvals and dry-run execution before moving from policy to real integration
- Impact: `tools/atlas_mcp_manager.py` now manages `suggested`, `approval_required`, `approved`, `blocked` and `executed_simulated` states, and logs lifecycle events under `memory/`
- Risk: simulation could be mistaken for real connector execution if future tooling does not keep the distinction explicit
- Rollback: remove `tools/atlas_mcp_manager.py`, delete `memory/mcp_events.jsonl`, and revert MCP handling back to routing plus governance metadata only

## 2026-04-25
- Decision: keep real Docs MCP integration deferred on this machine and add a controlled internal `docs_search` adapter instead
- Reason: official OpenAI docs confirm Codex MCP support, but the local `~/.codex/config.toml` is not configured for `openaiDeveloperDocs` and `codex.exe` invocation is not verifiably operational from this environment
- Impact: Atlas can now execute approved `docs_search` requests through a read-only adapter over curated official OpenAI docs references, while preserving simulated fallback and explicit lifecycle logging
- Risk: the adapter can be mistaken for a verified real MCP integration if the distinction is not kept explicit in docs and logs
- Rollback: remove `tools/docs_search_adapter.py`, revert `tools/atlas_mcp_manager.py` to simulation-only behavior, and keep `docs_search` in advisory-only mode

## 2026-04-25
- Decision: improve `docs_search_adapter` output quality without expanding its trust boundary
- Reason: Atlas needed more useful and auditable docs-search results before considering any broader MCP evolution
- Impact: the adapter now ranks and deduplicates curated results, exposes structured summary and key points, and signals confidence plus potential staleness

## 2026-04-30
- Decision: strengthen landing quality gates using evidence-backed public-readiness checks adapted from the reference repo's visual-direction, anti-generic and readiness discipline
- Reason: Atlas needed to catch derived landings that work technically but still read like README or PDF exports, without inventing recommendations beyond verified evidence
- Impact: `design_intelligence_audit` now emits `landing_score`, `public_readiness`, CTA-integrity and documentation-density signals, and `quality_gate_report` exposes that readiness in one aggregated view
- Risk: static heuristics can still drift into noisy taste checks if future changes weaken the evidence threshold
- Rollback: remove the landing-specific checks and public-readiness aggregation, and fall back to the previous narrower design-intelligence surface

## 2026-04-30
- Decision: make landing-readiness claims explicit in `design_evidence_policy.md`
- Reason: the new landing checks needed a policy-level reminder that public-readiness is an evidence question, not a copywriting opinion
- Impact: Atlas now documents that README-like density, broken CTA paths and weak above-the-fold clarity must stay in `needs_improvement` until evidence changes
- Risk: none beyond keeping the policy synchronized with future design-audit heuristics
- Rollback: remove the landing-specific clauses from `design_evidence_policy.md`
- Risk: confidence and stale signals can become misleading if the curated catalog is not maintained
- Rollback: revert `tools/docs_search_adapter.py` to the previous minimal result format and loosen the new assertions in `tests/test_mcp_manager.py`

## 2026-04-25
- Decision: externalize the `docs_search` curated catalog into `config/docs_search_catalog.json` and govern freshness metadata centrally
- Reason: Atlas needed the official-doc references to be maintainable, auditable and validated outside the adapter code before expanding the experiment
- Impact: the adapter now reads a canonical external catalog, governance rejects duplicate or malformed entries, and freshness policy is explicit per entry
- Risk: the catalog becomes another file-backed source of truth that can drift if updates skip governance or review
- Rollback: move the small catalog back into `tools/docs_search_adapter.py` and remove the new governance checks for catalog structure and freshness

## 2026-04-25
- Decision: add a read-only docs catalog health report instead of relying on manual inspection for freshness maintenance
- Reason: Atlas needed a lightweight way to see catalog status, upcoming expiry and topic coverage without scraping the web or mutating the catalog
- Impact: `tools/docs_catalog_report.py` now summarizes entry counts, expiry windows, top topics and maintenance recommendations over `config/docs_search_catalog.json`
- Risk: report logic can drift from adapter freshness semantics if both evolve independently
- Rollback: remove `tools/docs_catalog_report.py`, drop its test/governance requirements, and rely on direct catalog inspection again

## 2026-04-25
- Decision: treat explicit no-deploy wording as a safety restriction, not as deploy intent
- Reason: the first real bootstrap for `CodexAtlas-Web` exposed a false positive where `no deploy` escalated approval and blocked a legitimate safe bootstrap
- Impact: the orchestrator now distinguishes negated deploy phrases from real deploy intent in both intent classification and approval reasons
- Risk: the phrase matcher is still heuristic and should be reviewed if more multilingual safety phrases are added
- Rollback: revert the deploy-negation matcher and return to the previous keyword-only behavior

## 2026-04-25
- Decision: adapt the design, branding and visual QA block from `claude-vibecoding` into a smaller Codex-native design intelligence layer
- Reason: Atlas needed a faithful but safe way to improve professional design review without importing `.claude`, hooks, Playwright MCP or Claude-only runtime assumptions
- Impact: Atlas now has dedicated design-intelligence agents, structured skills, policies, a workflow and a read-only audit helper for visual-direction checkpointing, anti-generic UI review and design-system review
- Risk: the new audit heuristics could drift into weak taste-based feedback if they are not kept evidence-first and warning-first
- Rollback: remove the design-intelligence skills, workflow, policies and helper, then revert orchestrator and governance requirements to the previous smaller skill catalog

## 2026-04-30
- Decision: keep the official OpenAI Developer Docs MCP unconfigured locally and retain `docs_search_adapter` as the active read-only path
- Reason: official OpenAI docs confirm the MCP exists and document `codex mcp add openaiDeveloperDocs --url https://developers.openai.com/mcp`, but this Windows Codex installation still fails with `Access is denied` for `codex --version`, `codex mcp --help` and `codex mcp list`, even when invoked directly and outside the sandbox
- Impact: Atlas now documents the official MCP path clearly, but continues to rely on adapter-backed execution plus approval and lifecycle logging instead of claiming a real MCP connection
- Risk: users may assume MCP can be turned on immediately because the package is installed, even though the CLI path is currently not operational on this machine
- Rollback: if Codex CLI becomes operational later, the rollback is conceptual rather than destructive: add the official MCP through the documented Codex command, verify it with `codex mcp list`, and then re-evaluate whether the adapter should remain only as fallback

## 2026-04-30
- Decision: adapt `Distribution Integrity + README Coherence` from the reference repo as a small Atlas-native read-only check
- Reason: Atlas already had drift between the canonical README and the real skill surface, and the reference repo's `UPGRADE_LOG.md` correctly treats README coherence as an audit phase, not as an afterthought
- Impact: Atlas now exposes `surface-audit`, the README lists the current skill surface correctly, and future drift can be detected through the dispatcher before public sharing
- Risk: if the checker becomes too strict, it could turn low-value phrasing drift into noisy warnings
- Rollback: remove `surface-audit`, drop its registry/test/governance requirements, and fall back to manual README review only

## 2026-04-30
- Decision: make design-intelligence recommendations derive strictly from warning or skipped evidence instead of generic summary text
- Reason: a real audit on `CodexAtlas-Web` showed that `next_action` could still mention a missing CTA even when the CTA check was already passing
- Impact: `design_intelligence_audit` now exposes `recommendation_sources`, removes corrective recommendations from PASS checks, and marks unverifiable checks as `skipped` with a reason
- Risk: stricter evidence coupling may make the audit feel less suggestive when only weak signals are available
- Rollback: revert the recommendation-source logic and return to the previous generic summary generation

## 2026-04-30
- Decision: add a read-only aggregated quality gate report on top of existing Atlas validators
- Reason: the reference repo treats readiness as a gated phase, and Atlas already had the underlying audits but not a single human-facing readiness summary
- Impact: `quality_gate_report` now consolidates `audit-repo`, `certify-project`, `surface-audit` and `design_intelligence_audit` into one readiness view without duplicating their logic
- Risk: the aggregator could become a shadow policy layer if it starts inventing rules instead of relaying existing outputs
- Rollback: remove `tools/quality_gate_report.py`, drop its test/governance requirement, and return to reviewing each validator independently

## 2026-05-01
- Decision: add explicit phase-awareness to derived-project commands using a read-only resolver instead of hooks or hidden runtime
- Reason: the reference repo's phase gates and readiness-before-handoff pattern fits Atlas, and the factory needed to stop `audit-repo` or `certify-project` from running outside their safe lifecycle context
- Impact: `project-phase-report` now resolves `idea -> planning -> bootstrap -> build -> audit -> certified`, dispatcher blocks out-of-phase actions explicitly, and `quality_gate_report` now exposes phase alignment
- Risk: phase inference can become noisy if metadata, scaffold signals and Atlas evidence drift apart
- Rollback: remove `tools/project_phase_resolver.py`, delete the dispatcher phase checks, and fall back to ungated read-only commands

## 2026-05-01
- Decision: add a read-only phase playbook on top of the resolver instead of teaching the lifecycle through hidden rules or ad-hoc prose
- Reason: Atlas already knew the current phase and could block bad commands, but it still did not guide users toward the right next move inside that phase
- Impact: `project-phase-report` and `quality_gate_report` now expose allowed commands, recommended next steps and common mistakes from `config/phase_playbook.json`
- Risk: guidance can become stale if the playbook stops matching the real dispatcher rules
- Rollback: remove `config/phase_playbook.json`, drop the extra guidance fields, and keep phase handling limited to detection plus blocking

## 2026-05-01
- Decision: add read-only intent, prompt and skill-evaluation guidance layers before expanding Atlas with more capabilities
- Reason: the reference repo's Intent Clarifier and readiness discipline show that Atlas benefits more from better explicit guidance than from adding more runtime surface or automation
- Impact: Atlas now exposes `project-intent-report`, `prompt-builder` and `skill-evaluator`, and `quality_gate_report` can summarize intent, next-step prompts and whether a reusable skill is really justified
- Risk: heuristic intent analysis can become noisy if it starts inferring too much from documentation-style text instead of stable metadata and explicit phrasing
- Rollback: remove the three helper tools, drop their dispatcher commands, and revert `quality_gate_report` to the previous readiness-only scope

## 2026-05-01
- Decision: add a small priority engine on top of existing outputs instead of adding more validators or automatic actions
- Reason: Atlas already had enough evidence surfaces, but still needed a cleaner answer to "what should happen first" when phase, design and intent signals coexist
- Impact: `quality_gate_report` now returns `execution_plan`, `primary_action` and `why_now`, with phase-aware conflict resolution and reduced noise
- Risk: the ranking layer could become opinionated drift if it starts inventing priorities outside the existing evidence sources
- Rollback: remove `tools/priority_engine.py`, delete the extra planning fields from `quality_gate_report`, and keep the gate as a pure aggregation surface

## 2026-05-02
- Decision: route Atlas recommendations against the real Codex models available locally, but keep switching recommendation-only until the Codex CLI can be verified safely
- Reason: Atlas needed model guidance that matches the actual Codex catalog on this machine, while the zero-assumption rule forbids guessing whether CLI switching or config mutation is safe
- Impact: `config/model_routing_rules.json` now maps Atlas task signals to the real local model set, `tools/model_router_core.py` reports missing information and confirmation requirements explicitly, and `quality_gate_report` plus `prompt_builder` now surface model recommendations without pretending they can auto-switch
- Risk: the router will intentionally ask for confirmation more often until planning-vs-execution intent and cost-vs-quality priorities are explicit
- Rollback: revert the routing catalog and `model_router` changes, and fall back to the previous profile-only recommendation layer

## 2026-05-02
- Decision: align the router with the exact Codex Desktop model names and expose auto-switch as `not_available` instead of implying config-based switching
- Reason: the desktop model list is known, but the local Codex CLI still returns `Access is denied`, so Atlas should recommend those real models without implying that switching can be executed safely
- Impact: the router now prefers `GPT-5.3-Codex` for standard implementation, emits `cost_saver_model` explicitly, and asks for confirmation when two real model choices remain equally reasonable
- Risk: some recommendations will become more conservative because the router now prefers explicit user confirmation over silent tie-breaking
- Rollback: revert the latest routing-rule and router-output adjustments and return to the previous recommendation wording

## 2026-05-02
- Decision: add per-action model recommendations to `quality_gate_report` by reusing the existing router on each `execution_plan` step
- Reason: Atlas already knew the global best-fit model, but users still needed to see which model best matched each concrete next action
- Impact: each execution-plan step now carries `recommended_model`, `fallback_model`, `cheaper_alternative_model`, `requires_user_confirmation` and `why_model` without duplicating routing logic or attempting auto-switch
- Risk: generic phase actions may still ask for confirmation more often, because Atlas keeps the zero-assumption rule at the step level too
- Rollback: remove the per-step enrichment helper from `quality_gate_report` and return to a single top-level model recommendation

## 2026-05-01
- Decision: add an append-only decision feedback log for Atlas recommendations instead of writing project state back into derived repos
- Reason: Priority outputs are only useful over time if Atlas can remember whether a recommendation was accepted, ignored, deferred or replaced without mutating the derived project itself
- Impact: `memory/decision_feedback.jsonl` and `tools/decision_feedback.py` now capture follow-up decisions, and `quality_gate_report` can surface relevant previous feedback when similar priorities reappear
- Risk: if reasons become vague, the log can accumulate noise instead of real learning signals
- Rollback: remove the feedback log and helper, drop the feedback section from `quality_gate_report`, and return to stateless recommendation reporting

## 2026-05-01
- Decision: use decision feedback only as a weighting layer on top of existing evidence, not as a hidden controller or second memory system
- Reason: the reference repo's evidence and readiness discipline fits Atlas best when historical decisions can lower repeated noise or reinforce proven actions without overriding phase or governance signals
- Impact: `tools/feedback_analyzer.py` now derives simple acceptance and ignore patterns from `memory/decision_feedback.jsonl`, `priority_engine` applies explicit feedback weights, and `quality_gate_report` exposes adjusted priorities plus detected patterns
- Risk: if weighting becomes too strong, Atlas could hide a valid recommendation just because it was ignored in a different context
- Rollback: remove `tools/feedback_analyzer.py`, drop feedback weighting from `priority_engine`, and keep decision feedback as a passive log only

## 2026-05-02
- Decision: add configurable routing, local error learning, reference scouting and MCP readiness checks as read-only intelligence layers on top of the current factory
- Reason: the `claude-vibecoding` reference is strongest when adapted as explicit intent, readiness and evidence discipline, not as hidden runtime or extra automation
- Impact: Atlas can now recommend model-profile aliases, analyze recurring local failure patterns, evaluate the reference repo with an effort/benefit matrix, and keep MCP real activation blocked with a verifiable readiness report
- Risk: if these layers start inventing conclusions beyond the available evidence, Atlas could become noisier instead of smarter
- Rollback: remove `tools/model_router.py`, `tools/error_pattern_analyzer.py`, `tools/repo_improvement_scout.py`, `tools/mcp_readiness_check.py` and the quality-gate sections that consume them
