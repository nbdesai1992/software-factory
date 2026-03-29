# Software Factory

Turn a product spec into working software using Claude Code's autonomous orchestration system.

## What It Does

Software Factory installs a multi-agent orchestration system into any project. You describe what you want to build, and it:

1. **Interviews you** to create a structured spec (`/spec create`)
2. **Decomposes** the spec into phases and tasks
3. **Spawns worker agents** via `claude -p` (backend, frontend, infrastructure) to execute each task
4. **Tracks progress** against requirements with resumable sessions
5. **Surfaces blockers** when human input is needed
6. **Verifies** frontend work visually with automated screenshots

## Quick Start

```bash
# 1. Clone the factory
git clone <this-repo> software-factory

# 2. Set up your project (new or existing)
mkdir my-project && cd my-project
git init

# 3. Run the onboarding wizard
python /path/to/software-factory/onboard.py

# 4. Open Claude Code and build
claude

# Inside Claude Code:
/spec create "describe what you want to build"
# ... answer a few questions ...
/orchestrate
# ... watch it build ...
/status
```

## Onboarding Questions

The setup wizard asks:

| Question | Purpose | Example |
|----------|---------|---------|
| Project name | Identity, UI references | "Invoice Tracker" |
| Description | Design context, CLAUDE.md | "Tool for freelancers to manage invoices" |
| Domain | Design vocabulary/colors | "finance, invoicing" |
| Design context | Brand aesthetic, visual feel | "Premium, minimal, dark" (or auto-generated) |
| Frontend framework | Which worker/skills to install | react, vue, static-html, none |
| Backend framework | Worker configuration | fastapi, express, django, none |
| Database | Project context | postgresql, sqlite, none |
| Deploy platform | Which deploy adapter | render, none |
| Dev server port/command | UI verification config | 5173, "npm run dev" |
| Testing policy | CLAUDE.md testing section | local, deploy-only |

## What Gets Installed

After onboarding, your project gets:

```
your-project/
├── CLAUDE.md                    # Generated project guidelines (with Design Context)
├── render.yaml                  # Render blueprint (if deploy platform is render)
├── .gitignore                   # Updated with session/
└── .claude/
    ├── settings.json            # Permissions for agents
    ├── factory-config.json      # Saved config (for re-onboarding)
    ├── agents/
    │   ├── backend-worker.md    # TDD backend agent
    │   ├── frontend-worker.md   # Design-aware UI agent
    │   └── infra-worker.md      # Deployment agent
    └── skills/
        ├── orchestrate/         # Main orchestrator (decompose → spawn → monitor)
        ├── spec/                # Spec creation and management
        ├── status/              # Session diagnostics
        ├── worker-protocol/     # Shared worker conventions
        ├── backend-test/        # Test-driven development flow
        ├── bold-design/         # Domain-specific UI design
        ├── verify-ui/           # Visual verification loop
        └── deploy/              # Platform-specific deployment
```

## Commands

| Command | Description |
|---------|-------------|
| `/spec create "goal"` | Interview → structured spec with requirements |
| `/spec update` | Modify the spec (triggers re-planning) |
| `/spec show` | View spec with completion tracking |
| `/orchestrate` | Execute the spec autonomously |
| `/status` | Progress summary |
| `/status detail` | Current phase task breakdown |
| `/status blockers` | Active blockers needing input |
| `/status requirements` | Requirement-to-task coverage map |

## Architecture

```
                    /spec create
                         │
                         ▼
                    ┌─────────┐
                    │  SPEC   │  Human-approved requirements
                    └────┬────┘
                         │
                    /orchestrate
                         │
                         ▼
                 ┌───────────────┐
                 │ ORCHESTRATOR  │  Decomposes into phases → tasks
                 └───────┬───────┘
                         │
              ┌──────────┼──────────┐
              ▼          ▼          ▼
        ┌──────────┐ ┌──────────┐ ┌──────────┐
        │ backend  │ │ frontend │ │  infra   │
        │ worker   │ │ worker   │ │ worker   │
        └──────────┘ └──────────┘ └──────────┘
              │          │          │
              ▼          ▼          ▼
          Tests +    Screenshots   Deploy +
          API code   + UI code     Infra config

              └──────────┼──────────┘
                         │
                    session/
                    (progress, blockers, decisions)
```

**Sequential execution:** Tasks run one at a time via `claude -p` (headless CLI). Each worker is an independent Claude Code session with its own context window. The orchestrator waits for each to complete before spawning the next. Workers can use the Agent tool to spawn their own subagents — unlike the previous subagent-based approach, nesting is now possible.

## Deploy Platforms

**V1 (current):**
- **Render** — Full adapter with CLI, API reference, blueprint schema, pricing docs, and starter `render.yaml` generation

**Future:**
- Vercel
- Fly.io

To add a new platform, create `factory/templates/skills/deploy/{platform}/SKILL.md.tpl` with the platform's CLI commands, API reference, and conventions.

## Re-onboarding

To update your project's configuration:

```bash
python /path/to/software-factory/onboard.py --reconfigure
```

This re-reads your saved config and lets you change settings.

## Human Intervention

The system runs autonomously but needs human input for:
- Deployment platform authentication (login before orchestrating)
- API keys and secrets for third-party services
- Ambiguous requirements (the worker asks, you decide)
- DNS setup for custom domains

See [docs/HUMAN-INTERVENTION-GUIDE.md](docs/HUMAN-INTERVENTION-GUIDE.md) for the complete list.
