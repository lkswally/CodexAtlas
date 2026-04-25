# Claude Vibecoding Design Intelligence Assessment

This document captures the design, branding and visual QA block from the local reference clone at `_reference/claude-vibecoding/` and maps it to Codex-Atlas.

## Design block mapping

| Original component | Purpose | Claude dependency | Codex-Atlas equivalent | Recommendation |
| --- | --- | --- | --- | --- |
| `Intent Clarifier` in `README.md`, `CLAUDE.md`, `pipeline-reference.md` | force enough intent before visual work starts, especially mood, originality and audience | medium: implemented as orchestrator behavior inside `CLAUDE.md` and Engram drawers | `skills/visual-direction-checkpoint/` + `workflows/design_intelligence_pipeline.md` + `policies/visual_direction_policy.md` | adapt now |
| `Visual Direction Checkpoint` | explicit visual direction pause between UX architecture and UI design | medium: orchestrator-owned and coupled to Claude conversation flow | `skills/visual-direction-checkpoint/` and `agents/ux_architect.md` | adapt now |
| `brand-agent` | produce brand identity, tone, palette, typography and anti-patterns | medium: depends on Engram drawers and creative-agent chain | `agents/brand_agent.md` + existing `product-branding-review` skill + new design skills | adapt now |
| `ux-architect` | define CSS foundation, spacing, tokens and composition rules before implementation | low/medium: workflow is reusable, but original uses local design-data engine and Engram | `agents/ux_architect.md` + `skills/design-system-review/` | adapt now |
| `ui-designer` | create the visual design system and anti-generic checks | medium: original includes Claude-specific checkpoints and MCP references | `agents/ui_designer.md` + `skills/design-system-review/` + `policies/anti_generic_ui_policy.md` | adapt now |
| `evidence-collector` | validate UI with screenshots, E2E flows and evidence | high: depends on Playwright MCP, runtime servers and screenshot artifacts | `agents/evidence_collector.md` + `skills/anti-generic-ui-audit/` + read-only evidence checklist | adapt now in reduced form |
| `reality-checker` | final gate with proof-before-pass behavior | medium/high: original uses Playwright MCP, deploy URL, broad production checks | `agents/reality_checker.md` + existing `certify-project` + design-intelligence audit helper | adapt now in reduced form |
| `frontend-audit.sh` | deterministic pre-return anti-generic UI audit | medium: original is bash/grep heavy and tied to frontend-developer runtime flow | `tools/design_intelligence_audit.py` + `skills/anti-generic-ui-audit/` | adapt now |
| `Anti-Generic Guardrails` in `README.md`, `CLAUDE.md`, `pipeline-reference.md` | block generic teal-plus-default-sans outputs and generic heroes | low conceptually, high if copied literally | `policies/anti_generic_ui_policy.md` + read-only checks with evidence and warnings-first behavior | adapt now |
| `Visual Fidelity` and `Evidence Trail Mandatory` | require proof before PASS and compare output against intent/reference | high: original relies on screenshots, reference images and LLM-as-judge flow | `policies/design_evidence_policy.md` + read-only evidence-first reporting | adapt now in reduced form |
| `hooks/frontend-audit.sh` and hook-based quality gates | automatic interception before/after tool use | high: Claude hooks, `~/.claude`, shell runtime, hidden lifecycle | Atlas governance, skills and manual read-only audits | discard as runtime, keep principles |
| `design-data/` search engine | curated design intelligence dataset for styles, colors, typography and UX rules | medium: local node search engine and CSV corpus | manual policy + skill guidance only for now | watchlist |
| `Context7` and 21st.dev references in `pipeline-reference.md` | pull external component inspiration | medium/high: MCP/runtime specific | documented inspiration only; no live connector | watchlist |
| `Playwright MCP` visual QA path | execute browser-based screenshot and E2E validation | high: unavailable by design in current Atlas stage | keep `certify-project` and design audit read-only/manual | discard for now |
| `Pixel Bridge`, creative image/logo/video agents | visual runtime and asset generation | high: outside Atlas scope and depends on external services | none | discard |
| `CLAUDE.md` as monolithic system prompt | central runtime behavior file | high: Claude-only | `AGENTS.md`, policies, workflows, structured skills | already adapted |

## Extracted patterns worth preserving

### Real agents involved

- `ux-architect`
- `ui-designer`
- `brand-agent`
- `evidence-collector`
- `reality-checker`

### Where they intervene

1. Intent clarification before planning.
2. Visual direction checkpoint before detailed UI work.
3. Brand and design-system definition before implementation.
4. Frontend pre-return audit before claiming UI completion.
5. Evidence-based QA and reality checking before certification.

### Inputs they require

- audience
- project type
- mood or vibe
- originality level
- visual references if available
- intended hero and layout direction
- brand constraints
- actual UI surface to inspect

### Outputs they expect

- explicit visual direction
- anti-generic constraints
- design-system decisions
- evidence-backed QA findings
- prioritized issues and recommended next action

### Useful guardrails

- avoid default teal plus generic sans as the unexamined answer
- require explicit audience and visual direction
- require originality or variance level
- treat generic hero structure as a warning signal
- require evidence before PASS
- distinguish between read-only review and actual implementation

### Deterministic checks worth adapting

- typography-family inspection
- hero-structure inspection
- CTA presence
- responsive-baseline inspection
- contrast sanity checks
- spacing and token coherence hints
- evidence checklist with concrete file references

### What remains Claude-specific

- `.claude/` runtime layout
- `CLAUDE.md` as source of truth
- hook interception
- Engram drawers as required memory system
- Playwright MCP driven screenshot QA
- automatic deployment and creative asset chains
