# Future Refactor Plan

This document tracks the planned migration of AskSharon's architecture from its current structure to a more standard layered architecture.

---

## Current Structure (v1)

```text
assistant/
  core/               # Business logic, shared utilities
  modules/            # Feature modules and integrations
    voice/
    email/
    calendar/
    planner/
    behavioural_intelligence/
  data/               # Database files
```

**Issues with current structure:**
- No clear separation between API layer and business logic
- Modules mix service/integration concerns with business rules
- UI code (Streamlit) sometimes directly imports modules
- No explicit API boundary for future REST/GraphQL clients

---

## Target Structure (v2)

```text
app/
  api/                # HTTP endpoints (FastAPI routers)
    routes/
      tasks.py
      calendar.py
      email.py
      goals.py
  core/               # Pure business logic, workflows, domain rules
    workflows/
    domain/
    utils/
  services/           # External integrations (Gmail, Calendar, OpenAI, etc.)
    gmail/
    google_calendar/
    openai_client/
  db/                 # Database models, sessions, migrations
    models/
    migrations/
    session.py

ui/
  streamlit/          # Streamlit UI (only calls app/api)
  web/                # (future) React/Next.js frontend

tests/
  unit/               # Unit tests for core logic
  integration/        # Integration tests for services/API
  e2e/                # End-to-end tests (existing)

tools/
  check_architecture.py
```

---

## Benefits of Target Structure

1. **Clear API boundary**: Future clients (mobile app, CLI, webhooks) can call `app/api` without touching internals
2. **Testable core**: Pure business logic in `app/core` with no external dependencies
3. **Reusable services**: `app/services` can be used by core, API, or background jobs
4. **UI decoupling**: UI only knows about API, not internal modules
5. **Standard pattern**: Matches industry-standard FastAPI/Django/Flask app structures

---

## Migration Strategy

### Phase 1: Non-Breaking Additions (Now → Q1 2026)

Add new structure alongside existing one:

1. Create `app/api/` folder with FastAPI routers
   - Start with read-only endpoints (GET /tasks, GET /goals)
   - Internally call existing `assistant/modules/*` code

2. Create `app/core/` for new business logic
   - Move pure functions from modules into core
   - Keep existing module code working

3. Update Streamlit UI to call new API endpoints
   - Gradual migration: one screen at a time
   - Old code continues to work

**Goal**: Prove the new structure works without breaking existing features.

### Phase 2: Service Extraction (Q2 2026)

Extract external integrations into `app/services/`:

1. Create `app/services/gmail/` from `assistant/modules/email/`
2. Create `app/services/google_calendar/` from `assistant/modules/calendar/`
3. Create `app/services/openai_client/` (centralize OpenAI calls)

**Goal**: Clear separation between "talking to external APIs" and "business logic".

### Phase 3: Database Layer (Q2-Q3 2026)

Consolidate database access:

1. Create `app/db/models/` with all SQLAlchemy models
2. Create `app/db/session.py` for session management
3. Add proper migrations with Alembic
4. Move existing DB code from modules

**Goal**: Single source of truth for data models and DB access.

### Phase 4: Remove Old Structure (Q3-Q4 2026)

Once all features migrated:

1. Delete `assistant/modules/` (code moved to `app/services/`)
2. Delete `assistant/core/` (code moved to `app/core/`)
3. Update all tests to use new structure
4. Update documentation

**Goal**: Clean codebase with no legacy cruft.

---

## Migration Checklist

### Prerequisites
- [ ] All existing features have tests (prevent regressions)
- [ ] Document current behavior (baseline for comparison)
- [ ] Get user approval for migration plan

### Phase 1 (Non-Breaking)
- [ ] Create `app/api/routes/tasks.py` (read-only)
- [ ] Create `app/api/routes/goals.py` (read-only)
- [ ] Create `app/api/routes/calendar.py` (read-only)
- [ ] Update one Streamlit screen to use new API
- [ ] Verify existing functionality still works
- [ ] Run all tests (must pass)

### Phase 2 (Service Extraction)
- [ ] Create `app/services/gmail/client.py`
- [ ] Create `app/services/google_calendar/client.py`
- [ ] Create `app/services/openai_client/client.py`
- [ ] Migrate calling code to use new services
- [ ] Add service-level tests

### Phase 3 (Database Layer)
- [ ] Create `app/db/models/` (Task, Goal, Appointment, etc.)
- [ ] Set up Alembic migrations
- [ ] Migrate all database access to use new models
- [ ] Run full test suite

### Phase 4 (Cleanup)
- [ ] Remove `assistant/modules/`
- [ ] Remove old `assistant/core/`
- [ ] Update all documentation
- [ ] Update `tools/check_architecture.py` rules
- [ ] Celebrate! 🎉

---

## Known Risks

1. **User disruption**: Migration could break existing workflows
   - Mitigation: Thorough testing, gradual rollout, keep old code working during transition

2. **Time investment**: Large refactor requires significant dev time
   - Mitigation: Phased approach, deliver value at each phase

3. **Behavioral changes**: New code might not exactly match old behavior
   - Mitigation: Comprehensive tests before migration, diff comparison

4. **Incomplete migration**: Ending up with mixed old/new structure
   - Mitigation: Clear checkpoints, document what's migrated vs. what's not

---

## Decision Log

| Date       | Decision | Rationale |
|------------|----------|-----------|
| 2025-11-21 | Adopt layered architecture (app/api/core/services/db) | Industry standard, better testability, clearer boundaries |
| 2025-11-21 | Phased migration (4 phases over ~1 year) | Minimize disruption, prove value incrementally |
| TBD        | Exact timing for each phase | Depends on feature development priorities |

---

## Questions / Open Issues

- **Q**: Should we migrate everything, or just new features?
  - **A**: TBD - might keep old structure for stable features, use new structure for new work

- **Q**: What if external APIs change during migration?
  - **A**: Services layer isolates these changes; update service, not whole codebase

- **Q**: How to handle data migrations?
  - **A**: Alembic migrations + careful testing with production data backup

---

**Status**: Planning
**Owner**: Engineering Team
**Next Review**: Q1 2026
**Last Updated**: 2025-11-21
