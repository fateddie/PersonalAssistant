# Phase 7: Prompt Coach - Implementation Tasks

## Week 1: Core Engine (8-12 hours)

### Database Setup (2 hours)

**Task 1.1: Create database migration**
- [ ] Create `migrations/phase_7_prompt_coach.sql`
- [ ] Add `prompt_sessions` table
- [ ] Add `prompt_templates` table
- [ ] Add `prompt_lessons` table
- [ ] Test migration on dev database
- [ ] Verify schema with SQLite browser

**Acceptance:**
```bash
sqlite3 assistant/data/memory.db ".schema prompt_sessions"
# Should show all columns: id, original_prompt, context, constraints, etc.
```

### Module Structure (1 hour)

**Task 1.2: Create module scaffolding**
- [ ] Create `assistant/modules/prompt_coach/` directory
- [ ] Create `__init__.py` with module registration
- [ ] Create placeholder files: `coach.py`, `extractor.py`, `interrogator.py`, `critic.py`
- [ ] Add to `module_registry.yaml`
- [ ] Verify module loads without errors

**Acceptance:**
```bash
python -c "from assistant.modules.prompt_coach import register; print('OK')"
# Should print: OK
```

### System Prompts (1 hour)

**Task 1.3: Implement system prompts**
- [ ] Create `system_prompts.py`
- [ ] Add `COACH_SYSTEM_PROMPT` (main coaching prompt from user's doc)
- [ ] Add `EXTRACTOR_PROMPT` (parse brain-dump)
- [ ] Add `INTERROGATOR_PROMPT` (generate questions)
- [ ] Add `CRITIC_PROMPT` (critique and teach)
- [ ] Add prompt versioning (for future iteration)

**Acceptance:**
```python
from assistant.modules.prompt_coach.system_prompts import COACH_SYSTEM_PROMPT
assert "CONTEXT" in COACH_SYSTEM_PROMPT
assert "blunt" in COACH_SYSTEM_PROMPT.lower()
```

### Extractor (2 hours)

**Task 1.4: Implement template extractor**
- [ ] Create `extractor.py`
- [ ] Implement `extract_template(brain_dump: str) -> TemplateDict`
- [ ] Parse into 6 sections: CONTEXT, CONSTRAINTS, INPUTS, TASK, EVALUATION, OUTPUT_FORMAT
- [ ] Mark missing sections as `[MISSING]`
- [ ] Mark unclear sections as `[UNCLEAR: reason]`
- [ ] Return structured dict with fill status per section

**Acceptance:**
```python
result = extract_template("help me write code for a thing")
assert result["task"]["status"] == "unclear"
assert result["constraints"]["status"] == "missing"
```

### Interrogator (2 hours)

**Task 1.5: Implement clarifying question generator**
- [ ] Create `interrogator.py`
- [ ] Implement `generate_questions(template: TemplateDict) -> List[Question]`
- [ ] Focus only on critical gaps (not nice-to-haves)
- [ ] Limit to max 5 questions
- [ ] Batch related questions
- [ ] Return structured questions with IDs

**Acceptance:**
```python
questions = generate_questions(partial_template)
assert len(questions) <= 5
assert all(q.id and q.text for q in questions)
```

### Critic (2 hours)

**Task 1.6: Implement critique generator**
- [ ] Create `critic.py`
- [ ] Implement `critique(original: str, template: TemplateDict) -> Critique`
- [ ] Compare original vs structured version
- [ ] Identify specific weaknesses in original
- [ ] Generate 3-5 prompt engineering lessons
- [ ] Explain WHY each improvement matters

**Acceptance:**
```python
critique = generate_critique(original_prompt, filled_template)
assert len(critique.lessons) >= 3
assert all(lesson.explanation for lesson in critique.lessons)
```

### Session Manager (2 hours)

**Task 1.7: Implement session state machine**
- [ ] Create `session.py`
- [ ] Implement `PromptCoachSession` class
- [ ] States: START → EXTRACT → INTERROGATE → WAITING → FILL → CRITIQUE → OUTPUT → SAVE
- [ ] Handle state transitions
- [ ] Persist session to database
- [ ] Support session resumption

**Acceptance:**
```python
session = PromptCoachSession.create("messy prompt")
assert session.status == "extracting"
session.process()
assert session.status in ["interrogating", "filling"]
```

---

## Week 2: API & UI (10-15 hours)

### API Endpoints (4 hours)

**Task 2.1: Implement core API routes**
- [ ] Create `assistant/modules/prompt_coach/routes.py`
- [ ] `POST /prompt-coach/start` - Start new session
- [ ] `GET /prompt-coach/session/{id}` - Get session state
- [ ] `POST /prompt-coach/answer/{id}` - Submit answers
- [ ] `GET /prompt-coach/result/{id}` - Get final output
- [ ] Add error handling and validation

**Acceptance:**
```bash
curl -X POST http://localhost:8000/prompt-coach/start \
  -H "Content-Type: application/json" \
  -d '{"prompt": "help me write code"}'
# Should return: {"session_id": 1, "status": "extracting"}
```

**Task 2.2: Implement template library endpoints**
- [ ] `POST /prompt-coach/save/{id}` - Save to library
- [ ] `GET /prompt-coach/templates` - List templates
- [ ] `POST /prompt-coach/use-template/{id}` - Use saved template
- [ ] `DELETE /prompt-coach/templates/{id}` - Delete template
- [ ] Add search/filter support

**Acceptance:**
```bash
curl -X GET http://localhost:8000/prompt-coach/templates
# Should return: [{"id": 1, "name": "...", "category": "...", ...}]
```

**Task 2.3: Implement lessons endpoint**
- [ ] `GET /prompt-coach/lessons` - Get lessons learned
- [ ] Filter by category
- [ ] Pagination support
- [ ] Return with frequency counts

**Acceptance:**
```bash
curl -X GET "http://localhost:8000/prompt-coach/lessons?category=vague_task"
# Should return lessons for that category
```

### Streamlit UI (6 hours)

**Task 2.4: Create main coach UI**
- [ ] Create `assistant/modules/voice/components/prompt_coach_ui.py`
- [ ] Brain dump input (large text area)
- [ ] "Coach Me" button to start session
- [ ] Loading state while processing
- [ ] Display session status

**Playwright Test:**
```python
def test_prompt_coach_starts_session(page):
    page.goto("http://localhost:8501")
    page.get_by_text("Prompt Coach").click()
    page.fill("textarea", "help me write code")
    page.get_by_role("button", name="Coach Me").click()
    page.wait_for_selector("text=Analyzing")
```

**Task 2.5: Implement template display**
- [ ] 6-section template view
- [ ] Color-coded status: ✅ filled, ⚠️ unclear, ❌ missing
- [ ] Expandable sections
- [ ] Edit capability for each section

**Playwright Test:**
```python
def test_template_displays_sections(page):
    # After starting session
    assert "CONTEXT" in page.content()
    assert "CONSTRAINTS" in page.content()
    assert "TASK" in page.content()
```

**Task 2.6: Implement Q&A flow**
- [ ] Display clarifying questions as cards
- [ ] Text input for each answer
- [ ] Submit all answers button
- [ ] Show progress (questions remaining)

**Playwright Test:**
```python
def test_clarifying_questions_flow(page):
    # After extraction with missing fields
    page.wait_for_selector("text=Clarifying Questions")
    page.fill("input[name='q1']", "Python for file renaming")
    page.get_by_role("button", name="Submit Answers").click()
```

**Task 2.7: Implement critique display**
- [ ] Critique summary card
- [ ] Expandable lessons with explanations
- [ ] Visual diff: original vs improved (optional)
- [ ] "Save lesson" button for important learnings

**Task 2.8: Implement final prompt output**
- [ ] Clean formatted final prompt
- [ ] Copy to clipboard button
- [ ] "Save as Template" button
- [ ] "Start New" button

**Playwright Test:**
```python
def test_final_prompt_copyable(page):
    # After critique complete
    page.wait_for_selector("text=Final Prompt")
    page.get_by_role("button", name="Copy").click()
    # Verify clipboard (platform-specific)
```

### Template Library UI (2 hours)

**Task 2.9: Implement template library view**
- [ ] Grid of saved templates
- [ ] Search by name/category
- [ ] Filter by category
- [ ] Sort by recent/most used
- [ ] Delete template option

**Task 2.10: Implement template usage flow**
- [ ] Click template to view
- [ ] "Use This Template" button
- [ ] Pre-fill session with template
- [ ] Allow customization before finalizing

---

## Week 3: Integration & Polish (8-12 hours)

### Event Bus Integration (2 hours)

**Task 3.1: Publish events**
- [ ] Publish `prompt.session.started` on new session
- [ ] Publish `prompt.template.completed` when template filled
- [ ] Publish `prompt.lesson.learned` with lessons array
- [ ] Publish `prompt.saved_to_library` on save
- [ ] Add to event bus documentation

**Acceptance:**
```python
# Verify events are published
def test_events_published():
    events = []
    subscribe("prompt.*", lambda e: events.append(e))
    start_coaching_session("test prompt")
    assert any(e.type == "prompt.session.started" for e in events)
```

**Task 3.2: Subscribe to relevant events**
- [ ] Subscribe to `task.created` - offer coaching
- [ ] Subscribe to `goal.created` - offer coaching
- [ ] Add "Coach this?" prompt in UI when triggered

### Phase 3.5 Integration (2 hours)

**Task 3.3: Hook into discipline features**
- [ ] Offer coaching when creating evening plan tasks
- [ ] Use coach for If-Then implementation intentions
- [ ] Add "Clarify with Coach" button on vague tasks
- [ ] Track coaching usage in discipline metrics

**Acceptance:**
```python
def test_coach_offered_for_vague_task(page):
    page.goto("http://localhost:8501")
    page.get_by_text("Add Task").click()
    page.fill("input", "do the thing")
    # Should show: "This task is vague. Clarify with Prompt Coach?"
```

### Lessons Dashboard (2 hours)

**Task 3.4: Implement analytics view**
- [ ] Common mistake categories (pie chart)
- [ ] Lessons over time (line chart)
- [ ] Most frequent issues
- [ ] Improvement metrics (if trackable)

**Task 3.5: Semantic search for lessons**
- [ ] Generate embeddings for lessons
- [ ] Store in FAISS index
- [ ] "Find similar lessons" feature
- [ ] Surface relevant past lessons during new sessions

### Testing (3 hours)

**Task 3.6: Unit tests**
- [ ] Test extractor with various inputs
- [ ] Test interrogator question generation
- [ ] Test critic lesson generation
- [ ] Test session state transitions
- [ ] Test API endpoints

**Acceptance:**
```bash
pytest tests/unit/test_prompt_coach.py -v
# Should show: 15+ passed
```

**Task 3.7: E2E tests with Playwright**
- [ ] Full coaching flow test
- [ ] Template save/load test
- [ ] Lessons view test
- [ ] Copy to clipboard test
- [ ] Error handling test

**Acceptance:**
```bash
pytest tests/e2e/test_prompt_coach_e2e.py -v
# Should show: 8+ passed
```

### Documentation (1 hour)

**Task 3.8: User documentation**
- [ ] Add usage guide in `docs/PROMPT_COACH_GUIDE.md`
- [ ] Document all available commands
- [ ] Add examples of good vs bad prompts
- [ ] Tips for getting most out of coach

**Task 3.9: Update project docs**
- [ ] Update `docs/INDEX.md` with Phase 7
- [ ] Update `CLAUDE.md` with prompt coach context
- [ ] Add to module registry documentation

---

## Deployment Checklist

### Pre-Deployment

- [ ] All unit tests pass
- [ ] All Playwright E2E tests pass
- [ ] Black formatting applied
- [ ] Mypy type checks pass
- [ ] Database migration tested
- [ ] Event bus integration verified
- [ ] UI responsive on different screen sizes

### Deployment

- [ ] Run migration: `sqlite3 assistant/data/memory.db < migrations/phase_7_prompt_coach.sql`
- [ ] Verify tables created
- [ ] Restart backend
- [ ] Restart frontend
- [ ] Test full coaching flow manually

### Post-Deployment

- [ ] Monitor for errors
- [ ] Gather user feedback
- [ ] Track usage metrics
- [ ] Iterate on system prompts if needed

---

## Estimated Effort Summary

| Week | Focus | Hours |
|------|-------|-------|
| 1 | Core Engine | 8-12 |
| 2 | API & UI | 10-15 |
| 3 | Integration & Polish | 8-12 |
| **Total** | | **26-39** |

---

## Success Criteria

Phase 7 is **COMPLETE** when:

✅ User can enter messy brain-dump and get structured template
✅ System asks <5 targeted clarifying questions
✅ Critique explains WHY improvements matter
✅ 3-5 lessons generated per session
✅ Templates can be saved to personal library
✅ Templates can be reused and customized
✅ Lessons searchable and viewable
✅ Integration with Phase 3.5 discipline features
✅ All unit tests pass (15+)
✅ All E2E tests pass (8+)
✅ Copy to clipboard works
✅ User documentation complete
