# Decomposition Patterns

Phase-aware examples for different types of development goals.

## Pattern: Full-Stack Feature

Goal: "Add user registration with API and UI"

### Phases
```
phase-1: Data Layer (FR-1, FR-3)
    p1-task-1: User model + migration           → backend-worker
    p1-task-2: Database seed/fixtures            → backend-worker
    p1-task-3: Model unit tests                  → backend-worker

phase-2: API Layer (FR-1, FR-2, FR-3, NFR-1)
    (decomposed after phase-1 completes)

phase-3: Frontend (FR-1, FR-2, FR-3, NFR-2)
    (decomposed after phase-2 completes)

phase-4: Integration & Deploy (NFR-1, NFR-2)
    (decomposed after phase-3 completes)
```

Key: Frontend depends on API. API depends on models. Each phase decomposes just-in-time.

## Pattern: Frontend Only

Goal: "Redesign the dashboard with a fresh visual identity"

### Phases
```
phase-1: UI Redesign (FR-1, NFR-1)
    p1-task-1: Design exploration + implementation → frontend-worker
    p1-task-2: Responsive testing                  → frontend-worker (depends on p1-task-1)
```

Single phase. Bold-design exploration happens within the frontend worker.

## Pattern: Backend Only

Goal: "Add authentication with JWT tokens"

### Phases
```
phase-1: Auth Foundation (FR-1, FR-2)
    p1-task-1: User model + migration        → backend-worker
    p1-task-2: JWT utility (sign, verify)     → backend-worker
    p1-task-3: Auth tests                     → backend-worker (depends on p1-task-1, p1-task-2)

phase-2: Auth Endpoints (FR-3, FR-4)
    (decomposed after phase-1)

phase-3: Auth Middleware (FR-5, NFR-1)
    (decomposed after phase-2)
```

Note: p1-task-1 and p1-task-2 have no dependency on each other, but in sequential mode they still run one at a time.

## Pattern: Infrastructure

Goal: "Add a PostgreSQL database and deploy the backend API"

### Phases
```
phase-1: Infrastructure (NFR-1, NFR-2)
    p1-task-1: Create deployment blueprint    → infra-worker
    p1-task-2: Deploy and verify              → infra-worker (depends on p1-task-1)
```

## Pattern: Multi-Service

Goal: "Split into separate frontend and backend services"

### Phases
```
phase-1: Project Restructure (FR-1)
    p1-task-1: Create backend/ directory, move API code  → backend-worker
    p1-task-2: Create frontend/ directory, move UI code  → frontend-worker
    p1-task-3: Update imports and paths                  → backend-worker (depends on p1-task-1)

phase-2: Service Configuration (FR-2, NFR-1)
    (decomposed after phase-1 — needs to know final structure)

phase-3: Deployment (NFR-2)
    (decomposed after phase-2)
```

## Decomposition Rules

1. **File exclusivity within phase**: No two tasks share files. Merge if needed.
2. **Dependency minimization**: Keep chains shallow. Independent tasks have no `depends_on` (even though they execute sequentially, explicit dependencies document real data flow).
3. **Right-size tasks**: One worker, 5-30 minutes. Bigger → split. Smaller → merge.
4. **Test proximity**: Tests live with the code they test in the same task.
5. **Single concern**: One logical concern per task (one model, one endpoint set, one UI component).
6. **Setup tasks for shared files**: Use `p{n}-task-0-setup` for config files, env files, shared utilities that multiple tasks need.
