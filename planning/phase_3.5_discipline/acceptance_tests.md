# Phase 3.5 Acceptance Tests

## Overview

This document defines acceptance criteria for Phase 3.5: Proactive Discipline System. All tests must pass before declaring the phase complete.

---

## Tier 1: Foundation Rituals

### AT-1.1: Evening Planning Trigger

**Given:** Current time is 6:00 PM (configurable)
**When:** Scheduler checks for evening planning completion
**Then:**
- User receives notification: "🌙 Time to plan tomorrow! Reflect on today and set Top 3 priorities."
- Notification appears in Streamlit UI
- Notification logged to `logs/frontend.log`
- No notification sent if evening plan already completed for today

**Test Command:**
```bash
# Manually set time to 6pm for testing
pytest tests/test_discipline_scheduler.py::test_evening_planning_trigger -v
```

**Screenshot:**
- `tests/screenshots/evening_planning_notification.png` should show notification banner

---

### AT-1.2: Evening Planning Form Submission

**Given:** User clicks evening planning notification
**When:** User fills form:
- What went well: "Completed 3 tasks, shipped feature X"
- What got in way: "Unexpected meeting, email overload"
- Top 3 priorities: ["Finish docs", "Review PRs", "Team sync"]
- One thing great: "Early morning deep work block"

**Then:**
- Form submits successfully (200 OK)
- Data stored in `daily_reflections` table:
  ```sql
  SELECT * FROM daily_reflections WHERE date = '2025-11-16';
  -- Should return row with all fields populated
  -- evening_completed = 1, evening_completed_at = [timestamp]
  ```
- Success message: "✅ Tomorrow's plan saved! See you in the morning."
- Top 3 priorities displayed in Streamlit sidebar

**Playwright Test:**
```python
def test_evening_planning_form_submission(page):
    page.goto("http://localhost:8501")
    page.get_by_text("Evening Planning").click()

    page.fill("textarea[aria-label='What went well today?']", "Completed 3 tasks")
    page.fill("textarea[aria-label='What got in the way?']", "Unexpected meeting")
    page.fill("input[aria-label='Priority 1']", "Finish docs")
    page.fill("input[aria-label='Priority 2']", "Review PRs")
    page.fill("input[aria-label='Priority 3']", "Team sync")
    page.fill("input[aria-label='One thing to make tomorrow great']", "Early deep work")

    page.screenshot(path="tests/screenshots/before_evening_plan_submit.png")
    page.get_by_role("button", name="Plan Tomorrow").click()
    time.sleep(2)
    page.screenshot(path="tests/screenshots/after_evening_plan_submit.png")

    assert "Tomorrow's plan saved!" in page.content()
    assert "Finish docs" in page.content()
```

---

### AT-1.3: Morning Fallback - Plan Exists

**Given:** User completed evening planning yesterday (6pm)
**When:** Current time is 8:00 AM
**Then:**
- System checks `daily_reflections` for today's plan
- Plan found → Display existing plan:
  ```
  ☀️ Good morning! Here's your plan for today:

  Top 3 Priorities:
  1. Finish docs
  2. Review PRs
  3. Team sync

  One thing to make today great: Early deep work block

  [Start Day] button
  ```
- No new planning required
- `morning_fallback = 0` (not a fallback, plan already exists)

**Playwright Test:**
```python
def test_morning_shows_existing_plan(page):
    # Prerequisites: Evening plan completed yesterday
    page.goto("http://localhost:8501")
    time.sleep(3)  # Wait for morning check

    assert "Good morning! Here's your plan" in page.content()
    assert "Finish docs" in page.content()
    assert "Review PRs" in page.content()
    assert "Start Day" in page.content()
```

---

### AT-1.4: Morning Fallback - No Plan

**Given:** User DID NOT complete evening planning yesterday
**When:** Current time is 8:00 AM
**Then:**
- System checks `daily_reflections` for today's plan
- Plan NOT found → Trigger quick planning mode:
  ```
  ☀️ No evening plan found. Let's quickly plan your day!

  [Quick Plan] button (cannot dismiss, must plan)
  ```
- User clicks "Quick Plan" → Simplified form:
  - Top 3 priorities for today (required)
  - Optional: One thing to make today great
- Form submission:
  - Stores in `daily_reflections`
  - Sets `morning_fallback = 1`
  - Sets `planning_date = today` (not yesterday)

**Playwright Test:**
```python
def test_morning_fallback_quick_plan(page):
    # Prerequisites: No evening plan for today
    page.goto("http://localhost:8501")
    time.sleep(3)

    assert "No evening plan found" in page.content()
    assert "Quick Plan" in page.content()

    page.get_by_role("button", name="Quick Plan").click()
    page.fill("input[aria-label='Priority 1']", "Urgent task")
    page.fill("input[aria-label='Priority 2']", "Important meeting")
    page.fill("input[aria-label='Priority 3']", "Code review")
    page.get_by_role("button", name="Start Day").click()

    assert "Day plan saved!" in page.content()
```

**Database Verification:**
```sql
SELECT * FROM daily_reflections WHERE morning_fallback = 1 AND date = '2025-11-16';
-- Should return row with morning_fallback=1
```

---

### AT-1.5: Eisenhower Matrix Classification

**Given:** User adds new task: "Review budget report"
**When:** User sets:
- Urgency: 3/5
- Importance: 5/5

**Then:**
- Task auto-classified to **Quadrant II** (Not Urgent, Important)
- Suggested action: "Schedule for deep work block"
- Task appears in Eisenhower Matrix UI under Quadrant II
- Color: Green (Q2 = strategic, schedule)

**Playwright Test:**
```python
def test_eisenhower_matrix_classification(page):
    page.goto("http://localhost:8501")
    page.get_by_text("Add Task").click()

    page.fill("input[aria-label='Task title']", "Review budget report")
    page.select_option("select[aria-label='Urgency']", "3")
    page.select_option("select[aria-label='Importance']", "5")
    page.get_by_role("button", name="Add").click()

    page.get_by_text("Eisenhower Matrix").click()
    assert "Quadrant II" in page.content()
    assert "Review budget report" in page.content()
```

**Backend Test:**
```python
def test_task_quadrant_logic():
    from assistant.modules.discipline.eisenhower import classify_task

    result = classify_task(urgency=3, importance=5)
    assert result == "II"  # Not Urgent, Important

    result = classify_task(urgency=5, importance=5)
    assert result == "I"  # Urgent, Important
```

---

### AT-1.6: Time Blocking with Calendar Sync

**Given:** User has task "Write Phase 3.5 docs" (Quadrant II, 90 min duration)
**When:** User clicks "Block Time" for this task
**Then:**
- System checks Google Calendar for free slots
- Suggests: "🕐 9:00 AM - 10:30 AM (Morning energy optimal for Q2 tasks)"
- User accepts suggestion
- Time block created in `time_blocks` table
- Google Calendar event created:
  ```
  Title: 🎯 Write Phase 3.5 docs (Time Block)
  Start: 2025-11-16 09:00
  End: 2025-11-16 10:30
  Description: Priority: Quadrant II | Effort: High
  ```

**Playwright Test:**
```python
def test_time_block_calendar_sync(page):
    page.goto("http://localhost:8501")
    page.get_by_text("My Tasks").click()

    # Find task and click "Block Time"
    page.locator("text=Write Phase 3.5 docs").click()
    page.get_by_role("button", name="Block Time").click()

    # Accept suggested time
    page.get_by_text("9:00 AM - 10:30 AM").click()
    page.get_by_role("button", name="Confirm").click()

    assert "Time blocked!" in page.content()
    assert "Added to Google Calendar" in page.content()
```

**API Test:**
```bash
curl -X POST http://localhost:8000/discipline/time-block \
  -H "Content-Type: application/json" \
  -d '{
    "task_id": 123,
    "start_time": "2025-11-16T09:00:00",
    "duration_minutes": 90
  }'

# Response:
# {
#   "success": true,
#   "block_id": 456,
#   "calendar_event_id": "abc123xyz",
#   "message": "Time block created and synced to Google Calendar"
# }
```

**Google Calendar Verification:**
```bash
# Check calendar via API
curl -X GET http://localhost:8000/calendar/events?date=2025-11-16

# Should include:
# {
#   "summary": "🎯 Write Phase 3.5 docs (Time Block)",
#   "start": {"dateTime": "2025-11-16T09:00:00Z"},
#   "end": {"dateTime": "2025-11-16T10:30:00Z"}
# }
```

---

## Tier 2: Behavioral Psychology

### AT-2.1: Habit Stacking Creation

**Given:** User wants to build habit: "Review Top 3 priorities every morning"
**When:** User creates habit stack:
- Anchor habit: "Pour morning coffee"
- New habit: "Review Top 3 priorities"
- Sequence: 1

**Then:**
- Habit chain stored in `habit_chains` table
- Pattern displayed: "After I pour morning coffee, I will review Top 3 priorities"
- Daily checkbox appears in Streamlit sidebar
- Success count initialized to 0

**Playwright Test:**
```python
def test_habit_stack_creation(page):
    page.goto("http://localhost:8501")
    page.get_by_text("Habit Stacking").click()

    page.fill("input[aria-label='Anchor habit']", "Pour morning coffee")
    page.fill("input[aria-label='New habit']", "Review Top 3 priorities")
    page.get_by_role("button", name="Create Stack").click()

    assert "Habit stack created!" in page.content()
    assert "After I pour morning coffee" in page.content()
```

**Database Verification:**
```sql
SELECT * FROM habit_chains WHERE anchor_habit = 'Pour morning coffee';
-- Should return:
-- | anchor_habit        | new_habit               | sequence_order | active | success_count |
-- | Pour morning coffee | Review Top 3 priorities | 1              | 1      | 0             |
```

---

### AT-2.2: Habit Chain Completion Tracking

**Given:** Habit chain exists: "After morning coffee → Review Top 3 priorities"
**When:** User checks "Completed today" checkbox
**Then:**
- `success_count` incremented in database
- Visual feedback: ✅ checkmark animation
- Milestone celebration at 3, 7, 21 days:
  ```
  🎉 3-day streak! You're building momentum.
  🔥 7-day streak! This is becoming a habit.
  ⭐ 21-day streak! Habit formed! (Research: 21 days = habit automation)
  ```

**Playwright Test:**
```python
def test_habit_chain_completion(page):
    page.goto("http://localhost:8501")
    page.get_by_text("Habit Stacking").click()

    checkbox = page.locator("input[aria-label='Pour morning coffee → Review Top 3']")
    checkbox.check()

    time.sleep(1)
    assert "✅" in page.content()
```

**Backend Test:**
```python
def test_habit_milestone_detection():
    from assistant.modules.discipline.habits import check_milestone

    assert check_milestone(success_count=3) == "🎉 3-day streak! You're building momentum."
    assert check_milestone(success_count=7) == "🔥 7-day streak! This is becoming a habit."
    assert check_milestone(success_count=21) == "⭐ 21-day streak! Habit formed!"
```

---

### AT-2.3: Implementation Intentions (If-Then)

**Given:** User struggles with procrastination on large tasks
**When:** User creates If-Then plan:
- Trigger: "I feel overwhelmed by task size"
- Action: "Break into 3 micro-steps and do step 1"

**Then:**
- Plan stored in `if_then_plans` table with `active=1`
- Plan displayed when user delays task 2+ times:
  ```
  💡 You planned: If "I feel overwhelmed by task size", then "Break into 3 micro-steps and do step 1"

  Want to apply this now? [Yes] [Not now]
  ```
- If user clicks "Yes": Guided micro-step breakdown form

**Playwright Test:**
```python
def test_if_then_plan_creation(page):
    page.goto("http://localhost:8501")
    page.get_by_text("If-Then Planning").click()

    page.fill("input[aria-label='If (trigger)']", "I feel overwhelmed by task size")
    page.fill("input[aria-label='Then (action)']", "Break into 3 micro-steps and do step 1")
    page.get_by_role("button", name="Save Plan").click()

    assert "If-Then plan saved!" in page.content()
```

---

### AT-2.4: GTD Brain Dump Parsing

**Given:** User has many scattered thoughts
**When:** User submits brain dump:
```
"Need to email client about invoice, buy groceries for weekend,
review Q4 budget, learn Python async patterns, fix bug in calendar module"
```

**Then:**
- OpenAI parses into structured tasks:
  ```json
  [
    {"title": "Email client about invoice", "quadrant": "I", "urgency": 5, "importance": 5},
    {"title": "Buy groceries for weekend", "quadrant": "III", "urgency": 4, "importance": 2},
    {"title": "Review Q4 budget", "quadrant": "II", "urgency": 3, "importance": 5},
    {"title": "Learn Python async patterns", "quadrant": "II", "urgency": 2, "importance": 4},
    {"title": "Fix bug in calendar module", "quadrant": "I", "urgency": 5, "importance": 4}
  ]
  ```
- All tasks stored in `tasks` table with `source='brain_dump'`
- User shown review screen: "5 tasks created. Review classifications?"

**API Test:**
```bash
curl -X POST http://localhost:8000/discipline/brain-dump \
  -H "Content-Type: application/json" \
  -d '{
    "thoughts": "Need to email client, buy groceries, review budget, learn async, fix calendar bug"
  }'

# Response:
# {
#   "success": true,
#   "tasks_created": 5,
#   "tasks": [...]
# }
```

---

### AT-2.5: Weekly Review Generation

**Given:** User has completed 7 days of daily reflections
**When:** System reaches Sunday 8:00 PM (configurable)
**Then:**
- Weekly review auto-generated:
  ```
  📊 Weekly Review: 2025-W46

  Evening Planning: 5/7 days (71%)
  Task Completion: Q1=85%, Q2=60%, Q3=40%, Q4=20%

  Top Blockers:
  - Unexpected meetings (3 mentions)
  - Email overload (2 mentions)
  - Low energy afternoons (2 mentions)

  Best Day: Tuesday (4/4 tasks completed)

  Insights:
  - Schedule Q2 tasks for Tuesday mornings (highest productivity)
  - Block 2pm-3pm for email batch processing
  - Consider time blocking around meeting-heavy days
  ```
- Review stored in `daily_reflections` with special `is_weekly_review=1` flag
- Synced to Supabase `weekly_reflections` table with embeddings
- User notification: "📊 Your weekly review is ready!"

**API Test:**
```bash
curl -X GET http://localhost:8000/discipline/weekly-review?week=2025-W46

# Response includes:
# {
#   "week": "2025-W46",
#   "evening_plan_rate": 0.71,
#   "task_completion": {"Q1": 0.85, "Q2": 0.60, ...},
#   "blockers": ["Unexpected meetings", ...],
#   "best_day": "Tuesday",
#   "insights": [...]
# }
```

**Supabase Sync Verification:**
```sql
-- Query Supabase via API or direct SQL
SELECT * FROM weekly_reflections WHERE week = '2025-W46' AND system_id = 'asksharon';
-- Should return row with insights and embedding vector
```

---

## Tier 3: Advanced Accountability

### AT-3.1: Pomodoro Session Start

**Given:** User has task "Write documentation" in progress
**When:** User clicks "Start Pomodoro" (25 min default)
**Then:**
- Pomodoro session created in `pomodoro_sessions` table
- Timer displayed: "🍅 24:59" (counts down)
- Task locked (cannot switch tasks mid-Pomodoro)
- Browser tab title updates: "🍅 24:59 | AskSharon"

**Playwright Test:**
```python
def test_pomodoro_start(page):
    page.goto("http://localhost:8501")
    page.get_by_text("My Tasks").click()
    page.locator("text=Write documentation").click()
    page.get_by_role("button", name="Start Pomodoro").click()

    time.sleep(2)
    assert "24:5" in page.content()  # Timer started (24:59 or 24:58)
    assert "Pomodoro running" in page.content()
```

---

### AT-3.2: Pomodoro Session Complete

**Given:** Pomodoro timer running for 25 minutes
**When:** Timer reaches 00:00
**Then:**
- Browser notification: "🍅 Pomodoro complete! Take a 5-minute break."
- Sound plays (browser beep)
- Modal: "What did you accomplish?"
- User enters: "Completed 3 sections of docs"
- Session marked `completed=1` in database
- Task progress updated (if measurable)

**Playwright Test:**
```python
def test_pomodoro_complete(page):
    # Note: Mock timer to 0 for testing
    page.goto("http://localhost:8501")
    # ... start pomodoro ...
    # ... fast-forward timer to 0 (via test hook) ...

    page.wait_for_selector("text=Pomodoro complete!", timeout=5000)
    assert "What did you accomplish?" in page.content()

    page.fill("textarea[aria-label='Accomplishment']", "Completed 3 sections")
    page.get_by_role("button", name="Save").click()

    assert "Great work!" in page.content()
```

---

### AT-3.3: Streak Tracking - Current Streak

**Given:** User completes evening planning for 5 consecutive days
**When:** User views streaks dashboard
**Then:**
- Streak displayed:
  ```
  🔥 Evening Planning Streak
  Current: 5 days
  Longest: 12 days
  Last completed: 2025-11-15

  [Don't break the chain! Keep it going tonight.]
  ```
- Visual: 5 consecutive green checkmarks on calendar
- At-risk warning if current day not completed by 8pm:
  ```
  ⚠️ Streak at risk! Complete today's evening planning to keep your 5-day streak alive.
  ```

**API Test:**
```bash
curl -X GET http://localhost:8000/discipline/streaks

# Response:
# [
#   {
#     "activity": "Evening Planning",
#     "current_streak": 5,
#     "longest_streak": 12,
#     "last_completed": "2025-11-15",
#     "at_risk": false
#   }
# ]
```

---

### AT-3.4: Streak Recovery Mode

**Given:** User had 5-day evening planning streak, broke it yesterday
**When:** User completes evening planning today
**Then:**
- Recovery notification:
  ```
  🎉 Welcome back! Your streak restarted at 1 day.
  Previous best: 5 days. You can beat it!
  ```
- Database updates:
  - `current_streak = 1` (reset)
  - `longest_streak = 5` (preserved)
  - `total_completions` incremented
- Visual: New streak starts on calendar

**Backend Test:**
```python
def test_streak_recovery():
    from assistant.modules.discipline.streaks import update_streak

    # Simulate: Had 5-day streak, broke it, now completing again
    result = update_streak(
        activity="Evening Planning",
        previous_streak=5,
        days_since_last=2  # Broke streak (missed 1 day)
    )

    assert result["current_streak"] == 1  # Reset
    assert result["longest_streak"] == 5  # Preserved
    assert result["message"] == "Welcome back! Your streak restarted at 1 day."
```

---

### AT-3.5: CBT Thought Challenging - Log

**Given:** User procrastinating on task "Learn Python async"
**When:** System detects task delayed 3+ times
**Then:**
- Prompt appears:
  ```
  💭 What's making you avoid this task?

  Common thoughts:
  - "This is too hard, I'll fail"
  - "I don't have time"
  - "I'm not good at this"
  - [Other...]
  ```
- User selects: "This is too hard, I'll fail"
- System responds:
  ```
  That sounds like All-or-Nothing Thinking.

  Evidence against this thought:
  - You've learned new skills before (Git, React, SQL)
  - You can start small (15 min tutorial)

  Reframe: "I can learn the basics step by step."

  [Accept reframe] [Write my own]
  ```
- Thought + reframe stored in `thought_logs` table

**Playwright Test:**
```python
def test_cbt_thought_challenge(page):
    page.goto("http://localhost:8501")
    page.get_by_text("My Tasks").click()

    # Simulate task delayed 3+ times
    # System should show thought challenge prompt
    page.wait_for_selector("text=What's making you avoid this task?", timeout=5000)

    page.get_by_text("This is too hard, I'll fail").click()
    page.wait_for_selector("text=All-or-Nothing Thinking", timeout=3000)

    assert "Reframe:" in page.content()
    assert "I can learn the basics step by step" in page.content()
```

---

### AT-3.6: CBT AI-Assisted Reframing

**Given:** User enters custom thought: "I'm too tired to focus"
**When:** User clicks "Get AI suggestion"
**Then:**
- OpenAI analyzes thought:
  ```json
  {
    "thought": "I'm too tired to focus",
    "distortions": ["Mental filter", "Fortune-telling"],
    "reframe": "I can do 10 minutes of easy tasks to build momentum",
    "evidence": "You completed tasks while tired before (see: 2025-11-10 reflection)"
  }
  ```
- Suggestion displayed to user
- User can accept, edit, or reject

**API Test:**
```bash
curl -X POST http://localhost:8000/discipline/thought-challenge \
  -H "Content-Type: application/json" \
  -d '{
    "task_id": 123,
    "thought": "I'm too tired to focus"
  }'

# Response:
# {
#   "distortions": ["Mental filter", "Fortune-telling"],
#   "reframe": "I can do 10 minutes of easy tasks to build momentum",
#   "evidence": "You completed tasks while tired before (see: 2025-11-10 reflection)"
# }
```

---

### AT-3.7: Energy-Based Scheduling

**Given:** User has tracked energy levels for 14 days:
- AM energy: [4, 5, 5, 4, 5, 4, 5, 4, 5, 5, 4, 5, 5, 4] (avg: 4.6/5)
- PM energy: [3, 2, 3, 2, 3, 3, 2, 3, 2, 2, 3, 2, 3, 2] (avg: 2.5/5)

**When:** User requests time block suggestions for Q2 task (deep work)
**Then:**
- System analyzes energy patterns:
  ```
  ⚡ Energy Analysis:
  Peak hours: 9:00-11:00 AM (avg 4.6/5)
  Low hours: 2:00-4:00 PM (avg 2.5/5)

  Suggestion: Schedule "Learn Python async" for 9:00-10:30 AM tomorrow.
  Reason: Q2 task requires deep focus. Your morning energy is optimal.
  ```
- User can accept or override

**API Test:**
```bash
curl -X GET http://localhost:8000/discipline/energy-patterns

# Response:
# {
#   "peak_hours": ["09:00", "10:00", "11:00"],
#   "peak_avg_energy": 4.6,
#   "low_hours": ["14:00", "15:00", "16:00"],
#   "low_avg_energy": 2.5,
#   "recommendations": [
#     "Schedule Q2 tasks for morning (9-11am)",
#     "Batch Q3 tasks for afternoon (2-4pm)"
#   ]
# }
```

---

## Integration Tests

### AT-INT-1: Full Daily Cycle (Evening → Morning)

**Scenario:** Complete user journey from evening planning to next morning

**Steps:**
1. **6:00 PM Day 1:** Evening planning notification appears
2. User fills reflection form (what went well, what got in way)
3. User sets Top 3 priorities for Day 2
4. System stores in `daily_reflections`, sets `evening_completed=1`
5. **8:00 AM Day 2:** Morning check runs
6. System finds existing plan, displays Top 3 priorities
7. User clicks "Start Day"
8. Sidebar shows Top 3 tasks
9. User completes tasks throughout day
10. **6:00 PM Day 2:** Cycle repeats

**Playwright Test:**
```python
def test_full_daily_cycle(page):
    # Simulate 6pm Day 1
    page.goto("http://localhost:8501")
    # ... complete evening planning ...

    # Simulate 8am Day 2
    # ... verify morning plan display ...

    # Simulate task completion
    # ... check tasks ...

    # Verify database
    # daily_reflections should have 2 rows (Day 1 plan, Day 2 plan)
```

---

### AT-INT-2: Habit Stack → Streak → Milestone

**Scenario:** User creates habit, completes it for 7 days, reaches milestone

**Steps:**
1. Create habit stack: "After coffee → Review priorities"
2. Day 1: Complete → `success_count=1`
3. Day 2: Complete → `success_count=2`
4. Day 3: Complete → `success_count=3`, milestone: "🎉 3-day streak!"
5. Day 4-6: Complete → `success_count` increments
6. Day 7: Complete → `success_count=7`, milestone: "🔥 7-day streak!"

**Backend Test:**
```python
def test_habit_streak_milestone_integration():
    # Create habit
    # Simulate 7 completions
    # Verify milestones triggered at 3 and 7
    pass
```

---

### AT-INT-3: Task → Time Block → Pomodoro → Completion

**Scenario:** End-to-end task workflow

**Steps:**
1. User creates task: "Write Phase 3.5 docs" (Q2, 90 min)
2. User blocks time: 9:00-10:30 AM
3. Google Calendar event created
4. At 9:00 AM: User starts Pomodoro (25 min)
5. After 25 min: Pomodoro completes, user logs progress
6. User starts 2nd Pomodoro
7. After 2nd Pomodoro: User marks task complete
8. System updates:
   - `tasks.completed = 1`
   - `pomodoro_sessions` has 2 completed sessions
   - `time_blocks.calendar_synced = 1`
   - Google Calendar event marked complete

**Playwright Test:**
```python
def test_task_workflow_integration(page):
    # Create task
    # Block time
    # Start pomodoro
    # Complete pomodoro
    # Mark task done
    # Verify all systems updated
    pass
```

---

## Performance Acceptance Tests

### AT-PERF-1: Evening Planning Trigger Latency

**Given:** Current time is 6:00:00 PM
**When:** Scheduler checks for trigger
**Then:** Notification appears within **5 seconds**

**Test:**
```bash
# Set time to 5:59:58 PM, wait 3 seconds
# Measure time from 6:00:00 to notification appearance
# Assert: latency < 5 seconds
```

---

### AT-PERF-2: Weekly Review Generation Time

**Given:** User has 7 days of daily reflections (20 tasks/day, 140 total)
**When:** User requests weekly review
**Then:** Review generated within **10 seconds**

**Test:**
```bash
time curl -X GET http://localhost:8000/discipline/weekly-review
# Assert: response time < 10s
```

---

### AT-PERF-3: Supabase Sync Latency

**Given:** Weekly review generated (5KB data)
**When:** System syncs to Supabase
**Then:** Sync completes within **3 seconds**

---

## Security Acceptance Tests

### AT-SEC-1: Supabase Row-Level Security

**Given:** Two users (user_a, user_b) in Supabase
**When:** user_a queries `weekly_reflections` table
**Then:** user_a sees only their own reflections, NOT user_b's

**Test:**
```sql
-- As user_a:
SELECT * FROM weekly_reflections;
-- Should return only rows where user_id = 'user_a'

-- Attempt to query user_b's data:
SELECT * FROM weekly_reflections WHERE user_id = 'user_b';
-- Should return 0 rows (RLS blocks)
```

---

### AT-SEC-2: Input Validation (Brain Dump)

**Given:** Malicious user submits brain dump with SQL injection
**When:** Input: `"'; DROP TABLE tasks; --"`
**Then:**
- Input sanitized before OpenAI call
- No SQL executed
- Error returned: "Invalid input detected"

---

## Backwards Compatibility Tests

### AT-BC-1: Existing Tasks Unaffected

**Given:** User has 50 existing tasks in database (before Phase 3.5)
**When:** Phase 3.5 deployed (new `quadrant` column added)
**Then:**
- All 50 tasks still exist
- `quadrant` is NULL for old tasks (acceptable)
- User can manually classify or auto-classify via urgency/importance

---

### AT-BC-2: Existing Goals/Streaks Preserved

**Given:** User has 10 active goals, 3 active streaks (from Phase 2)
**When:** Phase 3.5 deployed
**Then:**
- All goals still tracked
- All streaks preserved
- New discipline streaks added (evening planning, habit chains)

---

## Rollback Acceptance Test

### AT-ROLLBACK-1: Phase 3.5 Removal

**Given:** Phase 3.5 deployed, user has 14 days of discipline data
**When:** Admin runs rollback:
```bash
# Drop new tables
sqlite3 assistant/data/memory.db < migrations/rollback_phase_3.5.sql
```
**Then:**
- `daily_reflections`, `habit_chains`, `pomodoro_sessions`, etc. dropped
- Original tables (`tasks`, `goals`, `behaviour_metrics`) unchanged
- System still functional (Phase 3 features intact)
- No data corruption

---

## Success Criteria Summary

Phase 3.5 is **ACCEPTED** when:

✅ All Tier 1 tests pass (AT-1.1 to AT-1.6)
✅ All Tier 2 tests pass (AT-2.1 to AT-2.5)
✅ All Tier 3 tests pass (AT-3.1 to AT-3.7)
✅ All integration tests pass (AT-INT-1 to AT-INT-3)
✅ Performance tests meet latency requirements
✅ Security tests verify RLS and input validation
✅ Backwards compatibility verified
✅ Rollback tested successfully
✅ User completes 1 full week (7 days) of evening planning with >70% adherence
✅ All Playwright E2E tests pass with screenshots
✅ All pytest backend tests pass
✅ User documentation reviewed and approved

**Total Tests:** 35+ acceptance tests
**Estimated Test Execution Time:** 2-3 hours (includes manual user journey tests)
