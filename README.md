# Software Factory

**Prompt to production.** A Claude Code orchestration toolkit with pre-built skills, worker agents, and deployment configs that turns a product description into deployed, tested software — autonomously.

```
/spec create "build an invoice tracker for freelancers"
/orchestrate
```

That's it. The factory handles decomposition, coding, testing, visual design, and deployment across backend, frontend, and infrastructure — with you in the loop only when it matters.

---

## How It Works

```
  You describe it          The factory builds it           You push to deploy

  "Build a..."    ──►   Spec ──► Phases ──► Tasks   ──►   Deployed on Render
                              │                │
                         Orchestrator     Worker Agents
                         decomposes       execute code
                         the plan         autonomously
```

1. **Onboard** — Run the setup wizard. Answer a few questions about your stack. The factory installs skills, agents, and configs into your project.
2. **Spec** — Describe what you want. The spec skill interviews you and produces a structured requirements doc.
3. **Orchestrate** — One command. The orchestrator decomposes your spec into phases, spawns specialized worker agents (`claude -p` headless sessions), tracks progress, and handles failures.
4. **Deploy** — Infrastructure-first workflow. Backend deploys and tests against a real database before frontend work begins. You `git push` when ready — Render auto-deploys.

## What's In The Box

### Pre-Built Skills

| Skill | What It Does |
|-------|-------------|
| **orchestrate** | Decomposes specs into phases and tasks, spawns workers sequentially, monitors results, resumes across conversations |
| **spec** | Interactive requirements gathering — interviews you, produces structured specs with acceptance criteria |
| **bold-design** | Fights generic AI aesthetics. Enforces domain-specific design: distinctive typography, color from the product's world, signature visual elements |
| **verify-ui** | Autonomous screenshot loop — takes screenshots via dev-browser, analyzes against requirements, iterates until the UI is right |
| **backend-test** | Test-driven backend development against real databases. No mocks, no SQLite substitutes |
| **deploy** | Full Render operations — CLI commands, API reference, blueprint schema, debugging playbooks |
| **worker-protocol** | Shared conventions for all workers — task lifecycle, blocker escalation, interface contracts between tasks |
| **status** | Session diagnostics — progress, blockers, requirement coverage, decision audit trail |

### Worker Agents

| Agent | Skills | Purpose |
|-------|--------|---------|
| **backend-worker** | worker-protocol, backend-test | Models, migrations, API endpoints — tested against real cloud DB |
| **frontend-worker** | worker-protocol, bold-design, verify-ui | UI development with domain-specific design and visual verification |
| **infra-worker** | worker-protocol, deploy | Service provisioning, deployments, health verification |

### Generated Configs

Every onboarded project gets:

```
your-project/
├── CLAUDE.md               # Project context: stack, design direction, deployed URLs
├── render.yaml             # Render blueprint (monorepo: backend/ + frontend/)
└── .claude/
    ├── settings.json       # Permissions for headless workers
    ├── agents/             # 3 worker agent definitions
    └── skills/             # 8 skills (orchestration + development + deployment)
```

## Quick Start

```bash
# Clone the factory
git clone https://github.com/nbdesai1992/software-factory.git

# Go to your project
cd my-project

# Run the onboarding wizard
python /path/to/software-factory/onboard.py

# Open Claude Code
claude

# Build
/spec create "describe what you want"
/orchestrate
```

### One-Time Render Setup

Before your first `/orchestrate`:

1. `brew install render && render login`
2. Push your repo to GitHub
3. Render Dashboard → Blueprints → "New Blueprint Instance" → select repo
4. Set any API keys as env vars in the Render Dashboard

After that, the orchestrator runs autonomously. You push when it's time to deploy.

## Architecture

```
          /spec create "..."
                │
                ▼
          ┌───────────┐
          │   SPEC     │  Structured requirements + acceptance criteria
          └─────┬─────┘
                │
          /orchestrate
                │
                ▼
       ┌─────────────────┐
       │  ORCHESTRATOR    │  Decomposes → spawns → monitors → resumes
       └────────┬────────┘
                │  claude -p (headless sessions, sequential)
     ┌──────────┼──────────┐
     ▼          ▼          ▼
┌──────────┐ ┌──────────┐ ┌──────────┐
│ backend  │ │ frontend │ │  infra   │
│ worker   │ │ worker   │ │ worker   │
│          │ │          │ │          │
│ Models   │ │ Bold     │ │ Deploy   │
│ APIs     │ │ Design   │ │ Verify   │
│ Tests    │ │ Verify   │ │ Monitor  │
└──────────┘ └──────────┘ └──────────┘
     │          │          │
     ▼          ▼          ▼
  Real DB    Screenshots   Render
  on Render  + iteration   auto-deploy
```

**Infrastructure-first:** Cloud services are provisioned first. Backend develops and tests against the real Render database. Frontend wires to the deployed API. You `git push` to deploy — a natural checkpoint for code review.

**Sequential execution:** Workers run one at a time via `claude -p` headless CLI. Each gets its own Claude Code session with full tool access. The orchestrator reads results from disk and spawns the next worker.

**Resumable sessions:** All state lives in `session/` on disk. Close Claude Code mid-orchestration, reopen it, run `/orchestrate` — it picks up exactly where it left off.

## Commands

| Command | Description |
|---------|-------------|
| `/spec create "goal"` | Interview → structured spec with requirements |
| `/spec update` | Modify the spec (triggers re-planning on next orchestrate) |
| `/spec show` | View spec with completion tracking |
| `/orchestrate` | Execute the spec autonomously |
| `/status` | Progress summary |
| `/status detail` | Full phase and task breakdown |
| `/status blockers` | Active blockers needing your input |
| `/status requirements` | Requirement → task coverage map |

## Deploy Platform

**V1:** Render — full adapter with CLI reference, API docs, blueprint schema, pricing guide, and starter `render.yaml` generation (monorepo with `rootDir` per service).

**Future:** Vercel, Fly.io. To add a platform: `factory/templates/skills/deploy/{platform}/SKILL.md.tpl`.

## Human In The Loop

The system is autonomous but pauses for you when it matters:

| When | What You Do | Time |
|------|------------|------|
| Push to deploy | Review code, `git push` | 1-2 min |
| Missing API keys | Set env vars in Render Dashboard | 5 min |
| Unclear requirement | Answer the orchestrator's question | 1-5 min |
| Design review (optional) | Check `session/design-direction.md` | 5 min |

Full guide: [docs/HUMAN-INTERVENTION-GUIDE.md](docs/HUMAN-INTERVENTION-GUIDE.md)

## Re-Onboarding

```bash
python /path/to/software-factory/onboard.py --reconfigure
```

Re-reads saved config, lets you change settings, re-generates all files.
