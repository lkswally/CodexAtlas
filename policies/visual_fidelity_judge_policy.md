# Visual Fidelity Judge Policy

## Purpose

This layer is Atlas's third QA layer for frontend work:
1. local design and quality audits;
2. screenshot/runtime readiness;
3. screenshot-versus-intent fidelity judgment.

It does not run a browser, does not capture screenshots and does not call an external LLM by itself.

## Allowed Inputs

- explicit visual intent contract
- explicit brand profile or brand posture
- UI pre-return review
- design quality review
- existing screenshot evidence already produced elsewhere
- a structured project-local visual fidelity report

## Required Posture

- advisory only
- human approval boundary preserved
- no automatic PASS claims without evidence
- no claim of "visually aligned" unless screenshots and a structured comparison exist

## Accepted Evidence Shape

Atlas may treat a project-local report as valid evidence only when it includes:
- desktop and mobile coverage
- compared layers against intent and brand
- matched signals and/or drift signals
- a short summary of what was judged

## Blockers And Downgrades

- missing screenshot evidence means Atlas must not claim a strong visual PASS
- screenshot evidence without a structured comparison stays insufficient
- drift against intent, hierarchy, spacing, color or CTA behavior downgrades readiness

## Non-Goals

- no external screenshot capture
- no hidden model calls
- no browser automation from this layer
- no automatic fixes
