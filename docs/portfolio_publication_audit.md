# Portfolio Publication Audit and Website Alignment Plan

**Date:** 2026-09-23  
**Repository:** https://github.com/lkswally/CodexAtlas  
**Baseline:** main at ca535ac1db3e27945af6f60d1bcb76b41822b3b9  
**Working branch:** portfolio/codexatlas-readme-web

## Scope gate

| Check | Result |
|---|---|
| Local checkout | Verified outside the published content |
| Remote origin | https://github.com/lkswally/CodexAtlas.git |
| Baseline branch | main |
| Baseline HEAD | ca535ac1db3e27945af6f60d1bcb76b41822b3b9 |
| Baseline origin/main | ca535ac1db3e27945af6f60d1bcb76b41822b3b9 |
| Baseline worktree | Clean |

No unrelated repository was modified.

## Publication cleanup classification

| Surface | Classification | Action |
|---|---|---|
| README references to a named downstream product | NARRATIVE_ONLY | Removed through the portfolio rewrite |
| AGENTS and status-document examples | NARRATIVE_ONLY | Reworded as downstream/consumer projects |
| Committed JSON/JSONL runtime records | PRIVATE_INFORMATION / HISTORICAL_ARTIFACT | Local paths and downstream names redacted; derived-project registry reset to an empty public baseline |
| Ignored migration audit | HISTORICAL_ARTIFACT | Preserved locally; remains ignored |
| adapters/reyesoft | FUNCTIONAL_DEPENDENCY | Not hidden or renamed in this task |
| REYESOFT_ROOT and prompt constraints in tools/tests | FUNCTIONAL_DEPENDENCY | Not changed; recorded as architectural backlog |
| Visual-fidelity PNG files | TEST_FIXTURE | Kept; they contain placeholder text and are not presented as browser evidence |
| _reference | Research scratchpad | Remains ignored and outside the published tree |

## Architectural coupling found

ARCHITECTURAL_COUPLING_FOUND

The reusable core still contains named-consumer coupling in:

- tools/atlas_orchestrator.py
- tools/prompt_builder.py
- tests/_support_paths.py
- tests/test_atlas_orchestrator.py
- tests/test_prompt_builder.py
- adapters/reyesoft/
- selected policy and skill contracts

Changing this safely requires a separately reviewed compatibility plan for defaults, environment-variable names, adapters, tests, and downstream consumers. It was not disguised as generic wording and was not refactored during this publication task.

## Website source ownership

WEBSITE_SOURCE_EXTERNAL  
repository=https://github.com/lkswally/WebCodexAtlas.git  
local_checkout=external sibling checkout (read-only)  
public_url=https://web-codex-atlas.vercel.app/

Evidence:

- the sibling checkout Git config identifies lkswally/WebCodexAtlas as origin;
- its vercel.json declares the Vercel build;
- its HTML contains the audited domain and matching public content;
- the source is not contained in lkswally/CodexAtlas.

The website repository was read only for ownership verification. No website file, deployment, Vercel setting, or Git state was changed.

## Website claim matrix

| Website claim | Repository evidence | Status | Required change |
|---|---|---|---|
| “Factory gobernada para Codex” | Governance, audit, bootstrap, certification and routing tools exist | PARTIAL / broadly supportable | Explain deterministic tools and host boundary |
| “Atlas no reemplaza Codex. Lo gobierna.” | Policy and checks exist, but universal host enforcement does not | OVERSTATED | Use “adds governance checks around selected Codex workflows” |
| “Quality gate real” as a central decision layer | Quality report tooling and tests exist | PARTIAL | State that it applies when invoked, not to every host action |
| “6 agentes orbitando” | No six-agent executable trace or verified agent count | UNSUPPORTED | Replace with architecture components; avoid agent count |
| “Brand, UI y visual QA — Listo” | Readiness/check tooling exists; real browser smoke was skipped locally | OVERSTATED | Mark PARTIAL/opt-in and separate readiness from browser evidence |
| n8n readiness and offline JSON generation | Readiness and generator tooling exist; no production connection | BOUNDED | Keep only with explicit offline/inactive wording |
| MCPs opt-in | MCP manager and permission profiles exist; external docs MCP not configured | SUPPORTABLE WITH LIMIT | State CONFIGURED/ADVISORY, not live |
| Manual model fallback | Advisory model recommendations exist; no switching | SUPPORTABLE WITH LIMIT | State recommendation only |
| “bloquear trabajo fuera de scope” | Selected entrypoints can block; no universal interception | OVERSTATED | Scope to invoked checks and policies |
| Flow ending in implementation | Procedure exists; not an automatic runtime state machine | PROCEDURAL | Label as recommended workflow |
| “Atlas ordena la información” on idea intake | Browser JavaScript structures form fields | PARTIAL | Attribute to the form, not an AI analysis runtime |
| Form attempts an n8n test webhook | Code supports a configured /webhook-test/ URL | IMPLEMENTED BUT UNCONFIGURED | Keep fallback wording; do not imply current backend |
| Form consent.contact_allowed=true | No explicit consent control in the UI | PRIVACY GAP | Add explicit consent and privacy notice before collecting PII |
| Sitemap lastmod 2026-05-19 | Live page changed after that date | STALE | Regenerate dates during the website update |
| Installation using global python | Commands are structurally valid | PARTIAL | Prefer an isolated environment and requirements-dev.txt |
| Contact identity and LinkedIn | Public website content | OWNER DECISION | Keep only with explicit owner approval |

## Exact external website change plan

A separately authorized WebCodexAtlas task should:

1. replace “6 agents” artwork labels and agent-count claims with verified architecture components;
2. align the opening with the bounded factory/control-plane positioning from the CodexAtlas README;
3. describe governance and quality gates as invoked controls, not universal enforcement;
4. mark visual QA and external MCPs as PARTIAL/opt-in;
5. explain model-class recommendation versus host-controlled switching;
6. add a concise Current Verified Status table;
7. add an Autonomy Boundaries section;
8. link test counts only after revalidation against the website source date;
9. update installation to use an isolated Python environment;
10. add explicit privacy/consent controls or remove the PII intake form;
11. remove hardcoded consent=true behavior;
12. update sitemap metadata;
13. preserve the existing visual identity unless accessibility or responsive tests demonstrate a problem;
14. run build, responsive checks, keyboard navigation, console/network checks, and a real browser smoke before deployment.

## Recruiter review

A first-time reviewer can now determine from the README:

- what was built: a local governance, routing, execution-boundary and evidence toolkit;
- why it is interesting: deterministic controls around an LLM-assisted workflow;
- what works: governance, audit, bounded bootstrap/certification, registries and tests;
- what remains bounded: browser E2E, external MCP, host execution and model application;
- how to inspect it: focused commands and a reproducible test path.

Remaining confusion:

- the source tree still exposes a legacy named-consumer adapter and core defaults;
- the public website tells a more productized story than the repository;
- the absence of a license makes reuse intent unclear.

## Agentic-systems engineering review

The rewritten README avoids treating roles as agents, workflows as automation, model recommendations as switching, MCP profiles as connectivity, and failure logs as learning.

Residual technical concerns:

- named-consumer coupling remains in reusable core paths;
- a simulated MCP fallback can be misread by callers that inspect only ok=true;
- current Codex CLI readiness lacks the expected approval flag;
- committed operational logs remain part of the architecture even after redaction;
- Browser Smoke is opt-in and not part of the reproduced local PASS;
- the automatic CI workflow runs focused suites rather than the complete test suite.

## License status

LICENSE_DECISION_REQUIRED

No LICENSE or COPYING file exists and GitHub reports no detected license.

- MIT is suitable for simple permissive reuse.
- Apache-2.0 adds an explicit patent grant.
- Proprietary/all-rights-reserved preserves viewing while withholding reuse permission.

No license was selected in this task.

## Architecture audit backlog

1. Remove the named downstream-project default and environment-variable coupling from reusable tools.
2. Replace the consumer-specific adapter with a generic adapter contract or move it to its consumer repository.
3. Separate runtime event logs from publishable seed fixtures without breaking readiness checks.
4. Make MCP simulated fallback impossible to confuse with live execution.
5. Define the host approval behavior when the installed Codex CLI lacks the expected approval option.
6. Provision and re-run real Browser Smoke before claiming current browser evidence.
7. Resolve the pytest configuration warning under the installed pytest version or enforce the declared pytest<9 environment.
8. Decide and add a repository license.
9. Align the external WebCodexAtlas repository under a separately authorized task.

## Final validation

| Check | Result | Evidence |
|---|---|---|
| Full suite | PASS | 830 passed, 1 skipped in 859.40s |
| Skipped case | EXPECTED | Real-browser smoke is opt-in and requires provisioned Chromium |
| Python environment | VERIFIED | Python 3.14.5 / pytest 9.0.3 for the local publication run |
| `compileall` | PASS | `tools` and `tests` |
| Governance | PASS | Canonical root-first structure and contracts consistent |
| `atlas_verify` | PASS | Governance, audit, surface audit, and operational parity |
| Decision Benchmark V1 | PASS IN SCOPE | 45-case deterministic dataset; 3 focused tests passed |
| `git diff --check` | PASS | No whitespace errors |
| Baseline main CI | PASS | Run 31176337424 at `ca535ac` |
| Live website HTTP | PASS | `/`, `/validar-idea`, `/sitemap.xml`, and `/robots.txt` returned 200 |
| Website build and visual regression | NOT_RUN | Source belongs to external repository `lkswally/WebCodexAtlas` |

The first post-rewrite `atlas_verify` run correctly reported missing canonical skill/workflow/command mentions. The README was corrected with a compact canonical index; the re-run passed with zero failed checks.

No website source, deployment configuration, Vercel setting, Git history, or unrelated repository was modified.
