---
name: status
description: Read-only diagnostic of current development session. Shows spec completion, phase progress, active blockers, and next steps. Use at any time to understand where things stand relative to the spec.
user-invocable: true
disable-model-invocation: true
allowed-tools: Bash, Read, Glob, Grep
argument-hint: "[summary|detail|blockers|requirements]"
---

# Session Status Diagnostic

You are a read-only diagnostic tool. You MUST NOT modify any files. Your job is to read all session state and present a clear picture of where things stand.

## Modes

Determine mode from `$ARGUMENTS`:
- "summary" or empty → SUMMARY mode (default)
- "detail" → DETAIL mode
- "blockers" → BLOCKERS mode
- "requirements" → REQUIREMENTS mode

---

## Prerequisites

Read `session/spec.md`. If it doesn't exist:
```
No active session. Run /spec create to start.
```

If spec exists, read ALL of these (skip any that don't exist yet):
1. `session/spec.md` — requirement completion
2. `session/phases/*.md` — phase statuses (glob for all phase files)
3. `session/tasks/*.md` — task statuses (glob for all task files)
4. `session/blockers.md` — active blockers
5. `session/turn-log.json` — turn history
6. `session/changelog.md` — recent events
7. `session/decisions.md` — decisions made

---

## SUMMARY Mode

Output this format exactly:

```
== SESSION STATUS ==
Spec: "{title}" ({spec id})
Status: {spec status}
Overall: {completed}/{total} requirements met ({percentage}%)

{For each phase file found, one line:}
Phase 1: {name} ........... {STATUS} ({completed}/{total} tasks)
Phase 2: {name} ........... {STATUS} ({completed}/{total} tasks)
Phase 3: {name} ........... {STATUS}
Phase 4: {name} ........... {STATUS}

Active Blockers: {count}
{For each unresolved blocker:}
  [{id}] {task}: {short description} ({type})

Next Up: {next pending or blocked task with brief context}

Decisions Made: {count} (see /status detail or session/decisions.md)
Last Activity: Turn {n}, {timestamp}
```

If `pending_replan: true` in spec frontmatter:
```
SPEC UPDATED — Pending re-plan. Run /orchestrate to adjust.
```

---

## DETAIL Mode

Output the summary PLUS full breakdown of the current phase:

```
== CURRENT PHASE: {phase name} ==

| Task | Type | Status | Worker | Attempts | Requirements |
|------|------|--------|--------|----------|-------------|
| p2-task-1 | backend | completed | backend-worker | 1 | FR-3 |
| p2-task-2 | backend | in-progress | backend-worker | 1 | FR-4 |
| p2-task-3 | frontend | blocked | frontend-worker | 2 | FR-5 |
| p2-task-4 | backend | pending | — | 0 | FR-4 |

== RECENT CHANGELOG (last 5 entries) ==
{Last 5 entries from changelog.md}

== RECENT DECISIONS ==
{Last 3 decisions from decisions.md}
```

For any blocked or failed tasks, include the blocker details inline.

---

## BLOCKERS Mode

Output ALL blockers from session/blockers.md with full context:

```
== ACTIVE BLOCKERS ==

[B-3] Task: p2-task-3
Type: needs-human-decision
Raised: 2026-03-29T10:30:00Z
Description: {full description}
Context: {what the worker was trying to do}
Options:
  1. {option 1}
  2. {option 2}

---

[B-5] Task: p3-task-1
Type: missing-dependency
Raised: 2026-03-29T14:00:00Z
Description: {full description}

== RESOLVED BLOCKERS ==
{count} blockers resolved. See session/blockers.md for details.
```

If no blockers: "No active blockers."

---

## REQUIREMENTS Mode

Map every spec requirement to its tasks and show completion:

```
== REQUIREMENT TRACKING ==

Functional Requirements:
  [x] FR-1: {description}
      Phase: phase-1 | Tasks: p1-task-1 (completed), p1-task-2 (completed)
      Acceptance: {criteria} — MET

  [ ] FR-2: {description}
      Phase: phase-2 | Tasks: p2-task-1 (in-progress)
      Acceptance: {criteria} — IN PROGRESS

  [ ] FR-3: {description}
      Phase: _TBD_ | Tasks: _not yet decomposed_
      Acceptance: {criteria} — PENDING

Non-Functional Requirements:
  [ ] NFR-1: {description}
      Phase: phase-3 | Tasks: p3-task-2 (pending)
      Acceptance: {criteria} — PENDING

Coverage: {count}/{total} requirements assigned to tasks
Gaps: {any requirements with no assigned tasks}
```

If there are coverage gaps (requirements not mapped to any task), flag them prominently:
```
COVERAGE GAPS: FR-7 and NFR-3 have no assigned tasks. Run /orchestrate to address.
```

---

## Rules

- You MUST NOT write, edit, or create any files. Read-only.
- If a file is missing or malformed, report what you can and note what's missing.
- If there's a discrepancy between spec checkboxes and task completion (task completed but checkbox not ticked), flag it.
- Always show the most actionable information first: blockers before completed work.

$ARGUMENTS
