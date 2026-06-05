# Policy: frontend_visual_execution_guard

`frontend_visual_execution_guard` is a Codex-native quality gate for UI-facing work.
It does not run a browser, install tooling, activate MCPs or modify derived
projects. It checks whether the handoff has enough declared evidence to support
a frontend visual-ready claim.

## Purpose

Atlas must not confuse a successful build with a visually correct product.
For frontend, landing, marketing, fullstack and internal-tool work, the final
handoff should show:

- a clear visual brief or visual intent contract;
- mobile-first checkpoints;
- references, moodboard or a clear reason why references were not needed;
- browser or screenshot QA evidence;
- responsive checks;
- validation for promised motion, scroll, video or animation;
- a non-generic layout, color, typography, spacing, button and card system;
- honest limitations when the browser or screenshot check could not be run.

## States

- `ready`: the visual execution evidence is sufficient for a cautious handoff.
- `needs_visual_review`: the work may build, but still lacks enough visual or
  responsive evidence.
- `blocked_missing_visual_evidence`: the handoff claims visual completion while
  browser/screenshot evidence is missing.
- `blocked_motion_unverified`: motion, scroll-scrub, video or animation was
  promised but not validated.
- `blocked_generic_template_risk`: the output shows generic template risk
  without a strong brief and references.

## Hard Rules

- Build OK is not visual OK.
- Missing browser/screenshot QA must not be reported as visual pass.
- If browser QA could not run, the limitation must be stated explicitly.
- If motion, scroll-scrub or video is promised, Atlas must verify the asset,
  event, progress calculation and fallback, or block the visual-ready claim.
- If the surface repeats generic hero/cards/pill-button patterns without visual
  intent or references, Atlas must flag generic template risk.
- The guard remains advisory/readiness in Atlas core; product implementation
  still happens only in derived projects.
