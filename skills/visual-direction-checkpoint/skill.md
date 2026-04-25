# Skill: visual-direction-checkpoint

## Purpose

Turn a vague product or page brief into an explicit visual direction before UI work expands.

## When to use

- when mood, audience or originality are not explicit
- when a landing page or static site brief feels too generic
- when Atlas needs a lightweight equivalent of the reference repo’s Visual Direction Checkpoint

## When NOT to use

- when the request is already a concrete code implementation
- when the main problem is repo structure or governance drift
- when the task is deployment or destructive work

## Required inputs

- product context
- target audience or current audience guess
- references if available

## Expected outputs

- structured visual direction checkpoint
- explicit audience, mood and originality prompts
- next-step recommendation before design implementation

## Recommended agent

- `ux_architect`

## Recommended workflow

- `design_intelligence_pipeline`

## Recommended model

- `creative_product`

## Risks

- treating vague design preference as enough direction
- collapsing into generic marketing-site defaults
- proceeding to UI work without audience clarity

## Validations

- audience is explicit or marked as missing
- mood or vibe is explicit
- originality level is explicit
- next action is clear and non-destructive

## Examples

- "Run a visual direction checkpoint for this product brief."
- "Before building the landing page, clarify audience, mood and originality."

## Relationship with the orchestrator

The orchestrator should recommend this skill when a task asks for direction, mood, vibe, audience, originality or design clarification before actual UI implementation.
