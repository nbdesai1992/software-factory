# Software Factory

A Claude Code orchestration toolkit that turns a product spec into working software.

## What This Is

This repository contains the generic orchestration system — skills, agents, and templates that can be installed into any project. It is NOT a project itself; it is tooling.

## Repository Structure

```
software-factory/
├── onboard.py              # Interactive setup script — entry point
├── factory/
│   ├── skills/             # Generic skills (copied as-is to target projects)
│   │   ├── orchestrate/    # Decompose specs → spawn workers → track progress
│   │   ├── worker-protocol/# Shared worker conventions
│   │   ├── backend-test/   # TDD flow for backend work
│   │   ├── bold-design/    # Domain-specific UI design (reads CLAUDE.md at runtime)
│   │   ├── spec/           # Spec creation and management
│   │   └── status/         # Session diagnostic
│   └── templates/          # Customizable templates (rendered with project config)
│       ├── CLAUDE.md.tpl
│       ├── settings.json.tpl
│       ├── agents/         # Worker agent definitions
│       └── skills/         # Skills that need project context
│           ├── verify-ui/  # Screenshot verification (needs server config)
│           └── deploy/     # Platform adapters (render, etc.)
└── docs/
    ├── HUMAN-INTERVENTION-GUIDE.md
    └── decisions.md        # Factory-level decision log
```

## How to Use

1. Clone this repo
2. From your target project directory: `python /path/to/software-factory/onboard.py`
3. Answer the questions
4. Open Claude Code in your project
5. `/spec create "what you want to build"`
6. `/orchestrate`

## Development Guidelines

- Generic skills should contain NO project-specific content
- Templates use `{{PLACEHOLDER}}` syntax (simple string replacement, no Jinja2)
- New deploy platform adapters go in `factory/templates/skills/deploy/{platform}/`
- The orchestrator spawns workers via `claude -p` headless CLI sessions (one at a time, sequential)
- Workers load skills via the `--agent` flag which reads agent definitions from `.claude/agents/`
