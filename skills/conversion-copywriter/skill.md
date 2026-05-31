# Skill: conversion-copywriter

## Purpose

Audit and improve product copy in Atlas-native advisory mode.

This skill is for clarity, narrative, trust and conversion discipline. It should explain what the product is, who it serves, what problem it solves, what action the user should take and which objections remain unresolved, without drifting into hype or fake certainty.

## When to use

- when a landing, product page or flow needs clearer messaging
- when the hero is confusing, generic or too abstract
- when CTAs, forms or microcopy feel weak or misleading
- when Atlas should review whether the copy sounds credible instead of AI-generated filler

## When NOT to use

- when the task is only visual redesign with no messaging question
- when the request asks for guaranteed sales claims or invented proof
- when the task requires market research, legal review or backend implementation

## Required inputs

- page copy, hero or landing text
- target audience if known
- problem statement if known
- CTA labels or next-step flow if available

## Expected outputs

- copy readiness state
- clarity, conversion, trust and tone scores
- hero-message diagnostics
- open objections, warnings and missing inputs
- recommended copy changes without fake claims

## Recommended agent

- `planner` for structured copy review
- `reviewer` when the copy needs a stricter risk/trust pass

## Recommended workflow

- `atlas_project_pipeline`

## Recommended model

- `deep_reasoning`

## Risks

- sounding polished but vague
- using generic AI phrases instead of real value
- promising outcomes that the product cannot support
- leaving privacy, next-step or consent questions unanswered

## Validations

- do not promise guaranteed revenue, profitability or certainty
- keep CTA language aligned with the real next step
- flag generic AI-style filler and unsupported claims
- recommend clearer audience/problem/value framing before adding more copy

## Examples

- "Audit this landing hero and CTA for clarity and conversion."
- "Tell me if this copy sounds trustworthy or like generic AI filler."
- "Review this form microcopy and the objections it still leaves open."

## Relationship with the orchestrator

The orchestrator should recommend this skill when the task is landing-copy review, CTA improvement, messaging clarity, trust diagnostics or conversion-oriented narrative refinement.
