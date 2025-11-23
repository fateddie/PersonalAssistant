# Phase 7: Prompt Coach System

## Vision

Transform messy brain-dumps into structured, high-quality prompts through an intelligent coaching system that interrogates, structures, critiques, and teaches — becoming a core thinking discipline tool within AskSharon.

## Problem Statement

**User Pain Points:**
1. Initial prompts are often messy, incomplete, or vague
2. No repeatable template for quality prompts
3. Users don't understand *why* prompts fail or succeed
4. Time wasted on iterative prompt refinement
5. No learning accumulation — same mistakes repeated

**Personal Context:**
- Busy mind with many ideas, low completion rate
- Procrastination through overbuilding and parallel projects
- High creativity but needs systems, constraints, and structure to execute

## Solution

A Prompt Coach that:
1. **Extracts** messy brain-dumps into structured sections
2. **Interrogates** with targeted clarifying questions (minimum necessary)
3. **Structures** into a reusable 6-section template
4. **Critiques** weaknesses bluntly and constructively
5. **Teaches** why changes matter (builds prompt engineering skill)

### The Template Structure

```
CONTEXT:      What you're trying to achieve and why it matters
CONSTRAINTS:  Tone, audience, limits, boundaries, must-include elements
INPUTS:       Assumptions, data, drafts, examples, blockers
TASK:         Exact action you want the LLM to perform
EVALUATION:   How you'll judge output quality
OUTPUT FORMAT: Bullets, steps, table, sections, JSON, etc.
```

## Key User Requirements

> "I want something working immediately... This is not just for today's prompt — I want this to become a feature."

> "A system that extracts my messy brain-dump, forces clarity through structured sections, critiques weaknesses, and teaches me why."

## Success Metrics

**Prompt Quality:**
- Template completion rate: 100% (all 6 sections filled)
- Ambiguity reduction: 80%+ of vague elements clarified
- Reusability: 70%+ of prompts saved as templates

**User Learning:**
- Lessons captured per session: 3-5
- Repeat mistake reduction: 50% after 2 weeks
- User satisfaction with critiques: >80%

**System Performance:**
- Clarifying questions per session: <5 (targeted, not exhaustive)
- Time to final prompt: <5 minutes average
- Template library growth: 10+ personal templates per month

## Strategic Fit

**Short-term:** Personal prompt improvement tool (works immediately)
**Medium-term:** Embedded into AskSharon Streamlit UI
**Long-term:** "Prompt Intelligence Layer" integrated with:
- Phase 3.5 Discipline (use coach for task planning clarity)
- Phase 6 Gmail (coach email command formulation)
- Memory system (learn from past successful prompts)

## Constraints

- Must use existing unified API architecture
- Integrate with event bus (no cross-module imports)
- Follow phase-gated development (acceptance tests per week)
- Blunt, honest feedback (no flattery)
- Teaching-oriented (explain WHY, not just fix)

## Non-Goals (Out of Scope)

- Multi-user collaboration on prompts
- Integration with external prompt libraries (PromptBase, etc.)
- Automated prompt A/B testing
- Voice-based prompt coaching
- Model-specific optimization (GPT vs Claude vs etc.)

## Dependencies

- Phase 1: Unified API ✅
- Phase 2: Behavioral Intelligence ✅ (for learning patterns)
- Streamlit frontend ✅
- SQLite database ✅
- OpenAI API ✅ (for interrogation/critique)

## Timeline

**Total Duration:** 2-3 weeks (15-25 hours)

- **Week 1:** Core engine (template extraction, interrogation flow, critique)
- **Week 2:** UI & learning (Streamlit interface, template library, lessons tracker)
- **Week 3:** Integration & polish (Phase 3.5 hooks, analytics, E2E tests)

## Risk Mitigation

**Risk:** Over-questioning frustrates user
**Mitigation:** Limit to <5 targeted questions; batch related gaps

**Risk:** Critiques feel harsh
**Mitigation:** Always pair criticism with specific improvement + teaching

**Risk:** Template becomes rigid/limiting
**Mitigation:** Allow flexible sections; coach adapts to prompt type

**Risk:** Feature creep into full "prompt marketplace"
**Mitigation:** Strict non-goals; personal tool first

## References

- OpenAI Prompt Engineering Guide
- Anthropic Claude Prompting Best Practices
- "The Art of Prompt Engineering" (various)
- BJ Fogg: Tiny Habits (systems for behavior change)

## Approval

**Status:** ✅ Approved by user (2025-11-23)
**Next:** Implement Week 1 - Core Engine
