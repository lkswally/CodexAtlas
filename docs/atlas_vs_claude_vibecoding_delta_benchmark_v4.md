# Codex-Atlas V4 vs Claude-Vibecoding Delta Benchmark

Fecha: 2026-07-29.

Estado: auditoria read-only. No implementa skills, hooks, agents, MCPs, policies,
workflows ni runtime. No copia archivos desde `claude-vibecoding`.

## 1. Executive Summary

Decision: mantener Codex-Atlas como base estable y adaptar solo patrones de bajo
riesgo que fortalezcan evidencia, seguridad, DX o eficiencia sin importar el
runtime Claude.

Se actualizo el benchmark externo en sandbox desde el commit anterior
`2f75af6` hasta `9288a09552529ffede2af59390adc35d404bb751`. El delta real
incluye cinco commits:

| Commit | Tema | Lectura para Atlas |
|---|---|---|
| `9e54e6a` | composition variety system y fluid spacing | Candidato util para el gap real de salidas visuales repetitivas, pero debe entrar como auditoria evidence-aware, no como prompt suelto |
| `c1b4102` | `.codegraph/` en gitignore | WATCH; Atlas no adopta Codegraph runtime, pero el patron de excluir indices locales es sano |
| `c8a73cc` | reconciliacion de CLAUDE.md tras regresion | Reafirma que docs/runtime drift es un riesgo real en sistemas prompt-heavy |
| `dd4a165` | optimizacion de contexto: `CLAUDE.md` -31%, orquestador -24% | ADAPT conceptual: extraer referencias on-demand con triggers objetivos |
| `9288a09` | contratos QA, PASS_WITH_WARNINGS whitelist, VISUAL_IMPACT en templates, installer self-check 38->52 | ADAPT parcial: mejorar contratos y self-checks, rechazar installers globales |

El cambio mas valioso no es una feature nueva sino una disciplina: mover detalle
pesado a referencias on-demand, mantener invariantes de seguridad inline y medir
reduccion de contexto. Eso si resuelve un problema real de Atlas: el repositorio
tiene mucha superficie declarativa y varias docs largas que compiten por contexto.

El cambio mas tentador, y mas riesgoso, es el sistema de hooks globales. Sigue
siendo REJECT para Atlas. Los hooks de Claude modifican `~/.claude`, dependen del
lifecycle Claude y mezclan prevencion, telemetry, memoria y UX. Atlas debe seguir
prefiriendo tools repo-locales, tests y workflows opt-in.

## 2. Evidence Collected

### Claude-Vibecoding

- Repo: `https://github.com/Emaleo0522/claude-vibecoding`.
- Sandbox read-only: `D:\Proyectos\_benchmark_sandbox\claude-vibecoding`.
- Previous benchmark commit: `2f75af6efa9bd7692e39f695c468528eeadfa5e6`.
- Current `origin/main`: `9288a09552529ffede2af59390adc35d404bb751`.
- Delta command evidence:
  - `git log --oneline 2f75af6..origin/main`.
  - `git diff --name-status 2f75af6..origin/main`.
  - `git diff --stat 2f75af6..origin/main`.
- Delta size: 24 files changed, 813 insertions, 686 deletions.
- No installers, hooks, MCPs, deploys or runtime commands were executed.

### Codex-Atlas

- Atlas commit: `97661787fa6d446d797f7a38faf96ef3dc2cda1f`.
- Relevant tests: `221 passed in 1.26s`.
- Global suite: `780 passed, 1 skipped in 18.66s`.
- Governance: `ATLAS GOVERNANCE CHECK / OK`.
- `atlas_verify`: `status: ok`.
- `compileall`: `py -m compileall -q tools`, exit 0.
- `git diff --check`: clean before writing this report.
- Working tree before report: `main...origin/main`.

## 3. Delta Real Desde Benchmark Anterior

### Files Added

| Path | Purpose | Atlas reading |
|---|---|---|
| `.gitignore` | ignores `.codegraph/` local MCP index | Safe principle: local generated indexes should stay unversioned |
| `agents/engram-save-reference.md` | full memory save protocol | WATCH; useful lifecycle rigor, but Engram runtime remains external |
| `agents/orquestador-vdc-reference.md` | Visual Direction Checkpoint detail | ADAPT conceptually; Atlas has visual direction but can tighten decision points |
| `agents/orquestador-fase45-reference.md` | certification/publication details | WATCH; Atlas should not copy deploy/publication runtime |

### Files Modified

Major modifications:

- `CLAUDE.md`: 210-line churn, net large reduction. Keeps invariants inline and
  moves detail to references.
- `agents/orquestador.md`: 460-line churn, net large reduction. Moves phase
  details to reference docs.
- `agents/ui-designer.md`: adds composition variety system and hero archetypes.
- `agents/ux-architect.md`: adds fluid spacing doctrine.
- `agents/frontend-developer.md`: syncs fluid container expectations.
- `agents/evidence-collector.md` and `agents/reality-checker.md`: accept extended
  QA contract fields such as `PASS_WITH_WARNINGS`.
- `hooks/pre-return-audit.sh`: fixes container-width regex, adds doctrine around
  `min()`/`clamp()`.
- `install/linux.sh` and `install/windows.md`: update installed file counts and
  self-checks.
- `README.md`, `README.en.md`, `UPGRADE_LOG.md`: update counts and explain the
  changes.

### Hooks

No new hook file appears in this delta, but `pre-return-audit.sh` changed. The
new behavior is better aligned with evidence from generated landing pages:

- old regex missed `1200px`/`1280px` caps despite warning about 1180-1280;
- new regex covers `1000-1299px`;
- comments make fluid formulas (`min()`, `clamp()`) the expected escape hatch.

Atlas already has `tools/ui_pre_return_audit.py`, `frontend_visual_execution_guard`,
`design_quality_enforcement` and Evidence Runner. The useful adaptation is not
the bash hook. It is the testable rule: detect rigid narrow global containers
and prefer viewport-fluid envelopes.

### Agents and Orchestration

Claude-Vibecoding still runs a Claude-first orchestrator with 25 executable
agent roles and many references. The delta reduces inline context and pushes
phase detail into reference docs. This is directionally good but remains
incompatible with Atlas as runtime:

- `orquestador.md` says the orchestrator must not do real work inline;
- subagents return a strict envelope;
- `VISUAL_IMPACT` now drives checkpoint responsibility;
- phases 4/5 remain coupled to certification/git/deploy agents.

Atlas current state is safer: `tools/intelligent_orchestrator.py` is advisory,
deterministic, no runtime execution, and validated by tests. Atlas should borrow
the reference-on-demand discipline, not the 25-agent runtime.

### MCPs

Claude-Vibecoding keeps `mcp.registry.json` with manual states:
`LIVE`, `CONFIG_ONLY`, `PENDING_TOKEN`, `OPTIONAL`, `MISSING`. This is good DX,
but weak epistemically: `LIVE` is declarative and session-dependent.

Atlas already separates:

- MCP profiles;
- permission matrix;
- protocol validation;
- read-only `tools/call` validation;
- reality checks and harness docs.

Decision: do not create a second manual MCP registry. If Atlas wants a terse MCP
view, generate it from observed evidence and freshness.

### Security

Claude-Vibecoding remains stronger as an interactive guardrail UX because hooks
can block or warn in real time:

- `block-no-verify.js` blocks git bypasses, force push, destructive rm, reset,
  chmod 777, recursive chown and curl-to-shell.
- `config-protection.js` blocks edits to obvious secret files.
- `quality-gate.js` warns on `.only`, `debugger`, hardcoded secrets/passwords
  and TypeScript suppressions.

Atlas is stronger as governed architecture:

- `tools/dangerous_command_policy.py` is pure, data-driven and tested;
- it avoids global hooks and hidden side effects;
- governance and CI verify policy structure.

Decision: keep Atlas advisory-first. Add new dangerous/secret cases only as
deterministic patterns plus tests when a false negative is demonstrated.

### Docs, Tests, CI, Reporting

Claude-Vibecoding improved docs/install counts and upgrade log. Its tests remain
Node pure for helpers. Its reporting is excellent for a Claude runtime: health,
session summary, cost tracker, drift check, MCP registry.

Atlas is ahead in CI/release/evidence:

- global suite is green;
- browser smoke is real and observed in GitHub Actions;
- Evidence Quality Report and artifacts are versioned workflows;
- V3 RC1 exists as release discipline;
- Decision Benchmark V1 has 45 versioned cases and currently scores 100%.

## 4. Atlas vs Claude-Vibecoding Current Comparison

| Area | Atlas actual | Claude-Vibecoding actual | Mejor resuelto por | Evidencia | Riesgo |
|---|---|---|---|---|---|
| architecture | Repo-local, governed, evidence-first, advisory orchestrator | Claude global runtime with 25 agents and refs | Atlas | `atlas_verify`, architecture state, CI | Claude runtime too broad for Atlas |
| governance | Canonical governance check, policies/configs/tests | Audit system plus prompt doctrine | Atlas | governance OK, 780 tests | Atlas has heavy governance surface |
| evidence | Evidence Runner, bundle, report, browser smoke artifact | Return Envelope, Playwright MCP expectation | Atlas | browser workflow `27724893071`; Evidence tests | Atlas still lacks visual quality evaluator |
| security | Dangerous policy pure/tested, no global hooks | real-time blocking hooks | Split | Atlas tests vs Claude hook UX | Hooks are unsafe to copy globally |
| hooks | No global hooks; workflows/tools explicit | 13 reactive hooks plus manual utilities | Claude for UX, Atlas for safety | settings templates, hook scripts | Hidden lifecycle side effects |
| filesystem boundaries | Repo-local, workspace-root oriented | copies files to `~/.claude`, installs global config | Atlas | Atlas governance, Claude install docs | Global drift in Claude model |
| MCP | protocol validation, permission matrix, read-only call | manual registry, Engram/Context7/Playwright assumed | Atlas | MCP docs/tests vs `mcp.registry.json` | Manual LIVE labels stale |
| skills | Codex skills under `skills/`; repo-local | no real `SKILL.md`; refs under `agents/` | Atlas | search found only `external-skills-reference.md` | Claude naming can mislead |
| agents | manual/advisory docs plus orchestrator simulator | 25 agents, model frontmatter | Claude for UX, Atlas for stability | `agents/*.md`, Atlas simulator tests | Prompt drift and context cost |
| orchestration | deterministic simulator, no execution | full 5-phase pipeline with subagents | Atlas for safe core | `intelligent_orchestrator` tests | Claude pipeline is not Codex-native |
| model routing | abstract model classes, no hardcoded providers | Opus/Sonnet per agent | Atlas | model routing tests/policy | Claude is Anthropic-coupled |
| context minimization | partial, growing docs and tools | strong recent -31%/-24% extraction | Claude | commit `dd4a165`, UPGRADE_LOG | Too many refs can fragment truth |
| memory | file-backed, Engram sandbox/advisory | Engram required, cloud sync, mailbox | Atlas | Failure Registry, memory docs | Claude memory has external side effects |
| checkpoints | human approval docs, visual direction, browser smoke | visible checkpoint doctrine + VISUAL_IMPACT | Claude | agent protocol and VDC ref | Prompt-only enforcement |
| return envelopes | orchestrator/dispatcher contracts and tests | uniform subagent envelope | Tie | Atlas tests; `agent-protocol.md` | Dual schemas would drift |
| testing | 780 pass, critical CI, browser workflow | Node helper tests, audit 11/11 in logs | Atlas | local checks, workflows | Atlas global not always in main CI |
| CI | Atlas CI plus manual global/browser/evidence workflows | not primary validation path | Atlas | recent CI and workflow evidence | Browser workflow remains manual |
| DX | improving docs/tools, still formal | guided installers, healthcheck, session summaries | Claude | README/install/hooks | Installers mutate global machine |
| onboarding | repo-local, conservative | very guided Claude setup | Claude | install docs | too side-effectful for Atlas |
| session reporting | reports exist but mostly repo/workflow | session summary, cost report, compact suggestions | Claude | hooks/session*.js, cost*.js | possible privacy/token telemetry |
| release discipline | V3 RC1, tags, CI, docs | UPGRADE_LOG, install self-checks | Atlas | Atlas status and CI | Claude log is not release gate |
| observability | atlas_verify, dashboards, evidence reports | healthcheck, drift, MCP summary | Tie | both have observed tools | Claude health can be fail-open |
| cost/token efficiency | model routing advisory, decision benchmark | context split, stop rules, compact/cost hooks | Claude currently | `CLAUDE.md` reduction, stop rules | Zen delegation/provider coupling |

## 5. Skills and Reference Review

Finding: Claude-Vibecoding has no Codex-style skills in the audited tree. There
is no `SKILL.md` and no `skills/` directory. It has 24 on-demand references plus
`agent-protocol.md`, `AGENTS.md` and executable agent prompts. The table below
treats those references as "skill-like" knowledge blocks only.

| Reference | Purpose | Dependencies and side effects | Claude coupling | Atlas overlap | Decision | Rationale |
|---|---|---|---|---|---|---|
| `agent-protocol` | shared Return Envelope, Engram, rules | Engram examples, agent runtime | high | Atlas orchestrator envelope | DUPLICATED_BY_ATLAS | Good principle, but second schema would drift |
| `pipeline` | DAG/fase detail | Claude pipeline | high | Agent Loop/manual workflows | REJECT | Too coupled to 5-phase runtime |
| `intent-clarifier` | reduce vague briefs | prompt-only | medium | intent contracts, orchestrator intake | DUPLICATED_BY_ATLAS | Atlas already has intake and anti-generic policies |
| `better-auth` | auth implementation patterns | framework docs, code changes | low/medium | no direct Atlas runtime need | WATCH | Useful only for generated apps, not core architecture |
| `linux-hardening` | VPS hardening | shell/admin ops | medium | safe execution/human approval | WATCH | Keep as external reference, not automated |
| `pocketbase` | backend reference | app code dependency | low | none core | LOW_VALUE | Domain-specific, not Atlas stability |
| `devops-vps` | VPS deploy ops | SSH/deploy side effects | high | deploy is not Atlas priority | REJECT | Violates stability-first for now |
| `nothing-design` | specific aesthetic | design prompt only | low | anti-generic/design skills | WATCH | Maybe useful as style ref, not architecture |
| `react-patterns` | modern React patterns | Context7/codegen | low | app generation only | WATCH | Useful outside core; no V4 adoption |
| `redis-patterns` | Redis usage | app dependency | low | none core | LOW_VALUE | Domain-specific |
| `better-gsap` | advanced motion | GSAP dependency | medium | no visual regression yet | WATCH | Wait until motion verification exists |
| `scroll-storytelling` | advanced scroll | browser/motion deps | medium | Evidence lacks motion validation | WATCH | Do not adopt before verification |
| `creative-coding` | p5/GLSL/generative | app deps | medium | no core gap | LOW_VALUE | Capability, not stability |
| `advanced-effects` | Lottie/Rive/effects | app deps | medium | no core gap | LOW_VALUE | Adds complexity |
| `reactive-audio` | Web Audio/Tone | app deps | medium | no core gap | LOW_VALUE | Out of scope |
| `modo-diagnostico` | read-only audit mode | prompt discipline | medium | Atlas audit docs/governance | ADAPT | Strong DX if mapped to Atlas manual audit checklist |
| `cross-claude-mailbox` | cross-Claude coordination | Engram cloud, external memory | high | none desired | REJECT | External async edits are unsafe for Atlas |
| `orquestador-modificacion` | mini-pipeline for changes | Claude orquestador | high | Agent Loop manual | WATCH | Principle useful, runtime rejected |
| `orquestador-fase-2b` | visual assets phase | image/logo/video agents | high | Atlas image tools/manual | WATCH | Needs evidence and asset policy |
| `orquestador-edge-cases` | pipeline recovery | Claude runtime | high | Failure Registry | DUPLICATED_BY_ATLAS | Atlas has failure records/lookup |
| `external-skills` | add external skills via `npx skills add` | network/install side effects | high | Codex skill ecosystem separate | UNSAFE | Do not adopt auto-install pattern |
| `simplicity-first` | shorter outputs, structure only when needed | prompt-only | low | no single Atlas doc standard | ADAPT | Low-risk DX/token improvement if docs-only |
| `engram-save` | safe memory save protocol | Engram cloud/CLI | high | Failure Registry, memory docs | WATCH | Extract verification principle only |
| `orquestador-vdc` | visual direction checkpoint | Claude pipeline | medium/high | visual direction docs | ADAPT | Useful to make human checkpoints clearer |
| `orquestador-fase45` | certification/deploy phases | git/deploy agents | high | quality gates/release docs | REJECT | Deploy/runtime coupling too high |

Classification summary:

- ADAPT: `modo-diagnostico`, `simplicity-first`, `orquestador-vdc`.
- WATCH: domain references whose value depends on a future app-generation or
  visual verification workload.
- REJECT/UNSAFE: global installers, external skills auto-add, mailbox, deploy
  phases, global hooks.
- DUPLICATED_BY_ATLAS: return envelope, intent/failure edge cases.

## 6. Intelligent Decision Gate

| Candidate | Real Atlas problem? | Equivalent exists? | Complexity | Stability | Security | DX | Token impact | Coupling | Advisory-first? | Tests clear? | V3 RC1 risk | Decision |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Context splitting for long Atlas docs | Yes: many docs/policies/tools compete for context | Partial | lower if done carefully | positive | neutral | positive | lower | low | yes | doc link tests/search tests | low | ADAPT |
| Composition variety/fluid spacing audit | Yes: repeated generic visuals were an original Atlas finding | Partial anti-generic only | neutral | neutral | neutral | positive | neutral | low | yes | fixture CSS tests | low/medium | ADAPT |
| VISUAL_IMPACT checkpoint language | Yes: Atlas has browser evidence but no visual approval semantics | Partial | neutral | positive | neutral | positive | neutral | low | yes | schema/docs tests | low | ADAPT |
| Simplicity-first output style | Yes: reports can overgrow | Partial final-answer rules | lower | neutral | neutral | positive | lower | low | yes | docs-only | low | ADAPT |
| MCP registry manual `LIVE` | Yes DX, but Atlas has evidence reports | Yes | higher | negative epistemic | neutral | positive | neutral | medium | yes | possible | medium | REJECT literal |
| Healthcheck aggregator | Weak: Atlas has `atlas_verify` | Yes | higher | neutral | neutral | positive | neutral | low | yes | possible | medium | WATCH |
| Drift check against global runtime | No, Atlas repo-local | Governance/surface audit | higher | neutral | neutral | neutral | neutral | high | yes | possible | medium | REJECT |
| Global hooks | No, violates architecture | Dangerous policy/tests | much higher | negative | mixed | positive | neutral | very high | no | hard | high | REJECT |
| Engram cloud memory lifecycle | Not current priority | Failure Registry + docs | higher | negative until proven | negative/mixed | positive | higher | high | maybe | hard | high | WATCH/REJECT runtime |
| External skills auto-install | No | Codex skill handling separate | higher | negative | negative | mixed | higher | high | no | hard | high | UNSAFE |

Gate result: no runtime implementation is justified in this phase. The safe
path is documentation plus later isolated, tested adapters only where Atlas has
evidence of a real gap.

## 7. Safe Adoption Matrix

```json
[
  {
    "name": "Context splitting with on-demand references",
    "source_path": "CLAUDE.md, agents/orquestador.md, agents/*-reference.md",
    "source_commit": "9288a09552529ffede2af59390adc35d404bb751",
    "decision": "ADAPT",
    "atlas_gap": "Atlas has long, overlapping docs/policies and growing context surface.",
    "why_it_helps": "Keeps invariants inline while moving rare detail behind objective triggers.",
    "stability_impact": "positive",
    "security_impact": "neutral",
    "token_impact": "lower",
    "complexity_impact": "lower",
    "compatibility_risk": "Low if docs-only and link-tested; medium if it creates a second source of truth.",
    "dependencies": [],
    "tests_required": ["docs link integrity", "no orphaned policy/config references", "governance surface audit"],
    "rollback_plan": "Revert doc split and restore original doc text from git.",
    "requires_human_approval": true
  },
  {
    "name": "Evidence-aware composition variety and fluid spacing audit",
    "source_path": "agents/ui-designer.md, agents/ux-architect.md, hooks/pre-return-audit.sh",
    "source_commit": "9288a09552529ffede2af59390adc35d404bb751",
    "decision": "ADAPT",
    "atlas_gap": "Atlas previously observed generic repeated landing layouts and weak visual verification.",
    "why_it_helps": "Turns a vague anti-generic concern into concrete layout/container checks.",
    "stability_impact": "neutral",
    "security_impact": "neutral",
    "token_impact": "neutral",
    "complexity_impact": "neutral",
    "compatibility_risk": "Medium if added as another readiness layer; lower if folded into existing UI pre-return audit tests.",
    "dependencies": [],
    "tests_required": ["CSS fixture with 1280px rigid container fails", "min/clamp fluid container passes", "no browser dependency for unit tests"],
    "rollback_plan": "Remove added patterns from the existing audit config/tests only.",
    "requires_human_approval": true
  },
  {
    "name": "VISUAL_IMPACT checkpoint semantics",
    "source_path": "agents/agent-protocol.md, agents/orquestador-vdc-reference.md",
    "source_commit": "9288a09552529ffede2af59390adc35d404bb751",
    "decision": "ADAPT",
    "atlas_gap": "Atlas can capture browser evidence but does not yet distinguish technical PASS from human visual approval.",
    "why_it_helps": "Prevents technical evidence from being mistaken for aesthetic approval.",
    "stability_impact": "positive",
    "security_impact": "neutral",
    "token_impact": "neutral",
    "complexity_impact": "neutral",
    "compatibility_risk": "Low if advisory-only; medium if inserted into quality gates too early.",
    "dependencies": [],
    "tests_required": ["summary/report preserves technical PASS", "visual impact cannot auto-approve", "WARN/non-blocking integration test"],
    "rollback_plan": "Remove advisory field/doc note; Evidence Contract remains unchanged.",
    "requires_human_approval": true
  },
  {
    "name": "Simplicity-first reporting doctrine",
    "source_path": "CLAUDE.md, agents/simplicity-first-reference.md",
    "source_commit": "9288a09552529ffede2af59390adc35d404bb751",
    "decision": "ADAPT",
    "atlas_gap": "Atlas reports can be comprehensive but heavy; V4 wants stability and token savings before new capabilities.",
    "why_it_helps": "Reduces report noise while preserving detailed tables only when the task demands them.",
    "stability_impact": "neutral",
    "security_impact": "neutral",
    "token_impact": "lower",
    "complexity_impact": "lower",
    "compatibility_risk": "Low; docs/style guidance only.",
    "dependencies": [],
    "tests_required": ["none for runtime; optional docs lint"],
    "rollback_plan": "Revert docs-only guidance.",
    "requires_human_approval": false
  },
  {
    "name": "Diagnostic mode checklist",
    "source_path": "agents/modo-diagnostico-reference.md",
    "source_commit": "9288a09552529ffede2af59390adc35d404bb751",
    "decision": "ADAPT",
    "atlas_gap": "Atlas audits exist, but a concise read-only diagnostic checklist would improve operator DX.",
    "why_it_helps": "Makes read-only audits explicit and reduces accidental implementation during analysis tasks.",
    "stability_impact": "positive",
    "security_impact": "positive",
    "token_impact": "neutral",
    "complexity_impact": "neutral",
    "compatibility_risk": "Low if manual/docs-only; high if converted into runtime mode.",
    "dependencies": [],
    "tests_required": ["docs only", "optional command registry wording check"],
    "rollback_plan": "Remove the checklist doc.",
    "requires_human_approval": true
  }
]
```

## 8. Explicit Reject List

- Do not copy Claude global hooks.
- Do not write to `~/.claude`, Codex global config, MCP config or user PATH.
- Do not install Engram, Context7, Codegraph, Playwright MCP or external skills.
- Do not create new agents because Claude has 25.
- Do not add auto-deploy, auto-push or auto-commit.
- Do not make browser smoke blocking in Atlas CI.
- Do not create a manual MCP registry with `LIVE` unless it is derived from
  observed evidence and freshness.
- Do not introduce a second Return Envelope schema.
- Do not add visual/motion features before screenshot evidence is consumed by a
  tested verifier.

## 9. Recommended Next Steps

1. **P1: Context surface audit.** Identify the top 10 longest Atlas docs/policies
   loaded or cited frequently, then propose on-demand splits with link tests.
2. **P1: Visual composition audit V1.** Extend the existing UI audit surface, not
   a new readiness layer, with rigid-container and repeated-hero-pattern fixtures.
3. **P2: Visual approval semantics.** Add advisory `visual_impact` language to
   Evidence Quality Report docs before any schema or gate change.
4. **P2: Diagnostic checklist.** Create a short read-only audit checklist for
   Atlas manual mode, using Failure Registry only as optional record after the
   audit.
5. **P3: DX command map.** Improve README/docs index for existing commands
   (`atlas_verify`, evidence browser smoke, evidence report, global test) instead
   of adding a new healthcheck.

## 10. Final Verdict

Claude-Vibecoding improved meaningfully since `2f75af6`, especially in context
minimization, visual composition variety, checkpoint clarity and installer
self-checks. It remains a Claude-first global runtime. Atlas should not copy that
architecture.

Atlas is currently stronger for stability, governance, evidence, CI, release
discipline and safe model routing. Claude-Vibecoding is stronger for interactive
DX, prompt ergonomics, session reporting and token/context doctrine.

Safe adoption is narrow:

- adapt context splitting;
- adapt visual composition audit ideas;
- adapt checkpoint language;
- adapt simplicity-first reporting;
- reject global hooks, installers, Engram runtime, external skill auto-installs
  and auto-deploy.

No implementation is recommended before a separate approved phase with bounded
tests and rollback.
