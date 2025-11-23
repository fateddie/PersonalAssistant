# Phase 7: Unit Test Specifications

## 1. Extractor Tests

**File:** `tests/unit/test_prompt_coach_extractor.py`

```python
def test_extract_complete_prompt():
    """Well-formed prompt extracts all 6 sections"""
    prompt = """
    I need to write a Python script for file renaming.
    Target audience is myself. Must work on macOS, no external deps.
    I have a directory of photos with inconsistent names.
    Write a script that renames files to YYYY-MM-DD format.
    Success = handles 100 files without errors.
    Output should be a single .py file with comments.
    """
    result = extract_template(prompt)
    assert result["context"]["status"] == "filled"
    assert result["constraints"]["status"] == "filled"
    assert result["task"]["status"] == "filled"


def test_extract_vague_prompt():
    """Vague prompt marks sections as unclear/missing"""
    prompt = "help me write code for a thing"
    result = extract_template(prompt)
    assert result["task"]["status"] == "unclear"
    assert result["constraints"]["status"] == "missing"
    assert result["evaluation"]["status"] == "missing"


def test_extract_partial_prompt():
    """Partial prompt extracts what's available"""
    prompt = "Write a Python function to sort a list"
    result = extract_template(prompt)
    assert result["task"]["status"] == "filled"
    assert "Python" in result["task"]["content"]
    assert result["context"]["status"] == "missing"


def test_extract_handles_empty():
    """Empty prompt returns all missing"""
    result = extract_template("")
    for section in ["context", "constraints", "inputs", "task", "evaluation", "output_format"]:
        assert result[section]["status"] == "missing"


def test_extract_no_hallucination():
    """Extractor doesn't invent information not in prompt"""
    prompt = "help with email"
    result = extract_template(prompt)
    assert "specific" not in result["task"]["content"].lower() or result["task"]["status"] == "unclear"
```

---

## 2. Interrogator Tests

**File:** `tests/unit/test_prompt_coach_interrogator.py`

```python
def test_generates_questions_for_missing():
    """Missing sections generate questions"""
    template = {
        "context": {"status": "missing", "content": ""},
        "task": {"status": "filled", "content": "write code"},
        "constraints": {"status": "missing", "content": ""},
        "inputs": {"status": "missing", "content": ""},
        "evaluation": {"status": "missing", "content": ""},
        "output_format": {"status": "missing", "content": ""},
    }
    questions = generate_questions(template)
    assert len(questions) > 0
    assert len(questions) <= 5


def test_no_questions_for_complete():
    """Complete template generates no questions"""
    template = {
        "context": {"status": "filled", "content": "..."},
        "task": {"status": "filled", "content": "..."},
        "constraints": {"status": "filled", "content": "..."},
        "inputs": {"status": "filled", "content": "..."},
        "evaluation": {"status": "filled", "content": "..."},
        "output_format": {"status": "filled", "content": "..."},
    }
    questions = generate_questions(template)
    assert len(questions) == 0


def test_questions_are_targeted():
    """Questions address specific missing sections"""
    template = {
        "context": {"status": "filled", "content": "Python script"},
        "task": {"status": "unclear", "content": "do something"},
        "constraints": {"status": "missing", "content": ""},
        "inputs": {"status": "filled", "content": "data file"},
        "evaluation": {"status": "missing", "content": ""},
        "output_format": {"status": "filled", "content": "script"},
    }
    questions = generate_questions(template)
    question_text = " ".join(q.text.lower() for q in questions)
    assert "constraint" in question_text or "limit" in question_text or "requirement" in question_text


def test_max_five_questions():
    """Never generates more than 5 questions"""
    template = {k: {"status": "missing", "content": ""}
                for k in ["context", "constraints", "inputs", "task", "evaluation", "output_format"]}
    questions = generate_questions(template)
    assert len(questions) <= 5
```

---

## 3. Critic Tests

**File:** `tests/unit/test_prompt_coach_critic.py`

```python
def test_critique_identifies_improvements():
    """Critique highlights what was improved"""
    original = "write code"
    template = {
        "context": {"status": "filled", "content": "Python script for data processing"},
        "task": {"status": "filled", "content": "Write a script to parse CSV files"},
    }
    critique = generate_critique(original, template)
    assert "vague" in critique.analysis.lower() or "unclear" in critique.analysis.lower()


def test_critique_generates_lessons():
    """Critique includes 3-5 lessons"""
    original = "help me"
    template = {"task": {"status": "filled", "content": "..."}}
    critique = generate_critique(original, template)
    assert len(critique.lessons) >= 3
    assert len(critique.lessons) <= 5


def test_lessons_have_explanations():
    """Each lesson explains WHY it matters"""
    original = "do thing"
    template = {"task": {"status": "filled", "content": "..."}}
    critique = generate_critique(original, template)
    for lesson in critique.lessons:
        assert lesson.explanation is not None
        assert len(lesson.explanation) > 20


def test_critique_is_blunt():
    """Critique doesn't flatter or hedge"""
    original = "help"
    template = {"task": {"status": "filled", "content": "..."}}
    critique = generate_critique(original, template)
    hedging_phrases = ["perhaps", "maybe you could consider", "it might be nice"]
    for phrase in hedging_phrases:
        assert phrase not in critique.analysis.lower()
```

---

## 4. Session Tests

**File:** `tests/unit/test_prompt_coach_session.py`

```python
def test_session_creation():
    """Session creates with correct initial state"""
    session = PromptCoachSession.create("test prompt")
    assert session.status == "extracting"
    assert session.original_prompt == "test prompt"
    assert session.id is not None


def test_session_state_transitions():
    """Session transitions through expected states"""
    session = PromptCoachSession.create("help me write code")
    session.process()
    assert session.status in ["interrogating", "filling"]

    if session.status == "interrogating":
        session.submit_answers({"q1": "Python", "q2": "macOS"})
        session.process()

    assert session.status in ["filling", "critiquing", "complete"]


def test_session_persistence():
    """Session saves and loads from database"""
    session = PromptCoachSession.create("test prompt")
    session_id = session.id
    session.process()

    loaded = PromptCoachSession.load(session_id)
    assert loaded.original_prompt == "test prompt"
    assert loaded.status == session.status


def test_session_handles_errors():
    """Session gracefully handles processing errors"""
    session = PromptCoachSession.create("")
    session.process()
    assert session.status in ["error", "interrogating"]
```

---

## 5. API Tests

**File:** `tests/unit/test_prompt_coach_api.py`

```python
def test_start_session_endpoint():
    """POST /prompt-coach/start creates session"""
    response = client.post("/prompt-coach/start", json={"prompt": "write code"})
    assert response.status_code == 200
    data = response.json()
    assert "session_id" in data
    assert data["status"] == "extracting"


def test_get_session_endpoint():
    """GET /prompt-coach/session/{id} returns session state"""
    create_response = client.post("/prompt-coach/start", json={"prompt": "test"})
    session_id = create_response.json()["session_id"]

    response = client.get(f"/prompt-coach/session/{session_id}")
    assert response.status_code == 200
    assert "status" in response.json()


def test_answer_questions_endpoint():
    """POST /prompt-coach/answer/{id} accepts answers"""
    create_response = client.post("/prompt-coach/start", json={"prompt": "help"})
    session_id = create_response.json()["session_id"]

    response = client.post(
        f"/prompt-coach/answer/{session_id}",
        json={"answers": {"q1": "Python script"}}
    )
    assert response.status_code == 200


def test_save_template_endpoint():
    """POST /prompt-coach/save/{id} saves to library"""
    session_id = create_completed_session()

    response = client.post(
        f"/prompt-coach/save/{session_id}",
        json={"name": "My Template", "category": "coding"}
    )
    assert response.status_code == 200
    assert "template_id" in response.json()


def test_list_templates_endpoint():
    """GET /prompt-coach/templates returns template list"""
    response = client.get("/prompt-coach/templates")
    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_invalid_session_returns_404():
    """Invalid session ID returns 404"""
    response = client.get("/prompt-coach/session/99999")
    assert response.status_code == 404


def test_lessons_endpoint():
    """GET /prompt-coach/lessons returns lessons"""
    response = client.get("/prompt-coach/lessons")
    assert response.status_code == 200
```
