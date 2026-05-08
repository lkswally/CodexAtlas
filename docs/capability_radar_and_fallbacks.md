# Capability Radar and Fallback Models

Date: 2026-05-08

Scope: Codex-Atlas factory only. No REYESOFT changes, no derived-project changes, no MCP activation, no config mutation.

## Executive diagnosis

Atlas already adapted the safest parts of `claude-vibecoding`: intent clarification, visual direction, anti-generic review, evidence-based recommendations, readiness gates, phase guidance, decision feedback, model-routing advice and decision-council review.

The remaining high-value gap is not another runtime. It is clearer policy around when to escalate from local evidence to visual/media tooling or external model fallbacks.

## Atlas vs reference matrix

| Area | Atlas today | Reference pattern | Gap | Effort | Benefit | Recommendation |
| --- | --- | --- | --- | --- | --- | --- |
| Orchestration | Explicit dispatcher, phase guidance, quality gate | 5-phase orchestrator with hooks and Engram | Atlas is safer but less automatic | Medium | Medium | Keep explicit; do not copy runtime automation |
| Skills | Structured skills with metadata and behavior specs | Large specialized agent catalog | Atlas has enough core skills for factory work | Low | Medium | Add skills only through `skill_evaluator` |
| Evidence / QA | Evidence-bound design audit and quality gate | Evidence collector plus reality checker | No real screenshot/browser evidence yet | Medium | Medium | Watchlist; prefer manual evidence first |
| Branding | Brand/design review skills and policies | brand-agent with mood vectors and anti-patterns | No local design dataset or asset pipeline | Medium | Medium | Add policy now; dataset later only if repeated need |
| Visual media | Static/read-only audits | image-agent, logo-agent, video-agent | Atlas lacks media generation by design | High | Low-Medium | Defer runtime; keep advisory policy |
| Readiness | `quality_gate_report`, `atlas_verify`, certify | certification and reality checker | Atlas is strong for static/project structure | Low | High | Keep improving aggregator only from existing evidence |
| Decisions | priority engine, feedback, decision-council | chairman synthesis and false-positive guardrails | Atlas has enough for high-risk decisions | Low | High | Keep decision-council reserved for hard calls |
| Context/memory | JSONL logs, decision feedback, error patterns | Engram, DAG state, progressive loading | Atlas avoids external memory risk | Medium | Medium | Do not add Engram; improve summaries if logs grow |
| External tools | external_tool_policy advisory-only | Context7, Playwright, CodePen, deploy tools | Atlas intentionally blocks real MCP/tooling | Low | High | Keep default deny |
| Anti-hang | Timeouts in helpers, skipped/fail outputs | hook/runtime guardrails | Atlas avoids long-running tools | Low | High | Continue tool-level timeout and explicit skipped states |

## What not to copy

- `.claude` runtime layout
- global `CLAUDE.md` as the main instruction surface
- automatic hooks
- Engram as required memory
- Pixel Bridge
- Playwright MCP as default QA
- CodePen/21st.dev runtime pulls
- image/video generation agents with API keys
- automatic deploy, git push or provider setup

The useful pattern is discipline: clarify intent, require visual direction, demand evidence, avoid generic outputs, and refuse PASS without proof.

## MCP, branding, image and video capability matrix

| Capability | Use | Covered today | Reference contribution | Effort | Risk | Priority | Recommendation |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Branding review | Check identity, tone, typography and differentiation | Yes | brand-agent schema, anti-convergence, anti-patterns | Low | Low | High | Keep and refine policies |
| UX/UI static audit | Detect generic layouts and public-readiness issues | Yes | visual direction + pre-return audit | Low | Low | High | Keep current audit path |
| Screenshot visual QA | Validate rendered UI evidence | No | evidence-collector screenshot discipline | Medium | Medium-High | Medium | Watchlist; manual evidence before browser automation |
| Image analysis | Review user-provided visual references | Partial | visual fidelity scoring | Medium | Medium | Medium | Advisory-only until local workflow exists |
| Image generation | Produce hero/brand assets | No | image-agent fallback chain | High | High | Low | Defer; derived-project opt-in only |
| Logo generation | Produce vector identity | No | logo-agent workflow | High | High | Low | Defer; not Atlas core |
| Video review | Check video fallback/readiness | No | video fallback rule | Medium | High | Low | Policy only |
| Video generation | Generate animated backgrounds | No | video-agent CSS fallback discipline | High | High | Low | Defer; never block readiness |
| OpenAI Docs MCP | Official docs lookup | Adapter fallback exists | Not from reference | Medium | Medium | Medium | Keep blocked until CLI/MCP verified |
| Context7 / Docs MCP | Component/docs lookup | No real MCP | Reference uses for 21st.dev | Medium | Medium | Low-Medium | Watchlist; adapter/docs first |
| GitHub MCP | Remote repo/PR context | Local clone and web enough today | Not essential | Medium | Medium | Low | Prefer local clone or read-only CLI later |
| Playwright MCP | Browser evidence | No | Strong reference value but runtime-heavy | High | High | Medium later | Watchlist only |
| Engram memory | Persistent cross-session state | Local memory/logs exist | Reference depends on it | High | High | Low | Do not adopt now |

## NVIDIA Build fallback evaluation

This is a documentary benchmark, not an executed benchmark. No NVIDIA endpoint was called, no key was used and no Atlas config was changed.

NVIDIA docs say developers can access NIM endpoints through the NVIDIA API catalog and that the catalog provides free serverless APIs for development. Individual model pages still require account/API key handling, so Atlas should treat all candidates as manual benchmark options, not automatic routing targets.

| Model | Type | Free endpoint | Ideal use | Strengths | Weaknesses / risk | Atlas compatibility | Priority | Recommendation |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `qwen/qwen3-coder-480b-a35b-instruct` | Coding / agentic coding | Verified in catalog | Coding fallback, agentic code tasks | Long context, coding focus, browser-use claims | External key, unknown latency/cost limits in this environment | Good as manual benchmark | High | Benchmark manually before any profile |
| `minimaxai/minimax-m2.7` | Text reasoning/coding | Verified in catalog | General fallback for planning and coding | Recent, coding + reasoning + office tasks | Newer model; needs local benchmark | Good as manual benchmark | High | Benchmark manually |
| `deepseek-ai/deepseek-v3.2` | Reasoning/tool-use LLM | Verified in catalog listing | Planning, audits, structured reasoning | Long-context and agentic claims | Model behavior must be checked for false positives | Good as manual benchmark | High | Benchmark manually |
| `deepseek-ai/deepseek-v3.1-terminus` | Hybrid reasoning/tool calling | Verified in catalog listing | Audits and tool-aware planning | 128K context, function-calling claims | Older than v3.2; benchmark needed | Medium | Medium | Secondary benchmark |
| `moonshotai/kimi-k2-thinking` | Reasoning / tool use | Verified in catalog listing | Deep planning, architecture alternatives | Long context and reasoning claims | Unknown reliability for Atlas governance tone | Medium | Medium | Benchmark for planning only |
| `moonshotai/kimi-k2-instruct` | Coding/reasoning | Verified in catalog listing | Low-cost coding/planning fallback | Strong open MoE claims | Needs direct test on Atlas prompts | Medium | Medium | Watchlist benchmark |
| `meta/llama-4-maverick-17b-128e-instruct` | Multimodal general model | Verified in catalog | Visual reasoning, image understanding | Multimodal and multilingual | Not coding-specialized; license/behavior review needed | Medium | Medium | Benchmark for image analysis only |
| `google/gemma-3-27b-it` | Multimodal reasoning | Verified in catalog | Visual QA and image reasoning | 128K context, image input | Not a coding fallback | Medium | Medium | Benchmark for visual analysis |
| `microsoft/phi-4-multimodal-instruct` | Multimodal image/audio | Verified in catalog | Lightweight visual/audio review | 128K context, image/audio reasoning | Not ideal for deep code/architecture | Medium | Medium | Benchmark for media review |
| `nvidia/nemotron-content-safety-reasoning-4b` | Safety classifier | Verified in catalog | Policy/safety classification | Custom policy adaptation | Not a general Atlas worker | Low-Medium | Medium | Watchlist for safety checks |
| `nvidia/nemotron-mini-4b-instruct` | Small instruction model | Verified in catalog | Low-cost summaries/RAG/function-calling experiments | Fast small model | Likely too weak for high-risk Atlas decisions | Medium for low-risk only | Low | Watchlist only |
| `nvidia/llama-3_2-nemoretriever-300m-embed-v1` | Embedding/retrieval | Verified in catalog | Future docs/search retrieval | Purpose-built retrieval | Requires adapter/indexing work | Low now | Low | Do not use yet |

## Shortlist by use case

| Use case | Best candidate | Runner-up | Current Atlas posture |
| --- | --- | --- | --- |
| Planning | `minimaxai/minimax-m2.7` | `moonshotai/kimi-k2-thinking` | Manual benchmark only |
| Coding | `qwen/qwen3-coder-480b-a35b-instruct` | `deepseek-ai/deepseek-v3.2` | Manual benchmark only |
| Low-cost fallback | `nvidia/nemotron-mini-4b-instruct` | `google/gemma-3n-e4b-it` | Watchlist, not for critical work |
| Audit/review | `deepseek-ai/deepseek-v3.2` | `minimaxai/minimax-m2.7` | Manual benchmark only |
| Multimodal review | `google/gemma-3-27b-it` | `microsoft/phi-4-multimodal-instruct` | Manual benchmark only |
| Safety/policy | `nvidia/nemotron-content-safety-reasoning-4b` | `meta/llama-guard-4-12b` | Watchlist |
| Discard for Atlas core now | video/world-generation, autonomous-driving, digital-human and domain-specific models | N/A | Not relevant to factory governance |

## Manual benchmark protocol

Run the same prompt set against each candidate and score 1-5:

- follows constraints
- asks for missing information
- avoids unsupported claims
- preserves Atlas boundaries
- produces actionable evidence
- avoids false positives
- produces concise output
- handles Spanish/English mixed context

Do not benchmark with secrets, private project data or write access.

## Prompt for deeper Claude benchmark

```md
Quiero que evalues modelos de NVIDIA Build como fallback manual para Codex-Atlas, sin integrarlos todavia.

Contexto:
- Atlas es una factory gobernada para crear y auditar proyectos.
- No debe tocar REYESOFT, proyectos derivados ni config global.
- El routing interno de Codex Desktop sigue siendo manual/advisory.
- NVIDIA solo se evalúa como fallback externo cuando falten tokens/capacidad en otra herramienta.

Modelos candidatos:
- qwen/qwen3-coder-480b-a35b-instruct
- minimaxai/minimax-m2.7
- deepseek-ai/deepseek-v3.2
- deepseek-ai/deepseek-v3.1-terminus
- moonshotai/kimi-k2-thinking
- moonshotai/kimi-k2-instruct
- google/gemma-3-27b-it
- microsoft/phi-4-multimodal-instruct
- nvidia/nemotron-content-safety-reasoning-4b
- nvidia/nemotron-mini-4b-instruct

Evalua:
- planning
- coding
- audit/review
- visual/multimodal review
- low-cost summarization
- safety/policy classification

Para cada modelo devolve:
- fit con Atlas
- riesgos
- falsos positivos detectables
- costo/contexto esperado
- si merece benchmark manual
- si merece profile futuro
- si debe descartarse

No propongas integracion automatica. Si falta informacion oficial o benchmark real, marca `unknown` y pedi el dato.
```

## Model routing review

The current Codex Desktop router is aligned with the user-visible model list and keeps switching manual:

- planning/architecture: `GPT-5.4`
- standard implementation: `GPT-5.3-Codex` or `GPT-5.2-Codex`
- delicate code changes: `GPT-5.1-Codex-Max`
- documentation and low-risk actions: `GPT-5.4-Mini` or `GPT-5.1-Codex-Mini`
- standard audits: `GPT-5.2`, with `GPT-5.4` escalation for high complexity

No code change is recommended right now. The latest quality-gate execution already routes the low-risk "Avoid ..." action to a mini model while keeping strategic phase actions on stronger reasoning.

## Next safe improvement

Keep the new policies advisory-only and observe two or three real Atlas tasks before adding any adapter. If repeated tasks need visual evidence, the safest next implementation would be a read-only `visual_evidence_brief` skill that collects required screenshots/references and returns `skipped` when evidence is missing.
