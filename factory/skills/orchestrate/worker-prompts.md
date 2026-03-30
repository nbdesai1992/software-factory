# Worker Spawn Prompts

How the orchestrator constructs the `claude -p` command for each worker spawn.

## General Pattern

All workers are spawned as independent `claude -p` sessions via Bash:

```bash
claude -p \
  --agent "{worker type}" \
  --permission-mode "bypassPermissions" \
  --output-format json \
  --max-budget-usd {budget} \
  "{spawn prompt}" \
  > session/.last-worker-output.json 2>&1
echo "EXIT_CODE=$?"
```

Run this as a foreground Bash command with `timeout: 600000` (10 minutes). The orchestrator waits for each worker to complete before spawning the next. This is sequential execution mode.

The spawn prompt is MINIMAL. Workers read their full instructions from their task file and preloaded skills. The prompt just tells them which task to execute.

### Flag Reference

| Flag | Value | Purpose |
|------|-------|---------|
| `--agent` | `"{worker-type}"` | Loads agent definition from `.claude/agents/{worker-type}.md` (system prompt, tools, skills) |
| `--permission-mode` | `"bypassPermissions"` | Workers are non-interactive and cannot prompt for approval |
| `--output-format` | `json` | Returns structured JSON with `result`, `is_error`, `cost_usd`, `session_id` |
| `--max-budget-usd` | `50` (default) | Safety cap per worker invocation. High enough to avoid premature termination on subscription plans. |

## Capturing and Parsing Output

The JSON output is redirected to `session/.last-worker-output.json`. After the command completes, the orchestrator:

1. Checks the exit code: non-zero means crash/timeout.
2. Reads `session/.last-worker-output.json` and parses the JSON.
3. Extracts `is_error`, `session_id`, `cost_usd` for the turn log.
4. Reads the task file on disk (`session/tasks/{task-id}.md`) for the **authoritative** completion status.

The task file is always the source of truth — the JSON output is supplementary metadata.

## Frontend Worker Spawn

```bash
claude -p \
  --agent "frontend-worker" \
  --permission-mode "bypassPermissions" \
  --output-format json \
  --max-budget-usd 50 \
  "Your task ID is: {task-id}. Read session/tasks/{task-id}.md for your full task definition, file ownership, acceptance criteria, and dependencies. Execute the task following your preloaded skills (worker-protocol, bold-design, verify-ui)." \
  > session/.last-worker-output.json 2>&1
```

If there's a specific design context to pass:
```bash
claude -p \
  --agent "frontend-worker" \
  --permission-mode "bypassPermissions" \
  --output-format json \
  --max-budget-usd 50 \
  "Your task ID is: {task-id}. Read session/tasks/{task-id}.md for your full task definition. Design context: {brief direction from design-direction.md if it exists}. Execute following preloaded skills." \
  > session/.last-worker-output.json 2>&1
```

## Backend Worker Spawn

```bash
claude -p \
  --agent "backend-worker" \
  --permission-mode "bypassPermissions" \
  --output-format json \
  --max-budget-usd 50 \
  "Your task ID is: {task-id}. Read session/tasks/{task-id}.md for your full task definition, file ownership, acceptance criteria, and dependencies. Execute the task following your preloaded skills (worker-protocol, backend-test)." \
  > session/.last-worker-output.json 2>&1
```

If the task depends on a completed task with interface contracts:
```bash
claude -p \
  --agent "backend-worker" \
  --permission-mode "bypassPermissions" \
  --output-format json \
  --max-budget-usd 50 \
  "Your task ID is: {task-id}. Read session/tasks/{task-id}.md for your task definition. Also read session/tasks/completed/{dependency-id}.md for the interface contract you must consume. Execute following preloaded skills." \
  > session/.last-worker-output.json 2>&1
```

## Infrastructure Worker Spawn

```bash
claude -p \
  --agent "infra-worker" \
  --permission-mode "bypassPermissions" \
  --output-format json \
  --max-budget-usd 50 \
  "Your task ID is: {task-id}. Read session/tasks/{task-id}.md for your full task definition. Execute the task following your preloaded skills (worker-protocol, deploy)." \
  > session/.last-worker-output.json 2>&1
```

## Fix Worker Re-Spawn

When a worker failed or needs to address specific issues:

```bash
claude -p \
  --agent "{same worker type}" \
  --permission-mode "bypassPermissions" \
  --output-format json \
  --max-budget-usd 50 \
  "Your task ID is: {task-id}. This is attempt {n}. Read session/tasks/{task-id}.md — it contains the progress log from your previous attempt. The specific issues to fix: {list of issues}. Address ONLY these issues, do not refactor or rewrite." \
  > session/.last-worker-output.json 2>&1
```

## Blocker Resolution Re-Spawn

When a blocker has been resolved by the human:

```bash
claude -p \
  --agent "{worker type}" \
  --permission-mode "bypassPermissions" \
  --output-format json \
  --max-budget-usd 50 \
  "Your task ID is: {task-id}. This task was previously blocked. The blocker has been resolved: {resolution description}. Decision recorded as D-{n}: {decision summary}. Read session/tasks/{task-id}.md for context, then continue the task with this resolution applied." \
  > session/.last-worker-output.json 2>&1
```

## What NOT to Put in Spawn Prompts

- Do NOT embed the full task definition — workers read it from the task file
- Do NOT embed skill instructions — workers have skills preloaded via agent definition
- Do NOT embed the worker protocol — it's preloaded
- Keep prompts SHORT. The task file is the source of truth.

## Session ID Tracking

The JSON output includes a `session_id` field. Record this in the turn log's `worker_sessions` object. For most re-spawns, a fresh `claude -p` invocation with explicit context in the prompt is preferred over `claude -p --resume {session_id}` — it is simpler and avoids stale context accumulation.
