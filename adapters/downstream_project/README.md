# Downstream Project Adapter

This directory documents the boundary between CodexAtlas and a downstream consumer repository.

## Current contract

- the consumer repository keeps its own runtime and business logic
- the consumer identifies itself through `.atlas-project.json`
- Atlas tools run from `<atlas_root>/tools/` with `--project <consumer_root>`

## Compatibility note

- Atlas canonical structure is root-first
- downstream repositories must not mirror active Atlas core files in product paths
- legacy compatibility files belong in the downstream repository, outside the reusable core
