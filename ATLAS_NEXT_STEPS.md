# ATLAS Next Steps

This document captures the next safe moves after the post-Level 3B stabilization pass.

## Suggested priority

1. Use the current baseline for the first real project bootstrap test
2. Consolidate the documentary core and keep it current with real decisions
3. Evolve the suggestive orchestrator carefully before adding any autonomy
4. Use the new skill lifecycle layer before approving any new reusable Atlas skill

## Review before building

- Confirm that new pieces improve Atlas as a reusable factory rather than as a product app
- Separate what should stay global in Codex from what belongs inside Atlas
- Check that every new workflow has a human approval boundary if it can mutate project state
- Keep REYESOFT adapters local and do not pull REYESOFT-specific logic into Atlas core
- Revalidate the registry and project state whenever the structure changes
- Preserve compatibility for derived-project metadata and the legacy mirror while the retirement plan is still open
- Keep model and MCP profile catalogs configurable instead of turning one provider choice into a permanent rule
- Add skills only when the orchestrator can justify them clearly
- Use `skill_lifecycle_policy` and `skill_lifecycle_rules.json` before promoting a skill beyond `candidate`
- Keep execution tests side-effect free unless a real filesystem write is the behavior under test
- Preserve the skill metadata contract if any future skill is added
- Keep advanced operational fields aligned with real execution behavior, not just documentation
- Keep approval reasons and execution blockers explainable to humans, not just technically correct
- Keep `behavior.json` synchronized with helper implementations whenever execution changes
- Keep `bootstrap_contract.json` synchronized with the actual scaffold that `project-bootstrap` generates
- Keep bootstrap preflight rules aligned with real target-path safety constraints as Atlas creates more derived projects
- Keep type-specific template content useful without letting bootstrap turn into a runtime generator
- Keep external bootstrap templates aligned with contract variables so rendering stays predictable
- Keep the allowed bootstrap placeholder set intentionally small so templates stay governable and readable
- Keep template authors on the canonical placeholder syntax even though governance now checks several common formats for drift
- Keep `certify-project` aligned with the bootstrap contract so certification reflects the real factory output instead of drifting into a separate checklist
- Keep `docs/codex_system_prompt.md` and `AGENTS.md` aligned so Atlas does not grow two competing instruction surfaces
- Keep the Claude-vibecoding assessment current if Atlas adopts or rejects new reference patterns
- Keep `surface-audit` aligned with the real public Atlas surface so README drift is caught early, not after release
- Keep manual quality-gate policies stronger than the repo narrative, not weaker
- Keep observability logs append-only, lightweight and free of sensitive task payloads
- Keep the MCP experiment limited to a single read-only profile until Atlas proves the governance model holds
- Keep MCP lifecycle transitions explicit so approval and simulation do not turn into implicit connector activation
- Keep the internal docs adapter clearly separated from any future real MCP runtime integration
- Do not introduce a project-scoped `.codex/config.toml` for OpenAI Docs MCP until a working Codex CLI path proves that this local build can execute and verify MCP configuration
- Keep the docs adapter catalog fresh enough that confidence and stale signals remain meaningful
- Keep `config/docs_search_catalog.json` auditable and small enough that freshness maintenance stays realistic
- Use `tools/docs_catalog_report.py` before catalog edits so freshness and topic coverage decisions stay evidence-based
- Keep the first real project test narrowly scoped so Atlas is validating the factory, not attempting a product build in one step
- Keep the design-intelligence layer read-only until repeated audits prove its heuristics are useful and low-noise
- Keep design-intelligence checks evidence-first and warning-first unless a clear risk justifies stronger escalation
- Keep design-intelligence recommendation generation tied to the originating checks so `next_action` and `quick_wins` do not drift into generic advice
- Keep `quality_gate_report` as an aggregator over existing validators so readiness decisions do not fork into a second logic layer
- Observe the new phase-aware gating on a few more derived projects before expanding it beyond `bootstrap`, `audit` and `certified`
- Prefer stronger metadata or read-only evidence sources before adding more phase heuristics
- Keep `config/phase_playbook.json` aligned with real factory behavior so guidance stays useful and does not drift into cargo-cult advice
- Keep `project_intent_analyzer` aligned with explicit brief and metadata signals so it does not reintroduce the kind of false positives Atlas already removed from deploy intent detection
- Keep `model_router` alias-driven and configurable so Atlas can change provider strategy without rewriting routing logic
- Keep `model_router` tied to the visible Codex Desktop model list and ask before deciding when planning-vs-execution, cost-vs-quality or safe model switching are not explicit
- Keep model-routing outputs explicit about runtime limits: recommendations are advisory/manual until Codex model switching is verifiably available in this environment
- Keep `model_cost_control_readiness` advisory-only and conservative; it should prefer trimming context, splitting tasks and cheaper tiers before Atlas recommends a stronger model
- Keep `prompt_builder` phase-aware and explicit so it teaches the flow without becoming hidden automation
- Keep `prompt_builder` tied to real priority, feedback and validation signals instead of drifting back toward generic task templates
- Keep `skill_evaluator` conservative; it should block capability sprawl more often than it approves new reusable skills
- Keep `skill_improvement_review` advisory and hygiene-first; it should recommend review, merge or deprecate before Atlas grows the catalog
- Keep `skill_improvement_review` explicit about curated external-radar fit: `adapt_now`, `design_later`, `watchlist` or `discard` should stay reviewable instead of drifting into hidden trend-following
- Keep `visual_intent_contract` advisory and evidence-first until repeated usage proves that stronger gating would reduce generic design drift without over-blocking simple projects
- Keep `visual_intent_contract` aligned across `project_intent_analyzer`, `visual-direction-checkpoint`, `brand_agent`, `design_intelligence_audit` and `quality_gate_report`
- Keep `intent_clarifier_contract` strict enough that UI-facing work cannot rely on mostly inferred audience, domain or goal answers
- Keep `brand_profile_schema` aligned with the visual intent contract so identity, differentiation and accessibility rationale do not drift into generic branding language
- Keep `brand_json_v2_readiness` explicit-artifact-first; inferred brand structure should inform review, not replace a documented identity baseline
- Keep brand-profile warnings advisory and evidence-first until Atlas has enough repeated usage to justify stronger gating for public-facing UI work
- Keep `ui_pre_return_audit` advisory until Atlas has stronger visual proof inputs, but use it to prevent unsupported “UI ready” claims and generic handoff decisions
- Keep `frontend_auto_audit_rules` focused on local guardrails and evidence expectations; screenshot collection, fidelity judging and stronger final reality checks should stay in readiness/watchlist until separately approved
- Keep `atlas_error_learning_review` evidence-first and local-only; it should capture repeated real failures without turning hindsight into noisy pseudo-memory
- Keep `codex_runtime_compatibility_check` aligned with the real local Codex CLI surface so Atlas never communicates advisory runtime support as if it were active automation
- Keep `atlas_memory_readiness` local-first and reviewable; it should make current continuity explicit without drifting into hidden prompt reinjection, plugins or sync
- If the contract proves consistently useful, decide later whether it should become a stronger certification prerequisite for public-facing UI work
- Keep `error_pattern_analyzer` evidence-first so it reports recurring Atlas failure modes without turning log noise into fake system-learning claims
- Keep `repo_improvement_scout` anchored to the local reference clone and explicit effort/benefit tradeoffs, not to trend-chasing features
- Keep `mcp_readiness_check` read-only and approval-bound even though the local Codex CLI is now callable and `openaiDeveloperDocs` is visible
- Keep `priority_engine` as a ranking layer over existing evidence, not as a second policy engine with its own hidden rules
- Keep per-action model recommendations tied to the existing router so `execution_plan` guidance stays explainable instead of growing a second routing logic
- Keep landing-quality checks evidence-first and warning-first so Atlas catches README-like public pages without over-blocking intentionally simple derived sites
- Keep `atlas_verify` as a thin wrapper over existing checks; if it grows new logic, that logic should move back into the canonical validators instead
- Keep `decision-council` reserved for genuinely high-risk or conflicting decisions so Atlas does not turn routine work into ceremony
- Use `market-research-benchmark` before adding roadmap features that come mainly from external reference pressure rather than repeated Atlas-local need
- Keep visual/media capability decisions advisory-only until a derived project repeatedly needs screenshot, image or video evidence that static audits cannot provide
- Keep `creative_pipeline_readiness` advisory-only and approval-bound; readiness is not permission to generate assets or activate MCPs
- Keep `component_inspiration_readiness` advisory-only and local-first; readiness is not permission to copy external UI, activate 21st/Context7 or treat pattern browsing as proof of quality
- Keep `playwright_visual_qa_readiness` advisory-only and approval-bound; environment readiness is not permission to run browser automation or treat screenshots as a substitute for design intent, brand direction or accessibility review
- Keep `design_quality_enforcement` strict enough to block visually weak handoff claims, but evidence-first enough that it does not confuse intentional minimalism with accidental low fidelity
- Keep external model fallback evaluation separate from Codex Desktop model routing; benchmark NVIDIA candidates manually before adding any profile or adapter
- Keep `21st_magic` disabled until the exposed key is revoked, a fresh key is stored outside the repo, and a separate approval allows a controlled MCP test
- Keep `repo_graph_readiness` in watchlist/design-only posture until Atlas proves a local graph would reduce context materially without adding dependency or maintenance drag
- Keep memory automation in watchlist posture; if Atlas ever revisits it, prefer a local-first summary/readiness path before any plugin, hook or auto-injection runtime
- Keep `atlas_memory_readiness` honest about the current boundary: local files are useful continuity, not autonomous memory
- Keep `evidence_collector_readiness` strict about strong PASS language; advisory confidence is not the same thing as proof
- Fix known public placeholder links in derived landings before treating design readiness as anything stronger than `needs_improvement`
- Keep `design_evidence_policy.md` aligned with landing-readiness heuristics so public-facing PASS states always have traceable proof

## Possible future improvements

- A first real derived project created from Atlas and immediately audited/certified
- Atlas-native skill set for audit, planning and factory governance
- Reusable project templates with adapter placeholders
- Documentary pipeline for intent, planning, architecture, implementation review and certification
- Read-only quality-gate helpers for evidence, boundary and template checks if they prove reusable beyond current governance
- Stronger certification summaries that can be consumed by future handoff or reporting layers without adding autonomy
- Manual validator bundle for architecture drift and boundary checks
- Optional richer design-evidence helpers only after the current static-file audit path proves useful
- A read-only `visual_evidence_brief` skill if repeated projects need manual screenshot/reference collection before design review
- A manual NVIDIA fallback benchmark report if external-model fallback becomes a real operational need
- Small read-only observability summaries built on top of the new routing and governance logs
- A second controlled MCP only after the first one proves useful without broadening Atlas risk
- Stronger docs for derived-project extraction and adapter contracts
- A second-level orchestrator that can consume structured task metadata instead of only free text
- Skill-aware routing with richer signals than keyword matching
- Keep `market-research-benchmark` advisory and explicit; if it grows, prefer richer local reference payloads before any web or MCP expansion
- Optional skill manifest validation inside governance check if the catalog grows
- Controlled retirement plan for `00_SISTEMA/_meta/atlas/` once no consumers need it
- Better release hygiene around commit cadence, ignored local research clones and validation reports

## Watchlist

- Python version compatibility between Atlas tooling and old REYESOFT environments
- Double source of truth risk if derived repos start copying Atlas docs again
- Pressure to add MCP or hooks too early
- Confusing `codex mcp list` success with a configured and authenticated MCP server
- Treating the disabled `21st_magic` watchlist profile as permission to use a previously exposed API key
- Pressure to turn Atlas into a product runtime instead of a factory layer
- Claude-inspired patterns re-entering as hidden runtime assumptions instead of explicit Codex-native policies
- Deprecated flat skill files lingering too long beside canonical `skill.md` and `skill.json`
- Locked bootstrap residue under `tests/` becoming a persistent cleanliness issue
- Drift between root-first canonical files and the legacy mirror
- Hardcoded routing logic growing faster than the profile catalogs
- Skill metadata drifting between `skill.md`, `skill.json` and execution behavior
- Approval triggers and forbidden actions becoming decorative instead of actionable governance metadata
- Negated safety constraints like `no deploy` drifting back into false-positive approval or intent matches
- `behavior.json` diverging from helper implementations over time
- `bootstrap_contract.json` drifting away from the real scaffold helper or from `skill.json`
- type-aware templates becoming generic again as more project profiles are added
- external templates diverging from supported render variables or from per-profile contract metadata
- template quality checks becoming weaker than the actual bootstrap output as profiles evolve
- certification rules drifting away from the real bootstrap contract or from derived-project metadata
- observability logs growing without retention or summary rules
- MCP profile sprawl diluting the default-deny rule
- MCP approvals becoming implicit or durable without a clearer revocation policy
- Simulated MCP execution drifting away from the declared lifecycle or being confused with a real connector
- The docs adapter being mistaken for a verified real Codex MCP runtime on machines where `codex mcp` is not operational
- README and public-facing docs drifting behind the real Atlas command, skill and workflow surface as the factory evolves
- The Windows Store Codex package continuing to expose `codex.exe` while denying CLI execution, creating false confidence that MCP setup is available locally
- Confusing `codex_runtime_compatibility_check` or `mcp_readiness_check` with permission to mutate runtime, switch models or activate new MCPs automatically
- Confusing `atlas_memory_readiness` with permission to add automatic memory, hidden reinjection or cross-machine sync
- Treating `evidence_collector_readiness` as if inferred checks were equivalent to real screenshots, build proof or explicit human decision evidence
- The docs adapter confidence signal becoming noisy if ranking and verification dates drift from the curated catalog
- The curated docs catalog drifting because `last_verified` stops being updated or deprecated entries remain active too long
- The catalog report becoming disconnected from adapter semantics if freshness logic changes in one place but not the other
- Design-intelligence checks drifting into taste-only opinions instead of evidence-backed review
- Pressure to recreate Playwright-driven Claude QA before Atlas actually needs browser automation
- Pressure to implement repo graphs or memory runtimes before Atlas has enough repeated evidence that the extra surface would actually save context
- Anti-generic heuristics becoming brittle or over-blocking for intentionally simple internal tools
- Landing-readiness heuristics drifting into copy taste instead of verifiable public-facing quality signals
- Too many low-value skills diluting Atlas-native guidance
- Decision feedback becoming noisy if teams log vague reasons instead of concrete acceptance, deferral or replacement rationale

## Do not touch yet

- REYESOFT runtime modules
- Automatic deployment flows
- MCP connectors
- Automatic hooks or self-healing loops
- Large agent fleets copied from Claude-oriented repos
- Browser-driven visual automation copied from the reference repo before Atlas has a safe local need
- Design intelligence datasets without a real Atlas use case
- External model adapters before manual benchmark evidence proves the value
- Image or video generation agents inside Atlas core
- Automatic write-back from decision logs into derived projects
- Repository graph generators, memory plugins or RAG layers that require installs, background workers or hidden reinjection

## Recommended Level 2

- Introduce template skeletons for derived projects
- Add boundary validation docs for adapters vs canonical core
- Decide when the legacy mirror can be reduced or removed
- If routing proves stable, consider a structured task input schema for the orchestrator
- Consider a small skill metadata index if the skill set grows
- Decide whether the next step is richer skill matching or validator coverage for skill metadata
- Keep inaccessible local temp residue out of commits if the filesystem recreates blocked `pytest-cache-files-*` or similar directories
- If the skill catalog grows, decide whether governance should validate cross-field consistency between `execution_mode`, `allowed_paths_policy` and actual execution helpers
- If behavior metadata grows more complex, consider a shared schema or validator helper for `behavior.json`
- If skill execution contracts keep growing, consider a shared schema or validator helper for `bootstrap_contract.json` and similar future skill contracts
- If bootstrap profiles grow further, consider moving rendered text blocks into dedicated template files while keeping the contract as the source of truth
- If templates become significantly richer, consider a tiny dedicated renderer helper or template validator to catch unresolved placeholders early
- If template complexity keeps growing, consider moving repeated static sections into shared partials without expanding the placeholder surface
- If certification grows further, consider extracting its checks into a shared validator helper while keeping `atlas_dispatcher.py` small
- Keep the GitHub repo clean of `_reference/`, test residue and personal local artifacts
- If decision feedback becomes common, consider a small read-only summary layer that groups recurring acceptance and deferral patterns without turning memory into a second policy engine
- Watch for feedback weighting drifting into hidden personalization if the acceptance and ignore rules stop being explicit and reviewable
- Watch for model-routing aliases drifting away from the real `config/model_profiles.json` catalog
- Watch for real Codex model-routing rules drifting away from the locally verified model list or from the zero-assumption confirmation policy
- Watch for system-learning suggestions drifting into silent action-taking instead of remaining report-only
## External Sources

- If Atlas ever operationalizes external-source routing, keep it opt-in and read-only first.
- Reuse `external_tool_policy` before adding any automatic MCP or CLI escalation.
