# Workflow: create_project

## Purpose

Define how Atlas should bootstrap a derived project without mixing core and product logic.

## Expected outputs

- project brief
- selected templates
- local adapter decisions
- project-specific AGENTS rules
- validation checklist

## Rules

- do not copy Atlas core blindly
- keep adapters explicit
- keep product runtime outside Atlas core
- require human review before introducing automation or external integrations

## Status

Documented workflow with minimal executable support through the `project-bootstrap` skill scaffold mode.

## Related skill

- `project-bootstrap`
