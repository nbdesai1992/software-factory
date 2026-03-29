---
name: deploy
description: Manage all Render infrastructure — services, databases, Redis, cron jobs, deployments, logs, env vars, and IaC blueprints. Use when working with Render in any capacity (deploying, debugging, provisioning, monitoring).
allowed-tools: Bash, Read, Write, Edit
argument-hint: "[logs|deploy|status|create|blueprint|help]"
---

# Render Operations Guide

**CLI constraint:** Always use `-o json` or `-o text` — interactive mode doesn't work in this shell.

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

## When to Use the API Directly

The CLI doesn't cover everything. Use the Render API (`https://api.render.com/v1/`) with the stored API key for:
- Creating/deleting services, databases, Redis
- Managing env vars and env groups
- Custom domains
- Scaling and autoscaling
- Metrics (CPU, memory, HTTP latency, etc.)

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

## Debugging Playbooks

### "Site is down"
1. `render services list -o json` — check service status
2. `render deploys list -o json -r <ID>` — check if deploy failed
3. `render logs -r <ID> -o text --level error --limit 50` — find error

### "Deploy failed"
1. `render deploys list -o json -r <ID>` — find failed deploy ID
2. `render logs -r <ID> -o text --type deploy --limit 100` — build/deploy logs

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
