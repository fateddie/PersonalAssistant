# AskSharon.ai – Modular Personal Assistant Blueprint

**Internal package name:** `asksharon_ai_blueprint`
**Public brand:** AskSharon.ai

> 🎯 **Current Status:** Phase 4 (Fitness & Nutrition) Complete | 60+ files | 40+ automated tests | Full documentation

AskSharon.ai is a modular, voice-enabled personal assistant designed for **phase-gated**, **plug-in style** development. It manages email, tasks, routines, and behaviour — with persistent memory and a behavioural-psychology layer (adaptive goal reinforcement, conversational data elicitation, weekly reviews).

## 🚀 What's Working Right Now

✅ **3-Service Architecture** - Orchestrator (8000), Assistant API (8002), Frontend (8501)
✅ **Frontend UI** (Port 8501) - Chat interface with Streamlit
✅ **Fitness Tracker** - Workout sessions, exercise logging, RPE tracking, weekly stats
✅ **Nutrition Tracker** - Meal logging, macro tracking, food database, daily summaries
✅ **Prompt Coach** - Transform messy prompts into structured templates (🎓 Coach tab)
✅ **Discipline System** - Eisenhower Matrix, habits, Pomodoro, CBT thought logs
✅ **Database** - SQLite + FAISS for semantic search
✅ **Testing** - 40+ automated tests with visual regression
✅ **Automation** - One-command setup, start, test, stop
✅ **Documentation** - Comprehensive guides and tutorials

**🎓 New to the project? Start with [TUTORIAL.md](TUTORIAL.md) for a complete walkthrough!**

## 🧠 Shared Memory & Progress Reports

**NEW:** Cross-system intelligence with ManagementTeam + Progress tracking!

✅ **Shared Supabase Memory** - Semantic search across business & personal context
✅ **Progress Reports** - Track activity (yesterday, weekly, last session)
✅ **Morning Check-In** - See active business projects + linked tasks
✅ **Cross-System Intelligence** - Business projects → personal tasks

**Quick Commands:**
```bash
# View yesterday's activity
python scripts/progress_report.py yesterday

# Weekly progress report
python scripts/progress_report.py week

# Activity since last login
python scripts/progress_report.py last-session
```

**Documentation:**
- 📖 [Progress Reports Guide](docs/PROGRESS_REPORTS.md) - Complete guide
- 🚀 [Memory Quick Start](docs/MEMORY_QUICKSTART.md) - 10-minute setup
- 📚 [Memory Integration](docs/MEMORY_INTEGRATION.md) - Technical details

## 🎯 Core Characteristics

- ✅ **Automation** - One-command setup, automated testing, self-healing
- 🔔 **Notifications** - Proactive system events with clear communication
- 🛡️ **Error Handling** - Robust, structured, user-friendly error management
- 📝 **Decision Documentation** - Every technical choice logged with rationale

## 📁 Folder Structure

```
asksharon_ai_blueprint/
├── README.md
├── requirements.txt
├── docs/
│   ├── system_design_blueprint.md
│   ├── phase1_implementation_plan.md
│   └── architecture.puml
├── assistant/
│   ├── core/                  # orchestrator, scheduler, context manager
│   ├── modules/               # voice, memory, email, planner, BIL
│   ├── configs/module_registry.yaml
│   └── data/                  # schema.sql, seeds.json, memory.db (after init)
└── planning/
    ├── progress.yaml
    ├── phase_1_mvp/
    ├── phase_2_behaviour/
    ├── phase_3_planner/
    ├── phase_4_fitness/
    └── phase_5_expansion/
```

## 🚀 Quick Start

```bash
# 1. Clone & setup
git clone https://github.com/fateddie/asksharon_ai_blueprint.git
cd asksharon_ai_blueprint
./scripts/setup.sh

# 2. Configure environment (optional for Phase 1)
nano .env  # Edit with your API keys if needed

# 3. Start all services (one command!)
./scripts/start.sh

# 4. Check status anytime
./scripts/status.sh

# 5. Stop when done
./scripts/stop.sh
```

**Access Points:**
- 🔧 Orchestrator: http://localhost:8000
- 🌐 Assistant API: http://localhost:8002
- 📚 API Docs: http://localhost:8002/docs
- 💬 Chat UI: http://localhost:8501

**See [scripts/README.md](scripts/README.md) for all available scripts.**

## 📋 Phase-Gated Workflow

1. Work only on the active phase in `/planning/<phase>/`
2. Build per `tasks.md`
3. Verify per `acceptance_tests.md`
4. Update `/planning/progress.yaml` before unlocking next phase

## 🧩 Module System

All modules follow the **register()** contract:

```python
def register(app, publish, subscribe):
    """Register module with orchestrator"""
    app.include_router(router, prefix="/module")
    subscribe("event_name", handle_event)
    publish("module_loaded", {"name": "module"})
```

## 📚 Documentation

### 🎓 Getting Started
- **[TUTORIAL.md](TUTORIAL.md)** - Complete guide to what we've built (START HERE!)
- **[DEVELOPER_ONBOARDING.md](DEVELOPER_ONBOARDING.md)** - Quick setup guide
- **[PROGRESS.md](PROGRESS.md)** - Current status & achievements
- **[ROADMAP.md](ROADMAP.md)** - Future development plans

### 🏗️ Architecture & Design
- `docs/system_design_blueprint.md` - Complete technical architecture (450+ lines)
- `docs/IMPLEMENTATION_CONTROL_PLAN.md` - Implementation strategy
- `docs/architecture.puml` - PlantUML diagrams

### 🔧 Development Guidelines
- `.cursorrules` - 26 development rules (Python edition)
- `CLAUDE.md` - AI assistant context
- `principles.md` - Development philosophy
- `docs/DECISIONS.md` - Technical decision log

### 📖 Standards & Patterns
- `docs/RULES_DATABASE_PYTHON.md` - Comprehensive patterns
- `docs/AUTOMATION_STANDARDS.md` - Automation guidelines
- `docs/ERROR_HANDLING_GUIDE.md` - Error management
- `docs/NOTIFICATION_SYSTEM.md` - Notification patterns

### 🧪 Testing & Scripts
- **[scripts/README.md](scripts/README.md)** - All scripts explained

## 🔧 Tech Stack

- **Backend:** FastAPI + uvicorn
- **Frontend:** Streamlit (voice-ready)
- **Database:** SQLite + FAISS (semantic)
- **AI:** OpenAI API
- **Testing:** pytest
- **Formatting:** Black + mypy

## 📦 Packaging

```bash
cd ..
zip -r asksharon_ai_blueprint.zip asksharon_ai_blueprint/
```

## 🤝 Contributing

Follow the 26 Rules in `.cursorrules` and document decisions in `docs/DECISIONS.md`.

## 📄 License

Private - For personal use and MVP development.

---

**Built with** phase-gated methodology, event-driven architecture, and behavioral intelligence.
