# Design Intelligence Pipeline

This workflow is the Codex-native adaptation of the design, branding and visual QA block studied from the `claude-vibecoding` reference repo.

## Goal

Improve design direction and visual QA quality in Atlas-derived projects without importing Claude-only runtime pieces.

## Flow

1. **Intent clarification**
   - confirm audience, mood, vibe and originality
   - if the brief is vague, route to `visual-direction-checkpoint`
2. **Visual direction checkpoint**
   - lock explicit visual direction before UI implementation expands
   - require audience, mood, originality and non-goals
3. **Design-system review**
   - review typography, spacing, hierarchy and layout coherence
   - keep the review advisory and evidence-based
4. **Anti-generic UI audit**
   - inspect hero structure, CTA clarity, typography defaults, responsive baseline and contrast
   - warning before blocking unless risk is clear
5. **Evidence and reality check**
   - require concrete file evidence before declaring pass
   - report `status`, `warnings`, `evidence` and `next_action`

## Atlas constraints

- read-only by default
- no MCP required
- no hooks
- no hidden browser automation
- no deploy
- no REYESOFT mutation

## Expected outputs

- explicit visual direction
- design-system findings
- anti-generic warnings or blockers with evidence
- prioritized quick wins
- next action that is safe and human-readable
