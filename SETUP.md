# Setup Guide

Step-by-step instructions for creating a new project with Software Factory.

## Prerequisites

- [Claude Code](https://claude.ai/claude-code) installed
- [Render CLI](https://docs.render.com/cli) installed: `brew install render`
- Render CLI authenticated: `render login`
- GitHub account with push access

Verify Render is ready:
```bash
render workspace current -o json
```

## Step 1: Create an Empty Shell Repo

Create a new empty repository on GitHub (no README, no .gitignore — completely empty), then clone it locally:

```bash
git clone https://github.com/your-username/your-project.git
cd your-project
```

## Step 2: Run the Factory Onboarding

From inside your project directory:

```bash
python /path/to/software-factory/onboard.py
```

The wizard asks about your project (name, description, domain, design direction, tech stack, deployment platform) and installs everything:

- `backend/` — Skeleton FastAPI app with `/health` endpoint
- `frontend/` — Skeleton Next.js app with `/api/health` route
- `.claude/skills/` — 8 pre-built skills (orchestration, testing, design, deployment, etc.)
- `.claude/agents/` — 3 worker agent definitions (backend, frontend, infra)
- `.claude/settings.json` — Permissions for headless worker sessions
- `CLAUDE.md` — Project context, architecture, deployed URLs
- `render.yaml` — Render blueprint defining your services + database
- `.gitignore` — Updated with `session/`, `.env`

## Step 3: Commit and Push

```bash
git add .
git commit -m "factory setup"
git push
```

This pushes the render.yaml, skeleton apps, and all configs to GitHub. Render's GitHub integration will detect the render.yaml.

## Step 4: Create Env Group + Blueprint Instance

### 4a: Create shared env group (one-time per workspace)

If you don't already have a `general_builder_keys` env group in your Render workspace:

1. Render Dashboard → **Env Groups** → **New Environment Group**
2. Name it `general_builder_keys` (or whatever you specified during onboarding)
3. Add your shared API keys (e.g., `ANTHROPIC_API_KEY`)

The `render.yaml` references this group via `fromGroup` — all services will automatically receive these keys when the blueprint is applied.

### 4b: Apply Blueprint Instance

This is a one-time manual step. Render does not support creating Blueprint Instances via API or CLI — it must be done in the Dashboard.

1. Go to [Render Dashboard](https://dashboard.render.com/)
2. **Select the correct workspace** (not a shared/team workspace unless intended)
3. **Blueprints** → **New Blueprint Instance**
4. Select your GitHub repo and the branch you're deploying from (e.g., `develop` or `main`)
5. Render reads `render.yaml` and creates:
   - `{your-project}-api` (backend web service, Python/FastAPI)
   - `{your-project}-frontend` (frontend web service, Node/Next.js)
   - `{your-project}-db` (PostgreSQL database)
   - Links the shared env group to both services
   - Sets cross-service URLs (`API_URL` on frontend, `FRONTEND_URL` + `CORS_ORIGINS` on backend)
6. First deploy will build and deploy the skeleton apps. Both `/health` endpoints should return `{"status": "ok"}`.

**Important:** The infra-worker will never create services via API. It only verifies that services exist (created by you here) and uses them for deployments, logs, and health checks. If you skip this step, the orchestrator will raise a blocker asking you to do it.

## Step 5: Open Claude Code

```bash
claude
```

Open Claude Code in your project directory. It will load CLAUDE.md and all the installed skills.

## Step 6: Create a Spec

```
/spec create "describe what you want to build"
```

The spec skill interviews you about features, scope, constraints, and success criteria. Review and approve the generated spec.

## Step 7: Orchestrate

```
/orchestrate
```

The orchestrator takes over:

1. **Infrastructure** — Verifies Render services exist, pulls DB credentials into `backend/.env`
2. **Backend** — Writes models, migrations, API endpoints, tests against real Render DB
3. **Deploy backend** — Commits code, asks you to `git push` (your review checkpoint). Render auto-deploys.
4. **Frontend** — Writes UI with domain-specific design, wired to deployed backend API
5. **Deploy frontend** — Commits code, asks you to `git push`. Render auto-deploys.
6. **Verify** — Screenshots the deployed site, checks against requirements

## Step 8: Check Progress

At any time:

```
/status              # Quick summary
/status detail       # Full phase and task breakdown
/status blockers     # What needs your input
/status requirements # Requirement → task coverage
```

## What You'll Be Asked During Orchestration

The system runs autonomously but pauses for you at these points:

| When | What to do |
|------|-----------|
| **Push to deploy** | Review the diff, run `git push` (Render auto-deploys on commit) |
| **Missing env var** | Set it in Render Dashboard, reply to the orchestrator |
| **Unclear requirement** | Answer the question, orchestrator records your decision |
| **Design review** (optional) | Check `session/design-direction.md` after first frontend task |

## Re-Onboarding

To change your project's configuration later:

```bash
python /path/to/software-factory/onboard.py --reconfigure
```

## Diagnostic: Trajectory

After each orchestration run, `session/trajectory.md` contains the full agentic trajectory — every discrete step taken by the orchestrator and workers. Use this for evaluating harness behavior and diagnosing issues.
