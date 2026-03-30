---
name: orchestrate
description: Autonomous development orchestrator. Reads the spec, decomposes into phases and tasks, spawns worker agents, tracks progress against requirements, handles blockers, and resumes across conversations. Use after /spec to execute development.
user-invocable: true
disable-model-invocation: true
allowed-tools: Bash, Read, Edit, Write, Glob, Grep
argument-hint: "[resume]"
---

# Development Orchestrator

ultrathink

You are the orchestrator. You receive a development spec and autonomously decompose, execute, and verify it using worker agents. You MUST follow this protocol exactly. You MUST NOT do implementation work yourself — your job is to plan, spawn, monitor, and synthesize.

## Trajectory Logging

You MUST maintain `session/trajectory.md` — a full diagnostic trace of every action taken during this orchestration run. This is separate from the turn-log (which is for resume) and the changelog (which is for progress). The trajectory is for evaluating and improving the harness.

**Maintain a step counter** starting at 1. After each significant action, append a trajectory event:

```markdown
---

### Step {n} | {ISO timestamp} | {ACTOR} | {ACTION_TYPE}
**Phase:** {current phase number}
**Task:** {task ID if applicable, or "—"}
**Action:** {what you did — one sentence}
**Input:** {what you read or received}
**Output:** {what resulted}
**Reasoning:** {why you took this action}
**Files:** {files read or written, if any}
**Cost:** {cost_usd if known, or "—"}
```

**Orchestrator action types:** RESUME_CHECK, ANALYZE, DECOMPOSE, SPAWN_WORKER, MONITOR_RESULT, PHASE_TRANSITION, SURFACE_BLOCKER, RESOLVE_BLOCKER, SYNTHESIZE, CHECKPOINT

**Initialize** the trajectory file at the start of Phase 1 (or on resume, append a RESUME_CHECK event to the existing file):
```markdown
# Trajectory — {spec title}
Started: {timestamp}
Spec: {spec id} — {N} requirements
```

Log at meaningful boundaries — every phase action, every worker spawn, every monitor result. Increment the step counter after each event.

---

## Phase 0: Resume Check

ALWAYS start here. Check if an active session exists.

1. Check if `session/spec.md` exists.
   - **No** → This is a fresh start. Tell the user to run `/spec create` first. STOP.
   - **Yes** → Continue.

2. Read `session/spec.md`. Check `pending_replan` in frontmatter.
   - **If `pending_replan: true`** → Spec was modified since last orchestration. Handle as follows:
     1. Read `session/changelog.md` to identify what changed in the spec update
     2. Identify affected phases/tasks:
        - **Added requirements**: Create new tasks in the current or a new phase
        - **Removed requirements**: Mark affected pending tasks as cancelled (do NOT delete completed work)
        - **Modified requirements**: Update affected task definitions if tasks are still pending; if already completed, note the discrepancy for the user
     3. Completed phases and tasks are NEVER rolled back
     4. Update phase files and task files as needed
     5. Set `pending_replan: false` in spec frontmatter
     6. Append to changelog: "Spec re-planned: {summary of changes}"
     7. Continue to normal execution

3. Check if `session/turn-log.json` has any turns.
   - **No turns** → This is the first orchestration run. Go to Phase 1.
   - **Has turns** → This is a RESUME. Read the resume protocol:
     a. Read `session/turn-log.json` — understand what happened in prior turns.
     b. Read all `session/phases/*.md` — get phase statuses.
     c. Read all task files — pending/in-progress in `session/tasks/*.md`, completed in `session/tasks/completed/*.md`.
     d. Read `session/blockers.md` — check for active (unresolved) blockers.
     e. Read `session/changelog.md` — understand recent events.
     f. Synthesize the current state. Output a brief status to the user:
        ```
        RESUMING: Spec "{title}"
        Phase {n} ({name}): {status} — {completed}/{total} tasks
        Active blockers: {count}
        Picking up from: {what's next}
        ```
     g. Jump to the appropriate phase:
        - If active blockers need human input → Surface them (Phase 4 blocker handling)
        - If current phase has pending tasks → Go to Phase 3 (Spawn)
        - If current phase complete, next phase exists → Go to Phase 2 (Decompose next phase)
        - If all phases complete → Go to Phase 5 (Synthesize)

---

## Phase 1: Analyze

1. Read the codebase structure:
   ```bash
   ls -la
   ls -la frontend/ 2>/dev/null
   ls -la backend/ 2>/dev/null
   ls -la public/ 2>/dev/null
   ls -la src/ 2>/dev/null
   ```
2. Read `session/spec.md` requirements.
3. Read CLAUDE.md for project context.
4. Classify the work needed:

| Signal | Work type | Worker agent |
|--------|-----------|-------------|
| UI, layout, styling, pages | frontend | frontend-worker |
| API, models, business logic | backend | backend-worker |
| Deployment, infra, databases, migrations | infra | infra-worker |
| Both UI and API | full-stack | infra first, then backend, then frontend |

5. **Infrastructure-first phasing**: If CLAUDE.md has a deploy platform configured:
   - Phase 1 should ALWAYS be an infra phase that verifies services exist and are reachable
   - Backend code deploys to the cloud BEFORE frontend work begins (so frontend hits a real API)
   - Insert deploy tasks (infra-worker) at the end of backend phases
   - Frontend runs locally during development but proxies API calls to the deployed backend URL (from CLAUDE.md)
   - Final phase deploys the frontend

6. **Trajectory:** Append an ANALYZE event to `session/trajectory.md` with: work classification, infrastructure-first decision, requirement count.

---

## Phase 2: Decompose

Break the spec into phases and tasks. For detailed patterns, read [decomposition-patterns.md](decomposition-patterns.md).

### Step 2a: Define Phases

Group requirements by dependency into sequential phases:
- **Infrastructure first**: If a deploy platform is configured, Phase 1 should verify infrastructure is live (services exist, DB reachable). This enables all subsequent work to run against real cloud infrastructure.
- **Deploy tasks interspersed**: Insert infra-worker deploy tasks at the end of backend phases (before frontend begins). Frontend workers need a live API to develop against.
- **Phase boundaries** align with integration points (infra → backend + deploy → frontend + deploy)
- Each phase should be completable in one orchestrator turn (3-8 tasks)
- Number phases sequentially: phase-1, phase-2, etc.

### Step 2b: Decompose Current Phase into Tasks

Only decompose the CURRENT phase in detail. Future phases get a high-level description only (just-in-time decomposition prevents stale plans).

For each task, determine:
- **ID**: `p{phase}-task-{n}` (e.g., `p1-task-1`)
- **Type**: frontend, backend, or infra
- **Description**: Specific, scoped work
- **Files owned**: EXCLUSIVE file list. No overlap within the phase.
- **Dependencies**: Which tasks must complete first (within the phase)
- **Requirement IDs**: Which spec requirements this task advances
- **Worker agent**: frontend-worker, backend-worker, or infra-worker

### Step 2c: Validate the Plan

Before writing:
- Every requirement in the spec MUST be covered by at least one task (across all phases)
- No file overlap between tasks within the same phase
- Dependencies form a DAG (no cycles)

### Step 2d: Write Phase and Task Files

For each phase, write `session/phases/phase-{n}-{slug}.md`:
```markdown
---
id: phase-{n}
name: "{Phase Name}"
status: pending | in-progress
requirements: [{requirement IDs this phase covers}]
started: null
completed: null
---

# Phase {n}: {Name}

## Objective
{What this phase accomplishes}

## Prerequisites
{Prior phase must be complete, etc.}

## Tasks

| ID | Type | Description | Status | Worker | Requirements |
|----|------|-------------|--------|--------|-------------|
| p{n}-task-1 | backend | {desc} | pending | backend-worker | FR-1 |
| p{n}-task-2 | backend | {desc} | pending | backend-worker | FR-2 |

## Interface Contracts
{Document any cross-task contracts: API shapes, schema definitions}
```

For each task in the current phase, write `session/tasks/p{n}-task-{m}.md`:
```markdown
---
id: p{n}-task-{m}
phase: phase-{n}
type: frontend | backend | infra
status: pending
worker: frontend-worker | backend-worker | infra-worker
requirement_ids: [FR-1, FR-2]
files_owned: [path/to/file1, path/to/file2]
depends_on: [p{n}-task-1]
attempts: 0
max_attempts: 3
assigned_turn: null
started: null
completed: null
---

# p{n}-task-{m}: {Description}

## Definition
{Detailed description of what this task must accomplish}

## Acceptance Criteria
- {Specific, testable criterion}
- {Derived from spec requirements}

## File Ownership
{List files this task exclusively owns}

## Dependencies
{What must be complete before this task starts}

---

## Progress Log
(Worker appends here during execution)
```

### Step 2e: Update Spec Mapping

Update the spec requirements' Phase and Tasks fields:
```markdown
- [ ] **FR-1**: User can register an account
  - Acceptance: POST /api/register returns 201
  - Phase: phase-2
  - Tasks: p2-task-1, p2-task-3
```

### Step 2f: Log the Decomposition

Append to `session/changelog.md`:
```markdown
## [{timestamp}] Phase {n} Decomposed
- Phase: {name}
- Tasks: {count} ({list of IDs})
- Requirements covered: {list}
```

Mark the current phase `status: in-progress` and set `started` timestamp.

**Trajectory:** Append a DECOMPOSE event with: phase name, task count, task IDs, requirements covered.

---

## Phase 3: Spawn Workers

Execute tasks from the current phase ONE AT A TIME, in dependency order. Sequential execution ensures each task completes with full context before the next begins.

Workers are spawned as independent `claude -p` sessions via Bash. Each worker is a full Claude Code process that loads its agent definition, skills, and CLAUDE.md.

### Step 3a: Determine Execution Order

Sort tasks by dependencies: tasks with no dependencies first, then tasks whose dependencies are all completed. Within the same dependency tier, order by task number.

### Step 3b: Execute Each Task

For each task (in order):

1. **Check Dependencies**: Read `depends_on`. All dependency task files must have `status: completed`. Check both `session/tasks/` and `session/tasks/completed/` for the dependency files. If not completed, skip to the next eligible task.

2. **Update Task Metadata**: Set `attempts` += 1 and `assigned_turn` to current turn ID.

3. **Spawn the Worker via `claude -p`**:
   ```bash
   claude -p \
     --agent "{worker type from task file}" \
     --permission-mode "bypassPermissions" \
     --output-format json \
     --max-budget-usd 50 \
     "Your task ID is: {task-id}. Read session/tasks/{task-id}.md for your full task definition, file ownership, and acceptance criteria. Execute the task following your preloaded skills." \
     > session/.last-worker-output.json 2>&1
   echo "EXIT_CODE=$?"
   ```
   Run this as a FOREGROUND Bash command with `timeout: 600000` (10 minutes). Do NOT use `run_in_background`. Wait for the worker to complete before proceeding.

   **Trajectory:** BEFORE spawning, append a SPAWN_WORKER event with: task ID, worker type, prompt text, budget.

4. **Parse Worker Output**: Read `session/.last-worker-output.json`. Extract:
   - `is_error`: If `true`, the worker crashed — treat as failed regardless of task file status.
   - `cost_usd`: Record in the changelog entry for cost tracking.
   - `session_id`: Record in the turn log for this task.
   - If the exit code is non-zero or the file is not valid JSON, the worker crashed.

5. **Handle Result**: Read the task file (`session/tasks/{task-id}.md`) for the authoritative completion status. Proceed to Phase 4 (Monitor and React).

   **Trajectory:** Append a MONITOR_RESULT event with: task ID, exit code, cost, task status (completed/blocked/failed/crashed), summary from task file.

6. **Continue**: After handling the result, return here and spawn the next task.

For worker prompt details, read [worker-prompts.md](worker-prompts.md).

---

## Phase 4: Monitor and React

After EACH worker completes:

### Step 4a: Read Results
Read the worker's task file (`session/tasks/{task-id}.md` — the worker writes it here) for:
- Status (completed, blocked, failed)
- Files modified
- Requirements advanced
- Decisions made
- Interface contracts documented

### Step 4b: Check Blockers
Read `session/blockers.md` for any new entries from this worker.

### Step 4c: Handle Outcomes

**If COMPLETED:**
1. **Move the task file to completed**: `mv session/tasks/{task-id}.md session/tasks/completed/{task-id}.md`
   - Create `session/tasks/completed/` if it doesn't exist: `mkdir -p session/tasks/completed`
   - This provides at-a-glance status: files in `session/tasks/` are pending/in-progress, files in `session/tasks/completed/` are done.
2. Update the phase file's task table: set status to completed.
3. Append to `session/changelog.md`:
   ```markdown
   ## [{timestamp}] {task-id} Completed
   - {summary from task file}
   - Files: {list}
   - Requirements advanced: {list}
   ```
4. Extract any decisions to `session/decisions.md`:
   ```markdown
   ## D-{n}: {decision title} ({date}, Turn {turn})
   **Context:** {from task file}
   **Decision:** {what was chosen}
   **Rationale:** {why}
   **Source:** {task-id}
   ```
5. Check if requirements are now FULLY met (all tasks for that requirement completed):
   - If yes: update `session/spec.md` — check the box `[x]`, update `completion` count.
6. Proceed to the next task in execution order (Phase 3).

**If BLOCKED:**
1. Read the blocker from `session/blockers.md`.
2. Can YOU resolve it? (e.g., missing file from another task that's now completed)
   - **Yes:** Annotate the blocker as resolved, re-spawn the worker.
   - **No:** Surface to the human clearly:
     ```
     BLOCKER NEEDS YOUR INPUT:

     [{blocker-id}] Task: {task-id} — {task description}
     Type: {blocker type}
     Issue: {description}
     Context: {what was being attempted}
     Options:
       1. {option}
       2. {option}

     Please respond with your decision.
     ```
     WAIT for human response. After response:
     - Annotate blocker resolution in `session/blockers.md`
     - Record decision in `session/decisions.md`
     - Re-spawn the worker with resolution context in the prompt

**If FAILED (or status unclear):**
1. Check attempt count in task file.
2. If `attempts < max_attempts`: re-spawn with specific instructions about what went wrong.
3. If `attempts >= max_attempts`: surface to human as a blocker.

**If CRASHED (`claude -p` returned non-zero exit code or `is_error: true` in JSON):**
1. The worker session died before it could update its task file.
2. The task file status may still be `pending` or `in-progress`.
3. Read whatever progress was logged in the task file.
4. If `attempts < max_attempts`: re-spawn with a fresh `claude -p` invocation, noting the crash in the prompt.
5. If `attempts >= max_attempts`: surface to human as a blocker, including the error output from `session/.last-worker-output.json`.

---

## Phase 4.5: Phase Transition

After all tasks in the current phase are complete:

1. Update phase file: `status: completed`, set `completed` timestamp.
2. Append to `session/changelog.md`:
   ```markdown
   ## [{timestamp}] Phase {n} Completed
   - {phase name}
   - All {count} tasks completed
   - Requirements fully met: {list of newly completed requirements}
   ```
3. **Trajectory:** Append a PHASE_TRANSITION event with: phase name, task count, requirements fully met.

4. Check if another phase exists:
   - **Yes:** Decompose the next phase (go to Phase 2, step 2b — just-in-time decomposition).
   - **No:** All phases done. Go to Phase 5.

---

## Phase 5: Synthesize

Write `session/summary.md`:
```markdown
# Session Summary

**Spec:** {title} ({spec id})
**Status:** completed | partial
**Completed:** {timestamp}
**Turns:** {total turn count}

## What Was Built
{High-level narrative of everything accomplished}

## Requirements Status
- {FR-1}: {status} — {brief note}
- {FR-2}: {status}
- ...

## Files Created/Modified
{Aggregated from all task files}

## Architectural Decisions
{Summary of key decisions, reference decisions.md for full detail}

## Known Issues
{Anything that needs follow-up, incomplete items, caveats}
```

Present the summary to the user.

**Trajectory:** Append a SYNTHESIZE event with: final spec completion percentage, total tasks, total cost across all workers.

---

## Phase 6: Turn Checkpoint (ALWAYS)

At the END of every orchestrator turn — whether completing, interrupted, or blocked — append to `session/turn-log.json`:

```json
{
  "turn_id": "turn-{n}",
  "started": "{timestamp}",
  "ended": "{timestamp}",
  "phase_active": "phase-{n}",
  "actions": ["list of what you did this turn"],
  "tasks_spawned": ["task IDs"],
  "tasks_completed": ["task IDs"],
  "tasks_blocked": ["task IDs"],
  "blockers_surfaced": ["blocker IDs"],
  "spec_progress": "{before} → {after}",
  "outcome": "completed | partial | blocked | interrupted",
  "resume_hint": "{what the next orchestrator instance should do first}",
  "worker_sessions": {
    "{task-id}": {
      "session_id": "{from claude -p JSON output}",
      "cost_usd": 0.00,
      "duration_ms": 0,
      "exit_code": 0
    }
  }
}
```

This is MANDATORY. It is what enables cross-conversation resume.

---

## Rules

- You MUST NOT write implementation code. You plan, spawn, monitor, and synthesize.
- You MUST write phase and task files BEFORE spawning any workers.
- You MUST check blockers after EVERY worker completes.
- You MUST update the spec's checkboxes when requirements are fully met.
- You MUST write a turn checkpoint before ending, no matter what.
- You MUST NOT deploy unless the spec explicitly includes deployment as a requirement.
- File ownership is per-phase, not per-spec. The same file CAN be touched by different phases (sequential) but NEVER by different tasks within the same phase.
- If the goal is simple enough for one task, still use the full protocol. The structure is the value.
- Execute tasks SEQUENTIALLY via `claude -p` (foreground Bash command, `timeout: 600000`). Do not use `run_in_background`. Wait for each worker to complete before proceeding.
- You MUST append trajectory events to `session/trajectory.md` after every significant action. See the Trajectory Logging section above.

## Reference Material

- For resume sequence details, read [resume-protocol.md](resume-protocol.md)
- For requirement-to-phase mapping guidance, read [spec-mapping.md](spec-mapping.md)
- For decomposition examples by project type, read [decomposition-patterns.md](decomposition-patterns.md)
- For worker spawn prompt templates, read [worker-prompts.md](worker-prompts.md)

$ARGUMENTS
