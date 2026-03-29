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

## Step 1: Create a Shell Repo

Create a new empty repository on GitHub, then clone it locally:

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

- `.claude/skills/` — 8 pre-built skills (orchestration, testing, design, deployment, etc.)
- `.claude/agents/` — 3 worker agent definitions (backend, frontend, infra)
- `.claude/settings.json` — Permissions for headless worker sessions
- `CLAUDE.md` — Project context, architecture, deployed URLs
- `render.yaml` — Render blueprint with your services + database
- `.gitignore` — Updated with `session/`, `.env`

## Step 3: Push the Scaffolding

```bash
git add .
git commit -m "factory setup"
git push
```

## Step 4: Create Render Blueprint Instance

1. Go to [Render Dashboard](https://dashboard.render.com/)
2. **Blueprints** → **New Blueprint Instance**
3. Select your GitHub repo
4. Render reads `render.yaml` and creates:
   - `{your-project}-api` (backend web service)
   - `{your-project}-frontend` (frontend web service)
   - `{your-project}-db` (PostgreSQL database)
5. First deploy will fail — no application code yet. This is expected.
6. Set any API keys or secrets as env vars in the Render Dashboard.

## Step 5: Open Claude Code

```bash
claude
```

## Step 6: Create a Spec

```
/spec create "describe what you want to build"
```

The spec skill will interview you about features, scope, constraints, and success criteria. Review and approve the generated spec.

## Step 7: Orchestrate

```
/orchestrate
```

The orchestrator takes over:

1. **Infrastructure** — Verifies Render services exist, pulls DB credentials
2. **Backend** — Writes models, migrations, API endpoints, tests against real Render DB
3. **Deploy backend** — Commits code, asks you to `git push` (your review checkpoint)
4. **Frontend** — Writes UI with domain-specific design, wired to deployed backend API
5. **Deploy frontend** — Commits code, asks you to `git push`
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
| **Push to deploy** | Review the diff, run `git push origin main` |
| **Missing env var** | Set it in Render Dashboard, reply to the orchestrator |
| **Unclear requirement** | Answer the question, orchestrator records your decision |
| **Design review** (optional) | Check `session/design-direction.md` after first frontend task |

## Re-Onboarding

To change your project's configuration later:

```bash
python /path/to/software-factory/onboard.py --reconfigure
```
