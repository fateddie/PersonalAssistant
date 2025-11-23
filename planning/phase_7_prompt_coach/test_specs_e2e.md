# Phase 7: E2E Test Specifications

## Playwright E2E Tests

**File:** `tests/e2e/test_prompt_coach_e2e.py`

---

### Test 1: Full Coaching Flow

```python
def test_full_coaching_flow(page):
    """Complete flow from brain-dump to final prompt"""
    # Navigate to Prompt Coach
    page.goto("http://localhost:8501")
    page.get_by_text("Prompt Coach").click()

    # Enter brain dump
    page.fill("textarea[aria-label='Enter your prompt idea']",
              "help me write some code for a thing that processes data")

    # Start coaching
    page.get_by_role("button", name="Coach Me").click()

    # Wait for extraction
    page.wait_for_selector("text=Template", timeout=10000)

    # Should show template with some missing/unclear sections
    assert "TASK" in page.content()

    # If questions appear, answer them
    if page.locator("text=Clarifying Questions").is_visible():
        inputs = page.locator("input[type='text']")
        for i in range(inputs.count()):
            inputs.nth(i).fill(f"Answer {i+1}")
        page.get_by_role("button", name="Submit").click()

    # Wait for critique
    page.wait_for_selector("text=Critique", timeout=15000)

    # Should show lessons
    assert "Lessons" in page.content() or "lessons" in page.content()

    # Should show final prompt
    page.wait_for_selector("text=Final Prompt", timeout=5000)

    # Copy button should exist
    assert page.get_by_role("button", name="Copy").is_visible()
```

---

### Test 2: Template Save and Reuse

```python
def test_save_and_reuse_template(page):
    """Save template to library and reuse it"""
    # Complete a coaching session first
    complete_coaching_session(page, "write a python function")

    # Save as template
    page.get_by_role("button", name="Save as Template").click()
    page.fill("input[aria-label='Template Name']", "Python Function Template")
    page.select_option("select[aria-label='Category']", "coding")
    page.get_by_role("button", name="Save").click()

    # Verify saved
    page.wait_for_selector("text=Template saved")

    # Go to template library
    page.get_by_text("Template Library").click()

    # Find saved template
    assert "Python Function Template" in page.content()

    # Use template
    page.get_by_text("Python Function Template").click()
    page.get_by_role("button", name="Use Template").click()

    # Should pre-fill session
    assert page.locator("textarea").input_value() != ""
```

---

### Test 3: Lessons View

```python
def test_lessons_dashboard(page):
    """View accumulated lessons"""
    # Complete several sessions to generate lessons
    for prompt in ["help", "do thing", "make it work"]:
        complete_coaching_session(page, prompt)

    # Navigate to lessons
    page.get_by_text("My Lessons").click()

    # Should show lesson categories
    assert page.locator(".lesson-card").count() > 0

    # Should show explanations
    page.locator(".lesson-card").first.click()
    assert "WHY" in page.content() or "because" in page.content().lower()
```

---

### Test 4: Copy to Clipboard

```python
def test_copy_final_prompt(page):
    """Final prompt copies to clipboard"""
    complete_coaching_session(page, "write a test")

    # Click copy
    page.get_by_role("button", name="Copy").click()

    # Should show confirmation
    page.wait_for_selector("text=Copied")
```

---

### Test 5: Error Handling

```python
def test_handles_empty_prompt(page):
    """Gracefully handles empty prompt"""
    page.goto("http://localhost:8501")
    page.get_by_text("Prompt Coach").click()

    # Try to submit empty
    page.get_by_role("button", name="Coach Me").click()

    # Should show error or validation message
    assert page.locator("text=enter a prompt").is_visible() or \
           page.locator("text=required").is_visible()


def test_handles_api_error(page):
    """Gracefully handles backend errors"""
    # This test would require mocking the API to fail
    # Implementation depends on test infrastructure
    pass
```

---

### Test 6: Question Flow

```python
def test_clarifying_questions_flow(page):
    """Questions appear and can be answered"""
    page.goto("http://localhost:8501")
    page.get_by_text("Prompt Coach").click()

    # Very vague prompt should trigger questions
    page.fill("textarea", "help")
    page.get_by_role("button", name="Coach Me").click()

    # Wait for questions
    page.wait_for_selector("text=Clarifying Questions", timeout=10000)

    # Should have question inputs
    question_count = page.locator("input[type='text']").count()
    assert question_count > 0
    assert question_count <= 5  # Max 5 questions

    # Answer questions
    for i in range(question_count):
        page.locator("input[type='text']").nth(i).fill(f"Answer for question {i+1}")

    # Submit
    page.get_by_role("button", name="Submit").click()

    # Should progress past questions
    page.wait_for_selector("text=Template", timeout=10000)
```

---

## Integration Tests

**File:** `tests/integration/test_prompt_coach_integration.py`

### Event Bus Integration

```python
def test_event_bus_integration():
    """Prompt coach publishes expected events"""
    events_received = []

    def capture_event(event):
        events_received.append(event)

    subscribe("prompt.*", capture_event)

    # Run a coaching session
    session = PromptCoachSession.create("test prompt")
    session.process()

    # Should have published session started
    assert any(e.type == "prompt.session.started" for e in events_received)
```

### Database Persistence

```python
def test_database_persistence():
    """Sessions persist across restarts"""
    # Create session
    session = PromptCoachSession.create("test")
    session_id = session.id
    session.process()

    # Simulate restart by creating new connection
    new_session = PromptCoachSession.load(session_id)
    assert new_session.original_prompt == "test"
    assert new_session.status == session.status
```

### Memory Module Integration

```python
def test_memory_module_integration():
    """Lessons stored in memory for semantic search"""
    # Complete session with lessons
    session = PromptCoachSession.create("vague prompt")
    session.run_to_completion()

    # Search memory for lesson
    from assistant.core.context_manager import recall_memories
    results = recall_memories("prompt engineering lessons", limit=5)

    # Should find related lesson
    assert len(results) > 0
```

---

## Helper Functions

```python
def complete_coaching_session(page, prompt: str):
    """Helper to complete a full coaching session"""
    page.goto("http://localhost:8501")
    page.get_by_text("Prompt Coach").click()
    page.fill("textarea", prompt)
    page.get_by_role("button", name="Coach Me").click()

    # Wait and answer questions if needed
    page.wait_for_selector("text=Template", timeout=10000)

    if page.locator("text=Clarifying Questions").is_visible():
        inputs = page.locator("input[type='text']")
        for i in range(inputs.count()):
            inputs.nth(i).fill(f"Answer {i+1}")
        page.get_by_role("button", name="Submit").click()

    # Wait for completion
    page.wait_for_selector("text=Final Prompt", timeout=20000)
```
