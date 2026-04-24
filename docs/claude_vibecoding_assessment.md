# Claude Vibecoding Assessment for Codex-Atlas

## Scope reviewed

Reference inspected from `Emaleo0522/claude-vibecoding`:
- `README.md`
- `CLAUDE.md`
- `agents/`
- `hooks/`
- `docs/`
- `templates/`
- `design-data/`
- `install/`
- `install.sh`
- `pixel-bridge/`
- `UPGRADE_LOG.md`

This assessment documents what Atlas should adapt, what should remain inspiration only, and what should stay out of the Codex-native mother configuration.

## Block assessment

| Block | Classification | Problem it solves | Claude dependency | Codex-native equivalent | Risk | Recommendation |
|---|---|---|---|---|---|---|
| `README.md` | `ADAPTAR_A_CODEX` | Explains the operating model, pipeline and system surface | Low | Root `README.md` plus focused docs under `docs/` | Low | Implement now as Atlas documentation |
| `CLAUDE.md` | `ADAPTAR_A_CODEX` | Central system prompt, phase discipline, anti-generic rules, memory habits | High | `AGENTS.md`, `docs/codex_system_prompt.md`, `policies/`, `workflows/` | Medium | Implement now as split Codex-native guidance |
| `agents/` | `INSPIRACIÓN_SOLAMENTE` | Specialized responsibilities and handoff boundaries | Medium | Small Atlas role set under `agents/` and future skills/workflows | Medium | Reuse patterns selectively, do not mirror the full fleet |
| `hooks/` | `ADAPTAR_A_CODEX` | Security blocks, quality gates, cost and session summaries | High | `tools/atlas_governance_check.py`, `certify-project`, manual validators and policies | Medium | Adapt principles now, not the automatic Claude hooks |
| `docs/` | `ADAPTAR_A_CODEX` | Explains phases, upgrades and domain-specific improvements | Low | `docs/` in Atlas for architecture, mapping and assessments | Low | Implement now as documentary guidance |
| `templates/` | `ADAPTAR_A_CODEX` | Installer and prompt templates for Claude environments | High | Atlas template files under `templates/` and contract-backed renderers | Medium | Adapt only repo-local reusable templates |
| `design-data/` | `WATCHLIST_FUTURO` | Anti-generic and industry-aware design guidance | Medium | Small policy-driven template/data layer if Atlas gets a real need | Medium | Do not import now; revisit if branding reviews need structured datasets |
| `install/` | `WATCHLIST_FUTURO` | Automated setup for Claude environments | High | Future Codex-friendly bootstrap/install docs if Atlas needs distribution tooling | Medium | Document only for now; do not add installers yet |
| `install.sh` | `DESCARTAR` | Entry wrapper for Claude/Linux install flow | High | None right now | Low | Keep Atlas repo-local and manual |
| `pixel-bridge/` | `DESCARTAR` | Visual "agent office" and activity UI | High | None | High | Do not bring this into Atlas |
| `UPGRADE_LOG.md` | `ADAPTAR_A_CODEX` | Change traceability and anti-drift history | Low | `memory/decision_log.md` and status docs | Low | Already adapted; continue using Atlas memory/status files |

## Pattern-by-pattern assessment

### 1. System prompt / `CLAUDE.md`

- **Classification:** `ADAPTAR_A_CODEX`
- **Value:** it centralizes mission, phase discipline, guardrails and hard restrictions.
- **Claude dependency:** high, because it assumes Claude runtime files, hooks and Engram MCP.
- **Codex-native fit:** high, if split into `AGENTS.md`, workflow docs and explicit policies.
- **Recommendation:** implement now as a split instruction surface, not as a single Claude file.

### 2. Pipeline by phases

- **Classification:** `ADAPTAR_A_CODEX`
- **Value:** reduces chaos and clarifies when planning, architecture, QA and certification happen.
- **Claude dependency:** low to medium.
- **Codex-native fit:** high.
- **Recommendation:** implement now as a documentary pipeline with read-only quality gates and handoff rules. No deploy automation.

### 3. Specialized agents

- **Classification:** `INSPIRACIÓN_SOLAMENTE`
- **Value:** clearer role boundaries and better delegation prompts.
- **Claude dependency:** medium, because the original system expects an orchestrator spawning many subagents.
- **Codex-native fit:** selective.
- **Recommendation:** do not add 24 agents. Keep the current Atlas set and only expand when a role solves a repeated Atlas problem.

### 4. Hooks / guards

- **Classification:** `ADAPTAR_A_CODEX`
- **Value:** stops dangerous actions and raises quality early.
- **Claude dependency:** high in implementation, low in principle.
- **Codex-native fit:** high as manual validation and governance.
- **Recommendation:** adapt as policies, `governance_check`, `audit-repo`, `certify-project` and future read-only checks.

### 5. Anti-generic guardrails

- **Classification:** `ADAPTAR_A_CODEX`
- **Value:** prevents bland UX, copy and branding outputs.
- **Claude dependency:** low.
- **Codex-native fit:** high, especially for Atlas templates, branding review and handoff quality.
- **Recommendation:** reinforce now through policy and workflow rules, not through hidden automation.

### 6. Evidence / reality checker

- **Classification:** `ADAPTAR_A_CODEX`
- **Value:** forces validation evidence instead of optimistic closure.
- **Claude dependency:** medium when tied to Playwright and deploy URLs, low as a principle.
- **Codex-native fit:** high.
- **Recommendation:** implement now as evidence-required policy plus read-only certification and audit summaries.

### 7. Certification phase

- **Classification:** `ADAPTAR_A_CODEX`
- **Value:** verifies quality and boundary integrity before handoff.
- **Claude dependency:** low to medium.
- **Codex-native fit:** high.
- **Recommendation:** implement now as `certify-project` and keep it read-only by default.

### 8. Cost tracking / session summary

- **Classification:** `WATCHLIST_FUTURO`
- **Value:** operational awareness and handoff continuity.
- **Claude dependency:** medium in the original hooks-based implementation.
- **Codex-native fit:** medium.
- **Recommendation:** keep the simple Atlas memory files; do not add automated tracking yet.

## Specialized agent fit for Atlas

| Reference role | Status in Atlas | Recommendation |
|---|---|---|
| `project-manager-senior` | Partially covered by `planner` | Do not add yet; improve planning workflow first |
| `ux-architect` | Partially covered by `ux_brand` + `architect` | Keep as inspiration until Atlas needs stronger design-system specialization |
| `ui-designer` | Not present | Watchlist only; useful later if Atlas starts generating richer frontends |
| `security-engineer` | Partially covered by `security_guard` | No new role yet; strengthen policy and certification first |
| `brand-agent` | Partially covered by `ux_brand` | No separate agent yet |
| `frontend-developer` | Not present | Watchlist only; Atlas is still mother config, not a product runtime |
| `backend-architect` | Not present | Watchlist only |
| `evidence-collector` | Not present | Adapt the pattern through certification and evidence policy now, not a new agent |
| `seo-discovery` | Not present | Watchlist only |
| `api-tester` | Not present | Watchlist only as future read-only validator |
| `performance-benchmarker` | Not present | Watchlist only as future read-only validator |
| `reality-checker` | Already present | Keep and strengthen documentation, not automation |
| `self-auditor` | Partially covered by governance check | No separate new agent needed yet |

## Current Atlas stance

### Implement now

- Split system-prompt logic into `AGENTS.md`, policies and workflow docs
- Keep the phase pipeline explicit
- Strengthen anti-generic guidance
- Require evidence before closure
- Treat project boundaries as a first-class quality gate
- Keep `certify-project` read-only and derivative-focused

### Watchlist

- Structured design datasets
- Read-only API/performance/security validators
- Install/bootstrap distribution tooling for Atlas itself
- Richer session summaries or cost notes

### Discard

- `.claude` runtime structure
- Claude-only hook implementation
- Engram as a mandatory backend
- Pixel Bridge
- automatic deploy flow
