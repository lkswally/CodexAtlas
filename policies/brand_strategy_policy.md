# Brand Strategy Readiness Policy

## Purpose

`brand_strategy_readiness` is an Atlas-native advisory layer for checking whether a brand direction feels coherent, differentiated, credible and appropriate for its intended audience.

It exists to prevent:
- generic template branding;
- inconsistent tone between copy and visuals;
- vague positioning;
- low-trust presentation;
- category confusion;
- visual identity choices without clear rationale.

## Scope

This policy applies to frontend, landing, marketing and other UI-facing surfaces where brand perception materially affects trust, clarity and perceived product quality.

It does not apply to:
- backend-only services;
- purely internal technical utilities with no user-facing brand surface;
- runtime business logic.

## What Atlas may do

Atlas may:
- assess positioning clarity;
- assess differentiation quality;
- assess audience fit;
- assess brand tone consistency;
- assess palette role clarity;
- assess typography hierarchy;
- flag generic or template-like brand signals;
- recommend bounded brand improvements.

## What Atlas must not do

Atlas must not:
- promise that a brand direction will sell more;
- claim market leadership without evidence;
- generate logos or image assets in this layer;
- import external brand kits automatically;
- modify products directly from this readiness layer;
- treat generic style references as sufficient evidence of differentiation.

## Required posture

This layer is always:
- advisory;
- opt-in;
- reversible;
- non-destructive.

It must not auto-install tools, activate MCPs or add design dependencies.

## Blocking guidance

Atlas should raise warnings or blockers when it detects:
- no clear target audience;
- no meaningful category or positioning;
- generic template-like visual identity;
- unsupported trust claims;
- inconsistent verbal or visual tone;
- missing palette roles;
- missing typography hierarchy;
- CTA posture that conflicts with the brand promise.

## Human boundary

Brand decisions remain human-owned. Atlas can structure the review, show risks and suggest next steps, but it cannot certify brand quality from theory alone.
