# UI UX Design System Readiness Policy

## Purpose

`ui_ux_design_system_readiness` gives Atlas a governed, advisory-only way to recommend a stronger visual system before a UI implementation expands.

It exists to reduce:
- generic SaaS-template outputs
- weak hierarchy and palette choices
- stack choices made by habit instead of fit
- motion choices made by impulse instead of intent

It does not generate final UI code, install libraries, or modify derived projects automatically.

## When To Use

Use this layer when the request involves:
- landing pages
- marketing sites
- dashboards
- product surfaces with visible branding
- onboarding, form flow, empty, error or loading states
- medium or large UI changes where "just implement the screen" would skip visual system thinking

## When Not To Use

Do not require this layer for:
- backend-only work
- API-only changes
- purely operational scripts
- low-scope bug fixes with no meaningful visual surface

## Expected Inputs

The readiness layer works best when Atlas already has:
- project or product type
- audience
- visual intent direction
- basic stack signal when available

If these are missing, the layer should return advisory gaps instead of inventing a design system.

## What It Recommends

The layer may recommend:
- a landing or dashboard pattern
- a style direction
- palette strategy
- typography direction
- motion intensity and motion library posture
- anti-patterns to avoid
- a pre-delivery checklist
- a stack recommendation framed as fit guidance, not as a dependency mandate

## Motion Policy

Atlas must not install Framer Motion or Motion in the Atlas core.

For derived frontend projects, Atlas may recommend a React motion library only when:
- the project already uses a React-compatible stack
- CSS-only motion would likely become fragile
- the animation need is explicit and meaningful

Atlas should prefer CSS when:
- the motion need is simple
- the surface is mostly static
- a JS motion library would add complexity without clear benefit

All motion recommendations must respect reduced-motion accessibility expectations.

## 21st And External Inspiration

21st Magic or Magic Chat stay outside this layer's runtime.

This layer may suggest that external inspiration could help, but only through the existing readiness and approval boundaries in:
- `component_inspiration_readiness`
- `creative_pipeline_readiness`

External inspiration must not become a requirement for declaring a UI ready.

## Advisory Boundaries

This layer is advisory-only.

It must not:
- generate final components
- install libraries
- activate MCPs
- call external services
- rewrite a design system into a derived project automatically

## Success Condition

The layer is successful when Atlas can explain:
- what kind of visual system fits the product
- what should be avoided
- whether CSS is enough for motion
- whether a React motion library is worth considering
- what should be checked before delivery
