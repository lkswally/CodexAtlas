# E2E Flows — Phase-based Requirements (Phase 1A.2)

## Overview

End-to-end (E2E) flows are explicit command sequences that must succeed for each project phase. They validate the project state before advancing to the next phase.

## Current Phase Mapping

E2E flows are defined in `config/phase_playbook.json` under each phase's `e2e_required` array.

### phase:idea → phase:planning
- **No E2E flows** — use intent clarifier to prepare brief

### phase:planning → phase:bootstrap
- **No E2E flows** — bootstrap command generates initial structure

### phase:bootstrap → phase:build
- **REQUIRED**: `audit-repo` ✅
  - Validates generated structure
  - Checks governance files (README, AGENTS)
  - Ensures minimum directory structure exists
  - **Blocker if fails**: Cannot move to build without passing audit

### phase:build → phase:audit
- **PERIODIC**: `audit-repo` 
  - Runs during implementation to verify structure integrity
  - Not blocking, but recommended every iteration
  - **Recommendation**: Run after each major feature to catch drift

### phase:audit → phase:certified
- **REQUIRED**: `certify-project` ✅
  - Final governance and structure validation
  - Confirms all blockers resolved
  - **Blocker if fails**: Cannot certify without passing certify-project

### phase:certified (stable)
- **No E2E flows** — project is locked

## How quality-gate-report Shows E2E Status

The `quality-gate-report` command outputs:

```json
{
  "e2e_flows_posture": {
    "phase": "bootstrap",
    "total_required": 1,
    "completed": 0,
    "missing": 1,
    "flows": [
      {
        "flow": "audit-repo",
        "description": "Verify project structure and governance files are present",
        "required_for": "move to build phase",
        "status": "not_yet_run"
      }
    ],
    "next_action": "Run E2E flow: audit-repo"
  }
}
```

## Usage

Check E2E requirements for current phase:

```bash
python tools/atlas_dispatcher.py --project <project_root> quality-gate-report
```

Look for `e2e_flows_posture` section in output. It shows:
- Which flows are required
- Whether they've been run
- What the next action should be

## Adding New E2E Flows (Future)

To add a new required E2E flow to a phase:

1. Edit `config/phase_playbook.json`
2. Add entry to `phase.e2e_required` array
3. Format:
   ```json
   {
     "flow": "command-id",
     "description": "what it validates",
     "required_for": "why it matters"
   }
   ```
4. Update documentation in this file
5. Test with `quality-gate-report --project <test_project>`

## Phase 1A.2 Scope

This implementation:
- ✅ Adds `e2e_required` array to `phase_playbook.json`
- ✅ Extracts and displays E2E flows in `quality-gate-report` output
- ✅ Shows next action (which flow to run next)
- ⏳ Does NOT yet integrate with orchestrator (enforcement comes in 1A.5)
- ⏳ Does NOT block phase transitions yet (advisory only)

## Future (Phase 1A.5+)

When Boot Sequence is implemented, orchestrator will:
- Check E2E flow requirements at phase transitions
- Block advancement if required flow fails
- Suggest next E2E flow to run
