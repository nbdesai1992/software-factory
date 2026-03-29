# Resume Protocol

Detailed instructions for resuming an orchestration session across conversations.

## When Resume Triggers

Resume triggers when `session/spec.md` exists AND `session/turn-log.json` has at least one turn entry.

## The Resume Sequence

### Step 1: Read Turn History
```bash
cat session/turn-log.json
```
Parse the `turns` array. The last entry tells you:
- Which phase was active
- Which tasks were spawned, completed, or blocked
- The outcome (completed, partial, blocked, interrupted)
- The resume_hint (what to do first)

### Step 2: Read Phase Status
Glob all phase files:
```bash
ls session/phases/
```
Read each. Identify:
- Which phases are completed
- Which phase is in-progress (the current phase)
- Which phases are pending

### Step 3: Read Task Status
Glob task files for the current phase from both locations:
```bash
# Pending/in-progress tasks
ls session/tasks/p{current-phase}*.md
# Completed tasks
ls session/tasks/completed/p{current-phase}*.md
```
Read each. Categorize:
- **completed**: In `session/tasks/completed/`, done, requirements advanced
- **in-progress**: In `session/tasks/`, worker may have finished after last turn ended — check for completion markers. If completed, move to `session/tasks/completed/`
- **blocked**: Check if the blocker has been resolved since (human may have responded)
- **pending**: Not yet spawned
- **failed**: Check attempt count

### Step 4: Read Blockers
```bash
cat session/blockers.md
```
Identify active (unresolved) blockers. Check if any have been resolved by human input since the last turn.

### Step 5: Read Spec
```bash
cat session/spec.md
```
Check:
- `pending_replan: true` → Spec changed, need to re-plan
- Completion count → How much is done
- Status → Still active?

### Step 6: Synthesize and Report

Output to the user:
```
RESUMING: "{spec title}"
Last turn: {turn-id} ({outcome})
Phase: {current phase name} — {status}
Tasks: {completed}/{total} in current phase
Blockers: {active count}
Resume action: {what you're doing next, derived from resume_hint}
```

### Step 7: Route to Correct Phase

Based on synthesis:

| Situation | Action |
|-----------|--------|
| Active blockers needing human input | Surface them, wait |
| Blocker resolved by human since last turn | Re-spawn blocked worker |
| In-progress tasks (worker may have finished) | Read task file, handle completion |
| Pending tasks with met dependencies | Spawn them |
| Current phase all complete | Transition to next phase |
| All phases complete | Synthesize final summary |
| `pending_replan: true` | Re-plan before continuing |

## Important Notes

- NEVER assume anything from a prior conversation. Read ALL state from disk.
- Workers spawned via `claude -p` complete independently. Their task files may show completion even if the orchestrator wasn't around to observe it. The turn log records each worker's `session_id` for reference.
- The turn-log's `resume_hint` is advisory — always verify against actual file state.
- If files are missing or corrupted, report the issue to the human rather than guessing.

## Worker Re-Spawn Strategy

When re-spawning a worker after resume:

| Situation | Strategy |
|-----------|----------|
| Blocked then resolved | Fresh `claude -p` spawn with blocker resolution context in the prompt. |
| Failed (attempt < max) | Fresh `claude -p` spawn with error context in the prompt. |
| Interrupted mid-task | Check the task file status. If still `in-progress` with no completion summary, use a fresh spawn — the previous `claude -p` session is no longer running. |

Always prefer fresh invocations over `--resume`. Fresh spawns have cleaner context and avoid accumulating stale state from prior attempts.
