# Project Guidelines for Claude

## Project Overview

{{PROJECT_DESCRIPTION}}

## Design Context

{{DESIGN_CONTEXT}}

## Architecture

- **Frontend**: {{FRONTEND_FRAMEWORK}}
- **Backend**: {{BACKEND_FRAMEWORK}}
- **Database**: {{DATABASE}}
- **Deployment**: {{DEPLOY_PLATFORM}}

## Deployment

- Platform: {{DEPLOY_PLATFORM}}
- Dev server port: {{DEV_SERVER_PORT}}
- Dev server command: `{{DEV_SERVER_COMMAND}}`
- Backend API URL: https://{{PROJECT_SLUG}}-api.onrender.com
- Frontend URL: https://{{PROJECT_SLUG}}-frontend.onrender.com

### Development Workflow

Backend and database run on Render. Frontend runs locally during development for fast visual iteration, proxying API calls to the deployed backend. The orchestrator deploys backend code before starting frontend tasks, so the frontend always hits a real API with a real database.

## Orchestration System

This project uses an autonomous development orchestration system. Key commands:

- `/spec create` — Create a structured development specification
- `/spec update` — Modify an existing spec
- `/spec show` — View spec with completion status
- `/orchestrate` — Execute the spec: decompose, spawn workers, track progress
- `/status` — Diagnostic: where things stand relative to the spec

### How It Works

1. Human creates a spec with `/spec create "description"`
2. `/orchestrate` reads the spec, decomposes into phases and tasks
3. Worker agents are spawned as independent `claude -p` sessions (frontend-worker, backend-worker, infra-worker) and execute tasks autonomously
4. Progress is tracked in `session/` directory (gitignored)
5. Blockers are surfaced to the human for resolution
6. `/status` shows progress at any time
7. Orchestrator resumes across conversations by reading session state from disk

### Session Directory

All orchestration state lives in `session/` (ephemeral, gitignored):
- `spec.md` — The human-approved specification
- `phases/*.md` — Phase definitions with task tables
- `tasks/*.md` — In-progress task files with progress logs
- `tasks/completed/*.md` — Completed task files (moved here on completion)
- `turn-log.json` — Cross-conversation resume support
- `changelog.md`, `decisions.md`, `blockers.md` — Audit trail

## Testing Policy

- **Local testing**: Use dev-browser for UI verification (`/verify-ui`)
- **Backend testing**: Workers write and run tests as part of task execution
- **User feedback**: The user reports back with results from deployment
