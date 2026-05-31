# Policy: chrome_devtools_mcp_readiness

## Goal

Define when Atlas should recommend Chrome DevTools MCP as a manual, opt-in browser-truth layer for frontend quality work.

This policy is advisory and readiness-only.

## What This Layer Can Do

- detect whether a project looks frontend-oriented
- decide whether current Atlas checks may still be insufficient for real browser debugging
- recommend Chrome DevTools MCP only when layout, CSS, console, network or performance signals justify it
- warn about telemetry, browser-profile access and privacy implications
- recommend `--no-usage-statistics` for any future manual setup

## What This Layer Must Not Do

- do not install Chrome DevTools MCP
- do not run `npx`
- do not open a browser
- do not activate any MCP automatically
- do not mutate global Codex config
- do not touch derived projects

## When To Use

Use `chrome_devtools_mcp_readiness` when:

- a frontend project still has visual drift or browser-only uncertainty
- screenshots exist but debugging truth is still missing
- CSS, layout, console, network or performance symptoms are likely
- Atlas needs to say whether local checks are enough or whether a real browser would materially help

## When Not To Use

Do not use it when:

- the task is backend, CLI or non-visual
- current local design and evidence checks already look sufficient
- the request is to activate or run the MCP immediately

## Risks

This layer must always surface:

- telemetry risk
- browser profile access risk
- privacy risk

It must remind that browser-truth tooling can expose:

- authenticated sessions
- local browser history or profile state
- noisy or environment-specific performance readings

## Human Approval Boundary

Human approval is required before:

- adding Chrome DevTools MCP to Codex config
- connecting it to a real browser profile
- using it against any project that may expose sensitive local context

## Relationship To Existing Atlas Layers

- `visual_intent_contract` and `ui_ux_design_system_readiness` still govern design direction.
- `design_quality_enforcement` still governs local design quality signals.
- `visual_fidelity_judge` still governs screenshot-versus-intent evidence.
- `mcp_readiness_check` remains the canonical source for whether MCP servers appear configured locally.
- `quality_gate_report` may expose this posture, but it must not auto-activate the MCP.

## Initial Stance

- advisory only
- manual opt-in only
- no automatic activation
- no browser launch
- no global config mutation
