# Prompt Coach

Transform messy "brain-dump" prompts into well-structured, effective prompts through coaching, interrogation, and critique.

## Quick Start

1. Start services: `./scripts/start.sh`
2. Open http://localhost:8501
3. Click the **🎓 Coach** tab
4. Paste your messy prompt and click "Analyze"

## How It Works

### The 6-Section Template

Every good prompt should have these 6 sections:

| Section | Purpose | Example |
|---------|---------|---------|
| **CONTEXT** | Background the AI needs | "I'm a Python developer working on a data pipeline" |
| **CONSTRAINTS** | Requirements and limitations | "Must use pandas, no external APIs, Python 3.9+" |
| **INPUTS** | Data or information provided | "CSV file with columns: date, amount, category" |
| **TASK** | What the AI should do | "Write a function to aggregate monthly totals" |
| **EVALUATION** | How success is measured | "Should handle missing values, return sorted results" |
| **OUTPUT FORMAT** | Expected response format | "Python code with docstring, type hints, example usage" |

### The Coaching Flow

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│   INPUT     │ ──▶ │  QUESTIONS  │ ──▶ │   RESULT    │
│ Brain-dump  │     │ Fill gaps   │     │ + Critique  │
└─────────────┘     └─────────────┘     └─────────────┘
```

1. **Input**: Paste your messy prompt
2. **Extract**: AI identifies what's clear, unclear, or missing
3. **Questions**: Up to 5 targeted questions to fill gaps
4. **Result**: Structured prompt + critique + lessons learned

## Features

### Template Status Display
Visual indicators show section status:
- ✅ Filled - Clear information provided
- 🟡 Unclear - Ambiguous, needs clarification
- ❌ Missing - Not mentioned at all

### Critique & Lessons
After completion, you get:
- **Score** (1-10) - Overall prompt quality
- **Strengths** - What you did well
- **Weaknesses** - What needs improvement
- **Lessons** - Actionable tips for next time

### Save to Library
Save completed prompts for future reference:
- Optional naming for easy lookup
- View past prompts in "Saved Prompts" expander
- Track improvement over time

## Example

**Before (Brain-dump):**
```
help me write code for a thing that does stuff with files
```

**After (Structured):**
```markdown
## CONTEXT
Python developer needing file processing automation

## CONSTRAINTS
- Must work on macOS
- Use standard library only
- Handle files up to 1GB

## INPUTS
- Directory path containing CSV files
- Output directory for processed files

## TASK
Write a Python script that reads all CSV files from input directory,
removes duplicate rows, and saves cleaned files to output directory.

## EVALUATION
- Should handle empty files gracefully
- Log progress for large batches
- Return count of files processed

## OUTPUT FORMAT
Python script with:
- Main function with CLI arguments
- Error handling with clear messages
- Example usage in docstring
```

## API Endpoints

The Prompt Coach exposes these endpoints (on port 8002):

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/prompt-coach/start` | POST | Start new session with brain-dump |
| `/prompt-coach/answer` | POST | Submit answers to questions |
| `/prompt-coach/complete/{id}` | GET | Get final prompt + critique |
| `/prompt-coach/session/{id}` | GET | Get current session state |

## Database

Sessions are stored in `assistant/data/memory.db`:

```sql
prompt_sessions (
    id, created_at, original_prompt, final_prompt,
    overall_score, lessons_json, template_name
)
```

## Architecture

```
assistant/modules/prompt_coach/
├── __init__.py       # Module registration
├── models.py         # Pydantic models
├── system_prompts.py # LLM prompts
├── llm_client.py     # OpenAI client
├── extractor.py      # Parse brain-dump → template
├── interrogator.py   # Generate questions
├── critic.py         # Generate critique + lessons
├── coach.py          # FastAPI router
└── database.py       # SQLite storage
```

## Configuration

Set in `.env`:
```bash
# LLM model for coaching (default: gpt-4o-mini)
PROMPT_COACH_MODEL=gpt-4o-mini
```
