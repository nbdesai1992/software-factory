---
name: spec
description: Create or update a structured development specification. Use when starting a new feature, project, or major change. Interviews the user and produces a trackable spec.md with requirement IDs, acceptance criteria, and scope boundaries.
user-invocable: true
disable-model-invocation: true
allowed-tools: Bash, Read, Write, Edit, Glob, Grep
argument-hint: "[create|update|show] [description of what to build]"
---

# Spec Management

ultrathink

You manage the development specification — the contract between the human and the orchestrator. You MUST follow the exact templates and conventions below.

## Modes

Determine mode from `$ARGUMENTS`:
- Starts with "create" → CREATE mode
- Starts with "update" → UPDATE mode
- Starts with "show" → SHOW mode
- No mode specified → if session/spec.md exists, SHOW mode. Otherwise, CREATE mode.

---

## CREATE Mode

### Step 1: Read the Codebase

Understand what exists before asking questions:
1. Read the project directory structure (`ls` the root, key subdirectories)
2. Read CLAUDE.md for project context
3. Read any existing session/spec.md (error if one already exists — tell user to use `update`)
4. Identify: tech stack, frameworks, existing features, deployment target

### Step 2: Interview the Human

Ask these questions (adapt to context, skip what's obvious from codebase):

1. **"What are you building?"** — Get the high-level goal in their words.
2. **"Who is it for?"** — User type, use cases.
3. **"What are the must-have features?"** — These become functional requirements.
4. **"What should it NOT do?"** — These become out-of-scope items.
5. **"Any technical constraints?"** — Framework preferences, deployment targets, compatibility.
6. **"How will you know it's done?"** — Success criteria.

Do NOT ask all questions at once. Ask 1-2, wait for response, then follow up. Be conversational, not bureaucratic.

### Step 3: Draft the Spec

Based on the interview, write the spec using this EXACT template:

```markdown
---
id: spec-{unix-timestamp}
title: "{Title from the goal}"
status: draft
created: "{ISO 8601 timestamp}"
updated: "{ISO 8601 timestamp}"
completion: 0/{total requirements}
pending_replan: false
---

# {Title}

## Overview
{2-3 paragraphs: what is being built, why, who it's for}

## Scope

### In Scope
- {bullet list of what this spec covers}

### Out of Scope
- {bullet list of explicit exclusions}

## Requirements

### Functional Requirements
- [ ] **FR-1**: {Requirement description}
  - Acceptance: {Specific, testable criteria for "done"}
  - Phase: _TBD_
  - Tasks: _TBD_
- [ ] **FR-2**: {Next requirement}
  - Acceptance: {criteria}

### Non-Functional Requirements
- [ ] **NFR-1**: {Requirement description}
  - Acceptance: {criteria}

## Technical Constraints
- {constraint 1}
- {constraint 2}

## Success Criteria
{Holistic definition of "done" — beyond individual requirements}
```

### Step 4: Present and Confirm

Show the drafted spec to the human. Ask: "Does this capture what you want to build? Any requirements to add, remove, or change?"

Iterate until the human approves.

### Step 5: Write to Disk

1. Create the session directory:
   ```bash
   mkdir -p session/phases session/tasks
   ```
2. Write `session/spec.md` with the approved spec
3. Initialize `session/changelog.md`:
   ```markdown
   # Changelog

   ## [{timestamp}] Spec Created
   - Title: "{title}"
   - Requirements: {count} functional, {count} non-functional
   - Status: draft
   ```
4. Initialize `session/decisions.md`:
   ```markdown
   # Architectural Decisions

   (No decisions recorded yet. Decisions are logged here as the orchestrator and workers make architectural choices during execution.)
   ```
5. Initialize `session/blockers.md`:
   ```markdown
   # Blockers

   (No blockers recorded yet. Workers write here when they hit issues they cannot resolve.)
   ```
6. Initialize `session/turn-log.json`:
   ```json
   { "turns": [] }
   ```

Tell the human: "Spec created. Run `/orchestrate` to begin execution."

---

## UPDATE Mode

### Step 1: Read Current Spec
Read `session/spec.md`. If it doesn't exist, tell the user to run `/spec create` first.

### Step 2: Accept Changes
The human describes what to change. Apply changes following these rules:

- **Adding requirements**: Use the next available ID. If FR-1 through FR-5 exist, new one is FR-6. NEVER reuse a removed ID.
- **Removing requirements**: Delete the requirement line entirely. Do NOT renumber other requirements.
- **Modifying requirements**: Update the description/acceptance in place. Keep the same ID.
- **Changing scope**: Update the In Scope / Out of Scope sections.

### Step 3: Update Frontmatter
- Set `updated` to current timestamp
- Set `pending_replan: true` — this signals the orchestrator to re-plan on next run
- Update `completion` denominator to reflect new total

### Step 4: Write and Log
- Write updated `session/spec.md`
- Append to `session/changelog.md`:
  ```markdown
  ## [{timestamp}] Spec Updated
  - Added: {list of added requirement IDs}
  - Removed: {list of removed requirement IDs}
  - Modified: {list of modified requirement IDs}
  - pending_replan set to true
  ```

Tell the human: "Spec updated. The orchestrator will re-plan on next run."

---

## SHOW Mode

### Step 1: Read Everything
Read `session/spec.md`. If it doesn't exist, say so.

### Step 2: Display
Show the spec with a summary header:

```
== SPEC: {title} ==
Status: {status}
Completion: {checked}/{total} requirements ({percentage}%)
Last Updated: {updated}

Functional Requirements:
  [x] FR-1: {short description}
  [ ] FR-2: {short description}
  [ ] FR-3: {short description}
  [x] FR-4: {short description}

Non-Functional Requirements:
  [ ] NFR-1: {short description}
  [x] NFR-2: {short description}
```

If `pending_replan: true`, warn: "Spec has been updated since last orchestration. Run /orchestrate to re-plan."

---

## Rules

- Requirement IDs are PERMANENT. Never reuse, never renumber.
- The spec skill creates the session/ directory. No other skill creates it.
- The spec skill NEVER writes to phase files, task files, or summary.md. That's the orchestrator's job.
- Only the orchestrator updates checkboxes and the completion count during execution. The spec skill only updates them via the UPDATE mode when the human explicitly changes requirements.

$ARGUMENTS
