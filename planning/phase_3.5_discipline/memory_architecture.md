# Phase 3.5 Memory Architecture

## Overview

This document defines data storage strategy for Phase 3.5: Proactive Discipline System, considering existing memory infrastructure.

**Guiding Principle:** SQLite for all operational data (fast, offline, privacy), Supabase for selective semantic search (cross-system intelligence).

---

## Existing Memory Systems

### 1. SQLite (`assistant/data/memory.db`)

**Current Usage:**
- Tasks, goals, behaviour metrics
- Local storage, fast queries (<10ms)
- Offline capability
- Privacy-first (no cloud sync by default)

**Characteristics:**
- File-based database
- ACID compliant
- ~5MB current size
- No remote access

**Existing Tables:**
```sql
tasks (id, title, urgency, importance, effort, completed, created_at)
goals (id, name, target_per_week, completed, last_update)
behaviour_metrics (id, date, domain, question, response, sentiment)
```

---

### 2. FAISS Vector Index (Local)

**Current Usage:**
- Fast local semantic search
- 128-dimensional embeddings
- In-memory index

**Characteristics:**
- Embedding model: sentence-transformers/all-MiniLM-L6-v2
- Index type: Flat (exhaustive search)
- Stored in: `assistant/data/faiss_index.bin`

**Use Case:** Quick recall of similar tasks/goals locally

---

### 3. Supabase PostgreSQL with pgvector

**Current Usage:**
- Cross-system memory (AskSharon ↔ ManagementTeam)
- 1536-dimensional OpenAI embeddings (text-embedding-ada-002)
- Row-Level Security (RLS) for data isolation

**Characteristics:**
- Cloud-hosted PostgreSQL
- Real-time subscriptions
- Requires internet connection
- Higher latency (~200-500ms) vs SQLite

**Current Tables:**
```sql
conversation_memory (
  id UUID PRIMARY KEY,
  system_id TEXT,  -- 'asksharon' or 'managementteam'
  user_id UUID,
  content TEXT,
  embedding VECTOR(1536),
  metadata JSONB,
  created_at TIMESTAMPTZ
)

shared_insights (
  id UUID PRIMARY KEY,
  insight_type TEXT,
  content TEXT,
  embedding VECTOR(1536),
  source_system TEXT,
  created_at TIMESTAMPTZ
)
```

**RLS Policies:**
```sql
-- Users only see their own data
CREATE POLICY isolation ON conversation_memory
  FOR SELECT USING (user_id = auth.uid());

-- Systems can share insights
CREATE POLICY cross_system_insights ON shared_insights
  FOR SELECT USING (true);
```

---

## Phase 3.5 Storage Strategy

### Decision Matrix

| Data Type | SQLite | FAISS | Supabase | Rationale |
|-----------|--------|-------|----------|-----------|
| **Daily reflections** | ✅ Primary | ❌ | 🔶 Weekly sync | Hot data, needs fast access |
| **Time blocks** | ✅ Primary | ❌ | ❌ | Operational, no semantic search needed |
| **Habit chains** | ✅ Primary | ❌ | ❌ | Local tracking, privacy |
| **If-Then plans** | ✅ Primary | ✅ Local | ❌ | Need fast recall for triggers |
| **Pomodoro sessions** | ✅ Primary | ❌ | ❌ | Operational logs |
| **Streaks** | ✅ Primary | ❌ | ❌ | Simple counters |
| **Thought logs (CBT)** | ✅ Primary | 🔶 | 🔶 Patterns | Raw logs local, patterns cloud |
| **Weekly reviews** | ✅ Primary | ❌ | ✅ Sync | Semantic search across weeks |
| **Eisenhower tasks** | ✅ Extend existing | ❌ | ❌ | Extend `tasks` table |

**Legend:**
- ✅ Primary storage
- 🔶 Selective sync (some records, not all)
- ❌ Not stored here

---

## New SQLite Schema

### Core Discipline Tables

```sql
-- Daily reflections (evening planning + morning fallback)
CREATE TABLE daily_reflections (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    date DATE UNIQUE NOT NULL,  -- Date for which this plan applies
    planning_date DATE,  -- When this was planned (usually day before for evening planning)

    -- Evening reflection (day before)
    what_went_well TEXT,
    what_got_in_way TEXT,
    one_thing_learned TEXT,

    -- Tomorrow's plan
    top_priorities TEXT,  -- JSON: ["Priority 1", "Priority 2", "Priority 3"]
    one_thing_great TEXT,  -- One thing to make tomorrow great

    -- Metadata
    evening_completed BOOLEAN DEFAULT 0,
    evening_completed_at TIMESTAMP,
    morning_fallback BOOLEAN DEFAULT 0,  -- 1 if plan created in morning instead
    completion_rate REAL,  -- % of priorities actually completed (calculated next day)

    -- Energy tracking (Tier 3)
    energy_am INTEGER CHECK(energy_am BETWEEN 1 AND 5),
    energy_pm INTEGER CHECK(energy_pm BETWEEN 1 AND 5),

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for fast queries
CREATE INDEX idx_daily_reflections_date ON daily_reflections(date);
CREATE INDEX idx_daily_reflections_evening_completed ON daily_reflections(evening_completed);
CREATE INDEX idx_daily_reflections_planning_date ON daily_reflections(planning_date);

-- Time blocks (links tasks to calendar slots)
CREATE TABLE time_blocks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    task_id INTEGER NOT NULL REFERENCES tasks(id) ON DELETE CASCADE,
    start_time TIMESTAMP NOT NULL,
    end_time TIMESTAMP NOT NULL,
    duration_minutes INTEGER NOT NULL,
    calendar_event_id TEXT,  -- Google Calendar event ID
    calendar_synced BOOLEAN DEFAULT 0,
    completed BOOLEAN DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    UNIQUE(task_id, start_time)  -- Prevent double-booking same task
);

CREATE INDEX idx_time_blocks_task ON time_blocks(task_id);
CREATE INDEX idx_time_blocks_start ON time_blocks(start_time);

-- Habit chains (habit stacking)
CREATE TABLE habit_chains (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    anchor_habit TEXT NOT NULL,  -- Existing habit (e.g., "Pour morning coffee")
    new_habit TEXT NOT NULL,  -- New habit to stack (e.g., "Review Top 3 priorities")
    sequence_order INTEGER DEFAULT 1,  -- Order in chain (for multi-step stacks)
    active BOOLEAN DEFAULT 1,
    success_count INTEGER DEFAULT 0,  -- Total completions
    last_completed DATE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_habit_chains_active ON habit_chains(active);

-- Habit completion log (daily tracking)
CREATE TABLE habit_completions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    habit_chain_id INTEGER NOT NULL REFERENCES habit_chains(id) ON DELETE CASCADE,
    completion_date DATE NOT NULL,
    completed BOOLEAN DEFAULT 1,
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    UNIQUE(habit_chain_id, completion_date)  -- One entry per day per habit
);

CREATE INDEX idx_habit_completions_date ON habit_completions(completion_date);

-- Implementation intentions (If-Then planning)
CREATE TABLE if_then_plans (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    trigger TEXT NOT NULL,  -- "If I feel overwhelmed by task size"
    action TEXT NOT NULL,  -- "Break into 3 micro-steps and do step 1"
    task_id INTEGER REFERENCES tasks(id) ON DELETE SET NULL,  -- Optional link to specific task
    active BOOLEAN DEFAULT 1,
    times_used INTEGER DEFAULT 0,
    last_used TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_if_then_active ON if_then_plans(active);
CREATE INDEX idx_if_then_task ON if_then_plans(task_id);

-- Pomodoro sessions
CREATE TABLE pomodoro_sessions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    task_id INTEGER REFERENCES tasks(id) ON DELETE SET NULL,
    duration_minutes INTEGER DEFAULT 25,
    started_at TIMESTAMP NOT NULL,
    ended_at TIMESTAMP,
    completed BOOLEAN DEFAULT 0,
    interruptions INTEGER DEFAULT 0,
    accomplishment_notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_pomodoro_task ON pomodoro_sessions(task_id);
CREATE INDEX idx_pomodoro_started ON pomodoro_sessions(started_at);

-- Streaks (any tracked activity)
CREATE TABLE streaks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    activity TEXT UNIQUE NOT NULL,  -- "Evening Planning", "Morning Coffee → Review", etc.
    current_streak INTEGER DEFAULT 0,
    longest_streak INTEGER DEFAULT 0,
    last_completed DATE,
    total_completions INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_streaks_activity ON streaks(activity);

-- CBT thought logs (thought challenging)
CREATE TABLE thought_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    task_id INTEGER REFERENCES tasks(id) ON DELETE SET NULL,
    situation TEXT NOT NULL,  -- What triggered procrastination
    automatic_thought TEXT NOT NULL,  -- "This is too hard, I'll fail"
    cognitive_distortion TEXT,  -- "All-or-nothing thinking"
    evidence_for TEXT,  -- Evidence supporting the thought
    evidence_against TEXT,  -- Evidence against the thought
    reframe TEXT,  -- Balanced reframe
    outcome TEXT,  -- What happened after reframing
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_thought_logs_task ON thought_logs(task_id);
CREATE INDEX idx_thought_logs_created ON thought_logs(created_at);
```

---

### Extended Existing Tables

```sql
-- Add Eisenhower quadrant to existing tasks table
ALTER TABLE tasks ADD COLUMN quadrant TEXT CHECK(quadrant IN ('I', 'II', 'III', 'IV'));
ALTER TABLE tasks ADD COLUMN source TEXT DEFAULT 'manual';  -- 'manual', 'brain_dump', 'email', etc.

CREATE INDEX idx_tasks_quadrant ON tasks(quadrant);

-- Add weekly review flag to daily_reflections
-- (Already in schema above, but noted here for clarity)
```

---

## Supabase Selective Sync

### What Gets Synced to Supabase

**1. Weekly Reflections (Semantic Search)**

```sql
-- Supabase table
CREATE TABLE weekly_reflections (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    system_id TEXT NOT NULL DEFAULT 'asksharon',
    user_id UUID NOT NULL,
    week TEXT NOT NULL,  -- ISO week: "2025-W46"
    insights TEXT NOT NULL,  -- AI-generated summary from 7 daily reflections
    top_blockers TEXT[],  -- ["Unexpected meetings", "Email overload"]
    best_day TEXT,
    task_completion_metrics JSONB,  -- {"Q1": 0.85, "Q2": 0.60, ...}
    embedding VECTOR(1536),  -- OpenAI embedding for semantic search
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- RLS policy
CREATE POLICY user_weekly_reflections ON weekly_reflections
    FOR SELECT USING (user_id = auth.uid());
```

**Sync Logic:**
```python
# assistant/core/supabase_memory.py

def sync_weekly_reflection(self, week: str, insights: Dict):
    """Sync weekly review to Supabase for semantic search."""

    # Generate embedding
    embedding = openai.embeddings.create(
        model="text-embedding-ada-002",
        input=insights['summary_text']
    ).data[0].embedding

    # Insert to Supabase
    self.supabase.table('weekly_reflections').insert({
        'system_id': 'asksharon',
        'user_id': self.user_id,
        'week': week,
        'insights': insights['summary_text'],
        'top_blockers': insights['blockers'],
        'best_day': insights['best_day'],
        'task_completion_metrics': insights['task_completion'],
        'embedding': embedding
    }).execute()
```

**Why Sync Weekly Reviews?**
- Enables: "What patterns have I noticed across the last 4 weeks?"
- Semantic search: Find similar weeks by challenges/insights
- Cross-system: ManagementTeam can reference user's discipline patterns

---

**2. CBT Thought Patterns (Semantic Search)**

```sql
-- Supabase table
CREATE TABLE thought_patterns (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    system_id TEXT NOT NULL DEFAULT 'asksharon',
    user_id UUID NOT NULL,
    trigger_category TEXT,  -- "overwhelm", "perfectionism", "time_pressure"
    common_distortion TEXT,  -- "all-or-nothing", "catastrophizing"
    successful_reframes TEXT[],  -- Array of reframes that worked
    embedding VECTOR(1536),
    created_at TIMESTAMPTZ DEFAULT NOW()
);
```

**Sync Logic:**
- Every 10 thought logs → Analyze patterns → Sync aggregated insights
- NOT individual thoughts (privacy), only patterns

**Why Sync Thought Patterns?**
- Enables: "What reframes have worked for me in the past?"
- Semantic search: Find similar situations and successful strategies
- Future: Coach mode can suggest personalized reframes based on history

---

### What Stays Local (SQLite Only)

**Privacy-Sensitive Data:**
- Daily reflections (raw text)
- Habit completion logs
- Pomodoro session details
- Individual thought logs

**Operational Data:**
- Time blocks
- Streaks (counters only)
- If-Then plans

**Rationale:** These are hot operational data with no semantic search need, and some contain sensitive reflections user may not want cloud-synced.

---

## Storage Estimates

### SQLite Growth Projection

**Daily Data per User:**
- Daily reflection: ~500 bytes (text fields)
- Time blocks: 3/day × 200 bytes = 600 bytes
- Habit completions: 3/day × 100 bytes = 300 bytes
- Pomodoro sessions: 4/day × 150 bytes = 600 bytes
- Thought logs: 0.5/day × 300 bytes = 150 bytes (not every day)

**Total per day: ~2.2 KB**

**Annual Growth:**
- 2.2 KB/day × 365 days = ~803 KB/year
- **Estimate: ~1 MB/year per user**

**5-year projection: 5 MB** (negligible, SQLite handles GB easily)

---

### Supabase Growth Projection

**Weekly Syncs per User:**
- Weekly reflection: 1/week × 1.5 KB (text + embedding) = 78 KB/year
- Thought patterns: 1/month × 1.5 KB = 18 KB/year

**Total per year: ~96 KB/year per user** (~600 KB over 5 years)

**Cost Impact:**
- Supabase free tier: 500 MB database
- 1000 users × 0.6 MB = 600 MB (within free tier after 5 years!)

---

## Data Flow Diagram

```
USER ACTION
    ↓
┌─────────────────────────────────────────────────────┐
│ STREAMLIT FRONTEND                                  │
│ - Evening planning form                             │
│ - Task entry                                        │
│ - Habit tracking checkboxes                         │
└─────────────────────────────────────────────────────┘
    ↓
┌─────────────────────────────────────────────────────┐
│ FASTAPI BACKEND                                     │
│ /discipline/evening-plan POST                       │
│ /discipline/time-block POST                         │
│ /discipline/habit-stack POST                        │
└─────────────────────────────────────────────────────┘
    ↓
┌──────────────────┬──────────────────┬───────────────┐
│ SQLITE (Local)   │ FAISS (Local)    │ SUPABASE      │
│ - Daily data     │ - If-Then quick  │ - Weekly      │
│ - Time blocks    │   recall         │   reviews     │
│ - Habits         │                  │ - Thought     │
│ - Pomodoros      │                  │   patterns    │
│ - Streaks        │                  │   (selective) │
│ - Thought logs   │                  │               │
└──────────────────┴──────────────────┴───────────────┘
    ↓                                       ↓
FAST QUERIES (<10ms)              SEMANTIC SEARCH (200ms)
    ↓                                       ↓
OFFLINE CAPABLE                    CROSS-SYSTEM INSIGHTS
```

---

## Migration Strategy

### Phase 1: Create New Tables (Week 1)

```bash
# Run migration
sqlite3 assistant/data/memory.db < migrations/phase_3.5_discipline.sql

# Verify tables
sqlite3 assistant/data/memory.db ".tables"
# Should show: daily_reflections, time_blocks, habit_chains, etc.
```

### Phase 2: Extend Existing Tables (Week 1)

```sql
-- Add columns to existing tasks table
ALTER TABLE tasks ADD COLUMN quadrant TEXT;
ALTER TABLE tasks ADD COLUMN source TEXT DEFAULT 'manual';
```

### Phase 3: Create Supabase Tables (Week 1)

```bash
# Run via Supabase SQL Editor
CREATE TABLE weekly_reflections (...);
CREATE TABLE thought_patterns (...);

# Apply RLS policies
ALTER TABLE weekly_reflections ENABLE ROW LEVEL SECURITY;
CREATE POLICY user_weekly_reflections ON weekly_reflections FOR SELECT USING (user_id = auth.uid());
```

### Phase 4: Implement Sync Logic (Week 3)

```python
# assistant/core/supabase_memory.py

def sync_weekly_reflection(week, insights):
    # Generate embedding → Insert to Supabase
    pass

def sync_thought_patterns(patterns):
    # Aggregate patterns → Sync to Supabase
    pass
```

---

## Backup Strategy

### SQLite Backups

**Automated Daily Backups:**
```bash
# Add to cron (1am daily)
0 1 * * * sqlite3 /path/to/memory.db ".backup /path/to/backups/memory_$(date +\%Y\%m\%d).db"
```

**Retention:**
- Daily: Keep 7 days
- Weekly: Keep 4 weeks
- Monthly: Keep 12 months

### Supabase Backups

**Handled by Supabase:**
- Point-in-time recovery: 7 days (free tier)
- Daily automated backups
- Export option: pgdump

---

## Performance Optimization

### SQLite Query Optimization

**Indexes Already Created:**
- `idx_daily_reflections_date` - Fast date lookups
- `idx_time_blocks_task` - Fast task → time block queries
- `idx_habit_completions_date` - Fast daily habit queries

**Expected Query Performance:**
- Daily reflection fetch: <5ms
- Time block suggestions: <20ms (calendar API is bottleneck)
- Habit completion check: <3ms

### Supabase Query Optimization

**Embedding Index (pgvector):**
```sql
-- Create HNSW index for fast vector search
CREATE INDEX weekly_reflections_embedding_idx
ON weekly_reflections
USING hnsw (embedding vector_cosine_ops);
```

**Expected Performance:**
- Semantic search (top 5 similar weeks): ~200ms

---

## Privacy & Security

### SQLite (Local)

**Security:**
- File permissions: 600 (user read/write only)
- No network exposure
- Encrypted at rest (OS-level)

**Privacy:**
- Data never leaves user's machine (except selective Supabase sync)
- No third-party access
- User owns data file

### Supabase (Cloud)

**Security:**
- Row-Level Security (RLS) - users only see own data
- TLS encryption in transit
- Encrypted at rest (PostgreSQL native)

**Privacy:**
- Only weekly summaries synced (not raw daily reflections)
- User can opt out of Supabase sync (config flag)
- GDPR-compliant data deletion

**Opt-Out Configuration:**
```yaml
# config/daily_rituals.yaml
supabase_sync:
  enabled: true  # Set to false to disable all cloud sync
  weekly_reflections: true
  thought_patterns: false  # User can disable just thought pattern sync
```

---

## Monitoring & Observability

### Metrics to Track

**SQLite:**
- Database size growth rate
- Query latency (p50, p95, p99)
- Write failures

**Supabase:**
- Sync success rate
- Sync latency
- Embedding generation cost

**Logging:**
```python
logger.info(f"✅ Daily reflection saved (date={date}, planning_type={'evening' if not morning_fallback else 'morning'})")
logger.info(f"✅ Supabase sync: weekly_reflection week={week} (cost=$0.02)")
logger.warning(f"⚠️ Supabase sync failed: {error} (will retry)")
```

---

## Rollback Plan

### Removing Phase 3.5 Tables

```sql
-- migrations/rollback_phase_3.5.sql
DROP TABLE IF EXISTS thought_logs;
DROP TABLE IF EXISTS pomodoro_sessions;
DROP TABLE IF EXISTS if_then_plans;
DROP TABLE IF EXISTS habit_completions;
DROP TABLE IF EXISTS habit_chains;
DROP TABLE IF EXISTS time_blocks;
DROP TABLE IF EXISTS daily_reflections;

-- Remove added columns from tasks
ALTER TABLE tasks DROP COLUMN quadrant;
ALTER TABLE tasks DROP COLUMN source;
```

**Supabase Cleanup:**
```sql
DROP TABLE IF EXISTS thought_patterns;
DROP TABLE IF EXISTS weekly_reflections;
```

---

## Future Enhancements (Out of Scope for Phase 3.5)

**Phase 4 Considerations:**
- **Multi-device sync:** Sync SQLite across user's devices via Supabase
- **Collaborative features:** Share habit chains with accountability partners
- **Analytics dashboard:** Aggregate anonymized patterns across users
- **Export portability:** One-click export to Notion, Roam, Obsidian

---

## Summary

**Storage Philosophy:**
- **SQLite:** Fast, offline, privacy-first operational data
- **Supabase:** Selective semantic search for insights
- **FAISS:** Local fast recall (unchanged)

**Growth Projections:**
- SQLite: ~1 MB/year per user (negligible)
- Supabase: ~100 KB/year per user (well within free tier)

**Privacy Guarantees:**
- Raw reflections stay local
- Only aggregated insights sync to cloud
- User can opt out of all cloud sync

**Performance:**
- SQLite queries: <10ms
- Supabase semantic search: ~200ms
- Offline capability preserved

**Next Steps:**
1. Create `migrations/phase_3.5_discipline.sql` (see database_migrations.sql)
2. Test migration on dev database
3. Implement sync logic in `assistant/core/supabase_memory.py`
4. Add configuration flags for opt-out
