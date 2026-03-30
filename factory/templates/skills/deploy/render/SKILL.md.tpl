---
name: deploy
description: Manage all Render infrastructure — services, databases, Redis, cron jobs, deployments, logs, env vars, and IaC blueprints. Use when working with Render in any capacity (deploying, debugging, provisioning, monitoring).
allowed-tools: Bash, Read, Write, Edit
argument-hint: "[logs|deploy|status|create|blueprint|help]"
---

# Render Operations Guide

**CLI constraint:** Always use `-o json` or `-o text` — interactive mode doesn't work in this shell.

## Pre-Flight: Verify Workspace

Before ANY Render operation, verify you're in the correct workspace:
```bash
render workspace current -o json
```
If the workspace name doesn't match the project's expected workspace, raise a blocker. Do NOT proceed with operations in the wrong workspace — services could be created or modified in the wrong account.

## Known Services

| Service | ID | Type |
|---------|-----|------|
| (none provisioned yet) | — | — |

Update this table as new services are provisioned.

---

## Quick Reference: Everyday Commands

### Status & Logs
```bash
# All services in workspace
render services list -o json

# Logs for a service (last 100)
render logs -r <SERVICE_ID> -o text

# Error logs
render logs -r <SERVICE_ID> -o text --level error --limit 50

# Search logs by text
render logs -r <SERVICE_ID> -o text --text "Error,timeout"

# Time-windowed logs
render logs -r <SERVICE_ID> -o text --start "2026-03-28T00:00:00Z" --end "2026-03-28T12:00:00Z"

# Filter by HTTP status/method/path
render logs -r <SERVICE_ID> -o text --status-code 500,502 --method POST --path "/api"
```

### Deployments
```bash
render deploys list -o json -r <SERVICE_ID>           # List deploys
render deploys create -o json -r <SERVICE_ID> --confirm  # Trigger deploy
render deploys cancel -o json -r <SERVICE_ID>          # Cancel running deploy
```

### Service Management
```bash
render restart -o json -r <SERVICE_ID> --confirm       # Restart
render services instances -o json -r <SERVICE_ID>      # List instances
```

### Workspace
```bash
render workspace current -o json                       # Current workspace
render workspace list -o json                          # List workspaces
```

---

## IMPORTANT: Never Create Services via API

Services are created by the **human** via Render Dashboard → Blueprints → "New Blueprint Instance." This reads `render.yaml` and provisions all services in the correct workspace. The Render API does NOT support creating blueprint instances.

**You MUST NOT** use `POST /v1/services` or `POST /v1/postgres` to create services directly. This bypasses the blueprint, may target the wrong workspace, and creates unlinked services.

Your job is to **verify** services exist (created by the human via blueprint) and **use** them (deploy, logs, env vars, health checks). If services don't exist, raise a blocker asking the human to create the Blueprint Instance.

## When to Use the API Directly

The CLI doesn't cover everything. Use the Render API (`https://api.render.com/v1/`) with the stored API key for:
- Managing env vars and env groups
- Custom domains
- Scaling and autoscaling
- Metrics (CPU, memory, HTTP latency, etc.)
- Querying deploy status and logs

```bash
# Helper: extract API key from CLI config
RENDER_API_KEY=$(grep 'key:' ~/.render/cli.yaml | head -1 | awk '{print $2}')

# Example: list all services
curl -s -H "Authorization: Bearer $RENDER_API_KEY" https://api.render.com/v1/services

# Example: list env vars for a service
curl -s -H "Authorization: Bearer $RENDER_API_KEY" https://api.render.com/v1/services/<SERVICE_ID>/env-vars
```

For the full API reference, see [api-reference.md](api-reference.md).

---

## Infrastructure as Code: render.yaml

The project should use a `render.yaml` blueprint at the repo root. This declares all services, databases, env groups, and their configuration as code.

### When to use render.yaml
- Spinning up a new service (don't create manually in Dashboard)
- Adding a database or Redis instance
- Configuring env var groups shared across services
- Ensuring reproducible infrastructure

### Quick example
```yaml
services:
  - type: web
    name: {{PROJECT_SLUG}}
    runtime: node
    plan: starter
    region: oregon
    buildCommand: npm install
    startCommand: npm start
    healthCheckPath: /health
    envVars:
      - key: NODE_ENV
        value: production
      - fromGroup: shared-config

databases:
  - name: {{PROJECT_SLUG}}-db
    plan: starter
    region: oregon
    postgresMajorVersion: 16

envVarGroups:
  - name: shared-config
    envVars:
      - key: LOG_LEVEL
        value: info
```

For the full blueprint schema, service types, and advanced patterns, see [blueprint-reference.md](blueprint-reference.md).

---

## Service Types: Which to Use When

| Type | Blueprint `type` | Public URL | Traffic | Use case |
|------|------------------|------------|---------|----------|
| Web Service | `web` | Yes | HTTP from internet | API servers, web apps |
| Private Service | `pserv` | No | Internal only | Internal APIs, microservices |
| Background Worker | `worker` | No | None | Queue processing, async tasks |
| Cron Job | `cron` | No | None | Scheduled tasks (12hr max) |
| Static Site | `web` + `runtime: static` | Yes (CDN) | HTTP | SPAs, marketing sites |
| PostgreSQL | under `databases:` | No | Connection string | Relational database |
| Key Value | `keyvalue` | No | Connection string | Redis caching, sessions, queues |

---

## Post-Push Deploy Verification

After the human pushes code and Render auto-deploys, you MUST verify the deploy succeeded for EVERY service. Do not assume a push means a successful deploy.

### Verification sequence:
```bash
# 1. Check latest deploy status for each service
render deploys list -r <SERVICE_ID> -o json | head -20

# Look for: "status": "live" (success) or "status": "build_failed" / "update_failed" (failure)

# 2. If failed — pull build logs to diagnose
render logs -r <SERVICE_ID> -o text --type build --limit 50

# 3. If live — verify health endpoint
curl -s https://<service-url>/health
```

### If deploy failed:
1. Read the build logs to identify the error
2. Raise a blocker with the error details and build log output
3. Do NOT proceed to the next phase — a failed backend deploy means the frontend will hit stale or broken APIs

### Check ALL services, not just the one you deployed:
A push to the repo triggers auto-deploy on ALL services (both backend and frontend share the same repo). Verify each service's latest deploy status even if you only changed backend code — the frontend redeploy should also succeed.

---

## Debugging Playbooks

### "Site is down"
1. `render services list -o json` — check service status
2. `render deploys list -o json -r <ID>` — check if deploy failed
3. `render logs -r <ID> -o text --level error --limit 50` — find error

### "Deploy failed"
1. `render deploys list -o json -r <ID>` — find failed deploy ID
2. `render logs -r <ID> -o text --type build --limit 100` — build logs

### "App is slow"
1. `render logs -r <ID> -o text --limit 50` — check for obvious errors
2. Use API for metrics: `GET /v1/services/<ID>/metrics/http-latency`
3. Check instance count: `render services instances -o json -r <ID>`

---

## Detailed Reference (Supporting Files)

These files contain deep reference material — read them when you need specifics:

- [blueprint-reference.md](blueprint-reference.md) — Full render.yaml schema, all service fields, env var patterns, disks, scaling, preview environments, immutable fields
- [api-reference.md](api-reference.md) — All Render API endpoints organized by resource type
- [pricing-and-plans.md](pricing-and-plans.md) — Plan tiers, limits, free tier constraints, workspace tiers

$ARGUMENTS
