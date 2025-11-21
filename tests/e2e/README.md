# E2E Testing for AskSharon UI

## Overview

This directory contains End-to-End (E2E) tests for the Streamlit UI using Playwright.

**Per UI_TESTING_STANDARDS.md**: These tests are MANDATORY for any new/changed UI features.

## Prerequisites

1. **Install Playwright**:
   ```bash
   pip install playwright pytest-playwright
   playwright install chromium
   ```

2. **Start Backend Services**:

   The E2E tests require both the FastAPI backend and Streamlit frontend to be running.

   **Terminal 1 - Start FastAPI Backend**:
   ```bash
   cd /Users/robertfreyne/Documents/ClaudeCode/asksharon_ai_blueprint
   uvicorn assistant.core.orchestrator:app --port 8000 --reload
   ```

   **Terminal 2 - Start Streamlit Frontend**:
   ```bash
   cd /Users/robertfreyne/Documents/ClaudeCode/asksharon_ai_blueprint
   streamlit run assistant/modules/voice/main.py --server.port 8501
   ```

3. **Database Migration**:

   Ensure the goal calendar tables exist:
   ```bash
   python scripts/migrate_goal_calendar_separate_tables.py
   ```

## Running Tests

### Run All E2E Tests
```bash
PYTHONPATH=/Users/robertfreyne/Documents/ClaudeCode/asksharon_ai_blueprint:$PYTHONPATH pytest tests/e2e/ -v
```

### Run Specific Test
```bash
PYTHONPATH=/Users/robertfreyne/Documents/ClaudeCode/asksharon_ai_blueprint:$PYTHONPATH pytest tests/e2e/test_goal_calendar_ui.py -v
```

### Run with Visible Browser (for debugging)
Edit `tests/e2e/conftest.py` and change `headless=True` to `headless=False`.

## Test Coverage

### test_goal_calendar_ui.py

Tests the goal calendar integration feature:

1. ✅ `test_goal_creation_without_calendar` - Basic goal creation
2. ✅ `test_goal_creation_with_calendar_integration` - Full calendar flow
3. ✅ `test_calendar_fields_only_visible_for_goals` - Conditional UI visibility
4. ✅ `test_calendar_validation_on_invalid_input` - Error handling

## Current Status

**Tests Created**: ✅ 4 tests written
**Tests Executed**: ⏳ Pending backend startup
**Backend Required**: FastAPI on port 8000
**Frontend Required**: Streamlit on port 8501

## Next Steps

1. Start both backend and frontend services
2. Execute E2E tests: `pytest tests/e2e/test_goal_calendar_ui.py -v`
3. Verify all tests pass
4. Only then can we claim "calendar integration UI works"

Per UI_TESTING_STANDARDS.md: "No one (human or AI) is allowed to claim 'the UI works' without a passing E2E test."
