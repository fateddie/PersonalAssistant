# CLAUDE CONTEXT – AskSharon.ai

## Project Overview
Modular Python assistant (FastAPI + Streamlit) with phase-gated development.

## Core Principles (from principles.md - Preserved)
1. **Agentic workflow** - Model + Tools + Environment
2. **Tool-first** - Read/search/edit over giant prompts
3. **Agentic search** - Find files on demand
4. **Project memory** - Load .cursorrules, principles.md, claude.md
5. **Plan → Act → Check** - Explicit step breakdown
6. **Extensibility** - MCP tools, custom utilities
7. **Beyond code** - Discovery, refactoring, docs, analysis
8. **Simplicity** - Keep system transparent
9. **Validation** - Tests and checks over vibes
10. **Human-in-loop** - Accept/deny edits, inspect diffs

## AskSharon-Specific Rules
1. Read `/docs/system_design_blueprint.md` for architecture
2. Work only in active phase under `/planning/`
3. Modules use `register(app, publish, subscribe)` contract
4. Event bus communication only (no cross-imports)
5. Memory via `/assistant/core/context_manager.py`
6. Follow 26 Rules in `.cursorrules`

## Development Workflow

### Session Start
1. Load: principles.md, .cursorrules, claude.md
2. Summarize: Tech stack, active phase, constraints
3. Propose: Plan + tools + tests
4. Get: User approval

### During Task
1. Plan: Document in DECISIONS.md (WHY)
2. Act: Small reversible steps
3. Verify: pytest + black + mypy
4. Notify: User of progress
5. Log: Errors with context

### Before Responding
- [ ] Follows 26 Rules
- [ ] Error handling included
- [ ] Notifications added
- [ ] Tests written
- [ ] Decision logged

## Tech Stack
- **Backend:** FastAPI 0.115.2 + uvicorn
- **Frontend:** Streamlit 1.37.0
- **Database:** SQLite 3.x + SQLAlchemy
- **Semantic:** FAISS (128-dim vectors)
- **AI:** OpenAI API 1.43.0
- **Testing:** pytest
- **Formatting:** Black + mypy

## Inherited Standards
- See `.cursorrules` for 26 Rules
- See `docs/RULES_DATABASE_PYTHON.md` for patterns
- See `docs/AUTOMATION_STANDARDS.md` for automation
- See `docs/ERROR_HANDLING_GUIDE.md` for errors
- See `docs/NOTIFICATION_SYSTEM.md` for notifications

## Subagents
See `.claude/subagents.yaml` for specialized agents:
- module-builder
- bil-agent
- phase-validator
- error-handler-agent
- documentation-agent

## Key Commands
```bash
# Setup
./scripts/setup.sh

# Run
uvicorn assistant.core.orchestrator:app --reload
streamlit run assistant/modules/voice/main.py

# Test
./scripts/test_all.sh
python scripts/health_check.py

# Format
black assistant/
mypy assistant/
```
