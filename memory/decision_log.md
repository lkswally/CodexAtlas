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
- Risk: confidence and stale signals can become misleading if the curated catalog is not maintained
- Rollback: revert `tools/docs_search_adapter.py` to the previous minimal result format and loosen the new assertions in `tests/test_mcp_manager.py`
