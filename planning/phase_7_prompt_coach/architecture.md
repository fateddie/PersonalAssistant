# Phase 7: Prompt Coach - Architecture

## System Overview

```
┌─────────────────────────────────────────────────────────────┐
│                    STREAMLIT UI                              │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────┐  │
│  │ Brain Dump  │  │  Template   │  │   Lessons Library   │  │
│  │   Input     │  │   Display   │  │   (Past Learning)   │  │
│  └──────┬──────┘  └──────▲──────┘  └──────────▲──────────┘  │
└─────────┼────────────────┼────────────────────┼─────────────┘
          │                │                    │
          ▼                │                    │
┌─────────────────────────────────────────────────────────────┐
│                    FASTAPI BACKEND                           │
│  ┌─────────────────────────────────────────────────────┐    │
│  │              PROMPT COACH MODULE                     │    │
│  │  ┌───────────┐ ┌───────────┐ ┌───────────────────┐  │    │
│  │  │ Extractor │ │Interrogator│ │     Critic       │  │    │
│  │  │  (Parse)  │ │ (Questions)│ │ (Teach + Fix)    │  │    │
│  │  └─────┬─────┘ └─────┬─────┘ └────────┬──────────┘  │    │
│  │        │             │                │             │    │
│  │        ▼             ▼                ▼             │    │
│  │  ┌─────────────────────────────────────────────┐   │    │
│  │  │           SESSION MANAGER                    │   │    │
│  │  │  (State machine: extract → ask → fill →     │   │    │
│  │  │   critique → output)                        │   │    │
│  │  └─────────────────────┬───────────────────────┘   │    │
│  └────────────────────────┼────────────────────────────┘    │
│                           │                                  │
│  ┌────────────────────────▼────────────────────────────┐    │
│  │                   EVENT BUS                          │    │
│  │  prompt.session.started  prompt.template.completed   │    │
│  │  prompt.lesson.learned   prompt.saved_to_library     │    │
│  └─────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────┘
          │
          ▼
┌─────────────────────────────────────────────────────────────┐
│                    STORAGE LAYER                             │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────┐  │
│  │   SQLite    │  │    FAISS    │  │      Supabase       │  │
│  │  Sessions   │  │  Semantic   │  │  (Optional Sync)    │  │
│  │  Templates  │  │   Search    │  │  Cross-device       │  │
│  │  Lessons    │  │             │  │                     │  │
│  └─────────────┘  └─────────────┘  └─────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

## Core Components

### 1. Prompt Coach Module

**Location:** `assistant/modules/prompt_coach/`

```
prompt_coach/
├── __init__.py
├── coach.py           # Main coaching logic
├── extractor.py       # Parse brain-dump into template sections
├── interrogator.py    # Generate clarifying questions
├── critic.py          # Critique and teach
├── templates.py       # Template management
├── session.py         # Session state machine
└── system_prompts.py  # AI prompts for each stage
```

### 2. Session State Machine

```
                    ┌──────────────┐
                    │   START      │
                    └──────┬───────┘
                           │
                           ▼
                    ┌──────────────┐
                    │   EXTRACT    │  Parse brain-dump
                    └──────┬───────┘
                           │
                           ▼
                    ┌──────────────┐
              ┌────►│ INTERROGATE  │◄────┐  Ask clarifying questions
              │     └──────┬───────┘     │
              │            │             │
              │            ▼             │
              │     ┌──────────────┐     │
              │     │   WAITING    │     │  Wait for user answers
              │     └──────┬───────┘     │
              │            │             │
              │            ▼             │
              │     ┌──────────────┐     │
              │     │    FILL      │─────┘  Fill template (loop if gaps)
              │     └──────┬───────┘
              │            │
              │            ▼
              │     ┌──────────────┐
              └─────│   CRITIQUE   │  Generate critique + lessons
                    └──────┬───────┘
                           │
                           ▼
                    ┌──────────────┐
                    │   OUTPUT     │  Final prompt + template + lessons
                    └──────┬───────┘
                           │
                           ▼
                    ┌──────────────┐
                    │    SAVE      │  Optionally save to library
                    └──────────────┘
```

### 3. Database Schema

**New Tables:**

```sql
-- Coaching sessions
CREATE TABLE prompt_sessions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    status TEXT DEFAULT 'in_progress',  -- in_progress, completed, abandoned

    -- Input
    original_prompt TEXT NOT NULL,

    -- Extracted template
    context TEXT,
    constraints TEXT,
    inputs TEXT,
    task TEXT,
    evaluation TEXT,
    output_format TEXT,

    -- Output
    final_prompt TEXT,
    critique TEXT,
    lessons_json TEXT,  -- JSON array of lessons learned

    -- Metadata
    clarifying_questions_count INTEGER DEFAULT 0,
    duration_seconds INTEGER
);

-- Saved prompt templates (reusable)
CREATE TABLE prompt_templates (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    name TEXT NOT NULL,
    description TEXT,
    category TEXT,  -- e.g., 'coding', 'writing', 'analysis', 'planning'

    -- Template content
    context TEXT,
    constraints TEXT,
    inputs TEXT,
    task TEXT,
    evaluation TEXT,
    output_format TEXT,

    -- Full prompt
    full_prompt TEXT NOT NULL,

    -- Usage tracking
    use_count INTEGER DEFAULT 0,
    last_used_at TIMESTAMP,

    -- Source
    session_id INTEGER REFERENCES prompt_sessions(id)
);

-- Lessons learned (for pattern detection)
CREATE TABLE prompt_lessons (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    session_id INTEGER REFERENCES prompt_sessions(id),

    -- Lesson content
    category TEXT,  -- e.g., 'missing_context', 'vague_task', 'no_constraints'
    original_issue TEXT,
    improvement TEXT,
    explanation TEXT,  -- WHY this matters

    -- For semantic search
    embedding BLOB
);
```

### 4. API Endpoints

```python
# Start new coaching session
POST /prompt-coach/start
Body: {"prompt": "messy brain dump text..."}
Response: {"session_id": 123, "status": "extracting"}

# Get session state (for polling)
GET /prompt-coach/session/{session_id}
Response: {
    "status": "interrogating",
    "template": {...partial...},
    "questions": ["What's the target audience?", "..."]
}

# Answer clarifying questions
POST /prompt-coach/answer/{session_id}
Body: {"answers": {"question_1": "answer...", "question_2": "..."}}
Response: {"status": "filling" | "interrogating", ...}

# Get final output
GET /prompt-coach/result/{session_id}
Response: {
    "template": {...complete...},
    "final_prompt": "...",
    "critique": "...",
    "lessons": [...]
}

# Save to template library
POST /prompt-coach/save/{session_id}
Body: {"name": "My coding prompt", "category": "coding"}
Response: {"template_id": 456}

# List saved templates
GET /prompt-coach/templates
Response: [{"id": 456, "name": "...", "category": "...", ...}]

# Use saved template
POST /prompt-coach/use-template/{template_id}
Body: {"customizations": {"inputs": "new specific inputs..."}}
Response: {"session_id": 789, "pre_filled_template": {...}}

# Get lessons learned
GET /prompt-coach/lessons
Query: ?category=vague_task&limit=10
Response: [{"category": "...", "issue": "...", "improvement": "...", ...}]
```

### 5. System Prompts

**Location:** `assistant/modules/prompt_coach/system_prompts.py`

```python
COACH_SYSTEM_PROMPT = """
You are a blunt, constructive Prompt Coach and Critic.

Your job is to:
1. Take the user's initial prompt (often messy, incomplete, or vague).
2. Map it into a structured template:
   - CONTEXT
   - CONSTRAINTS
   - INPUTS
   - TASK
   - EVALUATION CRITERIA
   - OUTPUT FORMAT
3. Identify gaps, ambiguities, and weak spots.
4. Ask ONLY the minimum number of targeted clarifying questions needed.
5. Once complete, produce:
   a) A clean, filled-out template.
   b) A final "master prompt" the user can reuse.
   c) A critique with 3-5 prompt-engineering lessons.

Rules:
- Be blunt, honest, and critical. Do not flatter.
- Prioritize clarity, specificity, and constraints.
- Optimize for execution and usefulness.
- If vague, call it out and fix it.
- Ask only targeted questions (<5 total).
- Teach WHY changes matter.
"""

EXTRACTOR_PROMPT = """
Extract as much as possible from this brain-dump into the template sections.
Mark sections as [MISSING] or [UNCLEAR: reason] if not provided.
Do not invent information — only extract what's stated or clearly implied.
"""

INTERROGATOR_PROMPT = """
Based on the extracted template, generate 1-5 targeted clarifying questions.
Focus on the most critical gaps that prevent a quality prompt.
Batch related questions together.
Do not ask about nice-to-haves — only essentials.
"""

CRITIC_PROMPT = """
Compare the original prompt to the final structured version.
Identify:
1. What was weak or missing in the original
2. What specific improvements were made
3. 3-5 key prompt-engineering lessons the user should learn

Be direct and educational. The goal is skill-building, not validation.
"""
```

### 6. Event Bus Integration

**Events Published:**

| Event | Payload | When |
|-------|---------|------|
| `prompt.session.started` | `{session_id, original_prompt}` | New session begins |
| `prompt.template.completed` | `{session_id, template}` | Template fully filled |
| `prompt.lesson.learned` | `{session_id, lessons[]}` | Critique generated |
| `prompt.saved_to_library` | `{template_id, name, category}` | User saves template |

**Events Subscribed:**

| Event | Action |
|-------|--------|
| `task.created` | Offer prompt coaching for task description |
| `goal.created` | Offer prompt coaching for goal clarity |

### 7. Streamlit UI Components

**Location:** `assistant/modules/voice/components/prompt_coach_ui.py`

```python
# Main components:

def render_brain_dump_input():
    """Large text area for messy prompt input"""

def render_template_display(template: dict):
    """6-section template view with fill status indicators"""

def render_clarifying_questions(questions: list):
    """Question cards with answer inputs"""

def render_critique(critique: str, lessons: list):
    """Expandable critique with lesson cards"""

def render_final_prompt(prompt: str):
    """Copy-to-clipboard ready final prompt"""

def render_template_library():
    """Grid of saved templates with search/filter"""

def render_lessons_dashboard():
    """Analytics: common mistakes, improvement over time"""
```

### 8. Integration Points

**Phase 3.5 Discipline:**
- When creating evening plans, offer coach for task clarity
- Use coach to refine implementation intentions (If-Then)

**Phase 6 Gmail:**
- Coach natural language email commands for better accuracy

**Memory Module:**
- Store successful prompts in long-term memory
- Semantic search past prompts for similar situations

## Data Flow Example

```
1. User enters: "help me write code for a thing that does stuff"

2. EXTRACTOR parses:
   CONTEXT: [UNCLEAR: what kind of code? what language?]
   CONSTRAINTS: [MISSING]
   INPUTS: [MISSING]
   TASK: "write code" [VAGUE: what specifically?]
   EVALUATION: [MISSING]
   OUTPUT FORMAT: [MISSING]

3. INTERROGATOR generates:
   Q1: "What programming language and what does 'the thing' do?"
   Q2: "Who will use this code and are there any constraints?"
   Q3: "How will you know if the code is good enough?"

4. User answers questions

5. FILL completes template:
   CONTEXT: Python script for personal use to automate file renaming
   CONSTRAINTS: Must work on macOS, no external dependencies
   INPUTS: Directory path, naming pattern
   TASK: Write a Python script that renames files matching a pattern
   EVALUATION: Works on 100 files, handles errors gracefully
   OUTPUT FORMAT: Single Python file with comments

6. CRITIC generates:
   - Original was vague ("thing", "stuff") — specificity is essential
   - No constraints = unbounded solution space
   - Missing evaluation criteria = no way to judge success

   Lessons:
   1. Always specify the language/framework
   2. Constraints narrow the solution space
   3. Evaluation criteria = definition of done
   4. "Write code" is never enough — what code, for what?

7. OUTPUT: Clean final prompt ready for use
```

## Security Considerations

- No sensitive data in prompts stored unencrypted
- Session data auto-deleted after 30 days (configurable)
- Template library is user-local (no sharing by default)
- Lessons anonymized before any potential future aggregation

## Performance Targets

- Session start → first questions: <3 seconds
- Question answer → template update: <2 seconds
- Full session completion: <5 minutes average
- Template library load: <500ms for 100 templates
