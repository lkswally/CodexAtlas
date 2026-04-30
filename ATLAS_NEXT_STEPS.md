# ATLAS Next Steps

This document captures the next safe moves after the post-Level 3B stabilization pass.

## Suggested priority

1. Use the current baseline for the first real project bootstrap test
2. Consolidate the documentary core and keep it current with real decisions
3. Remove blocked deprecated flat skill pointers once filesystem access allows deletion
4. Remove blocked test residue folders once filesystem access allows deletion
5. Evolve the suggestive orchestrator carefully before adding any autonomy

## Review before building

- Confirm that new pieces improve Atlas as a reusable factory rather than as a product app
- Separate what should stay global in Codex from what belongs inside Atlas
- Check that every new workflow has a human approval boundary if it can mutate project state
- Keep REYESOFT adapters local and do not pull REYESOFT-specific logic into Atlas core
- Revalidate the registry and project state whenever the structure changes
- Preserve compatibility for derived-project metadata and the legacy mirror while the retirement plan is still open
- Keep model and MCP profile catalogs configurable instead of turning one provider choice into a permanent rule
- Add skills only when the orchestrator can justify them clearly
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

## Possible future improvements

- A first real derived project created from Atlas and immediately audited/certified
- Atlas-native skill set for audit, planning and factory governance
- Reusable project templates with adapter placeholders
- Documentary pipeline for intent, planning, architecture, implementation review and certification
- Read-only quality-gate helpers for evidence, boundary and template checks if they prove reusable beyond current governance
- Stronger certification summaries that can be consumed by future handoff or reporting layers without adding autonomy
- Manual validator bundle for architecture drift and boundary checks
- Optional richer design-evidence helpers only after the current static-file audit path proves useful
- Small read-only observability summaries built on top of the new routing and governance logs
- A second controlled MCP only after the first one proves useful without broadening Atlas risk
- Stronger docs for derived-project extraction and adapter contracts
- A second-level orchestrator that can consume structured task metadata instead of only free text
- Skill-aware routing with richer signals than keyword matching
- Optional skill manifest validation inside governance check if the catalog grows
- Controlled retirement plan for `00_SISTEMA/_meta/atlas/` once no consumers need it
- Better release hygiene around commit cadence, ignored local research clones and validation reports

## Watchlist

- Python version compatibility between Atlas tooling and old REYESOFT environments
- Double source of truth risk if derived repos start copying Atlas docs again
- Pressure to add MCP or hooks too early
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
- The docs adapter confidence signal becoming noisy if ranking and verification dates drift from the curated catalog
- The curated docs catalog drifting because `last_verified` stops being updated or deprecated entries remain active too long
- The catalog report becoming disconnected from adapter semantics if freshness logic changes in one place but not the other
- Design-intelligence checks drifting into taste-only opinions instead of evidence-backed review
- Pressure to recreate Playwright-driven Claude QA before Atlas actually needs browser automation
- Anti-generic heuristics becoming brittle or over-blocking for intentionally simple internal tools
- Too many low-value skills diluting Atlas-native guidance

## Do not touch yet

- REYESOFT runtime modules
- Automatic deployment flows
- MCP connectors
- Automatic hooks or self-healing loops
- Large agent fleets copied from Claude-oriented repos
- Browser-driven visual automation copied from the reference repo before Atlas has a safe local need
- Design intelligence datasets without a real Atlas use case

## Recommended Level 2

- Introduce template skeletons for derived projects
- Add boundary validation docs for adapters vs canonical core
- Decide when the legacy mirror can be reduced or removed
- If routing proves stable, consider a structured task input schema for the orchestrator
- Consider a small skill metadata index if the skill set grows
- Decide whether the next step is richer skill matching or validator coverage for skill metadata
- If the filesystem is unlocked later, remove `skills/_legacy_flat/`, `tests/tmpik5_anpo`, `tests/_tmp_bootstrap_case`, `tests/_tmp_bootstrap_tests`, `tests/_tmp_template_validation` and the three deprecated flat skill `.md` files
- If the skill catalog grows, decide whether governance should validate cross-field consistency between `execution_mode`, `allowed_paths_policy` and actual execution helpers
- If behavior metadata grows more complex, consider a shared schema or validator helper for `behavior.json`
- If skill execution contracts keep growing, consider a shared schema or validator helper for `bootstrap_contract.json` and similar future skill contracts
- If bootstrap profiles grow further, consider moving rendered text blocks into dedicated template files while keeping the contract as the source of truth
- If templates become significantly richer, consider a tiny dedicated renderer helper or template validator to catch unresolved placeholders early
- If template complexity keeps growing, consider moving repeated static sections into shared partials without expanding the placeholder surface
- If certification grows further, consider extracting its checks into a shared validator helper while keeping `atlas_dispatcher.py` small
- Keep the GitHub repo clean of `_reference/`, test residue and personal local artifacts
