# AskSharon.ai Scripts

Central management scripts for the AskSharon.ai application.

## Quick Start

```bash
# 1. Setup (first time only)
./scripts/setup.sh

# 2. Start all services
./scripts/start.sh

# 3. Check status
./scripts/status.sh

# 4. Run tests (includes frontend tests)
./scripts/test_all.sh

# 5. Stop all services
./scripts/stop.sh
```

**Milestone Testing:**
```bash
# Before marking phase complete
./scripts/test_milestone.sh
```

---

## Available Scripts

### 🚀 `start.sh` - Start All Services
**Central startup script** - launches all 3 services in one command.

```bash
./scripts/start.sh
```

**What it does:**
- ✅ Checks virtual environment exists
- ✅ Verifies ports 8000, 8002, and 8501 are free
- ✅ Starts Orchestrator on port 8000
- ✅ Starts Assistant API on port 8002
- ✅ Starts Streamlit frontend on port 8501
- ✅ Logs output to `logs/orchestrator.log`, `logs/assistant_api.log`, and `logs/frontend.log`
- ✅ Saves PIDs to corresponding `.pid` files
- ✅ Displays access URLs

**Access points after start:**
- Orchestrator: http://localhost:8000
- Assistant API: http://localhost:8002
- API Documentation: http://localhost:8002/docs
- Frontend UI: http://localhost:8501

---

### 🛑 `stop.sh` - Stop All Services
Cleanly shuts down all 3 services.

```bash
./scripts/stop.sh
```

**What it does:**
- Finds processes on ports 8000, 8002, and 8501
- Sends SIGTERM for graceful shutdown
- Force kills if processes don't stop
- Cleans up PID files

---

### 📊 `status.sh` - Check Service Status
Shows current status of all 3 services.

```bash
./scripts/status.sh
```

**What it shows:**
- Orchestrator status (port 8000)
- Assistant API status (port 8002)
- Frontend status (port 8501)
- Database status and size
- Log file information
- Quick summary

---

### ⚙️ `setup.sh` - Initial Setup
First-time environment setup (run once).

```bash
./scripts/setup.sh
```

**What it does:**
- Creates Python virtual environment
- Installs all dependencies from requirements.txt
- Initializes SQLite database from schema
- Creates .env configuration file
- Verifies all modules import successfully

---

### 🧪 `test_all.sh` - Full Test Suite
Runs all code quality checks and tests **including frontend tests**.

```bash
./scripts/test_all.sh
```

**Checks performed (7 total):**
1. Black code formatting
2. Mypy type checking
3. Module import verification
4. Database schema validation
5. Module registry validation
6. **Frontend tests (Playwright)** - NEW!
7. Pytest (if tests exist)

---

### 🏥 `health_check.py` - System Health Check
Comprehensive health verification.

```bash
python scripts/health_check.py
```

**Checks performed:**
1. Python version (>=3.8)
2. Dependencies (10 packages)
3. Core module imports
4. Module registry YAML
5. Database tables (5 expected)
6. File structure (11 key files)
7. Phase status tracking

---

### 📸 `test_frontend.py` - Comprehensive Frontend Testing
**Enhanced Playwright test suite** with visual regression testing.

```bash
source .venv/bin/activate
python scripts/test_frontend.py
```

**Test Coverage (7 checks):**
1. ✅ Page accessibility (HTTP 200)
2. ✅ Page metadata (title)
3. ✅ UI elements present (heading, caption, input, button)
4. ✅ Input interaction (typing text)
5. ✅ Button functionality (click + message render)
6. ✅ Console errors (none expected)
7. ✅ Visual regression (screenshot comparison)

**Visual Regression:**
- First run: Creates baseline in `tests/baselines/`
- Subsequent runs: Compares against baseline
- If changed: Saves diff to `tests/diffs/`
- Failures saved to `tests/failures/`

**Smart Behavior:**
- Auto-checks if services are running
- Requires Pillow for visual comparison: `pip install Pillow`
- Cleans up screenshots if UI unchanged

---

### 🎯 `test_milestone.sh` - Milestone Verification
**Comprehensive pre-milestone testing** - run before marking a phase complete.

```bash
./scripts/test_milestone.sh
```

**Verification Steps (5 sections):**
1. 📊 System health check (`health_check.py`)
2. 🧪 Code quality & tests (`test_all.sh`)
3. 📡 API endpoint verification (4 endpoints)
4. 🌐 Frontend verification (`test_frontend.py`)
5. 📚 Documentation check (6 key files)

**Exit Codes:**
- 0: All checks passed - milestone ready
- 1: Some checks failed - fix issues first

**When to run:**
- Before marking a phase complete
- Before updating `planning/progress.yaml`
- Before creating milestone commit

---

### ✅ `approve_frontend_changes.sh` - Approve UI Changes
**Update visual regression baseline** when UI is intentionally changed.

```bash
./scripts/approve_frontend_changes.sh
```

**What it does:**
- Finds latest screenshot from failed test
- Backs up current baseline
- Replaces baseline with new screenshot
- Cleans up failure/diff directories
- Prompts for confirmation

**When to use:**
- After intentional UI changes
- When test_frontend.py shows "UI changed"
- Before committing new baseline

**Workflow:**
```bash
# 1. Make UI changes to code
# 2. Run tests (will fail on visual regression)
python scripts/test_frontend.py

# 3. Review the diff image
open tests/diffs/frontend_diff_*.png

# 4. If changes look correct, approve
./scripts/approve_frontend_changes.sh

# 5. Commit new baseline
git add tests/baselines/ && git commit -m "Update frontend baseline"
```

---

## Typical Workflow

### First Time Setup
```bash
# 1. Clone/download project
cd asksharon_ai_blueprint

# 2. Run setup
./scripts/setup.sh

# 3. Edit .env with your API keys (optional for Phase 1)
nano .env

# 4. Start services
./scripts/start.sh
```

### Daily Development
```bash
# Start
./scripts/start.sh

# Check status anytime
./scripts/status.sh

# View logs
tail -f logs/backend.log
tail -f logs/frontend.log

# Stop when done
./scripts/stop.sh
```

### Before Committing Code
```bash
# Run all checks (includes frontend tests)
./scripts/test_all.sh

# Or run comprehensive milestone check
./scripts/test_milestone.sh
```

### Before Milestone Completion
```bash
# Comprehensive verification
./scripts/test_milestone.sh

# If all passed, update progress.yaml and commit
```

---

## Log Files

All logs are stored in `logs/`:

- `logs/orchestrator.log` - Orchestrator output (port 8000)
- `logs/assistant_api.log` - Assistant API output (port 8002)
- `logs/frontend.log` - Streamlit frontend output (port 8501)
- Corresponding `.pid` files for each service

**View logs in real-time:**
```bash
tail -f logs/orchestrator.log
tail -f logs/assistant_api.log
tail -f logs/frontend.log
```

---

## Troubleshooting

### "Port already in use"
```bash
# Stop existing services
./scripts/stop.sh

# Or manually kill processes
lsof -ti :8000 | xargs kill
lsof -ti :8002 | xargs kill
lsof -ti :8501 | xargs kill
```

### "Virtual environment not found"
```bash
# Run setup first
./scripts/setup.sh
```

### Services won't start
```bash
# Check logs for errors
cat logs/backend.log
cat logs/frontend.log

# Verify database exists
ls -la assistant/data/memory.db

# Re-run health check
python scripts/health_check.py
```

### Module import errors
```bash
# Reinstall dependencies
source .venv/bin/activate
pip install -r requirements.txt

# Verify imports
python -c "from assistant.core.orchestrator import app"
```

---

## Environment Variables

Edit `.env` to configure:

- `OPENAI_API_KEY` - OpenAI API key (optional for Phase 1)
- `DATABASE_URL` - SQLite database path
- `FASTAPI_PORT` - Backend port (default: 8000)
- `STREAMLIT_PORT` - Frontend port (default: 8501)
- `MORNING_CHECKIN_TIME` - Scheduler time (default: 07:30)
- `EVENING_REFLECTION_TIME` - Scheduler time (default: 21:00)

---

## Script Maintenance

All scripts follow these standards:
- ✅ Color-coded output for clarity
- ✅ Error handling with exit codes
- ✅ Verbose feedback for all operations
- ✅ Compatible with macOS and Linux
- ✅ Safe to run multiple times

**Update scripts:**
Scripts are kept in `scripts/` and should be updated when:
- New services are added
- Ports change
- Additional health checks are needed
- New dependencies are required
