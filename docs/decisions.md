# Software Factory — Decision Log

Architectural and design decisions for the factory itself. Per-project decisions are tracked in each project's `session/decisions.md`.

## Resolved

| # | Decision | Resolution | Rationale |
|---|----------|-----------|-----------|
| 1 | Worker spawning mechanism | `claude -p` headless CLI (not Agent() tool) | Full Claude Code sessions; skills load properly via `--agent` flag; workers can nest subagents |
| 2 | Skill loading in workers | Preloaded via `--agent` flag (not embedded in prompt) | `claude -p --agent` loads agent definition + skills from `.claude/skills/`; embedding was a workaround for Agent() tool which didn't reliably load skills |
| 3 | bold-design: template vs generic skill | Generic (reads CLAUDE.md at runtime) | CLAUDE.md is single source of truth; skill never needs re-onboarding on context change |
| 4 | verify-ui: template vs generic | Template (bakes in port/slug/command) | Code examples in dev-browser scripts need concrete values |
| 5 | render.yaml generation | Programmatic in onboard.py | Conditional sections (backend? database? frontend?) need code logic, not string replacement |
| 6 | Design context | Onboarding question with auto-default from domain | Low friction (Enter for default), high value (populates CLAUDE.md's Design Context for bold-design) |
| 7 | V1 platform scope | Render only | Vercel/Fly.io adapter structure documented for future |
| 8 | Worker resource cap | `--max-budget-usd` per task (default $5) | Replaces `maxTurns` from agent frontmatter; more meaningful limit tied to actual cost |
| 9 | Completed task file movement | `mv` to `session/tasks/completed/` by orchestrator | At-a-glance status; clean separation of active vs done; workers always write to `session/tasks/` |
| 10 | Worker execution order | Sequential (one at a time) | Safer for autonomous execution; avoids file conflicts; simpler debugging |

## Open (V2 Candidates)

- **Vercel deploy adapter** — Needs SKILL.md.tpl with Vercel CLI commands and API reference
- **Fly.io deploy adapter** — Needs SKILL.md.tpl with flyctl commands
- **Render workspace name** — Currently implicit via `render workspace current`; could be an explicit onboarding question
- **Parallel worker execution** — Currently sequential; could speed up independent tasks within a phase
- **Authentication provider templates** — Clerk, Auth0, NextAuth patterns as optional skills
- **Worker budget per type** — Frontend workers may need higher budgets than backend (more iterations for visual work)
- **`--resume` for interrupted workers** — Currently always fresh spawn; resume could save cost for long tasks
- **Multi-service render.yaml** — Current generation is basic; could detect monorepo structure and generate more sophisticated blueprints
