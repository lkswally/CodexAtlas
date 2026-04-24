# Skill: product-branding-review

## Purpose

Review product positioning, audience, UX direction and branding quality without collapsing into generic output.

## When to use

- when reviewing brand direction for a product concept
- when a landing page or UX proposal feels generic
- when audience, value proposition or visual direction are unclear

## When NOT to use

- when the task is backend implementation
- when the request is a security review
- when the repo audit is the main problem

## Required inputs

- product context
- target audience
- current positioning or visual direction
- references if available

## Expected outputs

- branding/UX review
- anti-generic findings
- recommendations for audience, value proposition and direction

## Recommended agent

- `ux_brand`

## Recommended workflow

- `atlas_project_pipeline`

## Recommended model

- `creative_product`

## Risks

- generic taste without evidence
- confusing product review with visual implementation
- importing business-specific branding into Atlas core

## Validations

- audience is explicit
- value proposition is explicit
- anti-generic policy is respected
- recommendations stay advisory unless implementation is requested

## Examples

- "Review this product positioning and landing-page direction."
- "Audit the brand and UX proposal before we build."

## Relationship with the orchestrator

The orchestrator should recommend this skill when the task intent is `branding_ux` or when the request asks for audience, positioning, visual direction or anti-generic UX review.
