# Phase 3.5 Implementation Tasks

## Week 1: Foundation Setup

### Database & Schema (3 days)

**Task 1.1: Create new database tables**
- [ ] Create `daily_reflections` table (evening/morning planning data)
- [ ] Create `time_blocks` table (calendar time blocking)
- [ ] Create `thought_logs` table (CBT thought challenging)
- [ ] Create migration script: `migrations/phase_3.5_discipline.sql`
- [ ] Test migration on dev database
- [ ] Verify schema with SQLite browser

**Acceptance:**
```bash
sqlite3 assistant/data/memory.db ".schema daily_reflections"
# Should show all columns: id, date, planning_date, top_priorities, etc.
```

**Task 1.2: Supabase selective sync setup**
- [ ] Create `weekly_reflections` table in Supabase
- [ ] Create `thought_patterns` table in Supabase (for CBT)
- [ ] Update `assistant/core/supabase_memory.py` with sync functions
- [ ] Test RLS policies (data isolation)
- [ ] Verify pgvector embeddings generation

**Acceptance:**
```python
from assistant.core.supabase_memory import sync_weekly_reflection
sync_weekly_reflection({"week": "2025-W46", "insights": "..."})
# Should appear in Supabase with user_id isolation
```

### Daily Rituals Backend (4 days)

**Task 1.3: Evening Planning API**
- [ ] Create `assistant/modules/discipline/rituals.py`
- [ ] Implement `/discipline/evening-plan` POST endpoint
- [ ] Fields: top_3_priorities, one_thing_great, reflection_today
- [ ] Store in `daily_reflections` table
- [ ] Return success + tomorrow's plan summary

**Acceptance:**
```bash
curl -X POST http://localhost:8000/discipline/evening-plan \
  -H "Content-Type: application/json" \
  -d '{"top_priorities": ["Task 1", "Task 2", "Task 3"], "one_thing_great": "Ship feature X"}'
# Should return 200 + plan_id
```

**Task 1.4: Morning Fallback API**
- [ ] Implement `/discipline/morning-fallback` POST endpoint
- [ ] Check if evening plan exists for today
- [ ] If exists: Return existing plan + reminder
- [ ] If missing: Trigger quick planning mode
- [ ] Mark as `morning_fallback=true` in database

**Acceptance:**
```bash
# If no evening plan exists:
curl -X POST http://localhost:8000/discipline/morning-fallback
# Should return {"fallback_needed": true, "quick_plan_url": "/discipline/quick-plan"}
```

**Task 1.5: Scheduled notification triggers**
- [ ] Create `assistant/modules/discipline/scheduler.py`
- [ ] Schedule evening planning (6pm default, configurable)
- [ ] Schedule morning fallback (8am default, if evening skipped)
- [ ] Use FastAPI BackgroundTasks for scheduling
- [ ] Add Streamlit notification integration

**Acceptance:**
```bash
# At 6pm:
# Should see: "🌙 Time to plan tomorrow! Reflect on today and set Top 3 priorities."

# At 8am (if no evening plan):
# Should see: "☀️ No evening plan found. Let's quickly plan your day!"
```

---

## Week 2: Tier 1 Features

### Eisenhower Matrix (2 days)

**Task 2.1: Task quadrant classification**
- [ ] Update `tasks` table schema: Add `quadrant` column (I, II, III, IV)
- [ ] Implement `/tasks/classify` POST endpoint
- [ ] Logic: urgency + importance → quadrant
- [ ] Auto-suggest: Q1 (do now), Q2 (schedule), Q3 (delegate), Q4 (delete)

**Acceptance:**
```python
# Task with urgency=5, importance=5 → Quadrant I (Urgent & Important)
# Task with urgency=2, importance=5 → Quadrant II (Not Urgent, Important)
```

**Task 2.2: Quadrant visualization in UI**
- [ ] Add Eisenhower Matrix view to Streamlit
- [ ] 2x2 grid: Urgent/Not Urgent × Important/Not Important
- [ ] Drag-and-drop between quadrants (if time permits, else buttons)
- [ ] Color-coded: Q1=Red, Q2=Green, Q3=Yellow, Q4=Gray

**Playwright Test:**
```python
def test_eisenhower_matrix_displays(page):
    page.goto("http://localhost:8501")
    page.get_by_text("Eisenhower Matrix").click()
    assert "Quadrant I" in page.content()
    assert "Quadrant II" in page.content()
```

### Time Blocking (3 days)

**Task 2.3: Time block creation**
- [ ] Create `time_blocks` table (task_id, start_time, duration, calendar_synced)
- [ ] Implement `/discipline/time-block` POST endpoint
- [ ] Input: task_id, preferred_time, duration
- [ ] Check calendar for conflicts (via existing calendar module)
- [ ] Reserve time block or suggest alternatives

**Acceptance:**
```bash
curl -X POST http://localhost:8000/discipline/time-block \
  -d '{"task_id": 123, "start_time": "2025-11-16T10:00:00", "duration_minutes": 60}'
# Should check calendar, create block, return confirmation
```

**Task 2.4: Calendar sync integration**
- [ ] Add Google Calendar event creation from time block
- [ ] Title: "🎯 [Task Name] (Time Block)"
- [ ] Description: Link to task, priority, notes
- [ ] Auto-delete if task completed early

**Acceptance:**
After creating time block, Google Calendar should show:
```
🎯 Write Phase 3.5 documentation (Time Block)
10:00 AM - 11:00 AM
Priority: Quadrant II
```

**Task 2.5: Time block suggestions**
- [ ] Analyze user's calendar for free slots
- [ ] Match task duration to available slots
- [ ] Prefer morning slots for Q1/Q2 tasks (high energy)
- [ ] Suggest batch processing for Q3 tasks

**Acceptance:**
```bash
curl -X GET http://localhost:8000/discipline/suggest-time-blocks?date=2025-11-16
# Should return: [{"task_id": 123, "suggested_time": "09:00", "reason": "Morning energy for Q2"}]
```

### Daily Reflection Prompts (2 days)

**Task 2.6: Evening reflection UI**
- [ ] Add evening planning form to Streamlit
- [ ] Fields:
  - What went well today? (text)
  - What got in the way? (text)
  - Top 3 priorities for tomorrow (list)
  - One thing to make tomorrow great (text)
- [ ] Submit → Store in `daily_reflections`

**Playwright Test:**
```python
def test_evening_reflection_form(page):
    page.goto("http://localhost:8501")
    page.get_by_text("Evening Planning").click()
    page.fill("textarea[aria-label='What went well today?']", "Shipped feature X")
    page.get_by_role("button", name="Plan Tomorrow").click()
    assert "Plan saved!" in page.content()
```

**Task 2.7: Morning plan display**
- [ ] Fetch yesterday's evening plan from database
- [ ] Display Top 3 priorities prominently
- [ ] Show time blocks for each priority
- [ ] Checkbox to mark as "Day Started"

---

## Week 3: Tier 2 - Behavioral Psychology

### Habit Stacking (2 days)

**Task 3.1: Habit chain builder**
- [ ] Create `habit_chains` table (anchor_habit, new_habit, sequence_order)
- [ ] Implement `/discipline/habit-stack` POST endpoint
- [ ] Pattern: "After [anchor habit], I will [new habit]"
- [ ] Track success count for each chain

**Acceptance:**
```json
POST /discipline/habit-stack
{
  "anchor_habit": "Morning coffee",
  "new_habit": "Review Top 3 priorities",
  "sequence_order": 1
}
// Should create chain and return tracking ID
```

**Task 3.2: Habit tracking UI**
- [ ] Display active habit chains in sidebar
- [ ] Checkbox: Did you complete the chain today?
- [ ] Visual indicator: ✅ = done, ⏳ = pending, ❌ = missed
- [ ] Celebrate 3-day, 7-day, 21-day milestones

### Implementation Intentions (If-Then Planning) (2 days)

**Task 3.3: If-Then plan creator**
- [ ] Create `if_then_plans` table (trigger, action, active)
- [ ] Implement `/discipline/if-then` POST endpoint
- [ ] Pattern: "If [situation], then I will [specific action]"
- [ ] Examples:
  - "If I feel procrastination, then I will work for just 2 minutes"
  - "If meeting ends early, then I will tackle top priority task"

**Acceptance:**
```json
POST /discipline/if-then
{
  "trigger": "I feel overwhelmed by task size",
  "action": "Break it into 3 micro-steps and do step 1",
  "active": true
}
```

**Task 3.4: If-Then reminders**
- [ ] Detect procrastination patterns (task delayed 3+ times)
- [ ] Surface relevant If-Then plans as reminders
- [ ] "You planned: If [trigger], then [action]. Want to apply this now?"

### GTD Cognitive Offloading (1 day)

**Task 3.5: Brain dump endpoint**
- [ ] Implement `/discipline/brain-dump` POST endpoint
- [ ] Accept freeform text of all thoughts/tasks
- [ ] Use OpenAI to parse into actionable tasks
- [ ] Auto-classify by Eisenhower quadrant
- [ ] Store in tasks table with `source=brain_dump`

**Acceptance:**
```bash
curl -X POST http://localhost:8000/discipline/brain-dump \
  -d '{"thoughts": "Need to email client, buy groceries, review budget, learn Python async"}'
# Should return parsed tasks:
# [
#   {"title": "Email client", "quadrant": "I", "urgency": 5},
#   {"title": "Buy groceries", "quadrant": "III", "urgency": 3},
#   ...
# ]
```

### Weekly Review Automation (2 days)

**Task 3.6: Weekly metrics aggregation**
- [ ] Create `/discipline/weekly-review` GET endpoint
- [ ] Query last 7 days of `daily_reflections`
- [ ] Calculate:
  - Evening planning completion rate
  - Task completion rate by quadrant
  - Top 3 recurring "what got in the way" themes
  - Most productive day of week
- [ ] Return summary with insights

**Acceptance:**
```bash
curl -X GET http://localhost:8000/discipline/weekly-review
# Should return:
# {
#   "week": "2025-W46",
#   "evening_plan_rate": 0.71,  // 5/7 days
#   "task_completion": {"Q1": 0.85, "Q2": 0.60, ...},
#   "blockers": ["Unexpected meetings", "Email overload", "Low energy PM"],
#   "best_day": "Tuesday"
# }
```

**Task 3.7: Sync to Supabase for semantic search**
- [ ] Weekly review triggers Supabase sync
- [ ] Store summary + insights in `weekly_reflections` table
- [ ] Generate embeddings for "blockers" and "lessons learned"
- [ ] Enable cross-system pattern detection (future: AskSharon + ManagementTeam)

---

## Week 4: Tier 3 - Advanced Accountability

### Pomodoro Timer (2 days)

**Task 4.1: Pomodoro session tracking**
- [ ] Create `pomodoro_sessions` table (task_id, duration, completed, started_at, ended_at)
- [ ] Implement `/discipline/pomodoro/start` POST endpoint
- [ ] Implement `/discipline/pomodoro/complete` POST endpoint
- [ ] Track interruptions and reasons

**Acceptance:**
```bash
curl -X POST http://localhost:8000/discipline/pomodoro/start \
  -d '{"task_id": 123, "duration_minutes": 25}'
# Returns: {"session_id": 456, "end_time": "2025-11-16T10:25:00"}

# After 25 minutes:
curl -X POST http://localhost:8000/discipline/pomodoro/complete \
  -d '{"session_id": 456, "completed": true}'
# Updates database, increments task progress
```

**Task 4.2: Pomodoro UI with timer**
- [ ] Add Streamlit timer widget
- [ ] Visual countdown: 25:00 → 00:00
- [ ] Sound notification when complete (browser beep)
- [ ] Quick log: "What did you accomplish?"

**Playwright Test:**
```python
def test_pomodoro_timer_starts(page):
    page.goto("http://localhost:8501")
    page.get_by_text("Start Pomodoro").click()
    page.wait_for_selector("text=24:5", timeout=2000)  # Timer counts down
    assert "Pomodoro running" in page.content()
```

### Streak Tracking (2 days)

**Task 4.3: Streak calculation logic**
- [ ] Create `streaks` table (activity, current_streak, longest_streak, last_completed)
- [ ] Implement `/discipline/streaks` GET endpoint
- [ ] Track streaks for:
  - Evening planning completion
  - Habit chain completion
  - Task completion rate >70%
  - Weekly review completion

**Acceptance:**
```bash
curl -X GET http://localhost:8000/discipline/streaks
# Should return:
# [
#   {"activity": "Evening Planning", "current": 5, "longest": 12, "at_risk": false},
#   {"activity": "Morning Coffee → Review", "current": 3, "longest": 7, "at_risk": false},
#   ...
# ]
```

**Task 4.4: Streak recovery logic**
- [ ] If streak broken, offer "recovery mode"
- [ ] User can activate: "I'm back on track" after 1 completion
- [ ] Reset `current_streak=1` but preserve `longest_streak`
- [ ] Notification: "Don't break the chain! You're at 5 days for [activity]"

### CBT Thought Challenging (2 days)

**Task 4.5: Procrastination thought log**
- [ ] Create `thought_logs` table (task_id, thought, distortion, reframe, created_at)
- [ ] Implement `/discipline/thought-challenge` POST endpoint
- [ ] Pattern:
  - Thought: "This is too hard, I'll fail"
  - Distortion: All-or-nothing thinking
  - Reframe: "I can start with one small step"

**Acceptance:**
```json
POST /discipline/thought-challenge
{
  "task_id": 123,
  "thought": "I don't have time for this",
  "distortion": "Fortune-telling",
  "reframe": "I have 10 minutes right now to make progress"
}
```

**Task 4.6: AI-assisted reframing**
- [ ] Integrate OpenAI to detect cognitive distortions
- [ ] Suggest evidence-based reframes
- [ ] Learn from user's past successful reframes
- [ ] Surface during task procrastination (delayed 2+ times)

**Acceptance:**
User enters: "I'm not good enough to do this"
AI suggests:
- Distortion: Labeling
- Reframe: "I'm learning. This is a skill I'm developing."
- Evidence: "You completed similar task last week"

### Energy-Based Scheduling (1 day)

**Task 4.7: Energy tracking**
- [ ] Add energy level to `daily_reflections` (1-5 scale for AM/PM)
- [ ] Analyze patterns: Best energy times for deep work
- [ ] Auto-suggest time blocks based on energy patterns
- [ ] Example: "You're most productive 9-11am. Block Q2 tasks then."

**Acceptance:**
After 2 weeks of tracking:
```bash
curl -X GET http://localhost:8000/discipline/energy-patterns
# Should return: {"peak_hours": ["09:00", "10:00", "11:00"], "low_hours": ["14:00", "15:00"]}
```

---

## Integration & Testing (Ongoing)

### Playwright E2E Tests (All Weeks)

**Task T.1: Evening planning flow test**
```python
def test_evening_planning_full_flow(page):
    # Navigate to evening planning
    page.goto("http://localhost:8501")
    page.get_by_text("Evening Planning").click()

    # Fill reflection
    page.fill("textarea[aria-label='What went well?']", "Completed 3 tasks")
    page.fill("textarea[aria-label='What got in way?']", "Unexpected meeting")

    # Set tomorrow's Top 3
    page.fill("input[aria-label='Priority 1']", "Finish documentation")
    page.fill("input[aria-label='Priority 2']", "Review PRs")
    page.fill("input[aria-label='Priority 3']", "Team sync")

    # Submit
    page.get_by_role("button", name="Plan Tomorrow").click()

    # Verify success
    assert "Tomorrow's plan saved!" in page.content()
    assert "Finish documentation" in page.content()
```

**Task T.2: Habit stack tracking test**
**Task T.3: Pomodoro timer test**
**Task T.4: Eisenhower matrix interaction test**
**Task T.5: Weekly review generation test**

**Acceptance:** All Playwright tests pass with screenshots
```bash
pytest tests/test_discipline_e2e.py -c pytest_e2e.ini -v
# Should show: 15 passed
```

### Backend Unit Tests (All Weeks)

**Task T.6: Database migration tests**
**Task T.7: API endpoint tests (pytest)**
**Task T.8: Scheduler timing tests**
**Task T.9: Supabase sync tests**

**Acceptance:**
```bash
pytest tests/test_discipline_backend.py -v
# Should show: 25+ passed
```

---

## Deployment Checklist

### Pre-Deployment

- [ ] All Playwright tests pass
- [ ] All pytest tests pass
- [ ] Black formatting applied
- [ ] Mypy type checks pass
- [ ] Database migrations tested on staging
- [ ] Supabase RLS policies verified
- [ ] Notification timing tested (6pm/8am triggers)
- [ ] Configuration documented in `config/daily_rituals.yaml.example`
- [ ] User guides complete in `docs/`
- [ ] DECISIONS.md updated

### Deployment

- [ ] Run migration: `sqlite3 assistant/data/memory.db < migrations/phase_3.5_discipline.sql`
- [ ] Verify tables created: `sqlite3 assistant/data/memory.db ".tables"`
- [ ] Restart backend: `uvicorn assistant.core.orchestrator:app --reload`
- [ ] Restart frontend: `streamlit run assistant/modules/voice/main.py`
- [ ] Test evening planning trigger (manually set time to 6pm for test)
- [ ] Verify Google Calendar sync
- [ ] User acceptance test: Complete one full evening → morning cycle

### Post-Deployment

- [ ] Monitor logs for errors: `tail -f logs/backend.log`
- [ ] Track user engagement metrics (evening plan completion rate)
- [ ] Gather user feedback after 1 week
- [ ] Iterate on notification timing if needed
- [ ] Document lessons learned in DECISIONS.md

---

## Estimated Effort

**Week 1:** 7 days (setup + evening/morning rituals)
**Week 2:** 7 days (Tier 1: Eisenhower, time blocking, reflection)
**Week 3:** 7 days (Tier 2: Habits, If-Then, GTD, weekly review)
**Week 4:** 7 days (Tier 3: Pomodoro, streaks, CBT, energy)

**Total:** ~28 days (4 weeks)

---

## Success Criteria

Phase 3.5 is **COMPLETE** when:

✅ User receives evening planning prompt at 6pm (configurable)
✅ Morning fallback activates if evening skipped
✅ Eisenhower Matrix categorizes all tasks
✅ Time blocks sync to Google Calendar
✅ Habit chains track for 21 days minimum
✅ Weekly review generates automatically
✅ Pomodoro timer integrates with task tracking
✅ Streak tracking shows current + longest streaks
✅ CBT thought challenging available during procrastination
✅ Energy-based scheduling suggests optimal work times
✅ All Playwright E2E tests pass (15+ tests)
✅ Backend pytest tests pass (25+ tests)
✅ User documentation complete (4 guides)
✅ Evening planning completion rate >70% after 2 weeks
