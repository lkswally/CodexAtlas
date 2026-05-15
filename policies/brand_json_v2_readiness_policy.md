# Brand JSON v2 Readiness Policy

## Purpose

`brand_json_v2_readiness` adapts the `brand.json v2` idea from the Vibecoding pipeline into an Atlas-safe readiness layer.

It does not generate a brand file automatically. It checks whether Atlas has enough explicit brand structure to justify stronger branding, visual-system, and handoff claims.

## When it is required

The readiness check is required when:

- the project is a landing page, public web surface, dashboard, or other UI-facing product
- Atlas is making a stronger claim about identity, differentiation, palette, typography, or visual quality
- a `visual_intent_contract` already says the project needs explicit visual direction

## What "v2 readiness" means in Atlas

A project is only considered `brand_json v2` ready when it has an explicit structured brand profile that covers:

- identity
- audience
- mood vector
- color strategy
- typography strategy
- layout and motion principles
- differentiation notes
- accessibility notes
- evidence expectations

An inferred profile may help analysis, but it is not strong enough to count as an explicit brand artifact for final UI-readiness claims.

## Inspiration versus copying

The profile may reference inspiration, but it must not collapse into imitation.

Atlas should flag readiness as weak when:

- inspiration references dominate differentiation notes
- derivative risk remains unresolved
- palette or typography choices still look like generic defaults

## Human approval boundary

Atlas should recommend human clarification when:

- the brand profile is only inferred
- core sections are missing
- derivative risk is present
- accessibility rationale is absent

## Relationship to existing Atlas layers

- `visual_intent_contract` defines the direction.
- `brand_profile_schema` defines the identity structure.
- `brand_json_v2_readiness` checks whether that structure is explicit and strong enough to be treated like a governed `brand.json v2` equivalent.

## Advisory-only scope

This readiness layer is read-only and advisory:

- it does not write `brand.json`
- it does not edit project files
- it does not resolve inspiration automatically
- it does not auto-approve branding claims
