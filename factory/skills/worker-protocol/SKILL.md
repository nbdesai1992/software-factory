---
name: worker-protocol
description: Shared convention for orchestrated workers. Use proactively when executing a task that was decomposed by the orchestrator, or when a session/ directory exists in the project root.
user-invocable: false
---

# Worker Protocol

You are executing a scoped task as part of an orchestrated development workflow. You MUST follow this protocol.

## Session Directory

All shared state lives in `session/` at the project root:

```
session/
  spec.md                    # The spec (read for context, do NOT modify)
  phases/
    phase-{n}-{name}.md      # Phase definitions (read for context)
  tasks/
    {your-task-id}.md         # YOUR task file (you read AND write this)
    completed/                # Completed task files (moved here by orchestrator — read for interface contracts)
  blockers.md                 # Append here when stuck (append-only)
  changelog.md                # Do NOT write (orchestrator only)
  decisions.md                # Do NOT write (orchestrator only)
  turn-log.json               # Do NOT write (orchestrator only)
  summary.md                  # Do NOT write (orchestrator only)
  design-direction.md         # Shared file — read if doing frontend work; the FIRST frontend worker
                              # in a project creates this during bold-design pre-exploration.
                              # Not subject to files_owned restriction.
  trajectory.md               # Append-only diagnostic trace — append your actions here (see Trajectory Logging)
```

## Task File Format

Your task file (`session/tasks/{your-task-id}.md`) has YAML frontmatter and a body. The orchestrator created it. You update it during execution.

### Fields You Update:
- `status`: Change from `pending` → `in-progress` → `completed` (or `blocked`/`failed`)
- `started`: Set to ISO timestamp when you begin
- `completed`: Set to ISO timestamp when you finish
- `attempts`: The orchestrator sets this before spawning you

### Sections You Append To:
- `## Progress Log` — Your work log. Append updates as you hit milestones.

## On Start

1. Read your task file: `session/tasks/{your-task-id}.md`
2. Understand: definition, acceptance criteria, file ownership, dependencies
3. Check dependencies: for each ID in `depends_on`, read that task file (check `session/tasks/completed/{id}.md` first, then `session/tasks/{id}.md`) and confirm `status: completed`. If not completed, write a blocker and STOP.
4. Update your task file: set `status: in-progress`, set `started` timestamp.
5. Append to Progress Log:
   ```markdown
   ### Started ({ISO timestamp})
   - Reading codebase to understand context
   - Dependencies verified: {list}
   ```

## During Work

Append progress updates to your task file's `## Progress Log` as you hit milestones:

```markdown
### Update {n} ({ISO timestamp})
- Completed: {what you did}
- Next: {what you're doing next}
- Files modified: {list}
```

## Trajectory Logging

You MUST append discrete events to `session/trajectory.md` for each significant action you take. This is a diagnostic trace of the full orchestration run — separate from your Progress Log (which is in your task file). The trajectory enables evaluation and improvement of the harness.

**Format for each event** (append to the file):
```markdown
---

### Step — | {ISO timestamp} | {your worker type} | {ACTION_TYPE}
**Task:** {your task ID}
**Skill:** {skill name if applicable, or "—"}
**Action:** {what you did — one sentence}
**Input:** {what you read or received}
**Output:** {what resulted}
**Files:** {files read or written}
**Reasoning:** {why you took this action}
```

Leave the step number as "—" (the orchestrator numbers them post-run).

**Action types:** START_TASK, READ_FILE, WRITE_FILE, RUN_COMMAND, SCREENSHOT, ANALYZE_SCREENSHOT, DESIGN_EXPLORATION, RAISE_BLOCKER, RECORD_DECISION, COMPLETE_TASK

**Log at meaningful boundaries, not every micro-action:**
- Log WRITE_FILE once for "Created Invoice model" — not per-line
- Log RUN_COMMAND once for "Ran pytest, 5/5 passed" — not per-test
- Log DESIGN_EXPLORATION once for the full bold-design pre-exploration output
- Always log START_TASK and COMPLETE_TASK

## Interface Contracts

If your task CREATES an interface (API endpoint, database schema, component props):
- Document it in your task file under `## Interface Contract`:
  ```markdown
  ## Interface Contract
  ### API: POST /api/users
  - Request: `{ email: string, password: string }`
  - Response: `{ id: int, email: string, created_at: string }`
  - Status: 201 (created), 400 (validation), 409 (conflict)
  ```

If your task CONSUMES an interface:
- Read the producing task's file for the contract.
- If it doesn't match your expectations, raise a blocker.

## When Stuck

If you hit something you cannot resolve — unclear requirement, missing dependency, needs human decision, external action required:

1. Append to `session/blockers.md`:
   ```markdown
   ## B-{next number}: {short title}
   **Raised:** {ISO timestamp}
   **Task:** {your task ID}
   **Type:** {unclear-requirement | missing-dependency | needs-human-decision | external-action}
   **Description:** {what's blocking you}
   **Context:** {what you were trying to do when you hit this}
   **Options:** {possible paths forward, if you see any}
   ```
2. Update your task file: set `status: blocked`.
3. Append to Progress Log: `### Blocked: {short reason}`
4. **STOP.** Do NOT guess. Do NOT work around it.

## Recording Decisions

When you make a significant technical choice (framework, pattern, architecture, algorithm), record it in your task file:

```markdown
### Decision
- **What:** {choice made}
- **Why:** {rationale — why this over alternatives}
```

The orchestrator will extract these into `session/decisions.md`.

## On Completion

Update your task file frontmatter: set `status: completed`, set `completed` timestamp.

Append a completion summary:
```markdown
### Completed ({ISO timestamp})

**Summary:**
- {What you built/changed — 2-3 sentences}
- Requirements advanced: {FR-X, FR-Y}

**Files Modified:**
- {path}: {what changed}

**Test Results:** (if applicable)
- {test}: PASS
- {test}: PASS
```

## Rules

- You MUST only modify files listed in `files_owned` in your task file.
  - **Exception — integration touchpoints:** You MAY make minimal, single-line additions to shared integration files (e.g., adding a router registration to `main.py`, adding a `<script>` tag to `index.html`, adding a CSS `<link>` to `index.html`, writing `session/design-direction.md`) when your task requires it. Document any such changes in your Progress Log. You MUST NOT refactor, restructure, or make substantive changes to files outside your ownership.
- You MUST NOT modify other task files, phase files, changelog.md, decisions.md, turn-log.json, summary.md, or spec.md.
- You MUST NOT deploy, push, or make changes visible outside the local repo.
- You MUST NOT rename or reorganize files outside your ownership.
- Your task file is your single source of truth. Keep it updated.
