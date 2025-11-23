# Phase 7: Prompt Coach - Acceptance Tests

## Overview

This document defines the acceptance criteria for Phase 7 Prompt Coach.
All tests must pass before the phase is considered complete.

**Related Documents:**
- [Unit Test Specifications](./test_specs_unit.md) - Detailed unit test code
- [E2E Test Specifications](./test_specs_e2e.md) - Playwright E2E test code

---

## Test Summary

### Unit Tests (24 total)

| Component | File | Test Count |
|-----------|------|------------|
| Extractor | `tests/unit/test_prompt_coach_extractor.py` | 5 |
| Interrogator | `tests/unit/test_prompt_coach_interrogator.py` | 4 |
| Critic | `tests/unit/test_prompt_coach_critic.py` | 4 |
| Session | `tests/unit/test_prompt_coach_session.py` | 4 |
| API | `tests/unit/test_prompt_coach_api.py` | 7 |

### E2E Tests (6 total)

| Test | File | Description |
|------|------|-------------|
| Full Flow | `tests/e2e/test_prompt_coach_e2e.py` | Brain-dump to final prompt |
| Template Save | `tests/e2e/test_prompt_coach_e2e.py` | Save and reuse templates |
| Lessons View | `tests/e2e/test_prompt_coach_e2e.py` | View accumulated lessons |
| Copy Clipboard | `tests/e2e/test_prompt_coach_e2e.py` | Copy final prompt |
| Error Handling | `tests/e2e/test_prompt_coach_e2e.py` | Handle empty/invalid input |
| Question Flow | `tests/e2e/test_prompt_coach_e2e.py` | Clarifying questions UI |

### Integration Tests (3 total)

| Test | File | Description |
|------|------|-------------|
| Event Bus | `tests/integration/test_prompt_coach_integration.py` | Events published |
| Database | `tests/integration/test_prompt_coach_integration.py` | Session persistence |
| Memory | `tests/integration/test_prompt_coach_integration.py` | Lessons in semantic search |

---

## Acceptance Criteria Summary

### Must Pass (Blocking)

| Test Category | Min Pass Rate | Test Count |
|---------------|---------------|------------|
| Extractor Unit | 100% | 5 |
| Interrogator Unit | 100% | 4 |
| Critic Unit | 100% | 4 |
| Session Unit | 100% | 4 |
| API Tests | 100% | 7 |
| E2E Full Flow | 100% | 1 |
| E2E Template Save | 100% | 1 |
| E2E Copy | 100% | 1 |

### Should Pass (Non-Blocking)

| Test Category | Target Pass Rate |
|---------------|-----------------|
| E2E Lessons View | 100% |
| E2E Error Handling | 100% |
| Integration Tests | 100% |

---

## Running Tests

```bash
# All unit tests
pytest tests/unit/test_prompt_coach*.py -v

# All E2E tests
pytest tests/e2e/test_prompt_coach_e2e.py -v

# Full test suite
pytest tests/ -k "prompt_coach" -v

# With coverage
pytest tests/unit/test_prompt_coach*.py --cov=assistant/modules/prompt_coach
```

---

## Definition of Done

Phase 7 is **COMPLETE** when:

- [ ] All 24+ unit tests pass
- [ ] All 6+ E2E tests pass
- [ ] API responds correctly to all endpoints
- [ ] UI displays all components without errors
- [ ] Copy to clipboard works
- [ ] Templates save and load correctly
- [ ] Lessons accumulate and display
- [ ] Event bus integration verified
- [ ] No console errors in browser
- [ ] No Python exceptions in logs

---

## Key Test Scenarios

### 1. Extractor Tests
- Well-formed prompt extracts all 6 sections
- Vague prompt marks sections as unclear/missing
- Partial prompt extracts available info
- Empty prompt returns all missing
- No hallucination (doesn't invent info)

### 2. Interrogator Tests
- Missing sections generate questions
- Complete template generates no questions
- Questions are targeted to gaps
- Max 5 questions enforced

### 3. Critic Tests
- Identifies improvements made
- Generates 3-5 lessons
- Lessons have explanations (WHY)
- Critique is blunt, not flattering

### 4. Session Tests
- Creates with correct initial state
- Transitions through states correctly
- Persists and loads from database
- Handles errors gracefully

### 5. API Tests
- Start session endpoint works
- Get session returns state
- Answer questions accepted
- Save template works
- List templates returns array
- Invalid session returns 404

### 6. E2E Tests
- Full coaching flow completes
- Templates save and reuse
- Lessons dashboard displays
- Copy to clipboard works
- Empty prompt handled
- Clarifying questions flow works
