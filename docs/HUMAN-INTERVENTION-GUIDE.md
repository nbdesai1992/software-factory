# Human Intervention Guide

When the software factory is running autonomously via `/orchestrate`, there are specific moments where human intervention is required. This guide documents every known intervention point so you know what to expect.

## How Intervention Works

Workers raise **blockers** when they hit something they can't resolve. The orchestrator surfaces these to you with clear context and options. You respond, the orchestrator records your decision, and the worker resumes.

You can check for blockers at any time with `/status blockers`.

---

## Intervention Categories

### 1. Deployment Platform Authentication

**When:** First time the infra-worker tries to use the deployment CLI or API.

**Symptom:** Blocker with type `external-action`, message about authentication failure or missing credentials.

**What to do:**
- **Render:** Run `! render login` in the Claude Code prompt (the `!` prefix runs it interactively). This opens a browser for OAuth. After login, the CLI stores credentials at `~/.render/cli.yaml`.
- **Vercel:** Run `! vercel login`
- **Fly.io:** Run `! fly auth login`

**Prevention:** Log in to your deployment platform CLI before running `/orchestrate` for the first time.

#### Render Setup (do this once before your first `/orchestrate` with deployment tasks)

1. **Install:** `brew install render` (or `npm install -g @render/cli`)
2. **Authenticate:** Run `! render login` in Claude Code — opens a browser for OAuth
3. **Verify:** `render workspace current -o json` should show your workspace
4. **Select workspace** (if you have multiple): `render workspace set`
5. **Credentials stored at:** `~/.render/cli.yaml`

---

### 2. Database Provisioning

**When:** A task requires creating a database for the first time.

**Symptom:** Blocker about database creation failure, or needing connection strings.

**What to do:**
- If using Render: The infra-worker can usually provision via `render.yaml` blueprint. But if the free tier database already exists (30-day expiry), you may need to delete it first from the Render dashboard.
- If using external database: Provide the connection string when asked. The blocker will have an `Options` field suggesting where to set it (env var, .env file, etc.).

**Prevention:** If you know you'll need a database, provision it before orchestration and add the connection string to your environment.

---

### 3. Environment Variables and Secrets

**When:** A worker needs an API key, secret, or connection string that doesn't exist yet.

**Symptom:** Blocker with type `needs-human-decision` or `external-action`, listing the env vars needed.

**What to do:**
- Create the required accounts (Stripe, SendGrid, Auth0, etc.)
- Provide the keys/secrets when asked
- The worker will tell you exactly where to set them (platform env vars, `.env` file, etc.)

**Prevention:** If your spec involves third-party services, set up those accounts and have API keys ready before orchestrating.

---

### 4. Git and Repository Setup

**When:** The infra-worker needs to connect a deployment service to your git repo.

**Symptom:** Blocker about missing git remote, or deployment service can't find the repo.

**What to do:**
- Create the GitHub/GitLab repo if it doesn't exist
- Push your code to it
- Ensure the deployment platform has access (GitHub app installed, OAuth connected, etc.)

**Prevention:** Have your git repo set up and pushed before running infrastructure tasks.

---

### 5. DNS and Custom Domains

**When:** A deployment task includes setting up a custom domain.

**Symptom:** Blocker about DNS verification failure.

**What to do:**
- Go to your domain registrar
- Add the DNS records specified in the blocker (usually a CNAME or A record)
- Wait for propagation (can take minutes to hours)
- Tell the orchestrator to retry

**Prevention:** DNS is inherently manual and asynchronous. Plan for this to take time.

---

### 6. Unclear Requirements

**When:** A worker encounters ambiguity in the spec that prevents implementation.

**Symptom:** Blocker with type `unclear-requirement`, describing what's ambiguous.

**What to do:**
- Read the blocker carefully — it will describe the ambiguity and often suggest options
- Make a decision and respond
- The orchestrator records your decision in `session/decisions.md` for future reference

**Example:** "The spec says 'users can share content' but doesn't specify: (1) share via link, (2) share to specific users, or (3) both. Which approach?"

---

### 7. Architecture Decisions

**When:** A worker faces a significant technical choice that could go multiple ways.

**Symptom:** Blocker with type `needs-human-decision`, presenting options with trade-offs.

**What to do:**
- Review the options presented
- Consider the trade-offs (the worker usually lists pros/cons)
- Make a decision

**Example:** "Should the API use REST or GraphQL? REST is simpler and matches the current codebase. GraphQL would reduce over-fetching for the dashboard but adds complexity."

---

### 8. Worker Failures (Max Attempts Reached)

**When:** A worker has failed 3 times on the same task.

**Symptom:** The orchestrator surfaces the task as a blocker after max attempts, showing error details from each attempt.

**What to do:**
- Read the error details from the task's progress log
- Common causes:
  - **Test failures that need design change:** The acceptance criteria may be too strict or contradictory
  - **Missing dependency:** Something the worker needs doesn't exist yet
  - **Environment issue:** Missing package, wrong Node/Python version, etc.
- Either fix the root cause yourself and tell the orchestrator to retry, or adjust the spec with `/spec update`

---

### 9. Design Direction Approval

**When:** A frontend worker runs the bold-design pre-design exploration for the first time.

**Symptom:** Not a blocker — the worker writes `session/design-direction.md` and proceeds. But you may want to review it.

**What to do:**
- After the first frontend task completes, review `session/design-direction.md`
- If the design direction is wrong, use `/spec update` to add design constraints, then the orchestrator will re-plan

**This is optional.** The worker will proceed without your input. But early review prevents wasted iterations.

---

## Minimizing Interventions

To get the smoothest autonomous run:

1. **Before `/orchestrate`:**
   - Log in to your deployment platform CLI
   - Have your git repo set up and pushed
   - Have API keys ready for any third-party services in the spec
   - Provision databases if you know you'll need them

### Render Pre-Flight Checklist

- [ ] `render` CLI installed and `render workspace current -o json` works
- [ ] `render.yaml` exists in repo root (generated during onboarding)
- [ ] Git repo pushed to GitHub/GitLab (Render deploys from git)
- [ ] Workspace selected if you have multiple: `render workspace set`
- [ ] API keys and secrets ready to set as env vars after first deploy

2. **Write detailed specs:**
   - The more specific your acceptance criteria, the fewer `unclear-requirement` blockers
   - Explicitly state technology preferences in Technical Constraints
   - Put things in Out of Scope to prevent workers from over-engineering

3. **Stay available:**
   - Blockers pause execution until resolved
   - Check `/status blockers` periodically
   - Quick responses keep the pipeline moving

---

## Intervention Quick Reference

| Intervention | Type | Typical Resolution Time | Can Prevent? |
|-------------|------|------------------------|-------------|
| Platform auth | external-action | 2 minutes | Yes — login beforehand |
| Database provisioning | external-action | 5 minutes | Yes — provision beforehand |
| Env vars / secrets | needs-human-decision | 5-30 minutes | Partially — have keys ready |
| Git repo setup | external-action | 5 minutes | Yes — set up beforehand |
| DNS / domains | external-action | Minutes to hours | No — inherently async |
| Unclear requirements | unclear-requirement | 1-5 minutes | Yes — write detailed specs |
| Architecture decisions | needs-human-decision | 2-10 minutes | Partially — constrain in spec |
| Worker failures | max-attempts | 5-30 minutes | No — but rare |
| Design review | (optional) | 5 minutes | N/A — optional |
