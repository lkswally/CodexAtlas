# Workflow: audit_repo

Legacy naming kept for compatibility with the executable command `audit-repo`.

## Purpose

Audit repository structure, governance metadata and drift before proposing deeper changes.

## Inputs

- workspace root
- canonical registry
- current policies

## Steps

1. Validate governance metadata
2. Check required structure
3. Compare docs against real files
4. List risks and gaps
5. Recommend next safe actions

## Output

- diagnosis
- findings
- recommended next steps

## Status

Documented and executable through `tools/atlas_dispatcher.py audit-repo`.
