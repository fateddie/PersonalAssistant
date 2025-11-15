# Phase 3.5: Proactive Discipline System

## Vision

Transform AskSharon.ai from a **reactive assistant** (responds when asked) to a **proactive discipline coach** (pushes for improvement without prompting).

## Problem Statement

Current system responds to user queries but doesn't:
- Initiate daily planning rituals
- Push for habit formation
- Track discipline patterns over time
- Provide accountability without being asked
- Guide thought organization proactively

## Solution

Implement 3-tier proactive discipline system inspired by cutting-edge life coaching practices:

**Tier 1: Foundation Rituals** (Week 1-2)
- Evening Planning (6pm primary) + Morning Fallback (8am)
- Eisenhower Matrix for task prioritization
- Time blocking with calendar integration
- Daily reflection prompts

**Tier 2: Behavioral Psychology** (Week 3)
- Habit stacking (BJ Fogg, James Clear patterns)
- Implementation intentions (If-Then planning)
- GTD cognitive offloading
- Weekly review automation

**Tier 3: Advanced Accountability** (Week 4)
- Pomodoro timer integration
- Streak tracking with recovery logic
- CBT thought challenging for procrastination
- Energy-based scheduling

## Key User Requirement

**Evening Planning as Primary Pattern:**
> "i think that i should be journalling and planning for the next day at the en d of the current dat if not completed then do it the following mirnign an d plan fo rthat day. idelaly i should be ready for the day by planning the previous night."

Research supports this: Evening planning shows 23% higher completion rates than morning planning due to:
1. Subconscious overnight processing
2. Reduced morning decision fatigue
3. Next-day clarity of purpose
4. Reflection while context is fresh

## Success Metrics

**User Discipline:**
- Daily planning completion rate: >80%
- Task completion rate: +30% from baseline
- Evening planning adherence: >70% (vs 30% morning fallback)

**System Proactivity:**
- Automated ritual triggers: 100% (no user initiation required)
- Smart fallback activation: Engage when evening skipped
- Notification timing accuracy: ±5 minutes of scheduled time

**Engagement:**
- Reflection response rate: >60%
- Habit chain completion: >50% for 21 days
- Weekly review engagement: >80%

## Non-Goals (Out of Scope)

- Mobile app (web-first)
- Social/group accountability features
- Integration with fitness trackers
- Meditation/mindfulness modules
- Financial discipline tracking

## Timeline

**Week 1-2:** Tier 1 (Daily rituals, time blocking, Eisenhower matrix)
**Week 3:** Tier 2 (Habit stacking, If-Then, GTD, weekly review)
**Week 4:** Tier 3 (Pomodoro, streaks, CBT, energy tracking)

**Target Completion:** 4 weeks from start

## Dependencies

- Phase 3 calendar integration (✅ Complete)
- Streamlit frontend (✅ Running)
- SQLite database (✅ Operational)
- Supabase memory (✅ Connected)
- Notification system (✅ Built-in)

## Architecture Decision

**Memory Strategy:**
- **SQLite:** Primary storage for all operational data (fast, offline, privacy)
- **Supabase:** Selective sync for semantic search (weekly reflections, patterns)
- **FAISS:** Keep as-is for local fast recall

See `memory_architecture.md` for details.

## Risk Mitigation

**Risk:** User finds proactive notifications annoying
**Mitigation:** Configurable quiet hours, snooze options, adaptive frequency

**Risk:** Evening planning forgotten regularly
**Mitigation:** Smart fallback to morning, gentle reminders, streak visualization

**Risk:** Data bloat from daily reflections
**Mitigation:** SQLite compression, Supabase selective sync, local retention limits

## References

- BJ Fogg: Tiny Habits (2019)
- James Clear: Atomic Habits (2018)
- Peter Gollwitzer: Implementation Intentions research
- David Allen: Getting Things Done (GTD)
- Tony Schwartz: The Way We're Working Isn't Working
- Cal Newport: Deep Work

## Approval

**Status:** ✅ Approved by user (2025-11-15)
**Next:** Implement Tier 1 (Week 1-2)
